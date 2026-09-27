# Literature Landscape

**Purpose:** map the four bodies of work this project sits between, and locate the gap precisely enough to write an introduction section against it.
**Compiled:** 2026-08-14. **Parent:** [00-INDEX](./00-INDEX.md)

The bodies are: (A) transcription theory in qualitative methodology, (B) ASR behavior and failure modes, (C) LLM-assisted qualitative coding, (D) quantitative ethnography as the methodological bridge, and (E) **prior work that already varies the transcript** — added in revision after a deliberate attempt to falsify this document's original gap claim, which succeeded in part. Read [§E](#e-prior-work-that-varies-the-transcript--the-falsification-attempt) before believing anything in §A–D about novelty.

**Revision note (2026-08-14).** The first draft of this document ended with the claim that *no one has held the audio, the codebook, and the coding model constant while varying only the transcription policy.* That was too strong. It has been retracted and replaced with a narrower claim that survives the counterexamples. The counterexamples are in §E, along with what they imply for the study design — which is more than a footnote, because they predict the effect you are looking for may be small.

---

## A. Transcription as a theoretical act

This is the literature that gives the paper its warrant. It is old, canonical in the learning sciences and in linguistic anthropology, and almost entirely absent from the ML-side ASR literature — which is exactly why an ISLS audience will find the collision interesting.

### A1. Ochs, E. (1979). "Transcription as Theory"

