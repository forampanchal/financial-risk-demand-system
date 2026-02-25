import pandas as pd
from pathlib import Path
from src.utils.config import get_data_path
from src.forecasting.seasonal_naive import seasonal_naive_forecast
from src.anomaly.residual_anomaly import compute_residual, compute_rolling_z_score
from src.risk.compute_risk import assign_risk


def main():
    # Load data
    data_path = get_data_path()
    df = pd.read_csv(data_path)

    if df.empty:
        raise ValueError("Input dataset is empty.")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Forecast (seasonal naive)
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

    # Ensure artifacts directory exists
    Path("artifacts").mkdir(exist_ok=True)

    # Save only latest day's result
    latest_row = df.iloc[-1:]
    latest_row.to_csv("artifacts/latest_risk.csv", index=False)

    print("Daily risk monitoring completed successfully.")


if __name__ == "__main__":
    main()
