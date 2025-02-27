from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename  # Add this import
import os
import uuid
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import logging
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')  # Add this line
# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'your-secret-key-here'  # Change this to a secure key in production

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    DATA_FILE = DATA_DIR / "user_data.json"
    LAND_RENTALS_FILE = DATA_DIR / "land_rentals.json"
    MARKETPLACE_FILE = DATA_DIR / "marketplace.json"

# Create data directory if it doesn't exist
os.makedirs(Config.DATA_DIR, exist_ok=True)

# Initialize files
def init_json_file(filepath, default_data):
    if not os.path.exists(filepath):
        with open(filepath, "w") as file:
            json.dump(default_data, file, indent=4)

# Initialize all required files
init_json_file(Config.DATA_FILE, {})
init_json_file(Config.LAND_RENTALS_FILE, [])
init_json_file(Config.MARKETPLACE_FILE, [])

def init_marketplace():
    """Initialize marketplace data file if it doesn't exist"""
    marketplace_file = os.path.join('data', 'marketplace.json')
    if not os.path.exists(marketplace_file):
        os.makedirs('data', exist_ok=True)
        with open(marketplace_file, 'w') as f:
            json.dump({'items': []}, f)
    return marketplace_file

# Helper functions for file operations
def load_data(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        init_json_file(file_path, {} if "user_data" in str(file_path) else [])
        return {} if "user_data" in str(file_path) else []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return {} if "user_data" in str(file_path) else []
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return {} if "user_data" in str(file_path) else []

def save_data(file_path, data):
    try:
        # Debug logging
        logger.info(f"Saving data to: {file_path}")
        logger.info(f"Data to save: {json.dumps(data, indent=2)}")
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        
        # Verify save
        logger.info(f"Data saved successfully to {file_path}")
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")
        raise

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# Modified signup route with password hashing
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            phone_number = request.form.get('phone_number', '')
            
            # Validate phone number
            if not phone_number or not phone_number.isdigit() or len(phone_number) != 9 or not phone_number.startswith('7'):
                flash('Please enter a valid Kenyan phone number starting with 7', 'error')
                return redirect(url_for('signup'))
            
            # Load existing user data
            user_data = load_data(Config.DATA_FILE)
            
            if username in user_data:
                flash('Username already exists. Please choose another.', 'error')
                return redirect(url_for('signup'))
            
            # Create new user with phone number
            user_data[username] = {
                'username': username,
                'password': generate_password_hash(password),
                'gender': request.form.get('gender', 'Not specified'),
                'location': request.form.get('location', 'Not specified'),
                'farming_type': request.form.get('farming_type', 'Not specified'),
                'phone_number': f"+254{phone_number}",
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile_pic': None
            }
            
            save_data(Config.DATA_FILE, user_data)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
            
    return render_template('signup.html')

# Modified login route with password verification
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            # Validate input
            if not username or not password:
                flash('Please enter both username and password', 'error')
                return redirect(url_for('login'))
            
            user_data = load_data(Config.DATA_FILE)
            
            if username not in user_data:
                flash('Invalid username or password', 'error')
                logger.warning(f"Login attempt with non-existent username: {username}")
                return redirect(url_for('login'))
                
            if not check_password_hash(user_data[username]['password'], password):
                flash('Invalid username or password', 'error')
                logger.warning(f"Failed login attempt for user: {username}")
                return redirect(url_for('login'))
            
            session['username'] = username
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('login'))  # Redirect without flash message

# Protected routes with login_required decorator
@app.route('/dashboard')
@login_required
def dashboard():
    if 'username' not in session:
        flash('Please login to access dashboard', 'error')
        return redirect(url_for('login'))
        
    try:
        username = session['username']
        user_data = load_data(Config.DATA_FILE)
        user_info = user_data.get(username, {})
        
        return render_template('dashboard.html', 
            username=username,
            user=user_info
        )
    except Exception as e:
        logger.error(f"Dashboard Error: {str(e)}")
        flash('An error occurred while loading the dashboard', 'error')
        return redirect(url_for('home'))

@app.route('/soil-mapping')
@login_required
def soil_mapping():
    soil_data = {
        "Region 1": "Loamy soil - Best for maize",
        "Region 2": "Clay soil - Best for rice",
        "Region 3": "Sandy soil - Best for cassava",
    }
    return render_template('soil_mapping.html', soil_data=soil_data)

@app.route('/climate-patterns')
def climate_patterns():
    climate_data = {
        "Region 1": {
            "climate": "Warm and Wet",
            "recommended_crops": ["Maize", "Beans"]
        },
        "Region 2": {
            "climate": "Cool and Wet",
            "recommended_crops": ["Rice", "Potatoes"]
        },
        "Region 3": {
            "climate": "Hot and Dry",
            "recommended_crops": ["Cassava", "Millet"]
        }
    }
    return render_template('climate_patterns.html', climate_data=climate_data)

