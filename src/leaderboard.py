from __future__ import annotations

import pandas as pd


def build_tier1_leaderboard(
    weekly_tickets: pd.DataFrame,
    agents: pd.DataFrame,
) -> pd.DataFrame:

    required_ticket_columns = [
        "ticket_id",
        "agent_id",
        "status",
        "resolved_at_normalized",
        "sla_breach",
        "csat_score",
        "current_helpdesk_transfer",
    ]

    required_agent_columns = [
        "agent_id",
        "name",
        "team",
        "site",
        "shift",
        "tier",
        "from_date",
        "to_date",
    ]

    missing_ticket = [
        col for col in required_ticket_columns
        if col not in weekly_tickets.columns
    ]

    missing_agents = [
        col for col in required_agent_columns
        if col not in agents.columns
    ]

    if missing_ticket:
        raise ValueError(
            f"Missing ticket columns: {missing_ticket}"
        )

    if missing_agents:
        raise ValueError(
            f"Missing agent columns: {missing_agents}"
        )

    # ---------------------------------------------------------
    # 1. Keep ONLY ticket columns needed by this function.
    # This prevents column collisions during the roster merge.
    # ---------------------------------------------------------
    tickets = weekly_tickets[
        required_ticket_columns
    ].copy()

    tickets = tickets[
        tickets["status"].isin(["resolved", "closed"])
    ].copy()

    # ---------------------------------------------------------
    # 2. Prepare roster
    # ---------------------------------------------------------
    roster = agents[
        required_agent_columns
    ].copy()

    roster["from_date"] = pd.to_datetime(
        roster["from_date"]
    )

    roster["to_date"] = pd.to_datetime(
        roster["to_date"]
    )

    # ---------------------------------------------------------
    # 3. Merge ONCE
    # ---------------------------------------------------------
    leaderboard_base = tickets.merge(
        roster,
        on="agent_id",
        how="left",
    )

    # ---------------------------------------------------------
    # 4. Match ticket to correct roster assignment
    # ---------------------------------------------------------
    leaderboard_base["assignment_match"] = (
        (
            leaderboard_base["resolved_at_normalized"]
            >= leaderboard_base["from_date"]
        )
        &
        (
            leaderboard_base["to_date"].isna()
            |
            (
                leaderboard_base["resolved_at_normalized"]
                <= leaderboard_base["to_date"]
            )
        )
    )

    leaderboard_base = leaderboard_base[
        leaderboard_base["assignment_match"]
    ].copy()

    # ---------------------------------------------------------
    # 5. Tier 1 only
    # ---------------------------------------------------------
    tier1 = leaderboard_base[
        leaderboard_base["tier"] == 1
    ].copy()

    # ---------------------------------------------------------
    # 6. Aggregate
    # ---------------------------------------------------------
    leaderboard = (
        tier1
        .groupby(
            [
                "agent_id",
                "name",
                "team",
                "site",
                "shift",
            ],
            as_index=False,
        )
        .agg(
            tickets_completed=(
                "ticket_id",
                "count",
            ),
            sla_breaches=(
                "sla_breach",
                "sum",
            ),
            avg_csat=(
                "csat_score",
                "mean",
            ),
            transfers=(
                "current_helpdesk_transfer",
                "sum",
            ),
        )
    )

    leaderboard["sla_breach_rate"] = (
        leaderboard["sla_breaches"]
        / leaderboard["tickets_completed"]
    )

    leaderboard = leaderboard.sort_values(
        "tickets_completed",
        ascending=False,
    ).reset_index(drop=True)

    return leaderboard