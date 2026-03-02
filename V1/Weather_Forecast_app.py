import requests
import pandas as pd
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk


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
    settings = {
        "lat": entry_lat.get(),
        "lon": entry_lon.get(),
        "token": entry_token.get(),
        "mode": Daily_hourly.get()
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f)

def daily_or_hourly():
    # Automatically save settings every time the user clicks "Get Forecast"
    save_current_settings()
    
    if  Daily_hourly.get() == "daily":
        load_Daily_weather_data()
    else:
        load_Hourly_weather_data()

def load_Daily_weather_data():
    target_lat = entry_lat.get()
    target_lon = entry_lon.get()
    user_token = entry_token.get()

    #Check if user have input
    if not target_lat or not target_lon or not user_token:
        messagebox.showwarning("Missing Info", "Please enter latitude, longitude, and API Token!")
        return

    # API Document "https://data.tmd.go.th/nwpapi/doc/"
    url = "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily/at"
    querystring = {"lat": target_lat, "lon": target_lon, "duration": "10", "fields": "cond,ws10m,tc_max,tc_min,rh,rain"}
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
        df['Temperature(°C)'] = df['tc_min'].astype(str) + " / " + df['tc_max'].astype(str) + " max"
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
            formatted_time = row['Time'].strftime('%d-%m-%Y')
            tree.insert("", "end", values=(formatted_time, row['Condition'], row['Rainfall(mm)'], 
                                           row['Humidity(%)'], row['Temperature(°C)'], row['Wind Speed(m/s)']))
            

    except Exception as e:
        messagebox.showerror("Error", f"Failed to get data: {e}")   

def load_Hourly_weather_data():
    target_lat = entry_lat.get()
    target_lon = entry_lon.get()
    user_token = entry_token.get()

    #Check if user have input
    if not target_lat or not target_lon or not user_token:
        messagebox.showwarning("Missing Info", "Please enter latitude, longitude, and API Token!")
        return
    
    # API Document "https://data.tmd.go.th/nwpapi/doc/"
    url = "https://data.tmd.go.th/nwpapi/v1/forecast/location/hourly/at"
    querystring = {"lat": target_lat, "lon": target_lon, "duration": "48", "fields": "cond,ws10m,tc,rh,rain"}
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
        df['time'] = pd.to_datetime(df['time'])
        df['cond'] = df['cond'].map(condition_map)
        df = df.rename(columns={
            'time': 'Time',
            'cond': 'Condition',
            'rain': 'Rainfall(mm)',
            'rh': 'Humidity(%)',
            'ws10m': 'Wind Speed(m/s)'
        })
        df.columns = ['Time', 'Condition', 'Rainfall(mm)', 'Humidity(%)', 'Temperature(°C)', 'Wind Speed(m/s)']
        
        
        for i in tree.get_children(): tree.delete(i)
        for index, row in df.iterrows():
            formatted_time = row['Time'].strftime('%d-%m-%Y %H:%M')
            tree.insert("", "end", values=(formatted_time, row['Condition'], row['Rainfall(mm)'], 
                                           row['Humidity(%)'], row['Temperature(°C)'], row['Wind Speed(m/s)']))
            

        

    except Exception as e:
        messagebox.showerror("Error", f"Failed to get data: {e}")

def show_How_to_get_API_key():
    How_to_get_API_key = """
    Go to https://data.tmd.go.th/nwpapi/doc/
    and follow Introduction
    """
    messagebox.showinfo("How to get API key", How_to_get_API_key)

#--------------------User Interface--------------------
root = tk.Tk()
root.title("Weather Forecast App   ( MAX 10 Days /  48 Hours )")
root.geometry("950x600")

#--------------------Load existing settings--------------------
saved_data = load_saved_settings()

#--------------------Setting Farme--------------------
input_frame = tk.LabelFrame(root, text=" Settings ", padx=10, pady=10)
input_frame.pack(fill="x", padx=10, pady=5)

tk.Label(input_frame, text="latitude:").grid(row=0, column=0)
entry_lat = tk.Entry(input_frame, width=15)
entry_lat.insert(0, saved_data.get("lat", ""))             # Load saved or use default
entry_lat.grid(row=0, column=1, padx=5)

tk.Label(input_frame, text="longitude:").grid(row=0, column=2)
entry_lon = tk.Entry(input_frame, width=15)
entry_lon.insert(0, saved_data.get("lon", ""))             # Load saved or use default
entry_lon.grid(row=0, column=3, padx=5)

tk.Label(input_frame, text="API Token:").grid(row=1, column=0, pady=5)
entry_token = tk.Entry(input_frame, width=80)
entry_token.insert(0, saved_data.get("token", ""))         # Load saved or use default
entry_token.grid(row=1, column=1, columnspan=4, padx=5)

Daily_hourly = tk.StringVar()
Daily_hourly.set(saved_data.get("mode","daily"))           # Load saved or use default
tk.Radiobutton(input_frame,text="Daily",variable=Daily_hourly,value="daily").grid(row=0,column=4)
tk.Radiobutton(input_frame,text="Hourly",variable=Daily_hourly,value="hourly").grid(row=0,column=5)

#--------------------Buttons--------------------
btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

refresh_btn = tk.Button(btn_frame, text="Get Forecast", command=daily_or_hourly, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
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