r"""
Corpus integrity checks for downloads/comments and downloads/llm_outputs.

Why
---
Three separate count discrepancies in this project turned out to have one
cause, and none of them announced itself:

  * The ISLS audit and the upgrade plan both say "78 meetings"; the corpus
    holds 81 files.
  * `compare_model_agreement.py` reports 3,263 blocks flagged by at least one
    model but only 3,224 of those exist in any source meeting's block list.
  * Two meetings appear three times in `downloads/comments/` -- once plain,
    once `_standard`, once `_exclusive` -- where every other multi-variant
    meeting appears twice.

The cause: two files written 2026-05-19 survive in the *previous* schema, using
`commenter_blocks` / `commenter_speakers` / `rttm_modes` where the 2026-05-28
re-run writes `blocks` / `speakers` / `rttm_mode`. They were never deleted when
the re-run produced the `_standard` / `_exclusive` pair for the same meetings.

That would be harmless bookkeeping except for `get_blocks()` in
`llm_classify_human_themes.py`:

    def get_blocks(data):
        return data.get("blocks") or data.get("commenter_blocks") or []

The fallback is silent, so all seven models happily coded those two stale files.
And `commenter_blocks` is *pre-filtered to commenter_candidate speakers* -- 31
blocks instead of 243 for one of them -- which is precisely the pre-filtering
the same file's own comment warns against:

    # NOTE for future maintainers: do NOT pre-filter to commenter_candidate
    # blocks here. The recurring/commenter_candidate classification is
    # unreliable for this task

So two of every model's 78 "meetings" were coded on a differently-constructed
input than the other 76, and they duplicate meetings the corpus already
contains. The counts they inflate are the ones that would go in a paper.

Usage
-----
    python audit_corpus.py            # report; exit 1 if anything is wrong
    python audit_corpus.py --quiet    # exit code only

`tests/test_corpus_integrity.py` pins the currently-known problems so this stops
being a report nobody runs and starts being a regression test.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import paths

VARIANT_RE = re.compile(r"^(.*)_(standard|exclusive)$")

# Schema detection keys on `blocks` vs `commenter_blocks` and nothing else.
#
# An earlier version of this check also treated `rttm_modes` (plural) as a
# legacy marker and flagged 29 files. That was wrong. The corpus has three
# shapes and only the third is stale:
#
#   52 files  blocks + rttm_mode   -- one diarization mode, the _standard /
#                                     _exclusive variant files
#   27 files  blocks + rttm_modes  -- written when both modes produced identical
#                                     output, so the field records
#                                     "standard=exclusive". Plural because it
#                                     names two modes, not because it is old.
#    2 files  commenter_blocks     -- genuinely superseded, and pre-filtered
#
# Singular vs plural `rttm_mode` is a description of the diarization run, not a
# schema version. Only the absence of `blocks` marks a stale file.
BLOCKS_KEY = "blocks"
LEGACY_BLOCKS_KEY = "commenter_blocks"

# Files known to be in the superseded schema. Listed rather than silently
# skipped so that a third one appearing is a test failure, not a shrug.
KNOWN_LEGACY = {
    "City Council Committee Meeting - October 6, 2025 [bubudvmIB_E]",
    "City Council Meeting - August 12, 2025 [Pg4nxjg-PUw]",
}


def load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def audit(comments_dir: Path, outputs_root: Path) -> dict:
    findings: dict[str, list] = defaultdict(list)
    meetings: dict[str, dict[str, Path]] = defaultdict(dict)
    schema: dict[str, str] = {}
    block_ids: dict[str, set] = {}

    for p in sorted(comments_dir.glob("*.json")):
        d = load(p)
        if d is None:
            findings["unreadable"].append(p.name)
            continue
        keys = set(d)
        if BLOCKS_KEY in keys:
            schema[p.stem] = "current"
        elif LEGACY_BLOCKS_KEY in keys:
            schema[p.stem] = "legacy"
            findings["legacy_schema"].append(p.stem)
        else:
            schema[p.stem] = "unknown"
            findings["unknown_schema"].append(p.stem)

        blocks = d.get(BLOCKS_KEY) or d.get(LEGACY_BLOCKS_KEY) or []
        block_ids[p.stem] = {b.get("block_id") for b in blocks}

        m = VARIANT_RE.match(p.stem)
        if m:
            meetings[m.group(1)][m.group(2)] = p
        else:
            meetings[p.stem]["plain"] = p

    # A plain file alongside both variants is the duplicate-meeting case.
    for base, v in sorted(meetings.items()):
        if "plain" in v and ("standard" in v or "exclusive" in v):
            findings["plain_shadows_variants"].append(base)

    # Phase-1 outputs referring to block ids the source does not contain.
    for model_dir in sorted(outputs_root.iterdir()):
        p1 = model_dir / "phase1_public_comments"
        if not p1.is_dir():
            continue
        for f in sorted(p1.glob("*.json")):
            d = load(f)
            if d is None:
                findings["unreadable_output"].append(f"{model_dir.name}/{f.name}")
                continue
            if f.stem not in block_ids:
                findings["output_without_source"].append(f"{model_dir.name}/{f.stem}")
                continue
            unknown = {c.get("block_id") for c in d.get("public_comments", [])} - block_ids[f.stem]
            if unknown:
                findings["unknown_block_ids"].append(
                    (model_dir.name, f.stem, sorted(x for x in unknown if x is not None)))
            if d.get("n_chunk_errors", 0):
                findings["chunk_errors"].append(
                    (model_dir.name, f.stem, d["n_chunk_errors"]))

    # Meetings in the corpus that no model has coded.
    coded: set[str] = set()
    for model_dir in outputs_root.iterdir():
        p1 = model_dir / "phase1_public_comments"
        if p1.is_dir():
            coded |= {f.stem for f in p1.glob("*.json")}
    findings["uncoded_meetings"] = sorted(set(block_ids) - coded)

    return {
        "findings": findings,
        "n_files": len(block_ids),
        "n_meetings": len(meetings),
        "schema": schema,
    }


def report(res: dict) -> str:
    f = res["findings"]
    L: list[str] = []
    L.append("# Corpus integrity audit\n")
    L.append(f"- Source files in comments dir: {res['n_files']}")
    L.append(f"- Distinct meetings (variants collapsed): {res['n_meetings']}\n")

    def section(key, title, fmt=lambda x: f"  - {x}"):
        items = f.get(key) or []
        L.append(f"## {title}: {len(items)}\n")
        for it in items[:25]:
            L.append(fmt(it))
        if len(items) > 25:
            L.append(f"  ... and {len(items)-25} more")
        L.append("")

    section("legacy_schema", "Files in the superseded schema")
    if f.get("legacy_schema"):
        L.append("  These use `commenter_blocks`, which `get_blocks()` accepts as a")
        L.append("  silent fallback. `commenter_blocks` is pre-filtered to")
        L.append("  commenter_candidate speakers, so any model run over one of these")
        L.append("  saw a small, differently-selected subset of the meeting.\n")

    section("plain_shadows_variants",
            "Meetings present BOTH as a plain file and as diarization variants")
    if f.get("plain_shadows_variants"):
        L.append("  Each of these is counted twice in any corpus-level total, and the")
        L.append("  plain copy is the stale one.\n")

    section("unknown_schema", "Files matching no known schema")
    section("unreadable", "Unreadable source files")
    section("unreadable_output", "Unreadable model outputs")
    section("output_without_source", "Model outputs with no source meeting")
    section("uncoded_meetings", "Source meetings no model has coded")
    section("unknown_block_ids", "Outputs citing block ids absent from the source",
            fmt=lambda x: f"  - {x[0]} / {x[1]}: {x[2][:10]}")
    section("chunk_errors", "Outputs recording chunk errors",
            fmt=lambda x: f"  - {x[0]} / {x[1]}: {x[2]} errors")
    return "\n".join(L)


def problems(res: dict) -> list[str]:
    """The findings that should fail a build, as short strings."""
    f = res["findings"]
    out: list[str] = []
    for stem in f.get("legacy_schema", []):
        out.append(f"legacy_schema:{stem}")
    for stem in f.get("plain_shadows_variants", []):
        out.append(f"plain_shadows_variants:{stem}")
    for stem in f.get("unknown_schema", []):
        out.append(f"unknown_schema:{stem}")
    for name in f.get("unreadable", []):
        out.append(f"unreadable:{name}")
    for name in f.get("output_without_source", []):
        out.append(f"output_without_source:{name}")
    for t in f.get("unknown_block_ids", []):
        out.append(f"unknown_block_ids:{t[0]}/{t[1]}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Check corpus integrity.")
    ap.add_argument("--comments", default=None)
    ap.add_argument("--outputs", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    comments = Path(args.comments) if args.comments else paths.COMMENTS_DIR
    outputs = Path(args.outputs) if args.outputs else paths.OUTPUTS_ROOT

    res = audit(comments, outputs)
    if not args.quiet:
        print(report(res))
    probs = problems(res)
    if probs:
        print(f"\n{len(probs)} problem(s) found.", file=sys.stderr)
        sys.exit(1)
    print("\nNo problems found.")


if __name__ == "__main__":
    main()
