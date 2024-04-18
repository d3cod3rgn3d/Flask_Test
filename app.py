import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask_login import LoginManager, login_user, current_user, login_required, logout_user, UserMixin


load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Example User class
class User(UserMixin):
	def __init__(self, user_id):
		self.id = user_id

# Example user loader function
@login_manager.user_loader
def load_user(user_id):
	conn = sqlite3.connect('database.db')
	c = conn.cursor()
	c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
	user_data = c.fetchone()
	conn.close()

	if user_data:
		# Create a User object with the retrieved user data
		user = User(user_data[0]) # Assuming user ID is the first column
		return user

	return None # Return None if user is not found

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = c.fetchone()
        conn.close()

        if existing_user:
            error_message = "Username or email already exists. Please choose a different one."
            return render_template('register.html', error_message=error_message)

        # If username and email are unique, proceed with registration
        hashed_password = generate_password_hash(password)
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))


    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username_or_email, username_or_email))
        user = c.fetchone()
        conn.close()

        if user:
            # User found, check password
            if check_password_hash(user[3], password):
                # Password is correct, authenticate the user
                # Use Flask-Login's login_user function to login the user
                user_obj = User(user[0])  # Initialize the User object with the user ID
                login_user(user_obj)
                return redirect(url_for('welcome'))
            else:
                flash("Invalid password. Please try again.", "error")
                return redirect(url_for('login'))
        else:
            flash("User does not exist. Please register.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    if request.method == 'POST':
        logout_user()
        return render_template('logout.html')  # Redirect to the logout page after logout
    else:
        # If the user tries to access the logout page directly via GET, redirect them to the index page
        return redirect(url_for('welcome'))


if __name__ == '__main__':
    app.run(debug=True)