In Ochs & Schieffelin (eds.), *Developmental Pragmatics*, Academic Press, pp. 43–72.
Full text: [UCLA copy](http://www.sscnet.ucla.edu/anthro/faculty/ochs/articles/ochs1979.pdf) · [Cassell mirror](https://www.justinecassell.com/discourse/pdfs/ochs_transcription_as_theory.pdf) · [EMCA bibliography entry](https://emcawiki.net/bibtex/browser.php?key=Ochs1979&bib=emca.bib)

The founding citation. Three claims that carry the whole paper:

- **Transcripts are data**, not a neutral record of data. What ends up on the page is already an analysis.
- **Recording equipment does not solve selective observation.** Ochs's phrasing is that the problems of selective observation "are not eliminated with the use of recording equipment" — a line that reads very differently in 2026, when the selection is being made by a decoder you did not write.
- **Selective transcription is *correct*, not sloppy.** A transcript that includes everything is not more scientific; it encodes a different (and often worse) hypothesis. Her worked example is phonetic vs. standard orthography in children's sound play: standard orthography makes some instances of sound play structurally invisible.

The third point is the one to lean on. It converts "should Whisper strip disfluencies?" from a quality question into a **theory-selection** question, which is the move that makes this an ISLS paper rather than an engineering note.

### A2. Bucholtz, M. (2000). "The Politics of Transcription"

*Journal of Pragmatics* 32(10):1439–1465. DOI `10.1016/S0378-2166(99)00094-6` · [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378216699000946) · [PDF via CNRS ICAR](https://icar.cnrs.fr//ecole_thematique/tranal_i/documents/Buscholz_Transcription.pdf) · [Semantic Scholar](https://www.semanticscholar.org/paper/The-politics-of-transcription-Bucholtz/40e4b3d8c3b8e7ced1e92648acce6884c952dd63)

**This is the paper to build the framework on.** Bucholtz splits transcription into two levels:

| Level | The question it answers |
|---|---|
| **Interpretive** | *What* is transcribed (inclusion/exclusion) |
| **Representational** | *How* it is transcribed (orthography, notation, layout) |

That is a ready-made two-axis design space for the experimental conditions in [03](./03-whisper-concord-spec.md#experimental-design). A Whisper prompt manipulates **both** axes at once, which is part of why its effects are hard to reason about informally — and a good reason to measure rather than argue.

Bucholtz also frames transcription as embedded in relations of power, using a police interrogation transcript and a newspaper's transcript of a radio program. That framing maps onto ISLS 2027's *Act Local, Think Global* theme with almost no forcing: whose speech gets normalized into standard orthography by a model trained predominantly on a particular distribution of English is a live equity question. See [C5](#c5-asr-accuracy-disparities) and [02](./02-submission-strategy.md#fitting-the-conference-theme).

### A3. Jefferson transcription notation

Jefferson, G. (2004). "Glossary of transcript symbols with an introduction," in Lerner (ed.), *Conversation Analysis: Studies from the First Generation*, John Benjamins. `[unverified — page numbers not checked]`

Relevant as the **maximal-fidelity end of the design space**: timed pauses `(0.7)`, overlap brackets `[ ]`, latching `=`, audible breath `.hh` / `hh`, cut-offs `-`, stretched sounds `:`. If you want a "CA-lite" condition, this is the notation to approximate.

⚠️ **Engineering constraint discovered in Concord's source:** Concord's VTT parser calls `stripTags()`, which deletes everything matching `<[^>]*>`. Any notation using angle brackets is silently destroyed at import. Jefferson notation is safe (it uses parentheses, brackets, colons); HTML-ish or XML-ish annotation schemes are not. Details in [03](./03-whisper-concord-spec.md#finding-2-striptags-destroys-angle-bracket-markup).

### A4. Naturalized vs. denaturalized transcription

Oliver, D. G., Serovich, J. M., & Mason, T. L. (2005). "Constraints and Opportunities with Interview Transcription: Towards Reflection in Qualitative Research." *Social Forces* 84(2):1273–1289. `[unverified — cited from memory of the methodological literature, not confirmed against the source in this pass; verify before citing]`

The naturalized/denaturalized distinction is the standard vocabulary practitioners actually use for the choice Rae described, and it maps cleanly onto the transcription-service taxonomy that has grown up around it: **full verbatim** (everything, including false starts and fillers), **clean/intelligent verbatim** (fillers removed, all meaning-bearing speech preserved), **edited**, **phonetic**, **Jeffersonian**.

Practitioner-side sources documenting that taxonomy and its methodological consequences — useful for the "current practice" paragraph, weak as scholarly citations:
[GoTranscript on verbatim vs. clean verbatim](https://gotranscript.com/en/blog/interview-transcription-template-qualitative-research) ·
[SkyScribe](https://www.sky-scribe.com/en/blog/conversation-transcript-verbatim-vs-cleaned-guides) ·
[HappyScribe's five-type taxonomy](https://www.happyscribe.com/blog/what-are-types-of-transcription-in-qualitative-research) ·
[Conveo](https://conveo.ai/insights/transcription-in-qualitative-research)

The pattern across all of them: **clean verbatim is recommended for thematic analysis and grounded theory; full verbatim or Jeffersonian is required for discourse and conversation analysis.** That is a *normative* claim about method–transcript fit that, as far as this survey found, has never been tested empirically at the level of "does the choice actually move the codes?" That absence is the paper.

---

## B. What Whisper actually does to a transcript

### B1. The model

Radford, A., et al. (2022). "Robust Speech Recognition via Large-Scale Weak Supervision." [arXiv:2212.04356](https://arxiv.org/abs/2212.04356). The Whisper paper. Note the training-data construction: weakly supervised on heterogeneous internet audio-transcript pairs, with substantial preprocessing to remove machine-generated transcripts. The transcript *style* the model reproduces is therefore an emergent property of that corpus, not a designed one.

### B2. Whisper's disfluency handling is inconsistent — and that is the finding

This is the empirical crux of the proposed study, and the literature is genuinely split, which is itself informative:

- **Evidence it preserves disfluencies:** [Lost in Transcription: Identifying and Quantifying the Accuracy Biases of Automatic Speech Recognition Systems Against Disfluent Speech](https://arxiv.org/pdf/2405.06150) documents that ASR output on spontaneous speech retains filled pauses, whole-word and phrase repetitions, partial-word stutters, and broken syllables. The [faster-whisper discussion thread #569](https://github.com/SYSTRAN/faster-whisper/discussions/569) is practitioners observing disfluencies appearing more on longer-form audio.
- **Evidence it removes them:** the [FluentWhisper writeup](https://huggingface.co/blog/pradachan/fluent-whisper) describes Whisper as performing *implicit* disfluency removal as a byproduct of its data normalization, and ships a LoRA adapter to make the cleanup explicit and single-pass.
- **Both, depending on context:** [Style-agnostic evaluation of ASR using multiple reference transcripts](https://arxiv.org/pdf/2412.07937) and [Mind the Pause: Disfluency-Aware Objective Tuning](https://arxiv.org/pdf/2605.12242) both treat transcript style as a variable that ASR evaluation has historically confounded.

**The synthesis to put in the paper:** Whisper applies a transcription policy. That policy is real, consequential, context-dependent, undocumented, and unstable across audio length and speaker. It is precisely the kind of decision Ochs and Bucholtz insist belongs to the researcher, and it is currently being made by a decoder.

### B3. Hallucination — Koenecke et al. (2024), "Careless Whisper"

*FAccT '24*. [arXiv:2402.08021](https://arxiv.org/abs/2402.08021) · [HTML](https://arxiv.org/html/2402.08021v2) · [FAccT PDF](https://facctconference.org/static/papers24/facct24-111.pdf) · [Science news coverage](https://www.science.org/content/article/ai-transcription-tools-hallucinate-too) · [Montreal AI Ethics summary](https://montrealethics.ai/careless-whisper-speech-to-text-hallucination-harms/)

Numbers worth quoting exactly:

- ~**1.7%** of audio segments from speakers **with aphasia** and ~**1.2%** from speakers **without** produced transcriptions containing fabricated text (April–May 2023 runs, an earlier Whisper version).
- ~**40%** of the fabricated segments were harmful or concerning; about half of those alluded to violence, sexual innuendo, or demographic stereotypes.
- **Mechanism:** hallucination correlates with longer non-vocal durations. Silences, "umm"s, and "aah"s are not reliably interpreted as silence.
- **Mitigation since:** OpenAI updated the model to skip silence and re-transcribe on suspected hallucination; a December 2023 re-run eliminated most of the earlier fabrications.

**Why this is load-bearing for the argument, and not just a scare stat:** Koenecke et al. found that *the failure concentrates exactly where the qualitative signal lives*. The long pause before answering a sensitive question — the thing Rae's decision point is about — is the same acoustic condition that drives fabrication. A researcher who trims disfluencies is discarding data; a researcher who keeps them is, on older model versions, inviting invention. Neither is safe by default and neither is currently *reported*. That is an unusually clean motivation paragraph.

### B4. Kid-Whisper and the classroom-audio gap

[Kid-Whisper: Towards Bridging the Performance Gap in Automatic Speech Recognition for Children VS. Adults](https://arxiv.org/pdf/2309.07927) ([arXiv:2309.07927](https://arxiv.org/abs/2309.07927)). Relevant if any condition uses K-12 classroom audio: Whisper's error rate on child speech is materially worse than on adult speech, which confounds any cross-condition comparison run on classroom data. Argues for interview/adult audio in the first study.

### B5. ASR accuracy disparities

The broader fairness literature on ASR performance across speaker demographics is the bridge from B3 to Bucholtz's power framing in [A2](#a2-bucholtz-m-2000-the-politics-of-transcription), and to the ISLS 2027 *Act Local, Think Global* theme. Koenecke has prior work here. `[unverified — the canonical 2020 PNAS racial-disparity ASR paper was not re-checked in this pass; verify author list and venue before citing]`

### B6. Adjacent tooling

[WhisperX](https://github.com/m-bain/whisperX) (forced alignment + VAD + diarization, word-level timestamps) and [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped) matter operationally: word-level timestamps are what make the time-anchored unit spine in [03](./03-whisper-concord-spec.md#the-alignment-problem) possible. Your existing pipeline already runs `whisper large-v3` → `pyannote` diarization, which is most of the way there.

---

## C. LLM-assisted qualitative coding

The fastest-moving of the four bodies, and the one where this document's first draft was most overconfident.

### C1. The numbers do not line up, and that is itself the finding

**Revised 2026-08-14.** An earlier draft claimed a clean asymmetry — *deductive coding works, inductive coding does not* — resting on two figures: GPT-4o reaching 96% agreement and **κ = 0.71** applying a human codebook to medical-education transcripts, versus only **31%** of GPT-4's inductively generated codes matching human ones. Those were flagged `[verify]` at the time. They should have been flagged harder, because a rigorous study points the **other way**:

> **Zhang, Wu, Xie, Rubino, Graver, Cai, Kim & Carroll (2025)**, on a real Discord-community dataset, report GPT-4 at **Cohen's κ = 0.57 for inductive** coding and **Fleiss' κ = 0.46 for deductive** coding with a pre-established codebook. [AHFE 2025](http://doi.org/10.54941/ahfe1006232) · [Penn State record](https://pure.psu.edu/en/publications/exploring-inductive-and-deductive-qualitative-coding-with-ai-inve/) · [AHFE open access](https://openaccess.cms-conferences.org/publications/book/978-1-964867-71-7/article/978-1-964867-71-7_14)

Deductive **below** inductive, and both only moderate. See [C6](#c6-the-penn-state-group--qualigpt-and-ai4qual) for why this group's numbers deserve particular weight.

**What to actually conclude.** Not "deductive is better" and not "inductive is better." The honest reading is that **reported LLM–human agreement ranges from about κ = 0.46 to κ = 0.71 across studies, and the ordering of inductive versus deductive flips depending on corpus, codebook, model, and prompt.** The variance *between studies* is larger than the difference *between coding modes* within any one of them.

That is good news for your design, and it is worth saying out loud in the paper: if published agreement is that unstable across studies that all treat the transcript as fixed, then **an unmeasured upstream variable is a plausible contributor** — which is the hypothesis your study exists to test.

Design consequence is unchanged: **hold the codebook fixed and human-authored, vary only the transcript.** Not because deductive is demonstrably better, but because it removes a large, poorly-characterized source of variance from a study that is trying to isolate a different one.

### C2. Inter-rater reliability studies, LLM vs. human

- [Investigation of the Inter-Rater Reliability between Large Language Models and Human Raters in Qualitative Analysis](https://arxiv.org/abs/2508.14764) ([PDF](https://arxiv.org/pdf/2508.14764) · [PERC version](https://www.per-central.org/items/perc/6051.pdf)). Physics-education context. **Rates audio transcripts** — closest existing work to yours. After hyperparameter and prompt optimization, ChatGPT-4o and 4.5-preview reached substantial agreement (κ > 0.6) on three themes and moderate on a fourth. Note that "after optimizing prompts" is doing a lot of work in that sentence, and is itself an under-reported researcher degree of freedom.
- **[Exploring Inductive and Deductive Qualitative Coding With AI: Investigating Inter-Rater Reliability Between Large Language Model and Human Coders](https://pure.psu.edu/en/publications/exploring-inductive-and-deductive-qualitative-coding-with-ai-inve/)** — **Penn State authors.** Read this first, and consider it a potential local advisor lead. See [04](./04-coursework-alignment.md#finding-a-local-advisor--this-is-now-concrete).
- [Assessing the Reliability of Large Language Models for Deductive Qualitative Coding: A Comparative Study of ChatGPT Interventions](https://arxiv.org/html/2507.14384). Finding worth carrying: **step-by-step reasoning interventions achieve both validity and high IRR**, approximating a trained human coder. Relevant to Concord's "rationale" requirement — the model is asked to justify, which the literature says also improves the label.
- [Using large language models to complement humans for the coding of social media interactions between science teachers](https://link.springer.com/article/10.1007/s44217-025-00868-x), *Discover Education* (2025). Education context; reports GPT-4o reaching human-comparable inter-coder reliability.
- [Qualitative Coding with GPT-4: Where it Works Better](https://learning-analytics.info/index.php/JLA/article/download/8575/7877/44307), *Journal of Learning Analytics*. **Venue matters** — JLA is inside the ISLS orbit, so this establishes that the topic is legible to your target reviewers.
- [Large Language Models in Qualitative Analysis: Comparing Traditional and Researcher-Interpreted Approaches](https://journals.sagepub.com/doi/10.1177/16094069261426100), *International Journal of Qualitative Methods* (2026).

### C3. Human-in-the-loop workflow design

- [Exploring the Human-LLM Synergy in Advancing Theory-driven Qualitative Analysis](https://dl.acm.org/doi/10.1145/3778354), *ACM TOCHI*. Introduces CHALET (iterative coding → disagreement analysis → conceptualization). The **disagreement-analysis** framing is directly reusable: your cross-condition disagreements are the finding, not noise to be minimized.
- [Human-AI Collaboration in Thematic Analysis using ChatGPT: A User Study and Design Recommendations](https://arxiv.org/pdf/2311.03999).
- [When LLMs fall short in Deductive Coding: Model Comparison and Human-AI Collaboration Workflow Design](https://arxiv.org/pdf/2512.21041).
- [Qualitative Coding Analysis through Open-Source Large Language Models: A User Study and Design Recommendations](https://arxiv.org/html/2602.18352v1). Introduces **ChatQDA**, an on-device platform using open-weight models specifically to preserve data privacy. This is a direct precedent for the "run it locally so the IRB conversation is short" argument in [02](./02-submission-strategy.md#irb--the-penn-state-process) — and a competitor to be aware of.
- [LOGOS: LLM-driven End-to-End Grounded Theory Development and Schema Induction](https://arxiv.org/pdf/2509.24294).
- [How K-12 Educators Use AI: LLM-Assisted Qualitative Analysis at Scale](https://arxiv.org/pdf/2507.17985) ([v3 HTML](https://arxiv.org/html/2507.17985v3)).

### C4. CSCL-specific

At least one CSCL-context study reports that LLM annotation surfaced significant differences in collaborative knowledge construction across CSCL designs, but **did not capture contextual nuance** — human experts remained necessary to interpret patterns. `[unverified — surfaced in search summary without a resolvable citation; find the primary source]` This is the standard ISLS-community caveat and you should expect a reviewer to raise it. Pre-empt it: your design does not claim the model interprets, only that it *labels consistently enough to detect a shift in labeling caused by an upstream change.*

### C5. ASR accuracy disparities

See [B5](#b5-asr-accuracy-disparities).

### C6. The Penn State group — QualiGPT and AI4Qual

**This is the most important entry on this page for practical purposes, because these people are down the hall.**

**[He "Albert" Zhang](https://he-zhang.com/)** ([hpz5211@psu.edu](mailto:hpz5211@psu.edu), [IST directory](https://ist.psu.edu/directory/hpz5211)) is a fifth-year PhD candidate (ABD) in Informatics at Penn State's [College of IST](https://ist.psu.edu/), advised by **Distinguished Prof. John M. Carroll**, working closely with **Prof. ChanMin Kim** (College of Education) and Prof. Syed M. Billah. Student member of Penn State's [Center for Socially Responsible AI](https://csrai.psu.edu/). His dissertation is titled **"Integrating Large Language Models into the Qualitative Research Process."**

He calls the research programme **AI4Qual** — 11 works and counting. The relevant ones:

| Work | Venue | What it is |
|---|---|---|
| **QualiGPT: GPT as an Easy-to-Use Tool for Qualitative Coding** | [arXiv:2310.07061](https://arxiv.org/abs/2310.07061) (2023) | The tool. API-based (not the chat interface), built for privacy, prompt customization, and thematic analysis workflow integration. |
| **When Qualitative Research Meets LLM: Exploring the Potential of QualiGPT** | [arXiv:2407.14925](https://arxiv.org/abs/2407.14925) (2024) | QualiGPT in front of working researchers — where it saves labour and **where they refuse to delegate**. |
| **Harnessing the Power of AI in Qualitative Research: Exploring, Using and Redesigning ChatGPT** | [*Computers in Human Behavior: Artificial Humans* (2025)](https://doi.org/10.1016/j.chbah.2025.100144) | Trust is renegotiated at the point of **re-scoping**, not at first contact. |
| **Exploring Inductive and Deductive Qualitative Coding with AI** | [AHFE 2025](http://doi.org/10.54941/ahfe1006232) | The κ numbers in [C1](#c1-the-numbers-do-not-line-up-and-that-is-itself-the-finding). |
| **When the Interviewer Is a Bot: Behavior, Breakdowns, and Trust in MLLM-Led Interviews** | HCOMP 2026 | What participants withhold from a machine interviewer. |
| **AI4Qual: A Comprehensive Field Guide to LLM-Supported Qualitative Research** | [Tutorial, IUI 2026](https://doi.org/10.1145/3742414.3794947), Limassol, July 2026 | Half-day hands-on tutorial. Zhang was lead organizer and instructor. |

**Read the dissertation arc as he states it on his own site**, because it hands you your positioning:

> 1. (2023) Can a general-purpose LLM code qualitative data at all?
> 2. (2025) Do researchers trust it once confidential transcripts are involved?
> 3. (2025) Does it agree with human coders closely enough to count?
> 4. (2026) And if the model runs the interview itself — what do people withhold?
> 5. **still open — Where must a human stay in the loop, and how do we teach that?**

He also scopes the programme explicitly: *"Covers the full qualitative pipeline — coding, inter-rater reliability, interviewing, follow-up generation, and the ethics of each."*

**Note what is not in that list: transcription.** Every one of those works begins from a transcript that already exists. The stage where audio becomes text — the stage this project is about — sits immediately upstream of his entire programme and is unexamined by it. His open question 5 ("where must a human stay in the loop") has an answer nobody has proposed: *at the transcription decision, because that is where the methodological commitment is made and currently nobody makes it.*

That is a complementary contribution, not a competing one — which is the right relationship to have with the most productive group in your subfield at your own institution.

**Practical notes.** Zhang is ABD in year five, so he may be on the market; check before assuming he will still be at Penn State in 2027. Carroll and Kim are faculty and are the durable contacts — and **Kim is in the College of Education**, which is the bridge to the ISLS/learning-sciences side. Zhang reviews for the *Journal of Learning Analytics* and the *International Journal of Qualitative Methods*, and is Associate Chair for the CHI 2027 full paper track — so this group is legible to exactly the venues in [02 §Backup venues](./02-submission-strategy.md#backup-venues). Approach guidance in [04](./04-coursework-alignment.md#finding-a-local-advisor--this-is-now-concrete).

---

## D. Quantitative Ethnography — the methodological home

This is the sub-community inside ISLS whose entire premise is closing the loop between qualitative coding and quantitative modeling. If the paper has a natural reviewer pool, it is here.

- [ISLS Quantitative Ethnography research-topic page](https://www.isls.org/research-topics/quantitative-ethnography/) — confirms QE is an ISLS-recognized topic area, which matters for track selection and keyword tagging.
- [Tools for Quantitative Ethnography](https://www.quantitativeethnography.org/tools/) — the canonical tool list.
- **nCoder** — platform for developing, validating, and implementing automated coding schemes over large text collections. [Shaffer's NAPLES webinar: "Tools of Quantitative Ethnography: Epistemic Network Analysis and nCoder"](https://www.psy.lmu.de/isls-naples/intro/all-webinars/shaffer_video/index.html). **nCoder is the closest existing thing to Concord within the ISLS community, and you must position against it.** The differentiator: nCoder validates a *classifier* against human coding; Concord additionally applies design-based statistical correction (DSL/PPI) so that a fallible judge still yields an unbiased population estimate with an honest interval. Neither varies the *transcript*.
- **Shaffer's ρ / rhoR** — an R package implementing a Monte Carlo rejective test for the generalizability of a binary IRR statistic. This is the QE community's answer to "your κ was computed on a small sample, why should I believe it generalizes." Expect a reviewer from this community to ask for it. Budget for it in the analysis plan.
- **Epistemic Network Analysis (ENA)** — quantifies and visualizes connections among coded elements. A stretch goal, not a v1 requirement: if transcription policy shifts *co-occurrence structure* and not just marginal code rates, that is a much stronger finding than a prevalence shift. Worth a paragraph in Future Work even if unattempted.
- [Scoping the Emerging Field of Quantitative Ethnography](https://link.springer.com/chapter/10.1007/978-3-030-67788-6_1) (Kaliisa et al., ICQE20) — [PDF](https://idealab.sites.clemson.edu/papers/Kaliisa_ICQE20.PDF). Use for the "opportunities and challenges" framing.
- [Critical Quantitative Ethnography (CritQE)](https://link.springer.com/chapter/10.1007/978-3-032-12229-2_4) — the equity-facing branch. Directly relevant to the Bucholtz power framing and the ISLS 2027 theme.
- **ICQE** (International Conference on Quantitative Ethnography) is a plausible **backup venue** if ISLS 2027 does not land. See [02](./02-submission-strategy.md#backup-venues).

---

## E. Prior work that varies the transcript — the falsification attempt

**A first draft of this document claimed: *"no one has held the audio, the codebook, and the coding model constant while varying only the transcription policy, and reported how far the resulting codes move."* That claim was overstated and is retracted.** A deliberate search for counterexamples found several, and one of them materially changes the study design. What follows is what turned up and what survives of the gap.

### E1. The strongest counterexample — and it predicts a *small* effect

**Southwell, R., Pugh, S., Perkoff, E. M., Clevenger, C., Bush, J., Lieber, R., Ward, W., Foltz, P., & D'Mello, S. (2022). "Challenges and Feasibility of Automatic Speech Recognition for Modeling Student Collaborative Discourse in Classrooms." *EDM 2022*, long paper.**
[Proceedings entry](https://educationaldatamining.org/edm2022/proceedings/2022.EDM-long-papers.26/index.html) · [PDF](https://educationaldatamining.org/edm2022/proceedings/2022.EDM-long-papers.26/2022.EDM-long-papers.26.pdf)

Two numbers from this literature that you must confront head-on:

- Prior work reported a **4.2% decrease in accuracy** for classifying collaborative skills using ASR transcripts versus human transcripts.
- A **word error rate of 57%** decreased classifier performance by only **20%** relative to perfect transcription.

The interpretation offered: *the constrained, contextualized nature of conversation makes discourse-level NLP models robust to modifications of individual words.*

**Take this seriously. It is a direct prediction that your study will find a small or null effect.** That is not a reason to abandon it — it is a reason to redesign around it. See [Consequences for the design](#consequences-for-the-design) below.

Related, same research programme: [Investigating Automated Transcriptions for Multimodal CPS Detection in Groupwork](https://link.springer.com/chapter/10.1007/978-3-031-93965-5_15) and [Computational Modeling of Collaborative Discourse to Enable Feedback and Reflection in Middle School Classrooms](https://dl.acm.org/doi/10.1145/3636555.3636917) (LAK 2024).

### E2. Transcription *convention* has been varied — in a different task

[Can Authorship Attribution Models Distinguish Speakers in Speech Transcripts?](https://arxiv.org/pdf/2311.07564) ran the same analysis over two transcription encodings of the same speech — BBN (with punctuation and capitalization) versus LDC (limited or no punctuation and capitalization) — and reports that transcription style can have a **surprisingly large impact on performance**, though the effect was modest for their specific n-gram-heavy feature set.

So the *experimental move* — hold audio and analysis constant, vary transcription convention — has precedent. It has simply never been aimed at qualitative coding.

### E3. ASR error propagation is a mature field

Error propagation through cascaded ASR→NLU systems is well studied, and the field's own conclusion undercuts naive WER-based reasoning: [Analyzing Error Propagation in Korean Spoken QA with ASR–LLM Cascades](https://arxiv.org/html/2605.17443) and the practitioner literature on [why WER misleads](https://www.gladia.io/blog/what-is-wer) both make the point that a low WER can coexist with total task failure, because word-level accuracy is not semantic preservation.

Also relevant: [A Comparative Analysis of Automatic Speech Recognition Errors in Small Group Classroom Discourse](https://dl.acm.org/doi/fullHtml/10.1145/3565472.3595606), which reports WER of **0.822 (Google) and 0.847 (Whisper)** on *student* speech in classrooms — catastrophically high, and a strong argument for keeping K-12 classroom audio out of a first study. Compare [B4](#b4-kid-whisper-and-the-classroom-audio-gap).

### E4. Preprocessing decisions are made, but not studied

Several LLM-coding papers describe their preprocessing pipeline — [one removes filler words, inaudible markers, and speaker labels, normalizes whitespace, and corrects spelling](https://arxiv.org/html/2508.07517v1); another concludes that aggressive lexical normalization is unnecessary and keeps punctuation and stop-words intact. **These are contradictory choices, made in passing, justified by nothing, and never compared.** That is the residue of the gap: the decision is being made constantly and studied never.

### What actually survives

The original claim was wrong in scope. The narrower claim appears to hold:

| Dimension | Prior work (E1–E3) | This study |
|---|---|---|
| **Framing** | ASR output is **error**, measured against a single human ground truth. A quality question. | Transcription is **policy**, with no single ground truth. A theory-selection question, per [Ochs](#a1-ochs-e-1979-transcription-as-theory) and [Bucholtz](#a2-bucholtz-m-2000-the-politics-of-transcription). |
| **Conditions** | 2 (human vs. ASR) | N researcher-authored policies, spanning both Bucholtz axes |
| **Analyzer** | Supervised classifiers over n-gram and prosodic features — the things demonstrated to be robust to word-level perturbation | **LLM judges applying a human codebook**, which read surface text far more directly and have no such robustness result |
| **Outcome measure** | Classifier accuracy against human labels | Corrected **code prevalence** with honest intervals (DSL/PPI), which is what a qualitative claim actually rests on |
| **Unit of analysis** | Fixed | **Treated as a dependent variable** — see [03 §Finding 1](./03-whisper-concord-spec.md#finding-1-unitization-is-punctuation-dependent). Nobody has looked at this. |

**Revised gap statement:** *the effect of transcription convention on downstream analysis has been measured for supervised classifiers and found small; it has not been measured for LLM-based qualitative coding, where the analyzer reads surface text directly, and it has never been framed as a researcher-controlled policy rather than as ASR error.*

That is a smaller claim than the first draft made. It is also defensible, and a reviewer who knows the Southwell line of work will respect a paper that cites it up front rather than one that appears not to know it exists.

### Consequences for the design

E1 is a real threat, so plan for it:

1. **Pre-register an equivalence test.** If the honest expected outcome is "no difference," then *demonstrating equivalence within a stated bound* is the finding, and it is a useful one — it would license the field to use clean verbatim without anxiety. Concord ships `tostEquivalence`; pick δ in advance. See [03 §Statistics](./03-whisper-concord-spec.md#statistics--and-concord-already-ships-them).
2. **Choose disfluency-sensitive constructs.** Southwell's robustness result is about *topical* and *skill* classification. Codes for **hesitation, uncertainty, epistemic stance, tentativeness, struggle, or affective discomfort** live *in* the disfluencies. If transcription policy moves anything, it moves those. Pick constructs where the mechanism is plausible; do not test where you expect nothing and then report nothing.
3. **Report the unit-boundary effect separately.** Even if code prevalence is stable, unit counts almost certainly are not. That is an independent finding requiring no effect on the codes at all.
4. **Cite E1 in your introduction, not your limitations.** "Prior work found discourse-level classifiers robust to transcription variation; we ask whether that robustness extends to LLM judges, which read surface text directly" is a stronger opening than any gap claim.

---

## The three framings of the study, in ascending ambition

1. **Instrument paper (safest).** "Here is a pipeline that makes transcription policy explicit and auditable, and here is what it reveals." → *Interactive Tools & Demos*, 4 pages. Recommended, see [02](./02-submission-strategy.md#recommendation). **Note that this framing survives a null result intact**, which given [E1](#e1-the-strongest-counterexample--and-it-predicts-a-small-effect) is a substantial part of why it is recommended.
2. **Sensitivity-analysis paper.** "Code prevalence for construct X shifts by N points between clean- and full-verbatim transcription of identical audio; here is the interval." → poster or short paper. Requires a gold-coded corpus, and requires the effect to exist.
3. **Methodological-critique paper (most ambitious, highest risk).** "Published qualitative findings using ASR transcription carry an unreported researcher degree of freedom, and here is its magnitude." → long paper. Requires a large sample, will draw hostile review, and [E1](#e1-the-strongest-counterexample--and-it-predicts-a-small-effect) may simply refute it. Do not attempt first.

Everything needed for framing 1 exists. Whisper's prompt gives you the policy knob. Concord gives you the codebook, the judge, the gold calibration, and the error correction. The QE literature gives you the reliability statistics reviewers will demand. Ochs gives you a forty-seven-year-old warrant for why anyone should care.

---

## What I could not verify in this pass

Recorded honestly so future-you does not treat these as settled:

- **The ISLS 2027 call for proposals itself.** `2027.isls.org` and the 2026 sub-pages are client-rendered and returned empty bodies to direct fetch; the Chrome extension was not connected in this session. All ISLS specifics below came from search-engine summaries of those pages. **Open the site directly and confirm before acting on any date.**
- **The full text of the two key ISLS papers.** [Lopez-Fierro & Nguyen (CSCL 2024)](https://repository.isls.org/bitstream/1/10537/1/CSCL2024_3-10.pdf) and [Mathur & Shapiro (ICLS 2022)](https://repository.isls.org/bitstream/1/8993/1/ICLS2022_19-26.pdf) were characterized from abstracts and repository metadata only; `repository.isls.org` also returned empty to automated fetch. These two are the most important things on this page to read yourself.
- **The Southwell et al. (EDM 2022) paper in full** ([§E1](#e1-the-strongest-counterexample--and-it-predicts-a-small-effect)). The 4.2% and 57%/20% figures came from search summaries and appear to be that paper's *citations of earlier work* rather than its own results. **Trace them to their original sources before putting either number in a submission** — they are load-bearing for the design decision to plan for a null.
- The GPT-4o `κ = 0.71` / 31%-inductive-match pairing in [C1](#c1-the-numbers-do-not-line-up-and-that-is-itself-the-finding).
- Oliver, Serovich & Mason (2005) full citation ([A4](#a4-naturalized-vs-denaturalized-transcription)).
- Jefferson (2004) page numbers ([A3](#a3-jefferson-transcription-notation)).
- The specific CSCL LLM-annotation study in [C4](#c4-cscl-specific).
- Whether **NCTE** releases audio alongside transcripts. (**TalkMoves is resolved:** transcripts only, no audio or video released — confirmed against the [arXiv abstract](https://arxiv.org/abs/2204.09652) and the [SumnerLab repo](https://github.com/SumnerLab/TalkMoves). See [03 §Candidate corpora](./03-whisper-concord-spec.md#candidate-corpora).)

---

**Next:** [02 — Submission strategy & timeline](./02-submission-strategy.md)
