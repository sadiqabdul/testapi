from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import timedelta
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
import os

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")  # Load from environment variable
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change to a strong key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# User Model
class User(db.Model):
    __tablename__ = 'users'  # Avoid using 'user', which is a reserved keyword in PostgreSQL
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# To-do Model
class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(120), nullable=False)
    completed = db.Column(db.Boolean, default=False)


# Routes

@app.route('/')
def home():
    try:
        # Test a simple query
        db.session.execute(text('SELECT 1'))
        return "Database connected, home"
    except Exception as e:
        return f"Error: {str(e)}"


# Register Route
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Check if the email is already in use
        if User.query.filter_by(email=email).first():
            return jsonify(message="Email is already registered"), 409
        
        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Create and save the new user
        user = User(name=name, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User registered"), 201

    except Exception as e:
        return f"Error: {str(e)}"


# Login Route
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password matches
        if user and check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.email)
            return jsonify(access_token=access_token, message="Welcome!")
        else:
            return jsonify(message="Invalid email or password"), 401
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)
