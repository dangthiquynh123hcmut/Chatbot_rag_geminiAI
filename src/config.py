from pymongo import MongoClient
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('DB_NAME', 'pdf_chatbot')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'pdf_files')

# API configuration
API_KEY = os.getenv('API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'Google AI')

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# Validate and format MongoDB URI
if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set in .env file")

# Split URI to handle username and password
uri_parts = MONGODB_URI.split('@')
if len(uri_parts) > 1:
    auth_part = uri_parts[0]
    if ':' in auth_part and '//' in auth_part:
        auth_parts = auth_part.split('//')[1].split(':')
        if len(auth_parts) == 2:  # Make sure we have both username and password
            username = auth_parts[0]
            password = auth_parts[1]
            # Escape username and password
            username = quote_plus(username)
            password = quote_plus(password)
            # Rebuild URI with escaped credentials
            MONGODB_URI = f"mongodb+srv://{username}:{password}@{uri_parts[1]}"

# Initialize MongoDB client and collections
try:
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    
    # Collections
    collection = db[COLLECTION_NAME]  # For PDF files
    users = db['users']  # For user accounts
    conversations = db['conversations']  # For chat history
    
    # Create indexes for better query performance
    users.create_index("username", unique=True)
    users.create_index("email", unique=True)
    conversations.create_index("user_id")
    conversations.create_index("timestamp")
    
    # Test connection
    client.server_info()
    print("MongoDB connection successful")
except Exception as e:
    print(f"Error connecting to MongoDB: {str(e)}")
    raise

# Create FastAPI app
app = FastAPI(
    title="PDF Chatbot API",
    description="API for PDF Chatbot with user authentication and chat history",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Export everything needed by other modules
__all__ = [
    'app',
    'db',
    'collection',
    'users',
    'conversations',
    'SECRET_KEY',
    'ALGORITHM',
    'ACCESS_TOKEN_EXPIRE_MINUTES',
    'API_KEY',
    'MODEL_NAME'
]

