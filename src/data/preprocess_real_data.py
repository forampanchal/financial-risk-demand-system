import pandas as pd
from pathlib import Path

RAW_DATA_PATH = "data/raw/store_item_demand.csv"
OUTPUT_PATH = "data/raw/real_retail_demand.csv"


def load_raw_data():
    df = pd.read_csv(RAW_DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df


def aggregate_daily_demand(df):
    daily = (
        df.groupby("date", as_index=False)["sales"]
        .sum()
        .rename(columns={"sales": "demand"})
        .sort_values("date")
    )
    return daily


def main():
    df = load_raw_data()
    daily_demand = aggregate_daily_demand(df)

    Path("data/raw").mkdir(parents=True, exist_ok=True)
    daily_demand.to_csv(OUTPUT_PATH, index=False)

    print(f"Real retail demand data saved to {OUTPUT_PATH}")
    print(daily_demand.head())
    print(daily_demand.tail())


if __name__ == "__main__":
    main()
