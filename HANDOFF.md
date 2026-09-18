# Handoff

**Written 2026-09-04, updated 2026-09-07.** For a session starting with no memory of the
conversation that produced the current state. Read this before touching anything.

The working directory is `hands_on_dl`. A sibling repository, `../AITranscribe`, holds
the research programme and about half the recent work. Both matter.

---

## 1. Orientation, in one minute

Two repositories, one project.

- **`hands_on_dl`** -- a corpus of Lancaster PA city council meetings, transcribed and
  coded by seven local language models, plus the analysis around it. Start with
  `EXPLAINER_handsondl_2026_09_04.md`, which assumes no prior knowledge of anything.
- **`../AITranscribe`** -- the research programme those results serve, targeting ISLS
  2027. Start with `EXPLAINER_aitranscribe_2026_09_04.md`.

If you only read one thing beyond this file, read the `hands_on_dl` explainer.

Fast lookups:

| I need | File |
|---|---|
| A specific number | `RESULTS.md` |
| Why a decision was made | `NOTEBOOK.md`, newest first, append-only |
| The prosody work and what to do next | `../AITranscribe/docs/isls2027/08-prosody-corpus-and-modernisation.md` |
| What execution corrected in the plan | `../AITranscribe/docs/isls2027/07-windows-execution-findings.md` |

---

## 2. Repository state

| | `hands_on_dl` | `AITranscribe` |
|---|---|---|
| Branch | `isls-chunk-framing` | `isls-execution-findings` |
| Commits ahead of the base branch | 18 (of `main`) | 13 (of `master`) |
| Remote tracking branch | `origin/isls-chunk-framing` | none |
| Where the remote points | GitHub, `jad507/hands_on_dl` | a personal server, `shiro` |

**`hands_on_dl` was pushed to `origin/isls-chunk-framing` between 09-04 and 09-07, by the
user.** It now sits 1 commit ahead of that remote branch and 18 ahead of `main`.
`AITranscribe` has never been pushed and is 13 ahead of `master`. Do not push without
asking. `contested_blocks.csv` contains
public-comment text from identifiable private citizens; this is public-meeting testimony
already present in the tracked corpus, so it is not a new exposure, but the GitHub
repository should be confirmed private first.

The user's IRB has an exclusion covering public data including social media and YouTube,
so collecting and analysing public videos needs no further permission. That was stated
explicitly on 2026-09-04.

Working trees are clean.

---

## 3. What the 2026-09-04 session did

Three phases.

**Diagnosed the previous session's stop.** A phi-4 GPU run died at 02:29 the night
before. It was not a power cut and not memory: uptime was unbroken, there was no crash
report and no resource-exhaustion event. The harness reported the background task as
killed, and Claude Code itself carried on normally afterwards and went idle at 02:35.
Two GPU watchdog resets (nvlddmkm event 153) did occur that night, at 00:53 and 08:12,
neither at the stop time; the card does throw TDRs under sustained load.

**Wrote two plain-language explainers**, one per repository, for readers with no
background at all. Roughly 17,500 words. The user then renamed both to dated filenames;
cross-links were repointed.

**Built a contrastive-stress video corpus**, which is the substantial new work. Search,
acoustic measurement, an any-source path, and validation against labelled ground truth.
Full account in doc 08. Headline: 497 videos seen, 91 caption-verified, 81 measured, 20
strong; detector accuracy 80% on n=5 labelled files.

## 3b. What the 2026-09-07 session did

**Finished the stress measurement**, 81 of 91. Two results beyond the count: the
measurement is deterministic (30 rows remeasured three days later came back
bit-identical), and nine of the eleven full-coverage items are 4-word fragments rather
than sentences, so only two carry real weight.

**Finished phi-4**, all five conditions. It confirmed the noise-floor spread and
falsified the reasoning behind the "context suppresses flagging" retraction. Full entry
at the top of `NOTEBOOK.md`; new rows in `RESULTS.md`.

**Fixed an analysis bug that fabricated an effect.** `analyse()` treated a condition
whose directory existed as complete, so running it mid-run reported a 25.1% difference
off zero completed meetings. Any figure produced by a mid-run `analyse` call is suspect
and cannot be identified from its output. `RESULTS.md` has not been audited for this.

**Hit the background-task kill a second time** and moved long runs to detached
`Start-Process`. See section 6.

---

## 4. What to do next, ranked

**1. Human coding of the gold sample.** Unchanged as the top priority for months. The
sample is drawn, stratified, blind, weighted and pre-registered in `downloads/gold_sample/`.
It needs 8 to 12 hours of a qualified human. Until it exists, every result in the project
is agreement between machines, not accuracy, and condition C of the chunk experiment
cannot be interpreted at all. No amount of compute substitutes.

