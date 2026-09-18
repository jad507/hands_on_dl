"""
Tests for verify_stress.py.

The risky part of this script is not the acoustics, it is the bookkeeping that
happens before them. If the word windows are wrong, every prominence number is
measured over the wrong slice of audio and the output is confident nonsense that
looks fine in a spreadsheet.

Two failure modes get pinned here.

The first is the rolling-caption duplication. YouTube auto-captions restate the
previous line as plain text before the next timed line, so a parser that takes
every line doubles the whole transcript, and every second "occurrence" of the
target sentence is a phantom with no audio under it.

The second is occurrence overlap. If the search for the sentence advances one
word at a time instead of jumping past a match, a sentence containing a repeated
run reports more occurrences than the speaker said.

The acoustic scoring is tested for the property that actually matters: it is
relative within a repetition, so a quiet recording and a loud one give the same
answer about which word was stressed.

Run:  python -m pytest test_verify_stress.py -v
"""

import numpy as np
import pytest

import verify_stress as V


def cue(t0, t1, body):
    def ts(x):
        return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}"
    return f"{ts(t0)} --> {ts(t1)} align:start position:0%\n{body}\n"


# ------------------------------------------------------- word-level parsing

def test_word_timings_come_from_the_inline_markers():
    vtt = ("WEBVTT\nKind: captions\nLanguage: en\n\n" +
           cue(0.0, 3.0, "hello<00:00:00.500><c> there</c><00:00:01.200><c> world</c>"))
    got = V.parse_vtt_words(vtt)
    assert [w for w, _ in got] == ["hello", "there", "world"]
    assert got[0][1] == pytest.approx(0.0)
    assert got[1][1] == pytest.approx(0.5)
    assert got[2][1] == pytest.approx(1.2)


def test_rolling_restatement_lines_are_skipped():
    """The duplication artefact. A cue whose body has no inline timing is the
    previous line shown again; counting it doubles the transcript and invents
    occurrences that have no audio behind them."""
    vtt = ("WEBVTT\n\n" +
           cue(0.0, 3.0, "hello<00:00:00.500><c> there</c>") +
           cue(3.0, 3.01, "hello there") +
           cue(3.01, 6.0, "second<00:00:03.500><c> line</c>"))
    assert [w for w, _ in V.parse_vtt_words(vtt)] == \
           ["hello", "there", "second", "line"]


def test_closing_tags_do_not_become_words():
    vtt = "WEBVTT\n\n" + cue(0.0, 2.0, "a<00:00:00.400><c> b</c><00:00:00.800><c> c</c>")
    assert [w for w, _ in V.parse_vtt_words(vtt)] == ["a", "b", "c"]


def test_contractions_and_case_are_normalised():
    vtt = "WEBVTT\n\n" + cue(0.0, 2.0, "I<00:00:00.300><c> DIDN'T</c><00:00:00.600><c> say,</c>")
    assert [w for w, _ in V.parse_vtt_words(vtt)] == ["i", "didn't", "say"]


def test_digits_are_kept_as_words():
    """Same reason as in find_stress_videos: the number is what differs between
    otherwise identical utterances."""
    vtt = "WEBVTT\n\n" + cue(0.0, 2.0, "step<00:00:00.300><c> 1</c><00:00:00.600><c> now</c>")
    assert [w for w, _ in V.parse_vtt_words(vtt)] == ["step", "1", "now"]


def test_hours_are_parsed():
    assert V.hms("01:02:03.500") == pytest.approx(3723.5)


# ---------------------------------------------------------------- locating

def words_at(seq, step=0.2):
    return [(w, i * step) for i, w in enumerate(seq)]


def test_locate_finds_each_repetition():
    stream = words_at("a b i didn't say he stole the money c d "
                      "i didn't say he stole the money".split())
    occ = V.locate(stream, "i didn't say he stole the money")
    assert len(occ) == 2
    assert [w for w, _ in occ[0]] == "i didn't say he stole the money".split()


