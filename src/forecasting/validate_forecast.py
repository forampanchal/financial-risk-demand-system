import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

from src.utils.config import get_data_path

DATA_PATH = get_data_path()


MODEL_PATH = "artifacts/forecasting/prophet_model.pkl"


def load_model():
    return joblib.load(MODEL_PATH)


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


def generate_forecast(model, history_df):
    prophet_df = history_df.rename(
        columns={"date": "ds", "demand": "y"}
    )[["ds", "y"]]

    forecast = model.predict(prophet_df[["ds"]])
    return forecast


def merge_actual_forecast(df, forecast):
    merged = df.merge(
        forecast[["ds", "yhat"]],
        left_on="date",
        right_on="ds",
        how="left"
    )

    merged["residual"] = merged["demand"] - merged["yhat"]
    return merged


def plot_forecast(merged_df):
    plt.figure(figsize=(14, 6))

    plt.plot(
        merged_df["date"],
        merged_df["demand"],
        label="Actual Demand",
        alpha=0.7
    )

    plt.plot(
        merged_df["date"],
        merged_df["yhat"],
        label="Forecast",
        linestyle="--"
    )

    # Highlight shock periods
    shocks = merged_df[merged_df["shock_flag"] == 1]
    plt.scatter(
        shocks["date"],
        shocks["demand"],
        color="red",
        label="Shock",
        zorder=5
    )

    plt.legend()
    plt.title("Actual vs Forecasted Demand with Shock Events")
    plt.xlabel("Date")
    plt.ylabel("Demand")
    plt.tight_layout()
    plt.show()


def main():
    model = load_model()
    df = load_data()

    forecast = generate_forecast(model, df)
    merged = merge_actual_forecast(df, forecast)

    print(merged[["date", "demand", "yhat", "residual"]].head())
    plot_forecast(merged)


if __name__ == "__main__":
    main()
