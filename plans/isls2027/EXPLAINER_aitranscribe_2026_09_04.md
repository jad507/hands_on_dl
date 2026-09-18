# What this research programme is, explained from scratch

**Audience:** someone who has heard of AI language models, vaguely knows they can
read and write text, and knows nothing else. No prior knowledge of qualitative
research, of this repository, of Concord, or of the `hands_on_dl` project is
assumed.

**Last updated:** 2026-09-04.

**Companion document:** `hands_on_dl/EXPLAINER.md` covers the code and the
empirical results. This document covers the research programme those results
serve: what question is being asked, why anybody should care, what has been built
so far, and what has to happen next.

If you are trying to decide which to read first: read the other one if you want to
know what was found; read this one if you want to know why anyone was looking.

---

## Table of contents

1. [Start here: the argument in one page](#1-start-here-the-argument-in-one-page)
2. [The old idea this rests on](#2-the-old-idea-this-rests-on)
3. [What changed when machines started transcribing](#3-what-changed-when-machines-started-transcribing)
4. [The study, stated plainly](#4-the-study-stated-plainly)
5. [The best demonstration: seven sentences that become one](#5-the-best-demonstration-seven-sentences-that-become-one)
6. [The strongest objection, and how it is answered](#6-the-strongest-objection-and-how-it-is-answered)
7. [Concord, and why it is in the picture](#7-concord-and-why-it-is-in-the-picture)
8. [The three pieces of software and how they fit](#8-the-three-pieces-of-software-and-how-they-fit)
9. [What happened when we started actually running things](#9-what-happened-when-we-started-actually-running-things)
10. [Where each piece stands right now](#10-where-each-piece-stands-right-now)
11. [The plan, and the deadline](#11-the-plan-and-the-deadline)
12. [Honest risks](#12-honest-risks)
13. [Glossary](#13-glossary)

---

## 1. Start here: the argument in one page

Researchers who study human conversation work from **transcripts**: written
versions of what people said. Interviews, classroom recordings, therapy sessions,
city council meetings.

Making a transcript feels like copying. It is not. It is a long series of
judgement calls, and different calls produce genuinely different documents from
the same audio. Do you write down the "um"s? The pauses, and how long they were?
The false starts, where somebody begins a sentence, abandons it, and starts over?
Do you note that a word was said loudly, or sarcastically, or through laughter?

Each of those is a decision about what counts as data. And each one shapes what
you can subsequently find, because you cannot analyse what you did not write down.

For fifty years, the field has treated these as the researcher's decisions, made
deliberately, and defended in the write-up.

Then speech recognition got good. A researcher with forty hours of audio now runs
it through a tool called Whisper and has transcripts by lunchtime. This is a
genuine and welcome advance. But Whisper makes every one of those decisions on the
researcher's behalf. It drops most filler words. It tidies false starts. It adds
punctuation that nobody spoke. It does this silently, it does it inconsistently
depending on audio quality, and it leaves no record of what it removed.

So the methodological choices did not go away. **They moved, from the researcher
to a neural network's default settings, and became invisible in transit.**

This project builds an instrument that pulls those choices back into the open:
makes the transcription policy something you write down and version, runs the same
audio through several different policies, and measures how far the eventual
research findings move as a result.

The claim is deliberately narrow. It is **not** "AI can do qualitative research."
It is not "AI is ruining qualitative research." It is:

> An unexamined automated step silently fixes methodological choices that the
> field considers the researcher's to make. Here is an instrument that surfaces
> them and measures what they cost.

---

## 2. The old idea this rests on

### Ochs, 1979

In 1979, Elinor Ochs published a paper called "Transcription as Theory." Her
argument, in plain terms:

A transcript looks like a neutral record. It is not. It is a *theoretical
document*. What you chose to write down encodes what you already believed was
important, before you analysed anything.

Her illustrations were concrete. If you transcribe a child's speech in a column
next to the adult's, you have implied a conversation between equals. If you put
the adult first and the child's responses underneath, you have implied that the
adult leads. Same audio, different page layout, different theory of what is
happening, and a reader who was not there cannot tell which was a finding and
which was a formatting choice.

This paper is foundational in the field. It is the reason serious qualitative
methods training spends real time on transcription conventions.

### The practical version of the same point

Here is how a professor who teaches qualitative methods put it in conversation,
and this framing is the direct origin of the study:

Graduate students typically take a single qualitative methods course and come out
not understanding how much labour competent qualitative work actually requires.
Her concrete example: a researcher is effectively obliged to listen to every
recording in full, and manual transcription must come **after** at least one
complete pass through the data. The reason is not diligence for its own sake. The
first pass is what *generates the researcher's decision points.* You cannot know
what matters in this material until you have sat with it.

And her illustration of such a decision point, which is worth quoting because it
is the whole project in one sentence:

> Do you transcribe breaths, pauses, stutters, and false starts, because they
> carry information -- or is it more faithful to trim most of that out?

There is no universal right answer. It depends entirely on what you are studying.

If you are studying **what people argued about at a council meeting**, the "um"s
are noise and removing them makes the document easier to read and code.

If you are studying **hesitation**, or **discomfort**, or **who gets interrupted
and who does not**, then the "um"s and the pauses are your entire dataset, and a
transcript that removes them has destroyed the evidence while looking like a
perfectly good transcript.

### The bet this project makes

The design bet is that the professor is right that the decision must be
researcher-led, **and simultaneously** that the *execution* of the decision is now
automatable.

If both of those hold, then the interesting research object is not "automated
transcription" as a topic. It is:

> **the difference in downstream analytic output when the same audio is
> transcribed under different researcher-authored policies.**

That is a measurable quantity. Nobody had measured it in the way this study
proposes. And measuring it requires building the instrument, which is what the
software here is for.

---

## 3. What changed when machines started transcribing

### What Whisper actually does

Whisper is OpenAI's speech recognition system. It is very good, it is free, it
runs on a laptop, and it has become the default in a great many research labs
essentially overnight.

It also, by default, produces a *cleaned* transcript. Consider a speaker saying:

> "I -- I mean, the thing is, it's, uh, it's not safe. For the kids I mean."

Whisper is likely to hand you:

> "I mean, the thing is, it's not safe for the kids, I mean."

Look at what happened. The stutter is gone. The "uh" is gone. A sentence boundary
was invented and then moved. Punctuation that nobody uttered has been supplied,
and that punctuation now tells a reader how to hear the utterance.

For many purposes this is an improvement. That is exactly why it is dangerous: it
is helpful most of the time, so nobody examines it.

### Three properties that make this worse than a human making the same choices

**It is silent.** A human transcriptionist following a convention writes the
convention down, and a reader can find it. Whisper's cleanup is not documented per
file and leaves no trace of what was removed. You cannot recover the "um" you
never saw.

**It is inconsistent.** Whisper cleans more aggressively when the audio is hard.
Which means the amount of cleanup correlates with recording quality, which
correlates with where in the room somebody was standing, which may correlate with
whether they were a nervous first-time speaker or a confident regular. Your
measurement error is not random with respect to the thing you are studying. That
is the worst kind.

**It is unversioned.** Whisper updates. A hosted transcription service updates
without telling you. A study run in March and a study run in September may not be
comparable, and nothing in either output records the difference. In the sister
repository we hit exactly this: a corpus produced in June does not reproduce in
September, and the cause is an unrecorded change somewhere in the software stack.

### What "policy" means here

The proposed fix is to make the transcription policy an explicit object: a written
configuration file that states what gets kept and what gets dropped, versioned in
the same repository as the analysis, and cited in the write-up the same way a
codebook is.

Two named policies to make this concrete:

- **clean-verbatim** -- drop filler words and false starts, supply standard
  punctuation, produce readable prose.
- **full-verbatim** -- keep everything, mark pauses with their durations, mark
  overlapping speech, do not invent punctuation.

Run the same audio under both. If the research findings come out the same, you
have learned that your finding is robust to transcription policy, which is worth
reporting. If they come out different, you have learned that a decision nobody was
looking at is partly responsible for your result, which is worth reporting a great
deal more.

Either outcome is publishable. That is a good property for a study to have.

---

## 4. The study, stated plainly

The contribution being prepared for the ISLS 2027 conference is a pipeline that:

1. **Makes transcription policy explicit, versioned, and researcher-authored** --
   a file you can read, edit, and cite, rather than a set of defaults inside a
   neural network.
2. **Runs the same audio through several policies** -- so the policy is the only
   thing that differs.
3. **Measures how far the downstream qualitative codes move** as a result, and
   reports that movement with honest uncertainty rather than an impression.

Working title: *Transcription policy as a researcher-controlled parameter:
instrumenting the ASR-to-LLM qualitative-analysis pipeline.*

ISLS is the International Society of the Learning Sciences. The 2027 annual
meeting is in Mumbai, 12 to 16 June 2027. The conference theme is "Act Local,
Think Global: Contextualizing Design, Learning and Technologies."

### Is this venue receptive?

Yes, and this was checked rather than assumed, because the obvious worry is that a
learning-sciences audience would be hostile to anything involving AI and coding.

Two pieces of evidence:

- A student paper called "Making Human-AI Contributions Transparent in Qualitative
  Coding" **won the Naomi Miyake Outstanding Student Paper Award** at CSCL 2024,
  and appears at the front of the volume. A student paper about AI in qualitative
  coding, given the top student prize.
- "Interactive Transcription Techniques for Interaction Analysis" (ICLS 2022) is a
  full-length paper about transcription methodology.

Both the genre and the topic are established at this venue. There is also a
critical strand in the community that is sceptical of automation, and this
project's framing is on that strand's side: the argument is that automation is
quietly taking decisions away from researchers, and here is how to take them back.

---

## 5. The best demonstration: seven sentences that become one

This is the sharpest version of the argument, it takes thirty seconds to present,
and it is the single most persuasive thing in the whole project.

Take the sentence:

> I didn't say he stole the money.

Read it aloud seven times, each time stressing a different word. Each reading
means something genuinely different:

| Stress on | What it means |
|---|---|
| **I** didn't say he stole the money | Somebody else said it |
| I **didn't** say he stole the money | I deny saying it |
| I didn't **say** he stole the money | I implied it, or wrote it, but did not say it |
| I didn't say **he** stole the money | Somebody else stole it |
| I didn't say he **stole** the money | He took it some other way, or borrowed it |
| I didn't say he stole **the** money | He stole some other money |
| I didn't say he stole the **money** | He stole something else |

Seven distinct claims. In a courtroom, or a classroom, or a council chamber, these
are not variations on a theme; they are different statements about the world.

Now run all seven recordings through Whisper.

**You get seven identical transcripts.**

Not seven slightly degraded transcripts. Not seven transcripts with error bars.
Seven files that are byte-for-byte the same. All of the meaning that distinguished
the readings lived in the pitch and timing, and the transcription step does not
represent pitch or timing at all. The information is not damaged; it is **gone**,
at stage one, before any analysis begins.

Anything downstream, no matter how sophisticated, is now working on a document in
which the distinction cannot be recovered. A more powerful language model does not
help. The evidence is not there to reason about.

### Why this is the plan's best asset rather than its worst problem

It would be easy to read that as "so the pipeline fails." It is better than that.

**It is the cleanest possible statement of the Ochs argument.** Ochs said a
transcript is a theory of what matters. Here is a case where the theory is
"prosody does not matter," it was adopted by default, nobody chose it, and it
destroys the entire content of the utterance.

**It supplies the answer to the strongest objection to the whole study**, which is
the subject of the next section.

**It gives the study a principled scope.** The size of a transcription-policy
effect is not one number. It is a function of **where the construct you are
studying lives.**

- Constructs that live in **word choice** ("did they mention water quality?")
  survive transcription almost intact.
- Constructs that live in **structure** ("who interrupted whom?") survive
  partially, and depend on whether your policy preserved overlap and timing.
- Constructs that live in **delivery** ("was that sincere?", "were they
  hesitant?") do not survive at all under a default policy.

That is a real finding with practical consequences, and it turns "the pipeline
scores zero on prosody" from an embarrassment into the result.

---

## 6. The strongest objection, and how it is answered

Good research plans should state the argument most likely to sink them. Here is
this project's.

### The objection

There is existing work that varies the transcript and measures the downstream
effect, and **it reports the effect is small.**

Southwell and colleagues (Educational Data Mining, 2022) classified collaborative
skills from classroom discourse, comparing automatic transcripts against human
ones. Their headline: a **4.2% decrease in classification accuracy** from using
ASR instead of human transcription.

Worse for us, they also found that a **57% word error rate cost only about 20%** of
classifier performance. Fifty-seven percent of the words wrong, and the classifier
still did four-fifths as well.

Their conclusion is reasonable: discourse-level models are robust to word-level
perturbation. If more than half the words can be wrong and the analysis mostly
holds, then fussing over whether "um" was transcribed looks like a rounding error.

An earlier draft of this project's planning documents claimed nobody had varied
transcription while holding audio, codebook, and model constant. **That claim was
overstated and has been formally retracted** inside the literature review. This is
recorded in the repository rather than quietly deleted.

### The three-part answer

**One: plan for the null, in advance.** The design now includes a pre-registered
**equivalence test**. That is a statistical procedure that can conclude "these are
the same, within a margin we specified beforehand," rather than merely failing to
find a difference. The difference matters: "we found no effect" is weak and often
just means the study was too small, whereas "we demonstrated the effect is smaller
than X" is a positive result. Deciding this before seeing the data is what makes it
credible.

**Two: choose constructs where the effect can exist.** Southwell's classifier
looked at collaborative skills, which live largely in word choice, so it is exactly
the case predicted to be robust. The prosody demonstration shows that a construct
living in delivery has a transcription-policy effect of essentially 100%. The
honest framing is therefore not "transcription matters" versus "it does not." It
is: **the effect is a function of where your construct lives, and here is the
gradient.**

**Three, and this is the part that was not planned.** While building the
instrument we found a much cleaner demonstration of the underlying thesis, in a
different part of the pipeline, where the confound Southwell's result relies on
does not exist at all. That is section 9.

---

## 7. Concord, and why it is in the picture

### What it is

Concord is an open-source tool by Ethan Mollick for measuring things in text
systematically. Point it at a body of text, define what you are looking for, and
it produces measurements with statistical properties you can defend.

The relevant part is what it adds beyond "ask a language model and write down the
answer":

**Calibration.** You give it items whose correct answer is known. It works out how
the automated measure relates to the truth, so its output can be adjusted rather
than trusted raw.

**Error correction.** Knowing the measure's error rate, it can correct aggregate
estimates for that error, instead of reporting a biased number.

**Honest confidence intervals.** Its output is "34%, plus or minus 6" rather than
"34%." For a study whose entire point is that a methodological choice moves the
number, being able to say whether a movement is larger than the uncertainty is not
optional. It is the study.

### Why it fits here

There is a stated gap. Concord's own documentation, in a section titled "What's
NOT in v1," opens with:

> "No local Whisper. Transcripts import as VTT/SRT/JSON; audio transcription can
> attach later via any local OpenAI-compatible endpoint."

So Concord starts from a transcript and does not make one. This project starts from
audio and makes transcripts under controlled policies. The piece we would build is
the piece its authors have written down as missing, rather than a speculative
extension.

### The trap we found in its design

While reading Concord's source code rather than its documentation, one detail
turned up that would have quietly wrecked the experiment.

Concord gives every unit of text an ID, and that ID is a **content hash**: a
fingerprint computed from the text itself. Two identical texts get the same ID;
change one character and the ID changes completely.

For most purposes this is elegant. For this experiment it is fatal, and here is
why:

1. The whole design changes the transcription policy.
2. Changing the policy changes the text.
3. Changing the text changes every unit ID.
4. So there is no shared key to line the two conditions up by.

You would have two sets of measurements about the same audio with no way to say
which measurement corresponds to which, which is precisely the comparison the study
exists to make.

The fix, established from the source: comparison must join on **time anchors**
(when the unit starts, and who was speaking), which do survive into the unit
record, rather than on unit IDs. Finding this during planning rather than during
analysis is worth an enormous amount.

### What we since verified empirically

The planning documents raised questions about Concord's behaviour that could only
be settled by running it. Small programs were written that import Concord's real
modules and probe them. Findings:

**Two ways to divide text, and they differ by a factor of two.** Concord can treat
each speaking turn as a unit, or each sentence. On our corpus: turns give **10,069
units**, sentences give **20,468**. That is **2.03 times** as many things being
counted, from one configuration choice. On individual meetings the ratio ranges
from 1.00 to 225. Any per-unit rate you report depends on which you picked.

**A default that silently fuses turns.** Concord merges adjacent subtitle cues
separated by less than a configured gap, defaulting to 30 seconds. At that default,
**11 speaking turns silently fuse** across our corpus. Two different people's
speech becomes one unit attributed to one of them.

Worse, setting the gap to 0 does not disable merging, because the comparison is
"gap is less than or equal to the limit," so cues that abut exactly still merge.
You have to set it to -1. Somebody setting 0 and believing they had disabled
merging would be wrong and would have no indication of it.

**The answer to the emphasis-notation question.** A planning document asked: if you
want to mark stressed words in a transcript, what notation is safe? Tested against
Concord's actual parser:

| Notation | Result |
|---|---|
| `CAPITALS` | Safe |
| `[square brackets]` | Safe |
| `"quotation marks"` | Safe |
| `*asterisks*` | **Changes where units are divided** |
| `_underscores_` | **Changes where units are divided** |
| `^carets^` | **Changes where units are divided** |
| `{curly braces}` | **Changes where units are divided** |
| `\|pipes\|` | **Changes where units are divided** |
| `<angle brackets>` | **Silently deleted** |

The middle group is the dangerous one, because asterisks are the obvious thing to
reach for. Marking emphasis that way does not merely annotate the text; it changes
how the sentence splitter divides it, so **your unit count changes because of your
annotation style.** Every rate you compute then has a denominator your notation
inflated.

The recommendation is CAPITALS, and it is now written down with the evidence
behind it.

---

## 8. The three pieces of software and how they fit

Three separate repositories sit side by side on this machine. They do different
jobs and it is easy to confuse them.

### `AITranscribe` (this repository)

The planning and the new harness.

- `docs/isls2027/` -- seven planning documents: the literature landscape, the
  submission strategy and timeline, the technical specification for connecting to
  Concord, how the work routes through coursework, an audit of the sister
  repository, the prosody stress test, and the execution findings.
- `transcribe2/` -- the new harness. Give it audio or a URL, get aligned
  transcripts from multiple engines under multiple policies, plus a Concord-ready
  subtitle file.
- `SSRI/` -- grant material for a research-institute proposal. Supporting material,
  not software.

#### The one clever idea in `transcribe2`

Worth explaining because it solves a problem that would otherwise be fatal.

The obvious way to compare two transcription approaches is to run both and diff the
output. **This does not work.** Each engine decides for itself where one segment
ends and the next begins. So when the outputs differ, you cannot tell whether the
*policy* produced the difference or whether the two engines simply carved the audio
into different pieces. The confound is unavoidable and it destroys the research
question.

The solution is a **frozen spine**:

```
source (file or URL)
  ffmpeg           -> one canonical 16 kHz mono WAV, used by every engine
  diarize ONCE     -> spine.json   (FROZEN; nothing is permitted to change it)
     whisper           fills in text for those exact segments
     gemma:clean       fills in text for those exact segments
     gemma:verbatim    fills in text for those exact segments
  emit             -> one subtitle file per engine, plus a comparison table
```

Work out who spoke when **once**, freeze that as the skeleton, then have every
engine fill in text for the *same* segments. Comparison then joins on segment ID
with no alignment step whatsoever, because by construction every condition is
describing the identical objects.

The confound is not corrected for afterwards. It is designed out.

### `hands_on_dl`

The existing corpus and pipeline. Lancaster city council meetings, downloaded,
diarized, transcribed, and coded by seven local language models across 78 meetings
and roughly 10,069 speaking turns. This is where the empirical findings come from,
and it has its own full explainer.

Its original purpose was different: it began as teaching material for a deep
learning course, and the research pipeline grew inside it.

### `concord`

Ethan Mollick's measurement tool, cloned locally so its behaviour can be tested
directly rather than inferred from documentation. Everything in section 7 came
from running it.

---

## 9. What happened when we started actually running things

The plan was written in August 2026. In September we started executing it on this
Windows workstation. This section is what actually happened, and it changed the
plan.

The full technical account is in `docs/isls2027/07-windows-execution-findings.md`.
This is the plain-language version.

### The pilot data existed, and it measures something else entirely

The plan's item 5 said, roughly: you already have pilot data and do not know it.
Twenty-six meetings had been processed twice, through two different speaker-
detection settings. Same audio, different processing, same model, same prompt. The
coding results differ. That looked like a free demonstration of the transcription-
policy effect, needing no new data and no ethics approval.

We ran it. The result was not what the plan expected.

The two versions turn out to be **99.4% byte-identical in text**. Not similar.
Character-for-character the same. So the differences in coding cannot be caused by
the text, because the text does not differ.

The actual cause is somewhere nobody had looked.

### The invisible dial

When the language model is asked "is this speaking turn a public comment or a
council member doing official business," it is not asked about one turn at a time.
The software sends **three consecutive turns in one request**, for speed and for
context.

Three was chosen because it was fast and fit comfortably. It is not in any methods
section. It is not in any paper. Nobody had ever thought of it as a setting.

Now: turns are numbered in order. Batches of three starting at turn 0 give you
`[0 1 2] [3 4 5] [6 7 8]`. Turn 4 is judged next to turns 3 and 5.

If the list shifts by one, the batches become `[0] [1 2 3] [4 5 6]`. Turn 4 is now
judged next to 5 and 6.

**The text of turn 4 has not changed by a single character.** Only its company
changed.

Does that matter? It matters enormously.

We built a controlled experiment: twelve meetings, frozen so every condition sees
exactly the same turns in the same order, same model, same prompt, same machine,
same evening. The only thing varied is where the batch boundaries fall. And
critically, one condition is a **deliberate duplicate** of another, changing
nothing at all, so we could measure how much the results move from doing nothing.
That is the baseline any real effect has to beat.

| | gemma-4-4b | ministral-8b |
|---|---|---|
| Changed when **nothing** was changed | 2.19% | 0.41% |
| Changed when the batch boundary **moved by one** | 12.10% | 7.47% |

And on the genuinely hard cases, the turns where different models disagree with
each other:

> **Both models change their answer on 27% to 36% of contested turns when the only
> difference is which two neighbours were in the same envelope.**

Another way to say it: take the turns a model flagged as public comments **twice
in a row** under identical conditions, its most confident results. Shift the batch
boundary by one. **gemma loses 26.4% of them. ministral loses 18.1%.**

### Why this is better than the result it replaced

The original plan was to show that transcription policy silently shapes findings.
That is a good study and it remains the plan. But it has a soft spot: changing the
transcription changes the words, and a critic can always say the model reacted to
different words, which is not surprising.

Here, **the text is byte-identical.** There is no confound left to argue about.
The only thing that varied is how the analysis software happened to group the
items before asking about them.

That is the same thesis -- an unexamined automated step silently makes a
methodological choice -- demonstrated more cleanly than the original design could
manage, on data already in hand.

It is also a broader result. It applies to anyone using a language model to
classify a list of anything, not just to people transcribing audio.

### The obligatory caveat, stated as loudly as the finding

We measured **agreement**, not **accuracy**. We know the models disagree with each
other, and with themselves under a batch shift. We do not know which answer is
right, because no human has coded a reference sample yet.

This matters most for the condition where batch context is removed entirely. One
model flags 57% more turns when judged alone. It is tempting to conclude that
context was suppressing flags and that judging alone is more accurate.

**That conclusion is not available from this data.** The software that generates
the report writes the warning into the report itself, and there is an automated
test that fails if the warning ever disappears.

### A retraction, 49 minutes after publication

Worth recording because it shows the standard being applied.

At 00:57 one night, a finding was committed: removing batch context makes the
model flag 57% more turns, so context must suppress flagging.

At 01:46 it was retracted. The second model, same corpus, same conditions, showed a
0.99 ratio. Completely flat.

"Context suppresses flagging" is a fact about one model, not about language models.

What survives on both models is subtler and more interesting: the **total count**
barely moved for the second model while **20% of the individual selections
changed.** A researcher watching only the headline number would have concluded that
nothing happened, while a fifth of the underlying data changed underneath them.

From this came a standing rule:

> Every *direction* has replicated across two models. No *magnitude* has. Nothing
> is reported as a mechanism without at least two models showing it.

### Three smaller corrections

**Nothing was lost.** A status document claimed five analysis programs had been
lost and their published figures were therefore unsupported. They were in a
snapshot inside this repository the entire time. Recovered and re-run, they
reproduce the earlier figures exactly.

**The corpus is smaller than every document said.** 81 files on disk, minus 3 that
are empty, minus 2 that are stale duplicates in an obsolete format, giving 76 real
files over 50 meetings, from 53 distinct meetings. The two stale files matter more
than the arithmetic: their contents had already been filtered before saving, so
feeding one into an experiment about context would have silently corrupted it.
They are now excluded by name, with a test enforcing it.

**The corpus does not reproduce.** Re-running the same model on the same audio with
the same prompt three months later changes 0.80% of the results, and only 48.7% of
meetings come out identical. The cause is an unrecorded change in the software
stack between June and September. This is a small effect and a large warning: it
is the study's own thesis happening to the study.

---

## 10. Where each piece stands right now

### `transcribe2`: further along than its README says

The README states that the model-free paths are tested but the Whisper and Gemma
engines "have not been run," because the machine it was written on had no GPU and
no model weights.

That machine is not this machine. Checked today:

- **45 tests pass** (plus 8 subtests), in 2.3 seconds.
- **`python doctor.py` exits clean** and reports the core pipeline runnable, with
  every capability available: yt-dlp for URLs, Whisper, Gemma 4 audio, real
  diarization, and pitch extraction for prosody triage.
- ffmpeg, ffprobe, yt-dlp, numpy, faster-whisper, transformers, torch with CUDA,
  accelerate, pyannote.audio, and parselmouth are all present, with an RTX A2000
  and 12 GB of video memory behind them.

Two warnings worth knowing before the first real run:

- **`HF_TOKEN` is unset.** Some pyannote models are access-gated and will not
  download without a token.
- **`torchcodec` cannot load its libraries**, because on Windows it needs the
  "full-shared" FFmpeg build that ships DLLs. pyannote's built-in audio decoding
  will fail; audio may need to be pre-loaded into memory instead. This is the most
  likely thing to break on the first real invocation.

So the honest status is: **the harness has never processed real audio, but every
prerequisite for doing so is now in place and verified.** That is a meaningfully
different position from what the README describes, and the first real run is now a
short task rather than a speculative one.

### `hands_on_dl`: the empirical work

427 tests passing. The chunk-framing experiment complete on two models, one
condition and a quarter into a third. The Concord bridge verified on all 81
meetings. A blind, pre-registered sample drawn and waiting for a human.

Full detail in its own explainer.

### `concord`

Cloned, probed, and characterised. The behaviours in section 7 were measured, not
assumed.

### The planning documents

All seven exist. Document 07 records what execution corrected in the others, and
the index has been annotated so a reader arriving at the original claims is
redirected to the corrections.

---

## 11. The plan, and the deadline

### The deadline is close

ISLS 2026 closed submissions on **20 October 2025** for a June 2026 conference,
after two extensions from an original date of 5 October. Applying the same offset,
the ISLS 2027 deadline is likely **early-to-mid October 2026**.

Today is 4 September 2026. That is roughly **five to six weeks.**

The planning documents, written on 14 August, said seven weeks. That figure is now
stale and should be read as five to six. It also lands on top of a course midterm.

### What has to happen, in order

**1. Human coding. This is the bottleneck and nothing substitutes for it.**

A blind, stratified sample has been drawn from the corpus and is ready. It needs
roughly 8 to 12 hours of a qualified person reading speaking turns and assigning
labels, with no visibility of what any model said.

Everything currently reported is agreement between machines. Without human labels
there is no accuracy, no way to say which model is better, and no way to
interpret what removing batch context does. This one task unlocks more of the
analysis than any other.

The safeguards are already in place: the sample is stratified so it is not mostly
easy cases, the answer key is a separate file, each item carries a weight so the
corpus-level estimate is unbiased, and a pre-registration document states what will
be measured before any coding begins.

**2. Finish the third model.** Two models have been through all five experimental
conditions. A third is partly done and needs about three hours of GPU time. Two
data points do not establish a range, and two of the current claims rest on exactly
two models.

**3. Run `transcribe2` on real audio.** Everything is installed and the
environment check is green. Start with a short clip, expect the torchcodec problem,
and get one meeting through end to end.

**4. Decide what the paper actually is.** This is a genuine strategic choice and it
should be made deliberately:

- **Option A: lead with the batching finding.** It is finished, it is controlled,
  it replicates across models, and it needs no ethics approval. It is a narrower
  claim than the original plan but it is *done*.
- **Option B: lead with transcription policy as planned**, with the batching result
  as supporting evidence that the general mechanism is real.
- **Option C: the pipeline as the contribution**, with both effects as
  demonstrations of what the instrument can find.

Given five to six weeks, Option A has the least risk attached to it. Option B is
the more ambitious paper and needs `transcribe2` to have produced real results
first.

**5. Ethics approval, if human subjects are involved.** Public council meetings are
already public record, but the process should be started early rather than
discovered late.

### Also outstanding

- Finish the second analysis phase for models missing meetings.
- A worked end-to-end walkthrough of the Concord integration.
- Nothing has been pushed. This repository has **5 commits** on the local branch
  `isls-execution-findings`, and the sister repository has 14 on its own branch;
  neither branch has a remote tracking branch. Note that the two repositories push
  to different places: this one to a personal server (`shiro`), and `hands_on_dl`
  to GitHub. One analysis file in the sister repository contains public-comment
  text from identifiable private citizens. It is public-meeting testimony and is
  already in the tracked corpus, so this is not a new exposure, but the GitHub
  repository should be confirmed private before pushing.

---

## 12. Honest risks

Stated plainly, because a plan that only lists its strengths is not a plan.

**The transcription-policy effect may be small.** Prior work predicts it will be,
for constructs that live in word choice. The mitigation is a pre-registered
equivalence test, so a null is a reportable result rather than a wasted study, and
the deliberate selection of constructs where an effect can exist.

**Five to six weeks is tight**, and it overlaps with coursework. The batching
finding being already complete is the main hedge against this.

**`transcribe2` has never processed real audio.** Every prerequisite is verified,
but "the environment check passes" and "it produced a correct transcript" are
different claims, and one known problem (torchcodec) is waiting.

**Nothing has been validated against humans yet.** Everything reported so far is
machines agreeing or disagreeing with machines. This is the largest single gap and
it is addressed by task 1 above.

**Two models is not many.** The noise floor differs fivefold between the two tested
so far. A third would tell us whether that is a range or a coincidence.

**The corpus does not reproduce exactly**, for reasons that predate this work and
are not fully identified. The effect is small (0.80%) and now measured rather than
suspected, but it means results from June and results from September should not be
mixed in a single analysis.

---

## 13. Glossary

**ASR** -- automatic speech recognition. Turning audio into text.

**Batch window** -- how many items are sent to a language model in one request.
The subject of section 9's finding.

**Calibration** -- working out how an automated measure relates to known-correct
answers, so its output can be adjusted rather than trusted raw.

**Clean-verbatim** -- a transcription policy that removes filler words and false
starts and supplies standard punctuation.

**Codebook** -- the written definitions of the categories a researcher assigns,
with examples.

**Coding** -- assigning categories to passages of text. Nothing to do with
programming.

**Concord** -- Ethan Mollick's open-source tool for systematic text measurement,
with calibration and error correction.

**Content hash** -- an identifier computed from a text's own characters. Identical
text gives an identical ID; any change gives a completely different one.

**CSCL / ICLS / ISLS** -- the learning-sciences conference community. ISLS is the
society; CSCL and ICLS are its conferences.

**Diarization** -- working out who spoke when in a recording, without identifying
who they are.

**Equivalence test** -- a statistical test that can positively conclude "these are
the same within a stated margin," rather than merely failing to find a difference.

**Full-verbatim** -- a transcription policy that keeps filler words, false starts,
pauses and overlaps.

**IRB** -- Institutional Review Board, the body that approves research involving
human subjects.

**Prosody** -- the pitch, stress, rhythm and timing of speech. The part that
carries meaning without being in the words.

**Spine** -- in `transcribe2`, the frozen list of who-spoke-when that every
transcription engine must fill text into, so their outputs are directly comparable.

**Transcription policy** -- an explicit, written, versioned statement of what gets
transcribed and what does not. The central object of the study.

**VTT / WebVTT** -- the subtitle file format Concord imports.

**Whisper** -- OpenAI's speech recognition model, now the default in most research
labs.

**Word error rate (WER)** -- the proportion of words a transcription system gets
wrong.

---

## Where to look next

| I want to... | Read |
|---|---|
| Understand the code and the numbers | `../hands_on_dl/EXPLAINER_handsondl_2026_09_04.md` |
| See the framing and the seven things that change the plan | `docs/isls2027/00-INDEX.md` |
| Know what prior work exists and where the gap is | `docs/isls2027/01-literature-landscape.md` |
| Know the deadline and the ethics process | `docs/isls2027/02-submission-strategy.md` |
| See the Concord integration contract | `docs/isls2027/03-whisper-concord-spec.md` |
| See the prosody argument in full | `docs/isls2027/06-prosody-stress-test.md` |
| See what execution corrected | `docs/isls2027/07-windows-execution-findings.md` |
| Run the new harness | `transcribe2/README.md`, starting with `python doctor.py` |

---

## A note on how these documents are written

Everything in `docs/` is written to be committed to version control and read a
year from now by somebody with no memory of the conversation that produced it.

Claims sourced from the web carry links. Claims that were not independently
verified are marked `[unverified]`. Claims read out of source code cite the file
and the function.

And claims that turned out to be wrong are **retracted in place**, with the
original text preserved and the reason recorded, rather than deleted. There are
several such retractions in these documents. That is the system working, not the
system failing: a plan that has never been corrected is a plan nobody has tested.
