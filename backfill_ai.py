import sqlite3
import database as db
import ai_model


def backfill():
    conn = db.get_connection()
    c = conn.cursor()

    # Reset all previous AI scores so we start fresh
    print("Resetting all transaction scores to Normal...")
    c.execute(
        'UPDATE "Transaction" SET anomaly_score = 0.0, risk_level = \'Normal\'')
    c.execute('DELETE FROM "AI_Analysis"')
    conn.commit()

    # Get EVERY single transaction from the database
    c.execute(
        'SELECT transaction_id, amount, sender_account, timestamp FROM "Transaction"')
    rows = c.fetchall()
    print(f"Analyzing ALL {len(rows)} transactions...")

    flagged = 0
    for tx_id, amount, sender, ts in rows:
        sender_id = sender if sender else 1
        score, risk, reason = ai_model.score_transaction(amount, sender_id, ts)

        # Update the transaction
        c.execute(
            'UPDATE "Transaction" SET anomaly_score = ?, risk_level = ? WHERE transaction_id = ?',
            (score, risk, tx_id)
        )

        # If it's an anomaly, save the details
        if risk != 'Normal':
            c.execute('''
                INSERT INTO "AI_Analysis"
                    (transaction_id, anomaly_score, risk_level, detection_reason)
                VALUES (?, ?, ?, ?)
            ''', (tx_id, score, risk, reason))
            flagged += 1

    conn.commit()
    conn.close()
    print(f" Done! Flagged {flagged} anomalous transactions.")


if __name__ == '__main__':
    backfill()
