from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
from gridfs import GridFS
import os
import io
from PyPDF2 import PdfReader
# Import các hàm xử lý từ app.py
from app import get_text_chunks, get_vector_store, get_conversational_chain, GoogleGenerativeAIEmbeddings, FAISS

# Import MongoDB configuration
from config import db

app = FastAPI(title="PDF Chatbot API")

# Cấu hình CORS để cho phép truy cập từ các domain khác
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các origins
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các HTTP methods
    allow_headers=["*"],  # Cho phép tất cả các headers
)

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

class ChatRequest(BaseModel):
    question: str

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

@app.post("/upload-pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...), user_id: str = Form(None)):
    try:
        # Khởi tạo GridFS
        fs = GridFS(db)
        
        file_infos = []
        for file in files:
            # Đọc nội dung file
            content = await file.read()
            
            # Lưu file vào GridFS
            file_id = fs.put(content, filename=file.filename, content_type=file.content_type)
            
            # Lưu thông tin file vào MongoDB
            file_info = {
                "filename": file.filename,
                "upload_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "user_id": user_id,
                "file_id": str(file_id),
                "size": len(content),
                "metadata": {
                    "content_type": file.content_type
                }
            }
            
            # Lưu vào MongoDB
            result = db.files.insert_one(file_info)
            file_info["_id"] = str(result.inserted_id)
            file_infos.append(file_info)
            
        return {"message": "PDF files uploaded successfully", "files": file_infos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_with_pdfs(request: ChatRequest):
    try:
        # Lấy API key và model name từ environment
        api_key = os.getenv('API_KEY')
        model_name = os.getenv('MODEL_NAME', 'Google AI')
        
        if not api_key:
            raise HTTPException(status_code=500, detail="API key is not configured in environment variables")

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_with_pdfs(request: ChatRequest, user_id: str = Form(None)):
    try:
        # Lấy API key và model name từ environment
        api_key = os.getenv('API_KEY')
        model_name = os.getenv('MODEL_NAME', 'Google AI')
        
        if not api_key:
            raise HTTPException(status_code=500, detail="API key is not configured in environment variables")

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

@app.get("/conversations")
async def get_conversations(user_id: str, limit: int = 10, page: int = 1):
    try:
        # Tính toán offset cho phân trang
        skip = (page - 1) * limit
        
        # Lấy lịch sử cuộc trò chuyện
        conversations = list(db.conversations.find({"user_id": user_id})
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit))
        
        # Đếm tổng số cuộc trò chuyện
        total_count = db.conversations.count_documents({"user_id": user_id})
        
        # Format dữ liệu trả về
        formatted_conversations = []
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
            formatted_conversations.append(conv)
        
        return ConversationHistoryResponse(
            conversations=formatted_conversations,
            total_count=total_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
