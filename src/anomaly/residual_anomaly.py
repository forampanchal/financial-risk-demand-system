def compute_residual(df):
    df = df.copy()
    df["residual"] = df["demand"] - df["forecast"]
    return df


def compute_rolling_z_score(df, window=30):
    df = df.copy()

    df["rolling_mean"] = df["residual"].rolling(window=window).mean()
    df["rolling_std"] = df["residual"].rolling(window=window).std()

    df["z_score"] = (df["residual"] - df["rolling_mean"]) / df["rolling_std"]

    return df
