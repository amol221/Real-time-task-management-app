from flask import flash, g, jsonify, make_response, redirect, render_template, request, url_for
from app import app, mongo, bcrypt,socketio
from models import User, Task
from bson.objectid import ObjectId
from jwt_utilities import create_token, jwt_required


# Error handler for HTTP errors. Returns a custom error page.

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page Not Found"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal Server Error"), 500



# Default route that renders the home page.
@app.route('/')
def home1():
    return render_template('home.html')


# Route for user registration.
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user already exists
        existing_user = mongo.db.users.find_one({"username": username})
        if existing_user:
            flash('Username already exists. Choose a different one.', 'danger')
            return redirect(url_for('register'))

        # If user doesn't exist, proceed with registration
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        mongo.db.users.insert_one({"username": username, "password": hashed_pw})
        flash('Account created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# Route for user login.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({"username": username})

        # Check if entered password matches the stored hashed password for the user.
        if user and bcrypt.check_password_hash(user["password"], password):
            token = create_token(str(user["_id"]))
            response = redirect(url_for('home'))
            
            response.set_cookie('token', token)
            return response
        else:
            flash('Login unsuccessful. Check username and password.', 'danger')

    return render_template('login.html')



# Route for displaying tasks on the home page. It checks if the user is an admin and displays tasks accordingly.
@app.route('/')
@app.route('/home')
@jwt_required
def home():
    if g.user["username"] == 'admin':
        tasks = mongo.db.tasks.find()
    else:
        tasks = mongo.db.tasks.find({"user_id": g.user["_id"]})
    return render_template('home.html', tasks=tasks)


# Route to add a new task
@app.route('/add_task', methods=['POST'])
@jwt_required
def add_task():
    title = request.form['title']
    description = request.form['description']
    mongo.db.tasks.insert_one({"title": title, "description": description, "user_id": g.user["_id"]})
     # Emitting a new task event to the frontend
    socketio.emit('add_task', {'title': title, 'description': description})
    flash('Task added!', 'success')
    return redirect(url_for('home'))


# Route to update a task
@app.route('/edit_task/<task_id>', methods=['POST'])
@jwt_required
def edit_task(task_id):
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('home'))
    
    if g.user["username"] != 'admin' and task["user_id"] != g.user["_id"]:
        flash('Permission denied.', 'danger')
        return redirect(url_for('home'))

    title = request.form['title']
    description = request.form['description']
    
    mongo.db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"title": title, "description": description}})
    # Emitting an update task event to the frontend
    socketio.emit('update_task', {'task_id': task_id, 'title': title, 'description': description})
    flash('Task updated successfully!', 'success')
    return redirect(url_for('home'))


# Route to delete task
@app.route('/delete_task/<task_id>', methods=['POST'])
@jwt_required
def delete_task(task_id):
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('home'))
    
    if g.user["username"] != 'admin' and task["user_id"] != g.user["_id"]:
        flash('Permission denied.', 'danger')
        return redirect(url_for('home'))
    
    mongo.db.tasks.delete_one({"_id": ObjectId(task_id)})
    socketio.emit('delete_task', {'task_id': task_id})
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('home'))

#it will discard token
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('token')
    flash('You have been logged out.', 'success')
    return response
