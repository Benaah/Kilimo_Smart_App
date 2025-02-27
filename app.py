from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
import requests

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

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

# Routes
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = load_data(data_file)

        if username in user_data:
            flash("Username already exists. Please log in.", 'error')
            return redirect(url_for('signup'))

        user_data[username] = {"password": password}
        save_data(data_file, user_data)

        flash("Sign-up successful! Please log in.", 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = load_data(data_file)

        if username in user_data and user_data[username]['password'] == password:
            session['username'] = username
            flash("Login successful!", 'success')
            return redirect(url_for('dashboard'))

        flash("Invalid username or password.", 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("Please log in to access the dashboard.", 'error')
        return redirect(url_for('login'))

    features = [
        "Soil Mapping by Region",
        "Multi-Language Support",
        "Voice Interface for Non-Readers/Writers",
        "Daily Weather Updates",
        "Land Leasing/Renting Options",
        "Buy/Sell Marketplace",
        "Learn about Crop Diseases"
    ]

    return render_template('dashboard.html', features=features, username=session['username'])

@app.route('/soil-mapping')
def soil_mapping():
    soil_data = {
        "Region 1": "Loamy soil - Best for maize",
        "Region 2": "Clay soil - Best for rice",
        "Region 3": "Sandy soil - Best for cassava",
    }
    return render_template('soil_mapping.html', soil_data=soil_data)

@app.route('/daily-weather', methods=['GET', 'POST'])
def daily_weather():
    weather_data = None
    if request.method == 'POST':
        city = request.form['city']
        weather_data = get_weather(city)
        if not weather_data:
            flash("Could not fetch weather data. Please try again.", 'error')

    return render_template('daily_weather.html', weather_data=weather_data)

@app.route('/land-leasing', methods=['GET', 'POST'])
def land_leasing():
    if request.method == 'POST':
        location = request.form['location']
        size = request.form['size']
        price = request.form['price']
        contact = request.form['contact']

        land_rentals = load_data(land_rentals_file)
        land_rentals.append({'location': location, 'size': size, 'price': price, 'contact': contact})
        save_data(land_rentals_file, land_rentals)

    land_rentals = load_data(land_rentals_file)
    return render_template('land_leasing.html', land_rentals=land_rentals)

@app.route('/marketplace', methods=['GET', 'POST'])
def marketplace():
    if request.method == 'POST':
        item_name = request.form['item_name']
        price = request.form['price']
        description = request.form['description']
        username = session.get('username', 'Anonymous')

        marketplace = load_data(marketplace_file)
        marketplace.append({'item_name': item_name, 'price': price, 'description': description, 'username': username})
        save_data(marketplace_file, marketplace)

    marketplace = load_data(marketplace_file)
    return render_template('marketplace.html', marketplace=marketplace)

@app.route('/crop-disease')
def crop_disease():
    diseases = {
        "Maize": "Leaf Blight: Caused by fungal infection; manage by crop rotation and fungicide.",
        "Rice": "Rice Blast: Fungal disease; prevent by proper water management and resistant varieties.",
        "Cassava": "Cassava Mosaic Disease: Virus transmitted by whiteflies; control by resistant varieties."
    }
    return render_template('crop_disease.html', diseases=diseases)

@app.route('/voice-command', methods=['GET', 'POST'])
def voice_command():
    if request.method == 'POST':
        command = request.json.get('command')
        if command:
            if 'soil' in command.lower():
                return jsonify({'redirect': url_for('soil_mapping')})
            elif 'weather' in command.lower():
                return jsonify({'redirect': url_for('daily_weather')})
            elif 'market' in command.lower():
                return jsonify({'redirect': url_for('marketplace')})
            elif 'land' in command.lower():
                return jsonify({'redirect': url_for('land_leasing')})
            elif 'disease' in command.lower():
                return jsonify({'redirect': url_for('crop_disease')})
            else:
                return jsonify({'message': "Command not recognized."})
        return jsonify({'message': "No command received."})
    # For GET requests, render the voice interface page
    return render_template('voice_command.html')
