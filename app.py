# code by Amol 
#this is main page from where our programme will run

from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO



app = Flask(__name__)
# The SECRET_KEY is used for encryption in sessions and signing flash messages.
# It ensures data integrity by preventing data tampering.
app.config["SECRET_KEY"] = 'it_is_the super_secret_key'
app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"

# Initializing PyMongo for MongoDB integration with the app.
mongo = PyMongo(app)

# Initializing Bcrypt for password hashing.
bcrypt = Bcrypt(app)

# Initializing SocketIO for real-time web communication.
socketio = SocketIO(app)


from routes import *

@app.before_request
def load_user():
    if "user_id" in g:
        user = mongo.db.users.find_one({"_id": ObjectId(g.user_id)})
        g.user = user


if __name__ == '__main__':
    socketio.run(app, debug=True)