# What this project is, explained from scratch

**Audience:** someone who has heard of AI language models, vaguely knows they can
read and write text, and knows nothing else. No prior knowledge of this
repository, of statistics, or of qualitative research methods is assumed. Every
term is defined the first time it is used.

**Last updated:** 2026-09-04.

**Companion document:** the sister repository `AITranscribe` has its own
`EXPLAINER.md` covering the research programme this code serves. This document
covers the code and the empirical findings. If you only read one, read this one
first: it is the concrete half.

---

## Table of contents

1. [The thirty-second version](#1-the-thirty-second-version)
2. [The real-world situation this comes from](#2-the-real-world-situation-this-comes-from)
3. [Why a computer, and why this is harder than it sounds](#3-why-a-computer-and-why-this-is-harder-than-it-sounds)
4. [The pipeline, stage by stage](#4-the-pipeline-stage-by-stage)
5. [How do you know if any of it worked?](#5-how-do-you-know-if-any-of-it-worked)
6. [The main discovery: the invisible dial](#6-the-main-discovery-the-invisible-dial)
7. [How we made sure the discovery was real](#7-how-we-made-sure-the-discovery-was-real)
8. [What we got wrong, and how we caught it](#8-what-we-got-wrong-and-how-we-caught-it)
9. [What was actually built](#9-what-was-actually-built)
10. [Why there are 427 tests](#10-why-there-are-427-tests)
11. [What this makes possible](#11-what-this-makes-possible)
12. [What is not done, and what happens next](#12-what-is-not-done-and-what-happens-next)
13. [Glossary](#13-glossary)

---

## 1. The thirty-second version

Lancaster, Pennsylvania held a series of city council meetings in 2025 where
residents came to the microphone to object to a proposed AI data center. Those
meetings are on YouTube. There are dozens of them, each an hour or more long.

We wanted to study what residents actually said. Doing that by hand means
listening to every meeting, typing out every speaker, and then reading every
comment several times while sorting it into categories. For this many meetings
that is months of work.

So we built a machine that does a first pass: it downloads the videos, works out
who is speaking when, converts speech to text, picks out which speeches are
members of the public rather than council officials, and sorts each public
comment into four themes that human researchers had already identified.

Then we did something less common. Instead of taking the machine's output and
writing a paper, we spent our time asking: **how much of this output is real, and
how much of it is an accident of how the software happens to be arranged?**

The answer turned out to be interesting enough that it became the project.

We found a setting nobody had ever thought of as a setting. It was chosen for
speed, it is not mentioned in any methods write-up, and changing it flips
somewhere between a quarter and a third of the difficult judgements. That is the
headline finding, and sections 6 and 7 explain it completely.

---

## 2. The real-world situation this comes from

### The meetings

Lancaster is a small city in Pennsylvania. In 2025 a developer proposed building
an AI data center there. Data centers are large buildings full of computers; they
consume very large amounts of electricity and water, and they generate heat that
has to be removed.

Between July and November 2025, residents showed up at city council meetings to
speak during the public comment period. Public comment is the part of a municipal
meeting where any member of the public can address the council, usually for a
fixed number of minutes. What they said covered a lot of ground: the electrical
grid, drinking water quality, what happens to the hardware when it becomes
obsolete, whether the approval process was fair, who benefits and who pays.

Human researchers read a portion of this material and identified four recurring
themes:

1. **Municipally managed resources and utilities.** The project as a strain on
   things the city owns and runs: electricity, water, waste, and the city budget.
2. **Municipal process.** How the decision is being made, who was consulted, and
   whether the procedure is legitimate.
3. **Health and well-being.** Effects on residents' physical and mental health,
   and on the liveability of the area.
4. **Power dynamics and inequality.** Who has influence over the decision, who
   bears the costs, and how that maps onto existing inequalities.

Each theme has sub-themes underneath it. Here is a real quotation from the
codebook, filed under "water supply, quality, and cost":

> "Potable water, where it's available, especially in a community like ours, that
> is dependent on rainfall to dilute the -- what are we calling them? PFOs in our
> water? It's critical that we save every drop of potable water we have, so they
> shouldn't be going to just cooling uses."

Note the false start, the self-interruption, the speaker groping for a term. That
is what real speech looks like, and it will matter later.

### The analytical stance

One thing worth stating up front, because it shapes everything: the researchers
are **not** checking whether these residents are factually correct. Nobody is
fact-checking the claim about water. The object of study is how community members
narrate risk, assign responsibility, and connect one concern to another. In the
codebook's own words, comments are treated as "situated narratives."

This is a normal and well-established stance in qualitative research. It matters
here because it means the "right answer" for any given comment is a matter of
skilled human judgement, not a fact you can look up. That has consequences for
how you can and cannot evaluate a machine that tries to do the same job.

---

## 3. Why a computer, and why this is harder than it sounds

### The labour problem

The traditional method is called thematic analysis. A researcher reads all the
material, notices patterns, writes down a set of categories (a "codebook"), then
goes back through and assigns categories to every passage. This is called
"coding," and it has nothing to do with programming; in this field, to code
something means to label it.

Coding is slow. Serious qualitative work also expects you to listen to every
recording in full before you transcribe anything, because the first pass through
the data is what tells you what the decision points even are. For dozens of
hour-long meetings, one person is looking at months of work.

So there is an obvious temptation to hand it to a machine. And modern language
models are, genuinely, quite good at this kind of sorting task.

### The trap

Here is the problem, and it is the reason this repository exists.

When a human researcher codes a transcript, every judgement is theirs, and the
choices they made are at least in principle recoverable. When a machine does it,
a very large number of choices get made by whoever wrote the software, and most
of those choices are invisible. They are not written down anywhere. They were
often made for reasons that have nothing to do with the research question, such
as "this way it runs faster" or "this was the default."

That is fine if those choices do not affect the answer. The entire point of this
project is that at least one of them affects the answer a great deal.

We are not arguing that AI cannot do qualitative coding. We are arguing something
narrower and, we think, more useful: **an unexamined engineering step silently
makes methodological choices that the field considers the researcher's to make.**
And we built an instrument that surfaces one of them and measures how much it
moves the results.

---

## 4. The pipeline, stage by stage

"Pipeline" just means a chain of programs where each one's output is the next
one's input. Here is the whole chain. Nothing in this section is unusual; it is
included so the rest of the document makes sense.

### Stage 1: Get the video

`download_playlist.py` pulls the council meeting videos down from YouTube, and
`filter_council_videos.py` narrows the list to the meetings that are actually
relevant. This produces audio files and some metadata (title, date, video ID).

### Stage 2: Diarization, or "who spoke when"

**Diarization** is the task of splitting an audio recording into stretches by
speaker, without knowing who any of them are. The output is a list that says, in
effect: from 0:00 to 0:47 that was Speaker A, from 0:47 to 1:12 that was Speaker
B, and so on. The labels are arbitrary. Speaker A in one meeting has no
relationship to Speaker A in another meeting.

We use a tool called **pyannote** for this. It is a specialised neural network
that does nothing but diarization.

Diarization is genuinely hard. People talk over each other. Microphones get
handed around. Somebody coughs. A council member says "next speaker, please" and
the system may attach those three words to the beginning of the resident's turn.
All of these things happen in our data.

An important detail: pyannote can be run in more than one mode. We have two,
called **standard** and **exclusive**. They differ in how they handle moments
where two people are speaking at once. The practical result is that the same
audio, run through the two modes, produces two slightly different lists of who
spoke when. Twenty-six of our meetings exist in both versions. This turns out to
matter enormously, for reasons that arrive in section 6.

### Stage 3: Transcription, or "what they said"

**ASR** stands for automatic speech recognition: turning audio into text. The
current standard tool is **Whisper**, from OpenAI. We use a fast implementation
of it called faster-whisper.

Whisper is very good. It is not perfect, and its errors are not evenly
distributed: it handles a clear speaker at a good microphone far better than
someone speaking quickly at the back of a room.

Whisper also makes decisions that nobody asked it to make. By default it cleans
things up. It drops many filler words, tidies false starts, and inserts standard
punctuation. If a speaker says "I -- I mean, the thing is, it's, uh, it's not
safe," Whisper may well hand you "I mean, the thing is, it's not safe." Whether
that is an improvement or a destruction of evidence depends entirely on what you
are studying, and Whisper does not ask.

### Stage 4: Blocks

Combining stage 2 and stage 3 gives you text with speaker labels and timestamps.
`extract_commenter_blocks.py` groups that into **blocks**.

A block is one person's continuous speaking turn: everything Speaker C said from
when they started until somebody else started. A block carries a block ID (a
number, unique within its meeting), a speaker label, a start and end time, a word
count, and the text.

Across 78 meetings we have about **10,069 blocks**. That is the fundamental unit
of everything downstream. When you see a percentage in this project, the
denominator is almost always blocks.

Each block also gets a rough category from the diarization step: **recurring** if
that speaker appears a lot in this meeting, **commenter_candidate** if they
appear rarely. The intuition is that council members talk constantly and members
of the public speak once. The intuition is only roughly right, which the prompt
in stage 5 says explicitly.

### Stage 5: Phase 1, "is this a member of the public?"

Now the language model enters. This is `llm_classify_human_themes.py`.

Phase 1 asks a single yes-or-no question of every block: **is this block a
genuine public comment, or is it official business?** A council member calling a
vote is not a public comment. A city attorney explaining a zoning rule is not a
public comment. A resident saying they are worried about their water bill is.

The model is given written instructions (a **prompt**) describing the
distinction. The actual prompt is in `prompts/p1_system.txt` and is worth reading
because it is short and concrete. It lists what disqualifies a block (council
member, mayor, clerk, roll call, invited expert, brief procedural remark) and
what qualifies one (identifies as a resident or local stakeholder, expresses an
opinion or concern about a city decision, is speaking during public comment).

It also contains this warning, which is a small window into how much care this
takes:

> IMPORTANT: these categories are unreliable signals and must not be used as a
> hard filter. Civically active residents often speak in multiple meetings and
> multiple times per meeting, causing them to be classified as "recurring" even
> though they are genuine public commenters.

Of roughly 10,069 blocks, something on the order of 3,000 get flagged as public
comments, depending on which model you ask. That variation is itself a finding
and we will come back to it.

### Stage 6: Phase 2, "which themes does it touch?"

Every block that survived phase 1 goes to phase 2, which scores it against the
four themes. The model receives the full codebook, including the definitions,
the sub-themes, and the anchor quotations, and returns a number between 0 and 1
for each theme, plus a short written justification.

A score of 0 means the theme is absent; 1 means it is squarely on point. In
practice a score above 0.5 is treated as "this theme is present."

### Stage 7: Do it again with a different model

The whole thing is run with several different language models. Seven were run in
total. Five are usable:

| Model | Notes |
|---|---|
| qwen3.5-9b (q4, q5, q6, q8) | The same model at four different compression levels |
| phi-4 | Microsoft |
| gemma-4-4b | Google |
| ministral-8b | Mistral |

Two were excluded from the comparisons: **deepseek-r1-7b** and
**deepseek-r1-14b**. They failed phase 1 in opposite and spectacular directions.
The 7B model flagged 8,882 blocks out of 10,069 as public comments, which would
mean the council said almost nothing all year. The 14B model flagged 195, which
would mean almost no residents spoke. Including them in an agreement calculation
would measure how far a broken run sits from a working one, which is not a
quantity anybody wants. `compare_model_agreement.py` excludes them by default and
has an `--all-models` flag if you ever want to demonstrate the point.

That "q4, q5, q6, q8" business is **quantization**. A language model is a large
pile of numbers. Storing every number at full precision takes a lot of space and
memory. Quantization stores them at reduced precision, so the model becomes
smaller and faster, at some cost in quality. q4 is more compressed than q8. All
four are the same underlying model, squashed to different degrees. This gives us
something valuable: a comparison between two things that are *supposed* to agree,
which is a useful yardstick.

### Why local models

Every model here runs on the machine, on a single NVIDIA RTX A2000 with 12 GB of
memory, using a library called llama.cpp. Nothing is sent to a company's servers.

Two reasons. First, the data is public-meeting testimony from identifiable
private citizens, and shipping it to a third party raises questions we would
rather not have to answer. Second, and more subtly: a hosted model can change
underneath you without telling you. A local file with a known checksum cannot.
For a study whose entire subject is reproducibility, that matters.

The cost is that everything is slow. A full phase-1 pass over the corpus is
several hours of continuous GPU work.

### Provenance

Every output file carries a **provenance** block: which model file produced it
(with size and modification time), a cryptographic fingerprint of the prompt
text, the sampling settings, and the machine, GPU, and library versions in play.

This is unglamorous and it is the thing that saved the project. If you cannot say
exactly what produced a number, you cannot tell the difference between a
discovery and a bug.

---

## 5. How do you know if any of it worked?

This section is about measurement, and it is the part where jargon usually
arrives. There will be two proper names, Krippendorff and Gwet, and I will
explain who they are and what problem each of them was solving. There is no
mathematics beyond arithmetic.

### The problem in its simplest form

You have several coders labelling the same items. They might be humans, or
language models, or the same model run twice. How much do they agree?

The obvious answer is to count. Out of 10,069 blocks, on how many did they give
the same answer? Call that percentage agreement.

### Why percentage agreement lies

Suppose two coders label 10,000 blocks for "is this a public comment," and about
3,000 really are. Now suppose both coders are lazy and say "no" to everything.

They agree on 7,000 of 10,000 blocks. That is 70% agreement, from two coders who
demonstrated no skill whatsoever.

Now make the task more skewed. Suppose only 1% of blocks were public comments.
Two coders who always say "no" agree 99% of the time. You could report "99%
agreement" with a straight face while having measured nothing at all.

This is not a hypothetical problem for us. Our task is skewed: most blocks are
not public comments. Any measure that does not account for this is useless here.

### The fix: subtract the luck

The standard fix is **chance-corrected agreement**. The recipe is:

1. Measure how often the coders actually agreed. Call it `Ao` (observed).
2. Estimate how often they would have agreed by luck alone, given how often each
   coder used each label. Call it `Ae` (expected by chance).
3. Report how much of the *available room above luck* they actually covered:

```
        Ao - Ae
       ---------
         1 - Ae
```

Read that as: "of the improvement that was available over pure chance, what
fraction did they achieve?"

The result is 1.0 for perfect agreement, 0.0 for exactly-as-good-as-luck, and
negative if the coders did worse than random.

Apply it to our lazy coders. They agreed 99% of the time, but two coders who
always say "no" would also agree 99% of the time by chance. So `Ao` is 0.99, `Ae`
is 0.99, and the score is 0.00. The measure correctly reports that nothing
happened.

That is the whole idea. Everything below is variations on how to estimate `Ae`.

### Krippendorff's alpha

**Klaus Krippendorff** was a communications researcher who spent his career on
content analysis, the study of how you systematically categorise media and
documents. In the 1970s he published a measure now called **Krippendorff's
alpha**. Alpha is just the Greek letter, used as a name; it means nothing.

Alpha is the general-purpose workhorse. What makes it worth using over the
simpler alternatives:

- It handles **any number of coders**, not just two.
- It handles **missing data**. If coder 3 never got to meeting 12, alpha copes;
  many alternatives require you to throw the whole item away.
- It handles **different kinds of labels**. Yes-or-no labels, ordered scales like
  "low / medium / high," and plain numbers all work, and alpha knows that on an
  ordered scale, confusing "low" with "medium" is a smaller error than confusing
  "low" with "high." This is done by supplying a **distance function**, which is
  simply a rule that says how far apart two labels are.

The conventional reading, from Krippendorff's own writing: **0.80 and above** is
solid enough to draw conclusions from, **0.667 to 0.80** is good enough for
tentative claims, and below that you should be careful.

Our implementation is in `agreement.py`. It was checked against the worked
example printed in Krippendorff's own textbook and reproduces his published
answers exactly (0.691 treating the labels as unordered categories, 0.811
treating them as numbers). That check runs as part of the test suite, so if
somebody edits the function and breaks it, the tests fail immediately.

### The paradox, and why we needed a second measure

Here is a genuinely surprising thing about chance-corrected agreement, well
documented in the methodological literature and known as the **high agreement,
low kappa paradox**. ("Kappa" is another Greek letter naming another measure in
the same family; Cohen's kappa and Fleiss' kappa are the classic ones. Fleiss'
kappa handles more than two coders.)

The paradox: when almost everything belongs to one category, these measures can
collapse to zero, or go negative, even when the coders visibly agree on nearly
everything.

Here is the real example we tested against, from Kilem Gwet's writing:

| | Coder B says yes | Coder B says no |
|---|---|---|
| **Coder A says yes** | 118 | 5 |
| **Coder A says no** | 2 | 0 |

The two coders agree on 118 + 0 = 118 of 125 items. That is 94.4% agreement. Look
at the table: they are clearly doing the same job.

Fleiss' kappa on this table is **-0.0288**. Negative. Worse than chance.

The reason is that the chance-correction step looked at how lopsided the labels
were, concluded that two coders who both say "yes" nearly always would agree
about this often anyway, and subtracted away essentially all of the agreement.
Mathematically it is doing what it was designed to do. As a description of what
happened, it is misleading.

### Gwet's AC1

**Kilem Gwet** is a statistician who worked on inter-rater reliability and, in
the 2000s, published a measure specifically to fix this. It is called **AC1**,
which stands for "agreement coefficient 1."

The idea behind the fix, stated without mathematics: kappa assumes that when
coders are guessing, they guess in proportion to how often they use each label
overall. Gwet argued this is wrong. Coders do not guess randomly across the whole
dataset; they only guess on the **hard cases**. The easy cases, they simply get
right. So chance agreement should be estimated only over the region where coders
are plausibly uncertain, not over everything.

Estimating chance that way, AC1 on the same table above is **0.9408**, which
matches the eyeball impression.

Both of those numbers, -0.0288 and 0.9408, are checked in our test suite against
Gwet's published values.

### So which do you report?

Both. Always both.

Neither is right in general. Alpha is conservative and will sometimes tell you
that you have nothing when you have something. AC1 is more forgiving and will
sometimes flatter a weak result. Reporting only the one that suits your argument
is a way of lying with real numbers.

Here is our actual case, which shows why:

| What we measured | Krippendorff's alpha | Gwet's AC1 |
|---|---|---|
| All 10,017 blocks, five models | 0.590 | 0.827 |
| Only blocks that somebody flagged (3,224) | 0.234 | 0.256 |

Read the first row. Across everything, the models mostly agree that most blocks
are not public comments. That agreement is real, and it is nearly free, because
most blocks obviously are not. AC1 says 0.827 and is not wrong.

Read the second row. Restrict to blocks that at least one model flagged, and the
skew disappears. Now every item is one somebody thought was a public comment, and
the models are genuinely arguing. Both measures drop hard, and they agree with
each other, because on a balanced dataset the paradox does not arise.

Quoting the first row alone would suggest strong consensus. Quoting the second
alone would suggest chaos. The honest description is: **the models agree easily
about what is obviously not a public comment, and disagree substantially about
the cases that matter.** That sentence needs both rows.

### Jaccard, the simple one

**Paul Jaccard** was a Swiss botanist who, around 1900, wanted to compare the
plant species growing on two different mountainsides. He needed a number for how
similar two lists are. His answer is now called the **Jaccard index**:

```
       number of things on BOTH lists
      ---------------------------------
       number of things on EITHER list
```

If model A flags blocks {1, 2, 3} and model B flags {2, 3, 4}, they share 2 items
and between them name 4, so the Jaccard index is 2/4 = 0.5.

It has no chance correction, so it inherits none of the paradox and offers none
of the protection. It is here because it is easy to explain and easy to check by
hand, which makes it a useful sanity anchor next to the sophisticated measures.

Two Jaccard numbers worth knowing:

- Between **different models**, pairwise Jaccard runs **0.372 to 0.554**. Two
  different language models given the identical prompt and the identical text
  agree on roughly 40 to 55 percent of what they flag.
- Between **the same model at two compression levels** (qwen at q6 versus q8),
  Jaccard is **0.840**.

That second number is not an agreement result. It is a **ceiling**. It says: even
when the two things you are comparing are the same model, differing only in
numerical precision, they still disagree about 16% of the time. Whatever
agreement two genuinely different models could show, it is bounded below that.

### One more idea: the noise floor

This is the concept that ended up mattering most, so it gets its own subsection.

Language models are not deterministic in practice. There is a setting called
**temperature** which controls randomness. We set it to 0, which is supposed to
mean "always pick the most likely next word, no randomness at all." In principle
that makes the model a pure function: same input, same output, every time.

In practice, on a GPU, it does not. Floating-point arithmetic is not perfectly
associative, work gets scheduled across thousands of cores in an order that can
vary, and tiny differences in the last decimal place occasionally tip a
close-run decision the other way. Run the identical job twice and you get
slightly different answers.

That variation is the **noise floor**. It is the amount of change you get from
doing nothing.

The noise floor is the single most important number in an experiment like this,
because **any effect you want to claim has to be bigger than it.** If flipping a
setting changes 3% of your results, and running the same thing twice also changes
3% of your results, you have discovered nothing.

We measured ours. Repeatedly, and we got it wrong twice before getting it right.
Section 7 tells that story.

---

## 6. The main discovery: the invisible dial

### What batching is

When phase 1 asks the model "is this block a public comment," it does not ask
about one block at a time. It sends **three consecutive blocks in a single
request** and asks about all three.

The setting lives in `models.yaml`:

```yaml
settings:
  # Phase 1: blocks per LLM call. At ~100 words/block summary, 3 blocks is about
  # 300 content tokens, leaving headroom for reason fields in large meetings.
  p1_chunk_size: 3
```

There are two reasons for it, and both are reasonable.

The practical reason is speed. Every request to a language model has fixed
overhead: the instructions have to be re-read, the machinery has to spin up.
Batching three blocks per request cuts the number of requests by two thirds.
Across 10,069 blocks and seven models, that is the difference between a run that
finishes overnight and one that does not.

The substantive reason is context. Council meetings have structure. A council
member says "next, we'll hear from the public," then three residents speak, then
the mayor responds. If the model can see the block before and the block after, it
has a better chance of working out what is going on. Judging a fragment in
isolation is genuinely harder.

So: three. Why three and not two or five? Because three fit comfortably in the
available space and ran fast enough. It was an engineering decision.

### The thing nobody noticed

Blocks are numbered in order. With a batch size of 3 starting at block 0, the
batches are:

```
[0 1 2] [3 4 5] [6 7 8] [9 10 11] ...
```

Look at block 4. It is judged alongside blocks 3 and 5.

Now suppose the block list shifts by one, so the batches become:

```
[0] [1 2 3] [4 5 6] [7 8 9] ...
```

Block 4 is now judged alongside blocks 5 and 6.

**The text of block 4 has not changed by a single character.** The prompt has not
changed. The model has not changed. The temperature has not changed. The only
thing that is different is which two other blocks were in the same envelope.

The question is whether that matters. Nobody had ever asked, because nobody had
ever thought of the batch window as a variable. It is not in any methods section.
It is not in any paper. It is a number in a configuration file chosen because it
made a program run faster.

### The accident that revealed it

We did not set out to test this. We stumbled into it.

Recall from section 4 that 26 meetings exist in two diarization variants,
standard and exclusive. The original plan was to use that as a natural experiment
about **transcription policy**: same audio, two different processing routes, so
any difference in the final coding would be attributable to the processing.

So we built `blockmatch.py` to line up the two versions of each meeting and see
how they differ.

The result was not what we expected. The two variants are far more similar than
anybody had assumed:

- **97.3%** of blocks line up one-to-one between the two versions.
- Of those, **99.4% have byte-identical text.** Not similar text. The same
  characters.

That looked, at first, like a dead end. If the two versions produce the same text,
there is nothing to compare.

Except the coding results were not the same. On blocks whose text was identical
across the two variants, the models still gave different answers a lot of the
time.

That should be impossible. Same text, same model, same prompt, different answer.

The resolution is the batching. The 2.7% of blocks that did **not** line up
one-to-one still occupy positions in the list. A block that exists in one version
and not the other pushes everything after it up or down by one. Which means the
batch boundaries land in different places. Which means a block whose text is
identical is nonetheless judged in different company.

So we split the identical-text blocks into two groups: those whose surrounding
3-block batch was also identical, and those where the batch had been reshuffled
by an upstream insertion or deletion.

| Situation | How often the answer changed |
|---|---|
| Identical text, identical batch | **0.22% to 1.27%** |
| Identical text, batch reshuffled | **11.67% to 17.14%** |

The ranges are across the five usable models.

That is a very large difference for a variable nobody knew existed.

### Why the accident was not good enough

This is the part of the project I am most pleased with, and it is a point about
research method rather than about software.

The natural experiment above is suggestive, but it has a flaw that cannot be
patched: **which blocks landed in a reshuffled batch was not random.**

An upstream insertion or deletion happens where the two diarization modes
disagreed. They disagree in specific, non-random places: where people talked over
each other, where the audio was messy, where a speaker change was ambiguous.
Blocks near those places are therefore more likely to be reshuffled, and they are
also, plausibly, harder blocks in general.

So a sceptic can say: you have not shown that reshuffling causes instability. You
have shown that messy parts of the recording are both more likely to get
reshuffled and more likely to be coded inconsistently. The reshuffling might be a
symptom rather than a cause.

That objection is correct, and there is no way to answer it from the natural
experiment. You have to run a real one.

### The designed experiment

`chunk_experiment.py` and `run_chunk_experiment.ps1` implement it.

Pick 12 meetings. Freeze them: exactly the same file, the same blocks, in the same
order, for every condition. Same model. Same prompt. Same temperature. Same
machine, same evening, same model file on disk.

Then run phase 1 five times, changing **only** where the batch boundaries fall:

| Condition | Setting | What it is for |
|---|---|---|
| **A** | size 3, offset 0 | The baseline. What the corpus was actually made with. |
| **A2** | size 3, offset 0 | **Identical to A.** This is the control. |
| **B** | size 3, offset 1 | Every boundary after the first moves by one. Blocks untouched. |
| **C** | size 1 | No batch context at all. Each block judged alone. |
| **D** | size 5 | More context. |

Now every block appears in every condition, so nothing is selected. The sceptic's
objection is gone.

### Why deliberately run a condition identical to another one

Condition A2 is the most important condition in the experiment, and it is the one
that looks pointless.

A2 changes nothing. It is condition A, run again, minutes later, on the same
machine with the same everything. Any difference between A and A2 is pure noise
by construction. It is the noise floor, measured under exactly the conditions of
the effect, rather than estimated from somewhere else.

That last clause is the point. We already had a noise-floor estimate from
comparing our stored corpus against a fresh re-run. But those two runs were three
months apart, and in between, some library had been reinstalled or some driver
updated. That comparison therefore measures noise **plus** whatever changed in
the toolchain. It cannot separate the two.

A and A2 are separated by about half an hour. Nothing changed. That is a clean
floor.

### What we found

Two models, gemma-4-4b and ministral-8b, both run over all five conditions on
1,231 blocks:

| | gemma-4-4b | ministral-8b |
|---|---|---|
| **Control** (A vs A2, nothing changed) | 2.19% | 0.41% |
| **Effect** (A vs B, boundaries shifted) | 12.10% | 7.47% |
| **Ratio** | 5.5x | 18.4x |

Both models: shifting the batch boundary by one changes several times more
classifications than doing nothing at all. The effect is real, and it survives
the strictest control we could build.

Break it down by how hard the block is. A block is **unanimous** if all five
models agreed about it (either all flagged it or none did) and **contested** if
they split:

| Block type | gemma A vs A2 | gemma A vs B | ministral A vs A2 | ministral A vs B |
|---|---|---|---|---|
| Unanimous | 1.01% | 6.08% | 0.10% | 2.53% |
| Contested | 6.97% | 36.48% | 1.64% | 27.46% |

**On contested blocks, both models change their answer between 27% and 36% of the
time when the only thing that changed is which two neighbours were in the
envelope.**

That is the headline. Somewhere between a quarter and a third of the difficult
judgements are being decided by an invisible engineering default.

And note the unanimous row. Even on blocks that every model agreed about, gemma
flips 6.08% of them. This is **not** simply a matter of ambiguity being amplified.
The effect reaches into cases that looked settled.

One more, which is the version I would put in a talk:

> Take the blocks a model flagged as public comments in **both** A and A2. These
> are its stable positives: it said yes twice under identical conditions. Now
> shift the batch boundary by one.
>
> **gemma loses 26.4% of them. ministral loses 18.1%.**

Roughly a fifth to a quarter of a model's own confident, repeated positives
evaporate when you nudge a setting that nobody documents.

### What it actually means

Three things, in order of confidence.

**One, for anyone using an LLM to code text.** The batch window is a research
parameter and must be reported. Right now it is not reported because nobody knows
it is one. If you batch your items for speed, you have made a methodological
choice, and it is not a small one.

**Two, for this project specifically.** This is a cleaner demonstration of the
project's thesis than the one we set out to make. The original plan was to show
that transcription policy silently shapes results. That is a harder case, because
changing the transcription changes the text, and a sceptic can always say the
model reacted to different words. Here the text is byte-identical. There is no
confound left. The only variable is an arrangement decision made by the analysis
software.

**Three, and most honestly.** We do not know whether any of these answers are
*correct*. We have measured agreement, not accuracy. We have no human-coded
ground truth to compare against. This matters most for condition C.

Condition C removes batch context entirely. Gemma's flag count jumps 57% when you
do that. It is very tempting to conclude that batch context was suppressing
flags, and that judging blocks alone is more accurate.

**That conclusion is not available from this data**, and the report the tool
generates says so in writing, on purpose, so that a future reader cannot miss it.
Without human labels there is no accuracy here, only agreement. Condition C tells
you how much of the judgement was coming from the neighbours. Whether that
contribution helped or hurt is a different question that requires humans.

The test suite actually enforces this. `test_report_states_the_condition_c_caveat`
fails if the generated report stops containing that warning. The caveat is a
tested property of the software, not a note in somebody's memory.

---

## 7. How we made sure the discovery was real

The finding above is worth something only because of the work in this section. I
am spelling it out because "how did you check" is the question a reviewer will
ask, and because we got it wrong more than once.

### The noise floor, revised three times

**First attempt (natural experiment).** Comparing identical-batch against
reshuffled-batch blocks within the stored corpus gave a floor of 0.22% to 1.27%
and an effect of 11.67% to 17.14%. Ratio: roughly 17x to 51x.

That ratio is inflated. The floor came from a selected group of blocks (the ones
that happened to sit in an identical batch), and selected groups are not
representative.

**Second attempt (full corpus re-run).** Re-run the entire corpus with gemma and
compare against the stored version. Result: **0.80% of blocks change**, and only
48.7% of meetings reproduce exactly. Against a 13.77% effect, that is 17x.

Better, but still not clean, because June and September are separated by an
unrecorded toolchain change. That 0.80% is noise plus drift.

**Third attempt (the controlled A-vs-A2 condition).** Same machine, same session,
same model file, half an hour apart. Result: **2.19% for gemma.** Nearly three
times higher than the corpus-level estimate.

So the ratio fell from 51x to 5.5x. The effect did not change; our estimate of
the floor did.

**Then ministral replicated it and moved the number again.** Ministral's floor is
**0.41%**, five times lower than gemma's, on the identical corpus with identical
settings. Its ratio is **18.4x**.

The conclusion is not a number. It is this: **there is no single noise floor for
this project. It is a property of the model, and it must be reported per model.**
A paper that quotes one ratio for "LLM coding" is quoting an artifact of whichever
model it happened to use.

Everything above is in `RESULTS.md` with dates and commit hashes, including the
superseded versions. The wrong numbers were not deleted. They are marked as
superseded, with the reason. A reader who finds the 51x figure quoted somewhere
can trace why it was withdrawn.

### The thing that replicated exactly

Amid all that revision, one number stayed put, and it is the strongest evidence
we have.

The natural experiment said the effect on unanimous blocks was **6.09%**. The
controlled experiment, a completely different design on a different subset with a
different sampling scheme, said **6.08%**.

Two independent designs, four significant figures apart. The *effect* was
measured correctly all along. What was wrong was only ever the floor we were
comparing it against.

### The negative result we kept

Not everything worked. `analyze_chunk_context.py` tests whether the effect has a
**direction**: does a block become more likely to be flagged when its neighbours
are themselves public comments? A "contagion" hypothesis.

The answer is no. 47.7% concordant, which is a coin flip, and a z-score of -0.75,
which is nowhere near significant.

A negative result is only worth anything if you can show your test could have
detected the effect had it been there. So the test file contains a **power
check** (feed it fabricated data with a real directional effect, confirm the test
finds it) and a **specificity check** (feed it fabricated data with no effect,
confirm the test stays quiet). Both pass. The null result is therefore
informative rather than merely uninformative.

That specificity check took two tries. My first "no effect" fixture keyed its
pseudo-random behaviour on block *position*, and the block deletion I was
simulating shifts every position, which inverted the rule systematically and
produced 100% disagreement instead of 50%. I had accidentally built a strong
effect into my null condition. The fix was to key the rule on block identity
rather than position, using a stable hash. Then I hit a second version of the
same bug: Python's built-in `hash()` is randomised per process, so the test
passed or failed depending on the run. Switched to SHA-256 and it became stable.

I mention this because it is exactly the class of error the whole project is
about. A subtle dependence on ordering, invisible in the output, changing the
result.

### The standing rule

Out of all this came a rule that now governs the project:

> **Every direction has replicated across two models. No magnitude has.**
> Nothing goes in a paper as a mechanism without at least two models showing it.
> Report magnitudes per model, or lead with the invariants.

---

## 8. What we got wrong, and how we caught it

Four corrections worth recording, because in each case the wrong version was
plausible and had already been written down.

### "Batch context suppresses flagging" -- retracted after 49 minutes

At 00:57 we committed a finding: removing batch context (condition C) makes gemma
flag 387 blocks instead of 247, a 57% increase. The natural interpretation is
that seeing neighbours makes a model more conservative.

At 01:46 we retracted it. Ministral, same corpus, same conditions: 237 blocks at
size 1 versus 240 at size 3. A ratio of 0.99. Flat.

"Context suppresses flagging" is a fact about gemma, not about language models.

What survives on both is more interesting anyway: **membership churn**. Gemma
keeps 94.3% of its size-3 flags when moving to size 1; ministral keeps 80.0%.
Ministral's *total* moved by three blocks while a fifth of its actual selections
changed. The headline count was stable and the underlying set was not. If you
only looked at the count, you would have concluded nothing happened.

### "Five analysis artifacts were lost"

A status document asserted that five analysis scripts had been lost and their
published numbers were therefore unsupported.

They had not been lost. They were sitting in a snapshot of the repository inside
the sister project, dated 2026-07-17, the whole time. Recovered, re-run, and they
reproduce the earlier audit's figures **exactly**: 3,263 flagged blocks, 785
unanimous (24.1%), 1,719 majority (52.7%), Jaccard 0.372 to 0.554.

The status document's section is now marked SUPERSEDED with the original text
preserved underneath.

### The corpus is smaller than every document said

`audit_corpus.py` was written to answer a question that should have been trivial:
how many meetings are there?

Every document said something different. The real answer:

- 81 files on disk
- minus 3 that are empty (a `blocks` list with nothing in it)
- equals 78 coded files
- minus 2 that are stale duplicates in an obsolete file format
- equals **76 real coded files, covering 50 meetings**
- across **53 distinct meetings** in total

The two stale files matter more than the count. They are in an older schema and
their contents had already been **pre-filtered**, meaning somebody had removed
non-comment blocks before saving. Feeding a pre-filtered 31-block file into an
experiment about block context would silently corrupt it. They are now excluded
by name in `chunk_experiment.py`, with a test asserting the exclusion holds.

This audit had its own bug, worth mentioning. My first version reported 29 legacy
files instead of 2, because I checked for the legacy marker before checking for
the modern one, and a group of files carried both. The corrected rule is simple:
a file is legacy only if the modern key is absent.

### The bug that produced valid, empty output

The one that would have been hardest to catch downstream.

Following the project's ASCII-only convention, I did a sweep replacing typographic
dashes with plain hyphens. One of the replacements landed inside a regular
expression in `export_codebook.py` that parses the anchor quotations out of the
codebook. The pattern needed to match either an em dash or a double hyphen. After
the sweep it matched either a double hyphen or a double hyphen.

Result: **zero anchor quotations extracted.** And the built-in validator still
passed, because a construct with no examples is a structurally valid construct.

Perfectly well-formed output, containing nothing. That is the worst failure mode
there is, because nothing complains.

Fixed by using explicit Unicode escapes so no future text sweep can touch it, and
the expected count of 14 quotations is now pinned in a test.

There was a companion bug in the same area. `sample_gold.py` referred to a theme
as `power_dynamics_inequality`, while the pipeline writes
`power_dynamics_and_inequality`. It would have produced a 180-block coding sheet
whose fourth column silently joined to nothing. Caught by a test that asserts the
theme names match the pipeline's.

---

## 9. What was actually built

A tour of the new code. Each entry says what it does and why it needed to exist.

### Measurement

**`agreement.py`** -- the statistics from section 5, implemented from published
definitions with no new dependencies. Krippendorff's alpha with pluggable distance
functions, Gwet's AC1, Fleiss' kappa, Jaccard, Dice. Verified against published
worked examples.

One deliberate design decision worth noting: `jaccard` returns `None`, not 1.0,
when both sets are empty. Two models that flagged nothing have not agreed
perfectly; they have provided no information. Returning 1.0 would silently pull
every average upward. This is enforced by a test.

**`blockmatch.py`** -- lines up two versions of the same meeting using time
overlap rather than text matching, since the text is what we are trying to study.

Its central design decision is that it **refuses to force a one-to-one match.**
When diarization splits one turn into two, or merges two into one, most alignment
tools will pick a winner and discard the rest. This one builds a graph of which
blocks overlap which, finds the connected groups, and labels each group honestly:
one-to-one, split, merge, tangle, or unmatched.

The 97.3% one-to-one figure from section 6 comes out of this, and it is only
trustworthy because the tool was willing to report the other 2.7% as something
other than a match.

### The experiment

**`chunk_experiment.py`** -- selects the frozen 12-meeting corpus and analyses the
results. Selection is deterministic and stated: standard variants only, stale
files excluded, and among the rest the meetings closest to the median block count,
so the experiment is neither dominated by one enormous meeting nor made entirely
of trivial ones.

Determinism here is not fussiness. Each condition is a separate process run
minutes apart. If selection varied between invocations, the conditions would not
share a corpus and the whole design would be void, silently. There is a test that
calls the selector twice and asserts the results are identical.

**`run_chunk_experiment.ps1`** -- runs the five conditions. Each writes to its own
output directory via environment-variable redirection, so the real corpus is never
touched. Resumable: a meeting whose output already exists is skipped.

**`llm_classify_human_themes.py`** (modified) -- the batching logic was pulled out
into a standalone function `p1_chunks(blocks, size, offset)` and exposed as
command-line arguments. The provenance block now records the chunking settings,
so every output file states how it was batched.

### Corpus integrity

**`audit_corpus.py`** -- checks the corpus against itself. Finds files in obsolete
formats, plain files shadowing variant files, outputs with no matching source,
meetings that were never coded, block IDs referring to nothing, and recorded
parse errors.

**`compare_corpus_runs.py`** -- diffs two runs of the same model. This produced
the 0.80% corpus-level noise figure.

**`whisper_io.py`** -- reading and writing transcripts with provenance. Handles
both the old format (a bare list of segments) and the new one (a dictionary with
provenance attached), so old files still load. Closes a gap where the
transcription step recorded nothing about how it had run.

### The Concord bridge

Concord is a separate tool for qualitative text measurement, covered properly in
the sister repository's explainer. Two scripts connect to it.

**`export_vtt.py`** -- exports meetings as WebVTT subtitle files, which is what
Concord imports.

This one has a detail worth preserving. Concord merges adjacent subtitle cues when
the gap between them is small, controlled by a setting called
`maxMergeGapSeconds`. To disable merging entirely we set it to **-1**, not 0. The
reason is that the comparison in Concord's source is `gap <= max`, so at 0 two
cues that abut exactly still merge. Setting 0 and believing you had disabled
merging would quietly fuse turns.

We verified the round trip on all 81 meetings: **81/81 preserve the turn count
exactly**, 0 parse issues, 0 cues without a speaker.

Two findings fell out. At Concord's default of 30 seconds, **11 turns silently
fuse** across the corpus. And Concord offers two ways of dividing text into units:
by speaking turn, giving 10,069 units, or by sentence, giving 20,468. That is a
**2.03x** difference in the number of things you are counting, from a
configuration choice. On individual meetings the ratio runs from 1.00 all the way
to 225.

**`export_codebook.py`** -- converts the human codebook into Concord's format.
Four themes become continuous 0-to-1 measures, plus one binary measure for whether
a block is a public comment. Validated by Concord's own validator.

### Preparing for human coding

**`sample_gold.py`** -- draws a blind, stratified sample for humans to code.

Everything here is a deliberate safeguard against fooling ourselves:

- **Stratified** by how many models agreed, so the sample is not 68% easy cases
  the way the corpus is. Quotas are fixed in advance.
- **Blind.** The file a human codes contains the text and nothing else. No model
  predictions, no vote counts, no hints.
- **Keyed separately.** The answer key is a different file, written at the same
  time. It cannot be consulted accidentally.
- **Weighted.** Because strata were sampled at different rates, each block carries
  an inverse-probability weight so the corpus-level estimate is unbiased.
- **Pre-registered.** A `PREREGISTRATION.md` is written before any coding happens,
  stating what will be measured and how. Deciding the analysis afterwards, once
  you have seen the data, is how researchers accidentally manufacture findings.

### Test probes against real Concord

**`tools/concord_marker_probe.mjs`**, **`concord_roundtrip.mjs`**,
**`concord_validate_constructs.mjs`** -- small programs that import Concord's
actual modules and check behaviour empirically rather than trusting its
documentation. The formatting findings in section 11 come from these.

---

## 10. Why there are 427 tests

The user's instruction on this was explicit and, in hindsight, exactly right:

> "When you test if code you build works, leave those tests lying around in the
> relevant repo rather than stashing them away out of sight, because chances are
> that if you need to test something, it's probably a test that might make sense
> to keep around."

So every check written while building anything stayed. There are 427, and they run
in 39 seconds.

Some of them are unusual and worth explaining, because they show what testing is
for in a research codebase as opposed to a product.

**Tests that pin published values.** `test_agreement.py` checks our alpha against
Krippendorff's textbook answer and our AC1 against Gwet's. If someone optimises
the code and breaks the maths, the tests catch it against an external authority
rather than against our own previous output.

**Tests that pin the real corpus.** `test_corpus_integrity.py` hard-codes which
two files are known-stale and which three are known-uncoded. If a new stale file
appears, the test fails. It is a tripwire on the data, not the code.

**A 250-case grid on one small function.** `test_p1_chunks.py` runs the batching
function across every combination of list length, batch size, and offset, and
asserts one property: **flattening the batches gives back exactly the original
list, in order.**

That is the invariant that matters. A batcher that dropped a block would lower the
denominator of every percentage in the study. One that duplicated a block would
raise it and double-count a classification. Either produces output that looks
completely normal. Since this function is now load-bearing for the project's main
finding, the invariant is asserted across the whole grid rather than spot-checked.

**A test that keeps two files in sync.** `test_conditions_table_matches_the_runner_script`
reads the PowerShell runner and asserts every condition named in the Python is
present in it. If they drift apart, the analysis silently sees fewer conditions
than were actually run, and reports a smaller effect. The test makes the drift
loud.

**A test on prose.** `test_report_states_the_condition_c_caveat` asserts that the
generated report still contains the warning about not reading condition C as
accuracy. The caveat is enforced, not remembered.

Several of these tests found real bugs before the bugs found us: the theme-name
mismatch, the empty-codebook regex, the 29-versus-2 audit error, and two errors in
my own test expectations.

---

## 11. What this makes possible

Concrete things that are now available and were not before.

### Report a batch window the way you report a sample size

Right now, a paper using an LLM to code text will report the model, usually the
prompt, sometimes the temperature. It will not report the batch window, because
nobody knows it is a variable.

We can now say, with a controlled experiment behind it: batching changes 27% to
36% of contested judgements. That is a reporting standard argument, and it comes
with a tool that generates the number for any pipeline.

**Hypothetical.** A team codes 5,000 interview passages for "expressions of
institutional distrust," batching 10 per request for speed. They report 41% of
passages positive. A reviewer asks them to re-run at batch size 1 and at offset 1.
If the number moves to 34%, that is not a footnote; that is the finding being
partly an artifact. Today no reviewer knows to ask. Our contribution is making the
question askable and cheap to answer.

### Measure a pipeline's noise floor before trusting it

`run_repro_check.ps1` and `compare_corpus_runs.py` do this: run the same thing
twice, diff, report.

This should be routine and is not. And our own numbers show why it cannot be
inherited: gemma 2.19%, ministral 0.41%, five times apart on the identical corpus.

**Hypothetical.** A lab is choosing between two models for a coding task. Both
score similarly against a small validation set. One has a 0.4% floor and the other
2.2%. The second model needs roughly five times the sample size for the same
statistical power on any comparison. That is a real budget consequence, invisible
without the measurement.

We also checked whether you could shortcut this. Is a model's noise level
predictive of how sensitive it is to context? Across six models, the correlation
is **r = +0.13**. Essentially zero. **There is no cheap proxy. You have to measure
each model.** A quiet model is not therefore a stable one.

### Compare tools that carve text differently

`blockmatch.py` aligns on time rather than text, which means it can compare
outputs from tools that disagree about where the units are.

**Hypothetical.** A team wants to know whether switching from Whisper to a
different ASR engine changes their conclusions. The two engines segment audio
differently, so a naive diff is meaningless: every unit boundary moved. Aligning
on time and honestly reporting splits and merges lets them separate "the engines
carved it differently" from "the coding actually changed."

### Know what your text formatting is doing to your unit count

The Concord probes answered a question that had been open in the planning
documents: if you want to mark emphasis in a transcript, what notation is safe?

We tested ten notations against Concord's real parser:

| Notation | Result |
|---|---|
| `CAPITALS` | Safe |
| `[square brackets]` | Safe |
| `"quotation marks"` | Safe |
| `*asterisks*` | **Moves unit boundaries** |
| `_underscores_` | **Moves unit boundaries** |
| `^carets^` | **Moves unit boundaries** |
| `{curly braces}` | **Moves unit boundaries** |
| `\|pipes\|` | **Moves unit boundaries** |
| `<angle brackets>` | **Silently stripped** |

The middle group is the dangerous one. Marking emphasis with asterisks does not
just annotate the text; it changes how the sentence splitter divides it, so the
number of units you are measuring changes. Your denominator moves because of your
notation choice.

**Hypothetical.** A researcher marks stressed words with asterisks throughout a
transcript, as one naturally would. Their unit count rises. Every per-unit rate
they report is now computed against a denominator that their annotation style
inflated, and nothing warned them.

### Do human validation properly when it happens

The gold sample is drawn, stratified, blind, weighted, and pre-registered. When
the human coding is done, the analysis is already specified, which means the
result is a test rather than a search.

### Reproduce anything

Every result in `RESULTS.md` carries a date, a commit hash, and enough
configuration to re-run it. Every output file carries provenance. `NOTEBOOK.md` is
append-only, newest first, and includes the retracted claims with the reasons for
their retraction.

**Hypothetical.** Eighteen months from now a reviewer asks where a specific
number came from. The commit hash gives the exact code, the provenance block gives
the exact model file and prompt fingerprint, and the notebook entry gives the
reasoning at the time, including what was believed and later withdrawn. That is a
different situation from finding a spreadsheet called `final_v3_REAL.xlsx`.

---

## 12. What is not done, and what happens next

### The immediate blocker: human coding

This is the honest limitation on everything above. **We have measured agreement,
not accuracy.** We know the models disagree with each other and with themselves.
We do not know which of them is right, because there is no human-coded ground
truth yet.

Until that exists:

- Condition C cannot be interpreted. We cannot say whether removing batch context
  improves or degrades the coding, only that it changes it.
- We cannot say whether the 6% of unanimous blocks that flip under a batch shift
  are borderline cases the models were never sure about, or genuine errors.
- We cannot report accuracy for any model.

The sample is drawn and ready. It needs roughly 8 to 12 hours of a qualified human
reading blocks and assigning labels. There is no way to shortcut this and no
amount of additional compute substitutes for it.

### The third model

Two models have been run through all five conditions. A third, phi-4, is one
condition and a quarter complete. It was launched at 01:43 and terminated at
approximately 02:29 by the tooling that was supervising it, not by any fault of
the run itself; the machine did not reboot, did not run out of memory, and
recorded no crash.

Its state is verified clean: all 15 output files are valid, none truncated, no
recorded errors. It resumes with the same command and needs about three hours.

It matters because two points do not establish a range. The spread in noise floors
(0.41% to 2.19%) and the retraction of the context-suppression claim both rest on
exactly two models.

### Other open questions

- **The dose-response curve.** We tested offset 0 and offset 1. Offset 2 exists.
  If the effect scales with how much the composition changed, that is a mechanism;
  if it is flat, that is a threshold. Different stories.
- **Where the flips are.** Preliminary reading of the changed blocks suggests the
  batching shift specifically damages the distinction between a member of the
  public and an official speaking. That is a strong claim and needs proper coding
  of the changed blocks.
- **Whether "looseness" holds at larger batch sizes.** We have 1, 3, and 5. The
  shape between them is guessed at, not measured.

### Longer-term

- Finish phase 2 for the models that are missing meetings.
- A worked walkthrough of the Concord integration end to end.
- Execute `llms.ipynb`, the teaching notebook, after the recent library upgrade,
  since nobody has confirmed it still runs.

### Housekeeping

There are **14 commits** on the local branch `isls-chunk-framing`. That branch has
no remote tracking branch, so nothing has been pushed. This repository's remote is
GitHub, at `jad507/hands_on_dl`.

One analysis output, `contested_blocks.csv`, contains public-comment text from
identifiable private citizens. This is public-meeting testimony and is already
present in the tracked corpus, so pushing it is not a new exposure. But because
this particular remote is GitHub, confirm the repository is private before pushing
anything.

---

## 13. Glossary

**AC1** -- Gwet's agreement coefficient. A chance-corrected agreement measure
designed not to collapse when one category dominates. See section 5.

**Alpha, Krippendorff's** -- a general-purpose chance-corrected agreement measure
that handles any number of coders, missing data, and several kinds of label. See
section 5.

**ASR** -- automatic speech recognition. Audio to text.

**Batch / chunk window** -- how many blocks are sent to the language model in a
single request. Three, in this project. The subject of the main finding.

**Block** -- one person's continuous speaking turn. The fundamental unit here.
About 10,069 of them across 78 meetings.

**Chance-corrected agreement** -- any agreement measure that subtracts out the
agreement you would expect from luck. See section 5.

**Codebook** -- the written definitions of the categories, with examples. Here:
four themes about the data center, with sub-themes and anchor quotations.

**Coding** -- assigning categories to passages of text. Nothing to do with
programming.

**Concord** -- an external tool for qualitative text measurement, developed by
Ethan Mollick. Covered in the sister repository's explainer.

**Contested block** -- a block the five models split on. As opposed to
**unanimous**, where all five agreed (either all yes or all no).

**Diarization** -- splitting audio by speaker, without identifying who they are.

**Fleiss' kappa** -- a chance-corrected agreement measure for more than two
coders. Vulnerable to the high-agreement paradox. Included for comparison.

**GGUF** -- the file format the local models are stored in.

**Gold sample** -- a set of items coded by humans, used as the reference standard.

**High agreement, low kappa paradox** -- the phenomenon where chance-corrected
measures collapse to zero or below on heavily skewed data despite visibly high
agreement. See section 5.

**Jaccard index** -- overlap divided by union. The simplest similarity measure
here. Named after a Swiss botanist.

**llama.cpp** -- the library that runs the language models locally on the GPU.

**Noise floor** -- how much the results change when you change nothing. The
threshold any claimed effect must clear.

**Phase 1 / Phase 2** -- the two language-model stages. Phase 1 asks "is this a
public comment." Phase 2 scores comments against the four themes.

**Prompt** -- the written instructions given to a language model.

**Provenance** -- the record attached to every output saying exactly what produced
it.

**pyannote** -- the diarization tool.

**Quantization** -- compressing a model's numbers to fewer bits. q4 is more
compressed than q8. Same model, different size and quality.

**Standard / exclusive** -- the two pyannote diarization modes, differing in how
they handle overlapping speech. Twenty-six meetings exist in both.

**Temperature** -- the randomness setting on a language model. Zero means "always
pick the most likely option," which in practice is still not perfectly
deterministic on a GPU.

**Thematic analysis** -- the qualitative method being automated here: read the
material, identify recurring themes, then systematically assign them.

**VTT / WebVTT** -- the subtitle file format Concord imports.

**Whisper** -- OpenAI's speech recognition model. The current default in most
labs.

---

## Where to look next

| I want to... | Read |
|---|---|
| Find a specific number fast | `RESULTS.md` |
| Understand why a decision was made | `NOTEBOOK.md` (newest entries first) |
| Run the pipeline | `README.md` |
| Understand the research programme | `../AITranscribe/EXPLAINER.md` |
| See the experiment design | the docstring at the top of `chunk_experiment.py` |
| See what is checked and why | `tests/`, where every file's docstring explains the risk it guards |
