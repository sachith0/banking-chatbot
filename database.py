import os
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"  # Use the environment variable

# Set up SQLAlchemy Engine and Session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# User Model
class User(Base):
    __tablename__ = "users"
    customer_id = Column(String, primary_key=True)
    name = Column(String)
    account_number = Column(String, unique=True)
    password = Column(String)

# Transaction Model
class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id = Column(String, primary_key=True)
    customer_id = Column(String)
    account_number = Column(String)
    date_time = Column(String)
    amount = Column(Integer)
    transaction_type = Column(String)
    method = Column(String)
    description = Column(String)
    balance_after_transaction = Column(Integer)

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
