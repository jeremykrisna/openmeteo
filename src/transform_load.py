import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
RAW_FOLDER = PROJECT_ROOT / "raw"


load_dotenv(ENV_FILE)


DB_HOST = os.environ["POSTGRES_HOST"]
DB_PORT = os.environ["POSTGRES_PORT"]
DB_NAME = os.environ["POSTGRES_DB"]
DB_USER = os.environ["POSTGRES_USER"]
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)


engine = create_engine(DATABASE_URL)


def load_raw():

    files = RAW_FOLDER.glob("*.json")

    with engine.begin() as connection:

        for file_path in files:

            print(
                f"Processing file: {file_path}"
            )

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as f:

                weather_data = json.load(f)

            city = weather_data["city"]
            collected_at = weather_data["collected_at"]
            source_file = file_path.name

            connection.execute(
                text("""
                    INSERT INTO raw.weather (
                        city,
                        collected_at,
                        source_file,
                        raw_payload
                    )
                    VALUES (
                        :city,
                        :collected_at,
                        :source_file,
                        :raw_payload
                    )
                """),
                {
                    "city": city,
                    "collected_at": collected_at,
                    "source_file": source_file,
                    "raw_payload": json.dumps(
                        weather_data
                    ),
                },
            )

            print(
                f"{city}: "
                "Raw data loaded into PostgreSQL."
            )

    print("\nRAW loading completed.")


def transform_load_staging():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    raw_id,
                    city,
                    source_file,
                    raw_payload
                FROM raw.weather
                ORDER BY raw_id
            """)
        )

        raw_records = result.mappings().all()

    dataframes = []

    for record in raw_records:

        weather_data = record["raw_payload"]
        hourly = weather_data["hourly"]

        df = pd.DataFrame(
            {
                "weather_time": hourly["time"],
                "temperature_c": (
                    hourly["temperature_2m"]
                ),
                "humidity_pct": (
                    hourly[
                        "relative_humidity_2m"
                    ]
                ),
                "wind_speed_kmh": (
                    hourly["wind_speed_10m"]
                ),
            }
        )

        df["city"] = record["city"]

        df["source_file"] = (
            record["source_file"]
        )

        df["temperature_c"] = pd.to_numeric(
            df["temperature_c"],
            errors="coerce",
        )

        df["wind_speed_kmh"] = pd.to_numeric(
            df["wind_speed_kmh"],
            errors="coerce",
        )

        df["humidity_pct"] = pd.to_numeric(
            df["humidity_pct"],
            errors="coerce",
        )

        df["weather_time"] = (
            pd.to_datetime(
                df["weather_time"]
            )
            .dt.tz_localize(
                "Asia/Jakarta"
            )
        )

        required_columns = [
            "city",
            "weather_time",
            "temperature_c",
            "humidity_pct",
            "wind_speed_kmh",
        ]

        rows_before_cleaning = len(df)

        df = df.dropna(
            subset=required_columns
        )

        rows_after_cleaning = len(df)

        rows_removed = (
            rows_before_cleaning
            - rows_after_cleaning
        )

        print(
            f"{record['city']}: "
            f"{rows_before_cleaning} rows "
            "before cleaning, "
            f"{rows_after_cleaning} rows "
            "after cleaning, "
            f"{rows_removed} rows removed."
        )

        dataframes.append(df)

    if not dataframes:

        raise ValueError(
            "No valid weather data found "
            "in raw.weather."
        )

    df = pd.concat(
        dataframes,
        ignore_index=True,
    )

    print(
        f"\nTotal rows after cleaning: "
        f"{len(df)}"
    )

    with engine.begin() as connection:

        for _, row in df.iterrows():

            connection.execute(
                text("""
                    INSERT INTO staging.weather (
                        city,
                        weather_time,
                        temperature_c,
                        humidity_pct,
                        wind_speed_kmh,
                        source_file
                    )
                    VALUES (
                        :city,
                        :weather_time,
                        :temperature_c,
                        :humidity_pct,
                        :wind_speed_kmh,
                        :source_file
                    )

                    ON CONFLICT (
                        city,
                        weather_time
                    )

                    DO UPDATE SET
                        temperature_c =
                            EXCLUDED.temperature_c,
                        humidity_pct =
                            EXCLUDED.humidity_pct,
                        wind_speed_kmh =
                            EXCLUDED.wind_speed_kmh,
                        loaded_at =
                            CURRENT_TIMESTAMP,
                        source_file =
                            EXCLUDED.source_file
                """),
                {
                    "city": row["city"],
                    "weather_time": (
                        row["weather_time"]
                    ),
                    "temperature_c": (
                        row["temperature_c"]
                    ),
                    "humidity_pct": (
                        row["humidity_pct"]
                    ),
                    "wind_speed_kmh": (
                        row["wind_speed_kmh"]
                    ),
                    "source_file": (
                        row["source_file"]
                    ),
                },
            )

    print(
        "\nRAW → STAGING completed."
    )

    print(
        "\nTotal staging rows processed:"
    )

    print(len(df))


def load_dim_city():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    city,
                    raw_payload->>'latitude'
                        AS latitude,
                    raw_payload->>'longitude'
                        AS longitude
                FROM raw.weather
                ORDER BY raw_id
            """)
        )

        city_records = (
            result.mappings().all()
        )

    cities = {}

    for record in city_records:

        cities[record["city"]] = {
            "latitude": record["latitude"],
            "longitude": record["longitude"],
        }

    with engine.begin() as connection:

        for city, coordinates in (
            cities.items()
        ):

            connection.execute(
                text("""
                    INSERT INTO mart.dim_city (
                        city_name,
                        latitude,
                        longitude
                    )
                    VALUES (
                        :city_name,
                        :latitude,
                        :longitude
                    )

                    ON CONFLICT (city_name)

                    DO UPDATE SET
                        latitude =
                            EXCLUDED.latitude,
                        longitude =
                            EXCLUDED.longitude
                """),
                {
                    "city_name": city,
                    "latitude": (
                        coordinates["latitude"]
                    ),
                    "longitude": (
                        coordinates["longitude"]
                    ),
                },
            )

    print(
        "\nMART dim_city loaded."
    )


