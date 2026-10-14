r"""
Port `data_center_comment_themes.md` into Concord constructs.

Step 5.3 of the ISLS upgrade plan. The plan calls this "mostly mechanical" with
one real decision in it: "the four sub-themes per theme may or may not survive
as separate constructs -- decide deliberately."

The decisions, made deliberately
--------------------------------
**Sub-themes stay inside their parent construct, as `criteria.include` entries,
rather than becoming constructs of their own.** Three reasons, in order of
weight:

1. Nothing in the corpus was ever scored at sub-theme level. Phase 2 emits four
   scores per comment and no more, so promoting the eleven sub-themes to
   constructs creates eleven columns with no model counterpart to compare
   against, and eleven times the human coding burden for the gold sample.
2. The sub-themes are descriptive groupings inside a theme, not independent
   judgements. 1a (electricity), 1b (water) and 1c (e-waste) are three ways of
   being Theme 1; a comment about the grid is not "not-water".
3. They lose nothing by staying: as inclusion criteria they still reach the
   judge, in the same prompt, with the same anchor quotes attached.

If a later analysis wants sub-theme resolution, `--subthemes` emits them as
separate constructs. That is a deliberate act with a flag on it rather than a
default nobody chose.

**The four theme constructs are `continuous` on [0, 1], not `binary`.** This
matches what phase 2 already produces, so the existing corpus can be compared to
Concord output directly instead of through a threshold that would have to be
chosen first. Doc 05 Step 3.2 is explicit that 0.5 is a decision rather than a
default; keeping the constructs continuous defers that decision to analysis,
where it is visible, instead of burying it in the instrument.

**A fifth construct, `is_public_comment`, is `binary`.** Phase 1 is a real
judgement with real disagreement -- five models agree unanimously on only 24% of
the blocks any of them flagged -- and it is currently invisible to Concord, which
would otherwise be handed comments with the hard part already silently decided.

**`authoredBy` is `human` on every construct.** These come from a codebook
written by researchers doing exploratory thematic analysis, not from Concord's
Director. The distinction is not cosmetic: Concord tracks `humanTouched` and
`origin` precisely so a reader can tell which constructs a person actually
authored, and mislabelling these would overstate what the machine contributed.

Anchor quotes become `examples` with `kind: "positive"` and `label: 1.0`. The
codebook's paraphrases are deliberately NOT included: an example whose text is a
researcher's summary rather than a speaker's words would teach the judge to
match summaries.

Validation
----------
`--validate` feeds the output through Concord's own `createConstruct()`, so
acceptance is checked against the real validator rather than against this
file's idea of the schema.

Usage
-----
    python export_codebook.py --validate
    python export_codebook.py --subthemes --out downloads/concord/codebook_sub.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import paths

# Must match the keys phase 2 writes, so Concord output can be joined to the
# existing corpus without a translation table. Checked in tests.
THEME_KEYS = {
    1: "municipally_managed_resources",
    2: "municipal_process",
    3: "health_and_well_being",
    4: "power_dynamics_and_inequality",
}

THEME_RE = re.compile(r"^## Theme (\d+):\s*(.+?)\s*$", re.M)
SUB_RE = re.compile(r"^### Sub-theme (\d+)([a-z]):\s*(.+?)\s*$", re.M)
DEF_RE = re.compile(r"^\*\*Definition:\*\*\s*(.+?)\s*$", re.M)
SYN_RE = re.compile(r"^\*\*Synthesis:\*\*\s*(.+?)\s*$", re.M)
# A blockquote holding a real quotation:  > *"..."* <dash> Speaker N
#
# The dash in the source codebook is U+2014 EM DASH, written here as an escape
# rather than as the literal character so this file stays ASCII. That is not
# cosmetic: an earlier ASCII sweep rewrote a literal em-dash in this pattern to
# "--", after which the parser silently found ZERO anchor quotes and
# --validate still passed, because a construct with no examples is perfectly
# valid. test_export_codebook.py now asserts the quote count for exactly that
# reason. Both dash forms are accepted so a future re-punctuation of the
# codebook does not break it again.
QUOTE_RE = re.compile(
    r'^>\s*\*"(.+?)"\*\s*(?:—|–|--)\s*(.+?)\s*$', re.M)


def parse_codebook(text: str) -> list[dict]:
    """Split the markdown into themes, each with sub-themes and anchor quotes."""
    themes: list[dict] = []
    marks = [(m.start(), int(m.group(1)), m.group(2)) for m in THEME_RE.finditer(text)]
    # Stop the last theme at the summary table rather than the end of file.
    end_of_themes = text.find("## Summary Table")
    if end_of_themes == -1:
        end_of_themes = len(text)

    for i, (pos, num, title) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else end_of_themes
        body = text[pos:stop]

        d = DEF_RE.search(body)
        s = SYN_RE.search(body)

        subs = []
        sub_marks = [(m.start(), m.group(2), m.group(3)) for m in SUB_RE.finditer(body)]
        for j, (spos, letter, stitle) in enumerate(sub_marks):
            sstop = sub_marks[j + 1][0] if j + 1 < len(sub_marks) else len(body)
            sbody = body[spos:sstop]
            # The prose line under the heading, before any quote or bold block.
            lines = [ln.strip() for ln in sbody.splitlines()[1:]
                     if ln.strip() and not ln.startswith((">", "*", "#", "|"))]
            subs.append({
                "letter": letter,
                "title": stitle,
                "gloss": lines[0] if lines else "",
                "quotes": [{"text": q.group(1), "speaker": q.group(2)}
                           for q in QUOTE_RE.finditer(sbody)],
            })

        themes.append({
            "number": num,
            "title": title,
            "key": THEME_KEYS.get(num, f"theme_{num}"),
            "definition": d.group(1) if d else "",
            "synthesis": s.group(1) if s else "",
            "subthemes": subs,
        })
    return themes


def theme_construct(t: dict) -> dict:
    include = [f"{s['title']}: {s['gloss']}".strip().rstrip(":")
               for s in t["subthemes"]]
    examples = []
    for s in t["subthemes"]:
        for q in s["quotes"]:
            examples.append({"text": q["text"], "label": 1.0, "kind": "positive"})

    definition = t["definition"]
    if t["synthesis"]:
        definition = f"{definition}\n\nSynthesis: {t['synthesis']}"

    return {
        "name": t["key"],
        "type": "continuous",
        "scale": {"min": 0.0, "max": 1.0},
        "definition": definition,
        "criteria": {
            "include": include,
            "exclude": [
                "Do not assess whether the speaker's factual claims are true. "
                "The codebook's stated analytical stance treats comments as "
                "situated narratives: the object is how residents narrate risk, "
                "responsibility and value, not whether they are correct.",
                "Do not score procedural speech, staff reports or council "
                "deliberation. This construct applies to public comment.",
            ],
        },
        "edgeCases": [
            "A comment may belong to several themes at once; score each "
            "independently rather than forcing a single assignment.",
            "A block that fuses a public comment with a council member's "
            "question is a unitization problem, not a coding problem. Flag it "
            "rather than scoring the blend.",
        ],
        "examples": examples,
        "authoredBy": "human",
        "humanTouched": True,
    }


def subtheme_constructs(t: dict) -> list[dict]:
    out = []
    for s in t["subthemes"]:
        out.append({
            "name": f"{t['key']}__{s['letter']}",
            "type": "continuous",
            "scale": {"min": 0.0, "max": 1.0},
            "definition": f"{s['title']}. {s['gloss']}".strip(),
            "criteria": {
                "include": [s["title"]],
                "exclude": [f"Belongs to {t['key']} but to a different sub-theme."],
            },
            "edgeCases": [],
            "examples": [{"text": q["text"], "label": 1.0, "kind": "positive"}
                         for q in s["quotes"]],
            "authoredBy": "human",
            "humanTouched": True,
        })
    return out


def public_comment_construct() -> dict:
    return {
        "name": "is_public_comment",
        "type": "binary",
        "definition": (
            "The unit is a member of the public addressing the governing body "
            "during a meeting, as opposed to a council member, city staff, a "
            "presenter, or procedural speech."),
        "criteria": {
            "include": [
                "A resident or member of the public speaking during a public "
                "comment period or addressing the body directly.",
                "Speech that introduces the speaker as a member of the public, "
                "or that addresses council rather than answering it.",
            ],
            "exclude": [
                "Council members, the mayor, city staff and the solicitor.",
                "Roll call, motions, seconds, votes and other procedural speech.",
                "Consultants and applicants presenting a project.",
            ],
        },
        "edgeCases": [
            "A block that runs from a council member's question into a member "
            "of the public's answer is not cleanly either. Mark it and do not "
            "resolve it by picking the longer half -- unit boundaries are part "
            "of what this study measures.",
            "Civically active residents recur across meetings and the "
            "diarization pipeline may label them 'recurring'. Recurrence does "
            "not make someone an official.",
        ],
        "examples": [],
        "authoredBy": "human",
        "humanTouched": True,
    }


def validate_with_concord(constructs: list[dict], concord_root: Path) -> list[str]:
    """Run the proposal through Concord's real createConstruct()."""
    script = Path(__file__).resolve().parent / "tools" / "concord_validate_constructs.mjs"
    r = subprocess.run(
        ["node", str(script), str(concord_root)],
        input=json.dumps(constructs), capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return [f"validator failed: {r.stderr[-2000:]}"]
    return json.loads(r.stdout).get("errors", [])


def main() -> None:
    ap = argparse.ArgumentParser(description="Port the codebook to Concord constructs.")
    ap.add_argument("--themes-md", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--subthemes", action="store_true",
                    help="also emit the 11 sub-themes as separate constructs "
                         "(off by default; see the module docstring for why)")
    ap.add_argument("--no-public-comment", action="store_true",
                    help="omit the is_public_comment binary construct")
    ap.add_argument("--validate", action="store_true",
                    help="check the output against Concord's createConstruct()")
    ap.add_argument("--concord", default=None)
    args = ap.parse_args()

    md = Path(args.themes_md) if args.themes_md else paths.THEMES_MD_PATH
    out = Path(args.out) if args.out else (
        paths.DOWNLOADS_DIR / "concord" / "codebook.json")
    concord = Path(args.concord) if args.concord else paths.REPO_ROOT.parent / "concord"

    themes = parse_codebook(md.read_text(encoding="utf-8"))
    print(f"parsed {len(themes)} themes from {md.name}")
    for t in themes:
        nq = sum(len(s["quotes"]) for s in t["subthemes"])
        print(f"  Theme {t['number']} -> {t['key']:32s} "
              f"{len(t['subthemes'])} sub-themes, {nq} anchor quotes")

    constructs: list[dict] = []
    if not args.no_public_comment:
        constructs.append(public_comment_construct())
    constructs += [theme_construct(t) for t in themes]
    if args.subthemes:
        for t in themes:
            constructs += subtheme_constructs(t)

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": md.name,
        "generated_from": "data_center_comment_themes.md",
        "note": ("Sub-themes are inclusion criteria on their parent construct, "
                 "not constructs, because nothing in the corpus was ever scored "
                 "at sub-theme level. Re-run with --subthemes to change that "
                 "deliberately."),
        "constructs": constructs,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(constructs)} constructs -> {out}")

    if args.validate:
        errs = validate_with_concord(constructs, concord)
        if errs:
            print(f"\nConcord REJECTED {len(errs)} construct(s):")
            for e in errs:
                print(f"  {e}")
            sys.exit(1)
        print("\nAll constructs accepted by Concord's createConstruct().")


if __name__ == "__main__":
    main()
