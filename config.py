from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import ssl
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

# Add retryWrites and w=majority if not present in URI
if 'retryWrites' not in MONGODB_URI and 'w=' not in MONGODB_URI:
    MONGODB_URI += '&retryWrites=true&w=majority'

# Initialize MongoDB client
try:
    # Create a new client and connect to the server
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,  # 5 second timeout
        ssl=True,
        ssl_cert_reqs=ssl.CERT_NONE,  # Disable certificate verification
        server_api=ServerApi('1')
    )
    
    # Test the connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    # Get database and collection
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
except Exception as e:
    error_msg = str(e)
    if 'TLSV1_ALERT_INTERNAL_ERROR' in error_msg:
        print("""
        SSL Handshake Error Detected. Please check the following:
        1. Make sure your MongoDB Atlas cluster has IP whitelist set to allow all IPs (0.0.0.0/0)
        2. Ensure your MongoDB user has the correct permissions
        3. Try updating your MongoDB driver: pip install --upgrade pymongo
        4. If the issue persists, try using a newer version of Python
        """)
    raise ValueError(f"Failed to connect to MongoDB: {error_msg}")
