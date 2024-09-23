from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = {}
    geocoding_results = []  # List to store geocoding results
    default_unit = 'imperial'  # Default to Fahrenheit (imperial)
    unit = request.args.get('units', default_unit)
    api_key = os.getenv('WEATHER_API_KEY')

    if request.method == 'POST':
        city = request.form.get('city')

        # Step 1: Fetch cities using Geocoding API
        geo_url = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={api_key}'
        geo_response = requests.get(geo_url)
        
        if geo_response.status_code == 200:
            geocoding_results = geo_response.json()

            if len(geocoding_results) == 1:
                # If only one city result, fetch weather directly
                lat = geocoding_results[0]['lat']
                lon = geocoding_results[0]['lon']
                weather_url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={unit}'
                weather_response = requests.get(weather_url)
                
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    weather_data['units'] = '°C' if unit == 'metric' else '°F'

                    # Calculate local time
                    utc_time = datetime.utcnow()
                    timezone_offset = weather_data['timezone']
                    local_time = utc_time + timedelta(seconds=timezone_offset)
                    weather_data['local_time'] = local_time.strftime('%I:%M %p on %B %d, %Y')
                else:
                    weather_data = {'error': 'Weather data not found.'}
        else:
            weather_data = {'error': 'City not found or API limit reached.'}

    return render_template('index.html', weather_data=weather_data, geocoding_results=geocoding_results, unit=unit)

@app.route('/fetch_weather', methods=['POST'])
def fetch_weather():
    # Fetch the latitude and longitude from the form submission
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    unit = request.form.get('unit')
    api_key = os.getenv('WEATHER_API_KEY')

    if lat and lon:
        # Form a valid weather API URL using lat and lon
        weather_url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={unit}'
        weather_response = requests.get(weather_url)

        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            weather_data['units'] = '°C' if unit == 'metric' else '°F'

            # Calculate local time using timezone offset
            utc_time = datetime.utcnow()
            timezone_offset = weather_data['timezone']
            local_time = utc_time + timedelta(seconds=timezone_offset)
            weather_data['local_time'] = local_time.strftime('%I:%M %p on %B %d, %Y')

            # Return JSON response to be used in the AJAX callback
            return jsonify(weather_data=weather_data)
        else:
            return jsonify({'error': 'Weather data not found.'}), 404
    else:
        return jsonify({'error': 'Invalid latitude or longitude.'}), 400

@app.route('/toggle_units', methods=['POST'])
def toggle_units():
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    current_unit = request.form.get('current_unit')
    new_unit = 'imperial' if current_unit == 'metric' else 'metric'
    api_key = os.getenv('WEATHER_API_KEY')

    weather_url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={new_unit}'
    response = requests.get(weather_url)

    if response.status_code == 200:
        weather_data = response.json()
        weather_data['units'] = '°C' if new_unit == 'metric' else '°F'

        # Calculate local time
        utc_time = datetime.utcnow()
        timezone_offset = weather_data['timezone']
        local_time = utc_time + timedelta(seconds=timezone_offset)
        weather_data['local_time'] = local_time.strftime('%I:%M %p on %B %d, %Y')

        return jsonify(weather_data=weather_data, unit=new_unit)
    else:
        return jsonify(error='City not found or API limit reached.'), 404

if __name__ == '__main__':
    app.run(debug=True)
