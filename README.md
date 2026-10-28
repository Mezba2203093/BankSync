# 🏦 BankSync - Smart Banking & AI Fraud Detection

Welcome to BankSync! This project was built as a simulation of a modern banking transaction system for my CSE 3200 (Software Development Project II) course. 

The main goal of this project was to combine traditional Database Management (DBMS) with Machine Learning to see how they can work together to build a safer banking environment. It handles standard banking tasks while an AI model runs in the background to spot and prevent fraudulent activities.

#  What It Can Do

* Standard Banking: Create accounts, deposit cash, withdraw, and transfer money between users.
* Real ACID Transactions: Money transfers aren't just simple updates. I used explicit `BEGIN`, `COMMIT`, and   `ROLLBACK` SQL commands to ensure that if a transfer fails halfway through, no money is lost.
* AI Anomaly Detection: Using an Isolation Forest machine learning model (built with Scikit-Learn), the system scores every new transaction. If a transaction looks out of character (like an unusually huge transfer or a tiny $0.01 test transaction), it gets flagged.
* Cumulative Risk Profiling: The system doesn't just block you on the first mistake. It tracks your account's "risk score." If you keep making suspicious transfers, your score goes up. Once it hits `3.0`, the system assumes the account is compromised and blocks all outgoing transfers.
* Admin Dashboard: A secure, password-protected dashboard where a bank manager can view charts (built with Chart.js), monitor risk distributions, and manually reset a user's risk score if they are cleared of suspicion.

#  Tech Stack Used
* Backend: Python (Flask)
* Database: SQLite
* AI / Machine Learning: Pandas, Numpy, Scikit-Learn
* Frontend: HTML, CSS, Chart.js
* Version Control: Git & GitHub

#  How to Run It Locally

If you want to test it out on your own machine, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/Mezba2203093/BankSync.git
   cd BankSync
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Generate some test data and train the AI model:
   (Note: You'll need to create at least 2 accounts in the web app first before generating data)*
   ```bash
   python generate_data.py
   python ai_model.py
   python backfill_ai.py
   ```

4. Start the Flask server:
   ```bash
   python app.py
   ```

5. Open your browser and go to `http://127.0.0.1:5000`

#  Admin Access
To view the Analytics Dashboard, you'll need to log in. Click the "Analytics Dashboard" button on the home page, or go to `/dashboard`.

* Username: `admin`
* Password:** `admin123`


Developed by: Mezba Uddin Rubab (Roll: 2203093)  
Department of Computer Science & Engineering, RUET