# Lab 4 — Model comparison: gpt-4o-mini vs gpt-4o

**Cohort member:** Kanala Gnanendra Reddy
**Date:** 11/09/2026

## Numbers (filled in by `scripts/compare_models.py`)

```
Model                    n     Total $     Avg $/q      Time
------------------------------------------------------------
gpt-4o-mini             10    0.000761    0.000076    21.33s
gpt-4o                  10    0.014727    0.001473    23.65s
```

> gpt-4o cost 19.4× more than gpt-4o-mini on the same questions.

## Two-paragraph eyeball reflection

### Paragraph 1 — where the gap mattered

Across most of the ten questions, the two models gave very similar answers, so
the quality gap was not consistently meaningful. The clearest improvement from
`gpt-4o` was for the `schema_version` question: it correctly focused on actual
schema changes such as adding or removing columns and changing constraints,
whereas `gpt-4o-mini` drifted into generic semantic-versioning advice like
"incremented by 1 in the third digit." The `gpt-4o` answer about `response.usage`
was also slightly more precise because it emphasized actual per-request usage,
but the mini answer was still correct and readable. For basic topics such as
RAG, streaming, tokens, and API compatibility, I could not see a material
difference that justified using the more expensive model.

### Paragraph 2 — your rough rule for when to reach for the bigger model

I would switch to `gpt-4o` for questions that require multi-step reasoning,
careful interpretation of ambiguity, or a more reliable synthesis of several
pieces of information. For straightforward factual questions and short
explanations, `gpt-4o-mini` was clear, readable, and faster, so using the
larger model would add cost without a meaningful quality benefit. In this run,
`gpt-4o` cost about 18.7 times more per question ($0.001569 versus $0.000084
on average). I would therefore use `gpt-4o-mini` by default and reserve
`gpt-4o` for high-impact or demonstrably difficult queries where the extra
quality justifies the cost.

## Confidence calibration (optional)

The lab pipeline asks the model to return a `confidence` value in `[0, 1]`.
Skim the persisted rows in SQLite:

```bash
sqlite3 data/answers.db \
  "SELECT model, AVG(confidence), AVG(cost_usd) FROM answers GROUP BY model;"
```

Do the two models report similar confidence on the same questions, or do
they disagree on what they know? One sentence is enough.

The models reported nearly identical average confidence (`0.91` for `gpt-4o` versus `0.90` for `gpt-4o-mini`), suggesting they had a similar view of what they knew despite `gpt-4o` costing much more.
    