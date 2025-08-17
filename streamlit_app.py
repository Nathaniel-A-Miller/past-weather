# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import cartopy.crs as ccrs

# --- Streamlit Secrets ---
openweather_api = st.secrets["openweather"]["api_key"]

# --- API Endpoints ---
geo_name_url = "http://api.openweathermap.org/geo/1.0/direct"
weather_url = "https://api.openweathermap.org/data/3.0/onecall/day_summary"

# --- Functions ---

def get_place():
    """Prompt user for place and get lat/lon using OpenWeather Geocoding API."""
    place = st.text_input(
        "Enter city and country or US state (e.g., 'Paris, France' or 'Peoria, Illinois')"
    ).strip()
    if place:
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
            return place, lat, lon
    return None, None, None

def get_weather_data(lat, lon, date_obj):
    """Retrieve weather data from OpenWeather API for a single day."""
    params = {
        'lat': lat,
        'lon': lon,
        'date': date_obj.strftime('%Y-%m-%d'),
        'appid': openweather_api
    }
    response = requests.get(weather_url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def get_seven_day_weather(lat, lon, start_date):
    """Get 7-day weather for current year, 1 year ago, 10 years ago, and 1981."""
    def fetch_weather_for_range(base_date):
        weather_list = []
        for i in range(7):
            current_date = base_date + datetime.timedelta(days=i)
            weather_data = get_weather_data(lat, lon, current_date)
            weather_list.append({'date': current_date, 'data': weather_data})
        return weather_list

    current = fetch_weather_for_range(start_date)

    def safe_replace_year(date_obj, new_year):
        try:
            return date_obj.replace(year=new_year)
        except ValueError:  # handle Feb 29
            return date_obj.replace(year=new_year, day=28)

    one_year_ago = fetch_weather_for_range(safe_replace_year(start_date, start_date.year - 1))
    ten_years = fetch_weather_for_range(safe_replace_year(start_date, start_date.year - 10))
    eighty = fetch_weather_for_range(safe_replace_year(start_date, 1981))

    return current, one_year_ago, ten_years, eighty

def extract_max_temps_with_dates(weather_list):
    """Extract dates and max temperatures from weather API response."""
    dates = []
    temps = []
    for entry in weather_list:
        if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None:
            dates.append(entry['date'])
            temps.append(entry['data']['temperature']['max'])
    return dates, temps

def kelvin_to_fahrenheit(kelvin):
    """Convert Kelvin to Fahrenheit."""
    return (kelvin - 273.15) * 9/5 + 32

# --- Streamlit App ---

st.title("Past 7-Day Weather Comparison")

# Get place
place, lat, lon = get_place()

# Date picker widget
start_date = st.date_input("Select the starting date for your 7-day weather comparison")

# Only proceed if inputs are valid
if place and lat and lon and start_date:
    current, one_year, ten_years, eighty = get_seven_day_weather(lat, lon, start_date)

    # Extract max temps
    dates, current_max = extract_max_temps_with_dates(current)
    _, one_year_max = extract_max_temps_with_dates(one_year)
    _, ten_years_max = extract_max_temps_with_dates(ten_years)
    _, eighty_max = extract_max_temps_with_dates(eighty)

    # Convert to Fahrenheit
    current_f = [kelvin_to_fahrenheit(t) for t in current_max]
    one_year_f = [kelvin_to_fahrenheit(t) for t in one_year_max]
    ten_years_f = [kelvin_to_fahrenheit(t) for t in ten_years_max]
    eighty_f = [kelvin_to_fahrenheit(t) for t in eighty_max]

    # --- Plot temperatures ---
    dates_dt = [d if isinstance(d, datetime.date) else datetime.datetime.strptime(d, "%Y-%m-%d") for d in dates]
    year = dates_dt[0].year if dates_dt else start_date.year

    sns.set_style('whitegrid')
    sns.set_context('talk')
    palette = sns.color_palette(['#D94835', '#FFA500', '#1E3A8A', '#40E0D0'])
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_facecolor('#d9e6f2')

    sns.lineplot(x=dates_dt, y=current_f, marker='o', linewidth=2, label=f'{year}', color=palette[0], ax=ax)
    sns.lineplot(x=dates_dt, y=one_year_f, marker='o', linewidth=2, label=f'{year-1}', color=palette[1], ax=ax)
    sns.lineplot(x=dates_dt, y=ten_years_f, marker='o', linewidth=2, label=f'{year-10}', color=palette[2], ax=ax)
    sns.lineplot(x=dates_dt, y=eighty_f, marker='o', linewidth=2, label='1981', color=palette[3], ax=ax)

    ax.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax.set_ylabel('Max Temperature (°F)', fontsize=14, fontweight='bold')
    ax.set_title(f'7-Day Max Temp Comparison for {place}', fontsize=16, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.xticks(rotation=45)
    ax.legend(title='Year')
    sns.despine()
    ax.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(fig)

    # --- Map visualization ---
    fig_map = plt.figure(figsize=(10, 8))
    ax_map = fig_map.add_subplot(1, 1, 1, projection=ccrs.Orthographic(lon, lat))
    ax_map.set_global()
    ax_map.stock_img()
    ax_map.coastlines()
    ax_map.plot(lon, lat, 'o', color='red', transform=ccrs.PlateCarree())
    plt.title("Selected Location", fontsize=16, fontweight='bold')
    st.pyplot(fig_map)
