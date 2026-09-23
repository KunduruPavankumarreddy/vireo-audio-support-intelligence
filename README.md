# Vireo Audio — Support Intelligence

## 1. Business Problem

Vireo Audio receives weekly support-ticket exports and needs:
- a weekly support digest
- visibility into repeat contacts
- SLA exposure
- complaint themes
- a Tier-1 agent leaderboard

The tool converts the raw ticket export into a weekly operating view for support and finance stakeholders.

## 2. Solution

The application provides:

- Weekly ticket volume and week-over-week change
- Candidate repeat-contact detection
- Estimated repeat-contact cost
- First-response SLA breach rate and exposure
- CSAT
- Top complaint categories
- AI-assisted complaint themes with supporting ticket IDs
- Tier-1 agent leaderboard

## 3. Architecture

Raw CSV files
→ Cleaning and canonicalization
→ Business metrics
→ Repeat-contact detection
→ Complaint analysis
→ Streamlit dashboard

The application uses deterministic Python calculations for business metrics. The local LLM is used only to summarize complaint language; it does not calculate business KPIs.

## 4. Data Cleaning

The pipeline:
- removes duplicate ticket IDs while preferring the current helpdesk record
- normalizes legacy resolution timestamps to IST
- treats CSAT 0 as missing
- calculates handle time
- flags refund + replacement conflicts

## 5. Repeat-Contact Logic

A candidate repeat contact is identified using:

same customer
+ same product
+ same category
+ new ticket created within 30 days after the previous ticket's resolution

This is a transparent proxy because the dataset does not contain an explicit `same_issue` ground-truth field.

## 6. Validation

A reproducible sample of 50 candidate pairs was reviewed by comparing the previous and new customer messages.

39 were judged likely genuine repeats and 11 false positives.

Estimated precision: 78%

Estimated error rate: 22%

Main failure cases occurred when the same customer, product and category matched but the underlying issue was different.

This is proxy validation rather than definitive ground-truth accuracy.

## 7. Business Results

Latest complete week: 22–28 June 2026

- Tickets: 199
- Week-over-week change: +19.2%
- Candidate repeat contacts: 23
- Candidate repeat rate: 11.6%
- Candidate repeat-contact cost: ₹6,150
- SLA breaches: 15
- SLA breach rate: 7.5%
- SLA credit exposure: ₹5,250
- Average CSAT: 3.31/5
- Transfers: 21
- Refund amount: ₹125,797

## 8. Business Goal

Proposed operating goal:

Reduce candidate repeat-contact rate by 20% from the current 11.9% baseline.

Across the observed dataset, candidate repeat-contact cost exposure was approximately ₹367,500. A 20% reduction represents approximately ₹73,500 of potential contact-cost exposure avoided over the observed period, assuming channel mix and costs remain similar.

## 9. Limitations

- Repeat contacts are candidates, not confirmed same-issue contacts.
- AI complaint summaries are generated from sampled evidence and should be reviewed before operational decisions.
- Legacy monetary values are not directly combined with current-helpdesk rupee values.
- Tier-2 Escalations & Warranty is excluded from the Tier-1 volume leaderboard.

## 10. Run Locally

Install dependencies:

```bash
pip install -r requirements.txt