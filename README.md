# RAG PDF Chatbot

A FastAPI-based chatbot that uses RAG (Retrieval-Augmented Generation) to answer questions from PDF documents.

## 🚀 Deployment on Render

### Prerequisites
- GitHub account
- Render account (sign up at [render.com](https://render.com/))
- MongoDB Atlas database (get a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register))
- Google AI API key (get it from [Google AI Studio](https://makersuite.google.com/))

### 1. Fork and Clone the Repository
```bash
git clone https://github.com/your-username/rag-pdf-chatbot.git
cd rag-pdf-chatbot
```

### 2. Set Up Environment Variables
Create a `.env` file with the following variables:
```
MONGODB_URI=your_mongodb_connection_string
DB_NAME=pdf_chatbot
COLLECTION_NAME=pdf_files
API_KEY=your_google_ai_api_key
MODEL_NAME=Google AI
```

### 3. Deploy to Render
1. Push your code to a GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New +" and select "Web Service"
4. Connect your GitHub repository
5. Configure the service:
   - Name: `rag-pdf-chatbot` (or your preferred name)
   - Region: Choose the one closest to your users
   - Branch: `main` (or your preferred branch)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn run_api:app --host=0.0.0.0 --port=$PORT`
6. Add environment variables from your `.env` file
7. Click "Create Web Service"

### 4. Access Your Application
Once deployed, you'll get a URL like `https://rag-pdf-chatbot.onrender.com`

## 📚 API Endpoints

- `POST /upload`: Upload PDF files
- `POST /chat`: Send chat messages
- `GET /conversations/{user_id}`: Get conversation history
- `GET /files`: List uploaded PDF files
- `DELETE /files/{file_id}`: Delete a PDF file

## 🔧 Local Development

1. Create and activate virtual environment:
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
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
