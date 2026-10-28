from flask import Flask, render_template, request, redirect, url_for, session, flash
import database as db
import sqlite3
import ai_model

app = Flask(__name__)
app = Flask(__name__)
app.secret_key = 'super_secret_banksync_key'


def flag_transaction(transaction_id, amount, sender_account, timestamp=None):

    score, risk, reason = ai_model.score_transaction(
        amount, sender_account, timestamp)

    conn = db.get_connection()
    c = conn.cursor()
    try:
        c.execute(
            'UPDATE "Transaction" SET anomaly_score = ?, risk_level = ? WHERE transaction_id = ?',
            (score, risk, transaction_id)
        )
        if risk != 'Normal':
            c.execute('''
                INSERT INTO "AI_Analysis"
                    (transaction_id, anomaly_score, risk_level, detection_reason)
                VALUES (?, ?, ?, ?)
            ''', (transaction_id, score, risk, reason))
        conn.commit()
    finally:
        conn.close()

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
                <h2> Account Created Successfully!</h2>
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
            last_id = cursor.lastrowid
            flag_transaction(last_id, amount, account_id)

            cursor.execute(
                'SELECT balance FROM "Account" WHERE account_id = ?', (account_id,))
            new_balance = cursor.fetchone()[0]

            return f"""
                <h2> Deposit Successful!</h2>
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
            last_id = cursor.lastrowid
            flag_transaction(last_id, amount, account_id)

            cursor.execute(
                'SELECT balance FROM "Account" WHERE account_id = ?', (account_id,))
            new_balance = cursor.fetchone()[0]

            return f"""
                <h2> Withdrawal Successful!</h2>
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

        conn = db.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                'SELECT balance, cumulative_risk FROM "Account" WHERE account_id = ?', (sender_id,))
            sender_result = cursor.fetchone()

            if not sender_result:
                return "Error: Sender account not found"

            sender_balance, current_risk = sender_result

            if sender_balance < amount:
                return f"Error: Insufficient balance. Sender balance: ${sender_balance:.2f}"

            # 2. THE BLOCK: If they already have a high risk score, block them immediately
            if current_risk >= 3.0:
                cursor.execute('''
                    INSERT INTO "Transaction" (sender_account, receiver_account, transaction_type, amount, status, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (sender_id, receiver_id, 'Transfer', amount, 'Blocked', 'High'))
                conn.commit()
                return f"""
                    <h2 style='color:red;'> Account Under Review!</h2>
                    <p>This account has a cumulative risk score of {current_risk:.2f}.</p>
                    <p>Transaction blocked by AI Fraud Prevention System.</p>
                    <a href='/'>← Go Home</a>
                """

            # 3. RUN AI ON THIS SPECIFIC TRANSACTION
            score, risk, reason = ai_model.score_transaction(amount, sender_id)

            # Calculate new risk
            new_risk = current_risk + \
                score if risk != 'Normal' else max(0.0, current_risk - 0.1)

            # 4. START EXPLICIT TRANSACTION (ACID)
            conn.execute('BEGIN')

            # 5. ALL UPDATES HAPPEN INSIDE THE TRANSACTION
            # Update Sender Balance
            cursor.execute(
                'UPDATE "Account" SET balance = balance - ? WHERE account_id = ?', (amount, sender_id))
            # Update Receiver Balance
            cursor.execute(
                'UPDATE "Account" SET balance = balance + ? WHERE account_id = ?', (amount, receiver_id))
            # Update Sender Risk Score
            cursor.execute(
                'UPDATE "Account" SET cumulative_risk = ? WHERE account_id = ?', (new_risk, sender_id))

            # Log the transaction
            cursor.execute('''
                INSERT INTO "Transaction" (sender_account, receiver_account, transaction_type, amount, status, anomaly_score, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (sender_id, receiver_id, 'Transfer', amount, 'Completed', score, risk))

            # COMMIT EVERYTHING TOGETHER
            conn.commit()

            # 6. SHOW THE RESULT
            warning = ""
            if risk != 'Normal':
                warning = f"<p style='color:orange;'><strong>⚠️ Warning:</strong> AI flagged this as {risk} Risk. Your cumulative risk score is now {new_risk:.2f}. If it reaches 3.0, your account will be blocked.</p>"

            return f"""
                <h2>✅ Transfer Successful!</h2>
                <p>Amount Transferred: ${amount:.2f}</p>
                {warning}
                <p><strong>ACID Properties Applied:</strong> Money moved safely.</p>
                <a href='/'>← Go Home</a>
            """
        except Exception as e:
            conn.rollback()  # If anything fails, balances and risk score rollback!
            return f"Transfer Failed: {str(e)}"
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
        # Check if user actually typed a valid ID
        if account_id and account_id.isdigit():
            account_id = int(account_id)
            cursor.execute('''
                SELECT transaction_id, sender_account, receiver_account,
                       transaction_type, amount, timestamp, status,
                       anomaly_score, risk_level
                FROM "Transaction"
                WHERE sender_account = ? OR receiver_account = ?
                ORDER BY transaction_id DESC
            ''', (account_id, account_id))
        else:
            # If they clicked "Filter" but left it blank, show all
            cursor.execute('''
                SELECT transaction_id, sender_account, receiver_account,
                       transaction_type, amount, timestamp, status,
                       anomaly_score, risk_level
                FROM "Transaction"
                ORDER BY transaction_id DESC
                LIMIT 100
            ''')
    else:
        # Default GET request: show last 100 transactions
        cursor.execute('''
            SELECT transaction_id, sender_account, receiver_account,
                   transaction_type, amount, timestamp, status,
                   anomaly_score, risk_level
            FROM "Transaction"
            ORDER BY transaction_id DESC
            LIMIT 100
        ''')

    transactions = cursor.fetchall()
    conn.close()
    return render_template('history.html', transactions=transactions)


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    # SECURITY CHECK: If not admin, redirect to login
    if not session.get('is_admin'):
        return redirect('/admin_login')

    conn = db.get_connection()
    cursor = conn.cursor()

    total_accounts = cursor.execute(
        'SELECT COUNT(*) FROM "Account"').fetchone()[0]
    total_tx = cursor.execute(
        'SELECT COUNT(*) FROM "Transaction"').fetchone()[0]
    total_flagged = cursor.execute(
        'SELECT COUNT(*) FROM "Transaction" WHERE risk_level != \'Normal\'').fetchone()[0]
    risk_data = cursor.execute(
        'SELECT risk_level, COUNT(*) FROM "Transaction" GROUP BY risk_level').fetchall()
    daily_tx = cursor.execute(
        'SELECT DATE(timestamp) as day, COUNT(*) FROM "Transaction" GROUP BY day ORDER BY day DESC LIMIT 5').fetchall()
    accounts = cursor.execute(
        'SELECT account_id, cumulative_risk FROM "Account"').fetchall()

    conn.close()
    daily_tx = list(reversed(daily_tx))

    return render_template('dashboard.html',
                           total_accounts=total_accounts,
                           total_tx=total_tx,
                           total_flagged=total_flagged,
                           risk_data=risk_data,
                           daily_tx=daily_tx,
                           accounts=accounts)

# ---------- ADMIN RESET RISK ----------


@app.route('/reset_risk/<int:account_id>', methods=['POST'])
def reset_risk(account_id):
    # SECURITY CHECK
    if not session.get('is_admin'):
        return redirect('/admin_login')

    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE "Account" SET cumulative_risk = 0.0 WHERE account_id = ?', (account_id,))
        conn.commit()
        return redirect('/dashboard')
    except Exception as e:
        conn.rollback()
        return f"Error: {str(e)}"
    finally:
        conn.close()

# ---------- ADMIN LOGIN ----------


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            session['is_admin'] = True
            return redirect('/dashboard')
        else:
            return "<h2 style='color:red;'>Invalid Credentials. <a href='/admin_login'>Try Again</a></h2>"

    # If GET request, show login form
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Admin Login</title></head>
    <body style="font-family: Arial; max-width: 400px; margin: 100px auto; padding: 20px; text-align: center;">
        <h2>🔒 Admin Portal</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required style="width: 100%; padding: 10px; margin-bottom: 10px;"><br>
            <input type="password" name="password" placeholder="Password" required style="width: 100%; padding: 10px; margin-bottom: 10px;"><br>
            <button type="submit" style="background: #2c3e50; color: white; padding: 10px 20px; border: none; width: 100%; cursor: pointer;">Login</button>
        </form>
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    """

# ---------- ADMIN LOGOUT ----------


@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect('/')


# ---------- RUN ----------
if __name__ == '__main__':
    # db.init_db() <= commented so it doesnt wipe data in restart
    app.run(debug=True, port=5000)
