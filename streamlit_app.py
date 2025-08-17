# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import requests
import json
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


# Variables

# API key
openweather_api = st.secrets["openweather"]["api_key"]
# API endpoints
geo_name_url = "http://api.openweathermap.org/geo/1.0/direct"
weather_url = "https://api.openweathermap.org/data/3.0/onecall/day_summary"
# Initialize some global variables
lat = None
lon = None
date_obj = None

# Functions

# Given a place name (e.g., "Paris, France"), query the OpenWeather Geocoding API
# to get its latitude and longitude. Returns (lat, lon) if found, otherwise (None, None).

def get_place():
    global lat, lon
    global place
    place = input("Enter the city and country or US state you want weather for, separated by a comma \n"
              "examples: 'Paris, France' or 'Peoria, Illinois' ").strip()
    params = {
        "q": place,
        "limit": 1,
        "appid": openweather_api
    }
    response = requests.get(geo_name_url, params=params)
    data = response.json()
    if data:
        lat = float(data[0]['lat'])
        lon = float(data[0]['lon'])
        return lat, lon
    else:
        return None, None

def get_date():

    global date_obj

    try:
        date_str = input("Enter the date in YYYY-MM-DD format: ")
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        print("Valid date:", date_obj.date())
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")

    return date_obj.date()

def get_weather_data(lat, lon, date_obj, openweather_api):
    """
    Retrieves weather data from the OpenWeatherMap API.
    Args:
        lat (float): Latitude
        lon (float): Longitude
        date_obj (date, optional): Date object (default: today's date)
        openweather_api (str): OpenWeatherMap API key
    Returns:
        dict: Weather data if successful, None otherwise
    """
    # Use today's date if not provided
    if date_obj is None:
        date_obj = datetime.date.today()
    # Set API parameters
    params = {
        'lat': lat,
        'lon': lon,
        'date': date_obj.strftime('%Y-%m-%d'),
        'appid': openweather_api
    }
    response = requests.get(weather_url, params=params)
    # Check for successful response
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_seven_day_weather(lat, lon, start_date, openweather_api):
    """
    Fetches weather data for the next seven days starting from start_date,
    from 1 year ago, and from 10 years ago.
    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        start_date (datetime.date): Starting date.
        openweather_api (str): OpenWeatherMap API key.
    Returns:
        tuple: Three lists of weather data dictionaries for each day:
               (current_year_data, one_year_ago_data, ten_years_ago_data)
    """

    def fetch_weather_for_date_range(base_date):
        weather_data_list = []
        for i in range(7):
            current_date = base_date + datetime.timedelta(days=i)
            weather_data = get_weather_data(lat, lon, current_date, openweather_api)
            weather_data_list.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'data': weather_data
            })
        return weather_data_list
    current_year_data = fetch_weather_for_date_range(start_date)
    # Handle potential ValueError for leap year dates
    try:
        one_year_ago_date = start_date.replace(year=start_date.year - 1)
    except ValueError:
        # For Feb 29 on non-leap year, fallback to Feb 28
        one_year_ago_date = start_date.replace(year=start_date.year - 1, day=28)
    try:
        ten_years_ago_date = start_date.replace(year=start_date.year - 10)
    except ValueError:
        # For Feb 29 on non-leap year, fallback to Feb 28
        ten_years_ago_date = start_date.replace(year=start_date.year - 10, day=28)
    try:
        eighty_date = start_date.replace(year=1981)
    except ValueError:
        # For Feb 29 on non-leap year, fallback to Feb 28
        eighty_date = start_date.replace(year=start_date.year - 10, day=28)

    one_year_ago_data = fetch_weather_for_date_range(one_year_ago_date)
    ten_years_ago_data = fetch_weather_for_date_range(ten_years_ago_date)
    eighty_date_data = fetch_weather_for_date_range(eighty_date)
    return current_year_data, one_year_ago_data, ten_years_ago_data, eighty_date_data

