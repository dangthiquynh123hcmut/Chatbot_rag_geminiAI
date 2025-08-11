from fastapi import UploadFile, File, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from gridfs import GridFS
import os
import io
from PyPDF2 import PdfReader

# Import models
from models.api import (
    TokenResponse, 
    UserResponse, 
    RegisterRequest,  
    ChatRequest, 
    ChatResponse, 
)
from models.auth import User, LoginRequest

# Import config and auth
from config import app, db, ACCESS_TOKEN_EXPIRE_MINUTES
from auth import (
    get_current_active_user, 
    get_admin_user,
    get_password_hash, 
    create_access_token, 
    authenticate_user
)

# Import app functions
from app import get_text_chunks, get_vector_store, get_conversational_chain, GoogleGenerativeAIEmbeddings, FAISS

# Authentication endpoints
@app.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: RegisterRequest):
    # Check if username already exists
    if db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user document
    user_dict = user_data.dict()
    user_dict.pop('password')  # Remove plain password
    user_dict['hashed_password'] = hashed_password
    user_dict['created_at'] = datetime.utcnow()
    
    # Insert user into database
    result = db.users.insert_one(user_dict)
    
    # Return created user
    created_user = db.users.find_one({"_id": result.inserted_id})
    created_user['id'] = str(created_user.pop('_id'))
    return created_user

@app.post("/login/", response_model=TokenResponse)
async def login_for_access_token(form_data: LoginRequest ):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "is_admin": user.is_admin}, 
        expires_delta=access_token_expires
    )
    
    # Convert user to dict and remove sensitive data
    user_dict = user.dict()
    user_dict['id'] = str(user_dict.pop('_id', user_dict.get('id', '')))

    user_dict.pop('hashed_password', None)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user_dict
    }

# Protected endpoints
@app.post("/upload-pdfs/")
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload PDF files to the server and store them in the database.
    Requires authentication.
    """
    try:
        # Initialize GridFS
        fs = GridFS(db)
        
        uploaded_files = []
        
        for file in files:
            # Read file contents
            contents = await file.read()
            
            # Save file to GridFS
            file_id = fs.put(
                contents,
                filename=file.filename,
                content_type=file.content_type,
                uploadDate=datetime.utcnow(),
                user_id=current_user.username
            )
            
            # Prepare file info for database
            file_info = {
                "filename": file.filename,
                "upload_date": datetime.utcnow(),
                "user_id": current_user.username,
                "file_id": str(file_id),
                "metadata": {
                    "content_type": file.content_type,
                    "size": len(contents)
                }
            }
            
            # Save to database
            result = db.files.insert_one(file_info)
            file_info["id"] = str(result.inserted_id)
            
            uploaded_files.append(file_info)
        
        return {
            "message": "Files uploaded successfully",
            "uploaded_files": uploaded_files,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading files: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse)
async def chat_with_pdfs(request: ChatRequest):
    try:
        # Lấy API key và model name từ environment
        api_key = os.getenv('API_KEY')
        model_name = os.getenv('MODEL_NAME', 'Google AI')
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key not configured"
            )

        # Lấy tất cả file PDF từ MongoDB
        files = list(db.files.find())
        if not files:
            raise HTTPException(status_code=400, detail="No PDF files uploaded")
        
        # Tạo GridFS để đọc file
        fs = GridFS(db)
        
        # Đọc và xử lý PDF trực tiếp từ GridFS
        text = ""
        for file in files:
            try:
                # Đọc file từ GridFS
                grid_file = fs.get(ObjectId(file["file_id"]))
                # Đọc nội dung PDF trực tiếp từ bộ nhớ
                with io.BytesIO(grid_file.read()) as pdf_file:
                    # Đọc PDF trực tiếp từ BytesIO
                    pdf_reader = PdfReader(pdf_file)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
            except Exception as e:
                print(f"Lỗi khi đọc file: {str(e)}")
                continue
        if not text.strip():
            raise HTTPException(status_code=400, detail="Không thể đọc nội dung từ file PDF")
        
        text_chunks = get_text_chunks(text, model_name)
        vector_store = get_vector_store(text_chunks, model_name, api_key)
        
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(request.question)
        chain = get_conversational_chain(model_name, vectorstore=new_db, api_key=api_key)
        response = chain({"input_documents": docs, "question": request.question}, return_only_outputs=True)
        
        return ChatResponse(
            answer=response['output_text'],
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            model_name=model_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user/chat", response_model=ChatResponse)
async def user_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Get API key and model name from environment
        api_key = os.getenv('API_KEY')
        model_name = os.getenv('MODEL_NAME', 'Google AI')
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key not configured"
            )
        
        # Initialize embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )

        
        # Load vector store from FAISS
        try:
            vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vector store not found. Please upload PDFs first. Error: {str(e)}"
            )
        
        # Create conversation chain
        chain = get_conversational_chain(vector_store, api_key)
        
        # Process the question
        response = chain({"question": request.question, "chat_history": []})
        
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(request.question)
        chain = get_conversational_chain(model_name, vectorstore=new_db, api_key=api_key)
        response = chain({"input_documents": docs, "question": request.question}, return_only_outputs=True)
        
        # Lưu lịch sử cuộc trò chuyện vào MongoDB
        conversation = {
            "user_id": user_id,
            "question": request.question,
            "answer": response['output_text'],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "model_name": model_name
        }
        db.conversations.insert_one(conversation)
        
        return ChatResponse(
            answer=response['output_text'],
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            model_name=model_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

@app.get("/conversations/me/", response_model=List[Dict[str, Any]])
async def get_user_conversations(
    limit: int = 10,
    page: int = 1,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get chat history for the current authenticated user
    """
    skip = (page - 1) * limit
    conversations = list(
        db.conversations
        .find({"user_id": current_user.username})
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    
    # Convert ObjectId to string for JSON serialization
    for conv in conversations:
        conv["_id"] = str(conv["_id"])
    
    return conversations

@app.get("/conversations/all/", response_model=List[Dict[str, Any]])
async def get_all_conversations(
    limit: int = 10,
    page: int = 1,
    current_user: User = Depends(get_admin_user)
):
    """
    Get all chat history (admin only)
    """
    skip = (page - 1) * limit
    conversations = list(
        db.conversations
        .find()
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    
    # Convert ObjectId to string for JSON serialization
    for conv in conversations:
        conv["_id"] = str(conv["_id"])
    
    return conversations

@app.get("/pdf-files")
async def list_pdf_files(user_id: Optional[str] = None):
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        files = list(db.files.find(query))
        for file in files:
            file["_id"] = str(file["_id"])
            file["file_id"] = str(file["file_id"])
        
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/pdf-files/{file_id}")
async def delete_pdf_file(file_id: str):
    try:
        # Khởi tạo GridFS
        fs = GridFS(db)
        
        # Xóa file từ GridFS
        try:
            fs.delete(ObjectId(file_id))
        except:
            pass
            
        # Xóa thông tin file từ MongoDB
        result = db.files.delete_one({"file_id": file_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        return {"message": "PDF file deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
