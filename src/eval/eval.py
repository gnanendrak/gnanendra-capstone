import os

USE_FAKE = True  # <-- set False (and export OPENAI_API_KEY) to call the real model

QUESTION = "What is the company's policy on remote work?"

# The three canned responses used in fake mode.
# R1: concise + correct   R2: verbose + correct   R3: plausible but MISSING the "3 days" detail
CANNED = [
    "Employees may work remotely up to 3 days per week, with manager approval.",
    "Our remote-work policy lets team members work from home for up to three days "
    "each week. You'll want to coordinate with your manager for coverage, but the "
    "standard allowance is three remote days weekly.",
    "Employees are allowed to work remotely with manager approval, as described in "
    "the employee handbook.",
]


def _call_openai(question, temperature=0.7):
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": "You are an HR assistant. Policy: employees may work remotely up to "
                "3 days per week with manager approval. Answer the user's question.",
            },
            {"role": "user", "content": question},
        ],
    )
    return resp.choices[0].message.content.strip()


def ask_three(question):
    if USE_FAKE:
        return list(CANNED)
    return [_call_openai(question) for _ in range(3)]


print("mode:", "FAKE (canned)" if USE_FAKE else "REAL (gpt-4o-mini)")

answers = ask_three(QUESTION)
for i, a in enumerate(answers, 1):
    print(f"--- Response {i} ---\n{a}\n")

expected = "Employees may work remotely 3 days a week."

for i, a in enumerate(answers, 1):
    try:
        assert a == expected
        print(f"Response {i}: PASS")
    except AssertionError:
        print(f"Response {i}: FAIL  (assert answer == expected)")


def normalize(s):
    return " ".join(s.lower().split())


for i, a in enumerate(answers, 1):
    print(f"Response {i}: {'PASS' if normalize(a) == normalize(expected) else 'FAIL'}")


def mentions_three_days(a):
    text = a.lower
    return "3 days" in text or "three days" in text


for i, a in enumerate(answers, 1):
    print(
        f"Response {i}: {'has the 3-day detail' if mentions_three_days(a) else 'MISSING the 3-day detail'}"
    )

sneaky_wrong = "There is no limit — employees can work remotely all 3 days, 4 days, or 5 days, whenever they like."
print("mentions '3 days'? ", mentions_three_days(sneaky_wrong))
print("...but the answer is WRONG — it says there's no limit.")


def is_accurate(a):
    t = a.lower()
    has_limit = "3 days" in t or "three days" in t
    has_approval = "manager" in t or "approval" in t
    contradicts = any(
        p in t for p in ["no limit", "unlimited", "4 days", "5 days", "any day"]
    )
    return has_limit and has_approval and not contradicts


def is_grounded(a):
    # grounded = doesn't invent rules outside the known policy (toy check for the demo)
    invented = any(
        p in a.lower()
        for p in ["stipend", "reimburse", "equipment budget", "unlimited"]
    )
    return not invented


def follows_format(a, max_words=60):
    return len(a.split()) <= max_words


def evaluate(a):
    return {
        "accurate": is_accurate(a),
        "grounded": is_grounded(a),
        "format": follows_format(a),
    }


# score the three real answers + the sneaky-wrong one
labels = ["Response 1", "Response 2", "Response 3", "Sneaky-wrong"]
samples = answers + [sneaky_wrong]

print(f"{'':13} {'accurate':>9} {'grounded':>9} {'format':>7}")
for label, a in zip(labels, samples):
    p = evaluate(a)
    print(
        f"{label:13} {str(p['accurate']):>9} {str(p['grounded']):>9} {str(p['format']):>7}"
    )