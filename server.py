from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = FastAPI()

# Allow Electron frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# MEMORY SYSTEM (last 30 msgs)
# -----------------------------
conversation_history = []
MEMORY_LIMIT = 30

def add_to_memory(role, content):
    conversation_history.append({"role": role, "content": content})
    if len(conversation_history) > MEMORY_LIMIT:
        conversation_history.pop(0)

def build_context():
    context = (
        "You are Nova, an advanced trading mentor. "
        "Your tone is precise, technical, and structured. "
        "You explain market structure, liquidity, BOS/CHoCH, FVGs, trends, and entries clearly. "
        "You analyze charts like a professional trader. "
        "You do NOT introduce yourself unless asked.\n\n"
        "Conversation history:\n"
    )

    for msg in conversation_history:
        role = "User" if msg["role"] == "user" else "Nova"
        context += f"{role}: {msg['content']}\n"

    context += "\nNova:"
    return context


# -----------------------------
# MODELS
# -----------------------------
class Message(BaseModel):
    text: str

class ChartAnalysis(BaseModel):
    candles: list  # list of OHLC candles
    question: str


# -----------------------------
# MAIN CHAT ENDPOINT
# -----------------------------
@app.post("/ask")
def ask_ai(message: Message):

    # Add user message to memory
    add_to_memory("user", message.text)

    # Build Nova's context
    system_prompt = build_context()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message.text}
        ]
    )

    reply = response.choices[0].message.content

    # Add Nova's reply to memory
    add_to_memory("ai", reply)

    return {"reply": reply}


# -----------------------------
# CHART ANALYSIS ENDPOINT
# -----------------------------
@app.post("/analyze_chart")
def analyze_chart(data: ChartAnalysis):

    candles = data.candles
    question = data.question

    # Convert candles to readable text
    candle_text = ""
    for c in candles:
        candle_text += (
            f"Time: {c['time']}, O: {c['open']}, H: {c['high']}, "
            f"L: {c['low']}, C: {c['close']}\n"
        )

    prompt = (
        "Analyze the following candlestick data like a professional trader. "
        "Identify trends, liquidity zones, BOS/CHOCH, imbalances, and possible setups.\n\n"
        f"Candles:\n{candle_text}\n\n"
        f"User question: {question}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Nova, an elite trading analyst."},
            {"role": "user", "content": prompt}
        ]
    )

    reply = response.choices[0].message.content
    return {"analysis": reply}