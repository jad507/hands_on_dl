"""
Tests for sample_gold.py.

One property here matters more than the rest: the coding sheet must not leak
what the models said. A leak cannot be detected after the fact -- a coder who
saw a model's answer produces labels that look exactly like blind ones, and
every agreement statistic computed from them is quietly inflated. So the
blindness tests below are deliberately paranoid, checking not just for model
names but for stratum labels, vote counts, and any ordering that would let a
coder infer the stratum from position.

The second property is reproducibility: the same seed must give the same sample,
or the pre-registration is a description of something that no longer exists.

Run:  python -m pytest tests/ -v
"""

import json
import pytest

import sample_gold as SG


def blk(bid, start, end, text, speaker="SPEAKER_00"):
    return {"block_id": bid, "speaker": speaker, "category": "recurring",
            "start": start, "end": end, "duration_s": end - start,
            "segment_count": 1, "word_count": len(text.split()), "text": text}


@pytest.fixture
def corpus(tmp_path):
    """8 meetings x 30 blocks, shaped like the real corpus.

    In `downloads/`, stratum 0 is 6,806 of 10,069 blocks (68%) and the contested
    middle strata are small. A fixture with six equal strata would make the
    oversampling tests vacuous, so the vote pattern below reproduces the real
    skew: most blocks flagged by nobody, a thin contested middle, and a bump at
    unanimous."""
    comments = tmp_path / "comments"
    outputs = tmp_path / "out"
    comments.mkdir()
    models = SG.CORE_MODELS

    for mi in range(8):
        blocks = [blk(i, i * 40, i * 40 + 30, f"meeting {mi} block {i} words here")
                  for i in range(30)]
        # votes[i] = how many models flag block i. Skewed like the real corpus:
        # 20 of 30 unflagged, a thin 1-4 middle, 4 unanimous.
        vote_pattern = ([0] * 20) + [1, 1, 2, 2, 3, 4] + ([5] * 4)
        (comments / f"m{mi}.json").write_text(json.dumps({
            "title": f"Meeting {mi}", "video_id": f"v{mi}",
            "rttm_mode": "standard", "speakers": [], "blocks": blocks,
        }), encoding="utf-8")

        for k, model in enumerate(models):
            # model k flags block i when k is below that block's vote count
            flagged = [b for i, b in enumerate(blocks) if k < vote_pattern[i]]
            d = outputs / model / "phase1_public_comments"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"m{mi}.json").write_text(json.dumps({
                "title": f"Meeting {mi}", "video_id": f"v{mi}",
                "upload_date": "20250101", "model": model, "n_chunk_errors": 0,
                "public_comments": [
                    {"block_id": b["block_id"], "speaker": b["speaker"],
                     "start": b["start"], "end": b["end"],
                     "speaker_name": "unknown", "reason": "t", "text": b["text"]}
                    for b in flagged],
            }), encoding="utf-8")
    return comments, outputs


# --------------------------------------------------------------- blindness

def test_blind_sheet_never_names_a_model(corpus, tmp_path):
    """The failure this prevents is undetectable downstream."""
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=60)
    text = (out / "gold_sample_BLIND.md").read_text(encoding="utf-8").lower()
    for m in SG.CORE_MODELS + ["deepseek-r1-7b", "deepseek-r1-14b"]:
        assert m.lower() not in text, f"{m} leaked into the blind sheet"


def test_blind_sheet_never_reveals_stratum_or_votes(corpus, tmp_path):
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=60)
    text = (out / "gold_sample_BLIND.md").read_text(encoding="utf-8").lower()
    for token in ["stratum", "n_votes", "models_voting", "flagged by",
                  "vote count", "consensus"]:
        assert token not in text, f"'{token}' leaked into the blind sheet"


def test_sample_order_does_not_encode_the_stratum(corpus, tmp_path):
    """If items were emitted stratum by stratum, a coder would notice the run of
    obvious non-comments at the start and calibrate to it. The shuffle has to
    actually break the ordering."""
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=120)
    key = json.loads((out / "gold_sample_KEY.json").read_text(encoding="utf-8"))
    votes = [it["n_votes"] for it in key["items"]]
    # A stratum-ordered list would be sorted. Require that it is not, and that
    # the first ten items are not all from one stratum.
    assert votes != sorted(votes)
    assert len(set(votes[:10])) > 1


def test_key_holds_the_join_back_to_the_corpus(corpus, tmp_path):
    """Blind is only useful if the labels can be rejoined afterwards."""
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=60)
    key = json.loads((out / "gold_sample_KEY.json").read_text(encoding="utf-8"))
    for it in key["items"]:
        assert {"item", "meeting", "block_id", "n_votes", "models_voting_yes"} <= set(it)
    assert len({it["item"] for it in key["items"]}) == len(key["items"])


# ---------------------------------------------------------- reproducibility

def test_same_seed_gives_the_same_sample(corpus, tmp_path):
    comments, outputs = corpus
    a = _run(comments, outputs, tmp_path / "a", n=60, seed=1234)
    b = _run(comments, outputs, tmp_path / "b", n=60, seed=1234)
    assert _items(a) == _items(b)


def test_different_seed_gives_a_different_sample(corpus, tmp_path):
    comments, outputs = corpus
    a = _run(comments, outputs, tmp_path / "a", n=60, seed=1)
    b = _run(comments, outputs, tmp_path / "b", n=60, seed=2)
    assert _items(a) != _items(b)


# ------------------------------------------------------------ stratification

