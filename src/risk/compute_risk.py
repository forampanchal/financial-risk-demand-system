import pandas as pd
import numpy as np


def normalize_series(series):
    return (series - series.mean()) / (series.std() + 1e-6)


def compute_volatility(series, window=7):
    return series.rolling(window).std().fillna(0)


def compute_risk(df):
    df = df.copy()

    df["norm_residual"] = normalize_series(df["residual"])
    df["volatility"] = compute_volatility(df["demand"])

    df["risk_score"] = (
        0.5 * df["norm_residual"].abs() +
        0.3 * df["anomaly_flag"] +
        0.2 * normalize_series(df["volatility"])
    )

    return df


def compute_risk(df):
    df = df.copy()

    df["norm_residual"] = normalize_series(df["residual"])
    df["volatility"] = compute_volatility(df["demand"])

    df["risk_score"] = (
        0.5 * df["norm_residual"].abs() +
        0.3 * df["anomaly_flag"] +
        0.2 * normalize_series(df["volatility"])
    )

    return df


def assign_risk_level(df):
    conditions = [
        df["risk_score"] < 0.5,
        df["risk_score"].between(0.5, 1.2),
        df["risk_score"] > 1.2
    ]

    levels = ["LOW", "MEDIUM", "HIGH"]

    df["risk_level"] = np.select(
        conditions,
        levels,
        default="LOW")

    return df
