from __future__ import annotations

from typing import Any

import pandas as pd


def get_latest_complete_week(
    weekly_kpis: pd.DataFrame,
    dataset_end_date: pd.Timestamp
) -> pd.Timestamp:
    """
    Return the latest Monday-start week that is fully contained
    within the dataset period.
    """

    last_week = (
        dataset_end_date
        - pd.Timedelta(days=6)
    ).normalize()

    complete_weeks = weekly_kpis[
        weekly_kpis.index <= last_week
    ]

    if complete_weeks.empty:
        raise ValueError("No complete week available.")

    return complete_weeks.index.max()


def build_weekly_digest(
    weekly_kpis: pd.DataFrame,
    weekly_category_counts: pd.DataFrame,
    final_tickets: pd.DataFrame,
    week_start: pd.Timestamp,
) -> dict[str, Any]:
    """
    Build verified facts for one weekly support digest.

    Numerical values come from Python calculations.
    AI-generated text is intentionally kept separate.
    """

    if week_start not in weekly_kpis.index:
        raise ValueError(
            f"Week {week_start} not found in weekly KPI data."
        )

    current = weekly_kpis.loc[week_start]

    previous_week = week_start - pd.Timedelta(weeks=1)

    previous = (
        weekly_kpis.loc[previous_week]
        if previous_week in weekly_kpis.index
        else None
    )

    # Top categories
    top_categories = (
        weekly_category_counts[
            weekly_category_counts["week"] == week_start
        ]
        .sort_values("tickets", ascending=False)
        .head(5)
    )

    # Repeat-contact categories
    repeat_categories = (
        final_tickets[
            (final_tickets["week"] == week_start)
            & final_tickets["repeat_candidate"]
        ]
        .groupby("category")
        .size()
        .sort_values(ascending=False)
        .head(5)
    )

    if previous is not None:
        ticket_change_pct = (
            (current["tickets"] - previous["tickets"])
            / previous["tickets"]
            * 100
        )
    else:
        ticket_change_pct = None

    digest = {
        "week": week_start.strftime("%d %b %Y"),

        "tickets": int(current["tickets"]),

        "previous_tickets": (
            int(previous["tickets"])
            if previous is not None
            else None
        ),

        "ticket_change_pct": (
            round(float(ticket_change_pct), 2)
            if ticket_change_pct is not None
            else None
        ),

        "repeat_candidates": int(
            current["repeat_candidates"]
        ),

        "repeat_rate_pct": round(
            float(current["repeat_rate"]) * 100,
            2
        ),

        "repeat_contact_cost": int(
            current.get("repeat_contact_cost", 0)
        ),

        "sla_breaches": int(
            current["sla_breaches"]
        ),

        "sla_breach_rate_pct": round(
            float(current["sla_breach_rate"]) * 100,
            2
        ),

        "sla_credit_exposure": int(
            current["sla_credit_exposure"]
        ),

        "avg_csat": round(
            float(current["avg_csat"]),
            2
        ),

        "transfers": int(
            current["transfers"]
        ),

        "refunds": int(
            current["refunds"]
        ),

        "refund_amount": int(
            current["refund_amount"]
        ),

        "top_categories": (
            top_categories[
                ["category", "tickets"]
            ]
            .to_dict("records")
        ),

        "top_repeat_categories": [
            {
                "category": category,
                "repeat_candidates": int(count),
            }
            for category, count
            in repeat_categories.items()
        ],
    }

    return digest


def format_weekly_digest(
    digest: dict[str, Any],
    ai_summary: str | None = None,
) -> str:
    """Convert verified digest facts into a readable report."""

    text = f"""
WEEKLY SUPPORT DIGEST
Week: {digest["week"]}

WHAT CHANGED
Support handled {digest["tickets"]} tickets,
{digest["ticket_change_pct"]:+.1f}% versus the previous week.

REPEAT CONTACT
{digest["repeat_candidates"]} tickets were repeat-contact candidates
({digest["repeat_rate_pct"]:.1f}%).
Estimated candidate repeat-contact cost:
₹{digest["repeat_contact_cost"]:,}.

SLA
{digest["sla_breaches"]} tickets breached first-response SLA
({digest["sla_breach_rate_pct"]:.1f}%).
Estimated SLA credit exposure:
₹{digest["sla_credit_exposure"]:,}.

CUSTOMER EXPERIENCE
Average CSAT: {digest["avg_csat"]:.2f}/5.

OPERATIONS
Transfers: {digest["transfers"]}

TOP CATEGORIES
"""

    for item in digest["top_categories"]:
        text += (
            f'- {item["category"]}: '
            f'{item["tickets"]} tickets\n'
        )

    text += "\nTOP REPEAT-CONTACT CATEGORIES\n"

    for item in digest["top_repeat_categories"]:
        text += (
            f'- {item["category"]}: '
            f'{item["repeat_candidates"]} repeat candidates\n'
        )

    if ai_summary:
        text += "\nAI COMPLAINT SUMMARY\n"
        text += ai_summary.strip()

    return text.strip()