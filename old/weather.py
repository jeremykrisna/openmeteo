import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


KOTA = {
    "Jakarta": {
        "lat": -6.1754,
        "lon": 106.8272,
    },
    "Bandung": {
        "lat": -6.9216,
        "lon": 107.611,
    },
    "Surabaya": {
        "lat": -7.246,
        "lon": 112.7378,
    },
}


API_URL = "https://api.open-meteo.com/v1/forecast"

RAW_FOLDER = Path(
    r"C:\Users\User\Downloads\openweather\raw"
)

RAW_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def get_weather(city, coordinates):

    params = {
        "latitude": coordinates["lat"],
        "longitude": coordinates["lon"],
        "past_days": 10,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m"
        ),
        "timezone": "Asia/Jakarta",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
    }

    for attempt in range(3):
        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=30,
                verify=False, 
            )

            print(
                f"{city}: HTTP "
                f"{response.status_code}"
            )

            if not response.ok:

                print(
                    f"{city}: Response body: "
                    f"{response.text[:1000]}"
                )
                
            if response.status_code == 429:

                if attempt < 2:

                    print(
                        f"{city}: Rate limit, "
                        f"retrying in 60 seconds..."
                    )

                    time.sleep(60)

                    continue

            response.raise_for_status()

            weather_data = response.json()

            weather_data["city"] = city

            weather_data["collected_at"] = (
                datetime.now(JAKARTA_TZ).isoformat()
            )

            timestamp = datetime.now(
                JAKARTA_TZ
            ).strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            file_path = RAW_FOLDER / (
                f"{city.lower()}_{timestamp}.json"
            )

            with file_path.open(
                "w",
                encoding="utf-8",
            ) as f:

                json.dump(
                    weather_data,
                    f,
                    ensure_ascii=False,
                    indent=4,
                )

            print(
                f"{city}: Raw data saved to "
                f"{file_path}"
            )

            return

        except requests.exceptions.RequestException as exc:

            print(
                f"{city}: Request failed "
                f"(attempt {attempt + 1}/3): "
                f"{exc}"
            )

            if attempt < 2:

                print(
                    f"{city}: Retrying in 5 seconds..."
                )

                time.sleep(5)

    raise RuntimeError(
        f"Failed to retrieve weather data "
        f"for {city}"
    )


def main():

    print("Starting weather extraction...")

    for city, coordinates in KOTA.items():

        get_weather(
            city,
            coordinates,
        )

    print("Weather extraction completed.")


if __name__ == "__main__":

    main()