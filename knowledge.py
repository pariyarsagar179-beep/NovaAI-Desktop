import os
from chromadb import PersistentClient
from fastapi import UploadFile
from PyPDF2 import PdfReader
from openai import OpenAI

# OCR imports
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile

# Your real key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# Ensure vector store directory exists
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_DIR = os.path.join(BASE_DIR, "vector_store", "chroma")
os.makedirs(VECTOR_DIR, exist_ok=True)

# Chroma persistent client
chroma_client = PersistentClient(path=VECTOR_DIR)
collection = chroma_client.get_or_create_collection("nova_knowledge")


# ---------------------------------------------------------
# OCR-POWERED PDF TEXT EXTRACTION (NEW)
# ---------------------------------------------------------
def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Extracts text from ANY PDF:
    - normal text PDFs
    - scanned PDFs
    - image-based PDFs
    - chart screenshots inside PDFs
    """

    # Save uploaded PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    extracted_text = ""

    try:
        # Convert PDF pages to images
        pages = convert_from_path(tmp_path, dpi=300)

        for page in pages:
            # OCR each page
            text = pytesseract.image_to_string(page)
            extracted_text += text + "\n\n"

    except Exception as e:
        print("OCR extraction failed:", e)

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return extracted_text.strip()


# ---------------------------------------------------------
# EMBEDDING
# ---------------------------------------------------------
def embed_text(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# ---------------------------------------------------------
# ADD PDF TO KNOWLEDGE
# ---------------------------------------------------------
def add_pdf_to_knowledge(text: str, filename: str):
    if not text.strip():
        text = "NO_TEXT_EXTRACTED"

    embedding = embed_text(text)

    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[filename]
    )


# ---------------------------------------------------------
# QUERY KNOWLEDGE
# ---------------------------------------------------------
def query_knowledge(question: str):
    q_embed = embed_text(question)

    results = collection.query(
        query_embeddings=[q_embed],
        n_results=3
    )

    if not results["documents"]:
        return "No relevant knowledge found."

    docs = results["documents"][0]
    combined = "\n\n".join(docs)
    return combined