import requests
from datetime import datetime, timedelta
from functools import lru_cache
import pytz

@lru_cache(maxsize=None)
def Cordinates(location, api_key):
    opencageapi = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={api_key}"
    response = requests.get(opencageapi)
    data = response.json()

    if data['results']:
        coords = data['results'][0]['geometry']
        return coords['lat'], coords['lng']
    else:
        raise ValueError("Location not found!")

@lru_cache(maxsize=None)
def weatherdata(latitude, longitude, timezone):
    openmetroapi = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation_probability&timezone={timezone}"
    response = requests.get(openmetroapi)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        return None
    
@lru_cache(maxsize=None)
def getairquality(lat, long, aqi=True):
    Weatherapi = (f"http://api.weatherapi.com/v1/forecast.json"
                   f"?key="  
                   f"&q={lat},{long}"
                   f"&days=1"  
                   f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,air_quality"
                   f"{'&aqi=yes' if aqi else '&aqi=no'}")
    
    response = requests.get(Weatherapi)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None
    
def aqidescription(index):
    descriptions = {
        1: "Good",
        2: "Moderate",
        3: "Unhealthy for Sensitive Groups",
        4: "Unhealthy",
        5: "Very Unhealthy",
        6: "Hazardous"
    }
    return descriptions.get(index, "Unknown")

def showairquality(data):
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
        print(f"US EPA Index: {us_epa_index} ({aqidescription(int(us_epa_index))})")

def displayweatherdata(weather_data):
    if not weather_data:
        return
    
    currenttime = datetime.now()
    
    currentweather = weather_data.get('current_weather', {})
    if currentweather:
        print("\nCurrent Weather:")
        print(f"Temperature: {currentweather['temperature']}°C")
        print(f"Wind Speed: {currentweather['windspeed']} km/h")
    else:
        print("Current weather data not available.")
    
    hourlytime = weather_data['hourly']['time']
    hourlytemp = weather_data['hourly']['temperature_2m']
    hourlyhumidity = weather_data['hourly']['relative_humidity_2m']
    hourly_wind = weather_data['hourly']['wind_speed_10m']
    hourly_rainchance = weather_data['hourly']['precipitation_probability']

    print("\nHourly Forecast (next 24 hours):")
    print("Hour | Temperature (°C) | Relative Humidity (%) | Wind Speed (km/h) | Precipitation Probability (%)")

    umbrella_hours = []

    for i in range(len(hourlytime)):
        hour_time = datetime.fromisoformat(hourlytime[i].replace('Z', '+00:00'))
        
        if hour_time < currenttime:
            continue
        if hour_time > currenttime + timedelta(hours=24):
            break
        hour_label = hour_time.strftime("%H:%M")
        temp = hourlytemp[i]
        humidity = hourlyhumidity[i]
        wind_speed = hourly_wind[i]
        rainchance = hourly_rainchance[i]
        print(f"{hour_label:>4} | {temp:>16} | {humidity:>21} | {wind_speed:>11} | {rainchance:>29}")
        
        if rainchance > 60:
            umbrella_hours.append(hour_label)
    
    if umbrella_hours:
        print("\nBring an umbrella during these hours:")
        for hour in umbrella_hours:
            print(f"- {hour}")

def get_php_timezone(location):
    location_standardized = location.replace(' ', '_').title()
    for timezone in pytz.all_timezones:
        if location_standardized in timezone.split('/'):
            return timezone
    for country_code in pytz.country_timezones:
        country_name = pytz.country_names[country_code].replace(' ', '_').title()
        if location_standardized == country_name:
            return pytz.country_timezones[country_code][0]

    return None

def main(location: str|None):
    if not location:
        location = input("Enter the location: ").strip()
    opencage_api_key = ""
    include_air_quality = input("Do you want to include air quality data? (yes/no): ").strip().lower() == 'yes'
    try:
        t1 = datetime.now()
        latitude, longitude = Cordinates(location, opencage_api_key)
        print(f"Coordinates for {location}: Latitude {latitude}, Longitude {longitude}")
        
        if include_air_quality:
            air_quality = getairquality(latitude, longitude)

        phptz = get_php_timezone(location)
        if not phptz:
            return print("Location does not exist / is not supported. Please try again with another real location")

        weather_data = weatherdata(latitude, longitude, phptz)
        if weather_data:
            showairquality(air_quality)

        if weather_data:
            displayweatherdata(weather_data)

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

