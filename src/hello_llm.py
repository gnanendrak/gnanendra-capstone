"""hello_llm.py — Your first OpenAI API call.

Run it from the repo root:
    python src/hello_llm.py "What is RAG in one sentence?"
"""
import sys
import os
from dotenv import load_dotenv
from openai import OpenAI

#load env varibles
load_dotenv()

# Create the OpenAI client — it reads OPENAI_API_KEY from the environment automatically.
client=OpenAI()

def ask(question: str) -> str:
    """Send one question to LLM and return the answer test."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
           {"role": "system", "content": "You are concise."},
           {"role": "user", "content": question}
        ],
        temperature=0.3
    )

    #print("prompt_tokens: ",resp.usage.prompt_tokens)
    #print("completion_tokens: ",resp.usage.completion_tokens)
    #print("Total Tokens: ",resp.usage.total_tokens)
    return resp.choices[0].message.content

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Say hello in one sentence"
    print(ask(q))