import requests
import pandas as pd
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
import re


'''

                  Disclaimer

This project in only for Study Purpose
This project work with Google Gemini 3 and TMD Weather Forecast API
this project Only forecast in Thailand and hourly only

API by Thai Meteorological Department
API Document "https://data.tmd.go.th/nwpapi/doc/"

'''


#--------------------Store the config file--------------------
CONFIG_FILE = "settings.json"

#--------------------Function--------------------
def load_saved_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {} # Return empty if no file exists

def save_current_settings():
    
    if entry_token.get() == "" or entry_google_maps.get() == "":
        messagebox.showwarning("Missing Info", "Please enter all required fields!")
        return
    
    settings = {
        "token": entry_token.get(),
        "mode": Daily_hourly.get(),
        "Map_url": entry_google_maps.get().strip()
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f)


def load_weather_data():

    save_current_settings()

    if  Daily_hourly.get() == "daily":
        mode = "daily"
        duration = 10
        fields = "cond,ws10m,tc_max,tc_min,rh,rain"
    else:
        mode = "hourly"
        duration = 48
        fields = "cond,ws10m,tc,rh,rain" 
    
    user_token = entry_token.get()
    coordinates = extract_lat_lon_from_google_maps(entry_google_maps.get().strip())
    if coordinates is None:
        return None
    target_lat, target_lon = coordinates
    

    # API Document "https://data.tmd.go.th/nwpapi/doc/"
    url = f"https://data.tmd.go.th/nwpapi/v1/forecast/location/{mode}/at"
    querystring = {"lat": target_lat, "lon": target_lon, "duration": duration, "fields": fields}
    headers = {'accept': "application/json", 'authorization': f"Bearer {user_token.strip()}"}

    try:
        # Get data
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        forecast_list = data['WeatherForecasts'][0]['forecasts']

        condition_map = {1: "Clear", 2: "Partly cloudy", 3: "Cloudy", 4: "Overcast", 5: "Light rain", 
                         6: "Moderate rain", 7: "Heavy rain", 8: "Thunderstorm", 9: "Very cold", 
                         10: "Cold", 11: "Cool", 12: "Very hot"}

        # Json to pandas
        df = pd.json_normalize(forecast_list)
        df.columns = [c.replace('data.', '') for c in df.columns]
        if mode == "daily":
            df['Temperature(°C)'] = df['tc_min'].astype(str) + " °C / " + df['tc_max'].astype(str) + " °C max"
        else:
            df['Temperature(°C)'] = df['tc'].astype(str) + " °C"
        df = df.rename(columns={
            'time': 'Time',
            'cond': 'Condition',
            'rain': 'Rainfall(mm)',
            'rh': 'Humidity(%)',
            'ws10m': 'Wind Speed(m/s)'
        })
        df = df[['Time', 'Condition', 'Rainfall(mm)', 'Humidity(%)', 'Temperature(°C)', 'Wind Speed(m/s)']]
        df['Time'] = pd.to_datetime(df['Time'])
        df['Condition'] = df['Condition'].map(condition_map)

        for i in tree.get_children(): tree.delete(i)
        for index, row in df.iterrows():
            if mode == "daily":
                formatted_time = row['Time'].strftime('%d-%m-%Y')
            else:
                formatted_time = row['Time'].strftime('%d-%m-%Y %H:%M')
            tree.insert("", "end", values=(formatted_time, row['Condition'], row['Rainfall(mm)'], 
                                           row['Humidity(%)'], row['Temperature(°C)'], row['Wind Speed(m/s)']))
            
    
    except requests.RequestException as e:
        messagebox.showerror("Network Error", f"check your internet connection and API KEY")
        return
    except (KeyError, IndexError) as e:
        messagebox.showerror("Data Error", f"Invalid API response: {e}")
        return
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error: {e}")  
        return


def show_How_to_get_API_key():
    How_to_get_API_key = """
    Go to https://data.tmd.go.th/nwpapi/doc/
    and follow Introduction
    """
    messagebox.showinfo("How to get API key", How_to_get_API_key)


def extract_lat_lon_from_google_maps(url: str):
    """
    Extract latitude and longitude from a Google Maps URL.

    Supports formats like:
    - https://maps.google.com/?q=12.710220,102.052307
    - https://www.google.com/maps/place/.../@12.710220,102.052307,15z
    - https://www.google.com/maps/search/?api=1&query=12.710220,102.052307
    - https://www.google.com/maps/search/12.711099,+102.073581

    Returns:
        (lat, lon) as floats
    Raises:
        ValueError if coordinates not found
    """

    if not url:
        raise ValueError("Empty URL")

    # Expand short URL if needed (maps.app.goo.gl etc.)
    try:
        response = requests.get(url, timeout=15, allow_redirects=True)
        final_url = response.url
    except:
        final_url = url  # fallback

    # Pattern 1: @lat,lon
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon

    # Pattern 2: ?q=lat,lon or &q=lat,lon
    match = re.search(r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon

    # Pattern 3: query=lat,lon
    match = re.search(r'[?&]query=(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon
    
    
    # Pattern 4: /search/lat,lon or /maps/lat,lon (path-based format after redirect)
    match = re.search(r'/[-]?(\d+\.\d+),([-+]?\d+\.\d+)(?:\?|$|[^-\d])', final_url)
    if match:
        lat = float(match.group(1))
        lon_str = match.group(2).replace('+', '')
        lon = float(lon_str)
        return lat, lon

    messagebox.showerror("Error", "Latitude/Longitude not found in URL")
    return None



#--------------------User Interface--------------------


root = tk.Tk()
root.title("Weather Forecast App   ( MAX 10 Days /  48 Hours )")
root.geometry("950x600")


#--------------------Load existing settings--------------------


saved_data = load_saved_settings()


#--------------------Setting Farme--------------------


input_frame = tk.LabelFrame(root, text=" Settings ", padx=10, pady=10)
input_frame.pack(fill="x", padx=10, pady=5)


# Google Maps URL to lat and lot
tk.Label(input_frame, text="Google Maps URL:").grid(row=0, column=0)
entry_google_maps = tk.Entry(input_frame, width=40)
entry_google_maps.insert(0, saved_data.get("Map_url",""))
entry_google_maps.grid(row=0, column=1, padx=10, pady=5, sticky="ew")


tk.Label(input_frame, text="API Token:").grid(row=1, column=0, pady=5)
entry_token = tk.Entry(input_frame, width=80)
entry_token.insert(0, saved_data.get("token", ""))         # Load saved or use default
entry_token.grid(row=1, column=1, columnspan=4, padx=5)

Daily_hourly = tk.StringVar()
Daily_hourly.set(saved_data.get("mode","daily"))           # Load saved or use default
tk.Radiobutton(input_frame,text="Daily",variable=Daily_hourly,value="daily").grid(row=0,column=3)
tk.Radiobutton(input_frame,text="Hourly",variable=Daily_hourly,value="hourly").grid(row=0,column=4)


#--------------------Buttons--------------------


btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

refresh_btn = tk.Button(btn_frame, text="Get Forecast", command=load_weather_data, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
refresh_btn.grid(row=0, column=0, padx=5)

readme_btn = tk.Button(input_frame, text="How to get API key",command=show_How_to_get_API_key, bg="#f0f0f0", font=("Arial", 8))
readme_btn.grid(row=1, column=5)


#--------------------Table--------------------


columns = ('Time', 'Condition', 'Rainfall(mm)', 'Humidity(%)', 'Temperature(°C)', 'Wind Speed(m/s)')
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=140, anchor="center")
tree.pack(expand=True, fill='both', padx=10, pady=10)

root.mainloop()