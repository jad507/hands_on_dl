"""
Tests for find_stress_videos.py.

Two things here decide whether the search produces a real corpus or a pile of
false positives, and neither is obvious from reading the code.

The first is the rolling-duplicate problem. YouTube auto-captions repeat each
line as the next one scrolls into view, so the same sentence appears in the raw
VTT two or three times for reasons that have nothing to do with the speaker. If
that is not collapsed, EVERY video looks like a contrastive-stress demonstration
and the whole method is worthless. But collapsing too aggressively would erase
the genuine repeats, which are the signal. The rule has to remove consecutive
duplicates only, and the tests pin both halves of that.

The second is what counts as a hit. A chorus repeats. A catchphrase repeats. A
lecturer saying "so" forty times repeats. The filters that separate those from a
demonstration are a minimum phrase length, a minimum repeat count, and a maximum
time span, and each is tested against the case it exists to reject.

Run:  python -m pytest test_find_stress_videos.py -v
"""

import find_stress_videos as F


def vtt(*cues):
    """Build a VTT from (start_seconds, text) pairs."""
    out = ["WEBVTT", "Kind: captions", "Language: en", ""]
    for t, text in cues:
        h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
        out.append(f"{h:02d}:{m:02d}:{s:06.3f} --> {h:02d}:{m:02d}:{s + 1:06.3f}")
        out.append(text)
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------- VTT parsing

def test_consecutive_duplicates_are_collapsed():
    """The rolling-caption artefact. Without this every video is a false hit."""
    raw = vtt((0, "hello there"), (1, "hello there"), (2, "hello there"))
    assert [line for _, line in F.parse_vtt(raw)] == ["hello there"]


def test_a_genuine_later_repeat_survives():
    """The other half of the same rule: a line that comes back after something
    else is the actual signal and must not be collapsed away."""
    raw = vtt((0, "i didn't say he stole the money"),
              (3, "notice the stress"),
              (6, "i didn't say he stole the money"))
    lines = [line for _, line in F.parse_vtt(raw)]
    assert lines.count("i didn't say he stole the money") == 2


def test_inline_timing_tags_are_stripped():
    """Auto-captions carry per-word <00:00:01.234><c> markup; leaving it in would
    make two identical sentences compare unequal."""
    raw = vtt((0, "hello<00:00:00.320><c> there</c>"))
    assert [line for _, line in F.parse_vtt(raw)] == ["hello there"]


def test_headers_are_not_treated_as_speech():
    raw = vtt((0, "real speech"))
    assert [line for _, line in F.parse_vtt(raw)] == ["real speech"]


def test_timestamps_are_recovered():
    raw = vtt((0, "first"), (65, "second"))
    times = [t for t, _ in F.parse_vtt(raw)]
    assert times[0] == 0.0
    assert abs(times[1] - 65.0) < 0.01


# ------------------------------------------------------------- normalisation

def test_normalise_folds_case_and_punctuation():
    """"I didn't say he stole the money." and "i didnt say..." must match, or a
    speaker whose repetitions were punctuated differently by the ASR is missed."""
    assert F.normalise("I didn't SAY he stole the money.") == \
           ["i", "didn't", "say", "he", "stole", "the", "money"]


def test_normalise_handles_the_curly_apostrophe():
    """YouTube emits both. If they do not fold together, half the repeats of a
    contraction-bearing sentence fail to match each other."""
    assert F.normalise("didn\u2019t") == F.normalise("didn't")


# ------------------------------------------------------------- the hit rule

# Real demonstrations vary their patter between readings ("notice the change",
# "now this one", "hear the difference"). That variation is what makes the
# repeated sentence stand out from everything around it, so the fixture has to
# have it. A fixture with constant filler tests a case that does not occur and
# would have forced a wrong fix into the tool.
FILLERS = ["notice how the meaning changes", "now try this one",
           "hear the difference there", "same words completely different",
           "listen carefully to this", "and one more time", "watch what happens"]


def demo(sentence, n, gap=8.0):
    """A contrastive-stress demonstration: one sentence, n times, with patter."""
    cues, t = [], 0.0
    for i in range(n):
        cues.append((t, sentence))
        t += gap / 2
        cues.append((t, FILLERS[i % len(FILLERS)]))
        t += gap / 2
    return vtt(*cues)


