import pandas as pd


def seasonal_naive_forecast(df, season_length=7):
    df = df.copy()
    df["forecast"] = df["demand"].shift(season_length)
    return df
