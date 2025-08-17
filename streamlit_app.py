# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import cartopy.crs as ccrs

# --- Streamlit App ---

st.set_page_config(page_title="Past Weather Viewer", layout="wide")
st.title("Past Weather Comparison Viewer")

# --- User Inputs ---
place = st.text_input(
    "Enter the city and country or US state (e.g., 'Paris, France' or 'Peoria, Illinois'):"
)

start_date = st.date_input(
    "Select a starting date:",
    value=datetime.date.today(),
    min_value=datetime.date(1900, 1, 1),
    max_value=datetime.date.today()
)

# API key from Streamlit secrets
openweather_api = st.secrets["openweather"]["api_key"]

geo_name_url = "http://api.openweathermap.org/geo/1.0/direct"
weather_url = "https://api.openweathermap.org/data/3.0/onecall/day_summary"

# --- Functions ---

def get_coordinates(place_name):
    params = {"q": place_name, "limit": 1, "appid": openweather_api}
    response = requests.get(geo_name_url, params=params)
    data = response.json()
    if data:
        return float(data[0]['lat']), float(data[0]['lon'])
    return None, None

def get_weather_data(lat, lon, date_obj):
    params = {
        "lat": lat,
        "lon": lon,
        "date": date_obj.strftime('%Y-%m-%d'),
        "appid": openweather_api
    }
    response = requests.get(weather_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_seven_day_weather(lat, lon, start_date):
    def fetch_weather_for_date_range(base_date):
        weather_data_list = []
        for i in range(7):
            current_date = base_date + datetime.timedelta(days=i)
            weather_data = get_weather_data(lat, lon, current_date)
            weather_data_list.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "data": weather_data
            })
        return weather_data_list

    # current year
    current_year_data = fetch_weather_for_date_range(start_date)

    # 1 year ago
    try:
        one_year_ago_date = start_date.replace(year=start_date.year - 1)
    except ValueError:
        one_year_ago_date = start_date.replace(year=start_date.year - 1, day=28)
    one_year_ago_data = fetch_weather_for_date_range(one_year_ago_date)

    # 10 years ago
    try:
        ten_years_ago_date = start_date.replace(year=start_date.year - 10)
    except ValueError:
        ten_years_ago_date = start_date.replace(year=start_date.year - 10, day=28)
    ten_years_ago_data = fetch_weather_for_date_range(ten_years_ago_date)

    # 1981
    try:
        eighty_date = start_date.replace(year=1981)
    except ValueError:
        eighty_date = start_date.replace(year=1981, day=28)
    eighty_date_data = fetch_weather_for_date_range(eighty_date)

    return current_year_data, one_year_ago_data, ten_years_ago_data, eighty_date_data

def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9/5 + 32

# --- Main App Logic ---
if st.button("Get Weather"):

    if not place:
        st.warning("Please enter a place to continue.")
    else:
        lat, lon = get_coordinates(place)
        if lat is None:
            st.error("Could not find the specified location. Please check your input.")
        else:
            st.success(f"Coordinates found: Latitude {lat}, Longitude {lon}")

            current, one_year, ten_years, eighty = get_seven_day_weather(lat, lon, start_date)

            # Extract max temperatures
            def extract_max_temps(weather_list):
                return [
                    entry['data']['temperature']['max']
                    for entry in weather_list
                    if entry.get('data') and entry['data'].get('temperature') and entry['data']['temperature'].get('max') is not None
                ]

            current_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(current)]
            one_year_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(one_year)]
            ten_years_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(ten_years)]
            eighty_f = [kelvin_to_fahrenheit(t) for t in extract_max_temps(eighty)]

            dates = [datetime.datetime.strptime(entry['date'], "%Y-%m-%d") for entry in current]

            # --- Plot line chart ---
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
            ax.set_ylabel('Max Temperature (°F)', fontsize=14, fontweight='bold')
            ax.set_title(f'7-Day Max Temperature Comparison for {place}', fontsize=16, fontweight='bold')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            plt.xticks(rotation=45)
            ax.legend(title='Year')
            sns.despine()
            ax.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            st.pyplot(fig)

            # --- Plot globe map ---
            fig2 = plt.figure(figsize=(10, 8))
            ax2 = fig2.add_subplot(1, 1, 1, projection=ccrs.Orthographic(lon, lat))
            ax2.set_global()
            ax2.stock_img()
            ax2.coastlines()
            ax2.plot(lon, lat, 'o', color='red', transform=ccrs.PlateCarree())
            plt.title("Selected Location", fontsize=16, fontweight='bold')
            st.pyplot(fig2)
