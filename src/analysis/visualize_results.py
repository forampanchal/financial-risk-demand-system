import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


DATA_PATH = "artifacts/daily_risk_output.csv"
PLOTS_DIR = Path("artifacts/plots")


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df


def plot_demand_vs_forecast(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["demand"],
        mode="lines",
        name="Actual Demand"
    ))

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["forecast"],
        mode="lines",
        name="Forecast"
    ))

    # Highlight anomalies
    anomalies = df[df["anomaly_flag"] == 1]

    fig.add_trace(go.Scatter(
        x=anomalies["date"],
        y=anomalies["demand"],
        mode="markers",
        name="Anomalies",
        marker=dict(size=8)
    ))

    fig.update_layout(
        title="Demand vs Forecast",
        xaxis_title="Date",
        yaxis_title="Demand",
        template="plotly_white"
    )

    fig.write_html(PLOTS_DIR / "demand_vs_forecast.html")


def plot_zscore(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["z_score"],
        mode="lines",
        name="Z-Score"
    ))

    # Threshold lines
    fig.add_hline(y=2, line_dash="dash")
    fig.add_hline(y=-2, line_dash="dash")

    fig.update_layout(
        title="Rolling Z-Score Over Time",
        xaxis_title="Date",
        yaxis_title="Z-Score",
        template="plotly_white"
    )

    fig.write_html(PLOTS_DIR / "zscore_over_time.html")


def main():
    if not Path(DATA_PATH).exists():
        raise FileNotFoundError("daily_risk_output.csv not found.")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()

    plot_demand_vs_forecast(df)
    plot_zscore(df)

    print("Visualization files generated successfully.")


if __name__ == "__main__":
    main()
