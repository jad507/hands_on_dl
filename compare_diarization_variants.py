r"""
The diarization-variant pilot, and the chunk-framing decomposition it turned up.

Background
----------
26 meetings in `downloads/comments/` exist in two variants, `_standard` and
`_exclusive`, because pyannote was run in two diarization modes over the same
audio. `AITranscribe/docs/isls2027/05-hands-on-dl-upgrade-plan.md` Step 1 calls
mining this "the highest-value work in the entire plan", on the reading that it
is structurally the ISLS experiment one stage earlier in the pipeline: same
audio, different upstream processing, same model, same prompt.

The audit's headline was that flag counts differ on 16 of 26 pairs for
ministral-8b while the aggregate moves only ~1%, and read that as the Southwell
pattern -- aggregate robustness masking unit-level instability.

What this script found, and why the reading changed
---------------------------------------------------
Align the two variants by time (see blockmatch.py) and the premise does not
hold. 97.3% of blocks align one-to-one, and of those, 99.4% have *byte-identical
text*. The two diarization modes barely disagree about what was said; they
disagree about where a handful of turn boundaries fall.

So the instability is real but it is not coming from the transcript. Holding
text byte-identical and asking when a block's classification still flips gives:

    enclosing 3-block chunk identical   ->  0.2% - 1.3% flip rate
    enclosing 3-block chunk shifted     -> 11.7% - 17.1% flip rate

Phase 1 batches blocks `P1_CHUNK_SIZE` (3) at a time and asks the model to judge
the batch, so a single inserted or deleted block upstream shifts every
subsequent chunk boundary and every later block is judged alongside different
neighbours. That batching parameter -- chosen to fit a context window, never
treated as a methodological decision -- determines the coding outcome for
roughly one block in seven.

That is a cleaner result than the one it replaces, because the text is held
byte-identical rather than merely similar, so there is no confound with
transcript content at all. It is also the same argument the ISLS contribution is
making, one layer up: an unexamined step silently fixes a choice the field
considers the researcher's. Here the step is in the analysis harness rather than
the ASR.

The residual flip rate inside identical chunks (0.2-1.3%) is not zero, and it
should not be. Identical chunk plus identical prompt plus temperature 0 ought to
be reproducible; it is not quite, which is the same non-determinism recorded in
`plans/windows_environment_upgrade_status.md` section 3. This script reports it
as its own column rather than folding it into the effect.

Outputs (to --out, default downloads/agreement_analysis/diarization_variants/)
-----------------------------------------------------------------------------
    variant_alignment.csv        per meeting: block counts and alignment shapes
    chunk_framing.csv            the decomposition table above, per model
    flip_detail.csv              every flipped block, with both texts
    theme_score_movement.csv     phase 2: theme vectors for blocks in both variants
    threshold_sensitivity.csv    how the alignment moves with min_iou
    report.md                    the readable summary
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import agreement as AG
import blockmatch as BM
import paths

VARIANT_RE = re.compile(r"^(.*)_(standard|exclusive)$")

# Must match SETTINGS["p1_chunk_size"] in models.yaml. Read from there rather
# than hardcoded, because the entire finding below is about this number.
def _chunk_size(default: int = 3) -> int:
    try:
        import yaml
        cfg = yaml.safe_load(paths.MODELS_CONFIG_PATH.read_text(encoding="utf-8"))
        return int(cfg.get("settings", {}).get("p1_chunk_size", default))
    except Exception:
        return default


def load_json(path: Path | str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"  WARN could not read {path}: {e}", file=sys.stderr)
        return None


def find_variant_pairs(comments_dir: Path) -> dict[str, dict[str, Path]]:
    """Group the corpus into meetings that exist in both diarization variants."""
    groups: dict[str, dict[str, Path]] = defaultdict(dict)
    for p in sorted(Path(comments_dir).glob("*.json")):
        m = VARIANT_RE.match(p.stem)
        if m:
            groups[m.group(1)][m.group(2)] = p
        else:
            groups[p.stem]["plain"] = p
    return {k: v for k, v in groups.items()
            if "standard" in v and "exclusive" in v}


def discover_models(outputs_root: Path) -> list[str]:
    return sorted(d.name for d in Path(outputs_root).iterdir()
                  if (d / "phase1_public_comments").is_dir())


def flagged_ids(path: Path) -> set | None:
    d = load_json(path)
    if d is None:
        return None
    return {c["block_id"] for c in d.get("public_comments", [])
            if c.get("block_id") is not None}


def chunk_of(blocks: list[dict], pos: int, chunk: int) -> list[str]:
    """The texts of the chunk that the block at `pos` was judged inside."""
    c = pos // chunk
    return [b.get("text", "") for b in blocks[c * chunk:(c + 1) * chunk]]


def analyse(comments_dir: Path, outputs_root: Path, out_dir: Path,
            models: list[str] | None, min_iou: float) -> dict:
    chunk = _chunk_size()
    pairs = find_variant_pairs(comments_dir)
    models = models or discover_models(outputs_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"chunk size (p1_chunk_size) : {chunk}")
    print(f"variant pairs found        : {len(pairs)}")
    print(f"models                     : {', '.join(models)}")
    print()

    align_rows: list[dict] = []
    flip_rows: list[dict] = []
    thresh_rows: list[dict] = []
    # model -> bucket -> [n, flips]
    # model -> bucket -> [n_blocks, n_flips, n_flagged_in_either_variant]
    tally: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(lambda: [0, 0, 0]))
    text_stats = {"aligned": 0, "same_text": 0, "diff_text": 0, "unaligned": 0,
                  "blocks_a": 0, "blocks_b": 0}

    for meeting, v in sorted(pairs.items()):
        da, db = load_json(v["standard"]), load_json(v["exclusive"])
        if da is None or db is None:
            continue
        A, B = da.get("blocks", []), db.get("blocks", [])
        al = BM.align(A, B, min_iou=min_iou)
        counts = al.counts()

        by_a = {b["block_id"]: b for b in A}
        by_b = {b["block_id"]: b for b in B}
        pos_a = {b["block_id"]: i for i, b in enumerate(A)}
        pos_b = {b["block_id"]: i for i, b in enumerate(B)}

        same_text = sum(1 for aid, bid in al.map_a_to_b.items()
                        if by_a[aid].get("text") == by_b[bid].get("text"))
        text_stats["blocks_a"] += len(A)
        text_stats["blocks_b"] += len(B)
        text_stats["aligned"] += len(al.map_a_to_b)
        text_stats["same_text"] += same_text
        text_stats["diff_text"] += len(al.map_a_to_b) - same_text
        text_stats["unaligned"] += len(A) - len(al.map_a_to_b)

        align_rows.append({
            "meeting": meeting,
            "blocks_standard": len(A), "blocks_exclusive": len(B),
            "one_to_one": counts["one_to_one"], "split": counts["split"],
            "merge": counts["merge"], "tangle": counts["tangle"],
            "unmatched_standard": counts["unmatched_a"],
            "unmatched_exclusive": counts["unmatched_b"],
            "one_to_one_rate": round(al.one_to_one_rate(), 4),
            "aligned_same_text": same_text,
            "aligned_diff_text": len(al.map_a_to_b) - same_text,
        })

        for r in BM.threshold_sensitivity(A, B):
            thresh_rows.append({"meeting": meeting, **r})

        for model in models:
            ps = Path(outputs_root) / model / "phase1_public_comments" / f"{meeting}_standard.json"
            pe = Path(outputs_root) / model / "phase1_public_comments" / f"{meeting}_exclusive.json"
            if not (ps.exists() and pe.exists()):
                continue
            S, E = flagged_ids(ps), flagged_ids(pe)
            if S is None or E is None:
                continue

            for aid, bid in al.map_a_to_b.items():
                ta = by_a[aid].get("text", "")
                tb = by_b[bid].get("text", "")
                fa, fb = aid in S, bid in E
                flipped = fa != fb
                if ta != tb:
                    bucket = "text_differs"
                else:
                    ia, ib = pos_a[aid], pos_b[bid]
                    same_chunk = (ia % chunk == ib % chunk and
                                  chunk_of(A, ia, chunk) == chunk_of(B, ib, chunk))
                    bucket = "chunk_identical" if same_chunk else "chunk_shifted"
                tally[model][bucket][0] += 1
                tally[model][bucket][1] += flipped
                # Blocks flagged in at least one variant. A model that flags
                # almost nothing cannot flip much, so a low raw flip rate from
                # such a model is a statement about its base rate rather than
                # about its stability. deepseek-r1-14b is exactly this case.
                tally[model][bucket][2] += int(fa or fb)
                if flipped:
                    flip_rows.append({
                        "model": model, "meeting": meeting, "bucket": bucket,
                        "block_id_standard": aid, "block_id_exclusive": bid,
                        "flagged_standard": int(fa), "flagged_exclusive": int(fb),
                        "start": by_a[aid].get("start"),
                        "speaker_standard": by_a[aid].get("speaker"),
                        "speaker_exclusive": by_b[bid].get("speaker"),
                        "text_standard": ta[:300],
                        "text_exclusive": tb[:300],
                    })

            # blocks with no 1:1 partner: structurally incomparable, counted
            # separately so they cannot quietly inflate or deflate the rate
            for aid in al.unmatched_a:
                tally[model]["unaligned"][0] += 1
                tally[model]["unaligned"][2] += int(aid in S)
            for c in al.components:
                if c.shape in ("split", "merge", "tangle"):
                    for aid in c.a_ids:
                        tally[model]["unaligned"][0] += 1
                        tally[model]["unaligned"][2] += int(aid in S)

    _write_csv(out_dir / "variant_alignment.csv", align_rows)
    _write_csv(out_dir / "flip_detail.csv", flip_rows)
    _write_csv(out_dir / "threshold_sensitivity.csv", thresh_rows)

    chunk_rows = []
    for model in models:
        t = tally[model]
        row = {"model": model}
        for bucket in ("chunk_identical", "chunk_shifted", "text_differs", "unaligned"):
            n, f, pos = t[bucket]
            row[f"{bucket}_n"] = n
            row[f"{bucket}_flips"] = f
            row[f"{bucket}_rate"] = round(f / n, 4) if n else None
            row[f"{bucket}_flagged_either"] = pos
            # Instability among positives: of the blocks either variant
            # called a public comment, how many did the two variants
            # disagree about? Insensitive to base rate, so comparable
            # across models that flag at wildly different volumes.
            row[f"{bucket}_rate_among_positives"] = (
                round(f / pos, 4) if pos else None)
        chunk_rows.append(row)
    _write_csv(out_dir / "chunk_framing.csv", chunk_rows)

    theme_rows = compare_theme_scores(pairs, outputs_root, models, min_iou)
    _write_csv(out_dir / "theme_score_movement.csv", theme_rows)

    report = build_report(chunk, pairs, models, text_stats, chunk_rows,
                          align_rows, theme_rows, min_iou)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nwritten to {out_dir}")
    return {"chunk_rows": chunk_rows, "text_stats": text_stats}


def compare_theme_scores(pairs, outputs_root, models, min_iou) -> list[dict]:
    """Phase 2: for comments that survive in both variants, how far does the
    four-dimensional theme-score vector move?

    Restricted to 1:1 aligned blocks with byte-identical text, so any movement
    here is movement in the model's judgement of the same words, not a response
    to different words."""
    rows: list[dict] = []
    for meeting, v in sorted(pairs.items()):
        da, db = load_json(v["standard"]), load_json(v["exclusive"])
        if da is None or db is None:
            continue
        A, B = da.get("blocks", []), db.get("blocks", [])
        al = BM.align(A, B, min_iou=min_iou)
        by_a = {b["block_id"]: b for b in A}
        by_b = {b["block_id"]: b for b in B}

        for model in models:
            ps = Path(outputs_root) / model / "phase2_theme_scores" / f"{meeting}_standard.json"
            pe = Path(outputs_root) / model / "phase2_theme_scores" / f"{meeting}_exclusive.json"
            if not (ps.exists() and pe.exists()):
                continue
            ds, de = load_json(ps), load_json(pe)
            if ds is None or de is None:
                continue
            sc_s = {c["block_id"]: c.get("themes", {}) for c in ds.get("theme_scores", [])}
            sc_e = {c["block_id"]: c.get("themes", {}) for c in de.get("theme_scores", [])}
            for aid, bid in al.map_a_to_b.items():
                if aid not in sc_s or bid not in sc_e:
                    continue
                if by_a[aid].get("text") != by_b[bid].get("text"):
                    continue
                themes = sorted(set(sc_s[aid]) | set(sc_e[bid]))
                for th in themes:
                    a_s = sc_s[aid].get(th, {}).get("score")
                    b_s = sc_e[bid].get(th, {}).get("score")
                    if a_s is None or b_s is None:
                        continue
                    rows.append({
                        "model": model, "meeting": meeting, "theme": th,
                        "block_id_standard": aid, "block_id_exclusive": bid,
                        "score_standard": a_s, "score_exclusive": b_s,
                        "abs_delta": round(abs(float(a_s) - float(b_s)), 4),
                        "crosses_half": int((float(a_s) >= 0.5) != (float(b_s) >= 0.5)),
                    })
    return rows


def build_report(chunk, pairs, models, ts, chunk_rows, align_rows,
                 theme_rows, min_iou) -> str:
    L: list[str] = []
    L.append("# Diarization variants: alignment and the chunk-framing effect\n")
    L.append(f"- Variant pairs analysed: **{len(pairs)}**")
    L.append(f"- Models: {', '.join(models)}")
    L.append(f"- Alignment threshold `min_iou`: {min_iou}")
    L.append(f"- `p1_chunk_size`: **{chunk}**\n")

    L.append("## 1. The two variants barely differ in text\n")
    a = ts["blocks_a"] or 1
    L.append(f"- Blocks (standard side): {ts['blocks_a']}, (exclusive side): {ts['blocks_b']}")
    L.append(f"- Aligned 1:1 by time: {ts['aligned']} ({100*ts['aligned']/a:.1f}%)")
    if ts["aligned"]:
        L.append(f"  - byte-identical text: {ts['same_text']} "
                 f"({100*ts['same_text']/ts['aligned']:.1f}% of aligned)")
        L.append(f"  - text differs: {ts['diff_text']} "
                 f"({100*ts['diff_text']/ts['aligned']:.1f}% of aligned)")
    L.append(f"- No 1:1 partner (split / merge / tangle / unmatched): {ts['unaligned']}\n")
    L.append("The two diarization modes disagree about a small number of turn "
             "boundaries, not about what was said. Any classification instability "
             "between them therefore cannot mostly be a transcript effect.\n")

    L.append("## 2. Where the instability actually comes from\n")
    L.append("Every row below is a block that aligned 1:1 across the two variants. "
             "The first two buckets hold blocks whose text is **byte-identical** in "
             "both; they differ only in whether the 3-block chunk the model judged "
             "them inside was also identical.\n")
    def fmt(x):
        return f"{100*x:.2f}%" if x is not None else "-"

    L.append("| model | chunk identical: flips/n | rate | chunk shifted: flips/n | rate | ratio | flagged either (ident/shift) |")
    L.append("|---|---|---|---|---|---|---|")
    for r in chunk_rows:
        ci, cs = r["chunk_identical_rate"], r["chunk_shifted_rate"]
        ratio = f"{cs/ci:.0f}x" if (ci and cs) else "-"
        L.append(
            f"| {r['model']} | {r['chunk_identical_flips']}/{r['chunk_identical_n']} | "
            f"{fmt(ci)} | {r['chunk_shifted_flips']}/{r['chunk_shifted_n']} | "
            f"{fmt(cs)} | {ratio} | "
            f"{r['chunk_identical_flagged_either']} / {r['chunk_shifted_flagged_either']} |")

    L.append("\nThe last column is why `deepseek-r1-14b` must be read separately "
             "from the rest. Its low shifted-chunk rate is not stability: it flags "
             "almost nothing, so it has almost nothing to flip. Normalising by the "
             "blocks either variant called a public comment removes the base-rate "
             "artefact:\n")
    L.append("| model | chunk identical | chunk shifted |")
    L.append("|---|---|---|")
    for r in chunk_rows:
        L.append(f"| {r['model']} | {fmt(r['chunk_identical_rate_among_positives'])} | "
                 f"{fmt(r['chunk_shifted_rate_among_positives'])} |")
    L.append("\n(Disagreements as a share of blocks flagged in at least one variant.)\n")

    core = [r for r in chunk_rows if r["model"] != "deepseek-r1-14b"]
    ident = [r["chunk_identical_rate"] for r in core if r["chunk_identical_rate"]]
    shift = [r["chunk_shifted_rate"] for r in core if r["chunk_shifted_rate"]]
    if ident and shift:
        L.append(f"Excluding `deepseek-r1-14b`, the identical-chunk flip rate spans "
                 f"{100*min(ident):.2f}%-{100*max(ident):.2f}% and the shifted-chunk rate "
                 f"{100*min(shift):.2f}%-{100*max(shift):.2f}%: a "
                 f"{statistics.mean(shift)/statistics.mean(ident):.0f}x difference on "
                 f"byte-identical input text.\n")
    L.append("`P1_CHUNK_SIZE` was set to fit a context window. On this evidence it "
             "also decides the classification of roughly one block in seven whenever "
             "an upstream change shifts the batching offset.\n")
    L.append("The identical-chunk column is not zero. Identical chunk, identical "
             "prompt and temperature 0 should be reproducible, so that residual is "
             "run-to-run non-determinism -- the same effect recorded in "
             "`plans/windows_environment_upgrade_status.md` section 3. It is reported "
             "separately here rather than folded into the chunk effect.\n")

    if theme_rows:
        L.append("## 3. Phase 2 theme scores on identical text\n")
        by_model: dict[str, list[dict]] = defaultdict(list)
        for r in theme_rows:
            by_model[r["model"]].append(r)
        L.append("| model | scored pairs | mean abs delta | median | share moving | share crossing 0.5 |")
        L.append("|---|---|---|---|---|---|")
        for m in sorted(by_model):
            rs = by_model[m]
            d = [r["abs_delta"] for r in rs]
            moving = sum(1 for x in d if x > 0) / len(d)
            crossing = sum(r["crosses_half"] for r in rs) / len(rs)
            L.append(f"| {m} | {len(rs)} | {statistics.mean(d):.3f} | "
                     f"{statistics.median(d):.3f} | {100*moving:.1f}% | {100*crossing:.1f}% |")
        L.append("\nThese are the same words scored twice. 'Share crossing 0.5' is the "
                 "fraction that would change a binary theme assignment at the "
                 "conventional threshold -- the number to quote when arguing that the "
                 "threshold is a decision rather than a default.\n")

    worst = sorted(align_rows, key=lambda r: r["one_to_one_rate"])[:10]
    L.append("## 4. Meetings where the variants align worst\n")
    L.append("| meeting | blocks (std/exc) | 1:1 | split | merge | tangle | rate |")
    L.append("|---|---|---|---|---|---|---|")
    for r in worst:
        L.append(f"| {r['meeting'][:58]} | {r['blocks_standard']}/{r['blocks_exclusive']} | "
                 f"{r['one_to_one']} | {r['split']} | {r['merge']} | {r['tangle']} | "
                 f"{r['one_to_one_rate']:.3f} |")
    L.append("\nSee `threshold_sensitivity.csv` for how these shapes move with "
             "`min_iou`. The threshold is a researcher degree of freedom and should "
             "be pre-registered before any of these numbers are quoted.\n")
    return "\n".join(L)


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        print(f"  (no rows for {path.name})")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--comments", default=None, help="override comments dir")
    ap.add_argument("--outputs", default=None, help="override llm_outputs root")
    ap.add_argument("--out", default=None, help="output directory")
    ap.add_argument("--models", nargs="*", default=None,
                    help="restrict to these models (default: all found)")
    ap.add_argument("--min-iou", type=float, default=0.10,
                    help="alignment threshold (default 0.10)")
    args = ap.parse_args()

    comments = Path(args.comments) if args.comments else paths.COMMENTS_DIR
    outputs = Path(args.outputs) if args.outputs else paths.OUTPUTS_ROOT
    out = Path(args.out) if args.out else (
        paths.DOWNLOADS_DIR / "agreement_analysis" / "diarization_variants")

    analyse(comments, outputs, out, args.models, args.min_iou)


if __name__ == "__main__":
    main()
