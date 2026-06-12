import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

# Load data
df = pd.read_csv(
    "data/Dataset 2_Hourly EV loads - Per user.csv",
    sep=";",
    engine="python"
)

# Clean numeric columns
cols = ["Synthetic_3_6kW", "Synthetic_7_2kW",
        "Flex_3_6kW", "Flex_7_2kW"]

for col in cols:
    df[col] = df[col].astype(str).str.replace(",", ".")
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["Total_Load"] = df[cols].sum(axis=1)

# Convert date
df["date_from"] = pd.to_datetime(df["date_from"], format="%d.%m.%Y %H:%M")

# Aggregate hourly
df_hourly = df.groupby("date_from")["Total_Load"].sum().reset_index()

df_hourly = df_hourly.sort_values("date_from")
df_hourly["hour"] = df_hourly["date_from"].dt.hour
df_hourly["day"] = df_hourly["date_from"].dt.day
df_hourly["month"] = df_hourly["date_from"].dt.month
df_hourly["prev_load"] = df_hourly["Total_Load"].shift(1)
df_hourly = df_hourly.dropna()

X = df_hourly[["hour", "day", "month", "prev_load"]]
y = df_hourly["Total_Load"]

model = RandomForestRegressor(n_estimators=300, random_state=42)
model.fit(X, y)

# Save model
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/load_model.pkl")

print("✅ Model trained and saved successfully.")