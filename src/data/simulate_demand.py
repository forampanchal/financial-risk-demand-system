import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# -----------------------------
# Simulation configuration
# -----------------------------

START_DATE = "2022-01-01"
NUM_DAYS = 900  # ~2.5 years of daily data

BASE_DEMAND = 10000
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


def generate_base_demand():
    dates = pd.date_range(start=START_DATE, periods=NUM_DAYS, freq="D")

    demand = np.full(NUM_DAYS, BASE_DEMAND)

    return pd.DataFrame({
        "date": dates,
        "demand": demand
    })


def add_seasonality(df):
    df = df.copy()

    # Weekly seasonality (weekday vs weekend)
    weekly_pattern = np.where(
        df["date"].dt.weekday < 5,  # Mon–Fri
        1.05,  # weekdays slightly higher
        0.90   # weekends lower
    )

    # Yearly seasonality
    yearly_pattern = 1 + 0.15 * np.sin(
        2 * np.pi * df.index / 365
    )

    df["demand"] = df["demand"] * weekly_pattern * yearly_pattern
    return df


def add_noise(df):
    df = df.copy()

    noise = np.random.normal(
        loc=0,
        scale=0.05,  # 5% noise
        size=len(df)
    )

    df["demand"] = df["demand"] * (1 + noise)
    return df


def inject_shocks(df):
    df = df.copy()
    df["shock_flag"] = 0

    # Demand spike
    spike_start = 300
    spike_end = 310
    df.loc[spike_start:spike_end, "demand"] *= 1.35
    df.loc[spike_start:spike_end, "shock_flag"] = 1

    # Demand drop
    drop_start = 550
    drop_end = 565
    df.loc[drop_start:drop_end, "demand"] *= 0.6
    df.loc[drop_start:drop_end, "shock_flag"] = 1

    # Regime change (new normal)
    regime_start = 700
    df.loc[regime_start:, "demand"] *= 1.25

    return df


def main():
    df = generate_base_demand()
    df = add_seasonality(df)
    df = add_noise(df)
    df = inject_shocks(df)

    df["demand"] = df["demand"].clip(lower=0).round().astype(int)

    output_path = "data/simulated/demand_with_shocks.csv"
    df.to_csv(output_path, index=False)

    print(f"Simulated dataset saved to {output_path}")
    print(df.head())


if __name__ == "__main__":
    main()
