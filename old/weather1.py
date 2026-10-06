import json
import os
#import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
#import urllib3
from sqlalchemy import create_engine, text


#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = os.environ["OPENWEATHER_API_KEY"]
RAW_FOLDER = "/app/raw"
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


cities = {
    "Jakarta": {
        "lat": -6.1754,
        "lon": 106.8272
    },
    "Bandung": {
        "lat": -6.9216,
        "lon": 107.611
    },
    "Surabaya": {
        "lat": -7.246,
        "lon": 112.7378
    }
}

os.makedirs(RAW_FOLDER, exist_ok=True)

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

create_raw_table_sql = """
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.weather (
    id BIGSERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    extracted_at TIMESTAMP NOT NULL,
    payload JSONB NOT NULL
);
"""


with engine.begin() as connection:
    connection.execute(text(create_raw_table_sql))

for city, location in cities.items():
    lat = location["lat"]
    lon = location["lon"]
    weather_url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}"
        f"&lon={lon}"
        f"&appid={API_KEY}"
    )

    #for attempt in range(3):
    try:
        response = requests.get(weather_url,timeout=10)

        #if response.status_code == 429:
        #    print(f"{city}: Rate limit. Attempt {attempt + 1}/3")
        #    if attempt < 2:
        #        time.sleep(60)
        #        continue
        #    print(f"{city}: Failed after 3 attempts")
        #    break
        response.raise_for_status()

        weather_data = response.json()

        extracted_at = datetime.now(JAKARTA_TZ).replace(tzinfo=None)

        timestamp = extracted_at.strftime("%Y-%m-%d_%H-%M-%S")

        file_path = os.path.join(RAW_FOLDER,f"{city.lower()}_{timestamp}.json")
        with open(file_path,"w",encoding="utf-8") as json_file:
            json.dump(weather_data,json_file,ensure_ascii=False,indent=4)
        print(f"{city}: Raw JSON saved → {file_path}")

        insert_raw_sql = """
        INSERT INTO raw.weather (
            city,
            extracted_at,
            payload
        )
        VALUES (
            :city,
            :extracted_at,
            :payload
        );
        """

        with engine.begin() as connection:
            connection.execute(text(insert_raw_sql),
                {
                    "city": city,
                    "extracted_at": extracted_at,
                    "payload": json.dumps(weather_data)
                }
            )

        print(f"{city}: Raw payload inserted into raw.weather")
        #break
    except requests.exceptions.RequestException as e:
        raise e