# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---
//for milestone 1 it was 26 chunks

# Unit 1

## What This Does

This is a retrieval-augmented question-answering system built on the campus_life corpus — 88 short posts (student threads, course reviews, housing writeups) about student life at a university. It answers specific, factual questions grounded in those posts: laundry costs and hours by building, course workload and grading structure, dining and dining-dollar policies, study room booking rules, and walking times across campus. Every answer names the source document(s) it came from, and the system refuses to answer questions its documents don't cover rather than guessing.


## Chunking Strategy

**Chunk size:** paragraph based (no fixed character target)
**Overlap:** sentence-boundary-aware, walks back to the start of the last complete sentence rather than a fixed character count

The starter's default 800-character window never actually split anything on this corpus — campus_life posts average 317 characters, so almost none reach 800. That produced 88 documents to 88 chunks, one post always equals one chunk, even for posts covering multiple unrelated topics. The Old Brewhouse post is the clearest example: history, heating, laundry cost, and noise all sit in one chunk, so a question about laundry price would retrieve noise complaints and building history along with it. I switched to splitting on paragraph breaks instead, so each distinct idea in a multi-topic post becomes its own chunk. Paragraphs under 40 characters (mostly short titles) get merged into their neighbor instead of becoming orphan fragment chunks. I initially used a fixed 40-character overlap to carry a bit of the previous paragraph's text into the next chunk, so details near a paragraph boundary wouldn't get lost. That cut mid-word and mid-sentence in several cases (e.g. a chunk opening with "curved, but the lowest midterm is dropped" instead of "Not curved, but..."). I changed the overlap to walk backward to the last full sentence boundary instead of a fixed character count, whatever length that takes, which fixed it — checked by re-sampling 5 chunks and confirming each opened on a complete sentence. This produced 192 chunks from the same 88 documents, averaging 180 characters, ranging from 40 to 397.


## Sample Chunks


======================================================================
Chunk 1  |  source: admin_add_drop_deadline.txt#0  |  produced by: chunker.py::paragraph_split
======================================================================
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.

======================================================================
Chunk 2  |  source: course_cs_340_workload.txt#1  |  produced by: chunker.py::paragraph_split
======================================================================
That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.

======================================================================
Chunk 3  |  source: course_phys_130_exams.txt#1  |  produced by: chunker.py::paragraph_split
======================================================================
Not curved, but the lowest midterm is dropped.

The lab practical is worth 20% and almost nobody prepares for it.

======================================================================
Chunk 4  |  source: dining_verrill_street_grill_followup.txt#0  |  produced by: chunker.py::paragraph_split
======================================================================
Re: Verrill Street Grill

Adding to what people have said about Verrill Street Grill. The wait figure of up to 30 minutes on Friday evenings matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

======================================================================
Chunk 5  |  source: housing_morrow_house.txt#1  |  produced by: chunker.py::paragraph_split
======================================================================
Rooms are singles and doubles, hall bathrooms.

The good: cheapest housing tier by about $900 a year, and the singles are real singles.


## Sample Answer


**Question:** How much does laundry cost at Old Brewhouse?

**Answer:**
Laundry at Old Brewhouse costs $1.50 for a wash and $1.50 for a dry.
Source documents: housing_old_brewhouse_laundry.txt and housing_old_brewhouse.txt

```
```

**My relevance cutoff:** 0.55

I ran my 5 in-corpus questions and the 5 OUT_OF_SCOPE questions through retrieval and recorded the best distance for each. The two groups separated cleanly — worst in-corpus distance was 0.328, best out-of-scope distance was 0.787, leaving a 0.46-wide gap with nothing in it. I set the cutoff at 0.55, roughly centered in that gap, so it's well clear of both my weakest real match and my strongest false match.


| Question | In corpus? | Best distance |
|---|---|---|
| How many two-hour blocks can one person book a study room for per week? | Yes | 0.1928 |
| Do dining dollars carry over from spring to the following fall? | Yes | 0.2130 |
| How much does laundry cost at Old Brewhouse? | Yes | 0.2205 |
| How many washers and dryers are in Aldridge Hall? | Yes | 0.2748 |
| How long does it take to walk from Aldridge Hall to the science quad? | Yes | 0.3283 |
| What is the capital of Mongolia? | No | 0.7873 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.7985 |
| Who won the 1994 World Cup? | No | 0.8474 |
| How do I write a for loop in Rust? | No | 0.8571 |
| How do I change the oil in a diesel engine? | No | 0.8846 |

## How I Used AI

**1.** I asked Claude Code to replace the starter's fixed-800-character chunker with a paragraph-based one, since the default never split anything on this corpus (posts average 317 characters). The first version worked structurally but broke on overlap: it introduced a fixed 40-character slice to carry context between chunks, and that slice regularly landed mid-word or mid-sentence — e.g. a chunk opening with "curved, but the lowest midterm is dropped" instead of "Not curved, but...". It took three rounds of me inspecting the actual chunk output, showing it the exact broken text, and eventually having it show me the real code before it found the actual bug: the word-boundary-recovery logic was discarding the partial word instead of recovering it. I had it change the approach entirely — walk backward to the last full sentence boundary instead of a fixed character count — which fixed it.


