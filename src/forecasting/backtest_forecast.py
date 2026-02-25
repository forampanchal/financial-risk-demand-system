import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from src.utils.config import get_data_path

DATA_PATH = get_data_path()


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


def time_based_split(df, split_ratio=0.8):
    split_index = int(len(df)*split_ratio)
    train_df = df.iloc[:split_index]
    test_df = df.iloc[split_index:]
    return train_df, test_df


def prepare_prophet_format(df):
    return df.rename(
        columns={"date": "ds", "demand": "y"}
    )[["ds", "y"]]


def train_model(train_prophet_df):
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True
    )
    model.fit(train_prophet_df)
    return model


def evaluate_forecast(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true-y_pred)/y_true))*100

    return mae, rmse, mape


def train_sarima(train_series):
    model = SARIMAX(
        train_series,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 7),
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    results = model.fit(disp=False)
    return results


def forecast_sarima(results, steps):
    forecast = results.forecast(steps=steps)
    return forecast


def main():
    df = load_data()

    train_df, test_df = time_based_split(df)

    train_prophet = prepare_prophet_format(train_df)
    test_prophet = prepare_prophet_format(test_df)

    # ----- SARIMA -----
    sarima_model = train_sarima(train_df["demand"])
    sarima_forecast = forecast_sarima(sarima_model, len(test_df))

    mae_sarima, rmse_sarima, mape_sarima = evaluate_forecast(
        test_df["demand"],
        sarima_forecast
    )

    model = train_model(train_prophet)

    forecast = model.predict(test_prophet[["ds"]])

    test_df = test_df.copy()
    test_df["yhat"] = forecast["yhat"].values

    mae, rmse, mape = evaluate_forecast(
        test_df["demand"],
        test_df["yhat"]
    )

    # ---- Naive Baseline (t-1) ----
    test_df["naive_t1"] = test_df["demand"].shift(1)

    naive_t1_df = test_df.dropna(subset=["naive_t1"])

    mae_naive_t1, rmse_naive_t1, mape_naive_t1 = evaluate_forecast(
        naive_t1_df["demand"],
        naive_t1_df["naive_t1"]
    )

    # ---- Seasonal Naive (t-7) ----
    test_df["naive_t7"] = test_df["demand"].shift(7)

    naive_t7_df = test_df.dropna(subset=["naive_t7"])

    mae_naive_t7, rmse_naive_t7, mape_naive_t7 = evaluate_forecast(
        naive_t7_df["demand"],
        naive_t7_df["naive_t7"]
    )

    # ----- Residual from Seasonal Naive -----
    # Training residuals (for distribution estimation)
    train_df["naive_t7"] = train_df["demand"].shift(7)
    train_residual = train_df["demand"] - train_df["naive_t7"]
    train_residual = train_residual.dropna()

    res_mean = train_residual.mean()
    res_std = train_residual.std()
    test_df["residual_t7"] = test_df["demand"] - test_df["naive_t7"]
    test_df["z_score"] = (test_df["residual_t7"] - res_mean) / res_std

    print("===== Prophet Model =====")
    print(f"MAE  : {mae:.4f}")
    print(f"RMSE : {rmse:.4f}")
    print(f"MAPE : {mape:.2f}%")

    print("\n===== Naive (t-1) =====")
    print(f"MAE  : {mae_naive_t1:.4f}")
    print(f"RMSE : {rmse_naive_t1:.4f}")
    print(f"MAPE : {mape_naive_t1:.2f}%")

    print("\n===== SARIMA Model =====")
    print(f"MAE  : {mae_sarima:.4f}")
    print(f"RMSE : {rmse_sarima:.4f}")
    print(f"MAPE : {mape_sarima:.2f}%")

    print("\n===== Seasonal Naive (t-7) =====")
    print(f"MAE  : {mae_naive_t7:.4f}")
    print(f"RMSE : {rmse_naive_t7:.4f}")
    print(f"MAPE : {mape_naive_t7:.2f}%")

   # Test residuals
    print("\n===== Residual Analysis (t-7) =====")
    print(test_df["z_score"].describe())

    # ----- Z-Score Based Anomaly Detection -----

    # Anomaly flag (|z| >= 2)
    test_df["anomaly_flag"] = (test_df["z_score"].abs() >= 2).astype(int)

    # Risk Level Assignment
    def assign_risk(z):
        if abs(z) < 1:
            return "LOW"
        elif abs(z) < 2:
            return "MEDIUM"
        elif abs(z) < 3:
            return "HIGH"
        else:
            return "CRITICAL"

    test_df["risk_level"] = test_df["z_score"].apply(assign_risk)

    # Summary stats
    total_points = len(test_df)
    total_anomalies = test_df["anomaly_flag"].sum()
    anomaly_rate = (total_anomalies / total_points) * 100

    print("\n===== Z-Score Anomaly Summary =====")
    print(f"Total Observations : {total_points}")
    print(f"Total Anomalies    : {total_anomalies}")
    print(f"Anomaly Rate       : {anomaly_rate:.2f}%")

    print("\nRisk Level Distribution:")
    print(test_df["risk_level"].value_counts())


if __name__ == "__main__":
    main()

# I benchmarked Prophet against naive baselines and found that
# seasonal naive outperformed Prophet due to strong weekly regularity
# in demand. This informed a modeling decision to
# adopt seasonal naive for forecasting and focus modeling complexity on
# anomaly detection instead.