def test_locate_does_not_double_count_overlapping_runs():
    """Advancing one word at a time after a match would report three
    occurrences of "na na" in "na na na na", not two."""
    stream = words_at(["na"] * 4)
    assert len(V.locate(stream, "na na")) == 2


def test_locate_returns_word_times():
    stream = words_at("x i didn't say".split(), step=0.5)
    occ = V.locate(stream, "i didn't say")
    assert [round(t, 2) for _, t in occ[0]] == [0.5, 1.0, 1.5]


def test_locate_returns_nothing_when_absent():
    assert V.locate(words_at("one two three".split()), "four five six") == []


# --------------------------------------------------------- phrase extension

SENT = "i didn't say he stole the money".split()


# Real speech around the readings varies. Fixtures with fixed patter test a
# case that does not occur, and extension will correctly swallow the patter --
# which is right behaviour but tells you nothing about the sentence boundary.
LEADS = ["notice", "listen", "again", "here", "next", "another", "finally",
         "watch", "consider"]
TAILS = ["meaning", "understand", "different", "hear", "clear", "obviously",
         "right", "exactly", "good"]


def transcript_with(reps, truncated=0):
    """`reps` full readings plus `truncated` readings missing the opening words,
    which is what a slightly different ASR rendering looks like in practice."""
    seq = []
    for i in range(reps):
        seq += [LEADS[i % len(LEADS)]] + SENT + [TAILS[i % len(TAILS)]]
    for i in range(truncated):
        seq += [LEADS[(i + 3) % len(LEADS)]] + SENT[3:] + [TAILS[i % len(TAILS)]]
    return [(w, i * 0.2) for i, w in enumerate(seq)]


def test_extension_recovers_the_full_sentence_from_a_fragment():
    """The VOA failure, in miniature. The fragment "he stole the money" occurs
    more often than the whole sentence because one reading was transcribed
    differently, so the detector prefers it and every downstream metric is then
    computed over four words instead of seven -- which is how a truncated
    fragment scored a perfect 1.0 coverage."""
    words = transcript_with(reps=8, truncated=1)
    got = V.extend_phrase(words, "he stole the money", min_repeats=4)
    assert got == "i didn't say he stole the money"


def test_extension_stops_where_the_surrounding_words_vary():
    """The boundary rule. Extension continues only while the longer phrase still
    repeats, so varying patter either side terminates it exactly at the
    sentence."""
    words = transcript_with(reps=9)
    got = V.extend_phrase(words, "say he stole", min_repeats=4)
    assert got == "i didn't say he stole the money"


def test_extension_does_absorb_genuinely_fixed_framing():
    """Stated as a property rather than a bug. If the same word really does
    precede every single reading, it is part of what repeats and extension takes
    it. The sentence is never lost, which is the guarantee that matters."""
    seq = []
    for i in range(6):
        seq += ["okay"] + SENT + [TAILS[i]]
    words = [(w, i * 0.2) for i, w in enumerate(seq)]
    got = V.extend_phrase(words, " ".join(SENT), min_repeats=4)
    assert "i didn't say he stole the money" in got
    assert got.startswith("okay")


def test_extension_will_not_drop_below_the_repeat_threshold():
    """An extension is only kept while the longer phrase still repeats enough.
    If the preceding word is different every time, nothing is added."""
    seq = []
    for lead in ["one", "two", "three", "four", "five", "six"]:
        seq += [lead] + SENT
    words = [(w, i * 0.2) for i, w in enumerate(seq)]
    got = V.extend_phrase(words, " ".join(SENT), min_repeats=4)
    assert got == "i didn't say he stole the money"


def test_extension_respects_the_length_cap():
    words = [(w, i * 0.2) for i, w in enumerate(("a b c d " * 40).split())]
    got = V.extend_phrase(words, "a b c d", min_repeats=4, max_words=8)
    assert len(got.split()) <= 8


# ------------------------------------------------------------ longest walk

