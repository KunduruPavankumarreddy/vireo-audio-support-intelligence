# Vireo Audio — Support Intelligence

An end-to-end support analytics and intelligence tool built for Vireo Audio's weekly support review.

The system analyzes support tickets to produce:
- Weekly support KPIs
- Repeat-contact signals
- SLA performance and financial exposure
- CSAT analysis
- Refund and transfer metrics
- Agent leaderboard
- AI-generated complaint summaries

## Business Problem

Vireo Audio wanted a simple weekly view of:

1. What customers are complaining about
2. Whether customers are contacting support repeatedly
3. Which agents are closing the most tickets
4. Where support performance and customer experience may be deteriorating
5. What the financial impact of these issues could be

The goal was to provide actionable information without building a large support platform.

---

## Key Results

Analysis was performed on **11,875 canonical tickets** after resolving duplicate/re-imported records.

### Latest Complete Week
**22–28 June 2026**

| Metric | Result |
|---|---:|
| Tickets | 199 |
| Week-over-week change | +19.2% |
| Potential repeat contacts | 23 |
| Potential repeat rate | 11.6% |
| Estimated repeat-contact cost | ₹6,150 |
| SLA breaches | 15 |
| SLA breach rate | 7.5% |
| SLA exposure | ₹5,250 |
| CSAT | 3.31 / 5 |
| Transfers | 21 |
| Refund cases | 30 |
| Refund amount | ₹125,797 |

The largest weekly category increases were:

- **Charging & Battery:** +14
- **Returns & Refunds:** +11
- **Audio Quality:** +6

---

## Important Interpretation

The repeat-contact metric is deliberately described as a **potential repeat-contact signal**.

The supplied data does not contain a definitive `same_issue` label. Therefore, the system identifies candidates using:

- Same customer
- Same product
- Same category
- New ticket created after the previous ticket was resolved
- Within 30 days

The analysis found:

- **1,527 candidate repeat pairs**
- **1,414 unique candidate repeat tickets**

No unsupported precision/error rate is claimed because there was no labeled ground-truth dataset for same-issue classification.

---

## Data Cleaning

The raw dataset contained duplicate ticket IDs because some tickets appeared in both the current helpdesk and legacy system.

Cleaning included:

- Parsing timestamp fields
- Resolving duplicate ticket records
- Preserving source-system information
- Normalizing legacy resolution timestamps
- Handling missing resolution timestamps
- Converting CSAT `0` values to missing values
- Detecting refund + replacement conflicts
- Calculating handle time
- Validating chronological consistency

After cleaning:

- Duplicate ticket IDs were resolved
- Resolution-before-creation records: **0**
- CSAT zero values: **0**
- Refund + replacement conflicts were retained as an explicit flag rather than silently deleted

---

## Architecture

```text
                    ┌──────────────────┐
                    │   Raw CSV Files   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Data Cleaning     │
                    │ & Normalization   │
                    └────────┬─────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │      Analysis Pipeline      │
              ├─────────────────────────────┤
              │ Weekly Metrics               │
              │ SLA Analysis                 │
              │ Repeat Contact Detection     │
              │ CSAT Analysis                │
              │ Refund Analysis              │
              │ Agent Leaderboard            │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌──────────────────┐          ┌──────────────────┐
     │ Numeric Analysis │          │ AI Complaint     │
     │ Python / Pandas  │          │ Summary          │
     └────────┬─────────┘          │ Ollama           │
              │                    └────────┬─────────┘
              └────────────┬───────────────┘
                           ▼
                  ┌──────────────────┐
                  │ Streamlit        │
                  │ Dashboard        │
                  └──────────────────┘
```

---

## Project Structure

