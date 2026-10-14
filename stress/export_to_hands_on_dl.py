r"""
Copy the contrastive-stress work into the public hands_on_dl repository.

hands_on_dl/stress/ already holds byte-identical copies of four of these
scripts (its commit 763a46d), with tests in hands_on_dl/tests/ and a conftest
that puts stress/ on sys.path. This refreshes that copy with everything the
ICDS 2026 poster rests on: the scripts, the small result files (CSV/JSON, no
audio), the human labels, and the StressTest reproduction outputs. AITranscribe
itself stays private.

Scripts keep resolving their data as HERE / "stress_search", so the data goes
to hands_on_dl/stress/stress_search/. Audio never goes (it's gitignored here and
there, and it's other people's recordings); the manifests point at it by
relative path, and README_stress.md says how to rebuild it.

Refuses to copy anything that looks like credentials, and scans every copied
text file for home-directory paths and tailnet addresses before writing.

    python export_to_hands_on_dl.py --dry-run    # what would change
    python export_to_hands_on_dl.py              # copy (no git commands)
"""
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = HERE.parent / "hands_on_dl"

SCRIPTS = """verify_stress.py stress_from_audio.py find_stress_videos.py validate_stress_detector.py
classify_explanation.py cut_clips.py recut_clips.py label_server.py
measure_whistress.py validate_whistress.py measure_classical.py wavelet_libritts_words.yaml
export_stresstest.py score_stresstest.py null_check_stress.py
measure_llm_stress.py measure_llamacpp_stress.py reproduce_stresstest_gemma.py
reproduce_stresstest_server.py reproduce_stresstest_qwen2audio.py cascade_stresstest.py
summarize_llm_markup.py score_markup_stresstest.py score_corpus_labels.py
requirements-stress.txt export_to_hands_on_dl.py""".split()
TESTS = ["test_verify_stress.py", "test_find_stress_videos.py"]
EXTRA = ["patches/whistress-transformers5-compat.patch",
         "CopilotDocs/tiktok_contrastive_stress_confirmed_candidates.csv"]
DATA = """verified_candidates.csv explanation_classification_v2.csv clip_manifest_v3.csv
whistress_reps_v3.csv whistress_reps_v3_summary.json classical_reps_v3.csv null_check_summary_v3.json
llamacpp_nemotron-3-nano-omni-q4km_v3.csv
llamacpp_nemotron-3-nano-omni-q4km_stresstest.csv llm_stress_e4b_stresstest.csv llm_stress_e2b_stresstest.csv
stresstest/manifest.csv stresstest_scores.json whistress_stresstest_top1.csv whistress_stresstest_summary.json
whistress_stresstest_validation.csv classical_stresstest.csv
stresspresso/manifest.csv stresspresso_scores.json whistress_stresspresso_top1.csv whistress_stresspresso_summary.json
whistress_stresspresso_validation.csv classical_stresspresso.csv
markup_stresstest_scores.json llamacpp_nemotron_markup_summary_v3.json
labels/video_review.csv labels/clip_review.csv""".split()
DATA_GLOBS = ["stresstest_repro/*/*.json", "stresstest_repro/*/*.jsonl",
              "stresspresso_repro/*/*.json", "stresspresso_repro/*/*.jsonl"]
DOCS = {"README_stress.md": "stress/README.md"}  # AITranscribe path -> hands_on_dl path

FORBIDDEN = re.compile(r"cookie|\.auth|secret|token|credential", re.I)
LEAKS = re.compile(r"/home/\w+|C:\\Users\\\w+|\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
IGNORE = ["# stress/: corpus and StressTest audio stay local (other people's recordings)",
          "stress/stress_search/**/*.wav", "stress/stress_search/**/*.mp4",
          "stress/stress_search/**/*.mkv", "stress/stress_search/**/*.webm", "stress/stress_search/classical/"]


def plan() -> list[tuple[Path, Path]]:
    pairs = [(HERE / f, DEST / "stress" / f) for f in SCRIPTS + EXTRA]
    pairs += [(HERE / f, DEST / "tests" / f) for f in TESTS]
    pairs += [(HERE / src, DEST / dst) for src, dst in DOCS.items()]
    pairs += [(HERE / "stress_search" / f, DEST / "stress" / "stress_search" / f) for f in DATA]
    for g in DATA_GLOBS:
        pairs += [(p, DEST / "stress" / "stress_search" / p.relative_to(HERE / "stress_search"))
                  for p in sorted((HERE / "stress_search").glob(g))]
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    problems, changes, total = [], [], 0
    for src, dst in plan():
        rel = src.relative_to(HERE).as_posix()
        if FORBIDDEN.search(rel):
            problems.append(f"refused (looks like credentials): {rel}")
            continue
        if not src.exists():
            problems.append(f"missing, skipped: {rel}")
            continue
        text = src.read_text(encoding="utf-8", errors="replace")
        if hit := LEAKS.search(text):
            problems.append(f"contains {hit.group(0)!r}, skipped: {rel}")
            continue
        state = "new" if not dst.exists() else "same" if filecmp.cmp(src, dst, shallow=False) else "changed"
        total += src.stat().st_size
        if state != "same":
            changes.append((state, src, dst))
    for state, src, dst in changes:
        print(f"  {state:8s} {dst.relative_to(DEST)}")
    print(f"{len(changes)} files to write, {total / 1e6:.1f} MB in the export")
    for p in problems:
        print("  !", p)
    if args.dry_run:
        return 0

    for _, src, dst in changes:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    gi = DEST / ".gitignore"
    have = gi.read_text(encoding="utf-8").splitlines()
    missing = [ln for ln in IGNORE if ln not in have]
    if missing:
        gi.write_text(gi.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + "\n".join(missing) + "\n",
                      encoding="utf-8")
        print(f"  .gitignore: +{len(missing)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
