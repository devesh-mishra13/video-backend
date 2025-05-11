from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging configuration
logging.basicConfig(level=logging.INFO)

# Fetch MongoDB URL and optional DB name
MONGO_URL = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")  # Make sure this exists in your .env file

# Mongo client and collection (initialized later)
client = None
db = None
users_collection = None# auth_utils.py
from passlib.context import CryptContext
import jwt
import os
from datetime import datetime, timedelta

# Set up the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key for signing the JWT token (keep it secure in production)
SECRET_KEY = os.getenv("JWT_SECRET")

# Hash a password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify a password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Create JWT token with expiration
def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")


async def initialize_mongo_connection():
    global client, db, users_collection
    try:
        # Create MongoDB client
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        await client.admin.command("ping")
        logging.info("✅ Successfully connected to MongoDB.")

        # Use the specified database name from .env or default to Scene
        db_name = MONGO_DB_NAME or 'Scene'
        db = client[db_name]
        
        # Access the correct collection 'Personal' in the Scene database
        users_collection = db.get_collection("Personal")

    except Exception as e:
        logging.error(f"❌ Could not connect to MongoDB: {e}")

def get_users_collection():
    return users_collection

async def get_chats_collection():
    client = AsyncIOMotorClient(MONGO_URL)  # Use the MONGO_URL loaded from env
    db = client[MONGO_DB_NAME]
    return db["chats"]