**2.** I asked Claude Code to set my relevance cutoff in `config.py` after getting a clean distance report (in-corpus questions clustered under 0.33, out-of-scope ones above 0.78). I told it to set `RELEVANCE_CUTOFF = 0.55`, but the gate kept showing `cutoff 0.6` in every run afterward, including fresh (non-cached) ones. I had it grep the codebase for where `0.6` actually appeared, which showed the real variable controlling the gate was `THRESHOLD`, not `RELEVANCE_CUTOFF` — a variable I'd added that nothing in the pipeline read. I corrected the actual `THRESHOLD` value instead and confirmed the fix with a fresh run.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts | 4 of 5 | ? | ? | ? | ? |
| 5. Answers cite the correct source | 4 of 5 | ? | ? | ? | ? |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->
     
Produced by `run_eval.py::main` — retrieval via `store.py::search`, chunks from `chunker.py::split_documents`. Corpus: campus_life, top-k 5, relevance cutoff 0.55, 3 runs per question, caching off.

**Sample real output:**

```
How much does laundry cost at Old Brewhouse? — run 1

At Old Brewhouse, laundry costs $1.50 for a wash and $1.50 for a dry. 

Sources: `housing_old_brewhouse.txt` and `housing_old_brewhouse_laundry.txt`
```

```
How many washers and dryers are in Aldridge Hall? — run 1

Based on the documents provided, there are eight washers and six dryers in Aldridge Hall (housing_aldridge_hall_laundry.txt).
```

```
Out-of-scope gate — 5 of 5 refused, e.g.:
What is the capital of Mongolia? → refused (best distance 0.787, cutoff 0.55)
```

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer (4 of 5) | MET | All 3 runs scored 5/5 — every question's answer was present in the retrieved chunks every time, with distances well under the 0.55 cutoff (0.19–0.33 range). |
| 2 | Every answer names a source (5 of 5) | MET | All 15 answers across 3 runs named at least one specific source file. |
| 3 | Gate stops out-of-corpus questions (4 of 5) | MET | All 5 OUT_OF_SCOPE questions were refused (distances 0.79–0.89, well above the 0.55 cutoff). This is a single deterministic pass, so the same result applies to all 3 run columns. |
| 4 | Chunks read as complete thoughts (4 of 5) | MET | After fixing the overlap bug in Milestone 3, I resampled 5 chunks and all 5 opened on complete sentences with no mid-word or mid-sentence cuts. Deterministic — same result across all 3 columns. |
| 5 | Answers cite the correct source, not just any source (4 of 5) | MET | Checked all 15 answers: each cited source file matched the question's actual topic (e.g. the laundry question cited the Old Brewhouse laundry doc, not one of the other 4 retrieved-but-irrelevant housing docs). |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->
     
     
No criteria were missed — all 5 hit their targets across all 3 runs.

I'd tighten **criterion 4** (chunks read as complete thoughts, target 4 of 5). As written, I only ever checked 5 chunks out of 192 total by hand — a sample that small could easily miss a boundary problem sitting somewhere else in the corpus. A stronger version: "At least 18 of 20 randomly sampled chunks (out of 192) read as a complete thought, no cut-off sentences at either end." A bigger sample is harder to pass by luck and would actually tell me something about the whole corpus, not just the 5 chunks I happened to look at.

## The Improvement

**What I changed:**

Added a second chunking strategy, `fixed_size_split`, that chunks documents into a fixed ~300-character window with overlap, but snaps both chunk boundaries to the nearest sentence end instead of cutting at a raw character count. I temporarily swapped it in for `paragraph_split` and re-ran the full eval to compare.


**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

My diagnosis in Milestone 3 found no actual misses, but flagged that criterion 4 (chunk boundaries) was only checked against a 5-chunk sample out of 192 — a strategy comparison was the most direct way to test whether a different chunking approach would meaningfully change results, not just spot-check the existing one.

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Answers cite the correct source | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

**Did it help?** 
<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

No, not measurably. All 5 criteria scored identically to the paragraph-split "before" run — same correct facts, same correct sources cited, gate still refusing 5/5 out-of-scope questions. Distances shifted slightly (e.g. washers/dryers moved from 0.275 to 0.322) but stayed well clear of the 0.55 cutoff either way. `fixed_size_split` produced 132 chunks vs. 192 for `paragraph_split` — fewer, slightly larger chunks — but on this corpus, where most posts are already short and single-topic, both strategies land on essentially the same content per chunk. A change more likely to move these numbers would be one that alters what gets *retrieved*, like hybrid search, rather than how already-short documents get sliced.


## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

Nothing failed against my current criteria — all 5 hit their targets across all 3 runs, both before and after the chunking change. But that's a limitation of the test itself, not proof the system is solid: I only wrote 5 test questions, and all 5 are single-fact lookups that appear near-verbatim in one clearly-relevant document. I never tested multi-hop questions (where the answer requires combining facts from two different documents) or cross-document questions (where the system has to correctly pick between several documents covering similar topics, like two different buildings' laundry posts). If I had more time, I'd write a second batch of harder test questions specifically targeting those cases before trusting this system more broadly.


## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->

None of my 5 criteria actually tested multi-hop or cross-document reasoning — they all measure whether a single fact was retrieved and cited correctly, which this corpus makes fairly easy since most answers live in one obviously-relevant document. Next time I'd write at least one criterion specifically targeting a harder case, e.g. "for at least 3 of 5 questions requiring information from two chunks, the answer correctly combines both." A criterion that's only ever tested the easy case doesn't tell you much about where the system actually breaks.
