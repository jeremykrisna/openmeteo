import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

DB_HOST = os.environ["POSTGRES_HOST"]
DB_PORT = os.environ["POSTGRES_PORT"]
DB_NAME = os.environ["POSTGRES_DB"]
DB_USER = os.environ["POSTGRES_USER"]
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(
        f"[{timestamp}] {message}",
        flush=True,
    )


def fail(message: str) -> None:
    log(f"ERROR: {message}")
    sys.exit(1)

def check_null_values() -> None:

    log("Checking NULL / empty values...")

    query = text(
        """
        SELECT COUNT(*)
        FROM staging.weather
        WHERE city IS NULL
           OR TRIM(city) = ''
           OR weather_time IS NULL
           OR temperature_c IS NULL
           OR humidity_pct IS NULL
           OR wind_speed_kmh IS NULL
        """
    )

    with engine.connect() as connection:
        invalid_rows = connection.execute(query).scalar()

    if invalid_rows > 0:
        fail(
            "NULL / empty value check failed. "
            f"Invalid rows: {invalid_rows}"
        )

    log("NULL / empty value check passed.")


def check_duplicates() -> None:

    log("Checking duplicate city + weather_time...")

    query = text(
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                city,
                weather_time
            FROM staging.weather
            GROUP BY
                city,
                weather_time
            HAVING COUNT(*) > 1
        ) duplicates
        """
    )

    with engine.connect() as connection:
        duplicate_groups = connection.execute(query).scalar()

    if duplicate_groups > 0:
        fail(
            "Duplicate check failed. "
            f"Duplicate groups: {duplicate_groups}"
        )

    log("Duplicate check passed.")

def quarantine_invalid_rows() -> None:

    log("Checking invalid measurement values...")

    query = text(
        """
        INSERT INTO staging.weather_quarantine (
            city,
            weather_time,
            temperature_c,
            humidity_pct,
            wind_speed_kmh,
            source_file,
            failure_reason,
            quarantined_at
        )
        SELECT
            city,
            weather_time,
            temperature_c,
            humidity_pct,
            wind_speed_kmh,
            source_file,
            CASE
                WHEN humidity_pct < 0
                  OR humidity_pct > 100
                    THEN 'Invalid humidity'

                WHEN wind_speed_kmh < 0
                    THEN 'Invalid wind speed'

                WHEN temperature_c < -50
                  OR temperature_c > 60
                    THEN 'Invalid temperature'
            END AS failure_reason,
            CURRENT_TIMESTAMP
        FROM staging.weather
        WHERE humidity_pct < 0
           OR humidity_pct > 100
           OR wind_speed_kmh < 0
           OR temperature_c < -50
           OR temperature_c > 60
        ON CONFLICT (city, weather_time)
        DO UPDATE SET
            temperature_c = EXCLUDED.temperature_c,
            humidity_pct = EXCLUDED.humidity_pct,
            wind_speed_kmh = EXCLUDED.wind_speed_kmh,
            source_file = EXCLUDED.source_file,
            failure_reason = EXCLUDED.failure_reason,
            quarantined_at = EXCLUDED.quarantined_at
        """
    )

    with engine.begin() as connection:
        result = connection.execute(query)

    log(
        f"Rows quarantined: {result.rowcount}"
    )


def main() -> None:

    log("========================================")
    log("STAGING DATA QUALITY CHECK")
    log("========================================")

    check_null_values()

    check_duplicates()

    quarantine_invalid_rows()

    log("========================================")
    log("STAGING DATA QUALITY PASSED")
    log("========================================")


if __name__ == "__main__":
    main()