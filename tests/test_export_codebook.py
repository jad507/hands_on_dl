"""
Tests for export_codebook.py.

The test that earns its place here is `test_anchor_quotes_are_actually_parsed`.

While writing this module an ASCII cleanup rewrote a literal em-dash inside the
quote-matching regex to "--". The codebook's blockquotes use an em-dash, so the
parser then found **zero** anchor quotes -- and `--validate` still passed,
because a construct with no examples is perfectly valid. The output was
well-formed, Concord accepted it, and every anchor quote the researchers had
chosen was silently gone.

That is the same failure shape this whole project is about: a change that
produces valid-looking output and destroys the content. So the count is pinned.

Run:  python -m pytest tests/ -v
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

import export_codebook as EC
import paths

REPO = Path(__file__).resolve().parent.parent
CONCORD = REPO.parent / "concord"

corpus_only = pytest.mark.skipif(
    not paths.THEMES_MD_PATH.is_file(),
    reason="codebook not present on this machine",
)


@pytest.fixture(scope="module")
def themes():
    return EC.parse_codebook(paths.THEMES_MD_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------- parsing

@corpus_only
def test_four_themes_with_the_pipeline_keys(themes):
    assert len(themes) == 4
    assert [t["key"] for t in themes] == [
        "municipally_managed_resources", "municipal_process",
        "health_and_well_being", "power_dynamics_and_inequality"]


@corpus_only
def test_theme_keys_match_what_phase_2_writes():
    """A construct name that differs from the pipeline's theme key means
    Concord output cannot be joined to the existing corpus."""
    import glob
    files = sorted(glob.glob(str(paths.OUTPUTS_ROOT / "*" /
                                 "phase2_theme_scores" / "*.json")))
    if not files:
        pytest.skip("no phase-2 outputs on this machine")
    for f in files[:5]:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        scores = d.get("theme_scores") or []
        if scores:
            assert set(scores[0]["themes"].keys()) == set(EC.THEME_KEYS.values())
            return
    pytest.skip("no scored comments found")


@corpus_only
def test_every_theme_has_a_definition_and_subthemes(themes):
    for t in themes:
        assert t["definition"], f"Theme {t['number']} lost its definition"
        assert t["subthemes"], f"Theme {t['number']} lost its sub-themes"
        for s in t["subthemes"]:
            assert s["title"]
            assert s["gloss"], f"{t['key']}/{s['letter']} lost its gloss"


@corpus_only
def test_subtheme_count_is_the_expected_thirteen(themes):
    assert [len(t["subthemes"]) for t in themes] == [3, 3, 4, 3]


@corpus_only
def test_anchor_quotes_are_actually_parsed(themes):
    """The regression this file exists for.

    The codebook's blockquotes are `> *"quote"* <em-dash> Speaker N`. If the
    dash in QUOTE_RE stops matching the dash in the source, this silently drops
    to zero and everything downstream still validates."""
    per_theme = [sum(len(s["quotes"]) for s in t["subthemes"]) for t in themes]
    assert per_theme == [4, 4, 3, 3], (
        f"anchor quote counts changed: {per_theme}. If the codebook was edited "
        f"this is expected -- update the numbers. If it was not, QUOTE_RE has "
        f"stopped matching the source's dash character.")
    assert sum(per_theme) == 14


@corpus_only
def test_quotes_are_speaker_words_not_researcher_paraphrase(themes):
    """The codebook marks some entries '(Paraphrase)'. Those are researcher
    summaries, and using one as a positive example would teach a judge to match
    summaries rather than speech."""
    for t in themes:
        for s in t["subthemes"]:
            for q in s["quotes"]:
                assert "paraphrase" not in q["text"].lower()


@corpus_only
def test_summary_table_is_not_parsed_as_a_theme(themes):
    """The file ends with a '## Summary Table' section whose rows mention every
    theme. Letting it bleed into Theme 4 would attach the whole table to that
    construct's definition."""
    for t in themes:
        assert "Core Question" not in t["definition"]
        assert "|" not in t["definition"]


# ------------------------------------------------------------ constructs

@corpus_only
def test_theme_constructs_are_continuous_on_zero_to_one(themes):
    """Matching phase 2's output shape means the existing corpus can be
    compared directly, without first choosing a threshold."""
    for t in themes:
        c = EC.theme_construct(t)
        assert c["type"] == "continuous"
        assert c["scale"] == {"min": 0.0, "max": 1.0}


@corpus_only
def test_subthemes_become_inclusion_criteria_not_constructs(themes):
    """The deliberate decision recorded in the module docstring."""
    c = EC.theme_construct(themes[0])
    assert len(c["criteria"]["include"]) == len(themes[0]["subthemes"])
    assert any("lectric" in i for i in c["criteria"]["include"])


@corpus_only
def test_analytical_stance_reaches_the_judge(themes):
    """The codebook's most unusual feature is an explicit epistemology: comments
    are situated narratives and their factual accuracy is not assessed. If that
    does not reach the judge, the instrument is not the codebook."""
    c = EC.theme_construct(themes[0])
    joined = " ".join(c["criteria"]["exclude"]).lower()
    assert "factual" in joined or "accuracy" in joined
    assert "situated narrative" in joined


@corpus_only
def test_anchor_quotes_become_positive_examples(themes):
    c = EC.theme_construct(themes[0])
    assert len(c["examples"]) == 4
    for e in c["examples"]:
        assert e["kind"] == "positive"
        assert e["label"] == 1.0
        assert e["text"]


def test_public_comment_construct_is_binary():
    c = EC.public_comment_construct()
    assert c["type"] == "binary"
    assert c["criteria"]["include"] and c["criteria"]["exclude"]
    # The fused-speaker case is the one that matters most for this study.
    assert any("boundar" in e.lower() for e in c["edgeCases"])


def test_constructs_are_marked_human_authored():
    """Concord tracks who authored a construct. Labelling a researcher-written
    codebook as director-drafted would overstate the machine's contribution."""
    c = EC.public_comment_construct()
    assert c["authoredBy"] == "human"
    assert c["humanTouched"] is True


# ------------------------------------------- validation against real Concord

concord_only = pytest.mark.skipif(
    shutil.which("node") is None
    or not (CONCORD / "server" / "core" / "objects.js").is_file(),
    reason="node or the concord checkout is not available",
)


@corpus_only
@concord_only
def test_concord_accepts_every_construct(themes):
    """Checked against Concord's real createConstruct(), not against this
    file's idea of the schema."""
    constructs = [EC.public_comment_construct()] + [
        EC.theme_construct(t) for t in themes]
    errors = EC.validate_with_concord(constructs, CONCORD)
    assert errors == [], f"Concord rejected constructs: {errors}"


@corpus_only
@concord_only
def test_concord_accepts_the_subtheme_variant(themes):
    constructs = [EC.public_comment_construct()]
    for t in themes:
        constructs.append(EC.theme_construct(t))
        constructs += EC.subtheme_constructs(t)
    assert len(constructs) == 18
    assert EC.validate_with_concord(constructs, CONCORD) == []


@concord_only
def test_the_validator_actually_rejects_bad_input():
    """A validator that accepts everything proves nothing. This is the power
    check for test_concord_accepts_every_construct."""
    bad = [{"name": "no_type_here", "definition": "x"}]
    assert EC.validate_with_concord(bad, CONCORD) != []

    worse = [{"name": "bad_type", "type": "not_a_real_type"}]
    assert EC.validate_with_concord(worse, CONCORD) != []
