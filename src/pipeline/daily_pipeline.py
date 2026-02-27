import json
import os
import pandas as pd
import boto3
from pathlib import Path
from src.utils.config import read_demand_data, read_cursor, write_cursor, USE_S3, S3_BUCKET
from src.forecasting.seasonal_naive import seasonal_naive_forecast
from src.anomaly.residual_anomaly import compute_residual, compute_rolling_z_score
from src.risk.compute_risk import assign_risk


def save_to_s3(df, key):
    """Save a dataframe as CSV directly to S3."""
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=df.to_csv(index=False)
    )
    print(f"Saved {key} to S3.")


def save_outputs(df, latest_row):
    """Save pipeline outputs either locally or to S3."""
    if USE_S3:
        save_to_s3(df, "daily_risk_output.csv")
        save_to_s3(latest_row, "latest_risk.csv")
    else:
        # Local development
        Path("artifacts").mkdir(exist_ok=True)
        df.to_csv("artifacts/daily_risk_output.csv", index=False)
        latest_row.to_csv("artifacts/latest_risk.csv", index=False)
        print("Saved outputs locally.")


def main():
    # Load data

    df = read_demand_data()

    if df.empty:
        raise ValueError("Input dataset is empty.")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # ── Read cursor ───────────────────────────────────────────
    # Check what date we last processed
    last_processed = read_cursor()

    if last_processed is None:
        # First ever run — start from the earliest possible valid date
        # We need at least 7 rows for seasonal naive + 30 rows for rolling z-score
        # So we start from row 37 (index 36)
        cursor_date = df["date"].iloc[36]
    else:
        # Find the next date after last processed
        last_date = pd.Timestamp(last_processed)
        remaining = df[df["date"] > last_date]

        if remaining.empty:
            print("Pipeline has reached the end of the dataset. No new data to process.")
            return
        cursor_date = remaining["date"].iloc[0]
    # ── Filter data up to cursor date ─────────────────────────
    # This simulates "we only know data up to today"
    df = df[df["date"] <= cursor_date]

    # ── Forecast ─────────────────────────────────────────────
    df = seasonal_naive_forecast(df)
    df = df.dropna(subset=["forecast"])

    # Residual
    df = compute_residual(df)

    # Rolling Z-score
    df = compute_rolling_z_score(df, window=30)
    df = df.dropna(subset=["z_score"])

    # Risk assignment
    df["risk_level"] = df["z_score"].apply(assign_risk)
    df["anomaly_flag"] = (df["z_score"].abs() >= 2).astype(int)

    # ── Save outputs ──────────────────────────────────────────
    latest_row = df.iloc[-1:]
    save_outputs(df, latest_row)

    # ── Advance cursor ────────────────────────────────────────
    write_cursor(str(cursor_date.date()))

    print(f"Pipeline ran for date: {cursor_date.date()}")
    print(f"Risk level: {df.iloc[-1]['risk_level']}")
    print(f"Z-score: {df.iloc[-1]['z_score']:.4f}")
    print("Daily risk monitoring completed successfully.")


if __name__ == "__main__":
    main()
