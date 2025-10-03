
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -------------------------
# Configuration / paths
# -------------------------
FLIGHTS_PATH = "flights2022.csv"
WEATHER_PATH = "flights_weather2022.csv"
OUTDIR = "flight_analysis_outputs"
os.makedirs(OUTDIR, exist_ok=True)

# -------------------------
# Utility functions
# -------------------------
def safe_read_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path)
    print(f"Loaded {path} -> shape: {df.shape}")
    return df

def hhmm_to_datetime(date_series, time_series):
    """
    Convert HHMM-like integers/strings to datetimes using the provided date_series.
    - time_series entries like 530, 1530, 0, NaN are handled.
    - Returns pandas Series of datetimes (same index).
    """
    if time_series is None or date_series is None:
        return pd.Series(pd.NaT, index=date_series.index)
    s = time_series.fillna(np.nan).astype(str).str.replace(r'\.0+$','', regex=True).str.zfill(4)
    mask_valid = s.str.isdigit()
    out = pd.Series(pd.NaT, index=date_series.index, dtype="datetime64[ns]")
    try:
        hh = s[mask_valid].str.slice(0,2).astype(int)
        mm = s[mask_valid].str.slice(2,4).astype(int)
        out_valid = pd.to_datetime(date_series[mask_valid].dt.date) + pd.to_timedelta(hh, unit="h") + pd.to_timedelta(mm, unit="m")
        out.loc[mask_valid] = out_valid
    except Exception:
        # fallback: return NaT if anything fails
        out[:] = pd.NaT
    return out

# -------------------------
# Load data
# -------------------------
flights_raw = safe_read_csv(FLIGHTS_PATH)
weather_raw = safe_read_csv(WEATHER_PATH)

# Standardize column names to uppercase to make matching robust
flights_raw.columns = [c.upper() for c in flights_raw.columns]
weather_raw.columns = [c.upper() for c in weather_raw.columns]

# -------------------------
# Prepare flights dataframe
# -------------------------
fl = flights_raw.copy()

# If YEAR, MONTH, DAY exist, create FL_DATE
if set(["YEAR","MONTH","DAY"]).issubset(fl.columns) and "FL_DATE" not in fl.columns:
    fl["FL_DATE"] = pd.to_datetime(fl[["YEAR","MONTH","DAY"]], errors="coerce")
elif "FL_DATE" in fl.columns:
    fl["FL_DATE"] = pd.to_datetime(fl["FL_DATE"], errors="coerce")
# If there's a time_hour or similar date-time column, convert
if "TIME_HOUR" in fl.columns:
    try:
        fl["TIME_HOUR"] = pd.to_datetime(fl["TIME_HOUR"], errors="coerce")
    except Exception:
        pass

# Create scheduled / actual datetimes when time fields exist (common names)
time_map = {
    "CRS_DEP_TIME": "SCHED_DEP_DATETIME",
    "DEP_TIME": "ACTUAL_DEP_DATETIME",
    "CRS_ARR_TIME": "SCHED_ARR_DATETIME",
    "ARR_TIME": "ACTUAL_ARR_DATETIME"
}
for tcol, outcol in time_map.items():
    if tcol in fl.columns and "FL_DATE" in fl.columns:
        fl[outcol] = hhmm_to_datetime(fl["FL_DATE"], fl[tcol])

# DEP_DELAY may already be minutes; if not, compute using datetimes
if "DEP_DELAY" in fl.columns:
    fl["DEP_DELAY_MIN"] = pd.to_numeric(fl["DEP_DELAY"], errors="coerce")
else:
    if "ACTUAL_DEP_DATETIME" in fl.columns and "SCHED_DEP_DATETIME" in fl.columns:
        fl["DEP_DELAY_MIN"] = (fl["ACTUAL_DEP_DATETIME"] - fl["SCHED_DEP_DATETIME"]).dt.total_seconds() / 60
    else:
        fl["DEP_DELAY_MIN"] = np.nan

# Cancellation flag: prefer explicit column(s), otherwise infer
cancel_col = None
for c in fl.columns:
    if "CANCEL" in c:
        cancel_col = c
        break
if cancel_col:
    fl["CANCELLED_FLAG"] = pd.to_numeric(fl[cancel_col], errors="coerce").fillna(0).astype(int)
