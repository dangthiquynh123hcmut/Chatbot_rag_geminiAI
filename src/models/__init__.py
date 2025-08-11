"""
This module contains all the Pydantic models used in the application.
"""

# Import all models to make them available when importing from models
from .api import (
    FileUpload,
    TokenResponse,
    UserResponse,
    RegisterRequest,
    LoginRequest,
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    ConversationHistoryResponse,
    PDFUploadResponse
)

from .auth import (
    Token,
    TokenData,
    User,
    UserInDB,
    UserCreate
)

# Make these available when importing from models
__all__ = [
    # API models
    'FileUpload',
    'TokenResponse',
    'UserResponse',
    'RegisterRequest',
    'LoginRequest',
    'ChatRequest',
    'ChatResponse',
    'ConversationHistory',
    'ConversationHistoryResponse',
    'PDFUploadResponse',
    
    # Auth models
    'Token',
    'TokenData',
    'User',
    'UserInDB',
    'UserCreate'
]
