# Customer Churn Analysis

## Project overview
This project analyzes customer subscription behavior to identify patterns associated with cancellations and recommend practical retention improvements. It includes a synthetic telecom-style dataset, a reusable Python cleaning and analysis pipeline, CSV reports, and charts.

## Objectives
- Measure overall customer churn.
- Compare churn across contract, service, payment, and billing segments.
- Explore how tenure, monthly charges, usage, and support interactions relate to churn.
- Recommend retention actions based on observed risk patterns.

## Folder structure
```text
Customer-Churn-Analysis/
├── data/
│   └── customer_churn_raw.csv
├── src/
│   └── churn_analysis.py
├── reports/
│   ├── customer_churn_cleaned.csv
│   ├── cleaning_summary.csv
│   ├── kpi_summary.csv
│   ├── churn_by_segment.csv
│   ├── churn_by_tenure.csv
│   └── retention_recommendations.csv
├── visualizations/
│   ├── churn_distribution.png
│   ├── churn_by_contract.png
│   ├── tenure_vs_churn.png
│   └── charges_vs_churn.png
├── requirements.txt
└── README.md
```

## Run the project
Python 3.9+ is recommended.

```bash
pip install -r requirements.txt
python src/churn_analysis.py
```

To analyze another dataset with the same required column structure:
```bash
python src/churn_analysis.py --input path/to/dataset.csv --output-dir reports
```

## Dataset fields
- `customer_id`: Unique customer identifier
- `tenure_months`: Months subscribed
- `contract_type`: Subscription contract
- `internet_service`: Service type
- `payment_method`: Payment method
- `monthly_charges`: Monthly subscription charges
- `support_calls_90d`: Support calls in the last 90 days
- `monthly_usage_hours`: Approximate monthly usage
- `senior_citizen`: Binary indicator (0/1)
- `paperless_billing`: Paperless billing indicator
- `churn`: Whether the customer cancelled (Yes/No)

## Analysis outputs
- KPI summary and overall churn rate
- Churn rate by customer segment
- Churn rate by tenure group
- Visual charts comparing churn distribution, contract type, tenure, and charges
- Retention recommendations

## Data integrity notes
The included dataset is synthetic and created for this project. The raw CSV is preserved. The pipeline removes duplicate customer IDs, standardizes text, converts numeric fields, imputes numeric missing values using medians, checks domain ranges, and exports a cleaned copy. For a real business dataset, confirm whether duplicate IDs represent true duplicates before removing records and agree on imputation rules with data owners.

## Important interpretation note
This dataset is synthetic, so findings demonstrate an analysis workflow and should not be presented as real-world company results. Churn associations are descriptive and do not prove causation.
