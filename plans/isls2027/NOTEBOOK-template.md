# Lab Notebook — <project>

Copy this file to `hands_on_dl/NOTEBOOK.md` and start appending.

**Rules that make it actually work:**

1. **Newest entry at the top.** You will read the top far more often than the bottom.
2. **One entry per work session**, even a 20-minute one. Especially a 20-minute one — those are the ones you forget.
3. **Append-only.** Never edit a past entry to make it correct. If you were wrong, write a new entry saying so and link back. The record of being wrong is the most valuable thing in here.
4. **Record the commit hash.** An entry without one cannot be reproduced.
5. **Fill in `Surprised by` and `Open question` even when empty** — write "nothing" rather than deleting the field. A run that surprised you in no way is itself information.
6. **Commit the notebook with the work**, so `git log` and the notebook stay in sync.

Why bother: a state audit on 2026-08-14 checked seven remembered facts about this project against the repository after roughly ten days. Four were right, two were half-right, one was wrong. Facts are recoverable from the repository; the reasoning that produced them is not.

---

## Entry template

```markdown
## YYYY-MM-DD — <one-line summary>

**Commit:** <hash>
**Ran:** <script + arguments, verbatim enough to re-run>
**Config:** <model, N, chunk size, prompt version, anything varied>
**Result:** <the numbers, not a description of the numbers>
**Surprised by:** <what did not match expectation — or "nothing">
**Decided:** <any choice made, and why; especially thresholds and exclusions>
**Next:** <the single next action>
**Open question:** <what you would ask someone who knew more>
```

---

## Worked example

```markdown
## 2026-08-14 — Standard vs exclusive diarization: aggregate stable, per-meeting not

**Commit:** ee37763
**Ran:** ad-hoc comparison of phase1_public_comments counts across the 26 meetings
        present in both _standard and _exclusive variants
**Config:** ministral-8b, qwen3.5-9b-q6, phi-4; phase 1 only; prompt = in-script literal (unversioned — fix this)
**Result:** ministral 16/26 pairs differ, totals 630 vs 623 (-1.1%)
            qwen-q6   18/26 pairs differ, totals 601 vs 596 (-0.8%)
            phi-4     15/26 pairs differ, totals 853 vs 846 (-0.8%)
            Largest single-meeting swing: June 2 2025, ministral 25 -> 18 (-28%)
**Surprised by:** aggregate barely moves while most individual meetings do. Matches
            what Southwell et al. (EDM 2022) predict for discourse-level models —
            robust in aggregate, unstable per unit. Did not expect to reproduce it here.
**Decided:** report aggregate and per-meeting separately from now on. Reporting only
            the aggregate would have hidden the entire effect.
**Next:** block-level alignment across variants so this can be a per-block flip rate
          rather than a count delta. Same alignment problem as the Concord bridge —
          solve once, use twice.
**Open question:** are the 29 meetings where standard == exclusive systematically
          different (shorter? fewer speakers? cleaner audio?), or is it arbitrary?
          If systematic, the 26-meeting sample is biased.
```

---

## Companion file: `RESULTS.md`

The notebook is chronological and messy on purpose. `RESULTS.md` is the opposite — one table, one row per experiment, so that in September you can find the number you need without re-reading three months of prose.

| Date | Commit | Experiment | Config | N | Headline number |
|---|---|---|---|---|---|
| 2026-08-14 | ee37763 | Phase-1 cross-model agreement (core 5) | 5 models, DeepSeeks excluded | 78 meetings / 3263 blocks | unanimous 24.1%, majority 52.7% |
| 2026-08-14 | ee37763 | Quantization stability | qwen3.5-9b q6 vs q8 | 78 meetings | Jaccard 0.840 — *same model, not independent* |
| 2026-08-14 | ee37763 | Diarization variant sensitivity | ministral-8b, phase 1 | 26 paired meetings | 16/26 differ; aggregate −1.1% |

Add a row the moment a number exists. Never let a number live only in a terminal scrollback.
