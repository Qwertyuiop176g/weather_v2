import requests
from datetime import datetime, timedelta
from functools import lru_cache
import pytz

@lru_cache(maxsize=None)
def get_coordinates(location, api_key):
    """Fetch latitude and longitude for a given location using OpenCage API."""
    geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={api_key}"
    response = requests.get(geocode_url)
    data = response.json()

    if data['results']:
        coords = data['results'][0]['geometry']
        return coords['lat'], coords['lng']
    else:
        raise ValueError("Location not found!")

@lru_cache(maxsize=None)
def get_weather_data(latitude, longitude, timezone):
    """Fetch weather data from Open-Meteo API including precipitation probability."""
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation_probability&timezone={timezone}"
    response = requests.get(weather_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        return None
    
@lru_cache(maxsize=None)
def get_air_quality(lat, long, aqi=True):
    weather_url = (f"http://api.weatherapi.com/v1/forecast.json"
                   f"?key=e69f473e6b6841989ca121211240607"  # Replace with your actual WeatherAPI key
                   f"&q={lat},{long}"
                   f"&days=1"  # Fetching forecast for 1 day
                   f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,air_quality"  # Ensure air_quality is included
                   f"{'&aqi=yes' if aqi else '&aqi=no'}")
    
    response = requests.get(weather_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        print(f"Response content: {response.text}")  # Print error details
        return None
    
def get_aqi_description(index):
    """Return a description for the given US EPA index."""
    descriptions = {
        1: "Good",
        2: "Moderate",
        3: "Unhealthy for Sensitive Groups",
        4: "Unhealthy",
        5: "Very Unhealthy",
        6: "Hazardous"
    }
    return descriptions.get(index, "Unknown")

def print_air_quality(data):
        # Air Quality Data
        data = data['current']
        aqi = data['air_quality']
        print("\nAir Quality:")
        print(f"Carbon Monoxide (CO): {aqi.get('co', 'N/A')} μg/m3")
        print(f"Ozone (O3): {aqi.get('o3', 'N/A')} μg/m3")
        print(f"Nitrogen Dioxide (NO2): {aqi.get('no2', 'N/A')} μg/m3")
        print(f"Sulphur Dioxide (SO2): {aqi.get('so2', 'N/A')} μg/m3")
        print(f"PM2.5: {aqi.get('pm2_5', 'N/A')} μg/m3")
        print(f"PM10: {aqi.get('pm10', 'N/A')} μg/m3")
        us_epa_index = aqi.get('us-epa-index', 'N/A')
        print(f"US EPA Index: {us_epa_index} ({get_aqi_description(int(us_epa_index))})")

def display_weather_data(weather_data):
    """Display weather data including probability of rain."""
    if not weather_data:
        return
    
    # Get current time from the computer
    current_time = datetime.now()
    
    # Display current weather
    current_weather = weather_data.get('current_weather', {})
    if current_weather:
        print("\nCurrent Weather:")
        print(f"Temperature: {current_weather['temperature']}°C")
        print(f"Wind Speed: {current_weather['windspeed']} km/h")
    else:
        print("Current weather data not available.")
    
    # Prepare and display hourly forecast data
    hourly_times = weather_data['hourly']['time']
    hourly_temps = weather_data['hourly']['temperature_2m']
    hourly_humidity = weather_data['hourly']['relative_humidity_2m']
    hourly_wind = weather_data['hourly']['wind_speed_10m']
    hourly_precip_prob = weather_data['hourly']['precipitation_probability']

    print("\nHourly Forecast (next 24 hours):")
    print("Hour | Temperature (°C) | Relative Humidity (%) | Wind Speed (km/h) | Precipitation Probability (%)")

    umbrella_hours = []

    for i in range(len(hourly_times)):
        hour_time = datetime.fromisoformat(hourly_times[i].replace('Z', '+00:00'))
        # Only show data from the current hour onwards
        if hour_time < current_time:
            continue
        if hour_time > current_time + timedelta(hours=24):
            break
        hour_label = hour_time.strftime("%H:%M")
        temp = hourly_temps[i]
        humidity = hourly_humidity[i]
        wind_speed = hourly_wind[i]
        precip_prob = hourly_precip_prob[i]
        print(f"{hour_label:>4} | {temp:>16} | {humidity:>21} | {wind_speed:>11} | {precip_prob:>29}")
        
        if precip_prob > 60:
            umbrella_hours.append(hour_label)
    
    if umbrella_hours:
        print("\nBring an umbrella during these hours due to high chance of precipitation:")
        for hour in umbrella_hours:
            print(f"- {hour}")

def get_php_timezone(location):
    # Standardize the input location
    location_standardized = location.replace(' ', '_').title()

    # Check for matching timezone using the location name
    for timezone in pytz.all_timezones:
        if location_standardized in timezone.split('/'):
            return timezone

    # Check for matching timezone using country code
    for country_code in pytz.country_timezones:
        country_name = pytz.country_names[country_code].replace(' ', '_').title()
        if location_standardized == country_name:
            return pytz.country_timezones[country_code][0]

    return None

def main(location: str|None):
    if not location:
        location = input("Enter the location: ").strip()
    opencage_api_key = "b2f23b4d6a6246f29ea8c59b6ec2e7b6"  # Replace with your OpenCage API key
    include_air_quality = input("Do you want to include air quality data? (yes/no): ").strip().lower() == 'yes'
    try:
        t1 = datetime.now()
        latitude, longitude = get_coordinates(location, opencage_api_key)
        print(f"Coordinates for {location}: Latitude {latitude}, Longitude {longitude}")
        
        if include_air_quality:
            air_quality = get_air_quality(latitude, longitude)

        phptz = get_php_timezone(location)
        if not phptz:
            return print("Location does not exist / is not supported. Please try again with another real location")

        weather_data = get_weather_data(latitude, longitude, phptz)
        if weather_data:
            print_air_quality(air_quality)

        if weather_data:
            display_weather_data(weather_data)

        t2 = datetime.now()
        delta = t2-t1
        print(f"Code took {delta}s to run | DEBUG: {location}")
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print(e.with_traceback())

def debug_loop():
    main("Singapore")
    main("New York")
    main("Singapore")

if __name__ == "__main__":
    main(location=None)
