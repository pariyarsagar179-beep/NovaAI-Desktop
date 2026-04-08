import os
import tempfile
import re

from fastapi import UploadFile
from pdf2image import convert_from_path
import pytesseract
import chromadb
from openai import OpenAI

# ---------- Tesseract Path ----------
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\pariy\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# ---------- OpenAI ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Chroma DB ----------
chroma_client = chromadb.PersistentClient(path="pdf_db")
collection = chroma_client.get_or_create_collection(
    name="pdf_knowledge",
    metadata={"hnsw:space": "cosine"}
)

# ---------- Helpers ----------
def clean_text(text: str) -> str:
    text = text.replace("\x0c", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text: str, max_length: int = 800):
    words = text.split()
    chunks = []
    current = []
    current_len = 0

    for w in words:
        if current_len + len(w) + 1 > max_length:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
        current.append(w)
        current_len += len(w) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks

# ---------- OCR PDF TEXT EXTRACTION ----------
def extract_text_from_pdf(file: UploadFile) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    extracted_text = ""

    try:
        # ⭐ FIXED POPPLER PATH
        pages = convert_from_path(
            tmp_path,
            dpi=300,
            poppler_path=r"C:\poppler\poppler-25.12.0\Library\bin"
        )

        for page in pages:
            text = pytesseract.image_to_string(page)
            extracted_text += text + "\n"

    except Exception as e:
        print("OCR extraction failed:", e)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return clean_text(extracted_text)

# ---------- ADD PDF TO KNOWLEDGE ----------
def add_pdf_to_knowledge(text: str, filename: str):
    if not text.strip():
        print(f"No text extracted from {filename} — skipping.")
        return

    chunks = chunk_text(text)

    for idx, chunk in enumerate(chunks):
        emb = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        ).data[0].embedding

        collection.add(
            ids=[f"{filename}__chunk_{idx}"],
            embeddings=[emb],
            documents=[chunk],
            metadatas=[{"source": filename}]
        )

# ---------- QUERY KNOWLEDGE ----------
def query_knowledge(question: str) -> str:
    q_emb = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[q_emb],
        n_results=5
    )

    if not results["documents"]:
        return ""

    docs = results["documents"][0]
    return "\n\n".join(docs)