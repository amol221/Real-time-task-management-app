from bson import ObjectId
import jwt
from functools import wraps
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from flask import render_template, request, g
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime
from app import mongo



# Generate a  RSA private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Extract the public key
public_key = private_key.public_key()

# Save the private key to a PEM file
with open("private_key.pem", "wb") as priv_key_file:
    priv_key_file.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

# Save the public key to a PEM file
with open("public_key.pem", "wb") as pub_key_file:
    pub_key_file.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )


def create_token(user_id):
    """
    Generates a JWT token using the user's ID.
    
    Args:
    - user_id: The ID of the user for which the token is being generated.
    
    Returns:
    - A JWT token string.
    """
    with open("private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    
    token = jwt.encode({
        'sub': user_id,  # Subject of the token 
        'iat': datetime.datetime.utcnow(),  # Time the token was generated
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expiration time
    }, private_key, algorithm='RS256')
    
    return token


def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token')  # Get token from the cookie
        if not token:
                return render_template('error.html', error="Log in expired/not logged in please login again")

        try:
            with open("public_key.pem", "rb") as key_file:
                public_key = serialization.load_pem_public_key(
                    key_file.read(),
                    backend=default_backend()
                )

            payload = jwt.decode(token, public_key, algorithms=['RS256'])
            user_id = payload['sub']
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError("Invalid user")
            g.user = user  # Use Flask's g global object to store the user ID 

        except (jwt.ExpiredSignatureError, ValueError):
            return render_template('error.html', error="Log in expired/not logged in please login again")

        except jwt.InvalidTokenError:
            return render_template('error.html', error="Log in expired/not logged in please login again")

        
        return f(*args, **kwargs)

    return decorated_function
