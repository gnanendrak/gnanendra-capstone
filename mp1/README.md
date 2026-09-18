# MP1 Prompt Lab

## Purpose

This project compares four prompting strategies for extracting three fields from job postings:

- `company`
- `role`
- `years_experience_required`

The notebook evaluates 10 job snippets with four strategies, producing 40 model calls in total.

## Requirements

- Python 3.10 or newer
- An OpenAI API key
- VS Code with the Jupyter extension, or Jupyter Notebook

The required packages are listed in [requirements.txt](requirements.txt).

## Installation

From the `mp1` directory, create and activate a virtual environment:

```bash
cd /path/to/gnanendra-capstone/mp1
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows, activate the environment with:

```bash
.venv\Scripts\activate
```

## Configure the API key

Create a `.env` file in the `mp1` directory:

```env
OPENAI_API_KEY=your_api_key_here
```

Do not commit the `.env` file or expose the API key in the notebook.

## Run the notebook

Open the project in VS Code:

```bash
code .
```

Open [mp1_prompt_lab.ipynb](mp1_prompt_lab.ipynb), select the `.venv` Python interpreter as the notebook kernel, and run the cells from top to bottom.

The notebook runs these stages:

1. Loads the JSONL snippets and golden answers.
2. Builds zero-shot, few-shot, structured, and CoT prompts.
3. Executes 40 asynchronous model calls.
4. Parses each response as JSON.
5. Scores each extraction against the golden set.
6. Uses the judge model to assign a score from 1 to 4.
7. Builds the performance comparison table.

The expected status messages are similar to:

```text
Loaded 10 snippets, 10 golden entries.
Got 40 results.
Scored 40 results.
```

## Interpreting the comparison table

### Accuracy (mean of 3)

This is the average number of correct fields per response. The maximum is `3.00` because the notebook evaluates `company`, `role`, and `years_experience_required`.

- `3.00` means all three fields were correct on average.
- `2.00` means two fields were correct on average.
- Lower values indicate more extraction errors.

### Parse rate

This is the percentage of responses that were successfully parsed as JSON. A `100%` parse rate means the output format was valid for every call. A valid JSON response can still contain incorrect field values, so parse rate should be considered separately from accuracy.

### Judge score (out of 25)

The LLM judge assigns a score from 1 to 4, which is converted to a 25-point scale:

```python
average_judge_score * (25 / 4)
```

For example, an average judge score of `3.2` becomes `20.00/25`.

### Total cost

This is the estimated API cost for the 10 calls made by one strategy. Longer prompts, examples, and additional instructions generally increase input-token cost.

### Latency p50

This is the median response time in seconds. A lower value indicates faster typical responses. Latency can vary between runs because of network and service conditions.

## Current result interpretation

The current comparison shows:

- Few-shot and Structured achieved the highest accuracy at `3.00/3`.
- Zero-shot achieved `2.90/3` and was the cheapest strategy.
- CoT achieved `2.80/3`, the lowest accuracy in this run.
- All strategies achieved a `100%` parse rate.
- Structured was fastest at `1.673` seconds.
- Structured was also the most expensive, while Zero-shot was the least expensive.

These results suggest that Structured prompting offers the best balance of accuracy and latency, while Zero-shot is preferable when minimizing cost is the main concern. CoT did not show a clear advantage for this structured extraction task.

## J10 edge case

J10 is important for interpreting correctness. Its expected value for `years_experience_required` is `null` because the posting does not state a specific experience requirement.

This differs from `0`:

- `null`: no specific experience requirement is stated.
- `0`: the posting explicitly says that no experience is required.

The model must not replace missing information with `0` or invent a numeric value.

## Inspect detailed results

To inspect all imperfect extractions after the scoring cell has run:

```python
display(
	df[df["accuracy"] < 3][
		[
			"strategy",
			"snippet_id",
			"accuracy",
			"llm_judge_score",
			"extracted",
		]
	].sort_values(["snippet_id", "strategy"])
)
```

To inspect J10 specifically:

```python
display(
	df[df["snippet_id"] == "j10"][
		["strategy", "extracted", "accuracy", "llm_judge_score"]
	]
)
```

## Troubleshooting

### Missing API key

If the notebook reports `Set OPENAI_API_KEY first`, check that `.env` exists in the `mp1` directory and restart the notebook kernel.

### Data file not found

Run the notebook with `mp1` as the working directory. These files must exist:

```text
mp1/data/job_snippets.jsonl
mp1/data/golden_set.jsonl
```

### Import errors

Confirm that the notebook is using the same virtual environment where the requirements were installed:

```bash
python -m pip install -r requirements.txt
```