def test_a_real_demonstration_is_found():
    raw = demo("i didn't say he stole the money", 7)
    hit = F.find_repeated_phrase(F.parse_vtt(raw))
    assert hit is not None
    assert hit["phrase"] == "i didn't say he stole the money"
    assert hit["repeats"] == 7


PROSE = [
    "welcome back everyone to another episode of the programme",
    "today we are looking at something rather different",
    "the history here goes back several decades at least",
    "most people assume the opposite is true which is understandable",
    "but the evidence points somewhere else entirely",
    "let me walk through three examples from the archive",
    "the first comes from a municipal record in nineteen sixty",
    "nobody at the time thought it worth preserving",
    "the second is a letter that surfaced much later",
    "its author remains unidentified to this day",
    "the third example is the one that changed my mind",
    "it contradicts almost everything written before it",
    "so where does that leave the standard account",
    "probably in need of substantial revision",
    "thanks for watching and see you next time",
]


def test_ordinary_speech_produces_no_hit():
    """Specificity. If prose without a repeated sentence scored, the output would
    be dominated by whatever happened to rank highly in search."""
    raw = vtt(*[(i * 4.0, line) for i, line in enumerate(PROSE)])
    assert F.find_repeated_phrase(F.parse_vtt(raw)) is None


def test_digits_survive_normalisation():
    """The bug this caught, and it was in the tool rather than the fixture.

    The normaliser matched [a-z']+ only, so "step 1" and "step 2" both became
    ["step"] and every countdown, ranking or numbered-list video looked like one
    sentence repeated verbatim. The number is lexical content here: it is
    precisely the part that differs between utterances."""
    assert F.normalise("step 1 of 3") == ["step", "1", "of", "3"]
    assert F.normalise("step 1 is easy") != F.normalise("step 2 is easy")


def test_the_repeated_sentence_wins_over_surrounding_patter():
    """The selection rule, on realistic input.

    A real demonstration varies what it says between readings. The sentence is
    therefore the most-repeated gram in the transcript, and must be reported in
    preference to any longer gram that straddles it and the words either side.
    Ranking by length first got this wrong; ranking by repeat count gets it
    right."""
    cues, t = [], 0.0
    for i in range(6):
        cues.append((t, FILLERS[i % len(FILLERS)]))
        t += 4.0
        cues.append((t, "i didn't say he stole the money"))
        t += 4.0
    hit = F.find_repeated_phrase(F.parse_vtt(vtt(*cues)))
    assert hit is not None
    assert hit["phrase"] == "i didn't say he stole the money"
    assert hit["repeats"] == 6


def test_a_fully_fixed_frame_around_the_sentence_is_a_known_limitation():
    """Documented limitation, asserted so it cannot change silently.

    If the words either side of the target sentence are byte-identical on every
    repetition, the frame plus the sentence repeats exactly as often as the
    sentence alone, and the length tie-break reports the whole frame. No filter
    can separate the two without utterance boundaries, which auto-captions do
    not carry.

    This does not occur in real demonstrations, which vary their patter, and the
    smoke run over real videos returned clean sentences. But the boundary of the
    method belongs in a test rather than in somebody's memory. A reader of the
    output CSV who sees an over-long phrase is looking at this case."""
    cues, t = [], 0.0
    for _ in range(6):
        cues.append((t, "and here it is once more"))
        t += 4.0
        cues.append((t, "i didn't say he stole the money"))
        t += 4.0
    hit = F.find_repeated_phrase(F.parse_vtt(vtt(*cues)))
    assert hit is not None
    assert hit["phrase"].startswith("and here it is once more"), \
        "limitation no longer reproduces; revisit the ranking rule"


def test_heavily_templated_prose_is_a_known_false_positive():
    """Documented limitation, asserted so it cannot change silently.

    Forty lines built from one fixed template still contain a long gram that
    repeats, because the word stream carries no utterance boundaries and the
    filters cannot tell "one sentence said forty times" from "a template filled
    in forty times". Real speech does not do this and the smoke run found no
    such case, but the boundary of the method belongs in a test rather than in
    somebody's memory.

    If this ever starts returning None, the method got stricter and this test
    should be rewritten, not deleted."""
    raw = vtt(*[(i * 3.0, f"this is sentence number {i} and it is different")
                for i in range(40)])
    hit = F.find_repeated_phrase(F.parse_vtt(raw))
    assert hit is not None, "limitation no longer reproduces; revisit the method"


def test_is_periodic_detects_a_doubled_block():
    assert F.is_periodic(tuple("a b c d a b c d".split()), 4)
    assert not F.is_periodic(tuple("i didn't say he stole the money".split()), 4)


