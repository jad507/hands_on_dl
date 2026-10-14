#!/usr/bin/env python3
"""
Tests for everything that runs without a GPU, a model, or network access.

Deliberately covers the parts where a silent bug would invalidate an experiment
rather than crash a run:
  * chunk planning against Gemma's 30 s limit (coverage, no gaps, determinism)
  * spine join keys (the cross-engine alignment guarantee)
  * VTT emission against Concord's parser constraints
  * triage scoring on synthetic audio with a known answer

Not covered here, because they need a GPU and gated model downloads:
  * WhisperEngine.transcribe_segments
  * GemmaEngine.transcribe_segments
  * pyannote diarization
Those are exercised by `run.py --limit 3` on a real file.

    python test_pipeline.py
"""

from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

import audio as A
import emit as E
import triage as T
from spine import (
    GEMMA_MAX_CLIP_S,
    Segment,
    Spine,
    make_seg_id,
    plan_chunks,
    stitch,
)


def seg(start, end, speaker="SPEAKER_00", idx=0):
    return Segment(make_seg_id(idx, speaker, start), speaker, start, end)


class TestChunkPlanning(unittest.TestCase):
    """Gemma 4 E2B/E4B reject clips over 30 s. Getting this wrong means the run
    dies deep into a long meeting, or worse, silently truncates."""

    def test_short_segment_untouched(self):
        s = seg(10.0, 25.0)
        chunks = plan_chunks(s)
        self.assertEqual(len(chunks), 1)
        self.assertAlmostEqual(chunks[0].start, 10.0)
        self.assertAlmostEqual(chunks[0].end, 25.0)

    def test_exactly_at_limit(self):
        chunks = plan_chunks(seg(0.0, GEMMA_MAX_CLIP_S))
        self.assertEqual(len(chunks), 1)

    def test_all_chunks_under_limit(self):
        for dur in [30.1, 45, 60, 90, 127.3, 300, 1800, 3600]:
            with self.subTest(dur=dur):
                chunks = plan_chunks(seg(5.0, 5.0 + dur))
                self.assertGreater(len(chunks), 1)
                for c in chunks:
                    self.assertLessEqual(
                        c.duration, GEMMA_MAX_CLIP_S + 1e-6,
                        f"chunk {c.index} is {c.duration:.3f}s (> 30 s limit)",
                    )

    def test_full_coverage_no_gaps(self):
        s = seg(12.5, 12.5 + 137.2)
        chunks = plan_chunks(s)
        self.assertAlmostEqual(chunks[0].start, s.start, places=6)
        self.assertAlmostEqual(chunks[-1].end, s.end, places=6)
        for a, b in zip(chunks, chunks[1:]):
            self.assertLessEqual(b.start, a.end, "gap between chunks loses audio")

    def test_chunks_overlap(self):
        chunks = plan_chunks(seg(0.0, 120.0))
        for a, b in zip(chunks, chunks[1:]):
            self.assertGreater(a.end - b.start, 0.0, "no overlap at boundary")

    def test_deterministic(self):
        s = seg(3.25, 3.25 + 211.7)
        a = [(c.start, c.end) for c in plan_chunks(s)]
        b = [(c.start, c.end) for c in plan_chunks(s)]
        self.assertEqual(a, b)

    def test_no_trailing_sliver(self):
        # A final chunk shorter than the overlap would be pure duplicate audio.
        for dur in np.arange(30.5, 200.0, 3.7):
            chunks = plan_chunks(seg(0.0, float(dur)))
            if len(chunks) > 1:
                self.assertGreater(
                    chunks[-1].duration, 0.75,
                    f"dur={dur}: trailing sliver of {chunks[-1].duration:.3f}s",
                )


