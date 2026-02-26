from fastapi import FastAPI, HTTPException
import pandas as pd
from pathlib import Path

app = FastAPI(title="Financial Risk Monitor API")

ARTIFACT_PATH = Path("artifacts/latest_risk.csv")


@app.get("/")
def root():
    return {"message": "Financial Risk Monitor API running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/latest-risk")
def get_latest_risk():
    if not ARTIFACT_PATH.exists():
        raise HTTPException(
            status_code=404, detail="Latest risk file not found.")

    df = pd.read_csv(ARTIFACT_PATH)

    if df.empty:
        raise HTTPException(
            status_code=400, detail="Latest risk file is empty.")

    return df.iloc[0].to_dict()
