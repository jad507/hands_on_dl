r"""
Draw a stratified gold sample for blind human coding.

Why this exists
---------------
`AITranscribe/docs/isls2027/05-hands-on-dl-upgrade-plan.md` Step 4 calls human
labels "the real bottleneck" and says everything downstream of "how well do
models agree with humans" is blocked on them. There are no per-comment human
labels in this repository. Step 4 Path B is to code a stratified sample of
150-200 blocks yourself, budget 8-12 hours.

This draws that sample. It does three things that a spreadsheet would not.

**It is blind by construction.** The coding sheet contains block text and
nothing else -- no model votes, no theme scores, no stratum label, not even the
ordering. Concord's Calibration Studio exists for exactly this reason, and doc
05 is explicit: "Do not look at model output first." So the script writes two
files. `gold_sample_BLIND.md` is what you code from. `gold_sample_KEY.json` is
sealed until coding is finished; it holds the strata, the model votes and the
join back to the corpus. Opening the key early does not corrupt the data, it
corrupts *you*, and nothing downstream can detect that.

**It stratifies on model disagreement, not on convenience.** Sampling flagged
blocks only would measure agreement on a population selected by the thing being
evaluated. The universe here is every block; strata are the number of core
models that flagged it, 0 through 5. Contested strata are deliberately
oversampled -- that is where the information is -- and because the sampling
probabilities are recorded per stratum, estimates can be reweighted back to the
population afterwards. A convenience sample cannot be.

**It writes its own pre-registration.** Seed, strata, quotas, inclusion rules
and the date, emitted before any coding happens. Doc 05 Step 3.2 asks for the
0.5 theme threshold to be pre-registered because "sweeping it post hoc is a
researcher degree of freedom you are trying to make visible in others". The same
applies to every choice here.

Context blocks
--------------
Each sampled block is shown with its neighbours, marked clearly as context and
not to be coded. This is not a convenience. Doc 05's finding 4 describes block
58 of the Nov-18 budget hearing fusing a councillor's question into the finance
director's answer -- one unit, two speakers. A coder shown that block alone
cannot see it; a coder shown its neighbours can. And since the whole project's
finding is that the surrounding chunk changes the model's answer, showing a
human the same context is the fair comparison rather than a generous one.

Usage
-----
    python sample_gold.py                      # 180 blocks, seed 20260903
    python sample_gold.py --n 200 --seed 7
    python sample_gold.py --context 2
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import paths

CORE_MODELS = ["gemma-4-4b", "ministral-8b", "phi-4",
               "qwen3.5-9b-q6", "qwen3.5-9b-q8"]

# Quotas by number of core models that flagged the block. Contested strata are
# oversampled relative to their frequency: stratum 0 is ~68% of the corpus but
# gets ~14% of the sample, because a block nobody flagged is almost always
# obviously not a public comment and carries little information about where the
# boundary actually lies.
DEFAULT_QUOTAS = {0: 0.14, 1: 0.20, 2: 0.20, 3: 0.20, 4: 0.14, 5: 0.12}

# These must match the keys phase 2 writes into `themes` exactly, or the human
# labels cannot be joined to the model scores. Verified against
# downloads/llm_outputs/*/phase2_theme_scores/*.json, and asserted in
# tests/test_sample_gold.py against the live corpus -- an earlier draft of this
# file said "power_dynamics_inequality", dropping the "and", which would have
# produced a coding sheet whose fourth column joined to nothing.
THEMES = ["municipally_managed_resources", "municipal_process",
          "health_and_well_being", "power_dynamics_and_inequality"]


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_universe(comments_dir: Path, outputs_root: Path, models: list[str]):
    """Every block, with the number of models that flagged it."""
    blocks: dict[tuple[str, int], dict] = {}
    order: dict[str, list] = {}
    votes: dict[tuple[str, int], list[str]] = defaultdict(list)

    flagged_by: dict[str, dict[str, set]] = {}
    for m in models:
        d = outputs_root / m / "phase1_public_comments"
        if not d.is_dir():
            continue
        per: dict[str, set] = {}
        for f in d.glob("*.json"):
            data = load_json(f)
            if data is None:
                continue
            per[f.stem] = {c["block_id"] for c in data.get("public_comments", [])
                           if c.get("block_id") is not None}
        flagged_by[m] = per

    for src in sorted(comments_dir.glob("*.json")):
        data = load_json(src)
        if data is None:
            continue
        bl = data.get("blocks") or data.get("commenter_blocks") or []
        if not bl:
            continue
        meeting = src.stem
        # Only meetings every core model actually coded, or the vote count is
        # not comparable across strata.
        if not all(meeting in flagged_by.get(m, {}) for m in models):
            continue
        order[meeting] = [b["block_id"] for b in bl]
        for b in bl:
            key = (meeting, b["block_id"])
            blocks[key] = {**b, "meeting": meeting,
                           "title": data.get("title", meeting)}
            for m in models:
                if b["block_id"] in flagged_by[m][meeting]:
                    votes[key].append(m)
    return blocks, order, votes


def draw(blocks, votes, n: int, quotas: dict[int, float], seed: int):
    rng = random.Random(seed)
    strata: dict[int, list] = defaultdict(list)
    for key in blocks:
        strata[len(votes.get(key, []))].append(key)
    for k in strata:
        strata[k].sort()                       # determinism before shuffling

    sample: list[tuple] = []
    realised: dict[int, dict] = {}
    for k in sorted(quotas):
        want = int(round(n * quotas[k]))
        pool = strata.get(k, [])
        take = min(want, len(pool))
        chosen = rng.sample(pool, take) if take else []
        sample.extend(chosen)
        realised[k] = {
            "population": len(pool),
            "requested": want,
            "drawn": take,
            "sampling_fraction": round(take / len(pool), 6) if pool else None,
            "inverse_probability_weight": round(len(pool) / take, 4) if take else None,
        }
    rng.shuffle(sample)                        # blind the coder to stratum order
    return sample, realised


def snippet(text: str, limit: int = 240) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= limit else t[:limit] + " ..."


def write_blind(path: Path, sample, blocks, order, context: int) -> None:
    L = [
        "# Gold coding sheet (BLIND)",
        "",
        "Code these blocks **before** looking at any model output. The companion",
        "`gold_sample_KEY.json` holds the model votes and the strata; opening it",
        "first does not corrupt the data, it corrupts you, and nothing downstream",
        "can detect that.",
        "",
        "## What to record, per item",
        "",
        "1. **`public_comment`** -- is the TARGET block a member of the public",
        "   addressing the body? `yes` / `no` / `unsure`.",
        "   Council members, staff, and procedural speech are `no`. A block that",
        "   fuses a public comment with something else is `unsure` -- say so in",
        "   the note, because unit boundaries are part of what is being studied.",
        "2. If `yes`, score each of the four themes **0.0 to 1.0**:",
        "   `municipally_managed_resources`, `municipal_process`,",
        "   `health_and_well_being`, `power_dynamics_and_inequality`.",
        "   Definitions and anchor quotes: `downloads/data_center_comment_themes.md`.",
        "3. **`note`** -- anything that made the judgement hard. These are worth more",
        "   than the labels; they are what a reliability statistic cannot record.",
        "",
        "Context blocks are shown in grey brackets **for orientation only**.",
        "Do not code them.",
        "",
        "Write answers in `gold_coding.csv` (a template is written alongside this",
        "file), keyed by `item`.",
        "",
        "---",
        "",
    ]
    for i, key in enumerate(sample, start=1):
        meeting, bid = key
        b = blocks[key]
        seq = order[meeting]
        pos = seq.index(bid)
        L.append(f"## Item {i}")
        L.append("")
        L.append(f"*{b['title']}*  |  speaker `{b.get('speaker')}`  |  "
                 f"{b.get('start')}s-{b.get('end')}s  |  {b.get('word_count')} words")
        L.append("")
        for off in range(-context, context + 1):
            j = pos + off
            if j < 0 or j >= len(seq):
                continue
            nb = blocks.get((meeting, seq[j]))
            if nb is None:
                continue
            if off == 0:
                L.append("**TARGET --**")
                L.append("")
                L.append("> " + snippet(nb.get("text"), 2000).replace("\n", " "))
                L.append("")
            else:
                tag = "before" if off < 0 else "after"
                L.append(f"<sub>[context {tag}, speaker {nb.get('speaker')}: "
                         f"{snippet(nb.get('text'), 160)}]</sub>")
                L.append("")
        L.append("`public_comment:` ____   `note:` ____")
        L.append("")
        L.append("---")
        L.append("")
    path.write_text("\n".join(L), encoding="utf-8")


def write_template(path: Path, n: int) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "public_comment", *THEMES, "note"])
        for i in range(1, n + 1):
            w.writerow([i, "", "", "", "", "", ""])


def main() -> None:
    ap = argparse.ArgumentParser(description="Draw a blind stratified gold sample.")
    ap.add_argument("--n", type=int, default=180,
                    help="target sample size (default 180; plan says 150-200)")
    ap.add_argument("--seed", type=int, default=20260903)
    ap.add_argument("--context", type=int, default=1,
                    help="neighbouring blocks shown for orientation (default 1)")
    ap.add_argument("--models", nargs="*", default=CORE_MODELS)
    ap.add_argument("--comments", default=None)
    ap.add_argument("--outputs", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    comments = Path(args.comments) if args.comments else paths.COMMENTS_DIR
    outputs = Path(args.outputs) if args.outputs else paths.OUTPUTS_ROOT
    out = Path(args.out) if args.out else paths.DOWNLOADS_DIR / "gold_sample"
    out.mkdir(parents=True, exist_ok=True)

    blocks, order, votes = build_universe(comments, outputs, args.models)
    print(f"universe: {len(blocks)} blocks over {len(order)} meetings")
    dist = Counter(len(votes.get(k, [])) for k in blocks)
    for k in sorted(dist):
        print(f"  {k} of {len(args.models)} models flagged: {dist[k]}")

    sample, realised = draw(blocks, votes, args.n, DEFAULT_QUOTAS, args.seed)
    print(f"\ndrawn: {len(sample)} blocks")

    write_blind(out / "gold_sample_BLIND.md", sample, blocks, order, args.context)
    write_template(out / "gold_coding.csv", len(sample))

    key = {
        "generated": date.today().isoformat(),
        "seed": args.seed,
        "n_requested": args.n,
        "n_drawn": len(sample),
        "models": args.models,
        "context_blocks": args.context,
        "quotas": DEFAULT_QUOTAS,
        "strata": realised,
        "items": [
            {"item": i, "meeting": m, "block_id": b,
             "speaker": blocks[(m, b)].get("speaker"),
             "start": blocks[(m, b)].get("start"),
             "end": blocks[(m, b)].get("end"),
             "n_votes": len(votes.get((m, b), [])),
             "models_voting_yes": sorted(votes.get((m, b), []))}
            for i, (m, b) in enumerate(sample, start=1)
        ],
    }
    (out / "gold_sample_KEY.json").write_text(
        json.dumps(key, indent=2, ensure_ascii=False), encoding="utf-8")

    prereg = f"""# Pre-registration: gold coding sample

