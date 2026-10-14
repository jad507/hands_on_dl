# Submission Strategy & Timeline

**Parent:** [00-INDEX](./00-INDEX.md) · **Prev:** [01 — Literature landscape](./01-literature-landscape.md) · **Next:** [03 — Technical spec](./03-whisper-concord-spec.md)

⚠️ **Read this caveat first.** The ISLS websites (`2027.isls.org`, `2026.isls.org`) are client-rendered single-page applications. Direct fetch returned empty bodies, and browser tooling was unavailable in this session. **Every date and page limit below came from search-engine summaries of those pages, not from the pages themselves.** Treat them as strong priors, not facts. Confirm at [2027.isls.org](https://2027.isls.org/) and the [ISLS Annual Meeting page](https://www.isls.org/annual-meeting/) before committing to any calendar.

---

## The conference

**ISLS Annual Meeting 2027** — Mumbai, India, **June 12–16, 2027**.
Theme: *Act Local, Think Global: Contextualizing Design, Learning and Technologies*.
Site: [2027.isls.org](https://2027.isls.org/) · [ISLS event listing](https://www.isls.org/event/isls-annual-meeting-2027/)

The Annual Meeting combines two conference programs under one roof: **ICLS** (International Conference of the Learning Sciences) and **CSCL** (Computer-Supported Collaborative Learning). ISLS publishes explicit guidance on choosing between them — see the 2026 version, [Should I submit to ICLS or CSCL?](https://2026.isls.org/submitting-to-icls-or-cscl/), and the 2025 version, [Deciding between ICLS and CSCL](https://2025.isls.org/deciding-between-icls-and-cscl/). Expect a 2027 equivalent.

2027 also advertises a **Global South Learning Sciences Showcase** and a hybrid format with time-zone-aware slots — both consistent with the theme, and both worth reading closely once the CFP lands, because they may lower the cost of participation.

---

## What ISLS actually is, and what actually gets published there

Written in response to a reasonable worry: *maybe the learning sciences are firmly anti-AI, or desk-reject anything whose novel contribution is on the research-tools side.* The evidence says otherwise, on both counts, and the evidence is unusually clean.

### The field

The **learning sciences** is an interdisciplinary field studying how people learn in real settings — classrooms, museums, workplaces, online — drawing on cognitive science, sociocultural theory, anthropology, design research, and computer science. It is *empirical and theory-driven* rather than intervention-first, and its house methodology is **design-based research**: build something, study it in context, and refine both the artifact and the theory.

**ISLS** (International Society of the Learning Sciences) is the field's scholarly society. Its annual meeting runs two co-located conference programs, **ICLS** and **CSCL**, plus joint activities; [proceedings appear in three volumes](https://www.isls.org/isls-proceedings/) and are archived openly at [repository.isls.org](https://repository.isls.org/). ISLS describes its review process as "extremely rigorous" and treats proceedings papers as primary publications, not as extended abstracts — closer to CS conference norms than to the abstract-only conferences common elsewhere in education.

Its journals are the **Journal of the Learning Sciences (JLS)** and the **International Journal of Computer-Supported Collaborative Learning (ijCSCL)**.

### Evidence 1: AI-in-qualitative-coding work does not merely get published — it wins awards

The single most useful datapoint found:

> **Lopez-Fierro, S., & Nguyen, H. (2024). "Making Human-AI Contributions Transparent in Qualitative Coding." *CSCL 2024 Proceedings*, pp. 3–10.**
> [Repository record](https://repository.isls.org/handle/1/10537) · [PDF](https://repository.isls.org/bitstream/1/10537/1/CSCL2024_3-10.pdf)
> **Winner, Naomi Miyake Outstanding Student Paper Award.**

Unpack what that means. A paper about **AI's role in qualitative coding**, written by a **student**, printed at **pages 3–10** — the very front of the volume — **won CSCL's outstanding student paper award.** If the community were hostile to AI in methods work, this is precisely the paper that would have been rejected.

Its recommendations are also the direct intellectual predecessor of your contribution. It argues researchers should document (1) which parts of the coding process AI tools contribute to, (2) **the prompts used and illustrative AI output**, and (3) how those outputs are incorporated into codebook development — on the grounds that this improves credibility and confirmability.

**That is your paper's premise, already endorsed by this community, one stage downstream.** They said *disclose your coding prompts*. You extend it to: *disclose your transcription prompts too — and here is a tool that does it, plus evidence for why the transcription stage deserves the same scrutiny.* Cite this paper in your first paragraph. It converts your contribution from "an outsider's tool" into "the obvious next step in a line of work this community already rewarded."

### Evidence 2: transcription methodology is a published ICLS genre

> **Mathur, A., & Shapiro, B. R. (2022). "Interactive Transcription Techniques for Interaction Analysis." *ICLS 2022 Proceedings*, pp. 19–26.**
> [PDF](https://repository.isls.org/bitstream/1/8993/1/ICLS2022_19-26.pdf) · [Georgia State ScholarWorks](https://scholarworks.gsu.edu/ltd_facpub/46/)

A **full-length paper**, at the front of the volume, whose entire contribution is a set of transcription techniques. Its framing is worth borrowing almost verbatim: central to interaction analysis is the creation of transcripts that **selectively encode and represent** audio and video data, and existing transcription techniques have not explored what a different encoding technique would afford.

Swap "interactive visualization" for "researcher-authored ASR policy" and that is your abstract. This is proof of genre.

Also in the lineage: **"Qualitative Analysis of Video Data: Standards and Heuristics"** ([repository record](https://repository.isls.org/handle/1/370)), an older ISLS proceedings paper establishing analytic standards for video research — evidence that "here is how we should be doing our methods" is a recognized contribution type here, not a second-class one.

And on the tools side, the **Classroom Discourse Analyzer (CDA)**, a learning analytics tool that visualizes classroom discourse moves alongside video and transcripts, appears in this literature — so discourse-analysis tooling has a home.

### Evidence 3: the 2026 proceedings are full of generative AI

The [ISLS 2026 proceedings](https://2026.isls.org/proceedings/) (three volumes: [General](https://2026.isls.org/docs/General%20Volume%202026.pdf), [CSCL](https://2026.isls.org/docs/CSCL%20Volume%202026.pdf), and ICLS) include papers on interactive storytelling with generative AI, learner agency in writing with GenAI, computational modeling with AI, and re-envisioning assessment in the generative AI era — plus empirical studies comparing scaffolded AI agents against passive conditions and network analyses of AI's contributions to group interaction.

### The nuance that matters: there is a real critical strand

ISLS is not uncritical, and pretending otherwise would set you up badly. There is an active, respected line of work that is skeptical by design:

- **"Learning About and Against Generative AI Through Mapping Generative AI's Ecologies and Developing a Luddite Praxis," ICLS 2024, pp. 362–369** — [repository record](https://repository.isls.org/handle/1/11112) · [PDF](https://repository.isls.org/bitstream/1/11112/1/ICLS2024_362-369.pdf). It explicitly challenges the assumption that the learning sciences should embrace generative AI, and reframes the question as researching *about* and *against* it.
- **"Generative AI as a Mirror: Educators Exploring and Challenging Dominant Discourses about the Future of AI in Education"** — [repository record](https://repository.isls.org/handle/1/11180).

There is no single ISLS position statement on generative AI; the community holds diverse and openly critical views.

**This is good news for your framing, not bad.** Your contribution is *not* "AI can replace qualitative researchers." It is: *a widely adopted AI tool is silently making a methodological decision that belongs to the researcher, and here is an instrument that takes that decision back.* That argument is **on the same side** as the critical strand. It is a transparency-and-control contribution that happens to be built with AI, aimed at a problem AI created.

Write it that way. A paper that opens by celebrating automation will draw the Luddite-praxis reviewer as an enemy. A paper that opens with Ochs and Bucholtz, and treats Whisper's defaults as an *erosion* of researcher agency, draws that same reviewer as an ally.

### The four norms to respect

1. **Theory first, tool second.** Lead with the methodological argument. The tool is evidence for the argument, not the point of the paper. [Mathur & Shapiro](#evidence-2-transcription-methodology-is-a-published-icls-genre) do exactly this.
2. **Cite the community.** Learning sciences reviewers notice when a submission's bibliography is entirely arXiv. Cite Ochs, Bucholtz, Lopez-Fierro & Nguyen, Mathur & Shapiro, and the QE literature — not only the ML papers.
3. **Context matters.** "Under what conditions, for whom, and with what consequences" beats "our approach achieves X%." Do not write a benchmark paper.
4. **Reflexivity is expected.** State your position and your choices. Ironically, this is exactly what your tool operationalizes — which is a point worth making explicitly in the paper.

### Honest limits of this assessment

This is assembled from repository records, search summaries, and a small number of specific papers. The proceedings PDFs themselves could not be retrieved in this session (`repository.isls.org` and `2026.isls.org` both returned empty bodies to automated fetch). **Read [Lopez-Fierro & Nguyen](https://repository.isls.org/bitstream/1/10537/1/CSCL2024_3-10.pdf) and [Mathur & Shapiro](https://repository.isls.org/bitstream/1/8993/1/ICLS2022_19-26.pdf) in full** — eight pages each, and between them they will tell you more about what ISLS wants than this section can. Then skim one full recent proceedings volume to calibrate on tone and structure.

---

## Track comparison

| Track | Length | What it rewards | Fit for this project | Data/IRB burden |
|---|---|---|---|---|
| **Interactive Tools & Demos** | **4 pp + 1 p refs** | The artifact itself; feedback and collaborator-finding | **Excellent** | Lowest |
| Poster | short | Early-stage work, novel and promising ideas | Good | Low–moderate |
| Short paper (ICLS or CSCL) | 4 pp + 1 p refs | A defensible finding | Good, if a corpus lands | Moderate |
| Long paper (ICLS or CSCL) | 8 pp + 2 pp refs | Theoretical contribution grounded in real data | Poor for a first submission | High |
| Symposium | 90 min, chair + discussant | Standing in the community; a coherent multi-paper set | Not available to you yet | — |
| Workshop / Tutorial | — | Standing; a teachable method | Premature, but a good 2028 goal | — |
| Doctoral Consortium | — | Doctoral students | Likely ineligible (master's) `[unverified]` | — |

Page limits are from the 2026 cycle: [long papers 8 pp + up to 2 pp references; short papers 4 pp + 1 p references](https://www.isls.org/news/isls-2026-first-call-for-papers/); [Interactive Tools & Demos: a short paper of 4 pages excluding references, plus up to one page for references](https://2026.isls.org/interactive-tools-demos-submissions/).

### Why Interactive Tools & Demos

The 2026 call describes the session's purpose as enabling participants to get to know new interactive devices and environments potentially interesting for teaching and learning, to explore designs, and **to try out and compare methods for research and practice** — and states that authors of accepted proposals showcase their tools, get feedback, and find collaborators for future papers and symposia.

Four reasons that is the right target:

1. **"Compare methods for research" is literally your contribution.** You are not proposing a learning environment; you are proposing an instrument that lets researchers compare transcription methods. The track's own language covers it.
2. **Four pages is achievable alongside STAT 500 and AI 801.** See [04](./04-coursework-alignment.md).
3. **The demo format tolerates an engineering-forward contribution** in a community that otherwise expects theory. Your comparative advantage — you build things that work — is a liability in a long-paper review and an asset here.
4. **It converts the IRB problem into a data-selection problem.** A demo can run on public or already-coded corpora. A long paper implying original classroom data collection cannot.

The stated collaborator-finding purpose is also the actual strategic goal. You want to be in Mumbai standing next to a working tool, meeting learning-sciences researchers who have audio corpora and IRB approval and no engineer. That is a far better outcome than a poster nobody stops at.

One drafting note from the 2026 call worth internalizing: submissions should be written **for the reader of the proceedings, who may encounter the description after the event.** Write the four pages as a standalone method note, not as a demo teaser.

### Recommendation

**Primary: Interactive Tools & Demos.** Fall back to **Poster** if the tool is not demo-ready by the deadline. Do not attempt a long paper for a first ISLS submission with no prior venue history and no IRB.

Check whether the CFP permits parallel submission of a demo and a poster on related work — some years do, some do not, and it is not worth a desk reject to find out. `[unverified]`

### Fitting the conference theme

*Act Local, Think Global: Contextualizing Design, Learning and Technologies* is not decoration; ISLS reviewers weight it. Two honest connections, neither forced:

- **Contextualizing:** the paper's whole argument is that a globally deployed model (Whisper) applies one implicit transcription policy to every local context, and that researchers should be able to override it with a locally appropriate one. That is "think global, act local" almost verbatim.
- **Equity:** [Koenecke et al. (2024)](https://arxiv.org/abs/2402.08021) show hallucination concentrates in speakers with atypical speech timing. [Bucholtz (2000)](https://www.sciencedirect.com/science/article/abs/pii/S0378216699000946) frames transcription as embedded in power relations. Whose speech gets silently normalized is a real question, and a tool that surfaces the normalization is a real answer. See [01 §A2](./01-literature-landscape.md#a2-bucholtz-m-2000-the-politics-of-transcription) and [§D](./01-literature-landscape.md#d-quantitative-ethnography--the-methodological-home) on Critical Quantitative Ethnography.

Do not over-claim on the second one. A demo paper that gestures at equity without measuring it reads badly. One paragraph, honestly scoped.

---

## Timeline

### The deadline inference

The 2026 cycle, which is the only reliable guide:

| Event | Date |
|---|---|
| Original submission deadline | 5 October 2025 |
| [First extension](https://2026.isls.org/isls-2026-deadline-extension-oct-13/) | 13 October 2025 |
| [Second and final extension](https://2026.isls.org/isls-2026-2nd-and-final-deadline-extension-oct-20/) | **20 October 2025, 11:59pm AOE** |
| Conference | 15–19 June 2026, Irvine, California |

Offset from conference to deadline: **~8 months.** Applying that to 12 June 2027 gives a **primary deadline around 4–5 October 2026, with extensions plausibly to ~19 October 2026.**

**Today is 14 August 2026. That is roughly seven weeks to the likely primary deadline, and about nine to a likely final extension.** *(Corrected 2026-08-14: an earlier draft of this document was dated 27 July and said "ten weeks." It was wrong by 2.5 weeks. Everything in the backward plan below shifted accordingly.)*

Two cautions: do not plan against the extension (it is discretionary and 2026 needed *two*, which suggests the committee was chasing volume, not that extensions are routine); and note that Interactive Tools & Demos sometimes runs on a **different, later** deadline than the main ICLS/CSCL paper tracks. Check that specifically — if the demo track is later, it materially changes the plan. `[unverified]`

### Backward plan

Assume a hard target of **1 October 2026** for a submitted 4-page demo paper.

| Window | Milestone | Depends on |
|---|---|---|
| **Now → 3 Aug** | Confirm the actual CFP, dates, page limits, and demo-track deadline at [2027.isls.org](https://2027.isls.org/). Start [CITI training](#irb--the-penn-state-process) — it is the longest-lead item and blocks nothing else. | Nothing. Do it this week. |
| **3 Aug → 17 Aug** | Build the Whisper policy harness: same audio, N policy configs, N VTT outputs. Verify Concord ingests all N. | [03 §Phase 1](./03-whisper-concord-spec.md#phase-1-the-policy-harness) |
| **17 Aug → 31 Aug** | Solve the alignment problem. Get cross-condition unit alignment working via time anchors. **This is the hard part and the real contribution.** | [03 §The alignment problem](./03-whisper-concord-spec.md#the-alignment-problem) |
| **~24 Aug** | Fall semester begins `[unverified — confirm the Penn State World Campus academic calendar]`. Capacity drops sharply from here. | — |
| **31 Aug → 14 Sep** | Run the comparison end to end on one corpus. Produce the money figure: code prevalence by condition, with intervals. | Corpus decision, [03 §Candidate corpora](./03-whisper-concord-spec.md#candidate-corpora) |
| **14 Sep → 28 Sep** | Write the 4 pages. Get one read from someone in learning sciences — ideally your wife, whose field this is, and who can tell you in ten minutes whether the framing lands with an education audience. | The above |
| **28 Sep → 1 Oct** | Format to the ISLS template, check anonymization requirements, submit. | — |

**The honest risk assessment:** the alignment problem is the schedule risk. If it is not solved by end of August, drop to a poster and demo the harness without the cross-condition statistics. That is still a legitimate submission and still gets you to Mumbai.

### Backup venues

If ISLS 2027 does not land, in rough order of fit:

- **ICQE** (International Conference on Quantitative Ethnography) — the closest methodological community; see [01 §D](./01-literature-landscape.md#d-quantitative-ethnography--the-methodological-home).
- **Journal of Learning Analytics** — already publishes LLM-coding work ([01 §C2](./01-literature-landscape.md#c2-inter-rater-reliability-studies-llm-vs-human)).
- **LAK** (Learning Analytics & Knowledge).
- ISLS 2028 — a year of runway, a real IRB, and possibly a symposium instead of a demo.

---

## IRB — the Penn State process

You asked specifically for the process rather than for exemption strategies, so this is the process. One structural point first, because it changes the sequencing: **CITI training is a prerequisite for everyone listed on a protocol, takes about three hours, and can be completed before you have a protocol, a study, or even a start date.** It is the single highest-value thing you can do this week, and it is the only item on this page that is entirely within your control right now.

### The pieces

| Thing | What it is | Where |
|---|---|---|
| **HRPP** | Human Research Protection Program — the office that owns human-subjects oversight | [researchsupport.psu.edu/orp/irb](https://researchsupport.psu.edu/orp/irb/) |
| **Policy RP03** | *The Use of Human Participants in Research* — the governing university policy | [policy.psu.edu/policies/rp03](https://policy.psu.edu/policies/rp03) |
| **CITI** | The training platform. You need the **Social and Behavioral Human Subjects Research (IRB)** course. | [researchsupport.psu.edu/orp/education/citi](https://researchsupport.psu.edu/orp/education/citi/) |
| **CITI Decision Tool** | Interactive tool that tells you exactly which CITI courses your role and study type require | Linked from the CITI page above |
| **CATS IRB** | Centralized Application Tracking System — the portal you actually submit through | Linked from the HRPP site |
| **IRB Learning Path** | Penn State's own sequenced onboarding for new researchers | [researchsupport.psu.edu/orp/irb/irb-resources-training-and-events/irb-learning-path](https://researchsupport.psu.edu/orp/irb/irb-resources-training-and-events/irb-learning-path/) |
| **IRB Basic Steps** | Step-by-step process documentation, including [Step 5: After Approval](https://researchsupport.psu.edu/orp/irb/irb-basic-steps/step-5-after-approval/) | Same site |

### CITI specifics

- Course: **Social and Behavioral Human Subjects Research (IRB)**.
- **Passing score: 80%.**
- **~3 hours**, modular — you can stop and resume.
- Penn State requires **initial and continuing education every 3 years**.
- Independent corroboration of the requirement and format from a Penn State lab's own onboarding page: [LEMA Lab IRB requirements](https://sites.psu.edu/lemalab/setting-things-up/irb-requirements/); and from SSRI: [Human Subjects Training](https://ssri.psu.edu/clinicalresearchguidebook/human-subjects-training).

### Process facts worth knowing before you need them

- **Exempt is not "no IRB."** The LEMA page states it directly for their case: an experiment run by a Penn State affiliate must have Penn State IRB approval **even if exempt**. Exempt is a *determination the IRB makes*, not one you make.
- **Not-human-subjects-research is a separate category** from exempt. Penn State's guidance is that activities not meeting the definition of human subjects research do not require review and need not be submitted — *unless there is a question about whether the activity qualifies*, in which case HRPP makes a formal determination and that determination itself requires an application. Practical reading: if you think you are outside the definition and there is any ambiguity, submitting for a determination is cheap insurance and produces a document you can cite in a paper.
- **Secondary use of existing data** falls under **Exempt Category 4** under the revised Common Rule; publicly available data is one of the qualifying conditions. Penn State's summary of the 2018 Common Rule changes is at [Common Rule and Other Changes](https://researchsupport.psu.edu/orp/irb/irb-resources-training-and-events/common-rule-and-other-changes/). A useful plain-English explainer of Category 4 from another institution: [UAB, Category 4 — Secondary Use of Data](https://www.uab.edu/research/home/category-4-secondary-use-of-data).
- **Turnaround:** roughly **two weeks for exempt-level review**, dependent on submission volume and study complexity, and it is common for the IRB to request clarifications before approving. `[the two-week figure comes from a Penn State lab page, not from ORP directly — treat as approximate]`
- **Who can be PI on student research** — Penn State's rule was not confirmed in this pass. Many institutions require a faculty member as PI with the student as co-investigator. Since you will have a faculty advisor via the AI program, this is likely a formality, but **find out before you plan a protocol around it.** `[unverified]`
- **Everyone on the protocol needs current CITI.** If you later collaborate with someone who has a corpus, their training status becomes your bottleneck. Ask early.

### What this means for the October timeline

You will not have an approved protocol for original data collection by October 2026. Do not plan as if you might. The realistic sequence:

1. **Now:** complete CITI. Cost: one evening. Benefit: you are eligible for everything downstream, and you can honestly write "the author has completed institutional human-subjects training" in correspondence with potential collaborators — which matters more than it sounds when you are a first-year master's student asking a professor for their interview corpus.
2. **October 2026 submission:** built on data that does not require your own protocol — public corpora, or existing human-coded data obtained under someone else's approval with a data use agreement. See [03 §Candidate corpora](./03-whisper-concord-spec.md#candidate-corpora).
3. **Spring 2027 onward:** with CITI done and a demo accepted, submit a real protocol for the follow-on study. Two weeks of exempt review is nothing if you start it in February.

---

**Next:** [03 — Whisper → Concord technical spec](./03-whisper-concord-spec.md)
