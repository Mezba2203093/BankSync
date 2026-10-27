import database as db


def fix_balances():
    conn = db.get_connection()
    c = conn.cursor()

    print("Recalculating balances from transaction history...")

    # 1. Reset all account balances to 0
    c.execute('UPDATE "Account" SET balance = 0')

    # 2. Add all incoming money (Deposits and Transfers received)
    c.execute('''
        UPDATE "Account" 
        SET balance = balance + (
            SELECT COALESCE(SUM(amount), 0) 
            FROM "Transaction" 
            WHERE receiver_account = "Account".account_id
        )
    ''')

    # 3. Subtract all outgoing money (Withdrawals and Transfers sent)
    c.execute('''
        UPDATE "Account" 
        SET balance = balance - (
            SELECT COALESCE(SUM(amount), 0) 
            FROM "Transaction" 
            WHERE sender_account = "Account".account_id
        )
    ''')

    conn.commit()
    conn.close()
    print(" Balances successfully recalculated!")


if __name__ == '__main__':
    fix_balances()
