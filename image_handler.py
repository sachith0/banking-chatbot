from fastapi import APIRouter, HTTPException, UploadFile, File
import requests
import os
import sqlite3
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
from auth_handler import user_sessions  # Import session storage

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

GEMINI_API_KEY = "AIzaSyA8btcq5oLVtm0Pdg0kuuIgCAAkoTebmIs"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

DB_PATH = "/Users/sachiths/Documents/Telegrambot/banking_data.db"

# ✅ Extract Text from Image (OCR)
def extract_text_from_image(image_bytes: bytes) -> str:
    """Extracts text from an image using OCR with preprocessing."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("L")  # Grayscale for better OCR
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        image = image.filter(ImageFilter.SHARPEN)

        extracted_text = pytesseract.image_to_string(image, lang="hin+eng+kan+tam+ben")
        return extracted_text.strip()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing error: {str(e)}")

# ✅ Detect Transaction-Related Queries
def is_transaction_query(text: str) -> bool:
    keywords = ["transaction", "amount", "balance", "statement", "credited", "debited"]
    return any(word in text.lower() for word in keywords)

# ✅ Fetch Transactions from Database
def fetch_transaction_details():
    """Fetch last transaction details from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT transaction_id, amount, transaction_type, date_time, method FROM transactions ORDER BY date_time DESC LIMIT 1;")
        last_transaction = cursor.fetchone()
        conn.close()

        if last_transaction:
            return {
                "transaction_id": last_transaction[0],
                "amount": last_transaction[1],
                "transaction_type": last_transaction[2],
                "date_time": last_transaction[3],
                "method": last_transaction[4]
            }
        else:
            return "No transactions found."

    except Exception as e:
        return f"Error querying database: {str(e)}"

# ✅ Main API Endpoint
@router.post("/image-to-chatbot")
async def image_to_chatbot(image_file: UploadFile = File(...)):
    """Automates text extraction, database lookup, and AI response."""

    # ✅ Step 1: Validate User Session
    if not user_sessions:
        raise HTTPException(status_code=403, detail="No active session. Please log in first.")

    last_logged_in_user = list(user_sessions.keys())[-1]
    user_data = user_sessions[last_logged_in_user]

    # ✅ Step 2: Process Image & Extract Text
    image_bytes = await image_file.read()
    extracted_text = extract_text_from_image(image_bytes)

    # ✅ Step 3: Check if it's a Transaction Query
    transaction_details = None
    if is_transaction_query(extracted_text):
        transaction_details = fetch_transaction_details()

    # ✅ Step 4: Prepare API Request for Gemini
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [
                {"text": f"""
                You are a banking assistant. Answer concisely.

                **User Details:** {user_data['customer']}
                **Last Transaction:** {transaction_details if transaction_details else "No recent transactions."}

                Here is a scanned bank document. Extract transaction details:

                **Extracted Text:**
                {extracted_text}
                """}
            ]
        }]
    }

    # ✅ Step 5: Send API Request to Gemini
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            llm_response = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        else:
            llm_response = f"LLM API Error: {response.status_code} - {response.text}"

    except requests.exceptions.RequestException as e:
        llm_response = f"Request failed: {str(e)}"

    # ✅ Step 6: Return Final Response
    return {
        "extracted_text": extracted_text,
        "database_response": transaction_details if transaction_details else "Not a transaction-related query.",
        "llm_response": llm_response
    }
