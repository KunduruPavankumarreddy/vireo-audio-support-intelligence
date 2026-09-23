from __future__ import annotations

import time
from typing import Optional

import pandas as pd
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma3:4b"


def build_complaint_evidence(
    weekly_tickets: pd.DataFrame,
    max_categories: int = 5,
    samples_per_category: int = 3,
) -> pd.DataFrame:

    required_columns = [
        "ticket_id",
        "category",
        "product_name",
        "customer_message",
    ]

    missing = [
        col
        for col in required_columns
        if col not in weekly_tickets.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns in weekly_tickets: {missing}"
        )

    top_categories = (
        weekly_tickets["category"]
        .value_counts()
        .head(max_categories)
        .index
    )

    evidence = weekly_tickets[
        weekly_tickets["category"].isin(top_categories)
    ][required_columns].copy()

    samples = []

    for category, group in evidence.groupby(
        "category",
        sort=False
    ):
        sample_size = min(
            len(group),
            samples_per_category
        )

        samples.append(
            group.sample(
                n=sample_size,
                random_state=42
            )
        )

    if not samples:
        return pd.DataFrame(
            columns=required_columns
        )

    evidence = pd.concat(
        samples,
        ignore_index=True
    )

    return evidence


def generate_complaint_summary(
    evidence: pd.DataFrame,
    model: str = DEFAULT_MODEL,
    timeout: int = 90,
) -> tuple[str, float]:
    """
    Generate a concise complaint-theme summary using Ollama.

    Returns:
        summary text
        generation time in seconds
    """

    evidence_text = "\n\n".join(
        [
            f"Ticket ID: {row['ticket_id']}\n"
            f"Category: {row['category']}\n"
            f"Product: {row['product_name']}\n"
            f"Customer message: {row['customer_message']}"
            for _, row in evidence.iterrows()
        ]
    )

    prompt = f"""
You are a Vireo Audio support operations analyst.

From the customer messages below, identify the 3 most important
recurring complaint themes.

For each theme provide exactly:
1. Theme name
2. One short description
3. Two supporting ticket IDs

Rules:
- Use only the supplied messages.
- Do not invent causes.
- Do not invent statistics.
- Do not calculate metrics.
- Keep every theme concise.
- Return ONLY the 3 themes.
- Do not add an introduction or conclusion.

Customer messages:

{evidence_text}
"""

    start = time.time()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 250,
            },
        },
        timeout=timeout,
    )

    elapsed = time.time() - start

    response.raise_for_status()

    result = response.json()

    return result["response"].strip(), elapsed