**2. ~~Finish phi-4.~~ Done 2026-09-07.** All five conditions 12/12. It confirmed the
noise-floor spread (phi-4 1.46%, between ministral 0.41% and gemma 2.19%) and **broke the
reasoning behind the "context suppresses flagging" retraction**: phi-4 suppresses too, so
ministral is the exception rather than gemma being idiosyncratic. See the 2026-09-07
notebook entry.

The open replication question moved rather than closed. A **fourth model** would separate
the two live explanations for ministral's flatness, which this design cannot: at 8B it is
both the largest of the three and the one with the lowest noise floor, so "it ignores the
batch context" and "it is simply more stable" predict the same observation.

**3. ~~Measure the remaining 61 stress candidates.~~ Done 2026-09-07**, 81 of 91 measured.
For reference, the command was:

```bash
cd ../AITranscribe && python verify_stress.py
```

**4. First real `transcribe2` run.** `python doctor.py` exits clean with every capability
available, but nothing has ever processed real audio. Expect the torchcodec problem
(Windows needs the full-shared FFmpeg build). Before the first Gemma run, change
`GEMMA_VERBATIM_PROMPT` in `transcribe2/engines.py` from asterisks to CAPITALS; see doc 08
section 6 for why this matters.

**5. Decide what the paper is.** Five to six weeks to the likely ISLS deadline
(early-to-mid October 2026). The batching finding is finished, controlled, replicated
across three models and needs no ethics approval. The transcription-policy study is more
ambitious and needs `transcribe2` to have produced something. Doc 08 section 8 lays out
the options.

---

## 5. Standing rules

These came out of things going wrong. Do not quietly drop them.

**Every direction has replicated across three models. No magnitude has.** Nothing goes in
as a mechanism without at least two models showing it. Report magnitudes per model, or
lead with the invariants. This rule exists because "batch context suppresses flagging"
was published at 00:57 and retracted at 01:46 when a second model came back flat.

**Two models can detect a wrong claim. They cannot describe what is happening.** The
retraction above concluded the effect was gemma-specific, and phi-4 falsified that on
2026-09-07 by suppressing as well. The conclusion was right and the explanation was
wrong. When two models disagree, the honest statement is "model-dependent", not "the
odd one out is model X" -- you cannot tell which one is the outlier from a sample of two.

**There is no single noise floor.** It is a property of the model: gemma 2.19%, phi-4
1.46%, ministral 0.41%, on the identical corpus with identical settings. Any paper
quoting one ratio for "LLM coding" is quoting an artifact of whichever model it used.

**The strongest number is a range, not a point.** Contested blocks flip 27.5-36.5% under
a pure batching shift in all three models, on the same 244 blocks. Prefer this to any
single model's headline figure.

**Plain ASCII only**, in files and in chat output. No em dashes, no arrows, no
typographic quotes. Note the trap: a blanket dash-replacement sweep once broke a regex in
`export_codebook.py` so it extracted zero anchor quotations while its validator still
passed, because a construct with no examples is structurally valid. Where a regex must
match a typographic dash, write it as a `\u2014` escape so no future text sweep can
touch it.

**Leave tests in the repo.** The user asked for this explicitly and it has repeatedly
paid off. Tests caught, this session alone: a normaliser that stripped digits so every
countdown video looked like a stress demonstration; a ranking rule that reported phrases
no speaker said; a sampling window that made every word absorb the next word's onset; and
a dead regex arm that had never once fired.

**`NOTEBOOK.md` and `RESULTS.md` are append-only.** Superseded numbers are marked
superseded with the reason, not deleted. Three headline figures have been revised; the
record of being wrong is the part worth keeping.

**Commit locally, do not push.** Ask first.

---

## 6. Traps in this environment

Things that will cost you an hour if you rediscover them.

**The Bash tool resets its working directory between calls.** `cd` at the start of every
command, or use absolute paths. A `cd X && python - <<PY` heredoc runs with cwd X, but
the next call starts back at `hands_on_dl`.

**Long heredocs fail.** A `cat > file <<EOF` with a large document returns
`ENAMETOOLONG: uv_spawn`. Use the Write tool for anything substantial.

**PowerShell mangles native stderr.** In Windows PowerShell 5.1, `2>&1` on an exe wraps
each stderr line in an ErrorRecord and reports a nonzero exit even when the program
returned 0. `doctor.py` appeared to fail with exit 255 this way; run it through Bash to
see the true exit code.

