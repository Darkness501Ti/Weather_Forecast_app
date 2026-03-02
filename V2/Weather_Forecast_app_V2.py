"""""



''''''''''''''''''''''''''''''''how user experience''''''''''''''''''''''''''''''''
open program -> setup or load -> get Forecast -> see the table data -> clos program
get struggling? 
1. how to get api key?
2. how to get lat and lon?
3.error? and etc.


''''''''''''''''''''''''''''''''Main program logic''''''''''''''''''''''''''''''''
Main
open program -> load setting.json Function or 'set lat & lon' and 'set API KEY' and select'daily or hourly mode' -> get Forecast data and -> data to table -> close the program

Background Process
save setting.json Function (Save 'multiple lat&lon', 'daily or hourly mode', 'API KEY' )


Optional
save or set lat & lon : multiple lat&lon load or set lat & lon -> multiple lat&lon save
daily or hourly mode
how to get API  
how to get lat&lon 
Debug and log 



'''''''''''''''''''''''''''''Progression  '*' for Note'''''''''''''''''''''''''''''
Logic (yes is done, no is not done)

First priority
##setting config
load setting.json Function                                          no
save setting.json Function                                          no
daily or hourly mode                                                no *
set lat & lon                                                       no
set API KEY                                                         no


##data logic
set lat & lon                                                       no
set API KEY                                                         no
get Forecast data                                                   yes                   
data to table                                                       no **
multiple lat&lon                                                    no ***
multiple lat&lon load                                               no ***
multiple lat&lon save                                               no ***

##UI
set API KEY (input_box)                                             no 
set lat & lon (input_box)                                           no
load lat & lon (optionmenu)                                         no
get Forecast Function (button)                                      no
show data to Table (Table)                                          no
multiple lat&lon      (optionmenu)                                  no ***
multiple lat&lon save (button)                                      no ***



Second priority
## logic
how to get API                                                      yes
how to get lat&lon                                                  no
save and load Function                                              no


##UI
how to get API (button)                                             no
how to get lat&lon (button)                                         no
save and load Function (button)                                     no

Third priority
##Logic
Debug and log                                                       no

##UI
Debug and log (button) to (New Window Table)                        no


-----------------Note for Function Detail
*
select daily or hourly
    max daily  is duration is 10
    max hourly  is duration is 48

**
show Table
    make data form 'load data Function' to 'show Table'

***
multiple lat&lon save unlimited locations




"""""

import requests
import pandas as pd
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
import re
import logging
from datetime import datetime
import base64
import hashlib
from cryptography.fernet import Fernet
import threading
import msvcrt  # Windows file locking
from logging.handlers import RotatingFileHandler

CONFIG_FILE = "settings.json"
LOG_FILE = "weather_app.log"
ENCRYPTION_KEY_FILE = ".encryption_key"
MAX_LOG_SIZE = 1024 * 1024  # 1MB
BACKUP_COUNT = 3
REQUEST_TIMEOUT = 10  # seconds


class FileLock:
    """Context manager for file locking (Windows compatible)"""
    def __init__(self, file_path, mode='r'):
        self.file_path = file_path
        self.mode = mode
        self.file = None
        self.lock_file = None
    
    def __enter__(self):
        # Create lock file path
        self.lock_file = self.file_path + '.lock'
        
        # Wait for lock to be available (Windows compatible)
        max_wait = 30  # Maximum wait time in seconds
        wait_time = 0
        while wait_time < max_wait:
            try:
                # Try to create lock file exclusively
                self.lock_file_handle = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except OSError:
                # Lock file exists, wait and retry
                import time
                time.sleep(0.1)
                wait_time += 0.1
        
        if wait_time >= max_wait:
            raise TimeoutError("Could not acquire file lock")
        
        # Open the actual file
        self.file = open(self.file_path, self.mode)
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        # Close and remove lock file
        try:
            os.close(self.lock_file_handle)
            os.unlink(self.lock_file)
        except:
            pass


def get_or_create_encryption_key():
    """Get or create encryption key for API keys"""
    if os.path.exists(ENCRYPTION_KEY_FILE):
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_FILE, 'wb') as f:
            f.write(key)
        return key


