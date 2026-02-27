import json
import os
import boto3
import pandas as pd
from pathlib import Path

# ── Data paths ────────────────────────────────────────────────
USE_SIMULATED_DATA = False

SIMULATED_DATA_PATH = "data/simulated/demand_with_shocks.csv"
REAL_DATA_PATH = "data/raw/real_retail_demand.csv"


# ── S3 config ─────────────────────────────────────────────────
# We read these from environment variables so we never hardcode
# sensitive info in our code.
# Locally → we set these in our terminal
# On AWS  → we set these in Lambda/EC2 environment variables


S3_BUCKET = os.environ.get("S3_BUCKET")
USE_S3 = os.environ.get("USE_S3", "false").lower() == "true"


# ── Cursor config ─────────────────────────────────────────────
# Tracks which date the pipeline last processed.
# Right now this is a local JSON file.
# Later we'll swap this for S3 — the read/write functions stay the same.
CURSOR_PATH = Path("artifacts/cursor.json")
LATEST_RISK_PATH = Path("artifacts/latest_risk.csv")


def get_data_path():
    return SIMULATED_DATA_PATH if USE_SIMULATED_DATA else REAL_DATA_PATH


def read_demand_data():
    """Read demand CSV from S3 or local depending on environment."""
    if USE_S3:
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=S3_BUCKET, Key="real_retail_demand.csv")
        return pd.read_csv(obj["Body"])
    else:
        return pd.read_csv(get_data_path())


def read_cursor():
    """Return the last processed date as a string (YYYY-MM-DD).
    If no cursor sexists yet, return None so the pipeline knows its
    the the first run ever"""
    """Read last processed date.
    Uses S3 if USE_S3=true, otherwise reads local file."""

    if USE_S3:
        s3 = boto3.client("s3")
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key="cursor.json")
            data = json.loads(obj["Body"].read().decode("utf-8"))
            return data.get("last_processed_date")
        except s3.exceptions.NoSuchKey:
            # First ever run, cursor doesn't exist yet
            return None
    else:
        # Local Development
        if not CURSOR_PATH.exists():
            return None
        with open(CURSOR_PATH, "r") as f:
            data = json.load(f)
            return data.get("last_processed_date")


def write_cursor(date_str):
    """Save the last processed date so the next run knows wjere to continue. """
    """Save last processed date.
    Uses S3 if USE_S3=true, otherwise writes local file."""
    if USE_S3:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=S3_BUCKET,
            Key="cursor.json",
            Body=json.dumps({"last_processed_date": date_str})
        )

    else:
        # Local development
        CURSOR_PATH.parent.mkdir(exist_ok=True)
        with open(CURSOR_PATH, "w") as f:
            json.dump({"last_processed_date": date_str}, f)