**PowerShell coerces unquoted comma lists.** `-Conditions A,A2,B` arrives as the single
string `"A A2 B"`. The runner script now splits on commas and whitespace, so both forms
work, but a silently-does-nothing run was the original symptom.

**The venv is `../LancasterClaude/.venv`**, not inside either repository. Call it as
`../LancasterClaude/.venv/Scripts/python.exe` from `AITranscribe`, or activate it.

**`yt-dlp` was upgraded on 2026-09-04**, 2026.03.17 to 2026.8.19, plus `curl_cffi` to
0.16.3. This was authorised. Before the upgrade every YouTube media download returned
HTTP 403 while search and captions worked; afterwards downloads work with no cookies.
If downloads start 403ing again, update yt-dlp first. Note the pre-upgrade yt-dlp lived
in the *system* Python and the new one is in the venv.

**The GPU throws TDRs under sustained load.** RTX A2000 12GB. Two watchdog resets were
recorded on the night of 2026-09-03. Long runs mostly survive them, but do not assume a
multi-hour job is safe unattended.

**Do not launch long GPU work without asking.** Four runs went out on the night of
2026-09-03 and the fourth was stopped. That is information about the machine's
availability.

**Long runs started with the Bash or PowerShell tool's `run_in_background` get killed.**
This has now happened twice, both times to phi-4, both times with the machine provably
healthy:

| | 2026-09-03 | 2026-09-07 |
|---|---|---|
| Killed at | 02:30:53 | about 21:52:20 |
| Elapsed when killed | about 47 min | about 37 min |
| Reported as | harness `<status>killed</status>` | harness `<status>killed</status>` |

Checked both times and clean both times: uptime unbroken, no reboot, no
resource-exhaustion event (System 2004), no GPU watchdog reset (nvlddmkm 153) at the stop
time, no crash dump, no application error, RAM and disk with plenty of headroom. The two
elapsed times differ, so it is not a fixed timeout. Both kills landed while the session
was idle waiting for the user.

**Launch anything longer than about half an hour detached instead**, so it is not the
harness's child and cannot be killed with it:

```powershell
$root = "D:\Users\jad507\PycharmProjects\hands_on_dl"
Start-Process -FilePath "powershell.exe" `
  -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File", `
                ".\run_chunk_experiment.ps1","-Model","phi-4","-Conditions","B,C,D" `
  -WorkingDirectory $root `
  -RedirectStandardOutput "$root\logs\phi4.out.log" `
  -RedirectStandardError  "$root\logs\phi4.err.log" `
  -WindowStyle Hidden -PassThru
```

Keep the returned PID. Watch the log with `tail -f` and poll the PID separately, because a
detached process dying produces no notification of its own.

The runs are resumable, so a kill costs one meeting, not a condition. Check what actually
landed before restarting anything: count the files under
`downloads/chunk_experiment/runs/<condition>/<model>/phase1_public_comments/` and confirm
they parse, rather than trusting the last line of a log.

**TikTok is blocked on this machine by policy.** Never request a TikTok URL. The
already-known-URL reader in `find_stress_videos.py` skips those files outright and there
is a test asserting it. Copilot's TikTok output files remain in
`../AITranscribe/CopilotDocs/` as a record of what was searched; leave them.

---

## 7. Tests

```bash
cd hands_on_dl   && python -m pytest tests/ -q                                  # 427
cd ../AITranscribe && python -m pytest test_find_stress_videos.py test_verify_stress.py -q   # 47
cd ../AITranscribe/transcribe2 && python -m pytest test_pipeline.py -q          # 45
```

All green as of 2026-09-04.

Several are unusual and deliberately so: `test_agreement.py` pins our statistics against
Krippendorff's and Gwet's published worked examples; `test_corpus_integrity.py` is a
tripwire on the data rather than the code; `test_p1_chunks.py` asserts one invariant
across a 250-case grid because that function is load-bearing for the main finding; and
`test_report_states_the_condition_c_caveat` fails if a generated report stops carrying
its own warning. There are also two tests that assert *known limitations* so they cannot
change silently. Do not delete those as failures-in-waiting; read their docstrings.

---

## 8. Open questions nobody has answered

- Whether the 6% of unanimous blocks that flip under a batch shift are borderline cases
  or genuine errors. Needs the gold sample.
- The offset dose-response curve. Offsets 0 and 1 are tested; 2 exists. Scaling means a
  mechanism, flat means a threshold.
- Whether the batching shift specifically damages the public-versus-official distinction.
  Preliminary reading of the changed blocks suggests it does. Needs proper coding.
- Whether an audio-native model recovers the stress placement Whisper destroys. This is
  the question doc 08 was written to set up, and the user has said it is where they want
  to go next.