else:
    # infer cancelled when both actual dep and arr are missing
    act_dep = fl["ACTUAL_DEP_DATETIME"] if "ACTUAL_DEP_DATETIME" in fl.columns else pd.Series([pd.NaT]*len(fl))
    act_arr = fl["ACTUAL_ARR_DATETIME"] if "ACTUAL_ARR_DATETIME" in fl.columns else pd.Series([pd.NaT]*len(fl))
    fl["CANCELLED_FLAG"] = ((act_dep.isna()) & (act_arr.isna())).astype(int)

# Use a common column name for the carrier/airline
if "CARRIER" in fl.columns and "AIRLINE" not in fl.columns:
    fl = fl.rename(columns={"CARRIER":"AIRLINE"})
elif "OP_CARRIER" in fl.columns and "AIRLINE" not in fl.columns:
    fl = fl.rename(columns={"OP_CARRIER":"AIRLINE"})

# Keep a concise set for later use
useful_cols = [c for c in ["FL_DATE", "AIRLINE", "TAIL_NUM", "FL_NUM", "ORIGIN", "DEST", "DEP_DELAY_MIN", "ARR_DELAY", "DISTANCE", "CANCELLED_FLAG", "SCHED_DEP_DATETIME", "ACTUAL_DEP_DATETIME"] if c in fl.columns]
fl_small = fl[useful_cols].copy()
print("Flights after prep -> shape:", fl_small.shape)

# -------------------------
# Prepare weather dataframe
# -------------------------
wx = weather_raw.copy()
# If weather has YEAR/MONTH/DAY but no DATE, create DATE
if "DATE" not in wx.columns and set(["YEAR","MONTH","DAY"]).issubset(wx.columns):
    wx["DATE"] = pd.to_datetime(wx[["YEAR","MONTH","DAY"]], errors="coerce")
elif "DATE" in wx.columns:
    wx["DATE"] = pd.to_datetime(wx["DATE"], errors="coerce")

# If weather has station column matching ORIGIN, rename to ORIGIN
if "STATION" in wx.columns and "ORIGIN" not in wx.columns:
    # careful — only rename if likely the same code
    wx = wx.rename(columns={"STATION":"ORIGIN"})

# To keep merge efficient, aggregate numeric weather features per date (one row per DATE)
numeric_weather_cols = wx.select_dtypes(include=[np.number]).columns.tolist()
if len(numeric_weather_cols) > 0 and "DATE" in wx.columns:
    wx_agg = wx.groupby("DATE")[numeric_weather_cols].mean().reset_index()
    print("Aggregated weather rows (by date):", wx_agg.shape)
else:
    # if no numeric weather or no date, keep original but be careful merging
    wx_agg = wx.copy()
    print("No numeric weather/date found for aggregation; using raw weather for merge (may be many-to-many).")

# -------------------------
# Merge flights + weather (date-level merge)
# -------------------------
if "FL_DATE" in fl_small.columns and "DATE" in wx_agg.columns:
    merged = pd.merge(fl_small, wx_agg, left_on="FL_DATE", right_on="DATE", how="left", suffixes=("","_WX"))
    print("Merged on FL_DATE==DATE -> shape:", merged.shape)
else:
    # fallback: no weather-date available; proceed with flights only
    merged = fl_small.copy()
    print("No weather DATE to merge on; proceeding with flights only.")

# -------------------------
# Add derived columns
# -------------------------
m = merged.copy()
# Ensure FL_DATE datetime
if "FL_DATE" in m.columns:
    m["FL_DATE"] = pd.to_datetime(m["FL_DATE"], errors="coerce")
m["YEAR_MONTH"] = m["FL_DATE"].dt.to_period("M")
m["DEP_DELAY_MIN"] = pd.to_numeric(m["DEP_DELAY_MIN"], errors="coerce")
m["LONG_DELAY_FLAG"] = (m["DEP_DELAY_MIN"] > 15).astype(int)

# Save a cleaned merged CSV
cleaned_csv_path = os.path.join(OUTDIR, "cleaned_flights_merged.csv")
m.to_csv(cleaned_csv_path, index=False)
print("Saved cleaned merged CSV to:", cleaned_csv_path)

# -------------------------
# Visualizations (matplotlib)
# -------------------------
# Helper to save figures
def savefig(fig, fname):
    path = os.path.join(OUTDIR, fname)
    fig.savefig(path, bbox_inches="tight")
    print("Saved:", path)

# 1) Monthly average departure delay time-series
try:
    monthly = m.groupby("YEAR_MONTH")["DEP_DELAY_MIN"].mean().dropna()
    monthly.index = monthly.index.to_timestamp()
    fig = plt.figure(figsize=(10,5))
    plt.plot(monthly.index, monthly.values)
    plt.title("Monthly Average Departure Delay (minutes)")
    plt.xlabel("Month")
    plt.ylabel("Average Departure Delay (min)")
    plt.grid(True)
    savefig(fig, "monthly_avg_dep_delay.png")
    plt.close(fig)
