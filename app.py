
from flask import Flask
import database as db

app = Flask(__name__)


@app.route('/')
def index():
    return "🏦 BankSync is running! Visit /dashboard"


@app.route('/dashboard')
def dashboard():
    return "<h1>Dashboard - Coming Soon</h1>"


if __name__ == '__main__':
    db.init_db()
    app.run(debug=True, port=5000)
