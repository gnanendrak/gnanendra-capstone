# MP1 Prompt Strategy Comparison

## Summary Comparison Table Showing Performance Metrics

The table summarizes the performance of four prompting strategies across 40 model calls. Accuracy measures the average number of correct fields out of three: `company`, `role`, and `years_experience_required`. Parse rate measures whether the response was valid JSON. Judge score is scaled to 25 points. Cost is the total estimated API cost, and latency is the median response time.

| Strategy | Accuracy (mean of 3) | Parse rate | Judge score (out of 25) | Total cost ($) | Latency p50 (s) |
|---|---:|---:|---:|---:|---:|
| Zero-shot | 2.90 | 100.00% | 20.00 | $0.00043470 | 1.824 |
| Few-shot | 3.00 | 100.00% | 19.38 | $0.00075870 | 1.929 |
| Structured | 3.00 | 100.00% | 19.38 | $0.00077370 | 1.673 |
| CoT | 2.80 | 100.00% | 20.00 | $0.00046470 | 1.741 |

## Key Findings

- **Accuracy:** Few-shot and Structured achieved the highest accuracy at **3.00/3**. Zero-shot followed at **2.90/3**, while CoT scored **2.80/3**.
- **Reliability:** All strategies achieved a **100.00% parse rate**, so every response produced valid JSON. The remaining differences were semantic rather than formatting errors.
- **Judge evaluation:** Zero-shot and CoT received the highest judge score at **20.00/25**. The lower judge scores for Few-shot and Structured, despite their perfect deterministic accuracy, suggest that the two scoring methods applied slightly different evaluation standards.
- **Cost:** Zero-shot was the cheapest at **$0.00043470**. Few-shot cost **$0.00075870**, and Structured was the most expensive at **$0.00077370** because their prompts contained more instructions or examples.
- **Latency:** Structured was fastest at **1.673 seconds**, followed by CoT at **1.741 seconds**, Zero-shot at **1.824 seconds**, and Few-shot at **1.929 seconds**.

## Conclusion

The results show that all four strategies were reliable in producing parseable JSON. Few-shot and Structured prompting produced the strongest field-level accuracy, while Structured prompting offered the best speed-quality balance. Zero-shot minimized cost, and CoT did not outperform the simpler alternatives. Therefore, Structured prompting is recommended for production use when accuracy and latency are more important than minimizing token cost.
