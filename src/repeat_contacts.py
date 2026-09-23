import pandas as pd


CHANNEL_COSTS = {
    "chat": 210,
    "email": 260,
    "voice": 520,
    "social": 240,
}


def find_repeat_candidates(
    df: pd.DataFrame,
    window_days: int = 30
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Find repeat-contact candidate pairs.

    Proxy used in the validated notebook:
    same customer + same product + same category,
    where a later ticket is created within `window_days`
    after an earlier ticket was resolved.

    Returns:
        repeat_pairs:
            every qualifying new-ticket / previous-ticket pair
        repeat_tickets:
            one row per unique new ticket flagged as a candidate
    """

    required = [
        "ticket_id",
        "customer_id",
        "product_sku",
        "category",
        "channel",
        "created_at",
        "resolved_at_normalized",
        "customer_message",
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    data = df.copy()

    # Previous tickets must have a resolution timestamp.
    previous = data[
        data["resolved_at_normalized"].notna()
    ][
        [
            "ticket_id",
            "customer_id",
            "product_sku",
            "category",
            "resolved_at_normalized",
        ]
    ].rename(
        columns={
            "ticket_id": "previous_ticket_id",
            "resolved_at_normalized": "previous_resolved_at",
        }
    )

    # Later/current tickets.
    current = data[
        [
            "ticket_id",
            "customer_id",
            "product_sku",
            "category",
            "channel",
            "created_at",
            "customer_message",
        ]
    ].rename(
        columns={
            "ticket_id": "new_ticket_id",
            "created_at": "new_created_at",
            "customer_message": "new_customer_message",
        }
    )

    # Match on same customer + product + category.
    pairs = current.merge(
        previous,
        on=[
            "customer_id",
            "product_sku",
            "category",
        ],
        how="inner",
    )

    # A ticket cannot be a repeat of itself.
    pairs = pairs[
        pairs["new_ticket_id"]
        != pairs["previous_ticket_id"]
    ].copy()

    # New ticket must happen after previous resolution.
    pairs["days_after_resolution"] = (
        pairs["new_created_at"]
        - pairs["previous_resolved_at"]
    ).dt.total_seconds() / 86400

    pairs = pairs[
        (pairs["days_after_resolution"] > 0)
        &
        (pairs["days_after_resolution"] <= window_days)
    ].copy()

    pairs = pairs.sort_values(
        [
            "new_created_at",
            "previous_resolved_at",
        ]
    ).reset_index(drop=True)

    # Cost is based on the later/current contact channel.
    pairs["repeat_contact_cost"] = (
        pairs["channel"].map(CHANNEL_COSTS)
    )

    # One row per unique new ticket.
    repeat_tickets = (
        pairs.sort_values("days_after_resolution")
        .drop_duplicates(
            subset="new_ticket_id",
            keep="first",
        )
        .copy()
    )

    return pairs, repeat_tickets