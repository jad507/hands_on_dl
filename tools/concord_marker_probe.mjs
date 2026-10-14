/**
 * Which emphasis notation survives Concord's transcript ingest intact?
 *
 * Why this exists
 * ---------------
 * ISLS doc 06 (the prosody stress test) proposes a transcription policy "P5" in
 * which the transcript carries binary word-level prominence, so that a
 * prosodically-encoded construct has something to survive on. It leaves the
 * notation as an open question -- "capitals for stress or asterisks (*money*);
 * test which survives tokenization" -- and estimates an hour to answer. This is
 * that test.
 *
 * There are two hazards, and only the first was anticipated.
 *
 * 1. `stripTags()` in server/ingest/transcript.js is `s.replace(/<[^>]*>/g,"")`.
 *    Anything in angle brackets is deleted, because that is how the VTT voice
 *    tag <v Speaker0> is consumed. `<em>money</em>` therefore arrives as
 *    "money" with no trace that markup was ever there.
 *
 * 2. The one that actually decides the answer: `splitSentences()` in
 *    server/ingest/unitize.js only splits after ./!/? when the next
 *    non-whitespace character is \p{Lu} or a digit, with a special case that
 *    looks one character further past a quote or an opening bracket. An
 *    emphasis marker that is none of those makes the following sentence look
 *    like it begins in lowercase, so the split is suppressed and two sentences
 *    silently become one unit.
 *
 * That second one is disqualifying rather than inconvenient. The ISLS design's
 * thesis is that unit boundaries are load-bearing; a notation that moves them
 * changes N, changes every content-hashed unit id, and changes the question the
 * judge is asked -- while looking like it worked.
 *
 * Run:   node tools/concord_marker_probe.mjs [path-to-concord] > out.json
 * Tests: tests/test_concord_markers.py asserts on this output.
 */

import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const concordRoot = process.argv[2] || path.resolve(here, "..", "..", "concord");

const transcript = await import(
  pathToFileURL(path.join(concordRoot, "server", "ingest", "transcript.js")).href
);
const unitizeMod = await import(
  pathToFileURL(path.join(concordRoot, "server", "ingest", "unitize.js")).href
);

function buildVTT(text) {
  return ["WEBVTT", "", "1", "00:00:00.000 --> 00:00:04.000",
          `<v Speaker0>${text}`, ""].join("\n");
}

function ingestAndUnitize(text) {
  const issues = [];
  const cues = transcript.parseVTT(buildVTT(text), issues);
  const units = unitizeMod.unitize("probe", { turns: cues, issues }, "sentence", {});
  return {
    after_ingest: cues.length ? cues[0].text : "",
    units: units.map((u) => u.text),
    unit_ids: units.map((u) => u.id),
  };
}

// ---------------------------------------------------------------------------
// Probe 1: does the marker survive at all? Sentence-internal emphasis, using
// the sentence from the actor's exercise with stress on the final word.
// ---------------------------------------------------------------------------
const INLINE = {
  caps:            ["I didn't say he stole the MONEY.", "MONEY"],
  asterisk:        ["I didn't say he stole the *money*.", "*money*"],
  double_asterisk: ["I didn't say he stole the **money**.", "**money**"],
  underscore:      ["I didn't say he stole the _money_.", "_money_"],
  caret:           ["I didn't say he stole the ^money^.", "^money^"],
  square_bracket:  ["I didn't say he stole the [money].", "[money]"],
  curly:           ["I didn't say he stole the {money}.", "{money}"],
  pipe:            ["I didn't say he stole the |money|.", "|money|"],
  // Jefferson marks stress with underlining; the closest plain-text equivalent
  // is a combining macron below on the stressed vowel.
  jefferson_under: ["I didn't say he stole the mo̱ney.", "mo̱ney"],
  // Control: expected to be destroyed by stripTags.
  angle_bracket:   ["I didn't say he stole the <em>money</em>.", "<em>money</em>"],
};

const inline = {};
for (const [name, [text, marker]] of Object.entries(INLINE)) {
  const r = ingestAndUnitize(text);
  inline[name] = {
    input: text,
    after_ingest: r.after_ingest,
    units: r.units,
    survives_ingest: r.after_ingest.includes(marker),
    marker_intact: r.units.length === 1 && r.units[0].includes(marker),
  };
}

// ---------------------------------------------------------------------------
// Probe 2: the decisive one. A marker on the FIRST word of a second sentence.
// Correct behaviour is two units. Anything else means the notation silently
// moved a unit boundary.
// ---------------------------------------------------------------------------
const BOUNDARY = {
  plain:           "He denied it. Money was the issue.",
  caps:            "He denied it. MONEY was the issue.",
  asterisk:        "He denied it. *Money* was the issue.",
  double_asterisk: "He denied it. **Money** was the issue.",
  underscore:      "He denied it. _Money_ was the issue.",
  caret:           "He denied it. ^Money^ was the issue.",
  square_bracket:  "He denied it. [Money] was the issue.",
  curly:           "He denied it. {Money} was the issue.",
  pipe:            "He denied it. |Money| was the issue.",
  quote:           'He denied it. "Money" was the issue.',
};

const boundary = {};
for (const [name, text] of Object.entries(BOUNDARY)) {
  const r = ingestAndUnitize(text);
  boundary[name] = {
    input: text,
    n_units: r.units.length,
    units: r.units,
    splits_correctly: r.units.length === 2,
  };
}

// ---------------------------------------------------------------------------
// Probe 3: does marking a word change the unit id? It must, since ids are
// content hashes -- confirming it here so the ISLS harness does not discover it
// later. This is finding 3 in the technical spec, demonstrated rather than
// assumed.
// ---------------------------------------------------------------------------
const plainIds = ingestAndUnitize("I didn't say he stole the money.").unit_ids;
const capsIds = ingestAndUnitize("I didn't say he stole the MONEY.").unit_ids;
const idStability = {
  plain_id: plainIds[0],
  marked_id: capsIds[0],
  ids_differ: plainIds[0] !== capsIds[0],
};

console.log(JSON.stringify({ inline, boundary, id_stability: idStability }, null, 2));
