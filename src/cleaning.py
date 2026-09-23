import pandas as pd


def load_tickets(path: str) -> pd.DataFrame:
    """Load the raw Vireo ticket export."""
    return pd.read_csv(path)


def clean_tickets(tickets: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and canonicalize the Vireo ticket dataset.

    Rules:
    - Prefer helpdesk over legacy_fd when duplicate ticket IDs exist.
    - Parse ticket timestamps.
    - Convert legacy resolution timestamps from UTC to IST (+5:30).
    - Treat CSAT 0 as missing because valid CSAT is 1-5.
    - Flag tickets with both a refund and replacement.
    - Calculate handle time from first response to normalized resolution.
    """

    df = tickets.copy()

    # ---------------------------------------------------------
    # 1. Parse datetime columns
    # ---------------------------------------------------------
    date_cols = [
        "created_at",
        "first_response_at",
        "resolved_at",
    ]

    for col in date_cols:
        df[col] = pd.to_datetime(
            df[col],
            errors="coerce"
        )

    # ---------------------------------------------------------
    # 2. Prefer current helpdesk record over legacy_fd
    # ---------------------------------------------------------
    df["source_priority"] = df["source_system"].map({
        "helpdesk": 1,
        "legacy_fd": 2,
    })

    df = df.sort_values(
        ["ticket_id", "source_priority"]
    )

    df = df.drop_duplicates(
        subset="ticket_id",
        keep="first"
    )

    df = df.drop(
        columns="source_priority"
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # 3. Clean CSAT
    # ---------------------------------------------------------
    df["csat_score"] = pd.to_numeric(
        df["csat_score"],
        errors="coerce"
    ).astype("Float64")

    # 0 is not a valid survey response.
    # Treat it as missing rather than as a score of zero.
    df.loc[
        df["csat_score"] == 0,
        "csat_score"
    ] = pd.NA

    # ---------------------------------------------------------
    # 4. Refund + replacement conflict
    # ---------------------------------------------------------
    df["refund_amount_inr"] = pd.to_numeric(
        df["refund_amount_inr"],
        errors="coerce"
    ).fillna(0)

    replacement_flag = (
        df["replacement_issued"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin([
            "true",
            "1",
            "yes",
            "y"
        ])
    )

    df["refund_replacement_conflict"] = (
        (df["refund_amount_inr"] > 0)
        & replacement_flag
    )

    # ---------------------------------------------------------
    # 5. Normalize resolution timestamps
    # ---------------------------------------------------------
    df["resolved_at_normalized"] = df["resolved_at"]

    legacy_mask = (
        df["source_system"] == "legacy_fd"
    )

    df.loc[
        legacy_mask,
        "resolved_at_normalized"
    ] = (
        df.loc[legacy_mask, "resolved_at"]
        + pd.Timedelta(hours=5, minutes=30)
    )

    # ---------------------------------------------------------
    # 6. Calculate handle time
    # ---------------------------------------------------------
    df["handle_time"] = (
        df["resolved_at_normalized"]
        - df["first_response_at"]
    )

    return df