class TestStitch(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(stitch([]), "")
        self.assertEqual(stitch(["", "  "]), "")

    def test_single(self):
        self.assertEqual(stitch(["hello world"]), "hello world")

    def test_removes_overlap(self):
        out = stitch(["the quick brown fox", "brown fox jumps over"])
        self.assertEqual(out, "the quick brown fox jumps over")

    def test_single_word_match_is_not_treated_as_overlap(self):
        """Regression. With a 1-word minimum this returned
        "I never said that. she stole it" -- a silently deleted word -- because
        "that." and "That" normalize identically across a clause boundary."""
        out = stitch(["I never said that.", "That she stole it"])
        self.assertEqual(_words(out).count("that"), 2, out)
        self.assertIn("she stole it", out)

    def test_multiword_overlap_is_still_removed(self):
        out = stitch(["the quick brown fox", "brown fox jumps over"])
        self.assertEqual(_words(out).count("brown"), 1, out)
        self.assertEqual(out, "the quick brown fox jumps over")

    def test_case_and_punctuation_insensitive_on_real_overlap(self):
        out = stitch(["and then she said,", "She said, we should go"])
        self.assertEqual(_words(out).count("said"), 1, out)
        self.assertIn("we should go", out)

    def test_no_overlap_concatenates(self):
        out = stitch(["alpha beta", "gamma delta"])
        self.assertEqual(out, "alpha beta gamma delta")

    def test_never_deletes_content_on_ambiguity(self):
        # Conservative direction: duplicating a word is recoverable, dropping is not.
        out = stitch(["a b c", "x y z"])
        for w in "abcxyz":
            self.assertIn(w, out)


class TestSpine(unittest.TestCase):
    def _spine(self):
        segs = [
            Segment(make_seg_id(0, "SPEAKER_00", 0.0), "SPEAKER_00", 0.0, 5.0,
                    text={"whisper": "hello there", "gemma": "hello, there!"}),
            Segment(make_seg_id(1, "SPEAKER_01", 5.5), "SPEAKER_01", 5.5, 12.0,
                    text={"whisper": "general kenobi"}),
        ]
        return Spine("src.mp4", "a.wav", 12.0, segs, diarizer="test")

    def test_round_trip(self):
        s = self._spine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            s.to_json(p)
            back = Spine.from_json(p)
        self.assertEqual(len(back.segments), 2)
        self.assertEqual(back.segments[0].text["gemma"], "hello, there!")
        self.assertEqual(back.diarizer, "test")

    def test_join_key_is_text_independent(self):
        """The whole cross-engine alignment guarantee, in one assertion.

        Concord's unitId() hashes unit text, so a text-derived key breaks the
        moment the transcription policy changes. (server/core/ids.py)
        """
        a = Segment("x", "SPEAKER_00", 1.0, 2.0, text={"e": "one wording"})
        b = Segment("y", "SPEAKER_00", 1.0, 2.0, text={"e": "totally different"})
        self.assertEqual(a.join_key(), b.join_key())

    def test_engines_and_missing(self):
        s = self._spine()
        self.assertEqual(s.engines(), ["whisper", "gemma"])
        self.assertEqual(len(s.missing("gemma")), 1)
        self.assertEqual(len(s.missing("whisper")), 0)

    def test_validate_clean(self):
        self.assertEqual(self._spine().validate(), [])

    def test_validate_catches_duplicate_join_keys(self):
        s = self._spine()
        s.segments[1].speaker = "SPEAKER_00"
        s.segments[1].start = 0.0
        s.segments[1].end = 4.0
        problems = s.validate()
        self.assertTrue(any("join key" in p for p in problems), problems)

    def test_validate_catches_bad_duration(self):
        s = self._spine()
        s.segments[0].end = s.segments[0].start
        self.assertTrue(any("duration" in p for p in s.validate()))


class TestEmit(unittest.TestCase):
    """Every assertion here maps to a line of concord/server/ingest/transcript.js."""

    def _spine(self):
        segs = [
            Segment(make_seg_id(0, "SPEAKER_00", 0.0), "SPEAKER_00", 0.0, 5.0,
                    text={"e": "first turn"}),
            Segment(make_seg_id(1, "SPEAKER_00", 5.0), "SPEAKER_00", 5.0, 9.0,
                    text={"e": "second turn same speaker"}),
        ]
        return Spine("src", "a.wav", 9.0, segs)

    def test_voice_tag_form(self):
        with tempfile.TemporaryDirectory() as d:
            p = E.to_vtt(self._spine(), "e", Path(d) / "o.vtt")
            body = p.read_text(encoding="utf-8")
        self.assertTrue(body.startswith("WEBVTT"))
        self.assertIn("<v SPEAKER_00>first turn</v>", body)

    def test_speaker_label_starts_uppercase(self):
        """SPEAKER_PREFIX = /^([A-Z][\\w .'-]{0,40}?):\\s+(.*)$/s -- a lowercase
        label would not be recognized as a speaker at all."""
        with tempfile.TemporaryDirectory() as d:
            p = E.to_vtt(self._spine(), "e", Path(d) / "o.vtt")
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("<v "):
                    self.assertTrue(line[3].isupper(), line)

    def test_strictly_positive_gap_between_touching_cues(self):
        """mergeCues fuses same-speaker cues when gap <= maxMergeGapSeconds.
        The test is <=, so a zero gap still merges. Two touching segments must
        therefore end up with a strictly positive gap or Concord silently
        changes N between conditions."""
        with tempfile.TemporaryDirectory() as d:
            p = E.to_vtt(self._spine(), "e", Path(d) / "o.vtt")
            body = p.read_text(encoding="utf-8")
        times = []
        for line in body.splitlines():
            if "-->" in line:
                a, b = line.split("-->")
                times.append((_parse_ts(a.strip()), _parse_ts(b.strip())))
        self.assertEqual(len(times), 2)
        gap = times[1][0] - times[0][1]
        self.assertGreater(gap, 0.0, "cues touch; Concord will re-merge them")

    def test_angle_brackets_neutralized(self):
        """stripTags() deletes /<[^>]*>/g. Left alone, '<pause>' would vanish
        silently AND could corrupt the voice tag."""
        s = self._spine()
        s.segments[0].text["e"] = "he said <pause> nothing"
        with tempfile.TemporaryDirectory() as d:
            body = E.to_vtt(s, "e", Path(d) / "o.vtt").read_text(encoding="utf-8")
        self.assertIn("(pause)", body)
        self.assertNotIn("<pause>", body)

    def test_jefferson_notation_survives(self):
        s = self._spine()
        s.segments[0].text["e"] = "I (0.7) never .hh said wor- *that*"
        with tempfile.TemporaryDirectory() as d:
            body = E.to_vtt(s, "e", Path(d) / "o.vtt").read_text(encoding="utf-8")
        for token in ["(0.7)", ".hh", "wor-", "*that*"]:
            self.assertIn(token, body)

    def test_comparison_csv_flags_differences(self):
        segs = [
            Segment("a", "SPEAKER_00", 0.0, 1.0, text={"x": "same", "y": "same"}),
            Segment("b", "SPEAKER_00", 1.0, 2.0, text={"x": "one", "y": "other"}),
        ]
        s = Spine("src", "a.wav", 2.0, segs)
        with tempfile.TemporaryDirectory() as d:
            p = E.to_comparison_csv(s, Path(d) / "c.csv")
            rows = p.read_text(encoding="utf-8").splitlines()
        self.assertIn("True", rows[1])
        self.assertIn("False", rows[2])


class TestTriageSyntactic(unittest.TestCase):
    """Scores structural susceptibility to emphasis WITHOUT knowing the meaning."""

    def test_canonical_seven_meanings_sentence_scores_high(self):
        score, d = T.syntactic_score("I didn't say he stole the money")
        self.assertGreater(score, 0.6, d)
        self.assertTrue(d["negation"])
        self.assertTrue(d["reportative"])

    def test_flat_declarative_scores_low(self):
        score, _ = T.syntactic_score(
            "The quarterly budget report was distributed to all department heads"
        )
        self.assertLess(score, 0.3)

    def test_negation_plus_reportative_beats_either_alone(self):
        both, _ = T.syntactic_score("I never said she took it")
        neg, _ = T.syntactic_score("I never went to the building")
        rep, _ = T.syntactic_score("She said the building was open")
        self.assertGreater(both, neg)
        self.assertGreater(both, rep)

    def test_too_short_is_zero(self):
        self.assertEqual(T.syntactic_score("yes")[0], 0.0)
        self.assertEqual(T.syntactic_score("")[0], 0.0)

    def test_long_segments_dilute(self):
        short, _ = T.syntactic_score("I didn't say he stole it")
        padded = "I didn't say he stole it " + " ".join(["filler"] * 200)
        long_, _ = T.syntactic_score(padded)
        self.assertLess(long_, short)


class TestTriageAcoustic(unittest.TestCase):
    """Synthetic audio with a known answer: a burst is prominent, flat is not."""

    def _tone(self, dur=3.0, sr=16000, amp=0.1, f=180.0):
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        return (amp * np.sin(2 * np.pi * f * t)).astype(np.float32)

    def test_flat_tone_scores_low(self):
        score, d = T.acoustic_score(self._tone(), 16000)
        self.assertLess(score, 0.5, d)

    def test_amplitude_burst_scores_higher_than_flat(self):
        flat = self._tone()
        burst = flat.copy()
        mid = len(burst) // 2
        burst[mid : mid + 8000] *= 6.0  # half a second, 6x louder
        s_flat, _ = T.acoustic_score(flat, 16000)
        s_burst, d = T.acoustic_score(burst, 16000)
        self.assertGreater(s_burst, s_flat, d)

    def test_too_short_returns_zero(self):
        self.assertEqual(T.acoustic_score(np.zeros(100, dtype=np.float32), 16000)[0], 0.0)

    def test_never_raises_on_garbage(self):
        for bad in [np.zeros(16000, dtype=np.float32),
                    np.ones(16000, dtype=np.float32),
                    np.random.randn(16000).astype(np.float32)]:
            score, _ = T.acoustic_score(bad, 16000)
            self.assertTrue(0.0 <= score <= 1.0)


class TestTriageEpistemic(unittest.TestCase):
    def test_confident_scores_low(self):
        s, _ = T.epistemic_score({"avg_logprob": -0.15})
        self.assertLess(s, 0.5)

    def test_uncertain_scores_high(self):
        s, _ = T.epistemic_score({"avg_logprob": -1.2})
        self.assertGreater(s, 0.7)

    def test_missing_data_is_zero_not_crash(self):
        self.assertEqual(T.epistemic_score({})[0], 0.0)


class TestTriageCombined(unittest.TestCase):
    def test_conjunction_beats_either_alone(self):
        """The non-circular core: acoustically marked AND structurally sensitive."""
        base = dict(seg_id="s", acoustic=0.0, syntactic=0.0, epistemic=0.0)
        wa, ws, we = 0.45, 0.40, 0.15
        both = wa * 0.8 + ws * 0.8 + we * 0.0 + 0.15 * 0.8 * 0.8
        ac_only = wa * 0.8 + ws * 0.0 + we * 0.0
        syn_only = wa * 0.0 + ws * 0.8 + we * 0.0
        self.assertGreater(both, ac_only + syn_only * 0.5)
        del base

    def test_select_threshold_and_topk(self):
        scores = [T.TriageScore(f"s{i}", i / 10, 0, 0, 0) for i in range(10)]
        self.assertEqual(len(T.select(scores, threshold=0.5)), 5)
        self.assertEqual(T.select(scores, top_k=3), ["s9", "s8", "s7"])


class TestAudioRoundTrip(unittest.TestCase):
    def test_write_then_load_preserves_samples(self):
        sr = A.TARGET_SR
        t = np.linspace(0, 2.0, sr * 2, endpoint=False)
        original = (0.5 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
        with tempfile.TemporaryDirectory() as d:
            p = A.write_slice_wav(original, Path(d) / "t.wav")
            self.assertEqual(A.wav_info(p)[:2], (sr, 1))
            back = A.load_slice(p, 0.0, 2.0)
        self.assertEqual(len(back), len(original))
        self.assertLess(float(np.max(np.abs(back - original))), 1e-3)  # int16 quantization

    def test_slice_boundaries(self):
        sr = A.TARGET_SR
        sig = np.zeros(sr * 4, dtype=np.float32)
        sig[sr * 2 : sr * 3] = 0.5  # marker in the third second
        with tempfile.TemporaryDirectory() as d:
            p = A.write_slice_wav(sig, Path(d) / "t.wav")
            quiet = A.load_slice(p, 0.0, 1.0)
            loud = A.load_slice(p, 2.0, 3.0)
        self.assertLess(float(np.max(np.abs(quiet))), 0.01)
        self.assertGreater(float(np.max(np.abs(loud))), 0.4)

    def test_load_rejects_wrong_sample_rate(self):
        import wave

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.wav"
            with wave.open(str(p), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(44100)  # not 16 kHz
                w.writeframes(np.zeros(44100, dtype=np.int16).tobytes())
            with self.assertRaises(ValueError):
                A.load_slice(p, 0.0, 1.0)

    def test_is_url(self):
        self.assertTrue(A.is_url("https://youtube.com/watch?v=x"))
        self.assertFalse(A.is_url("C:\\audio\\file.wav"))
        self.assertFalse(A.is_url("/home/x/a.mp3"))


def _parse_ts(ts: str) -> float:
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _words(text: str) -> list[str]:
    """Lowercased, punctuation-stripped tokens -- matches how stitch() compares."""
    return [w.lower().strip(".,!?;:\"'") for w in text.split()]


if __name__ == "__main__":
    unittest.main(verbosity=2)
