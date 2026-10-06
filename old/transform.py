import json
import pandas as pd
import os
#import shutil

from datetime import datetime
from zoneinfo import ZoneInfo

all_records = []
jakarta_tz = ZoneInfo("Asia/Jakarta")

folder = r"C:\Users\User\Downloads\openweather"
raw_folder = os.path.join(folder, "raw")

#processed_folder = os.path.join(raw_folder, "processed")
#os.makedirs(processed_folder, exist_ok=True) 

for file_name in os.listdir(raw_folder):
    if file_name.endswith('.json'):
        file_path = os.path.join(raw_folder, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                unix_time = data.get("dt")
                
                if unix_time:
                    dt_obj = datetime.fromtimestamp(unix_time, tz=jakarta_tz)
                    waktu_jakarta = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    waktu_jakarta = None
                    
                kelvin_temp = data.get("main", {}).get("temp")
                celsius_temp = round(kelvin_temp - 273.15, 2) if kelvin_temp is not None else None
                
                wind_speed = data.get("wind", {}).get("speed")

                wind_kmh = (
                    round(wind_speed * 3.6, 2)
                    if wind_speed is not None
                    else None
                )
                    
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

            #target_path = os.path.join(processed_folder, file_name)
            #shutil.move(file_path, target_path)
            #print(f"Selesai! {file_name} telah dipindahkan ke folder 'processed'.\n")
            print(f"Selesai memproses {file_name}.")
            
        except Exception as e:
            print(f"Gagal memproses {file_name}: {e}")

if all_records:
    df = pd.DataFrame(all_records)
    print("\n--- Data Baru Berhasil Dikonversi ke DataFrame ---")
    print(df.head())
    
else:
    print("Tidak ada file JSON baru untuk diproses.")