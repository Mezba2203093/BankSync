import sqlite3

DB_NAME = 'bank.db'


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS "Customer" (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS "Account" (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        account_type TEXT DEFAULT 'Savings',
        balance REAL DEFAULT 0.0,
        FOREIGN KEY (customer_id) REFERENCES "Customer"(customer_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS "Transaction" (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_account INTEGER,
        receiver_account INTEGER,
        transaction_type TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Completed',
        anomaly_score REAL,
        risk_level TEXT DEFAULT 'Normal',
        FOREIGN KEY (sender_account) REFERENCES "Account"(account_id),
        FOREIGN KEY (receiver_account) REFERENCES "Account"(account_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS "AI_Analysis" (
        analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER NOT NULL,
        anomaly_score REAL,
        risk_level TEXT,
        detection_reason TEXT,
        analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES "Transaction"(transaction_id)
    )''')

    conn.commit()
    conn.close()
    print("Database checked/initialized successfully!")


if __name__ == '__main__':
    init_db()
