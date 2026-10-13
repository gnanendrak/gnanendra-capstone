import os, json
from dotenv import load_dotenv

load_dotenv()

USE_FAKE = (
    False  # <-- set False (and export OPENAI_API_KEY) to judge with the real gpt-4o
)

JUDGE_MODEL = "gpt-4o"  # the STRONG model — judging is where you don't cut corners

RUBRIC = """You are a strict, fair evaluator of answers from a question-answering assistant.
Score the CANDIDATE answer against the IDEAL answer on three dimensions, each 1-4:

- accuracy    : are the facts correct and complete versus the ideal? (1 Poor .. 4 Excellent)
- groundedness: is it supported by the ideal/source, with nothing invented or contradictory?
- format      : is it clear, appropriately concise, and well-structured?

Scale: 1 = Poor, 2 = OK, 3 = Good, 4 = Excellent.
Be strict on accuracy: an answer that omits a key fact or contradicts the ideal cannot score above 2.
Return your scores and a one-paragraph reasoning that names specific facts."""


def build_messages(question, ideal, candidate):
    user = (
        f"QUESTION:\n{question}\n\n"
        f"IDEAL ANSWER:\n{ideal}\n\n"
        f"CANDIDATE ANSWER:\n{candidate}"
    )
    return [{"role": "system", "content": RUBRIC}, {"role": "user", "content": user}]


JUDGE_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_scores",
        "description": "Submit rubric scores and reasoning for the candidate answer.",
        "parameters": {
            "type": "object",
            "properties": {
                "accuracy": {"type": "integer", "minimum": 1, "maximum": 4},
                "groundedness": {"type": "integer", "minimum": 1, "maximum": 4},
                "format": {"type": "integer", "minimum": 1, "maximum": 4},
                "reasoning": {"type": "string"},
            },
            "required": ["accuracy", "groundedness", "format", "reasoning"],
        },
    },
}


def _fake_judge(question, ideal, candidate, must_mention):
    """Deterministic stand-in so the notebook runs offline. A REAL judge reads for meaning."""
    c = candidate.lower()
    hits = [m for m in must_mention if m.lower() in c]
    contradicts = any(
        p in c for p in ["no limit", "unlimited", "whenever you like", "any day"]
    )
    accuracy = 1 if contradicts else (4 if len(hits) == len(must_mention) else 2)
    grounded = 1 if contradicts else 4
    fmt = 4 if len(candidate.split()) <= 40 else 3
    reasoning = (
        f"Mentions {len(hits)}/{len(must_mention)} required facts {hits}. "
        + ("Contradicts the policy (states there is no limit). " if contradicts else "")
        + (
            "Missing a required fact. "
            if hits and len(hits) < len(must_mention)
            else ""
        )
    )
    return {
        "accuracy": accuracy,
        "groundedness": grounded,
        "format": fmt,
        "reasoning": reasoning.strip(),
    }


def judge(question, ideal, candidate, must_mention, model=None):
    if USE_FAKE:
        return _fake_judge(question, ideal, candidate, must_mention)
    from openai import OpenAI

    print(f"Question: {question}\nCandidate: {candidate}\nIdeal: {ideal}\n")

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=model or JUDGE_MODEL,
        temperature=0,  # judging should be as consistent as possible
        messages=build_messages(question, ideal, candidate),
        tools=[JUDGE_TOOL],
        tool_choice={"type": "function", "function": {"name": "submit_scores"}},
    )
    print(f"Judge response: {resp.choices[0].message.tool_calls[0].function.arguments}\n")
    return json.loads(resp.choices[0].message.tool_calls[0].function.arguments)