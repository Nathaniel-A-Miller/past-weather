# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import seaborn as sns
import io

# --- Variables ---
openweather_api = st.secrets["openweather"]["api_key"]
geo_name_url = "http://api.openweathermap.org/geo/1.0/direct"
weather_url = "https://api.openweathermap.org/data/3.0/onecall/day_summary"

# --- Functions ---
def get_place_input():
    """Prompt the user for a place, return (lat, lon, place) or None if invalid/not ready."""
    place = st.text_input(
        "Enter city and country (format 'Paris, France', 'Peoria, Illinois' OR 'Paris, FR', 'Peoria, US-IL')"
    ).strip()

    if not place:
        return None

    # Try to normalize input
    parts = [p.strip() for p in place.split(",")]
    if len(parts) == 2 and len(parts[1]) > 2:
        # Convert country names to codes if possible
        country_lookup = {
            "france": "FR", "united states": "US", "usa": "US", "canada": "CA",
            "spain": "ES", "germany": "DE", "italy": "IT"
        }
        country = country_lookup.get(parts[1].lower(), parts[1])
        place = f"{parts[0]},{country}"

    params = {"q": place, "limit": 1, "appid": openweather_api}
    response = requests.get(geo_name_url, params=params)
    data = response.json()
    if data:
        return float(data[0]['lat']), float(data[0]['lon']), place
    else:
        st.warning("Place not found. Please enter a valid city and country/state.")
        return None

def get_date_input():
    """Prompt user for a date using a calendar widget."""
    date_obj = st.date_input(
        "Select a starting date for weather data (dates after today are forecast)",
        min_value=datetime.date(1979, 1, 1),   # earliest selectable date
        max_value=datetime.date.today()        # latest selectable date
    )
    return date_obj

def get_weather_data(lat, lon, date_obj):
    """Retrieve weather data from OpenWeatherMap API."""
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
        st.error(f"Error fetching weather data: {response.status_code}")
        return None


def get_seven_day_weather(lat, lon, start_date):
    """Fetch 7-day weather data for current year, 1 year ago, 10 years ago, and 1979."""
    def fetch_weather_for_date_range(base_date):
        weather_data_list = []
        for i in range(7):
            current_date = base_date + datetime.timedelta(days=i)
            data = get_weather_data(lat, lon, current_date)
            weather_data_list.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'data': data
            })
        return weather_data_list

    def safe_replace_year(d, year):
        try:
            return d.replace(year=year)
        except ValueError:
            return d.replace(year=year, day=28)

    current_year = fetch_weather_for_date_range(start_date)
    one_year_ago = fetch_weather_for_date_range(safe_replace_year(start_date, start_date.year - 1))
    ten_years_ago = fetch_weather_for_date_range(safe_replace_year(start_date, start_date.year - 10))
    eighty_year = fetch_weather_for_date_range(safe_replace_year(start_date, 1979))

    return current_year, one_year_ago, ten_years_ago, eighty_year


def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9/5 + 32


def extract_max_temps(weather_list):
    return [
        entry['data']['temperature']['max']
        for entry in weather_list
        if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None
    ]


# --- Main App Execution ---
st.title("Past Weather Comparison App 🌦️")

st.write("""
This app lets you compare maximum temperatures for a selected location 
over a 7-day period across different years, including the current year, 
one year ago, ten years ago, and 1979. The app works by calling the API of
OpenWeather, a weather data provider (their data begins in 1979).

Enter an input below to get started!
""")

# Inputs
place_data = get_place_input()
start_date = get_date_input()

# Only run when both inputs exist AND button is pressed
if place_data and start_date and st.button("Get Weather Data"):
    lat, lon, place = place_data

    # Fetch data
    current, one_year, ten_years, eighty = get_seven_day_weather(lat, lon, start_date)

    # Extract temperatures
    current_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(current)]
    one_year_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(one_year)]
    ten_years_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(ten_years)]
    eighty_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(eighty)]

    dates = [datetime.datetime.strptime(d['date'], "%Y-%m-%d") for d in current]

    # --- Globe Map ---
    fig_map = plt.figure(figsize=(6, 5))
    ax_map = fig_map.add_subplot(1, 1, 1, projection=ccrs.Orthographic(lon, lat))
    ax_map.stock_img()
    ax_map.coastlines(resolution='110m', linewidth=0.8)
    ax_map.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax_map.plot(lon, lat, 'o', color='red', markersize=8, transform=ccrs.PlateCarree())
    plt.title(f"Selected Location: {place}", fontsize=16, fontweight='bold')
    buf = io.BytesIO()
    fig_map.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    st.image(buf, width=350)
    plt.close(fig_map)

    # --- Temperature Plot ---
    sns.set_style('whitegrid')
    sns.set_context('talk')
    palette = sns.color_palette(['#D94835', '#FFA500', '#1E3A8A', '#40E0D0'])

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_facecolor('#d9e6f2')
    sns.lineplot(x=dates, y=current_f, marker='o', linewidth=2, label=f'{dates[0].year}', color=palette[0], ax=ax)
    sns.lineplot(x=dates, y=one_year_f, marker='o', linewidth=2, label=f'{dates[0].year-1}', color=palette[1], ax=ax)
    sns.lineplot(x=dates, y=ten_years_f, marker='o', linewidth=2, label=f'{dates[0].year-10}', color=palette[2], ax=ax)
    sns.lineplot(x=dates, y=eighty_f, marker='o', linewidth=2, label='1979', color=palette[3], ax=ax)
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
