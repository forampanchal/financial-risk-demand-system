from fastapi import FastAPI, HTTPException
import pandas as pd
from pathlib import Path

app = FastAPI(title="Financial Risk Monitor API")

LATEST_RISK_PATH = Path("artifacts/latest_risk.csv")
FULL_RISK_PATH = Path("artifacts/daily_risk_output.csv")


@app.get("/")
def root():
    return {"message": "Financial Risk Monitor API running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/latest-risk")
def get_latest_risk():
    if not LATEST_RISK_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No risk data found. Has the pipeline run yet?")

    df = pd.read_csv(LATEST_RISK_PATH)

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Latest risk file is empty.")

    return df.iloc[0].to_dict()


@app.get("/risk-history")
def get_risk_history(limit: int = 30):
    if not FULL_RISK_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No risk history found. Has the pipeline run yet?")

    df = pd.read_csv(FULL_RISK_PATH)

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Risk history file is empty.")

    # Return most recent `limit` rows, latest first
    df = df.tail(limit).iloc[::-1]

    return df[["date", "demand", "forecast", "z_score",
               "risk_level", "anomaly_flag"]].to_dict(orient="records")


@app.get("/anomalies")
def get_anomalies(limit: int = 10):
    if not FULL_RISK_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No risk history found. Has the pipeline run yet?")

    df = pd.read_csv(FULL_RISK_PATH)

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Risk history file is empty.")

    # Only return flagged anomalies, most recent first
    anomalies = df[df["anomaly_flag"] == 1].tail(limit).iloc[::-1]

    if anomalies.empty:
        return {"message": "No anomalies detected so far.", "anomalies": []}

    return {
        "total_anomalies": len(anomalies),
        "anomalies": anomalies[["date", "demand", "forecast",
                                "z_score", "risk_level"]].to_dict(orient="records")
    }
