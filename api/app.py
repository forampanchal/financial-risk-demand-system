from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd
import json
import boto3
import os
from pathlib import Path
from io import StringIO

app = FastAPI(title="Financial Risk Monitor API")

# ── Storage config ─────────────────────────────────────────────
S3_BUCKET = os.environ.get("S3_BUCKET")
USE_S3 = os.environ.get("USE_S3", "false").lower() == "true"

LATEST_RISK_PATH = Path("artifacts/latest_risk.csv")
FULL_RISK_PATH = Path("artifacts/daily_risk_output.csv")


# ── Data loading ───────────────────────────────────────────────
def load_csv(s3_key, local_path):
    if USE_S3:
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        return pd.read_csv(StringIO(obj["Body"].read().decode("utf-8")))
    else:
        if not local_path.exists():
            return None
        return pd.read_csv(local_path)


def load_latest():
    return load_csv("latest_risk.csv", LATEST_RISK_PATH)


def load_history():
    return load_csv("daily_risk_output.csv", FULL_RISK_PATH)


# ── Risk colors ────────────────────────────────────────────────
RISK_COLORS = {
    "LOW":      "#00d4aa",
    "MEDIUM":   "#f5a623",
    "HIGH":     "#e8453c",
    "CRITICAL": "#9b1dff",
}
RISK_BG = {
    "LOW":      "rgba(0,212,170,0.12)",
    "MEDIUM":   "rgba(245,166,35,0.12)",
    "HIGH":     "rgba(232,69,60,0.12)",
    "CRITICAL": "rgba(155,29,255,0.12)",
}


