import streamlit as st
import datetime
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import cartopy.crs as ccrs

# API key from Streamlit secrets
openweather_api = st.secrets["openweather"]["api_key"]

# API endpoints
geo_name_url = "http://api.openweathermap.org/geo/1.0/direct"
weather_url = "https://api.openweathermap.org/data/3.0/onecall/day_summary"

# --- Functions ---
def get_place():
    place = st.text_input("Enter city and country or US state (e.g., 'Paris, France')").strip()
    if place:
        params = {"q": place, "limit": 1, "appid": openweather_api}
        response = requests.get(geo_name_url, params=params)
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return place, lat, lon
    return None, None, None

def get_date():
    date_str = st.text_input("Enter date in YYYY-MM-DD format")
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj
    except ValueError:
        return None

def get_weather_data(lat, lon, date_obj):
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

def get_seven_day_weather(lat, lon, start_date, openweather_api):
    def fetch_weather_for_date_range(base_date):
        weather_data_list = []
        for i in range(7):
            current_date = base_date + datetime.timedelta(days=i)
            weather_data = get_weather_data(lat, lon, current_date)
            weather_data_list.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'data': weather_data
            })
        return weather_data_list

    current_year_data = fetch_weather_for_date_range(start_date)
    one_year_ago = start_date.replace(year=start_date.year - 1)
    ten_years_ago = start_date.replace(year=start_date.year - 10)
    eighty_date = start_date.replace(year=1981)

    one_year_ago_data = fetch_weather_for_date_range(one_year_ago)
    ten_years_ago_data = fetch_weather_for_date_range(ten_years_ago)
    eighty_data = fetch_weather_for_date_range(eighty_date)
    return current_year_data, one_year_ago_data, ten_years_ago_data, eighty_data

def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9/5 + 32

def extract_max_temps_with_dates(weather_list):
    dates = []
    temps = []
    for entry in weather_list:
        if entry.get("data") and entry["data"].get("temperature") and entry["data"]["temperature"].get("max") is not None:
            dates.append(datetime.datetime.strptime(entry["date"], "%Y-%m-%d"))
            temps.append(kelvin_to_fahrenheit(entry["data"]["temperature"]["max"]))
    return dates, temps

# --- Streamlit UI ---
place, lat, lon = get_place()
start_date = get_date()

if place and lat and lon and start_date:
    current, one_year, ten_years, eighty = get_seven_day_weather(lat, lon, start_date, openweather_api)

    # Extract dates and temperatures
    dates, current_f = extract_max_temps_with_dates(current)
    _, one_year_f = extract_max_temps_with_dates(one_year)
    _, ten_years_f = extract_max_temps_with_dates(ten_years)
    _, eighty_f = extract_max_temps_with_dates(eighty)

    # Plot temperatures
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
    ax.set_title(f'7-Day Max Temp Comparison for {place}', fontsize=16, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.xticks(rotation=45)
    ax.legend(title='Year')
    sns.despine()
    ax.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(fig)

    # Map
    fig_map = plt.figure(figsize=(10, 8))
    ax_map = fig_map.add_subplot(1, 1, 1, projection=ccrs.Orthographic(lon, lat))
    ax_map.set_global()
    ax_map.stock_img()
    ax_map.coastlines()
    ax_map.plot(lon, lat, 'o', color='red', transform=ccrs.PlateCarree())
    plt.title("Your selected location", fontsize=16, fontweight='bold')
    st.pyplot(fig_map)
