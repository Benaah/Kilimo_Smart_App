from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key

data_file = "user_data.json"
land_rentals_file = "land_rentals.json"
marketplace_file = "marketplace.json"

# Initialize user data file if not present
if not os.path.exists(data_file):
    with open(data_file, "w") as file:
        json.dump({}, file)

# Initialize land rentals data file if not present
if not os.path.exists(land_rentals_file):
    with open(land_rentals_file, "w") as file:
        json.dump([], file)

# Initialize marketplace data file if not present
if not os.path.exists(marketplace_file):
    with open(marketplace_file, "w") as file:
        json.dump([], file)

def load_user_data():
    with open(data_file, "r") as file:
        return json.load(file)

def save_user_data(data):
    with open(data_file, "w") as file:
        json.dump(data, file, indent=4)

def load_land_rentals():
    with open(land_rentals_file, "r") as file:
        return json.load(file)

def save_land_rentals(data):
    with open(land_rentals_file, "w") as file:
        json.dump(data, file, indent=4)

def load_marketplace():
    with open(marketplace_file, "r") as file:
        return json.load(file)

def save_marketplace(data):
    with open(marketplace_file, "w") as file:
        json.dump(data, file, indent=4)

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

        user_data = load_user_data()

        if username in user_data:
            flash("Username already exists. Please log in.", 'error')
            return redirect(url_for('signup'))

        user_data[username] = {"password": password}
        save_user_data(user_data)

        flash("Sign-up successful! Please log in.", 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = load_user_data()

        if username in user_data and user_data[username]["password"] == password:
            session['username'] = username
            flash("Login successful!", 'success')
            return redirect(url_for('dashboard'))

        flash("Invalid username or password.", 'error')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("Please log in to access the dashboard.", 'error')
        return redirect(url_for('login'))

    features = [
        "Soil Mapping by Region",
        "Multi-Language Support",
        "Voice Interface for Non-Readers/Writers",
        "Regional Climate Patterns with Crop Recommendations",
        "Land Leasing/Renting Options",
        "AI-Powered Crop Disease Identification",
        "Buy/Sell Marketplace",
    ]

    return render_template('dashboard.html', features=features, username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", 'success')
    return redirect(url_for('home'))

@app.route('/land-leasing', methods=['GET', 'POST'])
def land_leasing():
    if request.method == 'POST':
        location = request.form['location']
        size = request.form['size']
        price = request.form['price']
        contact = request.form['contact']

        land_rentals = load_land_rentals()
        land_rentals.append({'location': location, 'size': size, 'price': price, 'contact': contact})
        save_land_rentals(land_rentals)

    land_rentals = load_land_rentals()
    return render_template('land_leasing.html', land_rentals=land_rentals)

@app.route('/crop-disease', methods=['GET', 'POST'])
def crop_disease():
    if request.method == 'POST':
        if 'diseaseImage' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['diseaseImage']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Here you would add your image analysis logic
            # For demonstration, we'll use a dummy result
            analysis_result = {
                'disease': 'Powdery Mildew',
                'remedy': 'Apply fungicide and ensure proper air circulation.'
            }
            return render_template('crop_disease.html', analysis_result=analysis_result)
    return render_template('crop_disease.html')

@app.route('/marketplace', methods=['GET', 'POST'])
def marketplace():
    if request.method == 'POST':
        item_name = request.form['item_name']
        price = request.form['price']
        description = request.form['description']
        username = session.get('username', 'Anonymous')

        marketplace = load_marketplace()
        marketplace.append({'item_name': item_name, 'price': price, 'description': description, 'username': username})
        save_marketplace(marketplace)

    marketplace = load_marketplace()
    return render_template('marketplace.html', marketplace=marketplace)

if __name__ == '__main__':
    app.run(debug=True)