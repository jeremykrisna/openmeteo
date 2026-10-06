import json
import time
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

REQUIRED_HOURLY_FIELDS = {
    "time",
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
}

KOTA = [
    "Jakarta",
    "Bandung",
    "Surabaya",
]

GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FOLDER = PROJECT_ROOT / "raw"

RAW_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

def validate_weather_schema(data):
    hourly = data.get("hourly")

    if not hourly:
        raise ValueError("Schema drift detected: missing 'hourly' data")

    missing_fields = REQUIRED_HOURLY_FIELDS - hourly.keys()

    if missing_fields:
        raise ValueError(
            f"Schema drift detected: missing required fields "
            f"{sorted(missing_fields)}"
        )

def get_coordinates(city):
    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
        "countryCode": "ID",
    }

    for attempt in range(3):
        try:
            response = requests.get(
                GEOCODING_URL,
                params=params,
                timeout=30,
                verify=False
            )

            print(
                f"{city}: Geocoding HTTP "
                f"{response.status_code}"
            )

            response.raise_for_status()

            geocoding_data = response.json()

            results = geocoding_data.get(
                "results",
                []
            )

            if not results:
                raise RuntimeError(
                    f"No geocoding result found "
                    f"for {city}"
                )

            location = results[0]

            latitude = location["latitude"]
            longitude = location["longitude"]

            print(
                f"{city}: coordinates = "
                f"{latitude}, {longitude}"
            )

            return {
                "lat": latitude,
                "lon": longitude,
            }

        except (
            requests.exceptions.RequestException,
            KeyError,
        ) as exc:

            print(
                f"{city}: Geocoding failed "
                f"(attempt {attempt + 1}/3): "
                f"{exc}"
            )

            if attempt < 2:
                print(
                    f"{city}: Retrying in 5 seconds..."
                )
                time.sleep(5)

    raise RuntimeError(
        f"Failed to geocode {city}"
    )


def get_weather(
    city,
    coordinates,
    start_datetime,
    end_datetime,
):
    params = {
        "latitude": coordinates["lat"],
        "longitude": coordinates["lon"],
        "start_hour": start_datetime,
        "end_hour": end_datetime,
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
                verify=False
            )

            print(
                f"{city}: Weather HTTP "
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
            
            validate_weather_schema(weather_data)

            hourly = weather_data["hourly"]

            filtered_indices = [
                i
                for i, timestamp in enumerate(hourly["time"])
                if timestamp < end_datetime
            ]

            for key in hourly:
                hourly[key] = [
                    hourly[key][i]
                    for i in filtered_indices
                ]

            weather_data["city"] = city

            weather_data["collected_at"] = (
                datetime.now(
                    JAKARTA_TZ
                ).isoformat()
            )

            weather_data["start_hour"] = (
                start_datetime
            )

            weather_data["end_hour"] = (
                end_datetime
            )

            timestamp = datetime.now(
                JAKARTA_TZ
            ).strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            file_path = RAW_FOLDER / (
                f"{city.lower()}_"
                f"{start_datetime.replace(':', '-')}_"
                f"{end_datetime.replace(':', '-')}_"
                f"{timestamp}.json"
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


def main(start_datetime, end_datetime):
    print(
        "Starting weather extraction..."
    )

    print(
        f"Extraction period: "
        f"{start_datetime} → {end_datetime}"
    )

    for city in KOTA:

        coordinates = get_coordinates(city)

        get_weather(
            city,
            coordinates,
            start_datetime,
            end_datetime,
        )

    print(
        "Weather extraction completed."
    )


if __name__ == "__main__":
    start_datetime = sys.argv[1]
    end_datetime = sys.argv[2]

    main(
        start_datetime,
        end_datetime,
    )