**Written:** {date.today().isoformat()}, before any coding.

Recorded now so that none of it can be adjusted after seeing results. Doc 05
Step 3.2 asks for the theme threshold to be pre-registered because "sweeping it
post hoc is a researcher degree of freedom you are trying to make visible in
others"; the same applies to every choice below.

## Sampling

- Universe: all {len(blocks)} blocks in {len(order)} meetings coded by all
  {len(args.models)} core models. Blocks, not flagged blocks: sampling only
  flagged blocks would select on the outcome being evaluated.
- Excluded: meetings any core model did not code, so vote counts are comparable.
- Strata: number of core models that flagged the block, 0 to {len(args.models)}.
- Seed: `{args.seed}`. Sample order shuffled so stratum is not inferable from position.
- Quotas and realised draw:

| stratum | population | requested | drawn | sampling fraction | IPW |
|---|---|---|---|---|---|
""" + "\n".join(
        f"| {k} | {v['population']} | {v['requested']} | {v['drawn']} | "
        f"{v['sampling_fraction']} | {v['inverse_probability_weight']} |"
        for k, v in sorted(realised.items())
    ) + f"""

Contested strata are deliberately oversampled. Because the sampling fraction per
stratum is recorded, population estimates must be computed with the inverse
probability weights above; unweighted proportions from this sample describe the
sample only.