def kelvin_to_fahrenheit(kelvin):

  """Converts Kelvin to Fahrenheit."""
  return (kelvin - 273.15) * 9/5 + 32

get_place()

get_date()

print(date_obj)

weather_list, weather_list_year_ago, weather_list_ten_years, weather_list_eighty_dates = get_seven_day_weather(lat, lon, date_obj, openweather_api)

weather_list_eighty_dates

weather_list

print(weather_list)



# weather_list_date_temp = [(entry['date'], entry['data']['temperature']['max']) for entry in weather_list if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None]
# weather_list_year_ago_date_temp = [(entry['date'], entry['data']['temperature']['max']) for entry in weather_list_year_ago if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None]
# weather_list_ten_years_date_temp = [(entry['date'], entry['data']['temperature']['max']) for entry in weather_list_ten_years if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None]

weather_list_dates = [entry['date'] for entry in weather_list if 'date' in entry]

weather_list_max_temps = [
    entry['data']['temperature']['max']
    for entry in weather_list
    if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None
]

weather_list_year_ago_max_temps = [
    entry['data']['temperature']['max']
    for entry in weather_list_year_ago
    if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None
]

weather_list_ten_years_max_temps = [
    entry['data']['temperature']['max']
    for entry in weather_list_ten_years
    if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None
]

weather_year_eighty_date_max_temps = [
    entry['data']['temperature']['max']
    for entry in weather_list_eighty_dates
    if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None
]

current_year_fahrenheit = [kelvin_to_fahrenheit(temp) for temp in weather_list_max_temps]
one_year_ago_fahrenheit = [kelvin_to_fahrenheit(temp) for temp in weather_list_year_ago_max_temps]
ten_years_ago_fahrenheit = [kelvin_to_fahrenheit(temp) for temp in weather_list_ten_years_max_temps]
eighty_date_fahrenheit = [kelvin_to_fahrenheit(temp) for temp in weather_year_eighty_date_max_temps]

current_year_fahrenheit

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

weather_list_dates_dt = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in weather_list_dates]
year = weather_list_dates_dt[0].year
sns.set_style('whitegrid')
sns.set_context('talk')
palette = sns.color_palette(['#D94835', '#FFA500', '#1E3A8A', '#40E0D0'])
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_facecolor('#d9e6f2')  # light grayish blue background for plot area
sns.lineplot(x=weather_list_dates_dt, y=current_year_fahrenheit, marker='o', linewidth=2, label=f'{year}', color=palette[0], ax=ax)
sns.lineplot(x=weather_list_dates_dt, y=one_year_ago_fahrenheit, marker='o', linewidth=2, label=f'{year-1}', color=palette[1], ax=ax)
sns.lineplot(x=weather_list_dates_dt, y=ten_years_ago_fahrenheit, marker='o', linewidth=2, label=f'{year-10}', color=palette[2], ax=ax)
sns.lineplot(x=weather_list_dates_dt, y=eighty_date_fahrenheit, marker='o', linewidth=2, label='1981', color=palette[3], ax=ax)
ax.set_xlabel('Date', fontsize=14, fontweight='bold')
ax.set_ylabel('Maximum Temperature (°F)', fontsize=14, fontweight='bold')
ax.set_title(f'7-Day Maximum Temperature Comparison for {place}', fontsize=16, fontweight='bold')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
plt.xticks(rotation=45)
ax.legend(title='Year')
sns.despine()
ax.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# Sample data
latitude = lat
longitude = lon

fig = plt.figure(figsize=(10, 8))

# center map on selected coordinates
ax = fig.add_subplot(1, 1, 1, projection=ccrs.Orthographic(longitude, latitude))
ax.set_global() # This is a good practice to ensure the entire globe is considered for the plot
ax.stock_img() # Add background image of Earth
ax.coastlines() # Add coastlines

ax.plot(longitude, latitude, 'o', color='red', transform=ccrs.PlateCarree()) # Plot the point

# Add a title for clarity
plt.title("Your selection location", fontsize=16, fontweight='bold')

# Show the plot
plt.show()