def test_three_repeats_is_not_enough_by_default():
    """The threshold is 4. Three repeats happens in ordinary emphatic speech."""
    assert F.find_repeated_phrase(F.parse_vtt(demo("i love this sentence", 3))) is None
    assert F.find_repeated_phrase(F.parse_vtt(demo("i love this sentence", 4))) is not None


def test_a_chorus_spread_over_a_long_song_is_rejected():
    """A chorus repeats, which is why the search space is full of music. The
    discriminator is that a demonstration is compact: seven readings inside two
    minutes, not four spread across thirteen minutes of song."""
    cues, t = [], 0.0
    for _ in range(5):
        cues.append((t, "never gonna give you up never gonna let you down"))
        cues.append((t + 20, "some completely different verse material here"))
        t += 200.0        # 800 s span, well past the 300 s limit
    assert F.find_repeated_phrase(F.parse_vtt(vtt(*cues))) is None


def test_a_compact_demonstration_survives_the_span_filter():
    """The other side of the span rule: seven readings in ninety seconds is the
    real shape of the thing we are looking for, and must not be filtered out."""
    raw = demo("i never said she stole my money", 7, gap=13.0)
    hit = F.find_repeated_phrase(F.parse_vtt(raw))
    assert hit is not None and hit["repeats"] == 7


def test_a_short_stock_phrase_is_not_a_hit():
    """"you know what i mean" said five times is a verbal tic, not a sentence
    demonstration. Below the 4-word floor it would be, which is why the floor
    exists; this pins that a 3-word tic stays out."""
    raw = demo("you know what", 6)
    hit = F.find_repeated_phrase(F.parse_vtt(raw), min_words=4)
    assert hit is None or hit["n_words"] >= 4


def test_the_longer_phrase_wins():
    """A long exact repeat is much stronger evidence than a short one, and the
    short one is always a subset of it. Reporting the fragment would understate
    the find and make deduplication against other rows harder."""
    raw = demo("i never said she stole my money yesterday", 6)
    hit = F.find_repeated_phrase(F.parse_vtt(raw))
    assert hit["phrase"] == "i never said she stole my money yesterday"


def test_hit_reports_where_and_how_long():
    raw = demo("i didn't say we should kill him", 5, gap=10.0)
    hit = F.find_repeated_phrase(F.parse_vtt(raw))
    assert hit["first_s"] == 0.0
    assert 0 < hit["span_s"] <= 600


# ---------------------------------------------------- dedup against Copilot

def test_known_ids_are_read_from_all_three_url_shapes(tmp_path, monkeypatch):
    """watch?v=, shorts/ and youtu.be all appear in the earlier passes. Missing
    one shape would re-fetch captions for videos already catalogued."""
    docs = tmp_path / "CopilotDocs"
    docs.mkdir()
    (docs / "a.csv").write_text(
        "url\nhttps://www.youtube.com/watch?v=AAAAAAAAAAA\n"
        "https://www.youtube.com/shorts/BBBBBBBBBBB\n"
        "https://youtu.be/CCCCCCCCCCC\n", encoding="utf-8")
    monkeypatch.setattr(F, "HERE", tmp_path)
    assert F.load_known(tmp_path) == {"AAAAAAAAAAA", "BBBBBBBBBBB", "CCCCCCCCCCC"}


def test_tiktok_files_are_skipped_entirely(tmp_path):
    """TikTok is blocked on this machine by policy. The dedup reader must not
    even read those files, so no TikTok URL can leak into a fetch list."""
    docs = tmp_path / "CopilotDocs"
    docs.mkdir()
    (docs / "tiktok_candidates.csv").write_text(
        "url\nhttps://www.youtube.com/watch?v=DDDDDDDDDDD\n", encoding="utf-8")
    assert F.load_known(tmp_path) == set()


def test_music_hint_catches_the_obvious_cases():
    """These titles came back from real searches for the target sentences."""
    for title in ["GIVON - TWENTIES (Official Music Video)",
                  "Finesse2Tymes - Back End [Official Music Video]",
                  "Some Song (Lyrics)", "Artist - Track ft. Other"]:
        assert F.MUSIC_HINT.search(title), title
    for title in ["A Lesson in Inflection",
                  "Contrastive stress explained for ESL learners"]:
        assert not F.MUSIC_HINT.search(title), title