# ── Dashboard ──────────────────────────────────────────────────
def render_dashboard(latest, history):
    risk = latest.iloc[0]["risk_level"]
    z_score = round(float(latest.iloc[0]["z_score"]), 4)
    demand = int(latest.iloc[0]["demand"])
    forecast = int(latest.iloc[0]["forecast"])
    date = str(latest.iloc[0]["date"])[:10]
    anomalies = int(history["anomaly_flag"].sum())
    total = len(history)
    anom_rate = round((anomalies / total) * 100, 1)

    risk_color = RISK_COLORS.get(risk, "#666")
    risk_bg = RISK_BG.get(risk, "rgba(100,100,100,0.1)")

    # --- Prepare data for Chart.js (plain Python → JSON) ---
    dates = history["date"].tolist()
    demands = history["demand"].tolist()
    forecasts = [round(float(f), 1) for f in history["forecast"].tolist()]
    zscores = [round(float(z), 4) for z in history["z_score"].tolist()]

    # Anomaly points — null for non-anomaly days so Chart.js skips them
    anomaly_points = [
        int(row["demand"]) if row["anomaly_flag"] == 1 else "null"
        for _, row in history.iterrows()
    ]

    # Risk distribution for doughnut
    risk_counts = history["risk_level"].value_counts().to_dict()
    dist_labels = list(risk_counts.keys())
    dist_values = list(risk_counts.values())
    dist_colors = [RISK_COLORS.get(l, "#666") for l in dist_labels]

    # Recent anomalies table
    recent_anomalies = history[history["anomaly_flag"] == 1].tail(5).iloc[::-1]
    anomaly_rows = ""
    for _, row in recent_anomalies.iterrows():
        rc = RISK_COLORS.get(row["risk_level"], "#666")
        anomaly_rows += f"""
        <tr>
          <td>{str(row['date'])[:10]}</td>
          <td>{int(row['demand']):,}</td>
          <td>{round(float(row['z_score']), 3)}</td>
          <td><span class="badge" style="background:{rc}20;color:{rc};border:1px solid {rc}40">{row['risk_level']}</span></td>
        </tr>"""
    if not anomaly_rows:
        anomaly_rows = '<tr><td colspan="4" style="text-align:center;color:#4a5568">No anomalies detected</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Financial Risk Monitor</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg:      #060b18;
    --surface: #0d1526;
    --border:  rgba(255,255,255,0.06);
    --text:    #e2e8f0;
    --muted:   #4a5568;
    --accent:  #00d4aa;
  }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Grotesk', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }}
  body::before {{
    content: '';
    position: fixed; inset: 0;
    background-image:
      linear-gradient(rgba(0,212,170,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,212,170,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none; z-index: 0;
  }}
  .wrapper {{
    position: relative; z-index: 1;
    max-width: 1400px; margin: 0 auto; padding: 2rem;
  }}
  header {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 2.5rem; padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
  }}
  .logo {{ display: flex; align-items: center; gap: 0.75rem; }}
  .logo-icon {{
    width: 40px; height: 40px;
    background: linear-gradient(135deg, var(--accent), #4a9eff);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
  }}
  h1 {{ font-size: 1.2rem; font-weight: 600; letter-spacing: -0.02em; }}
  h1 span {{ color: var(--accent); }}
  .header-meta {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem; color: var(--muted); text-align: right;
  }}
  .live-dot {{
    display: inline-block; width: 7px; height: 7px;
    background: var(--accent); border-radius: 50%; margin-right: 6px;
    animation: pulse 2s infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.4; transform: scale(0.8); }}
  }}
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem; margin-bottom: 1.5rem;
  }}
  .stat-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.25rem 1.5rem;
    transition: border-color 0.2s;
    animation: fadeUp 0.4s ease both;
  }}
  .stat-card:hover {{ border-color: rgba(255,255,255,0.12); }}
  .risk-card {{
    background: {risk_bg};
    border-color: {risk_color}40 !important;
    position: relative; overflow: hidden;
  }}
  .risk-card::after {{
    content: ''; position: absolute; top: 0; right: 0;
    width: 80px; height: 80px;
    background: radial-gradient({risk_color}25, transparent 70%);
  }}
  .stat-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem; text-transform: uppercase;
    letter-spacing: 0.1em; color: var(--muted); margin-bottom: 0.5rem;
  }}
  .stat-value {{
    font-size: 1.8rem; font-weight: 700;
    letter-spacing: -0.03em; line-height: 1;
  }}
  .stat-sub {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem; color: var(--muted); margin-top: 0.4rem;
  }}
  .charts-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 1rem; margin-bottom: 1.5rem;
  }}
  .chart-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.5rem;
    animation: fadeUp 0.4s ease both;
  }}
  .chart-card.full {{ grid-column: 1 / -1; }}
  .card-title {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.1em; color: var(--muted); margin-bottom: 1rem;
  }}
  .chart-container {{ position: relative; width: 100%; height: 260px; }}
  .chart-container.tall {{ height: 320px; }}
  .bottom-grid {{
    display: grid; grid-template-columns: 1fr 1.5fr; gap: 1rem;
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--muted);
    text-align: left; padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--border);
  }}
  td {{
    padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border);
    color: var(--text); font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
  }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: rgba(255,255,255,0.02); }}
  .badge {{
    display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.05em;
    font-family: 'IBM Plex Mono', monospace;
  }}
  footer {{
    margin-top: 2rem; padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem; color: var(--muted);
  }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  .stat-card:nth-child(1) {{ animation-delay: 0.05s; }}
  .stat-card:nth-child(2) {{ animation-delay: 0.10s; }}
  .stat-card:nth-child(3) {{ animation-delay: 0.15s; }}
  .stat-card:nth-child(4) {{ animation-delay: 0.20s; }}
  .stat-card:nth-child(5) {{ animation-delay: 0.25s; }}
  @media (max-width: 900px) {{
    .charts-grid {{ grid-template-columns: 1fr; }}
    .bottom-grid {{ grid-template-columns: 1fr; }}
    .stats {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>
<div class="wrapper">

  <header>
    <div class="logo">
      <div class="logo-icon">📈</div>
      <div>
        <h1>Financial <span>Risk</span> Monitor</h1>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;color:var(--muted);margin-top:2px">
          Retail Demand Intelligence System
        </div>
      </div>
    </div>
    <div class="header-meta">
      <div><span class="live-dot"></span>LIVE</div>
      <div style="margin-top:4px">Last updated: {date}</div>
      <div style="margin-top:2px">{total} days monitored</div>
    </div>
  </header>

  <div class="stats">
    <div class="stat-card risk-card">
      <div class="stat-label">Current Risk Level</div>
      <div class="stat-value" style="color:{risk_color}">{risk}</div>
      <div class="stat-sub">as of {date}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Z-Score</div>
      <div class="stat-value" style="color:{'#e8453c' if abs(z_score) >= 2 else '#4a9eff'}">{z_score}</div>
      <div class="stat-sub">rolling 30-day window</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Actual Demand</div>
      <div class="stat-value" style="color:var(--accent)">{demand:,}</div>
      <div class="stat-sub">forecast: {forecast:,}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Anomalies</div>
      <div class="stat-value" style="color:#f5a623">{anomalies}</div>
      <div class="stat-sub">{anom_rate}% anomaly rate</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Days Processed</div>
      <div class="stat-value" style="color:#a78bfa">{total}</div>
      <div class="stat-sub">of 1,826 total</div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="chart-card full">
      <div class="card-title">📊 Demand vs Forecast — Anomalies Highlighted</div>
      <div class="chart-container tall"><canvas id="demandChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="card-title">📉 Rolling Z-Score — Threshold ±2σ</div>
      <div class="chart-container"><canvas id="zscoreChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="card-title">🥧 Risk Level Distribution</div>
      <div class="chart-container"><canvas id="distChart"></canvas></div>
    </div>
  </div>

  <div class="bottom-grid">
    <div class="chart-card">
      <div class="card-title">⚠️ Recent Anomalies</div>
      <table>
        <thead><tr><th>Date</th><th>Demand</th><th>Z-Score</th><th>Risk</th></tr></thead>
        <tbody>{anomaly_rows}</tbody>
      </table>
    </div>
    <div class="chart-card">
      <div class="card-title">ℹ️ System Info</div>
      <table><tbody>
        <tr><td>Forecast Model</td><td>Seasonal Naive (t-7)</td></tr>
        <tr><td>Anomaly Method</td><td>Rolling Z-Score (30d)</td></tr>
        <tr><td>Risk Threshold</td><td>|Z| ≥ 2σ</td></tr>
        <tr><td>Pipeline Schedule</td><td>Daily via AWS EventBridge</td></tr>
        <tr><td>Storage</td><td>Amazon S3</td></tr>
        <tr><td>Compute</td><td>AWS Lambda + EC2</td></tr>
        <tr><td>Data Source</td><td>Retail Demand (Kaggle)</td></tr>
        <tr><td>Date Range</td><td>2013-01-01 → 2017-12-31</td></tr>
      </tbody></table>
    </div>
  </div>

  <footer>
    <span>Financial Risk Monitor — Built with FastAPI + AWS</span>
    <span>Pipeline runs daily · Data advances one day per run</span>
  </footer>

</div>

<script>
const DATES     = {json.dumps(dates)};
const DEMANDS   = {json.dumps(demands)};
const FORECASTS = {json.dumps(forecasts)};
const ZSCORES   = {json.dumps(zscores)};
const ANOMALIES = [{','.join(str(v) for v in anomaly_points)}];
const DIST_LABELS = {json.dumps(dist_labels)};
const DIST_VALUES = {json.dumps(dist_values)};
const DIST_COLORS = {json.dumps(dist_colors)};

Chart.defaults.color = '#4a5568';
Chart.defaults.font.family = "'IBM Plex Mono', monospace";
Chart.defaults.font.size = 11;

const gridColor = 'rgba(255,255,255,0.05)';

// ── Demand vs Forecast chart ───────────────────────────────────
new Chart(document.getElementById('demandChart'), {{
  type: 'line',
  data: {{
    labels: DATES,
    datasets: [
      {{
        label: 'Actual Demand',
        data: DEMANDS,
        borderColor: '#00d4aa',
        backgroundColor: 'rgba(0,212,170,0.08)',
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#00d4aa',
        fill: true,
        tension: 0.3,
      }},
      {{
        label: 'Forecast',
        data: FORECASTS,
        borderColor: '#4a9eff',
        backgroundColor: 'transparent',
        borderWidth: 2,
        borderDash: [6, 3],
        pointRadius: 4,
        pointBackgroundColor: '#4a9eff',
        fill: false,
        tension: 0.3,
      }},
      {{
        label: 'Anomaly',
        data: ANOMALIES,
        borderColor: 'transparent',
        backgroundColor: '#e8453c',
        pointRadius: 8,
        pointHoverRadius: 10,
        pointBackgroundColor: '#e8453c',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        showLine: false,
        fill: false,
      }}
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{
        labels: {{ color: '#718096', boxWidth: 12, padding: 16 }}
      }},
      tooltip: {{
        backgroundColor: '#0d1526',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#e2e8f0',
        bodyColor: '#a0aec0',
        callbacks: {{
          label: ctx => {{
            if (ctx.dataset.label === 'Anomaly' && ctx.raw === null) return null;
            const val = ctx.raw?.toLocaleString() ?? ctx.raw;
            return ` ${{ctx.dataset.label}}: ${{val}}`;
          }}
        }}
      }}
    }},
    scales: {{
      x: {{
        grid: {{ color: gridColor }},
        ticks: {{ color: '#4a5568', maxRotation: 45 }}
      }},
      y: {{
        grid: {{ color: gridColor }},
        ticks: {{
          color: '#4a5568',
          callback: val => val.toLocaleString()
        }}
      }}
    }}
  }}
}});

// ── Z-Score chart ──────────────────────────────────────────────
new Chart(document.getElementById('zscoreChart'), {{
  type: 'line',
  data: {{
    labels: DATES,
    datasets: [{{
      label: 'Z-Score',
      data: ZSCORES,
      borderColor: '#4a9eff',
      backgroundColor: 'rgba(74,158,255,0.08)',
      borderWidth: 2,
      pointRadius: 4,
      pointBackgroundColor: ZSCORES.map(z => Math.abs(z) >= 2 ? '#e8453c' : '#4a9eff'),
      fill: true,
      tension: 0.3,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        backgroundColor: '#0d1526',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#e2e8f0',
        bodyColor: '#a0aec0',
      }},
      annotation: {{}}
    }},
    scales: {{
      x: {{
        grid: {{ color: gridColor }},
        ticks: {{ color: '#4a5568', maxRotation: 45 }}
      }},
      y: {{
        grid: {{ color: gridColor }},
        ticks: {{ color: '#4a5568' }},
        afterDataLimits(scale) {{
          scale.max = Math.max(scale.max, 2.5);
          scale.min = Math.min(scale.min, -2.5);
        }}
      }}
    }}
  }}
}});

// ── Distribution doughnut ──────────────────────────────────────
new Chart(document.getElementById('distChart'), {{
  type: 'doughnut',
  data: {{
    labels: DIST_LABELS,
    datasets: [{{
      data: DIST_VALUES,
      backgroundColor: DIST_COLORS,
      borderColor: '#060b18',
      borderWidth: 3,
      hoverOffset: 6,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {{
      legend: {{
        position: 'right',
        labels: {{ color: '#718096', boxWidth: 12, padding: 16 }}
      }},
      tooltip: {{
        backgroundColor: '#0d1526',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#e2e8f0',
        bodyColor: '#a0aec0',
        callbacks: {{
          label: ctx => ` ${{ctx.label}}: ${{ctx.raw}} days (${{ctx.parsed.toFixed(1)}}%)`
        }}
      }}
    }}
  }}
}});
</script>
</body>
</html>"""


# ── Routes ─────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def dashboard():
    latest = load_latest()
    history = load_history()
    if latest is None or history is None:
        return HTMLResponse("<h2 style='font-family:monospace;padding:2rem;color:#e8453c'>Pipeline has not run yet.</h2>")
    latest["date"] = pd.to_datetime(latest["date"]).dt.strftime("%Y-%m-%d")
    history["date"] = pd.to_datetime(history["date"]).dt.strftime("%Y-%m-%d")
    return render_dashboard(latest, history)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/latest-risk")
def get_latest_risk():
    df = load_latest()
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No risk data found.")
    return df.iloc[0].to_dict()


@app.get("/risk-history")
def get_risk_history(limit: int = 30):
    df = load_history()
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No risk history found.")
    df = df.tail(limit).iloc[::-1]
    return df[["date", "demand", "forecast", "z_score", "risk_level", "anomaly_flag"]].to_dict(orient="records")


@app.get("/anomalies")
def get_anomalies(limit: int = 10):
    df = load_history()
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No risk history found.")
    anomalies = df[df["anomaly_flag"] == 1].tail(limit).iloc[::-1]
    if anomalies.empty:
        return {"message": "No anomalies detected so far.", "anomalies": []}
    return {
        "total_anomalies": len(anomalies),
        "anomalies": anomalies[["date", "demand", "forecast", "z_score", "risk_level"]].to_dict(orient="records")
    }
