from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
import requests
import pyttsx3
import langdetect

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak_text(text, lang='en'):
    if lang == 'sw':
        engine.setProperty('voice', 'sw')  # Set Swahili voice if available
    else:
        engine.setProperty('voice', 'en')  # Default to English
    engine.say(text)
    engine.runAndWait()

# File paths for storing data
data_file = "user_data.json"
land_rentals_file = "land_rentals.json"
marketplace_file = "marketplace.json"

# Weather API Configuration
WEATHER_API_KEY = "bc6ba6fa150140b0ba9155229250802"  # Replace with your OpenWeatherMap API key
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# Initialize files if they don't exist
if not os.path.exists(data_file):
    with open(data_file, "w") as file:
        json.dump({}, file)

if not os.path.exists(land_rentals_file):
    with open(land_rentals_file, "w") as file:
        json.dump([], file)

if not os.path.exists(marketplace_file):
    with open(marketplace_file, "w") as file:
        json.dump([], file)

# Helper functions for file operations
def load_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def save_data(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def get_weather(city):
    try:
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

@app.route('/voice-command', methods=['GET', 'POST'])
def voice_command():
    if request.method == 'POST':
        command = request.json.get('command')
        response_text = "Amri haijatambuliwa."  # Default to Swahili if language is unclear
        language = 'sw'  # Default language
        
        if command:
            try:
                detected_lang = langdetect.detect(command)  # Detect language
            except langdetect.lang_detect_exception.LangDetectException:
                detected_lang = 'sw'  # Default to Swahili if detection fails
            
            if detected_lang == 'en':
                language = 'en'
            elif detected_lang == 'sw':
                language = 'sw'
            else:
                language = 'en'  # Default to English for unsupported languages

            command = command.lower()
            if any(word in command for word in ['soil', 'udongo']):
                response_text = "Redirecting to soil mapping." if language == 'en' else "Inapelekwa kwenye ramani ya udongo."
                speak_text(response_text, language)
                return jsonify({'redirect': url_for('soil_mapping')})
            elif any(word in command for word in ['weather', 'hali ya hewa']):
                response_text = "Fetching weather information." if language == 'en' else "Inatafuta taarifa ya hali ya hewa."
                speak_text(response_text, language)
                return jsonify({'redirect': url_for('daily_weather')})
            elif any(word in command for word in ['market', 'soko']):
                response_text = "Opening marketplace." if language == 'en' else "Fungua soko."
                speak_text(response_text, language)
                return jsonify({'redirect': url_for('marketplace')})
            elif any(word in command for word in ['land', 'shamba']):
                response_text = "Showing land leasing options." if language == 'en' else "Inaonyesha chaguzi za upangaji wa ardhi."
                speak_text(response_text, language)
                return jsonify({'redirect': url_for('land_leasing')})
            elif any(word in command for word in ['disease', 'ugonjwa']):
                response_text = "Providing crop disease information." if language == 'en' else "Inatoa maelezo kuhusu magonjwa ya mimea."
                speak_text(response_text, language)
                return jsonify({'redirect': url_for('crop_disease')})
        
        speak_text(response_text, language)
        return jsonify({'message': response_text})
    return render_template('voice_command.html')