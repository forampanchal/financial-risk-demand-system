from src.utils.config import get_data_path
from src.forecasting.validate_forecast import (
    generate_forecast,
    load_model as load_forecast_model
)

from src.risk.compute_risk import compute_risk, assign_risk_level
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest


MODEL_PATH = "artifacts/forecasting/prophet_model.pkl"
DATA_PATH = get_data_path()

ANOMALY_MODEL_PATH = "artifacts/anomaly/isolation_forest.pkl"


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df


def compute_residuals(df, forecast):
    merged = df.merge(
        forecast[["ds", "yhat"]],
        left_on="date",
        right_on="ds",
        how="left"
    )

    merged["residual"] = merged["demand"] - merged["yhat"]
    return merged


def train_anomaly_model(residuals):
    model = IsolationForest(
        n_estimators=200,
        contamination=0.03,  # ~3% anomalies
        random_state=42
    )

    model.fit(residuals[["residual"]])
    return model


def flag_anomalies(model, df):
    df["anomaly_flag"] = model.predict(df[["residual"]])
    df["anomaly_flag"] = df["anomaly_flag"].map({1: 0, -1: 1})
    return df


def main():
    forecast_model = load_forecast_model()
    df = load_data()

    forecast = generate_forecast(forecast_model, df)
    merged = compute_residuals(df, forecast)

    anomaly_model = train_anomaly_model(merged)
    merged = flag_anomalies(anomaly_model, merged)

    # 🔥 NEW: risk scoring
    merged = compute_risk(merged)
    merged = assign_risk_level(merged)

    print(
        merged[merged["risk_level"] == "HIGH"][
            ["date", "demand", "yhat", "residual",
                "anomaly_flag", "risk_score", "risk_level"]
        ].head(10)
    )

    import os
    os.makedirs("artifacts/anomaly", exist_ok=True)
    joblib.dump(anomaly_model, ANOMALY_MODEL_PATH)

    print("Anomaly + risk scoring complete.")
    return merged


if __name__ == "__main__":
    main()
