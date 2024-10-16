from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import timedelta
from flask_migrate import Migrate

import os

app = Flask(__name__)
# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
#postgresql://tododata_8ptj_user:02Int8llyOi43enGzb3ostBSbFexvdxI@dpg-cs3tq53qf0us73dvf7r0-a.frankfurt-postgres.render.com/tododata_8ptj
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change to a strong key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# To-do Model
class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(120), nullable=False)
    completed = db.Column(db.Boolean, default=False)


# Routes (add more later)

@app.route('/')
def home():
    return "home"

@app.route('/run-migrations', methods=['GET'])
def run_migrations():
    try:
        from flask_migrate import upgrade
        upgrade()  # Run the upgrade function
        return jsonify(message="Migrations applied successfully"), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# Register Route
@app.route('/register', methods=['POST'])
def register():
    name = request.json.get('name')
    email = request.json.get('email')
    password = request.json.get('password')
        
    # Check if the email is already in use
    if User.query.filter_by(email=email).first():
        return jsonify(message="Email is already registered"), 409
        
    # Create and save the new user
    users = User(name=name, email=email, password=password)
    db.session.add(users)
    db.session.commit()
    return jsonify(message="User registered"), 201
    
# Login Route
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')
    users = User.query.filter_by(email=email).first()

    # Check if user exists and password matches
    if users and users.password == password:
        access_token = create_access_token(identity=users.email)
        return jsonify(access_token=access_token, message="Welcome!")
    else:
        return jsonify(message="Invalid email or password"), 401


if __name__ == '__main__':
    app.run(debug=True)