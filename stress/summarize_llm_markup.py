r"""
What did the audio-native LLM actually mark, and where?

measure_llm_stress.py stores every transcript Gemma-4 produced (plain
verbatim prompt and the general meaning-preserving prompt) for every clip.
Its `*_markup_applied` column came from a regex whose cut-off rule matched
ordinary hyphenated words, so this recounts from the text itself, one
notation at a time:

    emphasis   *word* or **word**      (the one that bears on stress)
    pause      (1.2) or (.)
    bracket    [overlapping speech]
    cutoff     a trailing hyphen: "wor-"

and then asks the stress question directly:

  * single-repetition clips: when Gemma marks emphasis, which word, and does
    it match the word WhiStress / the wavelet toolkit rate most stressed
    (measure_whistress.py, measure_classical.py) on the same clip?
  * full original videos: of all emphasis marks, how many land on a word of
    the demonstrated sentence rather than on the surrounding explanation?

Usage
-----
    python summarize_llm_markup.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SS = HERE / "stress_search"

NOTATION = {
    "emphasis": re.compile(r"\*\*([^*\n]+?)\*\*|(?<!\*)\*([^*\n]+?)\*(?!\*)"),
    "pause": re.compile(r"\(\d+(?:\.\d+)?\)|\(\.\)"),
    "bracket": re.compile(r"\[[^\]\n]+\]"),
    "cutoff": re.compile(r"\b\w+-(?=\s|$|[,.;:!?\"'])"),
    # Some models mark stress in CAPITALS without being asked (Nemotron: "I didn't
    # say HE stole the money"). Filtered by capitals() below, not counted raw.
    "capitals": re.compile(r"\b[A-Z][A-Z']*[A-Z]\b"),
}
# Capitalised tokens that are spelling, not emphasis.
ACRONYMS = {"PM", "AM", "OK", "TV", "USA", "UK", "CEO", "ASAP", "NYC", "BBC", "CNN", "ESL", "EFL", "IELTS",
            "TOEFL", "DJ", "ID", "DC", "LA", "NASA", "FBI", "CIA", "UN", "EU", "GPS", "DVD", "CD", "PC",
            "US", "ILA", "TJT", "RSVP", "IQ", "CT", "FYI", "ASP"}  # "US" the country; a stressed "us" is lost


def norm(s: str) -> str:
    return re.sub(r"[^\w' ]", "", s.lower()).strip()


def capitals(text: str) -> list[str]:
    """Words written in capitals for emphasis: 2+ letters, not a known acronym,
    and not in a transcript that is mostly capitals anyway."""
    words = re.findall(r"[A-Za-z']+", text)
    if not words or sum(w.isupper() for w in words) > len(words) / 2:
        return []
    return [norm(m) for m in NOTATION["capitals"].findall(text) if m not in ACRONYMS]


def emphasized(text: str) -> list[str]:
    """Emphasis marks of either kind: *asterisks* / **bold**, or CAPITALS."""
    return [norm(a or b) for a, b in NOTATION["emphasis"].findall(text)] + capitals(text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--llm", type=Path, default=SS / "llm_stress_measured_full.csv")
    ap.add_argument("--prompts", default="plain,general", help="<prompt>_content columns to read")
    ap.add_argument("--out", type=Path, default=SS / "llm_markup_summary.json")
    ap.add_argument("--manifest", type=Path, default=SS / "clip_manifest.csv")
    ap.add_argument("--whistress", type=Path, default=SS / "whistress_reps.csv")
    ap.add_argument("--classical", type=Path, default=SS / "classical_reps.csv")
    args = ap.parse_args()
    prompts = args.prompts.split(",")

    rows = list(csv.DictReader(open(args.llm, encoding="utf-8")))
    phrase = {r["video_id"]: r["phrase"] for r in csv.DictReader(open(args.manifest, encoding="utf-8"))}
    ws = {(r["video_id"], r["condition"]): r for r in csv.DictReader(open(args.whistress, encoding="utf-8"))}
    cl = {(r["video_id"], r["condition"]): r for r in csv.DictReader(open(args.classical, encoding="utf-8"))}
    conds = [c for c in ("rep", "reps", "original") if any(r["condition"].split("_")[0] == c for r in rows)]

    def present(kind: str, text: str) -> bool:
        return bool(capitals(text)) if kind == "capitals" else bool(NOTATION[kind].search(text))

    out: dict = {"source": args.llm.name, "clips": len(rows), "by_notation": {}, "rep_clips_with_emphasis": {},
                 "originals": {}}
    for prompt in prompts:
        for cond in conds:
            sub = [r for r in rows if r["condition"].split("_")[0] == cond]
            out["by_notation"][f"{prompt}/{cond}"] = {
                "n": len(sub), **{k: sum(present(k, r[f"{prompt}_content"]) for r in sub) for k in NOTATION}}

        reps = []
        for r in rows:
            if not r["condition"].startswith("rep_"):
                continue
            marks = emphasized(r[f"{prompt}_content"])
            if not marks:
                continue
            k = (r["video_id"], r["condition"])
            w, c = ws.get(k, {}).get("top_word", ""), cl.get(k, {}).get("wavelet_top_word", "")
            marked = {t for m in marks for t in m.split()}
            reps.append({"video_id": r["video_id"], "condition": r["condition"], "marks": marks,
                         "whistress_top": w, "wavelet_top": c,
                         "matches_whistress": norm(w) in marked, "matches_wavelet": norm(c) in marked,
                         "transcript": r[f"{prompt}_content"][:120]})
        out["rep_clips_with_emphasis"][prompt] = {
            "n_marked": len(reps), "n_rep_clips": sum(r["condition"].startswith("rep_") for r in rows),
            "matches_whistress_top": sum(x["matches_whistress"] for x in reps),
            "matches_wavelet_top": sum(x["matches_wavelet"] for x in reps), "clips": reps}

        if "original" in conds:
            on_target = elsewhere = 0
            videos = []
            for r in rows:
                if r["condition"] != "original":
                    continue
                marks = emphasized(r[f"{prompt}_content"])
                target = set(norm(phrase[r["video_id"]]).split())
                hit = [m for m in marks if set(m.split()) & target]
                on_target += len(hit)
                elsewhere += len(marks) - len(hit)
                videos.append({"video_id": r["video_id"], "phrase": phrase[r["video_id"]],
                               "marks": len(marks), "on_target_sentence": len(hit), "target_marks": hit})
            out["originals"][prompt] = {"n_videos": len(videos),
                                        "videos_with_any_emphasis": sum(v["marks"] > 0 for v in videos),
                                        "marks_on_target_sentence": on_target, "marks_elsewhere": elsewhere,
                                        "videos": videos}

    args.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"{args.llm.name}: notation present, by prompt / condition (clips containing at least one):")
    for k, v in out["by_notation"].items():
        print(f"  {k:20s} n={v['n']:3d}  " + "  ".join(f"{n}={v[n]}" for n in NOTATION))
    for prompt, rc in out["rep_clips_with_emphasis"].items():
        print(f"Single-repetition clips, {prompt} prompt: emphasis (asterisks or capitals) in "
              f"{rc['n_marked']}/{rc['n_rep_clips']}; marked word = WhiStress top in "
              f"{rc['matches_whistress_top']}, = wavelet top in {rc['matches_wavelet_top']}")
    for prompt, o in out["originals"].items():
        print(f"Full originals, {prompt} prompt: emphasis in {o['videos_with_any_emphasis']}/{o['n_videos']} videos; "
              f"{o['marks_on_target_sentence']} marks on the demonstrated sentence, {o['marks_elsewhere']} elsewhere")


if __name__ == "__main__":
    main()
