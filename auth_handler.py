from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, User, Transaction
from fastapi.encoders import jsonable_encoder
import datetime

router = APIRouter()

# In-memory session storage
user_sessions = {}

class LoginRequest(BaseModel):
    account_number: str
    password: str

# Dependency: Get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user and stores session data"""

    user = db.query(User).filter(User.account_number == request.account_number.strip()).first()
    
    if not user or str(user.password).strip() != str(request.password).strip():
        raise HTTPException(status_code=401, detail="Invalid credentials")

    transactions = db.query(Transaction).filter(Transaction.account_number == user.account_number).all()
    
    user_sessions[user.account_number] = {
        "customer": jsonable_encoder(user),
        "transactions": jsonable_encoder(transactions),  # ✅ FIX: Store transactions
        "login_time": datetime.datetime.now().isoformat()
    }
    
    return {"message": "Login successful", "user_data": user_sessions[user.account_number]}
