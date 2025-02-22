import os
import time
import logging
import sqlite3
import requests
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from starlette.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest
from auth_handler import router as auth_router
from query_handler import router as query_router
from speech_handler import router as speech_router
from image_handler import router as image_router

# ✅ Load environment variables securely
load_dotenv()

# ✅ Access API keys & database paths
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH", "banking_data.db")  # Default if missing
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "app.log")

# ✅ Validate environment variables
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env file")

print(f"🔹 API Key Loaded: {GEMINI_API_KEY[:5]}*****")  # Hide API key for security
print(f"🔹 Database Path: {DATABASE_PATH}")

# ✅ Initialize FastAPI
app = FastAPI()

# ✅ Configure logging
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ✅ Prometheus Metrics
REQUEST_COUNT = Counter("api_requests_total", "Total API requests received")
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "API request latency")

# ✅ Middleware: Log Requests & Track Response Time
@app.middleware("http")
async def log_requests(request: Request, call_next):
    REQUEST_COUNT.inc()
    start_time = time.time()
    logger.info(f"📩 Received {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"❌ API Error: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)

    process_time = time.time() - start_time
    REQUEST_LATENCY.observe(process_time)
    logger.info(f"✅ Response: {response.status_code} | ⏱️ Time: {process_time:.4f} sec")

    return response

# ✅ Automate Database Setup: Check & Create Tables if Missing
def setup_database():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # ✅ Create transactions table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            amount REAL,
            transaction_type TEXT,
            date_time TEXT,
            method TEXT
        );
        """)

        # ✅ Create users table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        );
        """)

        conn.commit()
        conn.close()
        print("✅ Database setup complete!")

    except Exception as e:
        logger.error(f"❌ Database setup failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database setup failed")

setup_database()  # ✅ Run database setup on startup

# ✅ Expose Metrics for Monitoring
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

# ✅ Include Feature Routers
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(speech_router)
app.include_router(image_router)

# ✅ Automated Gemini API Call with Retry Logic
def call_gemini_api(payload, retries=3):
    headers = {"Content-Type": "application/json"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"⚠️ Gemini API failure (attempt {attempt+1}): {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed (attempt {attempt+1}): {str(e)}")

        time.sleep(2 ** attempt)  # Exponential backoff

    raise HTTPException(status_code=500, detail="Gemini API request failed after retries")

# ✅ Start API Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
