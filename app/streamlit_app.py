from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"

sys.path.append(str(SRC_DIR))


# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------
from pipeline import build_analysis_dataset
from metrics import calculate_weekly_kpis
from digest import build_weekly_digest, format_weekly_digest
from leaderboard import build_tier1_leaderboard
from ai_summary import (
    build_complaint_evidence,
    generate_complaint_summary,
)


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Vireo Support Intelligence",
    page_icon="🎧",
    layout="wide",
)


st.title("Vireo Support Intelligence")
st.caption(
    "Weekly support digest and Tier-1 operational view"
)


# ---------------------------------------------------------
# Load and prepare data
# ---------------------------------------------------------
@st.cache_data
def load_analysis_data():

    tickets, repeat_pairs, repeat_tickets = (
        build_analysis_dataset(
            str(DATA_DIR / "tickets.csv"),
            str(DATA_DIR / "products.csv"),
        )
    )

    agents = pd.read_csv(
        DATA_DIR / "agents.csv"
    )

    agents["from_date"] = pd.to_datetime(
        agents["from_date"]
    )

    agents["to_date"] = pd.to_datetime(
        agents["to_date"]
    )

    weekly_kpis = calculate_weekly_kpis(
        tickets
    )

    weekly_category_counts = (
        tickets
        .groupby(["week", "category"])
        .size()
        .reset_index(name="tickets")
    )

    return (
        tickets,
        agents,
        weekly_kpis,
        weekly_category_counts,
        repeat_pairs,
        repeat_tickets,
    )


(
    tickets,
    agents,
    weekly_kpis,
    weekly_category_counts,
    repeat_pairs,
    repeat_tickets,
) = load_analysis_data()


# ---------------------------------------------------------
# Week selector
# ---------------------------------------------------------
dataset_end_date = tickets["created_at"].max()

last_complete_week = (
    dataset_end_date.to_period("W-SUN").start_time
    - pd.Timedelta(weeks=1)
)

complete_weeks = weekly_kpis.index[
    weekly_kpis.index <= last_complete_week
]

selected_week = st.selectbox(
    "Select week",
    options=complete_weeks[::-1],
    format_func=lambda x: x.strftime("%d %b %Y"),
)


# ---------------------------------------------------------
# Digest
# ---------------------------------------------------------
digest = build_weekly_digest(
    weekly_kpis=weekly_kpis,
    weekly_category_counts=weekly_category_counts,
    final_tickets=tickets,
    week_start=selected_week,
)


st.subheader("Weekly Digest")


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Tickets",
    digest["tickets"],
    f'{digest["ticket_change_pct"]:+.1f}%'
)

col2.metric(
    "Repeat Rate",
    f'{digest["repeat_rate_pct"]:.1f}%'
)

col3.metric(
    "SLA Breach Rate",
    f'{digest["sla_breach_rate_pct"]:.1f}%'
)

col4.metric(
    "CSAT",
    f'{digest["avg_csat"]:.2f}/5'
)


st.markdown(
    f"""
**Repeat-contact candidate cost:** ₹{digest["repeat_contact_cost"]:,}

**SLA credit exposure:** ₹{digest["sla_credit_exposure"]:,}

**Transfers:** {digest["transfers"]}

**Refund amount:** ₹{digest["refund_amount"]:,}
"""
)


# ---------------------------------------------------------
# Top categories
# ---------------------------------------------------------
st.subheader("Top Support Categories")

category_df = pd.DataFrame(
    digest["top_categories"]
)

st.dataframe(
    category_df,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# AI complaint summary
# ---------------------------------------------------------
st.subheader("AI Complaint Themes")

st.info(
    "AI analysis runs locally through Ollama and may take "
    "around a minute on this machine."
)

generate_ai = st.button(
    "Generate AI Complaint Summary"
)

@st.cache_data(show_spinner=False)
def generate_ai_for_week(
    week: pd.Timestamp,
    tickets: pd.DataFrame,
):
    weekly_tickets = tickets[
        tickets["week"] == week
    ].copy()

    evidence = build_complaint_evidence(
        weekly_tickets
    )

    return generate_complaint_summary(
        evidence
    )

if generate_ai:

    with st.spinner("Analyzing customer complaints..."):

        ai_summary, generation_time = (
            generate_ai_for_week(
                selected_week,
                tickets,
            )
        )

    st.caption(
        f"Local AI generation time: "
        f"{generation_time:.1f} seconds"
    )

    st.markdown(ai_summary)

# ---------------------------------------------------------
# Tier-1 leaderboard
# ---------------------------------------------------------
st.subheader("Tier-1 Agent Leaderboard")


weekly_tickets = tickets[
    tickets["week"] == selected_week
].copy()


leaderboard = build_tier1_leaderboard(
    weekly_tickets,
    agents,
)


st.dataframe(
    leaderboard[
        [
            "name",
            "team",
            "site",
            "shift",
            "tickets_completed",
            "sla_breaches",
            "sla_breach_rate",
            "avg_csat",
            "transfers",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)