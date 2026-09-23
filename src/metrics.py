import pandas as pd


def add_week_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a week-start column based on ticket creation time.
    """
    result = df.copy()

    result["week"] = (
        result["created_at"]
        .dt.to_period("W-SUN")
        .dt.start_time
    )

    return result


def calculate_weekly_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate weekly operational KPIs.

    Expected columns:
    - ticket_id
    - week
    - repeat_candidate
    - sla_breach
    - csat_score
    - current_helpdesk_transfer
    - current_helpdesk_refund_amount
    """

    weekly = (
        df.groupby("week")
        .agg(
            tickets=("ticket_id", "count"),
            repeat_candidates=("repeat_candidate", "sum"),
            sla_breaches=("sla_breach", "sum"),
            avg_csat=("csat_score", "mean"),
            transfers=("current_helpdesk_transfer", "sum"),
            refunds=("current_helpdesk_refund_amount", "count"),
            refund_amount=("current_helpdesk_refund_amount", "sum"),
            repeat_contact_cost=("repeat_contact_cost", "sum"),
        )
    )

    weekly["repeat_rate"] = (
        weekly["repeat_candidates"] / weekly["tickets"]
    )

    weekly["sla_breach_rate"] = (
        weekly["sla_breaches"] / weekly["tickets"]
    )

    weekly["sla_credit_exposure"] = (
        weekly["sla_breaches"] * 350
    )

    weekly["ticket_change_pct"] = (
        weekly["tickets"].pct_change() * 100
    )

    weekly["repeat_change_pct"] = (
        weekly["repeat_rate"].pct_change() * 100
    )

    return weekly


def calculate_repeat_cost(repeat_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate repeat-contact cost using Vireo channel rates.
    """

    channel_costs = {
        "chat": 210,
        "email": 260,
        "voice": 520,
        "social": 240,
    }

    result = repeat_df.copy()

    result["repeat_contact_cost"] = (
        result["channel"].map(channel_costs)
    )

    return result