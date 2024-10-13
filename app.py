from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from flask_migrate import Migrate
import os

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('todos', lazy=True))

# Routes
@app.route('/')
def home():
    return "home"

# Migration Route
@app.route('/run-migrations', methods=['GET'])
def run_migrations():
    try:
        from flask_migrate import upgrade
        upgrade()
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
        access_token = create_access_token(identity=users.id)
        return jsonify(access_token=access_token)
    else:
        return jsonify(message="Invalid email or password"), 401

# Create Task
@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    task = request.json.get('task')
    user_id = get_jwt_identity()

    new_task = TodoItem(task=task, user_id=user_id)
    db.session.add(new_task)
    db.session.commit()

    return jsonify(message="Task created", task={"id": new_task.id, "task": new_task.task, "completed": new_task.completed}), 201

# Get All Tasks for Authenticated User
@app.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()
    tasks = TodoItem.query.filter_by(user_id=user_id).all()

    tasks_list = [{"id": task.id, "task": task.task, "completed": task.completed} for task in tasks]
    return jsonify(tasks=tasks_list)

# Update Task
@app.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    task = TodoItem.query.filter_by(id=task_id, user_id=user_id).first()

    if not task:
        return jsonify(message="Task not found"), 404

    task_data = request.json.get('task')
    completed = request.json.get('completed')

    if task_data:
        task.task = task_data
    if completed is not None:
        task.completed = completed

    db.session.commit()
    return jsonify(message="Task updated", task={"id": task.id, "task": task.task, "completed": task.completed})

# Delete Task
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    task = TodoItem.query.filter_by(id=task_id, user_id=user_id).first()

    if not task:
        return jsonify(message="Task not found"), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify(message="Task deleted")

# Search Task by Title
@app.route('/tasks/search', methods=['GET'])
@jwt_required()
def search_tasks():
    search_term = request.args.get('q')
    user_id = get_jwt_identity()
    
    if not search_term:
        return jsonify(message="Search term is required"), 400

    tasks = TodoItem.query.filter(TodoItem.user_id == user_id, TodoItem.task.ilike(f'%{search_term}%')).all()
    tasks_list = [{"id": task.id, "task": task.task, "completed": task.completed} for task in tasks]

    return jsonify(tasks=tasks_list)

if __name__ == '__main__':
    app.run(debug=True)