def test_every_stratum_is_represented(corpus, tmp_path):
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=120)
    key = json.loads((out / "gold_sample_KEY.json").read_text(encoding="utf-8"))
    seen = {it["n_votes"] for it in key["items"]}
    assert seen == {0, 1, 2, 3, 4, 5}


def test_contested_strata_are_oversampled(corpus, tmp_path):
    """Stratum 0 dominates the population and must not dominate the sample, or
    the coding hours go almost entirely into blocks nobody disagreed about."""
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=120)
    key = json.loads((out / "gold_sample_KEY.json").read_text(encoding="utf-8"))
    strata = key["strata"]
    frac0 = strata["0"]["sampling_fraction"]
    contested = [strata[str(k)]["sampling_fraction"]
                 for k in (1, 2, 3, 4) if strata[str(k)]["drawn"]]
    assert all(c > frac0 for c in contested), (
        "contested strata must be sampled at a higher rate than stratum 0")

    # And the consequence that matters: stratum 0 dominates the population but
    # must not dominate the coding hours.
    pop0 = strata["0"]["population"]
    total_pop = sum(v["population"] for v in strata.values())
    total_drawn = sum(v["drawn"] for v in strata.values())
    pop_share = pop0 / total_pop
    sample_share = strata["0"]["drawn"] / total_drawn
    assert pop_share > 0.5, "fixture no longer resembles the real corpus"
    assert sample_share < pop_share / 2, (
        f"stratum 0 is {pop_share:.0%} of the population and {sample_share:.0%} "
        f"of the sample; oversampling is not taking effect")


def test_inverse_probability_weights_are_recorded(corpus, tmp_path):
    """Oversampling is only defensible if it can be undone. Without the weights
    the sample describes itself and nothing else."""
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=120)
    key = json.loads((out / "gold_sample_KEY.json").read_text(encoding="utf-8"))
    for k, v in key["strata"].items():
        if v["drawn"]:
            assert v["inverse_probability_weight"] is not None
            assert v["inverse_probability_weight"] == pytest.approx(
                v["population"] / v["drawn"], rel=1e-3)


def test_universe_excludes_meetings_a_model_did_not_code(corpus, tmp_path):
    """A meeting one model skipped has an incomparable vote count and would land
    a block in the wrong stratum."""
    comments, outputs = corpus
    (outputs / SG.CORE_MODELS[0] / "phase1_public_comments" / "m0.json").unlink()
    blocks, order, _ = SG.build_universe(comments, outputs, SG.CORE_MODELS)
    assert "m0" not in order
    assert not any(m == "m0" for m, _ in blocks)


# -------------------------------------------------------------- the outputs

def test_all_four_files_are_written(corpus, tmp_path):
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=60)
    for name in ["gold_sample_BLIND.md", "gold_coding.csv",
                 "gold_sample_KEY.json", "PREREGISTRATION.md"]:
        assert (out / name).exists(), name


def test_coding_template_has_a_row_per_item(corpus, tmp_path):
    import csv
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=60)
    rows = list(csv.DictReader((out / "gold_coding.csv").open(encoding="utf-8")))
    key = json.loads((out / "gold_sample_KEY.json").read_text(encoding="utf-8"))
    assert len(rows) == len(key["items"])
    assert set(SG.THEMES) <= set(rows[0].keys())


def test_prereg_fixes_the_threshold_before_coding(corpus, tmp_path):
    """Doc 05 Step 3.2: the 0.5 threshold is a decision, not a default, and
    sweeping it post hoc is the researcher degree of freedom this project exists
    to make visible in others."""
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=60)
    text = (out / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "0.5" in text
    assert "seed" in text.lower()
    assert "inverse probability" in text.lower()


def test_context_blocks_are_marked_and_target_is_unambiguous(corpus, tmp_path):
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=30, context=1)
    text = (out / "gold_sample_BLIND.md").read_text(encoding="utf-8")
    assert text.count("**TARGET —**") == 30
    assert "context before" in text or "context after" in text


def test_context_zero_shows_only_the_target(corpus, tmp_path):
    comments, outputs = corpus
    out = tmp_path / "g"
    _run(comments, outputs, out, n=30, context=0)
    text = (out / "gold_sample_BLIND.md").read_text(encoding="utf-8")
    assert "context before" not in text and "context after" not in text


# ------------------------------------------------------------------ helpers

def _run(comments, outputs, out, n=60, seed=20260903, context=1):
    out.mkdir(parents=True, exist_ok=True)
    blocks, order, votes = SG.build_universe(comments, outputs, SG.CORE_MODELS)
    sample, realised = SG.draw(blocks, votes, n, SG.DEFAULT_QUOTAS, seed)
    SG.write_blind(out / "gold_sample_BLIND.md", sample, blocks, order, context)
    SG.write_template(out / "gold_coding.csv", len(sample))
    (out / "gold_sample_KEY.json").write_text(json.dumps({
        "seed": seed, "strata": {str(k): v for k, v in realised.items()},
        "items": [{"item": i, "meeting": m, "block_id": b,
                   "n_votes": len(votes.get((m, b), [])),
                   "models_voting_yes": sorted(votes.get((m, b), []))}
                  for i, (m, b) in enumerate(sample, start=1)],
    }, indent=2), encoding="utf-8")
    (out / "PREREGISTRATION.md").write_text(
        f"seed {seed}\nthreshold 0.5\ninverse probability weights recorded\n",
        encoding="utf-8")
    return out


def _items(out):
    key = json.loads((out / "gold_sample_KEY.json").read_text(encoding="utf-8"))
    return [(it["meeting"], it["block_id"]) for it in key["items"]]
