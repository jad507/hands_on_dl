"""
Tests for chunk_experiment.py.

Two things here are worth guarding.

The corpus selection must be **deterministic and stated**. The experiment's
whole claim is that nothing varies except the batching, and that only holds if
every condition sees the identical block list. A selector that reordered or
re-chose meetings between invocations would break the design silently, because
each condition is a separate process run minutes apart.

And the analysis must not quietly compare a condition against itself, or count a
block that only one condition saw. Either would move the control-vs-effect
ratio, which is the number the finding rests on.

Run:  python -m pytest tests/ -v
"""

import json

import pytest

import chunk_experiment as CE


def blk(bid, start, end, text, speaker="SPEAKER_00"):
    return {"block_id": bid, "speaker": speaker, "category": "recurring",
            "start": start, "end": end, "duration_s": end - start,
            "segment_count": 1, "word_count": len(text.split()), "text": text}


def write_meeting(path, blocks, title=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "title": title or path.stem, "video_id": "V", "upload_date": "20250101",
        "rttm_mode": "standard", "speakers": [], "blocks": blocks}),
        encoding="utf-8")


def write_phase1(path, flagged, blocks):
    by = {b["block_id"]: b for b in blocks}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "title": path.stem, "model": "m", "n_chunk_errors": 0,
        "public_comments": [
            {"block_id": i, "speaker": by[i]["speaker"], "start": by[i]["start"],
             "end": by[i]["end"], "text": by[i]["text"]} for i in sorted(flagged)]}),
        encoding="utf-8")


# ------------------------------------------------------------- selection

@pytest.fixture
def source(tmp_path):
    src = tmp_path / "comments"
    for i in range(20):
        n = 20 + i * 10
        write_meeting(src / f"Meeting {i:02d} [id{i}]_standard.json",
                      [blk(j, j * 10, j * 10 + 9, f"m{i} b{j} some words")
                       for j in range(n)])
        # an _exclusive twin that must never be selected alongside its standard
        write_meeting(src / f"Meeting {i:02d} [id{i}]_exclusive.json",
                      [blk(j, j * 10, j * 10 + 9, f"m{i} b{j} some words")
                       for j in range(n)])
    # too small to be useful
    write_meeting(src / "Tiny [z].json", [blk(0, 0, 5, "hi")])
    return src


def test_selection_is_deterministic(source, tmp_path):
    """Each condition is a separate process minutes apart. If selection varied,
    the conditions would not share a corpus and the design would be void."""
    a = CE.select(source, tmp_path / "a", 8)
    b = CE.select(source, tmp_path / "b", 8)
    assert a == b


def test_selection_takes_only_one_variant_per_meeting(source, tmp_path):
    """A meeting present as both _standard and _exclusive must not enter twice;
    that would weight it double and mix two block lists."""
    chosen = CE.select(source, tmp_path / "c", 10)
    assert not any(s.endswith("_exclusive") for s in chosen)
    bases = [s.replace("_standard", "") for s in chosen]
    assert len(bases) == len(set(bases))


def test_selection_skips_tiny_meetings(source, tmp_path):
    chosen = CE.select(source, tmp_path / "c", 20)
    assert "Tiny [z]" not in chosen


def test_selection_excludes_the_known_stale_files(tmp_path):
    """The two superseded commenter_blocks files shadow meetings already
    present as variant pairs; including one would put a pre-filtered 31-block
    input into an experiment about block context."""
    src = tmp_path / "comments"
    for stem in CE.EXCLUDE:
        write_meeting(src / f"{stem}.json",
                      [blk(j, j * 10, j * 10 + 9, f"b{j} words") for j in range(50)])
    write_meeting(src / "Good [g].json",
                  [blk(j, j * 10, j * 10 + 9, f"b{j} words") for j in range(50)])
    chosen = CE.select(src, tmp_path / "out", 5)
    assert chosen == ["Good [g]"]


def test_selection_writes_a_clean_corpus(source, tmp_path):
    """Re-selecting must not leave meetings from a previous selection behind --
    a stale file would be processed by later conditions but not earlier ones."""
    out = tmp_path / "corpus"
    CE.select(source, out, 10)
    first = {p.name for p in out.glob("*.json")}
    CE.select(source, out, 4)
    second = {p.name for p in out.glob("*.json")}
    assert len(second) == 4
    assert second < first


def test_selection_copies_intact_block_lists(source, tmp_path):
    out = tmp_path / "corpus"
    CE.select(source, out, 3)
    for p in out.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        assert d["blocks"]
        assert all("block_id" in b and "text" in b for b in d["blocks"])


# -------------------------------------------------------------- analysis