def load_dim_date():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT DISTINCT
                    weather_time::date
                        AS full_date
                FROM staging.weather
                ORDER BY full_date
            """)
        )

        date_records = (
            result.mappings().all()
        )

    with engine.begin() as connection:

        for record in date_records:

            full_date = record["full_date"]

            connection.execute(
                text("""
                    INSERT INTO mart.dim_date (
                        date_key,
                        full_date,
                        year,
                        month,
                        day,
                        quarter,
                        month_name,
                        day_of_week,
                        day_name
                    )
                    VALUES (
                        :date_key,
                        :full_date,
                        :year,
                        :month,
                        :day,
                        :quarter,
                        :month_name,
                        :day_of_week,
                        :day_name
                    )

                    ON CONFLICT (date_key)

                    DO UPDATE SET
                        full_date =
                            EXCLUDED.full_date,
                        year =
                            EXCLUDED.year,
                        month =
                            EXCLUDED.month,
                        day =
                            EXCLUDED.day,
                        quarter =
                            EXCLUDED.quarter,
                        month_name =
                            EXCLUDED.month_name,
                        day_of_week =
                            EXCLUDED.day_of_week,
                        day_name =
                            EXCLUDED.day_name
                """),
                {
                    "date_key": int(
                        full_date.strftime(
                            "%Y%m%d"
                        )
                    ),
                    "full_date": full_date,
                    "year": full_date.year,
                    "month": full_date.month,
                    "day": full_date.day,
                    "quarter": (
                        (
                            full_date.month - 1
                        ) // 3
                    ) + 1,
                    "month_name": (
                        full_date.strftime(
                            "%B"
                        )
                    ),
                    "day_of_week": (
                        full_date.isoweekday()
                    ),
                    "day_name": (
                        full_date.strftime(
                            "%A"
                        )
                    ),
                },
            )

    print(
        "\nMART dim_date loaded."
    )


def load_fact_weather():

    with engine.begin() as connection:

        connection.execute(
            text("""
                INSERT INTO mart.fact_weather (
                    city_key,
                    date_key,
                    weather_time,
                    temperature_c,
                    humidity_pct,
                    wind_speed_kmh,
                    loaded_at
                )
                SELECT
                    dc.city_key,
                    dd.date_key,
                    sw.weather_time,
                    sw.temperature_c,
                    sw.humidity_pct,
                    sw.wind_speed_kmh,
                    CURRENT_TIMESTAMP
                FROM staging.weather sw

                INNER JOIN mart.dim_city dc
                    ON sw.city = dc.city_name

                INNER JOIN mart.dim_date dd
                    ON sw.weather_time::date = dd.full_date

                LEFT JOIN staging.weather_quarantine sq
                    ON sw.city = sq.city
                    AND sw.weather_time = sq.weather_time

                WHERE sq.city IS NULL

                ON CONFLICT (
                    city_key,
                    weather_time
                )

                DO UPDATE SET
                    date_key =
                        EXCLUDED.date_key,
                    temperature_c =
                        EXCLUDED.temperature_c,
                    humidity_pct =
                        EXCLUDED.humidity_pct,
                    wind_speed_kmh =
                        EXCLUDED.wind_speed_kmh,
                    loaded_at =
                        CURRENT_TIMESTAMP
            """)
        )

    print(
        "\nMART fact_weather loaded."
    )


def main_staging():

    print(
        "Starting RAW → STAGING..."
    )

    load_raw()

    transform_load_staging()

    print(
        "\nRAW → STAGING "
        "completed successfully."
    )


def main_mart():

    print(
        "Starting STAGING → MART..."
    )

    load_dim_city()

    load_dim_date()

    load_fact_weather()

    print(
        "\nSTAGING → MART "
        "completed successfully."
    )


def main():

    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python transform_load.py "
            "[staging|mart]"
        )
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "staging":

        main_staging()

    elif mode == "mart":

        main_mart()

    else:

        print(
            "Invalid mode. "
            "Use 'staging' or 'mart'."
        )

        sys.exit(1)


if __name__ == "__main__":
    main()