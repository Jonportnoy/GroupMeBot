from groupy.client import Client
from groupy.api.bots import *
from datetime import datetime, timezone
from creds import *
import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry
client = Client.from_token(token)
group = client.groups.get(nu_chi)
bot = client.bots.list()[1].manager


# Set up the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 36,
	"longitude": -79,
	"daily": ["temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset", "uv_index_max", "rain_sum", "showers_sum", "snowfall_sum", "precipitation_sum"],
	"timezone": "America/New_York",
	"forecast_days": 1,
	"wind_speed_unit": "mph",
	"temperature_unit": "fahrenheit",
	"precipitation_unit": "inch"
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()[0]
daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()[0]
daily_apparent_temperature_max = daily.Variables(2).ValuesAsNumpy()[0]
daily_apparent_temperature_min = daily.Variables(3).ValuesAsNumpy()[0]
daily_sunrise = datetime.fromtimestamp(float(daily.Variables(4).ValuesInt64AsNumpy()[0])).strftime("%I:%M")
daily_sunset = datetime.fromtimestamp(float(daily.Variables(5).ValuesInt64AsNumpy()[0])).strftime("%I:%M")
daily_uv_index_max = daily.Variables(6).ValuesAsNumpy()[0]
daily_rain_sum = daily.Variables(7).ValuesAsNumpy()[0]

daily_data = {"date": pd.date_range(
    start=pd.to_datetime(daily.Time(), unit="s", utc=True),
    end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
    freq=pd.Timedelta(seconds=daily.Interval()),
    inclusive="left"
), "temperature_2m_max": daily_temperature_2m_max, "temperature_2m_min": daily_temperature_2m_min,
    "apparent_temperature_max": daily_apparent_temperature_max,
    "apparent_temperature_min": daily_apparent_temperature_min, "sunrise": daily_sunrise, "sunset": daily_sunset,
    "uv_index_max": daily_uv_index_max, "rain_sum": daily_rain_sum}

daily_dataframe = pd.DataFrame(data = daily_data)
intro_text = f"What's up bitches. Today's weather will be as followed\n"
bot_text = (intro_text +
            f"Max Temp: {daily_temperature_2m_max:.0f} degrees\n"
            f"Min Temp: {daily_temperature_2m_min:.0f} degrees\n"
            f"Sunrise: {daily_sunrise} AM\n"
            f"Sunset: {daily_sunset} PM\n"
            f"UV Index: {int(daily_uv_index_max)}\n")
if daily_rain_sum > 0:
    bot_text += f"Rain: {daily_rain_sum} inches"

Bots.post(bot, bot_id =bot_id,text=bot_text)