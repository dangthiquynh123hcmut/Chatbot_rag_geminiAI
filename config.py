from pymongo import MongoClient
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('DB_NAME', 'pdf_chatbot')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'pdf_files')

# API configuration
API_KEY = os.getenv('API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'Google AI')

# Validate and format MongoDB URI
if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set in .env file")

# Split URI to handle username and password
uri_parts = MONGODB_URI.split('@')
if len(uri_parts) > 1:
    auth_part = uri_parts[0]
    if ':' in auth_part:
        auth_parts = auth_part.split('//')[1].split(':')
        username = auth_parts[0]
        password = auth_parts[1]
        # Escape username and password
        username = quote_plus(username)
        password = quote_plus(password)
        # Rebuild URI with escaped credentials
        MONGODB_URI = f"mongodb+srv://{username}:{password}@{uri_parts[1]}"

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Test connection
    client.server_info()
    print("MongoDB connection successful")
except Exception as e:
    raise ValueError(f"Failed to connect to MongoDB: {str(e)}")