def encrypt_api_key(api_key):
    """Encrypt API key"""
    if not api_key:
        return ""
    key = get_or_create_encryption_key()
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key):
    """Decrypt API key"""
    if not encrypted_key:
        return ""
    try:
        key = get_or_create_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception:
        return ""  # Return empty if decryption fails


def validate_coordinates(lat_str, lon_str):
    """Validate and convert coordinate strings"""
    try:
        lat = float(lat_str)
        lon = float(lon_str)
        
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
            
        return lat, lon
    except ValueError as e:
        raise ValueError(f"Invalid coordinates: {e}")


def get_weather_condition_map():
    """Get weather condition mapping"""
    return {
        1: "Clear", 2: "Partly cloudy", 3: "Cloudy", 4: "Overcast", 5: "Light rain", 
        6: "Moderate rain", 7: "Heavy rain", 8: "Thunderstorm", 9: "Very cold", 
        10: "Cold", 11: "Cool", 12: "Very hot"
    }


def make_api_request(url, headers=None, params=None):
    """Make API request with consistent timeout and error handling"""
    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise requests.RequestException("Request timed out. Please check your internet connection.")
    except requests.exceptions.ConnectionError:
        raise requests.RequestException("Network connection error. Please check your internet.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise requests.RequestException("Invalid API token. Please check your API key.")
        elif e.response.status_code == 403:
            raise requests.RequestException("API access forbidden. Please check your permissions.")
        elif e.response.status_code == 429:
            raise requests.RequestException("API rate limit exceeded. Please try again later.")
        else:
            raise requests.RequestException(f"HTTP {e.response.status_code}: {e.response.reason}")
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Request failed: {str(e)}")



def extract_lat_lon_from_google_maps(url: str):
    """
    Extract latitude and longitude from a Google Maps URL.

    Supports formats like:
    - https://maps.google.com/?q=12.710220,102.052307
    - https://www.google.com/maps/place/.../@12.710220,102.052307,15z
    - https://www.google.com/maps/search/?api=1&query=12.710220,102.052307

    Returns:
        (lat, lon) as floats
    Raises:
        ValueError if coordinates not found
    """

    if not url:
        raise ValueError("Empty URL")

    # Expand short URL if needed (maps.app.goo.gl etc.)
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        final_url = response.url
    except requests.exceptions.RequestException as e:
        log_debug(f"Failed to expand URL: {e}")
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
    # This handles URLs like: https://www.google.com/maps/search/12.711099,+102.073581
    match = re.search(r'/[-]?(\d+\.\d+),([-+]?\d+\.\d+)(?:\?|$|[^-\d])', final_url)
    if match:
        lat = float(match.group(1))
        lon_str = match.group(2).replace('+', '')
        lon = float(lon_str)
        return lat, lon

    raise ValueError("Latitude/Longitude not found in URL")
    
    



def setup_logging():
    """Configure logging with rotation for debug mode (optional)"""
    settings = load_settings()
    debug_mode = settings.get("debug_mode", False)
    
    if not debug_mode:
        return  # Skip logging setup if debug mode is disabled
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create rotating file handler
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log_debug(message):
    """Log debug message to file (optional)"""
    settings = load_settings()
    debug_mode = settings.get("debug_mode", False)
    
    if debug_mode:
        try:
            logging.info(message)
            print(f"LOG: {message}")
        except:
            pass

def load_settings():
    """Load settings from JSON file with file locking and API key decryption"""
    if os.path.exists(CONFIG_FILE):
        try:
            with FileLock(CONFIG_FILE, 'r') as f:
                settings = json.load(f)
                
            # Migrate old settings format to new format
            if "locations" in settings and "saved_slots" in settings["locations"]:
                old_slots = settings["locations"]["saved_slots"]
                saved_locations = []
                for slot in old_slots:
                    if slot.get("name") and slot.get("lat") != 0 and slot.get("lon") != 0:
                        saved_locations.append({
                            "name": slot["name"],
                            "lat": slot["lat"],
                            "lon": slot["lon"],
                            "url": slot.get("url", "")
                        })
                
                # Update to new format
                settings["locations"] = {"saved_locations": saved_locations}
                save_settings(settings)
                log_debug("Migrated settings from old format to new format")
            
            # Decrypt API key if it's encrypted
            if "api_key" in settings and settings["api_key"]:
                settings["api_key"] = decrypt_api_key(settings["api_key"])
                
            return settings
            
        except (json.JSONDecodeError, IOError, TimeoutError) as e:
            log_debug(f"Error loading settings: {e}")
            messagebox.showerror("Settings Error", f"Failed to load settings: {e}")
        except TimeoutError as e:
            log_debug(f"Timeout loading settings: {e}")
            messagebox.showerror("Settings Error", "Settings file is locked by another process. Please try again.")
        
    return {
        "api_key": "",
        "mode": "daily",
        "debug_mode": False,
        "locations": {
            "saved_locations": []
        },
        "current_lat": "",
        "current_lon": ""
    }

def save_settings(settings):
    """Save settings to JSON file with file locking and API key encryption"""
    try:
        # Create a copy of settings to avoid modifying the original
        settings_copy = settings.copy()
        
        # Encrypt API key before saving
        if "api_key" in settings_copy and settings_copy["api_key"]:
            settings_copy["api_key"] = encrypt_api_key(settings_copy["api_key"])
        
        with FileLock(CONFIG_FILE, 'w') as f:
            json.dump(settings_copy, f, indent=2)
        log_debug("Settings saved successfully")
        
    except (IOError, TimeoutError) as e:
        log_debug(f"Error saving settings: {e}")
        messagebox.showerror("Settings Error", f"Failed to save settings: {e}")
    except Exception as e:
        log_debug(f"Unexpected error saving settings: {e}")
        messagebox.showerror("Settings Error", f"Unexpected error: {e}")


def save_location(name, lat, lon, url=""):
    """Save location to the list with validation"""
    try:
        # Validate coordinates
        lat_float, lon_float = validate_coordinates(str(lat), str(lon))
        
        settings = load_settings()
        new_location = {
            "name": name,
            "lat": lat_float,
            "lon": lon_float,
            "url": url
        }
        settings["locations"]["saved_locations"].append(new_location)
        save_settings(settings)
        log_debug(f"Saved location '{name}'")
        return True
        
    except ValueError as e:
        log_debug(f"Invalid coordinates for location '{name}': {e}")
        messagebox.showerror("Invalid Coordinates", str(e))
        return False
    except Exception as e:
        log_debug(f"Error saving location '{name}': {e}")
        messagebox.showerror("Error", f"Failed to save location: {e}")
        return False

def load_location_by_name(name):
    """Load location by name"""
    settings = load_settings()
    for location in settings["locations"]["saved_locations"]:
        if location["name"] == name:
            settings["current_lat"] = str(location["lat"])
            settings["current_lon"] = str(location["lon"])
            save_settings(settings)
            log_debug(f"Loaded location '{location['name']}'")
            return location
    return None

def get_saved_locations():
    """Get list of saved locations for dropdown"""
    settings = load_settings()
    locations = []
    for location in settings["locations"]["saved_locations"]:
        if location["name"] and location["lat"] != 0 and location["lon"] != 0:
            locations.append((location["name"], location["name"]))
    locations.append(("Custom", "Custom"))
    return locations

def delete_location_by_name(name):
    """Delete location by name"""
    settings = load_settings()
    saved_locations = settings["locations"]["saved_locations"]
    for i, location in enumerate(saved_locations):
        if location["name"] == name:
            del saved_locations[i]
            save_settings(settings)
            log_debug(f"Deleted location '{name}'")
            return True
    return False

def lat_and_lon():
    '''Get current lat/lon from settings'''
    settings = load_settings()
    return settings.get("current_lat", ""), settings.get("current_lon", "")

def process_weather_data(forecast_list, is_hourly=False):
    """Process weather forecast data into DataFrame with common formatting"""
    try:
        condition_map = get_weather_condition_map()
        
        # Json to pandas
        df = pd.json_normalize(forecast_list)
        df.columns = [c.replace('data.', '') for c in df.columns]
        df['time'] = pd.to_datetime(df['time'])
        df['cond'] = df['cond'].map(condition_map)
        
        if is_hourly:
            df = df.rename(columns={
                'time': 'Time',
                'cond': 'Condition',
                'rain': 'Rainfall(mm)',
                'rh': 'Humidity(%)',
                'ws10m': 'Wind Speed(m/s)',
                'tc': 'Temperature(°C)'
            })
        else:
            df['Temperature(°C)'] = df['tc_min'].astype(str) + " / " + df['tc_max'].astype(str) + " max"
            df = df.rename(columns={
                'time': 'Time',
                'cond': 'Condition',
                'rain': 'Rainfall(mm)',
                'rh': 'Humidity(%)',
                'ws10m': 'Wind Speed(m/s)'
            })
        
        # Ensure consistent column order
        df = df[['Time', 'Condition', 'Rainfall(mm)', 'Humidity(%)', 'Temperature(°C)', 'Wind Speed(m/s)']]
        
        return df
        
    except Exception as e:
        log_debug(f"Error processing weather data: {e}")
        raise ValueError(f"Failed to process weather data: {e}")


def display_weather_data(df, is_hourly=False):
    """Display weather data in the treeview"""
    try:
        # Clear existing data
        for i in tree.get_children():
            tree.delete(i)
        
        # Format time based on data type
        for index, row in df.iterrows():
            if is_hourly:
                formatted_time = row['Time'].strftime('%d-%m-%Y %H:%M')
            else:
                formatted_time = row['Time'].strftime('%d-%m-%Y')
            
            tree.insert("", "end", values=(
                formatted_time, row['Condition'], row['Rainfall(mm)'], 
                row['Humidity(%)'], row['Temperature(°C)'], row['Wind Speed(m/s)']
            ))
            
    except Exception as e:
        log_debug(f"Error displaying weather data: {e}")
        messagebox.showerror("Display Error", f"Failed to display weather data: {e}")


def load_Daily_weather_data():
    """Load daily weather forecast data"""
    settings = load_settings()
    target_lat = settings.get("current_lat", "")
    target_lon = settings.get("current_lon", "")
    user_token = settings.get("api_key", "")

    # Check if user has input
    if not target_lat or not target_lon or not user_token:
        messagebox.showwarning("Missing Info", "Please enter latitude, longitude, and API Token!")
        return

    try:
        # Validate coordinates
        validate_coordinates(target_lat, target_lon)
    except ValueError as e:
        messagebox.showerror("Invalid Coordinates", str(e))
        return

    log_debug(f"Loading daily weather for lat: {target_lat}, lon: {target_lon}")
    
    # API Document "https://data.tmd.go.th/nwpapi/doc/"
    url = "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily/at"
    querystring = {"lat": target_lat, "lon": target_lon, "duration": "10", "fields": "cond,ws10m,tc_max,tc_min,rh,rain"}
    headers = {'accept': "application/json", 'authorization': f"Bearer {user_token.strip()}"}

    try:
        # Get data using consistent API request function
        data = make_api_request(url, headers=headers, params=querystring)
        forecast_list = data['WeatherForecasts'][0]['forecasts']
        
        log_debug(f"Successfully retrieved {len(forecast_list)} daily forecasts")

        # Process and display data
        df = process_weather_data(forecast_list, is_hourly=False)
        display_weather_data(df, is_hourly=False)
        log_debug("Daily weather data displayed successfully")

    except requests.RequestException as e:
        log_debug(f"Failed to get daily weather data: {e}")
        messagebox.showerror("API Error", str(e))
    except ValueError as e:
        log_debug(f"Data processing error: {e}")
        messagebox.showerror("Data Error", str(e))
    except Exception as e:
        log_debug(f"Unexpected error loading daily weather: {e}")
        messagebox.showerror("Error", f"Failed to get daily weather data: {e}")


def load_Hourly_weather_data():
    """Load hourly weather forecast data"""
    settings = load_settings()
    target_lat = settings.get("current_lat", "")
    target_lon = settings.get("current_lon", "")
    user_token = settings.get("api_key", "")

    # Check if user has input
    if not target_lat or not target_lon or not user_token:
        messagebox.showwarning("Missing Info", "Please enter latitude, longitude, and API Token!")
        return

    try:
        # Validate coordinates
        validate_coordinates(target_lat, target_lon)
    except ValueError as e:
        messagebox.showerror("Invalid Coordinates", str(e))
        return
    
    log_debug(f"Loading hourly weather for lat: {target_lat}, lon: {target_lon}")
    
    # API Document "https://data.tmd.go.th/nwpapi/doc/"
    url = "https://data.tmd.go.th/nwpapi/v1/forecast/location/hourly/at"
    querystring = {"lat": target_lat, "lon": target_lon, "duration": "48", "fields": "cond,ws10m,tc,rh,rain"}
    headers = {'accept': "application/json", 'authorization': f"Bearer {user_token.strip()}"}

    try:
        # Get data using consistent API request function
        data = make_api_request(url, headers=headers, params=querystring)
        forecast_list = data['WeatherForecasts'][0]['forecasts']
        
        log_debug(f"Successfully retrieved {len(forecast_list)} hourly forecasts")

        # Process and display data
        df = process_weather_data(forecast_list, is_hourly=True)
        display_weather_data(df, is_hourly=True)
        log_debug("Hourly weather data displayed successfully")

    except requests.RequestException as e:
        log_debug(f"Failed to get hourly weather data: {e}")
        messagebox.showerror("API Error", str(e))
    except ValueError as e:
        log_debug(f"Data processing error: {e}")
        messagebox.showerror("Data Error", str(e))
    except Exception as e:
        log_debug(f"Unexpected error loading hourly weather: {e}")
        messagebox.showerror("Error", f"Failed to get hourly weather data: {e}")

def daily_or_hourly():
    """Handle daily or hourly selection"""
    # Extract coordinates from Google Maps URL if provided (optional)
    url = google_maps_url_var.get().strip()
    if url:
        if not extract_from_google_maps():
            return  # Stop if URL extraction failed
    else:
        # If no URL, check if coordinates are manually entered
        lat = lat_var.get().strip()
        lon = lon_var.get().strip()
        if not lat or not lon:
            messagebox.showwarning("Missing Info", "Please enter coordinates or provide a Google Maps URL")
            return
        
        # Validate manually entered coordinates
        try:
            validate_coordinates(lat, lon)
        except ValueError as e:
            messagebox.showerror("Invalid Coordinates", str(e))
            return
    
    settings = load_settings()
    mode = daily_hourly_var.get()
    settings["mode"] = mode
    settings["api_key"] = api_key_var.get()  # Save API key when getting forecast
    settings["current_lat"] = lat_var.get()
    settings["current_lon"] = lon_var.get()
    save_settings(settings)
    log_debug("API key and settings saved before getting forecast")
    
    if mode == "daily":
        load_Daily_weather_data()
    else:
        load_Hourly_weather_data()




def show_How_to_get_API_key():
    """Show API key instructions"""
    How_to_get_API_key = """
ไปที่ยัง https://data.tmd.go.th/nwpapi/ และทำการ เข้าสู่ระบบ หรือ สร้างบัญชีใหม่
หลังจากเข้าสู่ระบบแล้วกดที่ปุ่ม "Create New Token" จากนั้นชื่อและนำ Token มากรอกใส่ช่อง API Key
!!!คำเตือนTokenจะโชวให้เห็นแค่ครั้งเดียว
    """
    messagebox.showinfo("How to get API key", How_to_get_API_key)

def update_coordinate_status():
    """Update coordinate status indicator"""
    try:
        lat = lat_var.get().strip()
        lon = lon_var.get().strip()
        url = google_maps_url_var.get().strip()
        
        if lat and lon:
            try:
                validate_coordinates(lat, lon)
                if url:
                    coord_status_label.config(text="✓ From URL", fg="blue")
                else:
                    coord_status_label.config(text="✓ Manual entry", fg="green")
            except ValueError:
                coord_status_label.config(text="⚠ Invalid", fg="red")
        else:
            coord_status_label.config(text="Enter coordinates", fg="gray")
    except:
        coord_status_label.config(text="Ready", fg="green")


def extract_from_google_maps():
    """Extract coordinates from Google Maps URL"""
    url = google_maps_url_var.get().strip()
    if not url:
        update_coordinate_status()
        return True  # No URL provided is OK
    
    try:
        lat, lon = extract_lat_lon_from_google_maps(url)
        lat_var.set(str(lat))
        lon_var.set(str(lon))
        
        # Update settings
        settings = load_settings()
        settings["current_lat"] = str(lat)
        settings["current_lon"] = str(lon)
        save_settings(settings)
        
        log_debug(f"Extracted coordinates from URL: lat={lat}, lon={lon}")
        update_coordinate_status()
        return True
        
    except ValueError as e:
        log_debug(f"Failed to extract coordinates: {e}")
        messagebox.showerror("Error", f"Failed to extract coordinates: {e}")
        update_coordinate_status()
        return False
    except Exception as e:
        log_debug(f"Unexpected error extracting coordinates: {e}")
        messagebox.showerror("Error", f"Unexpected error extracting coordinates: {e}")
        update_coordinate_status()
        return False

def save_current_location():
    """Save current location to the list"""
    name = location_name_var.get().strip()
    lat = lat_var.get().strip()
    lon = lon_var.get().strip()
    url = google_maps_url_var.get().strip()
    
    if not name:
        messagebox.showwarning("Warning", "Please enter a location name")
        return
    
    if not lat or not lon:
        # Try to extract from URL first
        if url and extract_from_google_maps():
            lat = lat_var.get().strip()
            lon = lon_var.get().strip()
        
    if not lat or not lon:
        messagebox.showwarning("Warning", "Please enter valid coordinates")
        return
    
    # Check if location name already exists
    settings = load_settings()
    for location in settings["locations"]["saved_locations"]:
        if location["name"] == name:
            messagebox.showwarning("Warning", f"Location '{name}' already exists")
            return
    
    if save_location(name, lat, lon, url):
        update_location_dropdown()
        messagebox.showinfo("Success", f"Location '{name}' saved successfully")
        location_name_var.set("")  # Clear the name field

def on_location_selected(event):
    """Handle location selection from dropdown"""
    selected = location_dropdown_var.get()
    if selected == "Custom":
        update_coordinate_status()
        return
    
    location = load_location_by_name(selected)
    if location:
        lat_var.set(str(location["lat"]))
        lon_var.set(str(location["lon"]))
        google_maps_url_var.set(location["url"])
        log_debug(f"Loaded location: {location['name']}")
        update_coordinate_status()

def delete_current_location():
    """Delete currently selected location"""
    selected = location_dropdown_var.get()
    if selected == "Custom":
        messagebox.showwarning("Warning", "Please select a saved location to delete")
        return
    
    if delete_location_by_name(selected):
        messagebox.showinfo("Success", f"Location '{selected}' deleted")
        update_location_dropdown()
        location_dropdown_var.set("Custom")

def update_location_dropdown():
    """Update the location dropdown with saved locations"""
    locations = get_saved_locations()
    location_dropdown_var.set("Custom")
    location_dropdown['values'] = [display_text for display_text, slot_name in locations]


def toggle_debug_mode():
    """Handle debug mode toggle"""
    settings = load_settings()
    settings["debug_mode"] = debug_mode_var.get()
    save_settings(settings)
    
    if debug_mode_var.get():
        setup_logging()  # Enable logging
        messagebox.showinfo("Debug Mode", "Debug mode enabled. Logs will be saved to 'weather_app.log'")
    else:
        # Disable logging by clearing handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        messagebox.showinfo("Debug Mode", "Debug mode disabled. Logging stopped.")

def show_log_viewer():
    settings = load_settings()
    debug_mode = settings.get("debug_mode", False)
    
    if not debug_mode:
        messagebox.showinfo("Debug Mode", "Debug mode is disabled. Enable it in settings to view logs.")
        return
    
    log_window = tk.Toplevel(root)
    log_window.title("Debug Logs")
    log_window.geometry("800x400")
    
    text_widget = tk.Text(log_window, wrap=tk.WORD)
    scrollbar = ttk.Scrollbar(log_window, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Load log file content
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                text_widget.insert("1.0", content)
        except IOError as e:
            text_widget.insert("1.0", f"Error reading log file: {e}")
        except UnicodeDecodeError as e:
            text_widget.insert("1.0", f"Error decoding log file: {e}")
        except Exception as e:
            text_widget.insert("1.0", f"Unexpected error reading log file: {e}")
    else:
        text_widget.insert("1.0", "No log file found.")
    
    text_widget.config(state="disabled")


#--------------------User Interface--------------------
root = tk.Tk()
root.title("Weather Forecast App V2")
root.geometry("1200x700")

# Setup logging
setup_logging()

#--------------------Load existing settings--------------------
saved_data = load_settings()

#--------------------Variable Definitions--------------------
lat_var = tk.StringVar(value=saved_data.get("current_lat", ""))
lon_var = tk.StringVar(value=saved_data.get("current_lon", ""))
api_key_var = tk.StringVar(value=saved_data.get("api_key", ""))
google_maps_url_var = tk.StringVar(value="")
location_name_var = tk.StringVar(value="")
daily_hourly_var = tk.StringVar(value=saved_data.get("mode", "daily"))
location_dropdown_var = tk.StringVar(value="Custom")
debug_mode_var = tk.BooleanVar(value=saved_data.get("debug_mode", False))

#--------------------Settings Frame--------------------
settings_frame = tk.LabelFrame(root, text=" Settings ", padx=15, pady=15)
settings_frame.pack(fill="x", padx=15, pady=10)

# Location selection dropdown
tk.Label(settings_frame, text="Saved Locations:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=(0,5))
location_dropdown = ttk.Combobox(settings_frame, textvariable=location_dropdown_var, width=25, state="readonly", font=("Arial", 9))
location_dropdown.grid(row=0, column=1, padx=10, pady=(0,5))
location_dropdown.bind("<<ComboboxSelected>>", on_location_selected)

# Google Maps URL (manual extract)
tk.Label(settings_frame, text="Google Maps URL (Optional):", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
entry_google_maps = tk.Entry(settings_frame, textvariable=google_maps_url_var, width=50, font=("Arial", 9))
entry_google_maps.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky="ew")

# Add a hint label below the URL entry
url_hint_label = tk.Label(settings_frame, text="Optional: Enter coordinates manually below or paste Google Maps URL", 
                         font=("Arial", 8), fg="gray")
url_hint_label.grid(row=2, column=1, columnspan=3, padx=10, pady=(0,5), sticky="w")

# Manual coordinate entry
tk.Label(settings_frame, text="Manual Coordinates:", font=("Arial", 10)).grid(row=3, column=0, sticky="w", pady=5)
coord_frame = tk.Frame(settings_frame)
coord_frame.grid(row=3, column=1, columnspan=3, padx=10, pady=5, sticky="ew")

tk.Label(coord_frame, text="Latitude:").pack(side="left", padx=(0,5))
entry_lat = tk.Entry(coord_frame, textvariable=lat_var, width=15, font=("Arial", 9))
entry_lat.pack(side="left", padx=5)

tk.Label(coord_frame, text="Longitude:").pack(side="left", padx=(10,5))
entry_lon = tk.Entry(coord_frame, textvariable=lon_var, width=15, font=("Arial", 9))
entry_lon.pack(side="left", padx=5)

# Bind coordinate changes to status update
lat_var.trace('w', lambda *args: update_coordinate_status())
lon_var.trace('w', lambda *args: update_coordinate_status())
google_maps_url_var.trace('w', lambda *args: update_coordinate_status())

# Coordinate status indicator
coord_status_label = tk.Label(settings_frame, text="Ready", font=("Arial", 8), fg="green")
coord_status_label.grid(row=3, column=4, padx=10, pady=5)

# Location name and save/remove buttons
tk.Label(settings_frame, text="Location Name:", font=("Arial", 10)).grid(row=4, column=0, sticky="w", pady=5)
entry_location_name = tk.Entry(settings_frame, textvariable=location_name_var, width=25, font=("Arial", 9))
entry_location_name.grid(row=4, column=1, padx=10, pady=5)
save_location_btn = tk.Button(settings_frame, text="Save Location", command=save_current_location, bg="#FF9800", fg="white", font=("Arial", 9, "bold"))
save_location_btn.grid(row=4, column=2, padx=5, pady=5)
remove_location_btn = tk.Button(settings_frame, text="Remove", command=delete_current_location, bg="#f44336", fg="white", font=("Arial", 9, "bold"))
remove_location_btn.grid(row=0, column=2, padx=5, pady=(0,5))

# API Key with help button
tk.Label(settings_frame, text="API Token:", font=("Arial", 10)).grid(row=5, column=0, sticky="w", pady=5)
entry_api_key = tk.Entry(settings_frame, textvariable=api_key_var, width=50, show="*", font=("Arial", 9))
entry_api_key.grid(row=5, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
api_help_btn = tk.Button(settings_frame, text="How to get API key", command=show_How_to_get_API_key, bg="#f0f0f0", font=("Arial", 8))
api_help_btn.grid(row=5, column=3, padx=5, pady=5)

# Debug mode and log viewer
debug_frame = tk.Frame(settings_frame)
debug_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

debug_checkbox = tk.Checkbutton(debug_frame, text="Enable Debug Mode", variable=debug_mode_var, command=toggle_debug_mode, font=("Arial", 9))
debug_checkbox.pack(side="left", padx=(0,10))

log_viewer_btn = tk.Button(debug_frame, text="View Logs", command=show_log_viewer, bg="#E0E0E0", font=("Arial", 8))
log_viewer_btn.pack(side="left")

#--------------------Buttons Frame--------------------
buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=10)

get_forecast_btn = tk.Button(buttons_frame, text="Get Forecast", command=daily_or_hourly, bg="#2196F3", fg="white", font=("Arial", 12, "bold"), width=15)
get_forecast_btn.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

# Daily/Hourly selection
tk.Radiobutton(buttons_frame, text="Daily", variable=daily_hourly_var, value="daily").grid(row=1, column=0, pady=5, padx=10)
tk.Radiobutton(buttons_frame, text="Hourly", variable=daily_hourly_var, value="hourly").grid(row=1, column=1, pady=5, padx=10)

#--------------------Table--------------------
table_frame = tk.Frame(root, relief=tk.SUNKEN, borderwidth=1)
table_frame.pack(expand=True, fill='both', padx=15, pady=10)

columns = ('Time', 'Condition', 'Rainfall(mm)', 'Humidity(%)', 'Temperature(°C)', 'Wind Speed(m/s)')
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

# Configure columns with better styling
for col in columns:
    tree.heading(col, text=col, anchor="center")
    tree.column(col, width=140, anchor="center", minwidth=100)

# Style the treeview
style = ttk.Style()
style.configure("Treeview", font=("Arial", 10), rowheight=25)
style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#f0f0f0")

# Add scrollbar
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

tree.pack(side="left", fill='both', expand=True)
scrollbar.pack(side="right", fill='y')

#--------------------Status Bar--------------------
status_bar = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

#--------------------Update UI with saved data--------------------
update_location_dropdown()
update_coordinate_status()  # Initialize coordinate status

# Save settings on close
def on_closing():
    settings = load_settings()
    settings["current_lat"] = lat_var.get()
    settings["current_lon"] = lon_var.get()
    settings["api_key"] = api_key_var.get()
    settings["mode"] = daily_hourly_var.get()
    settings["debug_mode"] = debug_mode_var.get()
    save_settings(settings)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the GUI
root.mainloop()