## Analysis decisions, fixed in advance

1. **Phase-1 agreement** between human and model is computed over the full
   sample with Krippendorff's alpha (nominal) and Gwet's AC1, reported together.
   `unsure` is treated as missing, not as `no`.
2. **Phase-2 threshold is 0.5** for converting continuous theme scores to binary
   assignments. Chosen before seeing any human score. A sensitivity sweep over
   0.3-0.7 will be reported as a robustness check, not as the headline.
3. **Primary statistic is per-theme**, not pooled across the four themes.
4. **`deepseek-r1-7b` and `deepseek-r1-14b` are excluded** from the core
   comparison, on the pre-existing grounds that both phase-1 runs failed in
   opposite directions (8,882 vs 195 blocks flagged).
5. **Blocks the coder marks as fusing two speakers** are analysed separately and
   reported as a unitization finding rather than dropped.
6. Stopping rule: all {len(sample)} items are coded before any agreement
   statistic is computed. No interim looks.

## Blinding

`gold_sample_KEY.json` is not opened until `gold_coding.csv` is complete. The
coding sheet contains no model output, no stratum labels and no vote counts.
"""
    (out / "PREREGISTRATION.md").write_text(prereg, encoding="utf-8")

    print(f"\nwritten to {out}")
    print("  gold_sample_BLIND.md   <- code from this")
    print("  gold_coding.csv        <- write answers here")
    print("  PREREGISTRATION.md     <- read before starting")
    print("  gold_sample_KEY.json   <- DO NOT OPEN until coding is done")


if __name__ == "__main__":
    main()
