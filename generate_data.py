import database as db
import random
import time
from datetime import datetime, timedelta


def generate_normal_transactions(n=200):
    conn = db.get_connection()
    c = conn.cursor()

    c.execute('SELECT account_id FROM "Account"')
    accounts = [row[0] for row in c.fetchall()]

    if len(accounts) < 2:
        print(" Need at least 2 accounts. Create them in the app first.")
        conn.close()
        return

    print(f"Generating {n} normal transactions...")

    for _ in range(n):
        sender = random.choice(accounts)
        receiver = random.choice([a for a in accounts if a != sender])

        amount = round(random.gauss(200, 150), 2)
        amount = max(10, min(2000, amount))

        days_ago = random.randint(0, 30)
        timestamp = (datetime.now() - timedelta(days=days_ago)
                     ).strftime('%Y-%m-%d %H:%M:%S')

        c.execute('''
            INSERT INTO "Transaction"
                (sender_account, receiver_account, transaction_type, amount, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sender, receiver, 'Transfer', amount, timestamp, 'Completed'))

    conn.commit()
    conn.close()
    print(f" {n} normal transactions generated.")


def generate_anomalous_transactions(n=10):
    conn = db.get_connection()
    c = conn.cursor()

    c.execute('SELECT account_id FROM "Account"')
    accounts = [row[0] for row in c.fetchall()]

    if len(accounts) < 2:
        print(" Need at least 2 accounts. Create them in the app first.")
        conn.close()
        return

    print(f"Generating {n} anomalous transactions...")

    for i in range(n):
        sender = random.choice(accounts)
        receiver = random.choice([a for a in accounts if a != sender])

        if i % 2 == 0:
            amount = round(random.uniform(15000, 50000), 2)
            tx_type = 'Transfer'

        else:
            amount = round(random.uniform(0.01, 1.00), 2)
            tx_type = 'Transfer'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        c.execute('''
            INSERT INTO "Transaction"
                (sender_account, receiver_account, transaction_type, amount, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sender, receiver, tx_type, amount, timestamp, 'Completed'))

    conn.commit()
    conn.close()
    print(f" {n} anomalous transactions generated.")


if __name__ == '__main__':
    print("=" * 50)
    print("Generating BankSync test data...")
    print("=" * 50)
    generate_normal_transactions(200)
    generate_anomalous_transactions(10)
    print("\n✅ Done. Check your database with SELECT * FROM \"Transaction\";")
