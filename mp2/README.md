# Run the Mini-RAG project

This guide covers running the completed [`mp2_rag.py`](./mp2_rag.py) script.
For the overall MP2 brief, project structure, and curriculum context, see the
[project README](../README.md).

## Requirements

- Python 3.10 or newer
- An OpenAI API key with access to `text-embedding-3-small` and `gpt-4o-mini`
- A Qdrant Cloud collection/cluster, or a local Qdrant server

## 1. Set up the environment

From a terminal, change to this `learner` directory and create a virtual
environment:

```bash
cd learner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the environment template and edit `.env` with your own credentials:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY` in `.env`, then load
them into the current terminal session:

```bash
source .env
```

Keep `.env` private; do not commit or share API keys. For local Qdrant setup,
see the commented instructions in `.env.example`.

## 2. Build the vector collection

```bash
python3 mp2_rag.py ingest
```

This loads and chunks the story files in `corpus/`, creates the Qdrant
collection, embeds the chunks, and stores them. **Ingestion deletes and
recreates the existing `mp2_sherlock` collection**, so its current points are
replaced each time you run this command.

## 3. Ask a question

```bash
python3 mp2_rag.py ask
```

Enter a question at the prompt. The assistant answers using retrieved story
excerpts and prints the cited story sections. Submit an empty line or press
Ctrl-C to exit.

## 4. Validate retrieval and answers

```bash
python3 mp2_rag.py validate
```

Validation runs the questions in `data/predefined_questions.jsonl` and, when
`data/learner_questions.jsonl` has been filled in, runs those questions too.
It reports whether the expected source was cited, how many expected facts
appeared in each answer, and the response latency.

To add or change learner questions, edit `data/learner_questions.jsonl`. Keep
one valid JSON object per line and set `expected_source` to the corpus filename
that contains the answer.

## Troubleshooting

- If the script reports a missing API key, run `source .env` again in the
  current terminal. The environment file must contain `export` on each
  variable line.
- If Qdrant is unavailable, verify `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
  and confirm that the cluster/server is running.
- If an OpenAI request reports an exhausted budget or rate limit, the script
  cannot embed queries or generate answers until API access is available
  again.

## Interpreting validation results

The saved run in [`mp2_validation.txt`](./mp2_validation.txt) shows two
separate signals:

- **Source-match** checks whether the expected story appears among the
  retrieved citations. This run matched all five expected sources: 2/2
  predefined questions and 3/3 learner questions.
- **Facts matched** counts expected fact strings found in the generated
  answer. It is a literal, case-insensitive text check, not a judgment of
  semantic correctness. Counts ranged from 1/5 to 5/6 in this run, so a
  correct source match did not always mean the answer covered every expected
  detail.

The reflection in [`mp2_reflection.md`](./mp2_reflection.md) discusses what
these results suggest and what could be improved.