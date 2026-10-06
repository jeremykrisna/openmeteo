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


def check_city_referential_integrity() -> None:

    log("Checking city referential integrity...")

    query = text(
        """
        SELECT COUNT(*)
        FROM mart.fact_weather f
        LEFT JOIN mart.dim_city c
            ON f.city_key = c.city_key
        WHERE c.city_key IS NULL
        """
    )

    with engine.connect() as connection:
        invalid_rows = connection.execute(query).scalar()

    if invalid_rows > 0:
        fail(
            f"City referential integrity failed. "
            f"Invalid rows: {invalid_rows}"
        )

    log("City referential integrity passed.")


def check_date_referential_integrity() -> None:

    log("Checking date referential integrity...")

    query = text(
        """
        SELECT COUNT(*)
        FROM mart.fact_weather f
        LEFT JOIN mart.dim_date d
            ON f.date_key = d.date_key
        WHERE d.date_key IS NULL
        """
    )

    with engine.connect() as connection:
        invalid_rows = connection.execute(query).scalar()

    if invalid_rows > 0:
        fail(
            f"Date referential integrity failed. "
            f"Invalid rows: {invalid_rows}"
        )

    log("Date referential integrity passed.")


def check_observation_coverage() -> None:

    log("Checking observation coverage...")

    query = text(
        """
        SELECT
            c.city_name,
            COUNT(*) AS observation_count,
            MIN(f.weather_time) AS min_weather_time,
            MAX(f.weather_time) AS max_weather_time
        FROM mart.fact_weather f
        JOIN mart.dim_city c
            ON f.city_key = c.city_key
        GROUP BY
            c.city_name
        ORDER BY
            c.city_name
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()

    if not rows:
        log(
            "WARNING: No observations found in mart.fact_weather."
        )
        return

    for row in rows:

        log(
            f"City={row.city_name} | "
            f"Observations={row.observation_count} | "
            f"From={row.min_weather_time} | "
            f"To={row.max_weather_time}"
        )

    log("Observation coverage check completed.")


def main() -> None:

    log("========================================")
    log("MART DATA QUALITY CHECK")
    log("========================================")

    check_city_referential_integrity()

    check_date_referential_integrity()

    check_observation_coverage()

    log("========================================")
    log("MART DATA QUALITY COMPLETED")
    log("========================================")


if __name__ == "__main__":
    main()