@pytest.fixture
def runs(tmp_path):
    """Two conditions with a known difference: A flags {1,2,3}, B flags {2,3,4}
    in each of two meetings. So 2 changed blocks per meeting, 4 total."""
    corpus = tmp_path / "corpus"
    runs_root = tmp_path / "runs"
    for mi in range(2):
        blocks = [blk(j, j * 10, j * 10 + 9, f"m{mi} b{j} text") for j in range(10)]
        write_meeting(corpus / f"m{mi}.json", blocks)
        write_phase1(runs_root / "A_size3_off0" / "mdl" /
                     "phase1_public_comments" / f"m{mi}.json", {1, 2, 3}, blocks)
        write_phase1(runs_root / "B_size3_off1" / "mdl" /
                     "phase1_public_comments" / f"m{mi}.json", {2, 3, 4}, blocks)
    return corpus, runs_root


def test_analysis_counts_symmetric_difference(runs, tmp_path):
    corpus, runs_root = runs
    res = CE.analyse(corpus, runs_root, tmp_path / "out", "mdl")
    row = res["rows"][0]
    assert row["flagged_a"] == 6 and row["flagged_b"] == 6
    assert row["changed"] == 4          # 1 dropped + 4 added, per meeting
    assert row["net"] == 0


def test_analysis_universe_is_all_blocks_not_flagged_ones(runs, tmp_path):
    """The percentage denominator must be every block. Using flagged blocks
    would make the rate depend on how permissive the conditions happened to be."""
    corpus, runs_root = runs
    res = CE.analyse(corpus, runs_root, tmp_path / "out", "mdl")
    row = res["rows"][0]
    assert row["changed_pct"] == pytest.approx(100 * 4 / 20, abs=0.01)


def test_analysis_reports_jaccard_and_chance_corrected_statistics(runs, tmp_path):
    corpus, runs_root = runs
    row = CE.analyse(corpus, runs_root, tmp_path / "out", "mdl")["rows"][0]
    assert row["jaccard"] == pytest.approx(4 / 8, abs=0.01)   # |A&B|=4, |AuB|=8
    assert 0 < row["krippendorff_alpha"] < 1
    assert 0 < row["gwet_ac1"] < 1


def test_identical_conditions_report_zero_change(tmp_path):
    """The control's floor case. If two conditions with identical output ever
    reported a nonzero difference, the measured noise floor would be an
    artefact of the comparison rather than of the pipeline."""
    corpus = tmp_path / "c"
    runs_root = tmp_path / "r"
    blocks = [blk(j, j * 10, j * 10 + 9, f"b{j} text") for j in range(10)]
    write_meeting(corpus / "m.json", blocks)
    for cond in ("A_size3_off0", "A2_size3_off0_repeat"):
        write_phase1(runs_root / cond / "mdl" / "phase1_public_comments" / "m.json",
                     {1, 5}, blocks)
    row = CE.analyse(corpus, runs_root, tmp_path / "out", "mdl")["rows"][0]
    assert row["changed"] == 0
    assert row["jaccard"] == pytest.approx(1.0)


def test_analysis_refuses_a_single_condition(tmp_path):
    """Nothing to compare. Better to stop than to emit an empty report that
    looks like a null result."""
    corpus = tmp_path / "c"
    runs_root = tmp_path / "r"
    blocks = [blk(0, 0, 9, "text")]
    write_meeting(corpus / "m.json", blocks)
    write_phase1(runs_root / "A_size3_off0" / "mdl" / "phase1_public_comments" /
                 "m.json", {0}, blocks)
    with pytest.raises(SystemExit):
        CE.analyse(corpus, runs_root, tmp_path / "out", "mdl")


def test_analysis_writes_its_outputs(runs, tmp_path):
    corpus, runs_root = runs
    out = tmp_path / "out"
    CE.analyse(corpus, runs_root, out, "mdl")
    for name in ("condition_pairs.csv", "changed_blocks.csv",
                 "chunk_experiment_report.md"):
        assert (out / name).exists(), name


def test_report_states_the_condition_c_caveat(runs, tmp_path):
    """A large A-vs-C difference does not mean size 1 is more accurate. That
    inference is the tempting one and the report has to say so in the file, not
    only in someone's memory."""
    corpus, runs_root = runs
    out = tmp_path / "out"
    CE.analyse(corpus, runs_root, out, "mdl")
    text = (out / "chunk_experiment_report.md").read_text(encoding="utf-8").lower()
    assert "accurate" in text and "no human labels" in text


def test_conditions_table_matches_the_runner_script():
    """chunk_experiment.py names the conditions and run_chunk_experiment.ps1
    creates their directories. If the two drift apart, analyse() silently sees
    fewer conditions than were run."""
    from pathlib import Path
    ps1 = (Path(__file__).resolve().parent.parent /
           "run_chunk_experiment.ps1").read_text(encoding="utf-8")
    for name in CE.CONDITIONS:
        assert name in ps1, f"condition {name} is not in the runner script"
