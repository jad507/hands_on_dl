#!/usr/bin/env python3
"""
Human stress labels for the YouTube/TikTok corpus: a small labelling web app.

Doc 09 section 14.1. Every method was scored on the cut clips in
clip_manifest_v2.csv, and until now the only yardstick on the corpus was
"agrees with WhiStress". This page lets a person label the same clips, so the
corpus scorer can say "correct" instead. It serves one page plus the clip wavs
and appends every click to a CSV under stress_search/labels/, so labelling is
resumable and closing the browser loses nothing. Two modes:

  Review  one card per video: title, link (context only), the located phrase,
          each repetition clip in order. Keep, or exclude with a reason.
          -> labels/video_review.csv. A single bad clip of a kept video gets
          its own "bad" tick -> labels/clip_review.csv; it is skipped in
          labelling and dropped from scoring (verify_stress.bad_clips).
  Label   the repetition clips one at a time in a fixed shuffled order, with no
          title and no repetition number, so the demo's left-to-right order
          can't steer the answer (the detectors hear one clip at a time too).
          Toggle the stressed word(s), or mark the clip unclear or bad; the bad
          rate is the clipper's error rate. -> labels/clip_labels.csv

The order is one seeded shuffle of all clips, skipping excluded videos, so any
prefix of it is a random sample: stopping after 150 clips is fine.

WhiStress's pick can be shown, as a check rather than a starting point. By
default it appears only after a clip is answered ("you: X, WhiStress: Y"), and
Back lets you revise. A tick box shows it before answering instead, with A to
accept it. Either way each row records whistress_seen: 0 means the answer was
given without having seen WhiStress's pick for that clip (a revision after the
reveal, or any answer with the box ticked, is 1). The scorer uses the first
unseen answer per clip as the blind label, since the labels are the yardstick
WhiStress itself gets scored against.

Both CSVs are append-only logs; the latest row for a video or clip wins
(verify_stress.latest_rows). Exclusions are applied at analysis time by
verify_stress.excluded_videos(), never by deleting clips.

Stdlib only. Run on Shiro, open from any machine on the tailnet:

    python label_server.py --host <this machine's tailnet IP>     # then http://<that IP>:8765
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from verify_stress import HERE, LABELS, latest_rows, local_path

SDIR = HERE / "stress_search"
SEED = 20260929
REVIEW_FIELDS = ["video_id", "decision", "reason", "phrase_wrong", "correct_phrase", "note", "ts"]
CLIP_REVIEW_FIELDS = ["video_id", "condition", "bad", "ts"]  # one clip of a kept video marked unusable
LABEL_FIELDS = ["video_id", "condition", "phrase", "stressed_indices", "stressed_words",
                "status", "reason", "whistress_index", "whistress_seen", "note", "order_pos", "ts"]
_WRITE = threading.Lock()
LABEL_DIR = LABELS  # --labels points it elsewhere (for testing the page without touching real labels)


def video_info(manifest: Path) -> tuple[list[dict], dict[tuple[str, str], Path]]:
    """One entry per video (metadata + its clips), and (video_id, condition) -> wav."""
    meta = {}
    with open(SDIR / "verified_candidates.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            meta[r["video_id"]] = {"title": r["title"], "channel": r["channel"], "url": r["url"]}
    tiktok = HERE / "CopilotDocs" / "tiktok_contrastive_stress_confirmed_candidates.csv"
    with open(tiktok, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            vid = r["url"].rstrip("/").rsplit("/", 1)[-1]
            meta[vid] = {"title": r["sentence"], "channel": r["creator"], "url": r["url"]}

    videos, paths = {}, {}
    with open(manifest, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            vid, cond = r["video_id"], r["condition"]
            paths[(vid, cond)] = local_path(r["path"])
            v = videos.setdefault(vid, {
                "id": vid, "phrase": r["phrase"], "words": r["phrase"].split(),
                "bucket": r["bucket"], "reps": [], "flags": {}, "spliced": False, "original": False,
                **meta.get(vid, {"title": "", "channel": "", "url": ""})})
            if cond.startswith("rep_"):
                v["reps"].append(cond)
                # recut_clips.py's QA (v3 manifests): transcript mismatch, or a cut through speech
                edge = max(float(r.get("edge_start_db") or -99), float(r.get("edge_end_db") or -99))
                why = [w for w, bad in (("transcript doesn't match", r.get("qa_pass") == "False"),
                                        (f"starts or ends in speech ({edge:.0f} dB)", edge > -20)) if bad]
                if why:
                    v["flags"][cond] = "; ".join(why)
            elif cond == "reps_only":
                v["spliced"] = True
            elif cond == "original":
                v["original"] = True
    for v in videos.values():
        v["reps"].sort()
    return sorted(videos.values(), key=lambda v: v["id"].lower()), paths


def blind_order(videos: list[dict]) -> list[list[str]]:
    clips = sorted([v["id"], c] for v in videos for c in v["reps"])
    random.Random(SEED).shuffle(clips)
    return clips


def append(path: Path, fields: list[str], row: dict) -> None:
    with _WRITE:
        path.parent.mkdir(parents=True, exist_ok=True)
        new = not path.exists()
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            if new:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in fields})


class Handler(BaseHTTPRequestHandler):
    manifest: Path = SDIR / "clip_manifest_v3.csv"
    clips_dir: Path = SDIR / "clips_v3"
    videos: list[dict] = []
    by_id: dict[str, dict] = {}
    paths: dict[tuple[str, str], Path] = {}
    order: list[list[str]] = []
    whistress: dict[str, int] = {}       # "video_id|condition" -> WhiStress's top word index
    labelled: set[tuple[str, str]] = set()
    recut_lock = threading.Lock()

    @classmethod
    def load(cls):
        cls.videos, cls.paths = video_info(cls.manifest)
        cls.by_id = {v["id"]: v for v in cls.videos}
        cls.order = blind_order(cls.videos)

    def recut(self, vid: str) -> str:
        """Re-cut one video with its corrected sentence (recut_clips.py reads it
        from the review log) and reload; the page then shows the new clips."""
        with self.recut_lock:
            r = subprocess.run([sys.executable, str(HERE / "recut_clips.py"), "--only", vid,
                                "--manifest", str(self.manifest), "--clips-dir", str(self.clips_dir),
                                "--reviews", str(LABEL_DIR / "video_review.csv")],
                               capture_output=True, text=True, cwd=HERE)
            type(self).load()
            for key in [k for k in self.whistress if k.startswith(vid + "|")]:
                del self.whistress[key]  # its clips changed; WhiStress hasn't heard the new ones
            # its rep_NN files are new audio, so earlier per-clip "bad" marks no longer apply
            ts = time.strftime("%Y-%m-%dT%H:%M:%S")
            for (v, c), r in latest_rows(LABEL_DIR / "clip_review.csv", "video_id", "condition").items():
                if v == vid and r["bad"] == "1":
                    append(LABEL_DIR / "clip_review.csv", CLIP_REVIEW_FIELDS,
                           {"video_id": v, "condition": c, "bad": 0, "ts": ts})
            lines = [ln for ln in r.stdout.splitlines() if vid in ln]
            return lines[-1].strip() if lines else (r.stderr.strip().splitlines() or ["re-cut failed"])[-1]

    def log_message(self, fmt, *args):  # only POSTs are worth a log line
        if self.command == "POST":
            super().log_message(fmt, *args)

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.path = self.path.split("?", 1)[0]
        if self.path in ("/", "/index.html"):
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/state":
            reviews = latest_rows(LABEL_DIR / "video_review.csv", "video_id")
            labels = latest_rows(LABEL_DIR / "clip_labels.csv", "video_id", "condition")
            bad = latest_rows(LABEL_DIR / "clip_review.csv", "video_id", "condition")
            self.send_json({"videos": self.videos, "order": self.order, "whistress": self.whistress,
                            "clip_bad": [f"{k[0]}|{k[1]}" for k, r in bad.items() if r["bad"] == "1"],
                            "reviews": {k[0]: r for k, r in reviews.items()},
                            "labels": {f"{k[0]}|{k[1]}": r for k, r in labels.items()}})
        elif m := re.fullmatch(r"/audio/([^/]+)/([^/?]+)", self.path):
            path = self.paths.get((unquote(m[1]), unquote(m[2])))
            if path is None or not path.exists():
                self.send_error(404)
            else:
                self.send_audio(path)
        else:
            self.send_error(404)

    def send_audio(self, path: Path):
        """A wav, honouring Range requests (browsers use them to seek and replay)."""
        size = path.stat().st_size
        start, end = 0, size - 1
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if m and (m[1] or m[2]):
            if m[1]:
                start, end = int(m[1]), min(int(m[2]) if m[2] else size - 1, size - 1)
            else:
                start = max(0, size - int(m[2]))
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "no-cache")  # a re-cut replaces files in place
        self.end_headers()
        try:
            with open(path, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(1 << 16, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser dropped a fetch it no longer needed

    def do_POST(self):
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"error": "bad json"}, 400)
        vid = data.get("video_id")
        if vid not in self.by_id:
            return self.send_json({"error": "unknown video"}, 400)
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")

        if self.path == "/api/review":
            if data.get("decision") not in ("keep", "exclude"):
                return self.send_json({"error": "decision must be keep or exclude"}, 400)
            row = {"video_id": vid, "decision": data["decision"],
                   "reason": data.get("reason", "") if data["decision"] == "exclude" else "",
                   "phrase_wrong": int(bool(data.get("phrase_wrong"))),
                   "correct_phrase": " ".join(data.get("correct_phrase", "").split()),
                   "note": data.get("note", ""), "ts": ts}
            append(LABEL_DIR / "video_review.csv", REVIEW_FIELDS, row)
            if row["correct_phrase"] and row["correct_phrase"].lower() != self.by_id[vid]["phrase"]:
                row["recut"] = self.recut(vid)
                row["video"] = self.by_id.get(vid)
            return self.send_json(row)

        if self.path == "/api/clipbad":
            cond = data.get("condition")
            if (vid, cond) not in self.paths or not cond.startswith("rep_"):
                return self.send_json({"error": "unknown clip"}, 400)
            row = {"video_id": vid, "condition": cond, "bad": int(bool(data.get("bad"))), "ts": ts}
            append(LABEL_DIR / "clip_review.csv", CLIP_REVIEW_FIELDS, row)
            return self.send_json(row)

        if self.path == "/api/label":
            cond = data.get("condition")
            if (vid, cond) not in self.paths or not cond.startswith("rep_"):
                return self.send_json({"error": "unknown clip"}, 400)
            words = self.by_id[vid]["words"]
            try:
                idx = sorted({int(i) for i in data.get("stressed", [])})
            except (TypeError, ValueError):
                return self.send_json({"error": "stressed must be word indices"}, 400)
            if any(not 0 <= i < len(words) for i in idx):
                return self.send_json({"error": "word index out of range"}, 400)
            status = data.get("status")
            if status not in ("stressed", "none", "unsure", "bad"):
                return self.send_json({"error": "bad status"}, 400)
            if (status == "stressed") != bool(idx):
                return self.send_json({"error": "stressed needs words; other statuses none"}, 400)
            row = {"video_id": vid, "condition": cond, "phrase": " ".join(words),
                   "stressed_indices": json.dumps(idx),
                   "stressed_words": " ".join(words[i] for i in idx),
                   "status": status, "reason": data.get("reason", "") if status == "bad" else "",
                   "whistress_index": self.whistress.get(f"{vid}|{cond}", ""),
                   # a relabel always comes after the post-answer reveal
                   "whistress_seen": int(bool(data.get("assist")) or (vid, cond) in self.labelled),
                   "note": data.get("note", ""), "order_pos": data.get("order_pos", ""), "ts": ts}
            append(LABEL_DIR / "clip_labels.csv", LABEL_FIELDS, row)
            self.labelled.add((vid, cond))
            return self.send_json(row)

        self.send_error(404)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stress labels</title>
<style>
:root { --bg:#f6f5f2; --card:#fff; --ink:#1d1d1f; --mute:#6b6b70; --line:#dcdad4;
        --accent:#2f5bd3; --on:#2f5bd3; --onink:#fff; --keep:#1f8a4c; --excl:#b3261e; --warn:#9a6700; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#17181a; --card:#222326; --ink:#ececec; --mute:#9a9aa0; --line:#3a3b3f;
          --accent:#7ea2ff; --on:#4d74e6; --onink:#fff; --keep:#4cc07f; --excl:#ff7a6e; --warn:#e0b44a; }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.45 system-ui, sans-serif; }
header { position:sticky; top:0; z-index:5; background:var(--bg); border-bottom:1px solid var(--line);
         display:flex; gap:12px; align-items:center; padding:10px 16px; flex-wrap:wrap; }
header h1 { font-size:17px; margin:0 12px 0 0; }
.tab { border:1px solid var(--line); background:var(--card); color:var(--ink); padding:7px 14px;
       border-radius:8px; cursor:pointer; font:inherit; }
.tab.active { background:var(--on); color:var(--onink); border-color:var(--on); }
.stat { color:var(--mute); font-size:14px; margin-left:auto; }
main { max-width:980px; margin:0 auto; padding:16px; }
button { font:inherit; cursor:pointer; }
a { color:var(--accent); }
.card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px; margin:0 0 14px; }
.meta { color:var(--mute); font-size:14px; }
.phrase { font-size:20px; margin:8px 0 12px; }
.reps { display:flex; flex-wrap:wrap; gap:8px 14px; margin:10px 0; }
.rep { display:flex; flex-direction:column; font-size:13px; color:var(--mute); }
.rep audio { width:210px; height:34px; }
.rep .flag { color:var(--warn); cursor:help; }
.rep label.bad { font-size:12px; margin-left:8px; cursor:pointer; }
.rep.isbad span, .rep.isbad audio { opacity:.45; }
.rep.isbad span { text-decoration:line-through; }
.recutmsg { color:var(--warn); font-size:14px; margin-top:8px; }
.row { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:10px; }
.btn { border:1px solid var(--line); background:var(--card); color:var(--ink); padding:7px 14px; border-radius:8px; }
.btn.keep.sel { background:var(--keep); border-color:var(--keep); color:#fff; }
.btn.excl.sel { background:var(--excl); border-color:var(--excl); color:#fff; }
select, input[type=text] { font:inherit; padding:6px 8px; border:1px solid var(--line); border-radius:8px;
                          background:var(--card); color:var(--ink); }
input[type=text] { flex:1; min-width:180px; }
.badge { font-size:13px; padding:2px 8px; border-radius:99px; border:1px solid var(--line); }
.badge.keep { color:var(--keep); border-color:var(--keep); }
.badge.exclude { color:var(--excl); border-color:var(--excl); }
.toolbar { display:flex; gap:12px; align-items:center; margin-bottom:14px; flex-wrap:wrap; }
/* label mode */
#lab .big { text-align:center; padding:28px 16px; }
.words { display:flex; flex-wrap:wrap; justify-content:center; gap:10px; margin:22px 0; }
.word { font-size:24px; padding:10px 16px; border:2px solid var(--line); border-radius:10px;
        background:var(--card); color:var(--ink); position:relative; }
.word.on { background:var(--on); border-color:var(--on); color:var(--onink); }
.word.ws { outline:2px dashed var(--warn); outline-offset:3px; }
.word .wtag { position:absolute; bottom:-11px; right:-6px; font-size:11px; background:var(--warn); color:#fff;
              border-radius:4px; padding:0 4px; }
.word kbd { position:absolute; top:-9px; left:-7px; font-size:11px; background:var(--bg);
            border:1px solid var(--line); border-radius:4px; padding:0 4px; color:var(--mute); }
.acts { display:flex; flex-wrap:wrap; justify-content:center; gap:8px; margin-top:6px; }
.acts .btn { min-width:120px; }
.btn.primary { background:var(--on); border-color:var(--on); color:var(--onink); }
.acts .bad { color:var(--warn); border-color:var(--warn); }
kbd.k { font-size:12px; color:var(--mute); margin-left:6px; }
.progress { height:6px; background:var(--line); border-radius:3px; overflow:hidden; margin:6px 0 2px; }
.progress div { height:100%; background:var(--accent); }
#last { color:var(--mute); font-size:14px; min-height:22px; margin-top:14px; }
.help { color:var(--mute); font-size:14px; margin-top:18px; text-align:left; }
.hidden { display:none; }
</style></head>
<body>
<header>
  <h1>Stress labels</h1>
  <button class="tab" data-mode="rev">1 · Review videos</button>
  <button class="tab" data-mode="lab">2 · Label clips</button>
  <span class="stat" id="stat"></span>
</header>
<main>
  <section id="rev" class="hidden">
    <div class="toolbar">
      <label><input type="checkbox" id="onlyTodo"> show only unreviewed or clipping problems</label>
      <span class="meta">Keep or exclude each video. Exclusions drop it from labelling and from every analysis.
      Links and titles are context only; judge by the clips.</span>
    </div>
    <div id="cards"></div>
  </section>
  <section id="lab" class="hidden">
    <div class="card big">
      <div class="meta" id="pos"></div>
      <label class="meta"><input type="checkbox" id="assist"> show WhiStress's pick before I answer</label>
      <div class="progress"><div id="bar" style="width:0"></div></div>
      <audio id="player" preload="auto"></audio>
      <div id="startBox"><button class="btn primary" id="start" style="margin-top:22px">Start (plays audio)</button></div>
      <div id="clipBox" class="hidden">
        <div class="words" id="words"></div>
        <div class="acts">
          <button class="btn primary" id="save">Save stressed word(s)<kbd class="k">Enter</kbd></button>
          <button class="btn" id="replay">Replay<kbd class="k">Space</kbd></button>
          <button class="btn hidden" id="accept">WhiStress is right<kbd class="k">A</kbd></button>
        </div>
        <div class="acts" style="margin-top:10px">
          <button class="btn" data-status="none">No clear stress<kbd class="k">N</kbd></button>
          <button class="btn" data-status="unsure">Can't tell<kbd class="k">U</kbd></button>
          <button class="btn bad" data-status="bad" data-reason="cut_off">Bad: cut off<kbd class="k">C</kbd></button>
          <button class="btn bad" data-status="bad" data-reason="wrong_words">Bad: wrong/extra words<kbd class="k">W</kbd></button>
          <button class="btn bad" data-status="bad" data-reason="two_readings">Bad: two readings<kbd class="k">T</kbd></button>
        </div>
        <div class="acts" style="margin-top:10px">
          <button class="btn" id="back">&larr; Back</button>
          <button class="btn" id="skip">Skip &rarr;</button>
        </div>
        <div id="last"></div>
      </div>
      <div id="doneBox" class="hidden"><p style="font-size:20px">All clips labelled. Thank you.</p></div>
      <div class="help">Keys 1–9, 0 toggle the first ten words (click the rest). More than one word can be stressed.
      The order is shuffled once and fixed, so any stopping point leaves a random sample. Every answer is saved
      the moment you give it; Back revisits and relabels.<br>WhiStress's pick (one of the methods being scored
      against these labels) shows after each answer. Ticking the box above shows it before you answer, which is
      faster but no longer blind: those answers are recorded as having seen it.</div>
    </div>
  </section>
</main>
<script>
const $ = s => document.querySelector(s);
let S = null, mode = null, queue = [], qi = 0, sel = new Set(), started = false;
const REASONS = [["bad_clipping","bad clipping (fixable)"],["junk","junk / not usable"],["not_demo","not a stress demo"],
  ["explanation_in_phrase","phrase includes explanation speech"],["bad_audio","bad audio"],["other","other"]];

async function load() {
  S = await (await fetch("/api/state")).json();
  const saved = (() => { try { return localStorage.getItem("mode"); } catch { return null; } })();
  setMode(saved || "rev");
}
const excluded = id => S.reviews[id] && S.reviews[id].decision === "exclude";
const badClip = (v, c) => S.clip_bad.includes(v + "|" + c);  // one clip of a kept video, marked in review
function stat() {
  const nrev = Object.keys(S.reviews).length, nexc = S.videos.filter(v => excluded(v.id)).length;
  const q = S.order.filter(([v, c]) => !excluded(v) && !badClip(v, c)), nlab = q.filter(([v, c]) => S.labels[v + "|" + c]).length;
  $("#stat").textContent = `reviewed ${nrev}/${S.videos.length} (${nexc} excluded) · labelled ${nlab}/${q.length} clips`;
}
function setMode(m) {
  mode = m; try { localStorage.setItem("mode", m); } catch {}
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.mode === m));
  $("#rev").classList.toggle("hidden", m !== "rev"); $("#lab").classList.toggle("hidden", m !== "lab");
  if (m === "rev") renderCards(); else startLabel();
  stat();
}
document.querySelectorAll(".tab").forEach(t => t.onclick = () => setMode(t.dataset.mode));
async function post(url, body) {
  const r = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
  const j = await r.json(); if (!r.ok) { alertBox(j.error || "save failed"); throw new Error(j.error); } return j;
}
function alertBox(msg) { $("#stat").textContent = "⚠ " + msg; }
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const au = (v, c) => `/audio/${encodeURIComponent(v)}/${encodeURIComponent(c)}`;

// ------------------------------------------------------------- review mode
$("#onlyTodo").onchange = renderCards;
// the videos worth another look after a re-cut: unreviewed, or reviewed with a clipping complaint
const recheck = r => !r || r.reason === "bad_clipping" || r.reason === "bad_audio" || r.phrase_wrong === "1"
  || /clip/i.test(r.note || "");
function cardHTML(v, i) {
  const r = S.reviews[v.id] || {}, t = Date.now();
  const reps = v.reps.map((c, j) => {
    const fl = v.flags[c] ? ` <span class="flag" title="${esc(v.flags[c])}">⚠</span>` : "";
    const b = badClip(v.id, c);
    return `<div class="rep ${b ? "isbad" : ""}"><div><span>rep ${j + 1}${fl}</span><label class="bad"><input type="checkbox" data-bad="${c}" ${b ? "checked" : ""}> bad</label></div><audio controls preload="none" src="${au(v.id, c)}?t=${t}"></audio></div>`;
  }).join("");
  const extra = (v.spliced ? `<div class="rep">all reps spliced<audio controls preload="none" src="${au(v.id, "reps_only")}?t=${t}"></audio></div>` : "")
    + (v.original ? `<div class="rep">full video audio<audio controls preload="none" src="${au(v.id, "original")}"></audio></div>` : "");
  const opts = REASONS.map(([k, t]) => `<option value="${k}" ${r.reason === k ? "selected" : ""}>${t}</option>`).join("");
  const nflag = Object.keys(v.flags).length;
  return `<div class="card" data-id="${esc(v.id)}">
    <div class="meta">${i + 1}/${S.videos.length} · ${esc(v.bucket)} · ${v.reps.length} clips${nflag ? ` · ⚠ ${nflag} flagged by the automatic check` : ""}
      ${r.decision ? `<span class="badge ${r.decision}">${r.decision}${r.reason ? ": " + esc(r.reason) : ""}</span>` : ""}</div>
    <div><a href="${esc(v.url)}" target="_blank" rel="noopener">${esc(v.title || v.id)}</a>
      <span class="meta"> — ${esc(v.channel)}</span></div>
    <div class="phrase">“${esc(v.phrase)}”</div>
    <div class="reps">${reps}${extra}</div>
    <div class="row">
      <button class="btn keep ${r.decision === "keep" ? "sel" : ""}" data-act="keep">Keep</button>
      <button class="btn excl ${r.decision === "exclude" ? "sel" : ""}" data-act="exclude">Exclude</button>
      <select data-f="reason"><option value="">reason…</option>${opts}</select>
      <label><input type="checkbox" data-f="phrase_wrong" ${r.phrase_wrong === "1" ? "checked" : ""}> phrase is wrong</label>
      <input type="text" data-f="note" placeholder="note (optional)" value="${esc(r.note || "")}">
    </div>
    <div class="row"><input type="text" data-f="correct_phrase" placeholder="the sentence actually repeated, if the phrase above is wrong or cut short (re-cuts the clips)"
      value="${esc(r.correct_phrase || "")}"></div>
    <div class="recutmsg"></div></div>`;
}
function renderCards() {
  const todo = $("#onlyTodo").checked;
  $("#cards").innerHTML = S.videos.map((v, i) => todo && !recheck(S.reviews[v.id]) ? "" : cardHTML(v, i)).join("");
  document.querySelectorAll("#cards .card").forEach(bindCard);
}
function bindCard(card) {
  const id = card.dataset.id, f = k => card.querySelector(`[data-f=${k}]`);
  const send = async decision => {
    if (decision === "exclude" && !f("reason").value) { f("reason").focus(); alertBox("pick a reason to exclude"); return; }
    const phrase = f("correct_phrase").value.trim(), v = S.videos.find(x => x.id === id);
    const willCut = phrase && phrase.toLowerCase() !== v.phrase;
    if (willCut) card.querySelector(".recutmsg").textContent = "re-cutting with the corrected sentence… (a few seconds)";
    const res = await post("/api/review", {video_id:id, decision, reason:f("reason").value,
      phrase_wrong:f("phrase_wrong").checked || !!phrase, correct_phrase:phrase, note:f("note").value});
    const {recut, video, ...row} = res;
    S.reviews[id] = row;
    if (video) {
      S.videos[S.videos.findIndex(x => x.id === id)] = video;
      S.clip_bad = S.clip_bad.filter(k => !k.startsWith(id + "|"));
    }
    const i = S.videos.findIndex(x => x.id === id);
    const tmp = document.createElement("div"); tmp.innerHTML = cardHTML(S.videos[i], i);
    const fresh = tmp.firstElementChild; card.replaceWith(fresh); bindCard(fresh);
    if (recut) fresh.querySelector(".recutmsg").textContent = "re-cut: " + recut + " — listen again, then Keep or Exclude.";
    stat();
  };
  card.querySelectorAll("[data-act]").forEach(b => b.onclick = () => send(b.dataset.act));
  const resend = () => { if (S.reviews[id]) send(S.reviews[id].decision); };
  f("phrase_wrong").onchange = resend; f("note").onchange = resend;
  // a corrected sentence re-cuts even before a decision; it is saved as "exclude: bad clipping" until you choose
  f("correct_phrase").onchange = () => {
    if (S.reviews[id]) return send(S.reviews[id].decision);
    if (!f("reason").value) f("reason").value = "bad_clipping";
    send("exclude");
  };
  f("reason").onchange = () => { if (f("reason").value && (!S.reviews[id] || S.reviews[id].decision === "exclude")) send("exclude"); };
  // one clip plays at a time
  card.querySelectorAll("[data-bad]").forEach(box => box.onchange = async () => {
    const c = box.dataset.bad, key = id + "|" + c;
    await post("/api/clipbad", {video_id:id, condition:c, bad:box.checked});
    S.clip_bad = S.clip_bad.filter(k => k !== key).concat(box.checked ? [key] : []);
    box.closest(".rep").classList.toggle("isbad", box.checked);
    stat();
  });
  card.querySelectorAll("audio").forEach(a => a.onplay = () =>
    document.querySelectorAll("audio").forEach(o => { if (o !== a) o.pause(); }));
}

// -------------------------------------------------------------- label mode
function startLabel() {
  queue = S.order.filter(([v, c]) => !excluded(v) && !badClip(v, c));
  const first = queue.findIndex(([v, c]) => !S.labels[v + "|" + c]);
  qi = first < 0 ? queue.length : first;
  if (started) showClip();
}
const assistOn = () => $("#assist").checked;
try { $("#assist").checked = localStorage.getItem("assist") === "1"; } catch {}
$("#assist").onchange = () => { $("#assist").blur(); try { localStorage.setItem("assist", assistOn() ? "1" : "0"); } catch {}
  if (started) showClip(); };
$("#start").onclick = () => { started = true; $("#startBox").classList.add("hidden"); showClip(); };
function showClip() {
  const done = qi >= queue.length;
  $("#clipBox").classList.toggle("hidden", done); $("#doneBox").classList.toggle("hidden", !done);
  const nlab = queue.filter(([v, c]) => S.labels[v + "|" + c]).length;
  $("#bar").style.width = (100 * nlab / Math.max(1, queue.length)) + "%";
  if (done) { $("#pos").textContent = `${nlab}/${queue.length} labelled`; return; }
  const [vid, cond] = queue[qi], v = S.videos.find(x => x.id === vid), prev = S.labels[vid + "|" + cond];
  $("#pos").textContent = `clip ${qi + 1} of ${queue.length}` + (prev ? ` · already labelled: ${prev.status}${prev.stressed_words ? " — " + prev.stressed_words : ""}` : "");
  sel = new Set(prev && prev.status === "stressed" ? JSON.parse(prev.stressed_indices) : []);
  const ws = assistOn() ? S.whistress[vid + "|" + cond] : undefined;
  $("#words").innerHTML = v.words.map((w, i) =>
    `<button class="word ${sel.has(i) ? "on" : ""} ${i === ws ? "ws" : ""}" data-i="${i}">${i < 10 ? `<kbd>${(i + 1) % 10}</kbd>` : ""}${esc(w)}${i === ws ? `<span class="wtag">WhiStress</span>` : ""}</button>`).join("");
  $("#accept").classList.toggle("hidden", ws === undefined);
  document.querySelectorAll(".word").forEach(b => b.onclick = () => toggle(+b.dataset.i));
  const p = $("#player"); p.src = au(vid, cond) + "?t=" + Date.now(); p.play().catch(() => {});
}
function toggle(i) {
  const v = S.videos.find(x => x.id === queue[qi][0]); if (i >= v.words.length) return;
  sel.has(i) ? sel.delete(i) : sel.add(i);
  document.querySelector(`.word[data-i="${i}"]`).classList.toggle("on", sel.has(i));
}
async function save(status, reason) {
  if (qi >= queue.length) return;
  if (status === "stressed" && sel.size === 0) { alertBox("pick at least one word, or use No clear stress"); return; }
  const [vid, cond] = queue[qi];
  const row = await post("/api/label", {video_id:vid, condition:cond, status, reason: reason || "",
    stressed: status === "stressed" ? [...sel] : [], order_pos: qi, assist: assistOn()});
  S.labels[vid + "|" + cond] = row;
  const v = S.videos.find(x => x.id === vid), w = S.whistress[vid + "|" + cond];
  const you = row.status === "stressed" ? row.stressed_words : row.status + (row.reason ? " (" + row.reason + ")" : "");
  const agree = w !== undefined && row.status === "stressed" && JSON.parse(row.stressed_indices).includes(w);
  $("#last").textContent = `saved clip ${qi + 1} — you: ${you} · WhiStress: ${w === undefined ? "no pick" : v.words[w]}`
    + (row.status === "stressed" && w !== undefined ? (agree ? " ✓" : " ✗ (← to revise)") : "");
  qi++; stat(); showClip();
}
$("#save").onclick = () => save("stressed");
$("#accept").onclick = () => { const w = S.whistress[queue[qi][0] + "|" + queue[qi][1]];
  if (!assistOn() || w === undefined) return; sel = new Set([w]); save("stressed"); };
$("#replay").onclick = () => { const p = $("#player"); p.currentTime = 0; p.play(); };
$("#back").onclick = () => { if (qi > 0) { qi--; showClip(); } };
$("#skip").onclick = () => { if (qi < queue.length) { qi++; showClip(); } };
document.querySelectorAll("[data-status]").forEach(b => b.onclick = () => save(b.dataset.status, b.dataset.reason));
document.addEventListener("keydown", e => {
  if (mode !== "lab" || !started || e.target.tagName === "INPUT" || e.ctrlKey || e.metaKey || e.altKey) return;
  // a clicked button keeps focus, and Space/Enter would click it again on top of the shortcut
  if (document.activeElement && document.activeElement.tagName === "BUTTON") document.activeElement.blur();
  const k = e.key.toLowerCase();
  if (/^[0-9]$/.test(k)) toggle((+k + 9) % 10);
  else if (k === "enter") save("stressed");
  else if (k === " ") { e.preventDefault(); $("#replay").click(); }
  else if (k === "n") save("none");
  else if (k === "u") save("unsure");
  else if (k === "c") save("bad", "cut_off");
  else if (k === "w") save("bad", "wrong_words");
  else if (k === "t") save("bad", "two_readings");
  else if (k === "a") $("#accept").click();
  else if (k === "arrowleft" || k === "backspace") $("#back").click();
  else if (k === "arrowright") $("#skip").click();
  else return;
  e.preventDefault();
});
load();
</script></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default="stress_search/clip_manifest_v3.csv")
    ap.add_argument("--host", default="127.0.0.1",
                    help="address to bind; Shiro's Tailscale address to label from another machine")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--whistress", default="stress_search/whistress_reps_v3.csv",
                    help="measure_whistress.py output for the same manifest (skipped if missing)")
    ap.add_argument("--labels", default=str(LABELS), help="where the label CSVs go")
    ap.add_argument("--clips-dir", default="stress_search/clips_v3", help="where a re-cut writes clips")
    args = ap.parse_args()
    global LABEL_DIR
    LABEL_DIR = Path(args.labels)

    Handler.manifest, Handler.clips_dir = HERE / args.manifest, HERE / args.clips_dir
    Handler.load()
    if (HERE / args.whistress).exists():
        with open(HERE / args.whistress, newline="", encoding="utf-8") as f:
            Handler.whistress = {f"{r['video_id']}|{r['condition']}": int(r["top_index"])
                                 for r in csv.DictReader(f) if r["top_index"] != ""}
    else:
        print(f"no {args.whistress}: WhiStress's picks won't be shown")
    Handler.labelled = set(latest_rows(LABEL_DIR / "clip_labels.csv", "video_id", "condition"))
    missing = [f"{v}/{c}" for (v, c), p in Handler.paths.items() if c.startswith("rep_") and not p.exists()]
    print(f"{len(Handler.videos)} videos, {len(Handler.order)} clips"
          + (f"; {len(missing)} clip files missing (e.g. {missing[0]})" if missing else ""))
    print(f"labels -> {LABEL_DIR}")
    print(f"open http://{args.host}:{args.port}/", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
