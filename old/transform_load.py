import json
from pathlib import Path

import pandas as pd


RAW_FOLDER = Path(
    r"C:\Users\User\Downloads\openweather\raw"
)


files = RAW_FOLDER.glob("*.json")


dataframes = []


for file_path in files:

    print(f"Processing file: {file_path}")

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        weather_data = json.load(f)

    hourly = weather_data["hourly"]

    df = pd.DataFrame(
        {
            "weather_time": hourly["time"],
            "temperature_c": hourly["temperature_2m"],
            "humidity_pct": hourly["relative_humidity_2m"],
            "wind_speed_kmh": hourly["wind_speed_10m"],
        }
    )

    df["city"] = weather_data["city"]

    df["weather_time"] = pd.to_datetime(
        df["weather_time"]
    )

    dataframes.append(df)


df = pd.concat(
    dataframes,
    ignore_index=True,
)


print("\nFirst 5 rows:")
print(df.head())


print("\nLast 5 rows:")
print(df.tail())


print("\nDataFrame info:")
print(df.info())


print("\nNull values:")
print(df.isna().sum())


print("\nRows per city:")
print(df["city"].value_counts())


print("\nTotal row count:")
print(len(df))