"""End-to-end customer churn analysis pipeline."""
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REQUIRED = [
    "customer_id", "tenure_months", "contract_type", "internet_service",
    "payment_method", "monthly_charges", "support_calls_90d",
    "monthly_usage_hours", "senior_citizen", "paperless_billing", "churn"
]

def load_and_clean(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    missing = sorted(set(REQUIRED)-set(df.columns))
    if missing:
        raise ValueError(f"Required columns missing: {missing}")
    rows_before = len(df)
    duplicates = int(df.duplicated(subset=["customer_id"]).sum())
    df = df.drop_duplicates(subset=["customer_id"], keep="first").copy()

    text_cols = ["customer_id", "contract_type", "internet_service", "payment_method",
                 "paperless_billing", "churn"]
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()
    for col in ["contract_type", "internet_service", "payment_method", "paperless_billing"]:
        df[col] = df[col].str.title()
    df["churn"] = df["churn"].str.title()

    numeric_cols = ["tenure_months", "monthly_charges", "support_calls_90d",
                    "monthly_usage_hours", "senior_citizen"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in numeric_cols:
        if df[col].notna().any():
            df[col] = df[col].fillna(df[col].median())

    # Keep only valid binary target rows; normalize common Yes/No spellings.
    df["churn"] = df["churn"].replace({"Y": "Yes", "N": "No", "1": "Yes", "0": "No"})
    df = df[df["churn"].isin(["Yes", "No"])].copy()

    # Domain checks
    df.loc[~df["tenure_months"].between(0, 120), "tenure_months"] = np.nan
    df.loc[df["monthly_charges"] < 0, "monthly_charges"] = np.nan
    df.loc[df["support_calls_90d"] < 0, "support_calls_90d"] = np.nan
    df.loc[df["monthly_usage_hours"] < 0, "monthly_usage_hours"] = np.nan
    for col in ["tenure_months", "monthly_charges", "support_calls_90d", "monthly_usage_hours"]:
        if df[col].notna().any():
            df[col] = df[col].fillna(df[col].median())

    summary = {
        "rows_before_cleaning": rows_before,
        "rows_after_cleaning": len(df),
        "duplicate_customer_ids_removed": duplicates,
        "missing_values_after_cleaning": int(df.isna().sum().sum()),
        "overall_churn_rate_pct": round((df["churn"].eq("Yes").mean()*100), 2)
    }
    return df, summary

def create_analysis(df, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    churned = df[df["churn"] == "Yes"]
    overall = df["churn"].eq("Yes").mean()*100

    kpis = pd.DataFrame([
        {"metric":"Total customers","value":len(df)},
        {"metric":"Churned customers","value":len(churned)},
        {"metric":"Retained customers","value":int((df["churn"]=="No").sum())},
        {"metric":"Overall churn rate (%)","value":round(overall,2)},
        {"metric":"Average tenure (months)","value":round(df["tenure_months"].mean(),2)},
        {"metric":"Average monthly charges","value":round(df["monthly_charges"].mean(),2)}
    ])
    kpis.to_csv(outdir/"kpi_summary.csv", index=False)

    segment_rows = []
    for col in ["contract_type","internet_service","payment_method","paperless_billing","senior_citizen"]:
        grouped = df.groupby(col, dropna=False).agg(
            customers=("customer_id","count"),
            churned=("churn",lambda x:(x=="Yes").sum()),
            churn_rate_pct=("churn",lambda x:round((x=="Yes").mean()*100,2))
        ).reset_index()
        grouped.insert(0,"segment",col)
        grouped = grouped.rename(columns={col:"segment_value"})
        segment_rows.append(grouped)
    segments = pd.concat(segment_rows, ignore_index=True)
    segments.to_csv(outdir/"churn_by_segment.csv", index=False)

    tenure_bins = pd.cut(df["tenure_months"], bins=[-1,6,12,24,48,120],
                         labels=["0-6","7-12","13-24","25-48","49+"])
    tenure_analysis = df.assign(tenure_group=tenure_bins).groupby("tenure_group", observed=False).agg(
        customers=("customer_id","count"),
        churn_rate_pct=("churn",lambda x:round((x=="Yes").mean()*100,2))
    ).reset_index()
    tenure_analysis.to_csv(outdir/"churn_by_tenure.csv", index=False)

    # Visualizations
    plt.figure(figsize=(6,4))
    df["churn"].value_counts().reindex(["No","Yes"]).plot(kind="bar")
    plt.title("Customer Churn Distribution"); plt.xlabel("Churn"); plt.ylabel("Customers")
    plt.tight_layout(); plt.savefig(outdir.parent/"visualizations"/"churn_distribution.png", dpi=150); plt.close()

    contract = df.groupby("contract_type")["churn"].apply(lambda x:(x=="Yes").mean()*100).sort_values(ascending=False)
    plt.figure(figsize=(7,4)); contract.plot(kind="bar")
    plt.title("Churn Rate by Contract Type"); plt.xlabel("Contract Type"); plt.ylabel("Churn Rate (%)")
    plt.tight_layout(); plt.savefig(outdir.parent/"visualizations"/"churn_by_contract.png", dpi=150); plt.close()

    plt.figure(figsize=(7,4))
    df.boxplot(column="tenure_months", by="churn")
    plt.title("Customer Tenure by Churn Status"); plt.suptitle("")
    plt.xlabel("Churn"); plt.ylabel("Tenure (months)")
    plt.tight_layout(); plt.savefig(outdir.parent/"visualizations"/"tenure_vs_churn.png", dpi=150); plt.close()

    plt.figure(figsize=(7,4))
    df.boxplot(column="monthly_charges", by="churn")
    plt.title("Monthly Charges by Churn Status"); plt.suptitle("")
    plt.xlabel("Churn"); plt.ylabel("Monthly Charges")
    plt.tight_layout(); plt.savefig(outdir.parent/"visualizations"/"charges_vs_churn.png", dpi=150); plt.close()

    recommendations = [
        ("Month-to-month contracts", "Offer discounts or benefits for switching to annual contracts; prioritize renewal outreach."),
        ("Short-tenure customers", "Create a 30/60/90-day onboarding journey and proactively check in with new customers."),
        ("High support-call frequency", "Identify recurring service issues, improve first-contact resolution, and follow up after complaints."),
        ("High monthly charges", "Review pricing/value communication and test targeted bundles or loyalty offers."),
        ("Low product usage", "Use engagement nudges, tutorials, and personalized feature recommendations.")
    ]
    pd.DataFrame(recommendations,columns=["observed_risk_area","retention_recommendation"]).to_csv(outdir/"retention_recommendations.csv",index=False)

    return kpis, segments, tenure_analysis

def main(input_path, output_dir):
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    df, cleaning = load_and_clean(input_path)
    df.to_csv(outdir/"customer_churn_cleaned.csv", index=False)
    pd.DataFrame([cleaning]).to_csv(outdir/"cleaning_summary.csv", index=False)
    kpis, segments, tenure = create_analysis(df, outdir)
    print("Customer churn analysis completed.")
    print(kpis.to_string(index=False))
    print(f"Reports saved to: {outdir.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/customer_churn_raw.csv")
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()
    main(args.input, args.output_dir)
