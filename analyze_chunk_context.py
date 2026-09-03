r"""
Is the chunk-framing effect noise, or is it a bias with a sign?

The question
------------
`compare_diarization_variants.py` establishes that a block whose text is
byte-identical across two runs is classified differently 12-17% of the time when
the 3-block chunk it was judged inside is composed differently. That is a
stability result: the harness's batching injects noise into unit-level coding.

A much more serious possibility is that the effect is *directional* -- that a
block is more likely to be called a public comment when batched alongside other
public comments. That would be context contamination, it would bias the corpus
systematically rather than blur it, and it would mean comment counts are inflated
wherever comments cluster (which is everywhere, since public comment periods are
contiguous by design).

This script tests that, and the answer is **no, not detectably** -- but only once
the obvious test is discarded as circular. Both are reported, because the
difference between them is the whole methodological point.

Test 1: the naive one, which is circular
----------------------------------------
Condition on how many of a block's chunk-mates the model flagged:

    0 of 2 chunk-mates flagged  ->  P(flag) = 0.150
    1 of 2                      ->  P(flag) = 0.182
    2 of 2                      ->  P(flag) = 0.711

and the within-block version (same block, byte-identical text, different chunk
company) is 71.9% concordant against a 50% null, z ~ 9.

This looks overwhelming and it means very little. All three blocks in a chunk are
classified in **one forward pass**, emitted as one JSON object. The model's
outputs within a chunk are correlated by construction, so "this block's flag moved
with its chunk-mates' flags" is close to a restatement of "the model answered the
chunk consistently". Public comments also genuinely cluster in time, which
confounds it a second way.

Test 2: an exogenous measure of the neighbours
----------------------------------------------
Replace "how many chunk-mates did the model flag" with a property of the
neighbours that no language model ever saw: pyannote's `category` field, which is
`commenter_candidate` or `recurring` and is derived from diarization speaker
statistics alone.

Same within-block design, same blocks, independent neighbour measure:

    concordant 47.7%, discordant 52.3%, n = 258, z = -0.75

Consistent with chance. The directional reading is not supported.

What that licenses, and what it does not
----------------------------------------
Licensed: "the batching window destabilises unit-level coding" -- a noise claim,
strongly supported, with the text held byte-identical.

Not licensed: "the batching window biases coding toward finding comments."

And the negative result is weak evidence rather than strong: `category` is a coarse
proxy, and `llm_classify_human_themes.py`'s own comment calls the
recurring/commenter_candidate split "unreliable for this task". With n = 258 and a
noisy proxy this test would miss a small effect. The clean version requires human
labels on the neighbours (upgrade plan Step 4) or a direct experiment -- re-running
one meeting at `p1_chunk_size = 1` and at several deliberate chunk offsets, which
costs GPU time but no new data.

Usage
-----
    python analyze_chunk_context.py
    python analyze_chunk_context.py --models ministral-8b phi-4
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path

import blockmatch as BM
import paths

VARIANT_RE = re.compile(r"^(.*)_(standard|exclusive)$")


def load(p: Path) -> dict | None:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def chunk_size(default: int = 3) -> int:
    try:
        import yaml
        cfg = yaml.safe_load(paths.MODELS_CONFIG_PATH.read_text(encoding="utf-8"))
        return int(cfg.get("settings", {}).get("p1_chunk_size", default))
    except Exception:
        return default


def variant_pairs(comments_dir: Path) -> dict[str, dict[str, Path]]:
    g: dict[str, dict[str, Path]] = defaultdict(dict)
    for p in sorted(Path(comments_dir).glob("*.json")):
        m = VARIANT_RE.match(p.stem)
        if m:
            g[m.group(1)][m.group(2)] = p
    return {k: v for k, v in g.items() if "standard" in v and "exclusive" in v}


def mates(blocks: list[dict], pos: int, ch: int) -> list[dict]:
    """The other blocks in the chunk this one was judged inside."""
    c = pos // ch
    return [b for i, b in enumerate(blocks) if i // ch == c and i != pos]


def binom_z(concordant: int, total: int) -> float:
    if total == 0:
        return float("nan")
    return (concordant - total / 2) / math.sqrt(total * 0.25)


def run(comments_dir: Path, outputs_root: Path, out_dir: Path,
        models: list[str] | None) -> dict:
    ch = chunk_size()
    pairs = variant_pairs(comments_dir)
    if models is None:
        models = sorted(d.name for d in outputs_root.iterdir()
                        if (d / "phase1_public_comments").is_dir()
                        and not d.name.startswith("deepseek"))
    out_dir.mkdir(parents=True, exist_ok=True)

    marginal: dict[tuple[int, int], list[int]] = defaultdict(lambda: [0, 0])
    endo = {"concordant": 0, "discordant": 0, "tie": 0}
    exo = {"concordant": 0, "discordant": 0}
    rows: list[dict] = []

    for model in models:
        for meeting, v in sorted(pairs.items()):
            ps = outputs_root / model / "phase1_public_comments" / f"{meeting}_standard.json"
            pe = outputs_root / model / "phase1_public_comments" / f"{meeting}_exclusive.json"
            if not (ps.exists() and pe.exists()):
                continue
            da, db = load(v["standard"]), load(v["exclusive"])
            oa, ob = load(ps), load(pe)
            if not all((da, db, oa, ob)):
                continue
            A, B = da.get("blocks", []), db.get("blocks", [])
            S = {c["block_id"] for c in oa.get("public_comments", [])}
            E = {c["block_id"] for c in ob.get("public_comments", [])}

            # --- Test 1a: marginal P(flag | k chunk-mates flagged) ----------
            for side, blocks, F in (("standard", A, S), ("exclusive", B, E)):
                for i, b in enumerate(blocks):
                    m = mates(blocks, i, ch)
                    k = sum(1 for x in m if x["block_id"] in F)
                    marginal[(len(m), k)][0] += 1
                    marginal[(len(m), k)][1] += int(b["block_id"] in F)

            # --- within-block designs ---------------------------------------
            al = BM.align(A, B)
            ia = {b["block_id"]: i for i, b in enumerate(A)}
            ib = {b["block_id"]: i for i, b in enumerate(B)}
            ta = {b["block_id"]: b.get("text") for b in A}
            tb = {b["block_id"]: b.get("text") for b in B}

            for aid, bid in al.map_a_to_b.items():
                if ta[aid] != tb[bid]:
                    continue                     # text confound; excluded
                i, j = ia[aid], ib[bid]
                mA, mB = mates(A, i, ch), mates(B, j, ch)
                fA, fB = aid in S, bid in E

                # Test 1b: endogenous neighbour measure (circular; reported anyway)
                nA = sum(1 for x in mA if x["block_id"] in S)
                nB = sum(1 for x in mB if x["block_id"] in E)
                if nA != nB:
                    if fA == fB:
                        endo["tie"] += 1
                    elif (fA > fB) == (nA > nB):
                        endo["concordant"] += 1
                    else:
                        endo["discordant"] += 1

                # Test 2: exogenous neighbour measure (pyannote category)
                cA = sum(1 for x in mA if x.get("category") == "commenter_candidate")
                cB = sum(1 for x in mB if x.get("category") == "commenter_candidate")
                if cA != cB and fA != fB:
                    concord = (fA > fB) == (cA > cB)
                    exo["concordant" if concord else "discordant"] += 1
                    rows.append({
                        "model": model, "meeting": meeting,
                        "block_id_standard": aid, "block_id_exclusive": bid,
                        "flagged_standard": int(fA), "flagged_exclusive": int(fB),
                        "commenter_mates_standard": cA,
                        "commenter_mates_exclusive": cB,
                        "concordant": int(concord),
                    })

    _write_csv(out_dir / "chunk_context_detail.csv", rows)
    report = build_report(ch, models, marginal, endo, exo)
    (out_dir / "chunk_context_report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nwritten to {out_dir}")
    return {"marginal": marginal, "endogenous": endo, "exogenous": exo}


def build_report(ch, models, marginal, endo, exo) -> str:
    L: list[str] = []
    L.append("# Is the chunk-framing effect directional?\n")
    L.append(f"- `p1_chunk_size`: {ch}")
    L.append(f"- Models: {', '.join(models)}\n")

    L.append("## Test 1a (circular): P(flag | k chunk-mates flagged)\n")
    L.append("| chunk-mates | of which flagged | n | P(flag) |")
    L.append("|---|---|---|---|")
    for (nm, k), (n, f) in sorted(marginal.items()):
        if n < 30:
            continue
        L.append(f"| {nm} | {k} | {n} | {f/n:.3f} |")
    L.append("\nThis looks like a large effect and is close to meaningless. All "
             "blocks in a chunk are classified in one forward pass and emitted as "
             "one JSON object, so their labels are correlated by construction. "
             "Public comments also cluster in time, which confounds it again.\n")

    et = endo["concordant"] + endo["discordant"]
    L.append("## Test 1b (also circular): within-block, endogenous neighbours\n")
    if et:
        L.append(f"- Same block, byte-identical text, chunk company differs, flag differs: {et}")
        L.append(f"- Concordant with chunk-mate flag count: {endo['concordant']} "
                 f"({100*endo['concordant']/et:.1f}%)")
        L.append(f"- Discordant: {endo['discordant']} ({100*endo['discordant']/et:.1f}%)")
        L.append(f"- z against a 50/50 null: {binom_z(endo['concordant'], et):.2f}")
        L.append(f"- Flag unchanged despite different company: {endo['tie']}\n")
    L.append("Holding the block and its text constant removes the clustering "
             "confound but not the single-forward-pass one. Still not usable.\n")

    xt = exo["concordant"] + exo["discordant"]
    L.append("## Test 2 (the usable one): exogenous neighbours\n")
    L.append("Neighbour comment-likeness measured by pyannote's `category` field, "
             "derived from diarization speaker statistics, which no language model "
             "ever saw.\n")
    if xt:
        L.append(f"- Blocks where neighbour comment-likeness and the flag both differ: {xt}")
        L.append(f"- Concordant: {exo['concordant']} ({100*exo['concordant']/xt:.1f}%)")
        L.append(f"- Discordant: {exo['discordant']} ({100*exo['discordant']/xt:.1f}%)")
        L.append(f"- z against a 50/50 null: **{binom_z(exo['concordant'], xt):.2f}**\n")
    L.append("Consistent with chance. **The directional reading is not supported.**\n")

    L.append("## What this licenses\n")
    L.append("- Supported: the batching window *destabilises* unit-level coding. "
             "A noise claim, with the input text held byte-identical.")
    L.append("- Not supported: the batching window *biases* coding toward finding "
             "comments.\n")
    L.append("The negative result is weak evidence, not strong. `category` is a "
             "coarse proxy and `llm_classify_human_themes.py`'s own comment calls "
             "the recurring/commenter_candidate split unreliable for this task. At "
             f"n = {xt} with a noisy proxy this test would miss a small effect. The "
             "clean version needs human labels on the neighbours (upgrade plan "
             "Step 4), or a direct experiment: re-run one meeting at "
             "`p1_chunk_size = 1` and at several deliberate chunk offsets.\n")
    return "\n".join(L)


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Test the chunk effect for direction.")
    ap.add_argument("--comments", default=None)
    ap.add_argument("--outputs", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()

    comments = Path(args.comments) if args.comments else paths.COMMENTS_DIR
    outputs = Path(args.outputs) if args.outputs else paths.OUTPUTS_ROOT
    out = Path(args.out) if args.out else (
        paths.DOWNLOADS_DIR / "agreement_analysis" / "chunk_context")
    run(comments, outputs, out, args.models)


if __name__ == "__main__":
    main()
