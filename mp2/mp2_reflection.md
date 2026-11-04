# MP2 Reflection

## What worked

The validation run retrieved and cited the expected story for all five
questions: 2/2 predefined questions and 3/3 learner questions. This suggests
that retrieval is identifying the right source reliably for this small test
set. The Engineer's Thumb press-clue question also matched all six expected
facts (6/6), showing that the system could retrieve and explain the clue and
Hatherley's reaction accurately for that question.

## What didn't work

Correct source citations did not always mean complete answers. The run matched
17 of 34 expected facts overall (50%):

| Question | Expected facts matched |
| --- | ---: |
| Red-Headed League assistant | 2/5 |
| Speckled Band murder weapon | 3/6 |
| Blue Carbuncle goose trail | 3/7 |
| Engineer's Thumb press clue | 6/6 |
| Speckled Band method and motive | 3/10 |

The Engineer's Thumb question had full fact coverage, while the multi-part
Speckled Band question had the lowest coverage. The validation harness reports
a check mark based on whether the expected source was cited; fact matches are
reported separately and do not affect that check mark. Also, fact matching is
based on literal, case-insensitive substring checks, so it is a useful
indicator rather than a complete measure of answer quality.

## What I'd change

I would first inspect the retrieved excerpts and generated answers for the
Blue Carbuncle and Speckled Band questions, where several details were missed.
Because those questions require multiple facts or steps, I would try retrieving
more than three chunks and make the answer prompt explicitly address each part
of the question using only evidence in the retrieved text. I would then rerun
the same five questions and compare both source matches and expected-fact
coverage, while checking that latency remains acceptable.

## One surprise

All five answers cited the expected source, but the overall expected-fact
coverage was only 17/34. The most demanding Speckled Band question matched
just 3/10 expected facts, while the Engineer's Thumb question matched all 6.
The run took about 2.8–4.1 seconds per question, averaging approximately
3.6 seconds. This showed that finding the right story is easier than retrieving
enough specific evidence to answer every part of a question.
