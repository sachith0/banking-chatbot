import sqlite3
import pandas as pd

# Define file paths
DB_PATH = "/Users/sachiths/Documents/Telegrambot copy/banking_data.db"
CUSTOMERS_CSV = "/Users/sachiths/Documents/Telegrambot copy/1000_customers_data.csv"
TRANSACTIONS_CSV = "/Users/sachiths/Documents/Telegrambot copy/100000_transactiondata.csv"

# Connect to SQLite
db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# Create 'users' table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    customer_id TEXT PRIMARY KEY,
    name TEXT,
    account_number TEXT UNIQUE,
    ifsc_code TEXT,
    account_city TEXT,
    account_type TEXT,
    status TEXT,
    contact TEXT,
    password TEXT,
    created_at TEXT
)
''')

# Create 'transactions' table
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT,
    account_number TEXT,
    date_time TEXT,
    amount INTEGER,
    transaction_type TEXT,
    method TEXT,
    description TEXT,
    balance_after_transaction INTEGER
)
''')

db.commit()

# Load and insert customer data
try:
    customers_df = pd.read_csv(CUSTOMERS_CSV)
    print("📌 Customers Data Sample:\n", customers_df.head())  # Debugging line
    customers_df.to_sql("users", db, if_exists="replace", index=False)
    print("✅ Customers data inserted successfully.")
except Exception as e:
    print("❌ Error inserting customers data:", e)

# Load and insert transaction data
try:
    transactions_df = pd.read_csv(TRANSACTIONS_CSV)
    print("📌 Transactions Data Sample:\n", transactions_df.head())  # Debugging line
    transactions_df.to_sql("transactions", db, if_exists="replace", index=False)
    print("✅ Transactions data inserted successfully.")
except Exception as e:
    print("❌ Error inserting transactions data:", e)

print("✅ Database setup completed successfully.")
db.close()
