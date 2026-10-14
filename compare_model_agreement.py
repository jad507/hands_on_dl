"""
Cross-model agreement analysis for Phase 1 public-comment extraction.

All models classified the same source blocks (shared block_id space per
meeting), so agreement is computed at the block level:
  - For each meeting, collect the set of block_ids each model marked as a
    public comment.
  - Compute pairwise Jaccard similarity between models.
  - Compute per-block vote counts (how many of the 7 models flagged it).
  - Rank meetings by disagreement (share of flagged blocks that are NOT
    unanimous) to produce a manual-review priority list.

Outputs (to OUT_DIR):
  - model_agreement_report.md   : human-readable summary
  - pairwise_jaccard.csv        : model x model mean Jaccard matrix
  - meeting_disagreement.csv    : per-meeting stats, sorted worst-first
  - contested_blocks.csv        : every block flagged by some-but-not-all
                                  models, with text snippet and which models
                                  voted for it
"""

import csv
import glob
import json
import os
from collections import defaultdict
from itertools import combinations

LLM_OUTPUTS = os.environ.get(
    "LLM_OUTPUTS", r"downloads/llm_outputs")
COMMENTS_DIR = os.environ.get(
    "COMMENTS_DIR", r"downloads/comments")
OUT_DIR = os.environ.get("OUT_DIR", "agreement_analysis")

os.makedirs(OUT_DIR, exist_ok=True)

models = sorted(
    d for d in os.listdir(LLM_OUTPUTS)
    if os.path.isdir(os.path.join(LLM_OUTPUTS, d, "phase1_public_comments"))
)

# meeting -> model -> set(block_id); also keep comment text for snippets
flags = defaultdict(dict)
block_text = {}          # (meeting, block_id) -> text snippet
block_speaker = {}

for m in models:
    for f in glob.glob(os.path.join(LLM_OUTPUTS, m,
                                    "phase1_public_comments", "*.json")):
        meeting = os.path.splitext(os.path.basename(f))[0]
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"WARN could not load {f}: {e}")
            continue
        ids = set()
        for c in d.get("public_comments", []):
            bid = c.get("block_id")
            if bid is None:
                continue
            ids.add(bid)
            key = (meeting, bid)
            if key not in block_text:
                block_text[key] = (c.get("text") or "")[:160]
                block_speaker[key] = c.get("speaker_name") or c.get("speaker") or ""
        flags[meeting][m] = ids

meetings = sorted(flags)
print(f"models: {models}")
print(f"meetings: {len(meetings)}")

# ---- pairwise Jaccard (macro-averaged over meetings where both ran) ----
pair_scores = defaultdict(list)
for meeting in meetings:
    mm = flags[meeting]
    for a, b in combinations(models, 2):
        if a not in mm or b not in mm:
            continue
        A, B = mm[a], mm[b]
        if not A and not B:
            continue  # both empty: skip (undefined Jaccard, trivial agreement)
        pair_scores[(a, b)].append(len(A & B) / len(A | B))

jac = {p: (sum(v) / len(v) if v else float("nan"))
       for p, v in pair_scores.items()}

