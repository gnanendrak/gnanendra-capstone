import json

from pydantic import BaseModel, Field


class GoldenEntry(BaseModel):
    id: str
    question: str = Field(min_length=1)  # must be non-empty
    ideal_answer: str = Field(min_length=1)  # must be non-empty
    notes: str = ""  # optional, defaults to empty
    must_mention: list[str] = []  # optional list of required facts


def load_golden(path):
    """Read a .jsonl file, validate every line, return a list of GoldenEntry."""
    out = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                continue
            data = json.loads(line)
            out.append(GoldenEntry(**data))
        return out