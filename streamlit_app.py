# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import cartopy.crs as ccrs

# API key
openweather_api = st.secrets["openweather"]["api_key"]
# API endpoints
geo_name_url = "http://api.openweathermap.org/geo/1.0/direct"
weather_url = "https://api.openweathermap.org/data/3.0/onecall/day_summary"

# Initialize global variables
lat = None
lon = None
place = None
date_obj = None

# Functions

def get_place():
    """
    Prompts the user to enter a place in 'City, Country' or 'City, State' format.
    Validates input and retries until a valid place is entered and found via OpenWeather API.
    Returns:
        tuple: (lat, lon)
    """
    global lat, lon, place
    while True:
        place = st.text_input(
            "Enter the city and country or US state (City, Country or City, State):",
            value="Paris, France"
        )
        if not place or ',' not in place:
            st.warning("Please enter the place in 'City, Country' or 'City, State' format.")
            return None, None
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
            st.warning("Place not found. Please try again.")
            return None, None

def get_date():
    """
    Prompts the user to select a date using Streamlit date input widget.
    Returns:
        datetime.date
    """
    date_obj = st.date_input("Select the starting date:", datetime.date.today())
    return date_obj

def get_weather_data(lat, lon, date_obj, openweather_api):
    if date_obj is None:
        date_obj = datetime.date.today()
    params = {
        'lat': lat,
        'lon': lon,
        'date': date_obj.strftime('%Y-%m-%d'),
        'appid': openweather_api
    }
    response = requests.get(weather_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching weather: {response.status_code}")
        return None

def get_seven_day_weather(lat, lon, start_date):
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
    try:
        one_year_ago_date = start_date.replace(year=start_date.year - 1)
    except ValueError:
        one_year_ago_date = start_date.replace(year=start_date.year - 1, day=28)
    try:
        ten_years_ago_date = start_date.replace(year=start_date.year - 10)
    except ValueError:
        ten_years_ago_date = start_date.replace(year=start_date.year - 10, day=28)
    try:
        eighty_date = start_date.replace(year=1981)
    except ValueError:
        eighty_date = start_date.replace(year=1981, day=28)

    one_year_ago_data = fetch_weather_for_date_range(one_year_ago_date)
    ten_years_ago_data = fetch_weather_for_date_range(ten_years_ago_date)
    eighty_date_data = fetch_weather_for_date_range(eighty_date)

    return current_year_data, one_year_ago_data, ten_years_ago_data, eighty_date_data

def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9/5 + 32

def extract_max_temps(weather_list):
    return [
        entry['data']['temperature']['max']
        for entry in weather_list
        if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None
    ]

# Main app

st.title("Past Weather Viewer")

lat, lon = get_place()
if lat is None or lon is None:
    st.stop()

start_date = get_date()

current, one_year, ten_years, eighty = get_seven_day_weather(lat, lon, start_date)

# Extract and convert temperatures
current_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(current)]
one_year_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(one_year)]
ten_years_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(ten_years)]
eighty_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(eighty)]

dates = [datetime.datetime.strptime(entry['date'], "%Y-%m-%d") for entry in current]

# Plot 7-day temperatures
sns.set_style('whitegrid')
sns.set_context('talk')
palette = sns.color_palette(['#D94835', '#FFA500', '#1E3A8A', '#40E0D0'])
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_facecolor('#d9e6f2')

sns.lineplot(x=dates, y=current_f, marker='o', linewidth=2, label=f'{dates[0].year}', color=palette[0], ax=ax)
sns.lineplot(x=dates, y=one_year_f, marker='o', linewidth=2, label=f'{dates[0].year-1}', color=palette[1], ax=ax)
sns.lineplot(x=dates, y=ten_years_f, marker='o', linewidth=2, label=f'{dates[0].year-10}', color=palette[2], ax=ax)
sns.lineplot(x=dates, y=eighty_f, marker='o', linewidth=2, label='1981', color=palette[3], ax=ax)

ax.set_xlabel('Date', fontsize=14, fontweight='bold')
ax.set_ylabel('Maximum Temperature (°F)', fontsize=14, fontweight='bold')
ax.set_title(f'7-Day Maximum Temperature Comparison for {place}', fontsize=16, fontweight='bold')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
plt.xticks(rotation=45)
ax.legend(title='Year')
sns.despine()
ax.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
st.pyplot(fig)

# Plot globe with Cartopy
fig_map = plt.figure(figsize=(10, 8))
ax_map = fig_map.add_subplot(1, 1, 1, projection=ccrs.Orthographic(lon, lat))
ax_map.set_global()
ax_map.coastlines()
ax_map.plot(lon, lat, 'o', color='red', transform=ccrs.PlateCarree())
plt.title("Selected Location", fontsize=16, fontweight='bold')
st.pyplot(fig_map)
