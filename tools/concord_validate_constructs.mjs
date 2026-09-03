/**
 * Validate proposed constructs against Concord's own createConstruct().
 *
 * export_codebook.py could check the schema itself, but then it would be
 * checking its own understanding of the schema rather than the schema. This
 * imports server/core/objects.js and runs the real validator, so a change in
 * Concord's requirements surfaces as a failure here instead of at import time
 * in the middle of a study.
 *
 * Reads a JSON array of construct proposals on stdin.
 * Writes {"errors": [...], "ok": n} on stdout.
 *
 * Run:  node tools/concord_validate_constructs.mjs <concord-root> < constructs.json
 */

import path from "node:path";
import { pathToFileURL } from "node:url";

const concordRoot = process.argv[2];
if (!concordRoot) {
  console.error("usage: node concord_validate_constructs.mjs <concord-root>");
  process.exit(2);
}

const objects = await import(
  pathToFileURL(path.join(concordRoot, "server", "core", "objects.js")).href
);

let raw = "";
for await (const chunk of process.stdin) raw += chunk;
const proposals = JSON.parse(raw);

const errors = [];
let ok = 0;
for (const p of proposals) {
  try {
    const c = objects.createConstruct(p);
    // createConstruct fills defaults rather than echoing input, so confirm the
    // fields that actually matter survived rather than trusting it did not throw.
    if (c.name !== p.name) errors.push(`${p.name}: name not preserved`);
    if (c.type !== p.type) errors.push(`${p.name}: type not preserved`);
    if ((p.examples ?? []).length !== c.examples.length) {
      errors.push(`${p.name}: ${p.examples.length} examples in, ${c.examples.length} out`);
    }
    ok++;
  } catch (e) {
    errors.push(`${p?.name ?? "<unnamed>"}: ${e.message}`);
  }
}

console.log(JSON.stringify({ errors, ok }, null, 2));