@app.route('/land-leasing', methods=['GET', 'POST'])
@login_required
def land_leasing():
    if request.method == 'POST':
        location = request.form['location']
        size = request.form['size']
        price = request.form['price']
        contact = request.form['contact']

        land_rentals = load_data(Config.LAND_RENTALS_FILE)
        land_rentals.append({'location': location, 'size': size, 'price': price, 'contact': contact})
        save_data(Config.LAND_RENTALS_FILE, land_rentals)

    land_rentals = load_data(Config.LAND_RENTALS_FILE)
    return render_template('land_leasing.html', land_rentals=land_rentals)

@app.route('/marketplace', methods=['GET', 'POST'])
@login_required
def marketplace():
    if request.method == 'POST':
        try:
            logger.info("Processing marketplace item submission")
            
            # Create item data
            item_data = {
                'id': str(uuid.uuid4()),
                'name': request.form['item-name'],
                'description': request.form['item-description'],
                'price': float(request.form['item-price']),
                'contact': request.form['seller-contact'],
                'seller': session['username'],
                'date_posted': datetime.now().isoformat(),
                'image': None
            }
            
            # Handle image upload
            if 'item-image' in request.files:
                file = request.files['item-image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    item_data['image'] = f'uploads/{filename}'
                    logger.info(f"Saved marketplace item image: {filename}")

            # Load and update items
            try:
                items = load_data(Config.MARKETPLACE_FILE)
                if not isinstance(items, list):
                    items = []
                
                items.append(item_data)
                save_data(Config.MARKETPLACE_FILE, items)
                logger.info(f"Saved marketplace item with ID: {item_data['id']}")
                
                return jsonify({
                    'success': True,
                    'message': 'Item posted successfully',
                    'redirect': url_for('marketplace')
                })
                
            except Exception as e:
                logger.error(f"Error saving marketplace data: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Marketplace error: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    # GET request
    try:
        items = load_data(Config.MARKETPLACE_FILE)
        return render_template('marketplace.html', items=items if isinstance(items, list) else [])
    except Exception as e:
        logger.error(f"Error loading marketplace: {str(e)}")
        return render_template('marketplace.html', items=[])

@app.route('/crop-disease')
@login_required
def crop_disease():
    # Example crop disease data
    diseases = {
        "Maize": "Leaf Blight: Caused by fungal infection; manage by crop rotation and fungicide.",
        "Rice": "Rice Blast: Fungal disease; prevent by proper water management and resistant varieties.",
        "Cassava": "Cassava Mosaic Disease: Virus transmitted by whiteflies; control by resistant varieties."
    }
    return render_template('crop_disease.html', diseases=diseases)

# Add error handlers
@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f'Server Error: {str(e)}')
    return render_template('500.html'), 500

@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(f'Server Error: {str(e)} | Path: {request.path} | Method: {request.method} | Data: {request.data}')
    return render_template('404.html'), 404

# Define the daily_weather route BEFORE the voice_command route
@app.route('/daily-weather', methods=['GET'])
@login_required
def daily_weather():
    return render_template('daily_weather.html')

# Voice command endpoint
@app.route('/voice-command', methods=['GET', 'POST'])
@login_required
def voice_command():
    if request.method == 'POST':
        command = request.json.get('command', '').lower()
        
        # Command handling logic
        if 'dashboard' in command:
            return jsonify({'redirect': url_for('dashboard')})
        elif 'soil' in command:
            return jsonify({'redirect': url_for('soil_mapping')})
        elif any(word in command for word in ['weather', 'forecast', 'temperature']):
            return jsonify({'redirect': url_for('daily_weather')})
        elif 'climate' in command:
            return jsonify({'redirect': url_for('climate_patterns')})
        
        return jsonify({'message': 'Command not recognized'})
    
    return render_template('voice_command.html')

@app.route('/submit-land', methods=['POST'])
@login_required
def submit_land():
    try:
        logger.info("Starting land submission process") # Debug logging
        
        # Validate file upload
        if 'landPicture' not in request.files:
            logger.warning("No landPicture in request.files")
            return jsonify({
                'success': False, 
                'message': 'No file uploaded',
                'redirect': url_for('dashboard')
            }), 400

        file = request.files['landPicture']
        if file.filename == '':
            logger.warning("Empty filename in landPicture")
            return jsonify({
                'success': False, 
                'message': 'No file selected',
                'redirect': url_for('dashboard')
            }), 400

        # Create land data
        land_data = {
            'id': str(uuid.uuid4()),  # Add unique ID
            'location': request.form.get('location'),
            'size': request.form.get('size'),
            'price': request.form.get('price'),
            'description': request.form.get('description'),
            'contact': request.form.get('contact'),
            'owner': session['username'],
            'created_at': datetime.now().isoformat()
        }

        # Save image if present
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            land_data['image'] = filename
            logger.info(f"Saved image: {filename}")

        # Load and update listings
        try:
            listings = load_data(Config.LAND_RENTALS_FILE)
            if not isinstance(listings, list):
                listings = []
            
            listings.append(land_data)
            save_data(Config.LAND_RENTALS_FILE, listings)
            logger.info(f"Saved land listing with ID: {land_data['id']}")
            
        except Exception as e:
            logger.error(f"Error saving land data: {str(e)}")
            raise

        return jsonify({
            'success': True,
            'message': 'Land listing submitted successfully',
            'redirect': url_for('dashboard')
        }), 200

    except Exception as e:
        logger.error(f"Error in submit_land: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}",
            'redirect': url_for('dashboard')
        }), 500
        
