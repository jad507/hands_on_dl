/**
 * Round-trip exported VTT files through Concord and report whether the turn
 * count survives import.
 *
 * The question this answers is narrow and important: export_vtt.py writes one
 * cue per block, so Concord should produce exactly one turn per cue. If it
 * produces fewer, mergeCues fused turns and the block spine -- which every rate
 * in this study uses as its denominator -- was silently renegotiated at import.
 *
 * Imports Concord's real transcript.js rather than reimplementing the parse, so
 * this tracks the dependency instead of a snapshot of it.
 *
 * Run:  node tools/concord_roundtrip.mjs <concord-root> <vtt-dir> [maxMergeGapSeconds]
 * Emits a JSON array on stdout, one entry per file.
 */

import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [, , concordRoot, vttDir, gapArg] = process.argv;
if (!concordRoot || !vttDir) {
  console.error("usage: node concord_roundtrip.mjs <concord-root> <vtt-dir> [gap]");
  process.exit(2);
}

// export_vtt.py's NO_MERGE_GAP_SECONDS. Negative because mergeCues tests
// `gap <= maxMergeGapSeconds`, so 0 still merges cues that abut exactly.
const maxMergeGapSeconds = gapArg === undefined ? -1 : Number(gapArg);

const transcript = await import(
  pathToFileURL(path.join(concordRoot, "server", "ingest", "transcript.js")).href
);
const unitizeMod = await import(
  pathToFileURL(path.join(concordRoot, "server", "ingest", "unitize.js")).href
);

// mergeCues is module-private, so reach it the way the application does:
// parseVTT for cues, then compare against what a turn-scheme unitize yields.
function mergeLikeConcord(cues, gap) {
  const turns = [];
  for (const cue of cues) {
    if (!cue.text) continue;
    const last = turns[turns.length - 1];
    const g = last && cue.t0 != null && last.t1 != null ? cue.t0 - last.t1 : 0;
    if (last && last.speaker === cue.speaker && g <= gap) {
      last.text += (last.text ? " " : "") + cue.text;
      last.t1 = cue.t1 ?? last.t1;
    } else {
      turns.push({ speaker: cue.speaker ?? "Speaker", t0: cue.t0, t1: cue.t1, text: cue.text });
    }
  }
  return turns;
}

const files = (await readdir(vttDir)).filter((f) => f.endsWith(".vtt")).sort();
const out = [];

for (const f of files) {
  const raw = await readFile(path.join(vttDir, f), "utf8");
  const issues = [];
  const cues = transcript.parseVTT(raw, issues);

  // Expected cue count comes from the manifest the exporter wrote alongside.
  let expected = null;
  try {
    const m = JSON.parse(
      await readFile(path.join(vttDir, f.replace(/\.vtt$/, ".manifest.json")), "utf8"));
    expected = m.stats?.n_cues ?? null;
  } catch { /* manifest optional */ }

  const turns = mergeLikeConcord(cues, maxMergeGapSeconds);
  const atDefault = mergeLikeConcord(cues, 30);

  const units = unitizeMod.unitize("rt", { turns, issues }, "turn", {});
  const sentenceUnits = unitizeMod.unitize("rt", { turns, issues }, "sentence", {});

  const nullSpeakers = cues.filter((c) => c.speaker == null).length;

  out.push({
    file: f,
    expected,
    cues: cues.length,
    turns: turns.length,
    turns_at_concord_default_30s: atDefault.length,
    units_turn_scheme: units.length,
    units_sentence_scheme: sentenceUnits.length,
    cues_without_speaker: nullSpeakers,
    issues,
    ok: expected == null
      ? cues.length === turns.length
      : expected === cues.length && expected === turns.length && expected === units.length,
  });
}

console.log(JSON.stringify(out, null, 2));
