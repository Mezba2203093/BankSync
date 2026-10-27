import pandas as pd
import numpy as np
import pickle
import os
import database as db
from sklearn.ensemble import IsolationForest

MODEL_PATH = 'model.pkl'


def load_transactions():
    conn = db.get_connection()
    df = pd.read_sql_query('SELECT * FROM "Transaction"', conn)
    conn.close()
    return df


def engineer_features(df):
    df = df.copy()
    df['amount'] = df['amount'].astype(float)

    df['log_amount'] = np.log1p(df['amount'])

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['hour'] = df['timestamp'].dt.hour.fillna(12)

    freq = df.groupby('sender_account').size()
    df['sender_freq'] = df['sender_account'].map(freq).fillna(0)

    median = df['amount'].median()
    df['amount_deviation'] = (df['amount'] - median).abs()

    return df


def train_model():
    print("Loading transactions from database...")
    df = load_transactions()

    if len(df) < 20:
        print(" Need at least 20 transactions to train. Run generate_data.py first.")
        return False

    print(f"Training on {len(df)} transactions...")
    df = engineer_features(df)

    features = ['log_amount', 'hour', 'sender_freq', 'amount_deviation']
    X = df[features].values

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,   # expect ~5% anomalies
        random_state=42
    )
    model.fit(X)

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump((model, features), f)

    print(f" Model trained and saved to {MODEL_PATH}")
    return True


def score_transaction(amount, sender_account, timestamp=None):
    if not os.path.exists(MODEL_PATH):
        return 0.0, 'Normal', 'Model not trained'

    with open(MODEL_PATH, 'rb') as f:
        model, features = pickle.load(f)

    df = load_transactions()
    df = engineer_features(df)

    median = df['amount'].median() if len(df) else 0
    freq = df.groupby('sender_account').size().get(sender_account, 1)

    if timestamp is None:
        timestamp = pd.Timestamp.now()
    else:
        timestamp = pd.to_datetime(timestamp, errors='coerce')
    hour = timestamp.hour if not pd.isna(timestamp) else 12

    row = pd.DataFrame([{
        'log_amount': np.log1p(amount),
        'hour': hour,
        'sender_freq': freq,
        'amount_deviation': abs(amount - median)
    }])[features]

    pred = model.predict(row.values)[0]
    raw = model.decision_function(row.values)[0]

    # --- NEW STRICT RULES ---
    if amount > 10000:
        return 0.95, 'High', f"Extreme amount detected (${amount:,.2f})"
    elif amount < 1.00:
        return 0.75, 'Medium', f"Micro-transaction detected (${amount:,.2f})"

    # --- AI MODEL PREDICTION ---
    if pred == -1:
        score = float(np.clip(0.5 - raw, 0.5, 1.0))
        if score >= 0.85:
            risk = 'High'
            reason = f"Unusual pattern (score={score:.2f})"
        elif score >= 0.7:
            risk = 'Medium'
            reason = f"Suspicious pattern (score={score:.2f})"
        else:
            risk = 'Low'
            reason = f"Mildly unusual (score={score:.2f})"
        return score, risk, reason

    return 0.0, 'Normal', 'Within normal behavior'


if __name__ == '__main__':
    train_model()
