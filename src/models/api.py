from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId
import os
from models.auth import Token, User, UserCreate

class FileUpload(BaseModel):
    filename: str
    upload_date: str
    user_id: Optional[str] = None
    metadata: Optional[dict] = None
    file_id: str

    class Config:
        json_encoders = {
            ObjectId: lambda v: str(v)
        }

# Authentication Models
class TokenResponse(Token):
    user: User

class UserResponse(User):
    id: str

    class Config:
        json_encoders = {
            ObjectId: lambda v: str(v)
        }




class ChatResponse(BaseModel):
    answer: str
    timestamp: str
    model_name: str = os.getenv('MODEL_NAME', 'Google AI')

class ConversationHistory(BaseModel):
    user_id: str
    question: str
    answer: str
    timestamp: str
    model_name: str

    class Config:
        json_encoders = {
            ObjectId: lambda v: str(v)
        }

class ConversationHistoryResponse(BaseModel):
    conversations: List[ConversationHistory]
    total_count: int

class PDFUploadResponse(BaseModel):
    message: str
    timestamp: str


class ChatRequest(BaseModel):
    question: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str