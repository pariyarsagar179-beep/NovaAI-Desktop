import os
import json
import base64
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from openai import OpenAI

from test_knowledge import (
    extract_text_from_pdf,
    add_pdf_to_knowledge,
    query_knowledge,
    collection,
)

# ---------- Paths ----------
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
LOG_DIR = os.path.join(ROOT_DIR, "logs")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

os.makedirs(LOG_DIR, exist_ok=True)

# ---------- Logging ----------
LOG_FILE = os.path.join(LOG_DIR, "nova.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("nova")

# ---------- Config ----------
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

config = load_config()
username = config.get("username", None)

# ---------- OpenAI ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- FULL NOVA CHART ANALYSIS PROMPT ----------
BASE_PROMPT = """
You are Nova, a professional price action trader and chart analyst.

STRICT FORMATTING RULES (MUST FOLLOW):
- Every section MUST start on a NEW LINE.
- After every heading, insert a FORCED line break using: \n
- After every section, insert TWO forced line breaks: \n\n
- NEVER place a heading and bullet points on the same line.
- NEVER merge multiple sections together.
- NEVER write paragraphs.
- ALWAYS use bullet points under each heading.

OUTPUT FORMAT (FOLLOW EXACTLY):

### 1. Trend Direction
- Bullet point
- Bullet point

\n\n

### 2. Market Structure (HH, HL, LH, LL, BOS, CHOCH)
- Bullet point
- Bullet point

\n\n

### 3. Liquidity Zones
- Bullet point
- Bullet point

\n\n

### 4. Imbalances (FVG)
- Bullet point
- Bullet point

\n\n

### 5. Supply & Demand Zones
- Bullet point
- Bullet point

\n\n

### 6. Displacement
- Bullet point
- Bullet point

\n\n

### 7. Pullbacks / Retracements
- Bullet point
- Bullet point

\n\n

### 8. Support & Resistance
- Bullet point
- Bullet point

\n\n

### 9. Candlestick Patterns
- Bullet point
- Bullet point

\n\n

### 10. Breakouts / Retests / Fakeouts
- Bullet point
- Bullet point

\n\n

### 11. Volume Context
- Bullet point
- Bullet point

\n\n

### 12. Bullish Scenario
- Bullet point
- Bullet point

\n\n

### 13. Bearish Scenario
- Bullet point
- Bullet point

\n\n

### 14. Final Bias
- Bullet point (Bullish / Bearish / Neutral)

\n\n

ALWAYS follow this exact structure.
ALWAYS keep spacing.
ALWAYS use bullet points.
NEVER merge sections.
"""

# ---------- FastAPI ----------
app = FastAPI(title="NovaAI Backend")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- AI CALL FOR CHARTS ----------
def call_ai_model(prompt: str, image_bytes: bytes) -> str:
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": BASE_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        },
                    },
                ],
            },
        ],
    )

    return response.choices[0].message.content.strip()

# ---------- ROUTES ----------
@app.get("/health")
async def health():
    return {"status": "ok", "username": username}

@app.post("/predict")
async def predict(images: list[UploadFile] = File(...), question: str = Form("")):
    try:
        results = []
        for img in images:
            img_bytes = await img.read()
            analysis = call_ai_model(question, img_bytes)
            results.append(analysis)
        return {"answer": "\n\n".join(results)}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}

@app.post("/ask_charts")
async def ask_charts(images: list[UploadFile] = File(...), question: str = Form("")):
    try:
        results = []
        for img in images:
            img_bytes = await img.read()
            analysis = call_ai_model(question, img_bytes)
            results.append(analysis)
        return {"answer": "\n\n".join(results)}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}

@app.post("/upload_pdf")
async def upload_pdf(pdf: UploadFile = File(...)):
    try:
        text = extract_text_from_pdf(pdf)
        add_pdf_to_knowledge(text, pdf.filename)
        return {"message": f"{pdf.filename} learned successfully."}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}

@app.get("/knowledge_files")
async def knowledge_files():
    try:
        data = collection.get()
        metas = data.get("metadatas", [])
        files = sorted({m.get("source") for m in metas if m and "source" in m})
        return {"files": list(files)}
    except Exception:
        return {"files": []}

@app.post("/delete_pdf")
async def delete_pdf(filename: str = Form(...)):
    try:
        data = collection.get()
        ids = data.get("ids", [])
        to_delete = [i for i in ids if i.startswith(f"{filename}__chunk_")]
        if to_delete:
            collection.delete(ids=to_delete)
        return {"message": f"{filename} deleted from knowledge."}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}

@app.post("/ask_pdf")
async def ask_pdf(question: str = Form(...)):
    try:
        context = query_knowledge(question)

        if not context.strip():
            data = collection.get()
            docs_nested = data.get("documents", [])
            flat_docs = [d for sub in docs_nested for d in sub] if docs_nested else []

            full_text = "\n".join(flat_docs).strip()
            if not full_text:
                return {
                    "answer": "Your PDFs are uploaded, but I couldn't extract readable text from them."
                }

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are Nova. Summarize the user's uploaded trading PDFs."
                    },
                    {
                        "role": "user",
                        "content": f"Here is the combined text from the user's PDFs:\n{full_text}\n\nGive a clear, concise summary."
                    },
                ],
            )

            return {"answer": response.choices[0].message.content.strip()}

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are Nova. Use ONLY the context from the user's uploaded PDFs to answer."
                },
                {
                    "role": "user",
                    "content": f"Context from PDFs:\n{context}\n\nQuestion: {question}"
                },
            ],
        )

        return {"answer": response.choices[0].message.content.strip()}

    except Exception as e:
        return {"answer": f"Error: {str(e)}"}