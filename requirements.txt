from fastapi import FastAPI, HTTPException, Response, Path
from pydantic import BaseModel, EmailStr
from db import initialize_mongo_connection, get_users_collection, get_chats_collection
from auth_utils import hash_password, verify_password, create_access_token
import logging
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from bson import ObjectId
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust this based on your security needs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize collections
users_collection = None
chats_collection = None

@app.on_event("startup")
async def startup_event():
    global users_collection, chats_collection
    logger.info("Initializing MongoDB connection...")
    await initialize_mongo_connection()
    users_collection = get_users_collection()
    
    # Ensure to await the coroutine to get the actual collection object
    chats_collection = await get_chats_collection()  # Await this function to get the collection
    logger.info("MongoDB connection initialized successfully.")

# User input model for signup
class UserIn(BaseModel):
    name: str
    email: EmailStr
    password: str

# User input model for login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Request model for creating a new chat
class CreateChatRequest(BaseModel):
    user_id: str  # We'll leave this as string for now but convert to ObjectId in the logic
    chat_name: str

# Signup endpoint
@app.post("/signup")
async def signup(user: UserIn, response: Response):
    logger.info(f"Signup request for email: {user.email}")

    # Check if the user already exists
    if await users_collection.find_one({"email": user.email}):
        logger.warning(f"Email {user.email} already registered.")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user document
    user_dict = {
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password)
    }

    # Insert user into the database
    await users_collection.insert_one(user_dict)
    logger.info(f"User with email {user.email} created successfully.")
    
    # Generate JWT token
    token = create_access_token({
        "id": str(user_dict["_id"]),
        "email": user_dict["email"]
    })
    logger.info(f"Generated JWT token for email: {user.email}")

    return {"message": "User created successfully", "access_token": token}

# Login endpoint
@app.post("/login")
async def login(user: UserLogin, response: Response):
    logger.info(f"Login attempt for email: {user.email}")

    # Find the user in the database
    db_user = await users_collection.find_one({"email": user.email})
    
    if not db_user or not verify_password(user.password, db_user["password"]):
        logger.warning(f"Invalid login attempt for email: {user.email}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create JWT token
    token = create_access_token({
        "id": str(db_user["_id"]),
        "email": db_user["email"]
    })
    logger.info(f"Generated JWT token for email: {user.email}")

    # Set token in HttpOnly cookie
    response.set_cookie(key="access_token", value=token, httponly=True)
    logger.info(f"JWT token set in cookie for {user.email}")

    return {
        "access_token": token,
        "user": {
            "name": db_user["name"],
            "email": db_user["email"],
            "id": str(db_user["_id"])
        }
    }

# Logout endpoint
@app.post("/logout")
async def logout(response: Response):
    # Clear the JWT token cookie to log the user out
    response.delete_cookie("access_token")
    logger.info("JWT token deleted from cookies, user logged out successfully.")
    return {"message": "Logged out successfully"}

# Endpoint for creating a new chat
@app.post("/chat/create")
async def create_chat(req: CreateChatRequest):
    logger.info(f"Creating chat for user {req.user_id} with name {req.chat_name}")
    
    try:
        # Convert user_id to ObjectId
        user_id = ObjectId(req.user_id)
        
        # Generate a new chat ID using uuid4
        chat_id = str(uuid4())
        
        # Prepare the chat document to insert
        chat = {
            "user_id": user_id,
            "chat_id": chat_id,
            "chat_name": req.chat_name,
            "frames": [],
            "created_at": datetime.utcnow()  # Store current UTC time
        }
        
        # Insert the chat document into the MongoDB collection
        await chats_collection.insert_one(chat)
        logger.info(f"Chat with name {req.chat_name} created successfully.")
        
        # Return the chat_id to the client
        return {"message": "Chat created successfully", "chat_id": chat_id}
    
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(status_code=500, detail="Error creating chat")

@app.get("/user/{user_id}/chats")
async def get_user_chats(user_id: str = Path(..., description="The ID of the user")):
    logger.info(f"Fetching chats for user_id: {user_id}")

    try:
        user_obj_id = ObjectId(user_id)
        chats_cursor = chats_collection.find({"user_id": user_obj_id})
        chats = await chats_cursor.to_list(length=100)

        # Format the chats for the response
        formatted_chats = [
            {
                "chat_id": chat["chat_id"],
                "chat_name": chat["chat_name"],
                "created_at": chat.get("created_at"),
                "frames": chat.get("frames", [])
            } for chat in chats
        ]
        return {"chats": formatted_chats}
    
    except Exception as e:
        logger.error(f"Error fetching chats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chats")