from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from io import BytesIO

# Update imports for LangChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS

from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

from datetime import datetime

def extract_text_with_ocr(pdf_bytes, filename):
    """Extract text from scanned PDF using OCR"""
    try:
        # Convert PDF to list of images
        images = convert_from_bytes(pdf_bytes)
        text = ""
        
        # Process OCR for each page
        for i, image in enumerate(images):
            # Use Vietnamese and English language packs
            page_text = pytesseract.image_to_string(image, lang='vie+eng')
            if page_text.strip():
                text += f"\n--- Trang {i+1} ---\n{page_text}\n"
        
        return text.strip()
    except Exception as e:
        print(f"Lỗi khi xử lý OCR cho file {filename}: {str(e)}")
        return ""

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            # Read PDF content into memory
            pdf_bytes = pdf.file.read()
            
            # First try to extract text directly
            try:
                pdf_reader = PdfReader(BytesIO(pdf_bytes))
                page_texts = []
                has_text = False
                
                for page in pdf_reader.pages:
                    page_content = page.extract_text()
                    if page_content and page_content.strip():
                        page_texts.append(page_content)
                        has_text = True
                    else:
                        # If a page has no text, it might be a scanned page
                        break
                
                if has_text and len(page_texts) == len(pdf_reader.pages):
                    # All pages have text, use direct extraction
                    text += "\n\n".join(page_texts) + "\n\n"
                else:
                    # Some or all pages are scanned, use OCR
                    print(f"Phát hiện file scan, đang sử dụng OCR cho: {pdf.filename}")
                    text += extract_text_with_ocr(pdf_bytes, pdf.filename) + "\n\n"
                    
            except Exception as e:
                print(f"Lỗi khi đọc file {pdf.filename} bằng PyPDF2, đang thử dùng OCR: {str(e)}")
                text += extract_text_with_ocr(pdf_bytes, pdf.filename) + "\n\n"
                
        except Exception as e:
            print(f"Lỗi khi xử lý file {pdf.filename}: {str(e)}")
            continue
            
    return text.strip()

def get_text_chunks(text, model_name):
    if model_name == "Google AI":
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks, model_name, api_key=None):
    if model_name == "Google AI":
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")
    return vector_store

def get_conversational_chain(model_name, vectorstore=None, api_key=None):
    if model_name == "Google AI":
        prompt_template = """
        Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
        provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
        Context:\n {context}?\n
        Question: \n{question}\n

        Answer:
        """
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3, google_api_key=api_key)
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
        return chain

def user_input(user_question, model_name, api_key, pdf_docs, conversation_history):
    text_chunks = get_text_chunks(get_pdf_text(pdf_docs), model_name)
    vector_store = get_vector_store(text_chunks, model_name, api_key)
    user_question_output = ""
    response_output = ""
    if model_name == "Google AI":
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)
        chain = get_conversational_chain("Google AI", vectorstore=new_db, api_key=api_key)
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        user_question_output = user_question
        response_output = response['output_text']
        pdf_names = [pdf.name for pdf in pdf_docs] if pdf_docs else []
        conversation_history.append((user_question_output, response_output, model_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ", ".join(pdf_names))) 
    
    # if len(st.session_state.conversation_history) > 0:
    #     df = pd.DataFrame(st.session_state.conversation_history, columns=["Question", "Answer", "Model", "Timestamp", "PDF Name"])
    #     csv = df.to_csv(index=False)
    #     b64 = base64.b64encode(csv.encode()).decode()  # Convert to base64
    #     href = f'<a href="data:file/csv;base64,{b64}" download="conversation_history.csv"><button>Download conversation history as CSV file</button></a>'
    # st.snow()