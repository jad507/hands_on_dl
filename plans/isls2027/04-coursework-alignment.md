# Coursework Alignment: AI 801 and STAT 500

**Parent:** [00-INDEX](./00-INDEX.md) · **Prev:** [03 — Technical spec](./03-whisper-concord-spec.md)

Goal: make fall 2026 coursework *produce* the ISLS submission rather than compete with it. Source material is the two overview files in this repository — [`AI 801 Overview.txt`](./AI%20801%20Overview.txt) and [`Stat 500 Overview.txt`](./Stat%20500%20Overview.txt) — cross-referenced against the public course pages.

**The blunt summary:** STAT 500 is a strong, almost embarrassingly direct fit. AI 801 is a partial fit with one excellent hook and one risky one. Neither course will carry the project on its own, and the schedule collision in October is the real problem.

---

## STAT 500 — Applied Statistics

[Course page](https://online.stat.psu.edu/statprogram/stat500) · [Open course notes, CC BY-NC 4.0](https://online.stat.psu.edu/stat500/)
Textbook: Ott & Longnecker, *An Introduction to Statistical Methods and Data Analysis*, 7th ed.
Software: **Minitab**. Proctored exams via **Honorlock**. Two midterms plus a comprehensive final.

### What it gives you directly

| STAT 500 topic | Where it lands in the study |
|---|---|
| **Chi-square test of independence / contingency tables** | The code × transcription-condition table. This is the study's core descriptive analysis, taught in the course, in the same semester. |
| **Comparing two population proportions** | Code prevalence under policy P1 vs P2 — the naive (uncorrected) version of [`dslDiff`](./03-whisper-concord-spec.md#statistics--and-concord-already-ships-them). |
| **Paired-data comparison** | Exactly the paired structure that [the alignment problem](./03-whisper-concord-spec.md#the-alignment-problem) exists to create. McNemar's test is the categorical analogue of the paired *t*-test the course covers. |
| **ANOVA** | Prevalence across all five policy conditions at once, rather than pairwise. |
| **Nonparametric tests and bootstrap** (Lesson 12) | Bootstrap CIs on κ. Concord's `boot.js:bootstrapCI` does this with B=2000 and a seed; the course teaches you why it is legitimate. |
| **Type I/II error, power, sample size** | How many spine segments must you gold-code to detect a prevalence shift of δ? This determines the hand-coding budget — a real, immediate, load-bearing question. |
| **Confidence intervals and their interpretation** | Concord's entire Evidence Ladder is an argument about what a published interval is allowed to claim. |
| **Multiple regression** | `correction.js:dslOLS` / `dslLogit`. Optional. |

### What it does not give you

**STAT 500 does not cover inter-rater reliability.** No Cohen's κ, no Krippendorff's α, no Gwet's AC1. These are the field-standard statistics for your study and you will need to learn them from the [quantitative ethnography literature](./01-literature-landscape.md#d-quantitative-ethnography--the-methodological-home) and from `server/stats/agreement.js`, which implements all of them and is readable.

It also does not cover measurement-error correction (DSL/PPI). That is genuinely recent methodology and no master's-level applied stats course would.

### The Minitab problem

The course mandates Minitab; your pipeline is Python and JavaScript. Do not fight this — do the homework in Minitab and the research in your own stack. But do **one** deliberately redundant thing: run the same contingency table through Minitab and through Concord's `distributions.js:chi2Cdf` and confirm they agree. It costs an hour, it validates a dependency you are about to build a paper on, and it makes the coursework do real work. This belongs in the [verification step](./02-submission-strategy.md#backward-plan) either way.

### The schedule collision

Two midterms plus a comprehensive Honorlock-proctored final. **Midterm 1 will land near the ISLS deadline in early October.** Check the course calendar the day it is published and, if they collide, move the ISLS drafting window earlier rather than assuming you can absorb both. This is the most predictable failure mode on the whole plan.

---

## AI 801 — Foundations of Artificial Intelligence

[Course page](https://sites.psu.edu/gvwc/course/a-i-801-foundations-artificial-intelligence/) · [Program page](https://www.worldcampus.psu.edu/degrees-and-certificates/penn-state-online-artificial-intelligence-ai-engineering-masters-degree)
Textbook: Russell & Norvig, *AI: A Modern Approach*, 4th ed. (3rd ed. acceptable; [free PDF of 3rd ed. on GitHub](https://github.com/aimacode)).
Grading: 12 assignments (48%), Literature Review (10%), Final Project (40%), SEEQ survey (2%). No proctored exams.

### Set expectations correctly

AI 801 is **classical AI**: uninformed and informed search, game playing, propositional and first-order logic, knowledge representation, probability and Bayes, decision trees, MDPs, Bayesian belief networks, reinforcement learning. It is a prerequisite for **AI 574: Natural Language Processing** — which is where your actual subject matter lives, and which you are not taking yet.

There is a mismatch between the stated course objectives ("theoretical foundations and hands-on experience in **deep learning**") and the topic list, which contains no deep learning at all. Assume the topic list is authoritative. Do not walk in expecting to work on transformers.

### Hook 1: the Literature Review — take this one

100 points, 10% of the grade, two weeks, described as "the state of the art literature review... related to your project."

[Document 01](./01-literature-landscape.md) is a substantial head start on exactly this. It will need reframing for an AI audience — an AI 801 instructor cares about the LLM-as-classifier and Bayesian-inference angles, not about Ochs and Bucholtz — but the sourcing work is done.

**Reframe for AI 801 as:** *"Reliability and calibration of LLM classifiers under input perturbation."* That is a legitimate AI topic, it is your actual research question, and it maps to course content: a coding judge is a classifier with a confusion matrix; DSL/PPI correction is inference under a known error model; disagreement between judges is a probabilistic inference problem that Bayesian belief networks are the course's native vocabulary for.

Caution: it is described as a *team* assignment ("your team will have 2 weeks"). Coordinate early. See below.

### Hook 2: the Final Project — approach with care

40% of the grade, **teams of 2–3**, with a 2–3 page proposal and preliminary write-up due **Week 5** submitted as MS Word to a group OneDrive folder. Teams are pre-assigned; find yours under People → Groups in Canvas in the first two weeks.

Two real risks:

1. **Topic fit.** The course is classical AI. An "LLM pipeline for qualitative coding" project may or may not be accepted. Read the Project Description in Student Resources in week 1 and, if there is any doubt, email the instructor before the Week 5 proposal.
2. **Team dependency.** You do not control your teammates, and 40% of the grade rides on them. Coupling your conference submission to a group project you cannot unilaterally steer is a bad trade — especially with an October deadline that is *before* the project is due.

**Recommendation:** treat the Literature Review as the real integration point. Treat the Final Project as an opportunity if the topic and team happen to align, and as an entirely separate obligation if they do not. If it does align, the defensible framing is: *"a multi-agent classification system with disagreement resolution"* — that is genuinely AI 801 material (agents, uncertainty, belief networks) and genuinely what your [cross-model agreement work on the Lancaster corpus](../../README.md) already is.

You have an unusual asset here: you have already run seven models over 78 meetings and computed cross-model agreement. Most students will start their team project from nothing in week 5. Offer that as the substrate and you will likely get to pick the direction.

---

## Combined load assessment

| Obligation | Peak weeks | Conflicts with |
|---|---|---|
| ISLS submission | Sep–early Oct 2026 | STAT 500 midterm 1; AI 801 startup |
| STAT 500 homework | weekly, all semester | everything, mildly |
| STAT 500 midterms | ~mid-Oct, ~mid-Nov `[unverified]` | ISLS deadline |
| AI 801 assignments | 12 across the term | steady drag |
| AI 801 lit review | 2-week window, timing TBD | possibly ISLS drafting |
| AI 801 final project | proposal wk 5; delivery end of term | post-ISLS, mostly |

**The load is real but survivable**, mostly because the ISLS target is a 4-page demo paper rather than an 8-page long paper — which is the main reason [02](./02-submission-strategy.md#recommendation) recommends that track. If you were writing a long paper this would not work.

**The single highest-leverage move:** do the technically hard part — [the alignment problem](./03-whisper-concord-spec.md#the-alignment-problem) — in **August, before the semester starts.** It is the only piece that genuinely requires uninterrupted engineering time, and it is the only piece that cannot be done in fragments between problem sets. Everything after it is measurement and writing, both of which tolerate interruption.

---

## Finding a local advisor — this is now concrete

**Updated 2026-08-14.** There is an active research group at Penn State whose dissertation-level programme is *exactly* this area, and whose one unexamined blind spot is the stage your project addresses. Full detail in [01 §C6](./01-literature-landscape.md#c6-the-penn-state-group--qualigpt-and-ai4qual); the short version:

| Person | Role | Why they matter to you |
|---|---|---|
| **[He "Albert" Zhang](https://he-zhang.com/)** | PhD candidate (ABD, 5th yr), IST · [hpz5211@psu.edu](mailto:hpz5211@psu.edu) | Built **QualiGPT**. Dissertation: *Integrating LLMs into the Qualitative Research Process*. Taught the **AI4Qual** tutorial at IUI 2026 last month. |
| **John M. Carroll** | Distinguished Professor, IST | Zhang's advisor. Senior, extremely well known in HCI/CSCW. |
| **ChanMin Kim** | Professor, **College of Education** | Co-author across the AI4Qual line. **This is the bridge to the learning-sciences side and to ISLS.** |

**Why this is the single highest-value contact on your list.** A local faculty connection in this exact area potentially resolves four separate problems at once: the [PI-on-protocol question](./02-submission-strategy.md#process-facts-worth-knowing-before-you-need-them), access to corpora that already carry IRB coverage, a co-author who knows the ISLS and JLA reviewer pools, and — against your broader funding goal (tracked separately, not mirrored into this repository) — someone inside the university who can vouch that the work is real.

**The opening you have.** Zhang's own site lists the programme's open question as *"Where must a human stay in the loop, and how do we teach that?"* — and scopes the work as covering "coding, inter-rater reliability, interviewing, follow-up generation, and the ethics of each." **Transcription is not on that list.** Every paper in the programme starts from a transcript that already exists. You are proposing to examine the stage immediately upstream of their entire pipeline. That is complementary, and it is a much better first email than "I'm interested in your area":

> *"Your AI4Qual work all begins from an existing transcript. I've been measuring what happens one stage earlier — when the ASR step makes the transcription decisions instead of the researcher. Here's a pipeline that makes that decision explicit, and some pilot data showing the codes move. Could I ask three questions?"*

**Caveats.** Zhang is ABD in year five and may be on the market — verify he is still at Penn State before building a plan around him. Carroll and Kim are the durable contacts. And read [the AHFE 2025 paper](http://doi.org/10.54941/ahfe1006232) before writing; going in cold on someone's own results is the fastest way to waste the introduction.

**Timing.** Wait until Phase 2 of the [build plan](./03-whisper-concord-spec.md#build-phases) works, or until the [diarization-variant comparison](./05-hands-on-dl-upgrade-plan.md#step-1-mine-the-pilot-you-already-have-1-week) produces a figure. Having something to show changes the conversation entirely.

---

## What to do this week

Ordered by value, and none of it requires the semester to have started:

1. **Confirm the ISLS 2027 CFP.** Open [2027.isls.org](https://2027.isls.org/) in a browser — the automated fetch could not read it, so [every date in these documents is inferred](./02-submission-strategy.md#the-deadline-inference). Find the real deadline and specifically whether Interactive Tools & Demos runs on a different one.
2. **Start CITI.** [Social and Behavioral Human Subjects Research](https://researchsupport.psu.edu/orp/education/citi/), ~3 hours, 80% to pass. Blocks nothing, unblocks everything. Also run the CITI Decision Tool to confirm which courses your role requires.
3. **Run the alignment falsification test.** One day. Same audio, two trivially different policies, join on `(speaker, t0)`, confirm 1:1. If it fails, the design changes and you want to know now. [Details](./03-whisper-concord-spec.md#the-alignment-problem).
4. **Survey what human-coded education-discourse data actually exists** using [edu-convokit](https://edu-convokit.readthedocs.io/en/latest/tutorial_talkmoves.html), which packages TalkMoves and sibling corpora behind one interface. (TalkMoves itself is already confirmed **transcripts-only, no audio** — see [03 §Candidate corpora](./03-whisper-concord-spec.md#candidate-corpora) — so the question is what else is in there.)
5. **Ask your wife to read [01](./01-literature-landscape.md).** She is a tenure-track education professor and can tell you in ten minutes whether the framing lands with a learning-sciences audience — a judgment that would otherwise cost you a review cycle to obtain.
