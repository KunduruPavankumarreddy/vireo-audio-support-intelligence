from __future__ import annotations

import pandas as pd

from cleaning import load_tickets, clean_tickets
from metrics import add_week_column
from repeat_contacts import find_repeat_candidates


SLA_TARGETS = {
    "chat": pd.Timedelta(minutes=15),
    "voice": pd.Timedelta(hours=2),
    "social": pd.Timedelta(hours=4),
    "email": pd.Timedelta(hours=8),
}


def build_analysis_dataset(
    tickets_path: str,
    products_path: str,
):
    """
    Build the enriched ticket dataset used by the application.
    """

    # ---------------------------------------------------------
    # 1. Load + clean tickets
    # ---------------------------------------------------------
    raw_tickets = load_tickets(tickets_path)

    tickets = clean_tickets(raw_tickets)

    # ---------------------------------------------------------
    # 2. Add weekly period
    # ---------------------------------------------------------
    tickets = add_week_column(tickets)

    # ---------------------------------------------------------
    # 3. SLA calculations
    # ---------------------------------------------------------
    tickets["first_response_delay"] = (
        tickets["first_response_at"]
        - tickets["created_at"]
    )

    tickets["sla_target"] = (
        tickets["channel"].map(SLA_TARGETS)
    )

    tickets["sla_breach"] = (
        tickets["first_response_delay"]
        > tickets["sla_target"]
    )

    # ---------------------------------------------------------
    # 4. Current-helpdesk financial/transfer fields
    # ---------------------------------------------------------

    tickets["transfers"] = pd.to_numeric(
        tickets["transfers"],
        errors="coerce"
    ).fillna(0)

    tickets["refund_amount_inr"] = pd.to_numeric(
        tickets["refund_amount_inr"],
        errors="coerce"
    ).fillna(0)

    tickets["current_helpdesk_transfer"] = (
        tickets["transfers"]
        .where(
            tickets["source_system"] == "helpdesk",
            0
        )
    )

    tickets["current_helpdesk_refund_amount"] = (
        tickets["refund_amount_inr"]
        .where(
            tickets["source_system"] == "helpdesk",
            0
        )
    )

    # ---------------------------------------------------------
    # 5. Product name
    # ---------------------------------------------------------
    products = pd.read_csv(products_path)

    tickets = tickets.merge(
        products[
            ["sku", "product_name"]
        ],
        left_on="product_sku",
        right_on="sku",
        how="left",
        validate="many_to_one",
    ).drop(
        columns="sku"
    )

    # ---------------------------------------------------------
    # 6. Repeat-contact candidates
    # ---------------------------------------------------------
    repeat_pairs, repeat_tickets = find_repeat_candidates(
        tickets
    )

    tickets["repeat_candidate"] = (
        tickets["ticket_id"].isin(
            repeat_tickets["new_ticket_id"]
        )
    )

    # Cost belongs to the later/current contact.
    repeat_cost_map = (
        repeat_tickets
        .set_index("new_ticket_id")[
            "repeat_contact_cost"
        ]
    )

    tickets["repeat_contact_cost"] = (
        tickets["ticket_id"]
        .map(repeat_cost_map)
        .fillna(0)
    )

    return (
        tickets,
        repeat_pairs,
        repeat_tickets,
    )