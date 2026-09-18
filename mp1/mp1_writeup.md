# MP1 Reflection: Findings and Recommendations

## Findings

This experiment compared four prompting strategies across 40 model calls. All four strategies achieved a **100% parse rate**, meaning every response was successfully converted into valid JSON. Therefore, the main differences were in extraction accuracy, judge scores, cost, and latency.

- Few-shot and Structured prompting achieved the highest accuracy at **3.00 out of 3**.
- Zero-shot achieved **2.90 out of 3**, showing that simple instructions can still perform well.
- CoT achieved the lowest accuracy at **2.80 out of 3**.
- Zero-shot and CoT received the highest judge scores at **20.00 out of 25**.
- Few-shot and Structured received **19.38 out of 25**, despite achieving perfect deterministic accuracy.
- Structured prompting had the lowest latency at **1.673 seconds**.
- Zero-shot was the cheapest strategy at **$0.00043470**.
- Few-shot was the most expensive strategy at **$0.00075870**.

The difference between deterministic accuracy and judge score is important. Few-shot and Structured prompting achieved perfect field-level accuracy, but the LLM judge gave them lower scores. This may be because the judge used stricter criteria or evaluated the responses differently from the deterministic scoring function.

## Failure Patterns

The main possible errors involved interpreting experience requirements. The dataset included experience ranges, written numbers, approximate values, and missing requirements. These cases can produce valid JSON while still containing incorrect values.

The J10 case is especially important. If no specific experience requirement is stated, the correct value is `null`. This differs from `0`, which means that the job explicitly states that no experience is required. Returning a numeric value for J10 would be considered a fabricated requirement.

Because all strategies achieved a **100% parse rate**, formatting was not a failure pattern in this run. The remaining errors were semantic extraction errors, where the JSON was valid but one or more values did not match the expected answer.

The lower CoT accuracy suggests that adding reasoning instructions did not improve this structured extraction task. In some cases, extra reasoning may introduce unnecessary interpretation.

## Cost and Latency Analysis

Zero-shot was the cheapest strategy at **$0.00043470**, but it did not achieve the highest accuracy. Its latency was **1.824 seconds**.

CoT cost **$0.00046470** and had a latency of **1.741 seconds**. Although it achieved the same judge score as Zero-shot, it had lower deterministic accuracy.

Few-shot prompting had the highest latency at **1.929 seconds** and the second-highest cost at **$0.00075870**. The examples increased the input token count, but they also helped the strategy achieve perfect deterministic accuracy.

Structured prompting was the most expensive strategy at **$0.00077370**, but it achieved perfect accuracy and the fastest latency at **1.673 seconds**. This demonstrates a trade-off between token cost and response speed.

## Recommendations

- Use **Structured prompting** when accuracy, response speed, and predictable JSON output are important.
- Use **Few-shot prompting** when examples are helpful for explaining ambiguous extraction cases.
- Use **Zero-shot prompting** for simple, cost-sensitive tasks where slightly lower accuracy is acceptable.
- Do not assume that CoT will always improve structured extraction performance.
- Add strict JSON schema validation for `company`, `role`, and `years_experience_required`.
- Clearly distinguish `null` from `0` to prevent fabricated experience values.
- Add retry logic for invalid responses or incorrect field types.
- Measure cost per successful extraction instead of total cost alone.
- Test the strategies with a larger dataset and multiple repeated trials.
- Align the deterministic scoring logic and LLM judge rubric so that both evaluate the same three fields.

## Conclusion

The experiment shows that all four strategies produced reliable JSON formatting, but their semantic performance and efficiency differed. Few-shot and Structured prompting achieved the highest deterministic accuracy, while Zero-shot and CoT received the highest judge scores in this run.

Structured prompting is the most practical recommendation because it combined perfect deterministic accuracy with the lowest latency. However, its higher token cost should be monitored. Few-shot prompting is also accurate but less cost-efficient. Zero-shot is inexpensive and reasonably accurate, while CoT did not provide a clear advantage for this structured extraction task.

Future work should focus on semantic validation, J10 null handling, clearer judge instructions, retry logic, and testing on a larger and more varied dataset.