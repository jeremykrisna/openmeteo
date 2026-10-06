import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from sqlalchemy import create_engine, text


RAW_FOLDER = "/app/raw"
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

DB_HOST = os.environ["POSTGRES_HOST"]
DB_PORT = os.environ["POSTGRES_PORT"]
DB_NAME = os.environ["POSTGRES_DB"]
DB_USER = os.environ["POSTGRES_USER"]
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]


connection_string = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(connection_string)

all_records = []

for file_name in os.listdir(RAW_FOLDER):

    if not file_name.endswith(".json"):
        continue

    file_path = os.path.join(RAW_FOLDER, file_name)

    try:

        with open(file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)


        unix_time = data.get("dt")

        if unix_time is not None:

            dt_obj = datetime.fromtimestamp(
                unix_time,
                tz=JAKARTA_TZ
            )

            waktu_jakarta = dt_obj.replace(tzinfo=None)

        else:
            waktu_jakarta = None


        kelvin_temp = data.get("main", {}).get("temp")

        if kelvin_temp is not None:
            celsius_temp = round(kelvin_temp - 273.15, 2)
        else:
            celsius_temp = None


        wind_speed = data.get("wind", {}).get("speed")

        if wind_speed is not None:
            wind_kmh = round(wind_speed * 3.6, 2)
        else:
            wind_kmh = None

        record = {
            "file_name": file_name,
            "country": data.get("sys", {}).get("country"),
            "longitude": data.get("coord", {}).get("lon"),
            "latitude": data.get("coord", {}).get("lat"),
            "kota": data.get("name"),
            "kecepatan_angin_kmh": wind_kmh,
            "suhu": celsius_temp,
            "kelembaban": data.get("main", {}).get("humidity"),
            "cuaca": data.get("weather", [{}])[0].get("main"),
            "deskripsi": data.get("weather", [{}])[0].get("description"),
            "waktu_ambil": waktu_jakarta
        }

        all_records.append(record)

        print(f"Processed: {file_name}")


    except Exception as e:
        print(f"Gagal memproses {file_name}: {e}")

if not all_records:

    print("Tidak ada JSON yang berhasil diproses.")

else:

    df = pd.DataFrame(all_records)

    print("\n--- DataFrame hasil transformasi ---")
    print(df.head())

    df = df.dropna(
        subset=["kota", "waktu_ambil"]
    )

    print(
        f"\nJumlah record setelah validation: {len(df)}"
    )

    create_table_sql = """
    CREATE SCHEMA IF NOT EXISTS staging;

    CREATE TABLE IF NOT EXISTS staging.weather (
        file_name TEXT,
        country TEXT,
        longitude DOUBLE PRECISION,
        latitude DOUBLE PRECISION,
        kota TEXT NOT NULL,
        kecepatan_angin_kmh NUMERIC,
        suhu NUMERIC,
        kelembaban NUMERIC,
        cuaca TEXT,
        deskripsi TEXT,
        waktu_ambil TIMESTAMP NOT NULL,

        CONSTRAINT uq_weather_city_time
        UNIQUE (kota, waktu_ambil)
    );
    """

    with engine.begin() as connection:

        connection.execute(
            text(create_table_sql)
        )

    insert_sql = """
    INSERT INTO staging.weather (
        file_name,
        country,
        longitude,
        latitude,
        kota,
        kecepatan_angin_kmh,
        suhu,
        kelembaban,
        cuaca,
        deskripsi,
        waktu_ambil
    )
    VALUES (
        :file_name,
        :country,
        :longitude,
        :latitude,
        :kota,
        :kecepatan_angin_kmh,
        :suhu,
        :kelembaban,
        :cuaca,
        :deskripsi,
        :waktu_ambil
    )
    ON CONFLICT (kota, waktu_ambil)
    DO NOTHING;
    """

    records = df.to_dict(
        orient="records"
    )

    with engine.begin() as connection:
        result = connection.execute(
            text(insert_sql),
            records
        )

    print(
        f"\nRecord baru yang dimasukkan: {result.rowcount}"
    )
    print("Selesai: RAW → STAGING")