except Exception as e:
    print("Monthly plot failed:", e)

# 2) Daily cancellations with 30-day rolling mean
try:
    if "CANCELLED_FLAG" in m.columns:
        daily_cancel = m.groupby("FL_DATE")["CANCELLED_FLAG"].sum().sort_index()
        rolling = daily_cancel.rolling(window=30, min_periods=1).mean()
        fig = plt.figure(figsize=(12,5))
        plt.plot(daily_cancel.index, daily_cancel.values, label="Daily cancellations (count)")
        plt.plot(rolling.index, rolling.values, label="30-day rolling mean")
        plt.title("Daily Cancellations with 30-day Rolling Mean")
        plt.xlabel("Date")
        plt.ylabel("Cancellations (count)")
        plt.legend()
        plt.grid(True)
        savefig(fig, "daily_cancellations_rolling.png")
        plt.close(fig)
except Exception as e:
    print("Cancellations plot failed:", e)

# 3) Airline-wise average departure delay (top 15)
try:
    if "AIRLINE" in m.columns:
        airline_delay = m.groupby("AIRLINE")["DEP_DELAY_MIN"].mean().dropna().sort_values(ascending=False)
        top15 = airline_delay.head(15)
        fig = plt.figure(figsize=(10,6))
        plt.barh(top15.index[::-1], top15.values[::-1])
        plt.title("Top 15 Airlines by Average Departure Delay (min)")
        plt.xlabel("Average Dep Delay (min)")
        plt.tight_layout()
        savefig(fig, "airline_avg_dep_delay_top15.png")
        plt.close(fig)
except Exception as e:
    print("Airline plot failed:", e)

# 4) Correlation heatmap for numeric features (subset)
try:
    numeric_cols = m.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) > 1:
        subset = numeric_cols[:20]  # limit to 20 for readability
        corr = m[subset].corr()
        fig = plt.figure(figsize=(10,8))
        plt.imshow(corr, interpolation='nearest', aspect='auto')
        plt.colorbar()
        plt.xticks(range(len(subset)), subset, rotation=90)
        plt.yticks(range(len(subset)), subset)
        plt.title("Correlation matrix (numeric features)")
        plt.tight_layout()
        savefig(fig, "correlation_heatmap.png")
        plt.close(fig)
except Exception as e:
    print("Heatmap failed:", e)

# 5) Scatter: departure delay vs temperature-like field (if present)
temp_candidates = [c for c in m.columns if "TEMP" in c or "TEMPERATURE" in c or "TMAX" in c or "TMIN" in c]
if len(temp_candidates) > 0:
    tcol = temp_candidates[0]
    try:
        sample = m[[tcol, "DEP_DELAY_MIN"]].dropna()
        if len(sample) > 2000:
            sample = sample.sample(2000, random_state=1)
        fig = plt.figure(figsize=(8,6))
        plt.scatter(sample[tcol], sample["DEP_DELAY_MIN"], alpha=0.4, s=8)
        plt.xlabel(tcol)
        plt.ylabel("Departure Delay (min)")
        plt.title(f"Departure Delay vs {tcol}")
        plt.tight_layout()
        savefig(fig, f"dep_delay_vs_{tcol}.png")
        plt.close(fig)
    except Exception as e:
        print("Scatter plot failed:", e)
else:
    print("No temperature-like column found. Skipping dep delay vs temp scatter.")

# -------------------------
# Summary prints
# -------------------------
print("\nSummary stats:")
print("Merged rows:", len(m))
if "DEP_DELAY_MIN" in m.columns:
    print("Mean departure delay (min):", round(m["DEP_DELAY_MIN"].mean(skipna=True),2))
    print("Median departure delay (min):", round(m["DEP_DELAY_MIN"].median(skipna=True),2))
    if "LONG_DELAY_FLAG" in m.columns:
        print("Percent long delays (>15 min):", round(100*m["LONG_DELAY_FLAG"].mean(),2))
if "CANCELLED_FLAG" in m.columns:
    print("Total cancellations recorded:", int(m["CANCELLED_FLAG"].sum()))

print("\nOutput files saved to:", os.path.abspath(OUTDIR))
for fname in sorted(os.listdir(OUTDIR)):
    print("-", fname)
