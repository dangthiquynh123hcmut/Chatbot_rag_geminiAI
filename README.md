# RAG PDF Chatbot

A FastAPI-based chatbot that uses RAG (Retrieval-Augmented Generation) to answer questions from PDF documents.

### 1. Fork and Clone the Repository
```bash
cd Chatbot_rag_geminiAI
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root with the following variables:
```
MONGODB_URI
DB_NAME
COLLECTION_NAME
API_KEY
MODEL_NAME
```

### 3. Deploy to Render

### 4. Access Your Application
Once deployed, you'll get a URL like `https://chatbot-rag-geminiai.onrender.com`

## 📚 API Endpoints

- `POST /upload`: Upload PDF files
- `POST /chat`: Send chat messages
- `GET /conversations/{user_id}`: Get conversation history
- `GET /files`: List uploaded PDF files
- `DELETE /files/{file_id}`: Delete a PDF file
- `GET /health`: Health check endpoint

## 🔧 Local Development

1. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Development Server**:
   ```bash
   uvicorn run_api:app --reload
   ```

The API will be available at `http://localhost:8000`

## 🤖 RAG Pipeline
This application uses:
- Google's Generative AI for embeddings and chat
- FAISS for vector similarity search
- MongoDB for document storage
- FastAPI for the web server

## 📝 Notes
- The first request after deployment may take longer as Render spins up the instance
- Free tier has limitations on CPU and memory - consider upgrading for production use
- All PDF processing happens in memory - large files may cause timeouts
