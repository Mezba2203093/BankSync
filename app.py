from flask import Flask, render_template, request, redirect, url_for
import database as db
import sqlite3

app = Flask(__name__)

# ---------- HOME ----------


@app.route('/')
def index():
    return render_template('index.html')

# ---------- CREATE ACCOUNT ----------


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        account_type = request.form.get('account_type', 'Savings')
        initial_deposit = float(request.form.get('initial_deposit', 0))

        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'INSERT INTO "Customer" (name, email, phone) VALUES (?, ?, ?)',
                (name, email, phone)
            )
            customer_id = cursor.lastrowid

            cursor.execute(
                'INSERT INTO "Account" (customer_id, account_type, balance) VALUES (?, ?, ?)',
                (customer_id, account_type, initial_deposit)
            )
            account_id = cursor.lastrowid

            if initial_deposit > 0:
                cursor.execute('''
                    INSERT INTO "Transaction" (sender_account, receiver_account, transaction_type, amount, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (None, account_id, 'Deposit', initial_deposit, 'Completed'))

            conn.commit()
            return f"""
                <h2>✅ Account Created Successfully!</h2>
                <p><strong>Customer ID:</strong> {customer_id}</p>
                <p><strong>Account ID:</strong> {account_id}</p>
                <p><strong>Account Type:</strong> {account_type}</p>
                <p><strong>Balance:</strong> ${initial_deposit:.2f}</p>
                <a href='/'>← Go Home</a>
            """
        except sqlite3.IntegrityError:
            conn.rollback()
            return "Error: Email already exists!"
        except Exception as e:
            conn.rollback()
            return f"Error: {str(e)}"
        finally:
            conn.close()

    return render_template('create_account.html')

# ---------- DEPOSIT ----------


@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        account_id = int(request.form['account_id'])
        amount = float(request.form['amount'])

        if amount <= 0:
            return "Error: Amount must be greater than 0"

        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'UPDATE "Account" SET balance = balance + ? WHERE account_id = ?',
                (amount, account_id)
            )
            cursor.execute('''
                INSERT INTO "Transaction" (sender_account, receiver_account, transaction_type, amount, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (None, account_id, 'Deposit', amount, 'Completed'))
            conn.commit()

            cursor.execute(
                'SELECT balance FROM "Account" WHERE account_id = ?', (account_id,))
            new_balance = cursor.fetchone()[0]

            return f"""
                <h2>✅ Deposit Successful!</h2>
                <p>Account ID: {account_id}</p>
                <p>Amount Deposited: ${amount:.2f}</p>
                <p>New Balance: ${new_balance:.2f}</p>
                <a href='/'>← Go Home</a>
            """
        except Exception as e:
            conn.rollback()
            return f"Error: {str(e)}"
        finally:
            conn.close()

    return render_template('deposit.html')

# ---------- WITHDRAW ----------


@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        account_id = int(request.form['account_id'])
        amount = float(request.form['amount'])

        if amount <= 0:
            return "Error: Amount must be greater than 0"

        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT balance FROM "Account" WHERE account_id = ?', (account_id,))
            result = cursor.fetchone()
            if not result:
                return "Error: Account not found"
            current_balance = result[0]
            if current_balance < amount:
                return f"Error: Insufficient balance. Current balance: ${current_balance:.2f}"

            cursor.execute(
                'UPDATE "Account" SET balance = balance - ? WHERE account_id = ?',
                (amount, account_id)
            )
            cursor.execute('''
                INSERT INTO "Transaction" (sender_account, receiver_account, transaction_type, amount, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (account_id, None, 'Withdrawal', amount, 'Completed'))
            conn.commit()

            cursor.execute(
                'SELECT balance FROM "Account" WHERE account_id = ?', (account_id,))
            new_balance = cursor.fetchone()[0]

            return f"""
                <h2>✅ Withdrawal Successful!</h2>
                <p>Account ID: {account_id}</p>
                <p>Amount Withdrawn: ${amount:.2f}</p>
                <p>New Balance: ${new_balance:.2f}</p>
                <a href='/'>← Go Home</a>
            """
        except Exception as e:
            conn.rollback()
            return f"Error: {str(e)}"
        finally:
            conn.close()

    return render_template('withdraw.html')

# ---------- CHECK BALANCE ----------


@app.route('/balance', methods=['GET', 'POST'])
def check_balance():
    if request.method == 'POST':
        account_id = int(request.form['account_id'])
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT a.account_id, c.name, a.account_type, a.balance 
                FROM "Account" a
                JOIN "Customer" c ON a.customer_id = c.customer_id
                WHERE a.account_id = ?
            ''', (account_id,))
            result = cursor.fetchone()
            if not result:
                return "Error: Account not found"
            account_id, name, account_type, balance = result
            return f"""
                <h2>📊 Account Balance</h2>
                <p><strong>Account ID:</strong> {account_id}</p>
                <p><strong>Customer:</strong> {name}</p>
                <p><strong>Account Type:</strong> {account_type}</p>
                <p><strong>Balance:</strong> ${balance:.2f}</p>
                <a href='/'>← Go Home</a>
            """
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            conn.close()
    return render_template('balance.html')

# ---------- TRANSFER  ----------


@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if request.method == 'POST':
        sender_id = int(request.form['sender_id'])
        receiver_id = int(request.form['receiver_id'])
        amount = float(request.form['amount'])

        if amount <= 0:
            return "Error: Amount must be greater than 0"

        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            # Start explicit transaction
            conn.execute('BEGIN')

            # Check sender balance
            cursor.execute(
                'SELECT balance FROM "Account" WHERE account_id = ?', (sender_id,))
            sender_result = cursor.fetchone()
            if not sender_result:
                conn.rollback()
                return "Error: Sender account not found"
            sender_balance = sender_result[0]
            if sender_balance < amount:
                conn.rollback()
                return f"Error: Insufficient balance. Sender balance: ${sender_balance:.2f}"

            # Check receiver exists
            cursor.execute(
                'SELECT account_id FROM "Account" WHERE account_id = ?', (receiver_id,))
            if not cursor.fetchone():
                conn.rollback()
                return "Error: Receiver account not found"

            # Deduct from sender
            cursor.execute(
                'UPDATE "Account" SET balance = balance - ? WHERE account_id = ?',
                (amount, sender_id)
            )
            # Add to receiver
            cursor.execute(
                'UPDATE "Account" SET balance = balance + ? WHERE account_id = ?',
                (amount, receiver_id)
            )
            # Log transaction
            cursor.execute('''
                INSERT INTO "Transaction" (sender_account, receiver_account, transaction_type, amount, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (sender_id, receiver_id, 'Transfer', amount, 'Completed'))

            conn.commit()

            return f"""
                <h2>✅ Transfer Successful!</h2>
                <p>Sender Account: {sender_id}</p>
                <p>Receiver Account: {receiver_id}</p>
                <p>Amount Transferred: ${amount:.2f}</p>
                <p><strong>ACID Properties Demonstrated:</strong></p>
                <ul>
                    <li><strong>Atomicity:</strong> Both updates succeeded together</li>
                    <li><strong>Consistency:</strong> Total balance preserved</li>
                    <li><strong>Isolation:</strong> Transaction ran independently</li>
                    <li><strong>Durability:</strong> Changes are permanent</li>
                </ul>
                <a href='/'>← Go Home</a>
            """
        except Exception as e:
            conn.rollback()
            return f"""
                <h2>❌ Transfer Failed!</h2>
                <p>Error: {str(e)}</p>
                <p><strong>Rollback Executed:</strong> All changes undone.</p>
                <a href='/'>← Go Home</a>
            """
        finally:
            conn.close()

    return render_template('transfer.html')

# ---------- TRANSACTION HISTORY ----------


@app.route('/history', methods=['GET', 'POST'])
def history():
    conn = db.get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        account_id = request.form.get('account_id')
        if account_id and account_id.isdigit():
            account_id = int(account_id)
            cursor.execute('''
                SELECT transaction_id, sender_account, receiver_account, 
                       transaction_type, amount, timestamp, status
                FROM "Transaction"
                WHERE sender_account = ? OR receiver_account = ?
                ORDER BY timestamp DESC
            ''', (account_id, account_id))
        else:
            # Show all if no valid account
            cursor.execute('''
                SELECT transaction_id, sender_account, receiver_account, 
                       transaction_type, amount, timestamp, status
                FROM "Transaction"
                ORDER BY timestamp DESC
            ''')
    else:
        # Default: show last 50 transactions
        cursor.execute('''
            SELECT transaction_id, sender_account, receiver_account, 
                   transaction_type, amount, timestamp, status
            FROM "Transaction"
            ORDER BY timestamp DESC
            LIMIT 50
        ''')

    transactions = cursor.fetchall()
    conn.close()
    return render_template('history.html', transactions=transactions)


# ---------- RUN ----------
if __name__ == '__main__':
    db.init_db()
    app.run(debug=True, port=5000)