def test_walk_counts_a_clean_left_to_right_sweep():
    assert V.longest_walk([0, 1, 2, 3, 4, 5, 6]) == 7


def test_walk_survives_an_intro_reading():
    """Almost every real video says the sentence once neutrally before starting
    the walk. A strict monotonicity test throws those away; this must not."""
    assert V.longest_walk([4, 0, 1, 2, 3, 5, 6]) == 6


def test_walk_survives_a_single_tracker_slip():
    assert V.longest_walk([0, 1, 6, 2, 3, 4]) == 5


def test_walk_is_short_when_the_same_word_is_always_stressed():
    """This case is not a demonstration, but note the walk stays high because a
    flat sequence is non-decreasing. distinct_stress is what rejects it, which
    is why the report needs both numbers."""
    assert V.longest_walk([3, 3, 3, 3]) == 4
    assert len(set([3, 3, 3, 3])) == 1


def test_walk_of_empty_is_zero():
    assert V.longest_walk([]) == 0


# ------------------------------------------------------- prominence scoring

class FakeSound:
    """Stands in for a parselmouth Sound. Word `loud_idx` is louder and higher."""

    def __init__(self, bounds, loud_idx, gain=0.0):
        self.bounds, self.loud_idx, self.gain = bounds, loud_idx, gain

    def get_total_duration(self):
        return self.bounds[-1][2] + 1.0

    def _which(self, t):
        for i, (_, a, b) in enumerate(self.bounds):
            if a <= t < b:
                return i
        return None

    def to_intensity(self, minimum_pitch=75.0):
        s = self

        class I:
            def get_value(self, t):
                i = s._which(t)
                if i is None:
                    return 40.0 + s.gain
                return (70.0 if i == s.loud_idx else 55.0) + s.gain
        return I()

    def to_pitch(self):
        s = self

        class P:
            def get_value_at_time(self, t):
                i = s._which(t)
                if i is None:
                    return float("nan")
                return 250.0 if i == s.loud_idx else 120.0
        return P()


def build(words, loud_idx, gain=0.0, step=0.4):
    occ = [(w, i * step) for i, w in enumerate(words)]
    bounds = [(w, i * step, (i + 1) * step) for i, w in enumerate(words)]
    return FakeSound(bounds, loud_idx, gain), occ


def test_the_loud_high_word_is_the_stressed_one():
    words = "i didn't say he stole the money".split()
    snd, occ = build(words, loud_idx=4)
    prof = V.prominence_profile(snd, occ)
    best = max(range(len(prof)), key=lambda k: prof[k]["prominence"])
    assert words[best] == "stole"


def test_scoring_is_relative_so_recording_level_does_not_matter():
    """The z-score is taken within the repetition. A recording 20 dB louder must
    give the same answer, or every quiet clip would rank differently from a loud
    one for reasons that have nothing to do with the speaker."""
    words = "i didn't say he stole the money".split()
    quiet = V.prominence_profile(*build(words, 2, gain=0.0))
    loud = V.prominence_profile(*build(words, 2, gain=20.0))
    pick = lambda p: max(range(len(p)), key=lambda k: p[k]["prominence"])
    assert pick(quiet) == pick(loud) == 2


def test_every_word_gets_a_row():
    words = "one two three four five".split()
    prof = V.prominence_profile(*build(words, 1))
    assert [r["word"] for r in prof] == words
    assert all("prominence" in r for r in prof)


def test_nan_pitch_does_not_crash_the_z_score():
    """Pitch tracking returns nothing on unvoiced or creaky stretches. Those
    words must score neutrally rather than propagating NaN through the sum and
    making argmax meaningless."""
    words = "one two three four".split()
    snd, occ = build(words, 0)
    snd.to_pitch = lambda: type("P", (), {
        "get_value_at_time": staticmethod(lambda t: float("nan"))})()
    prof = V.prominence_profile(snd, occ)
    assert all(np.isfinite(r["prominence"]) for r in prof)
