from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_mail import Mail, Message
import mysql.connector
from datetime import timedelta
import hashlib
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# Secret key for session management and flash messages
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=30)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'live.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# Initialize Flask-Mail
mail = Mail(app)

# Database configuration
db_config = {
    'user': 'root',
    'password': '12345678',
    'host': 'localhost',
    'database': 'HOSPITALS'
}

# Helper function for database connection
def create_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        with create_connection() as conn:
            if conn:
                email = request.form['email']
                passcode = request.form['passcode']
                hashed_password = hash_password(passcode)

                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Users WHERE Email = %s AND Passcode = %s", (email, hashed_password))
                user = cursor.fetchone()

                if user:
                    session['user'] = user[1]  # Store username in session
                    flash(f"Welcome back, {user[1]}!")
                    return redirect(url_for('home'))
                else:
                    flash("Invalid email or password.")
                    return redirect(url_for('login'))

            flash("Database connection error.")
            return redirect(url_for('login'))

    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        with create_connection() as conn:
            if conn:
                full_name = request.form['full_name']
                phone = request.form['phone']
                age = int(request.form['age'])
                gender = request.form['gender']
                email = request.form['email']
                passcode = request.form['passcode']
                hashed_password = hash_password(passcode)

                cursor = conn.cursor()

                # Check if user already exists
                cursor.execute("SELECT * FROM Users WHERE Email = %s OR PhoneNumber = %s", (email, phone))
                if cursor.fetchone():
                    flash("An account with this email or phone number already exists. Please log in.")
                    return redirect(url_for('login'))

                # Insert new user
                sql = "INSERT INTO Users (FullName, PhoneNumber, Age, Gender, Email, Passcode) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (full_name, phone, age, gender, email, hashed_password))
                conn.commit()
                flash("Registration successful! Please log in.")
                return redirect(url_for('login'))

            flash("Database connection error.")
            return redirect(url_for('register'))

    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

# Route to send email notification after booking
@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.get_json()
    selected_date = data.get('date')
    selected_time = data.get('time')

    if not selected_date or not selected_time:
        return jsonify({'status': 'error', 'message': 'Date or time not provided.'})

    # Prepare the email message
    msg = Message(
        'Booking Confirmed',
        sender='hi@demomailtrap.com',
        recipients=['resqservices12@gmail.com']
    )
    
    msg.body = f'Your booking with the doctor has been confirmed for {selected_date} at {selected_time}.For further queries kindly contact us via our Customer support Email: resqservices12@gmail.com or Phone number: +9198203840274'

    try:
        mail.send(msg)
        return jsonify({'status': 'success', 'message': 'Email has been sent!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# API route to search doctors by specialization, hospital, and sort by rating
@app.route('/api/doctors', methods=['GET'])
def search_doctors():
    specialization = request.args.get('specialization')
    hospital_name = request.args.get('hospital')
    sort_by_rating = request.args.get('sort_by_rating')

    with create_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT doctor_name, hospital_name, rating FROM doctors WHERE 1=1"
        params = []

        if specialization:
            query += " AND speciality = %s"
            params.append(specialization)
        
        if hospital_name:
            query += " AND hospital_name = %s"
            params.append(hospital_name)
        
        if sort_by_rating == 'true':
            query += " ORDER BY rating DESC"

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
