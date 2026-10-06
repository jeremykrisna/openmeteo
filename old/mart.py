import os

import pandas as pd
from sqlalchemy import create_engine, text


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


query = """
SELECT
    kota,
    waktu_ambil,
    suhu,
    kecepatan_angin_kmh,
    kelembaban
FROM staging.weather;
"""

df = pd.read_sql(query, engine)

df["tanggal"] = pd.to_datetime(
    df["waktu_ambil"]
).dt.date


daily = (
    df.groupby(["kota", "tanggal"])
    .agg(
        suhu_rata_rata=("suhu", "mean"),
        suhu_min=("suhu", "min"),
        suhu_max=("suhu", "max"),
        angin_rata_rata_kmh=("kecepatan_angin_kmh", "mean"),
        kelembaban_rata_rata=("kelembaban", "mean"),
        jumlah_observasi=("suhu", "count")
    )
    .reset_index()
)


create_table_sql = """
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS mart.daily_weather (
    kota TEXT NOT NULL,
    tanggal DATE NOT NULL,
    suhu_rata_rata NUMERIC,
    suhu_min NUMERIC,
    suhu_max NUMERIC,
    angin_rata_rata_kmh NUMERIC,
    kelembaban_rata_rata NUMERIC,
    jumlah_observasi INTEGER,
    CONSTRAINT uq_daily_weather
    UNIQUE (kota, tanggal)
);
"""

with engine.begin() as connection:
    connection.execute(text(create_table_sql))


#daily.to_sql(
#    "daily_weather",
#    engine,
#    schema="mart",
#    if_exists="append",
#    index=False
#)

insert_sql = """
INSERT INTO mart.daily_weather (
    kota,
    tanggal,
    suhu_rata_rata,
    suhu_min,
    suhu_max,
    angin_rata_rata_kmh,
    kelembaban_rata_rata,
    jumlah_observasi
)
VALUES (
    :kota,
    :tanggal,
    :suhu_rata_rata,
    :suhu_min,
    :suhu_max,
    :angin_rata_rata_kmh,
    :kelembaban_rata_rata,
    :jumlah_observasi
)
ON CONFLICT (kota, tanggal)
DO UPDATE SET
    suhu_rata_rata = EXCLUDED.suhu_rata_rata,
    suhu_min = EXCLUDED.suhu_min,
    suhu_max = EXCLUDED.suhu_max,
    angin_rata_rata_kmh = EXCLUDED.angin_rata_rata_kmh,
    kelembaban_rata_rata = EXCLUDED.kelembaban_rata_rata,
    jumlah_observasi = EXCLUDED.jumlah_observasi;
"""

with engine.begin() as connection:
    for _, row in daily.iterrows():
        connection.execute(
            text(insert_sql),
            {
                "kota": row["kota"],
                "tanggal": row["tanggal"],
                "suhu_rata_rata": row["suhu_rata_rata"],
                "suhu_min": row["suhu_min"],
                "suhu_max": row["suhu_max"],
                "angin_rata_rata_kmh": row["angin_rata_rata_kmh"],
                "kelembaban_rata_rata": row["kelembaban_rata_rata"],
                "jumlah_observasi": row["jumlah_observasi"]
            }
        )

print("Daily weather data loaded into mart.daily_weather")