@app.route('/profile')
@login_required
def profile():
    try:
        user_data = load_data(Config.DATA_FILE)
        username = session.get('username')
        
        if username not in user_data:
            flash('User profile not found.', 'error')
            return redirect(url_for('dashboard'))
            
        user = user_data[username]
        
        # Format phone number for display
        phone_number = user.get('phone_number', 'Not specified')
        if phone_number and phone_number != 'Not specified':
            # Ensure the phone number is properly formatted
            if not phone_number.startswith('+254'):
                phone_number = f"+254{phone_number}"
            user['phone_number'] = phone_number
            
        return render_template('profile.html', username=username, user=user)
        
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        flash('Error loading profile.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/edit-profile/<username>', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    if session['username'] != username:
        flash('You can only edit your own profile.', 'error')
        return redirect(url_for('profile'))
        
    try:
        user_data = load_data(Config.DATA_FILE)
        
        if request.method == 'POST':
            # Get phone number and handle country code
            phone_number = request.form.get('phone_number', '')
            if phone_number:
                if not phone_number.startswith('+254'):
                    phone_number = f"+254{phone_number}"
            
            # Update user information
            user_data[username].update({
                'location': request.form.get('location', 'Not specified'),
                'farming_type': request.form.get('farming_type', 'Not specified'),
                'phone_number': phone_number if phone_number else 'Not specified'
            })
            
            # Handle password change if provided
            new_password = request.form.get('new_password')
            current_password = request.form.get('current_password')
            if new_password and current_password:
                if check_password_hash(user_data[username]['password'], current_password):
                    user_data[username]['password'] = generate_password_hash(new_password)
                else:
                    flash('Current password is incorrect.', 'error')
                    return render_template('edit_profile.html', username=username, user=user_data[username])
            
            save_data(Config.DATA_FILE, user_data)
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        return render_template('edit_profile.html', username=username, user=user_data[username])
        
    except Exception as e:
        logger.error(f"Profile edit error: {str(e)}")
        flash('Error updating profile. Please try again.', 'error')
        return redirect(url_for('profile'))

@app.route('/upload-profile-pic', methods=['POST'])
@login_required
def upload_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('profile'))
        
    file = request.files['profile_pic']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Update user profile picture in data
        user_data = load_data(Config.DATA_FILE)
        user_data[session['username']]['profile_pic'] = url_for('static', filename=f'uploads/{filename}')
        save_data(Config.DATA_FILE, user_data)
        
        flash('Profile picture updated successfully!', 'success')
    else:
        flash('Invalid file type', 'error')
        
    return redirect(url_for('profile'))

@app.route('/edit-profile-pic', methods=['POST'])
@login_required
def edit_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('edit_profile', username=session['username']))
        
    file = request.files['profile_pic']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('edit_profile', username=session['username']))
        
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Update user profile picture in data
            user_data = load_data(Config.DATA_FILE)
            user_data[session['username']]['profile_pic'] = f'uploads/{filename}'
            save_data(Config.DATA_FILE, user_data)
            
            flash('Profile picture updated successfully!', 'success')
        except Exception as e:
            logger.error(f"Error updating profile picture: {str(e)}")
            flash('Error updating profile picture', 'error')
    else:
        flash('Invalid file type. Please use PNG, JPG, JPEG or GIF', 'error')
        
    return redirect(url_for('edit_profile', username=session['username']))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_user():
    if 'username' in session:
        user_data = load_data(Config.DATA_FILE)
        user_info = user_data.get(session['username'], {})
        return {'user': user_info}
    return {'user': None}

@app.context_processor
def utility_processor():
    return {'current_year': datetime.now().year}

if __name__ == '__main__':
    app.run(debug=False)
