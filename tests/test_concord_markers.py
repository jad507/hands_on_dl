"""
Which emphasis notation is safe to use in a transcript Concord will ingest.

This answers an open question left in ISLS doc 06 (the prosody stress test),
which proposes a prominence-annotated transcription policy "P5" and says only
"capitals for stress or asterisks (*money*); test which survives tokenization".

The answer is CAPITALS, and asterisks are disqualified -- not because they get
stripped, but for a reason the doc did not anticipate.

`splitSentences()` in Concord's server/ingest/unitize.js splits after . ! ? only
when the next non-whitespace character is an uppercase letter or a digit, with a
special case that looks one character past a quote or an opening bracket. An
asterisk is neither, so a sentence whose first word is emphasized looks like it
begins in lowercase and the split is suppressed: two sentences silently become
one unit.

That is disqualifying rather than cosmetic. The ISLS design's thesis is that
unit boundaries are load-bearing. A notation that moves them changes N, changes
every content-hashed unit id, and changes the question the judge is asked --
while producing output that looks fine.

These tests drive Concord's real modules through `tools/concord_marker_probe.mjs`
rather than reimplementing its tokenizer, so they track the actual dependency.
They skip when node or the concord checkout is absent.

Run:  python -m pytest tests/ -v
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROBE = REPO / "tools" / "concord_marker_probe.mjs"
CONCORD = REPO.parent / "concord"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None
    or not CONCORD.is_dir()
    or not (CONCORD / "server" / "ingest" / "unitize.js").is_file(),
    reason="node or the concord checkout is not available",
)


@pytest.fixture(scope="module")
def probe():
    r = subprocess.run(["node", str(PROBE), str(CONCORD)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        pytest.fail(f"probe failed:\n{r.stderr[-2000:]}")
    return json.loads(r.stdout)


# ----------------------------------------------------- what stripTags destroys

def test_angle_bracket_markup_is_destroyed_silently(probe):
    """`<em>money</em>` arrives as plain "money". No error, no marker, no trace
    that anything was removed -- the worst possible failure shape, because a
    policy that recorded prominence would appear to have produced a transcript
    with none in it."""
    r = probe["inline"]["angle_bracket"]
    assert not r["survives_ingest"]
    assert not r["marker_intact"]
    assert "money" in r["after_ingest"]
    assert "<em>" not in r["after_ingest"]


@pytest.mark.parametrize("notation", [
    "caps", "asterisk", "double_asterisk", "underscore", "caret",
    "square_bracket", "curly", "pipe", "jefferson_under",
])
def test_non_angle_bracket_notations_survive_ingest(probe, notation):
    """Everything that is not angle brackets makes it through stripTags and
    into the unit text unchanged, including a Jefferson-style combining macron
    below."""
    r = probe["inline"][notation]
    assert r["survives_ingest"], f"{notation} did not survive ingest"
    assert r["marker_intact"], f"{notation} did not stay inside one unit"


# ------------------------------------------- the boundary test, which decides

def test_capitals_do_not_move_unit_boundaries(probe):
    """CAPITALS is the recommended notation. An emphasized word opening a
    sentence must still split into two units, exactly as unmarked text does."""
    assert probe["boundary"]["plain"]["n_units"] == 2
    assert probe["boundary"]["caps"]["n_units"] == 2
    assert probe["boundary"]["caps"]["splits_correctly"]


@pytest.mark.parametrize("notation", [
    "asterisk", "double_asterisk", "underscore", "caret", "curly", "pipe",
])
def test_these_notations_silently_merge_two_sentences(probe, notation):
    """The finding that disqualifies asterisks.

    If this ever starts failing, Concord's splitSentences has changed its
    allowed-opener set and the notation choice should be revisited -- that would
    be good news, not a broken test."""
    r = probe["boundary"][notation]
    assert r["n_units"] == 1, (
        f"{notation} now splits correctly; splitSentences may have changed. "
        f"Re-examine the P5 notation recommendation.")
    assert not r["splits_correctly"]


def test_square_brackets_and_quotes_are_also_safe(probe):
    """splitSentences explicitly looks one character past a quote or an opening
    bracket, so these two are safe as well. Square brackets are the fallback if
    CAPITALS turns out to interact badly with a judge prompt."""
    assert probe["boundary"]["square_bracket"]["n_units"] == 2
    assert probe["boundary"]["quote"]["n_units"] == 2


# ------------------------------------------------------------- unit ids

def test_marking_a_word_changes_its_unit_id(probe):
    """Concord's unit ids are SHA-256 of the unit text, so changing the
    transcription policy changes every id. The ISLS technical spec (doc 03,
    finding 3) states this; this demonstrates it, and it is the reason
    cross-condition joins must go through time anchors rather than ids.
    See blockmatch.py, which is that join."""
    s = probe["id_stability"]
    assert s["ids_differ"]
    assert s["plain_id"] != s["marked_id"]


# ------------------------------------------------------------- the summary

def test_exactly_one_recommended_notation_passes_both_probes(probe):
    """The whole point, asserted directly: of the candidates doc 06 names,
    CAPITALS is the one that survives ingest AND preserves unit boundaries."""
    def safe(name):
        return (probe["inline"].get(name, {}).get("marker_intact") is True
                and probe["boundary"].get(name, {}).get("splits_correctly") is True)

    assert safe("caps"), "CAPITALS should be safe on both probes"
    assert not safe("asterisk"), "asterisks should fail the boundary probe"
    assert safe("square_bracket"), "square brackets should be safe on both"
