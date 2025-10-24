import os
from datetime import datetime

from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI(title="CodeCleaner Backend")


class CodePayload(BaseModel):
    cleaned_code: str


SAVE_DIR = "received_codes"
os.makedirs(SAVE_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"status": "ok", "message": "CodeCleaner backend is running!"}


@app.post("/upload_code/")
def receive_code(data: CodePayload):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SAVE_DIR}/cleaned_{timestamp}.py"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(data.cleaned_code)

    print(f"[INFO] Received code saved to: {filename}")
    return {
        "status": "success",
        "message": f"Code received and saved to {filename}",
        "filename": filename
    }


@app.post("/analyze_code/")
async def analyze_code(request: Request):
    """Ek uç nokta: İleride kodu analiz etmek istersen kullanılabilir"""
    data = await request.json()
    code = data.get("cleaned_code", "")
    lines = len(code.splitlines())
    chars = len(code)
    return {
        "status": "ok",
        "lines": lines,
        "characters": chars,
        "message": "Code analyzed successfully"
    }