```text
vireo-audio-support-intelligence/
│
├── data/
│   ├── tickets.csv
│   ├── agents.csv
│   ├── customers.csv
│   ├── orders.csv
│   └── products.csv
│
├── docs/
│   └── memo_to_priya_raman.md
│
├── src/
│   ├── cleaning.py
│   ├── metrics.py
│   ├── repeat_contacts.py
│   ├── digest.py
│   ├── leaderboard.py
│   ├── ai_summary.py
│   └── pipeline.py
│
├── streamlit_app.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Main Components

### 1. Data Cleaning

`cleaning.py`

Handles:

- Duplicate ticket records
- Timestamp normalization
- CSAT cleaning
- Resolution timestamps
- Handle-time calculation
- Refund/replacement conflict detection

### 2. Weekly Metrics

`metrics.py`

Calculates:

- Ticket volume
- Week-over-week change
- Repeat-contact candidates
- SLA breaches
- SLA breach rate
- SLA financial exposure
- CSAT
- Transfers
- Refunds
- Refund amounts
- Repeat-contact cost

### 3. Repeat Contact Detection

`repeat_contacts.py`

Identifies potential repeat contacts using customer, product, category and timing relationships.

This is intentionally treated as a **candidate-generation method**, not a confirmed same-issue classifier.

### 4. AI Complaint Summary

`ai_summary.py`

Uses a local Ollama model to summarize complaint language from selected tickets.

The AI is used for **qualitative language/theme summarization**, while Python calculates the actual business metrics.

This separation prevents the LLM from becoming the source of truth for numerical KPIs.

### 5. Agent Leaderboard

`leaderboard.py`

Calculates weekly tickets closed/resolved by agent while:

- Matching agents to their applicable roster period
- Excluding Tier 2 Escalations & Warranty from volume comparisons
- Counting resolved/closed tickets
- Avoiding comparisons between Tier 2 and Tier 1 teams

### 6. Streamlit Dashboard

`streamlit_app.py`

Provides an interactive view of:

- Weekly KPIs
- Category trends
- Repeat-contact signals
- SLA performance
- CSAT
- Refunds
- Transfers
- Agent leaderboard
- AI-generated complaint summary

---

## AI Usage

The project uses a local Ollama model for complaint-language summarization.

### Model

```text
gemma3:4b
```

The LLM is not used to calculate:

- Ticket counts
- SLA rates
- Costs
- CSAT
- Refund totals
- Leaderboard rankings

Those calculations are deterministic Python/Pandas operations.

The AI component is used where language interpretation is useful.

---

## Cost

No paid API calls are required for the current implementation.

The complaint summarization uses a locally running Ollama model.

Therefore:

```text
Cost per run = ₹0 in external API/model charges
```

At approximately 650 tickets/week:

```text
650 × 4 weeks = 2,600 tickets/month
External LLM API cost = ₹0
```

This does not include the infrastructure/electricity cost of running the local model.

---

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/KunduruPavankumarreddy/vireo-audio-support-intelligence.git
cd vireo-audio-support-intelligence
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Streamlit

```bash
streamlit run streamlit_app.py
```

---

## Optional: Local AI Summary

Install and run Ollama, then make sure the required model is available:

```bash
ollama pull gemma3:4b
```

The application can then use the local model for complaint summaries.

---

## Evaluation & Limitations

The analysis was checked against the supplied dataset and business rules.

The pipeline validates:

- Duplicate handling
- Timestamp normalization
- Missing values
- SLA calculations
- Policy-period calculations
- Repeat-contact candidate generation
- CSAT handling
- Financial calculations
- Agent roster matching

### Known limitation

There is no ground-truth `same_issue` label in the supplied dataset.

Therefore, the repeat-contact metric is reported as a **candidate signal** rather than a measured classification accuracy.

Some false positives are possible when the same customer, product and category appear but the underlying issue is different.

---

## Business Recommendations

Based on the latest complete week:

1. Investigate potential repeat contacts, particularly Delivery, Returns and Other.
2. Investigate the sharp increase in Charging & Battery tickets.
3. Monitor first-response SLA performance because each breach carries a ₹350 store-credit exposure under the policy.
4. Use the weekly digest to identify recurring operational issues before they create additional support demand.

---

## Deliverables

- Streamlit support intelligence dashboard
- Weekly support digest
- Agent leaderboard
- Repeat-contact analysis
- SLA and financial analysis
- AI complaint summary
- Business memo for Priya Raman

See:

```text
docs/memo_to_priya_raman.md
```

---

## Author

**Pavan Kunduru**

Data Science / AI Engineering
