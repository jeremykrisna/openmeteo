import requests
import urllib3
import time
import json
import os
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#api_key = "OPENWEATHER_API_KEY"
api_key = os.environ["OPENWEATHER_API_KEY"]

#kota = ["Jakarta", "Bandung", "Surabaya"]
#limit = 1

kota = {
    "Jakarta": {"lat": -6.1754, "lon": 106.8272},
    "Bandung": {"lat": -6.9216, "lon": 107.611},
    "Surabaya": {"lat": -7.246, "lon": 112.7378}
}

#folder = r"C:\Users\User\Downloads\openweather"
#raw_folder = os.path.join(folder, "raw")
#
#os.makedirs(raw_folder, exist_ok=True)

raw_folder = "raw"
os.makedirs(raw_folder, exist_ok=True)

loc = []

#for city in kota:
#
#    api_url = (
#        f"http://api.openweathermap.org/geo/1.0/direct"
#        f"?q={city}&limit={limit}&appid={api_key}"
#    )
#
#    try:
#        r = requests.get(api_url,timeout=10,verify=False)
#
#        r.raise_for_status()
#
#        data = r.json()
#
#        if data:
#            loc.append({
#                "city": city,
#                "lat": data[0]["lat"],
#                "lon": data[0]["lon"]
#            })
#
#        else:
#            print(f"{city} tidak ditemukan")
#
#    except requests.exceptions.SSLError as e:
#        print(f"SSL Error: {e}")
#        print(f"Status: {r.status_code}")
#        print(f"Detail: {r.text}")
#
#    except requests.exceptions.HTTPError as e:
#        print(f"HTTP Error: {e}")
#        print(f"Status: {r.status_code}")
#        print(f"Detail: {r.text}")
#
#    except Exception as e:
#        print(f"Error: {e}")

#while True:

for location in loc:
    city = location["city"]
    lat = location["lat"]
    lon = location["lon"]
    weather_url = (f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}")
    for attempt in range(3):
        try:
            rr = requests.get(weather_url,timeout=10,verify=False)
            if rr.status_code == 429:
                print(f"{city}: Rate limit. Attempt {attempt + 1}/3")
                if attempt < 2:
                    time.sleep(60)
                    continue
                else:
                    print(f"{city}: Failed after 3 attempts")
                    break
            rr.raise_for_status()
            weather_data = rr.json()
            print(weather_data)
            sekarang = datetime.now()
            timestamp = sekarang.strftime("%Y-%m-%d_%H-%M-%S")
            file_path = os.path.join(raw_folder,f"{city.lower()}_{timestamp}.json")
            print("Saving to:", file_path)
            try:
                with open(file_path,"w", encoding="utf-8") as json_file:
                    json.dump(weather_data,json_file, ensure_ascii=False,indent=4)
                print(f"{city}: Raw data saved successfully")
            except IOError as e:
                print(
                    f"An error occurred while "
                    f"writing to the file: {e}"
                )
            except TypeError as e:
                print(f"An error occurred while serializing data: {e}")
            break
        except requests.exceptions.RequestException as e:
            print(f"{city}: Request error (Attempt {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                print(f"{city}: Failed after 3 attempts")
                    
#    time.sleep(3 * 60 * 60)