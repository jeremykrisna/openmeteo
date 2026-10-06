import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# Lokasi root project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Lokasi .env
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env
load_dotenv(ENV_FILE)


DB_HOST = os.environ["POSTGRES_HOST"]
DB_PORT = os.environ["POSTGRES_PORT"]
DB_NAME = os.environ["POSTGRES_DB"]
DB_USER = os.environ["POSTGRES_USER"]
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


engine = create_engine(DATABASE_URL)


with engine.connect() as connection:

    result = connection.execute(
        text("SELECT 1")
    )

    print(
        "PostgreSQL connection successful!"
    )

    print(
        f"Result: {result.scalar()}"
    )