"""AI-powered, but safe, decision support for the Market Basket dashboard.

The default provider is Ollama running on the user's machine.  It is free to
use once a local model has been downloaded and does not send the CSV elsewhere.
An OpenAI-compatible endpoint can be enabled with environment variables.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from utils.suggestions import generate_suggestions


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def dataset_profile(data):
    """Return aggregate metadata only; raw customer rows are never prompted."""
    numeric = data.select_dtypes(include=["number"]).columns.tolist()
    categorical = data.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    profile = {
        "rows": int(len(data)),
        "columns": list(map(str, data.columns)),
        "missing_values": {str(k): int(v) for k, v in data.isna().sum().items() if v},
        "numeric_metrics": {},
        "top_categories": {},
    }
    for column in numeric[:12]:
        series = pd.to_numeric(data[column], errors="coerce").dropna()
        if not series.empty:
            profile["numeric_metrics"][str(column)] = {
                "mean": round(float(series.mean()), 2),
                "median": round(float(series.median()), 2),
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2),
            }
    for column in categorical[:8]:
        values = data[column].fillna("Missing").astype(str).value_counts().head(5)
        profile["top_categories"][str(column)] = {str(k): int(v) for k, v in values.items()}
    return profile


def _prompt(profile, question):
    question = (question or "Give the most valuable next actions.").strip()[:500]
    return (
        "You are a careful market-basket analytics advisor. Use only the aggregate "
        "dataset profile below. Give 3-5 concise, evidence-based recommendations. "
        "For each one include: action, evidence, expected impact, and a caveat. "
        "Never invent values, claim causation from correlation, or propose automatic "
        "spending, pricing, customer contact, or other real-world action. This is "
        "decision support; a human must approve every action.\n\n"
        f"Question: {question}\nDataset profile:\n{json.dumps(profile, ensure_ascii=False)}"
    )


def _post_json(url, payload, headers=None):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def _ask_model(prompt):
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        result = _post_json(
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            {"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3},
            {"Authorization": f"Bearer {OPENAI_API_KEY}"},
        )
        return result["choices"][0]["message"]["content"].strip(), "OpenAI-compatible API"

    result = _post_json(
        OLLAMA_URL,
        {"model": OLLAMA_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False},
    )
    return result["message"]["content"].strip(), f"Local Ollama ({OLLAMA_MODEL})"


def generate_ai_advice(data, question=None):
    """Generate advice and gracefully preserve core functionality offline."""
    profile = dataset_profile(data)
    try:
        answer, provider = _ask_model(_prompt(profile, question))
        if answer:
            return {"answer": answer, "provider": provider, "fallback": False, "profile": profile}
        raise RuntimeError("The AI returned an empty response.")
    except (RuntimeError, KeyError, HTTPError, URLError, TimeoutError, ValueError) as exc:
        fallback = "\n".join(f"• {item}" for item in generate_suggestions(data))
        return {
            "answer": fallback,
            "provider": "Built-in data rules",
            "fallback": True,
            "profile": profile,
            "notice": f"AI advisor unavailable ({exc}). Showing local rule-based insights instead.",
        }
