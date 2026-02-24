import pandas as pd
import numpy as np
from pathlib import Path
from prophet import Prophet
import joblib

from src.utils.config import get_data_path

DATA_PATH = get_data_path()


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    return df


def prepare_for_prophet(df):
    prophet_df = df.rename(columns={
        "date": "ds",
        "demand": "y"
    })[["ds", "y"]]

    return prophet_df


def train_forecast_model(prophet_df):
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True
    )

    model.fit(prophet_df)
    return model


MODEL_DIR = Path("artifacts/forecasting")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def save_model(model):
    joblib.dump(model, MODEL_DIR / "prophet_model.pkl")


def main():
    df = load_data()
    prophet_df = prepare_for_prophet(df)

    model = train_forecast_model(prophet_df)
    save_model(model)

    print("Forecasting model trained and saved.")


if __name__ == "__main__":
    main()