with open(os.path.join(OUT_DIR, "pairwise_jaccard.csv"), "w", newline="",
          encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow([""] + models)
    for a in models:
        row = [a]
        for b in models:
            if a == b:
                row.append("1.000")
            else:
                p = (a, b) if (a, b) in jac else (b, a)
                row.append(f"{jac.get(p, float('nan')):.3f}")
        w.writerow(row)

# ---- per-block votes and per-meeting disagreement ----
meeting_rows = []
contested_rows = []
for meeting in meetings:
    mm = flags[meeting]
    n_models = len(mm)
    votes = defaultdict(list)
    for m, ids in mm.items():
        for bid in ids:
            votes[bid].append(m)
    n_blocks = len(votes)
    unanimous = sum(1 for v in votes.values() if len(v) == n_models)
    contested = n_blocks - unanimous
    majority = sum(1 for v in votes.values() if len(v) > n_models / 2)
    meeting_rows.append({
        "meeting": meeting,
        "models_ran": n_models,
        "blocks_flagged_by_any": n_blocks,
        "unanimous": unanimous,
        "contested": contested,
        "majority_agreed": majority,
        "contested_share": round(contested / n_blocks, 3) if n_blocks else 0.0,
    })
    for bid, vlist in sorted(votes.items()):
        if 0 < len(vlist) < n_models:
            contested_rows.append({
                "meeting": meeting,
                "block_id": bid,
                "votes": len(vlist),
                "of": n_models,
                "models_voting_yes": ";".join(sorted(vlist)),
                "speaker": block_speaker.get((meeting, bid), ""),
                "text_snippet": block_text.get((meeting, bid), ""),
            })

meeting_rows.sort(key=lambda r: (-r["contested_share"], -r["contested"]))

with open(os.path.join(OUT_DIR, "meeting_disagreement.csv"), "w",
          newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(meeting_rows[0].keys()))
    w.writeheader()
    w.writerows(meeting_rows)

with open(os.path.join(OUT_DIR, "contested_blocks.csv"), "w", newline="",
          encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(contested_rows[0].keys()))
    w.writeheader()
    w.writerows(contested_rows)

# ---- summary report ----
total_blocks = sum(r["blocks_flagged_by_any"] for r in meeting_rows)
total_unanimous = sum(r["unanimous"] for r in meeting_rows)
total_contested = sum(r["contested"] for r in meeting_rows)
total_majority = sum(r["majority_agreed"] for r in meeting_rows)

# per-model totals + agreement with majority vote
model_total = defaultdict(int)
model_majority_hit = defaultdict(int)
majority_block_count = 0
for meeting in meetings:
    mm = flags[meeting]
    n_models = len(mm)
    votes = defaultdict(int)
    for m, ids in mm.items():
        for bid in ids:
            votes[bid] += 1
    maj = {bid for bid, v in votes.items() if v > n_models / 2}
    majority_block_count += len(maj)
    for m, ids in mm.items():
        model_total[m] += len(ids)
        model_majority_hit[m] += len(ids & maj)

lines = []
lines.append("# Cross-Model Agreement: Phase 1 Public-Comment Extraction\n")
lines.append(f"Models compared: {', '.join(models)}\n")
lines.append(f"Meetings compared: {len(meetings)}\n")
lines.append("## Overall\n")
lines.append(f"- Blocks flagged as public comment by >=1 model: {total_blocks}")
lines.append(f"- Unanimous (all models that ran agree): {total_unanimous} "
             f"({100*total_unanimous/total_blocks:.1f}%)")
lines.append(f"- Majority-agreed (>50% of models): {total_majority} "
             f"({100*total_majority/total_blocks:.1f}%)")
lines.append(f"- Contested (some but not all): {total_contested} "
             f"({100*total_contested/total_blocks:.1f}%)\n")
lines.append("## Per-model totals\n")
lines.append("| model | blocks flagged | recall vs majority vote | precision vs majority vote |")
lines.append("|---|---|---|---|")
for m in models:
    rec = model_majority_hit[m] / majority_block_count if majority_block_count else 0
    prec = model_majority_hit[m] / model_total[m] if model_total[m] else 0
    lines.append(f"| {m} | {model_total[m]} | {rec:.3f} | {prec:.3f} |")
lines.append("\n## Pairwise mean Jaccard (per-meeting, macro-averaged)\n")
lines.append("| | " + " | ".join(models) + " |")
lines.append("|---|" + "---|" * len(models))
for a in models:
    row = [a]
    for b in models:
        if a == b:
            row.append("1.000")
        else:
            p = (a, b) if (a, b) in jac else (b, a)
            row.append(f"{jac.get(p, float('nan')):.3f}")
    lines.append("| " + " | ".join(row) + " |")
lines.append("\n## Top 15 meetings to manually review (most contested)\n")
lines.append("| meeting | flagged | unanimous | contested | contested share |")
lines.append("|---|---|---|---|---|")
for r in meeting_rows[:15]:
    lines.append(f"| {r['meeting'][:70]} | {r['blocks_flagged_by_any']} | "
                 f"{r['unanimous']} | {r['contested']} | {r['contested_share']} |")
lines.append("\nFull details: meeting_disagreement.csv, contested_blocks.csv, "
             "pairwise_jaccard.csv\n")

with open(os.path.join(OUT_DIR, "model_agreement_report.md"), "w",
          encoding="utf-8") as fh:
    fh.write("\n".join(lines))

print("done ->", OUT_DIR)
