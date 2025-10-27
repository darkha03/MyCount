from flask import Flask, jsonify, render_template, session
from flask_cors import CORS
from routes.plans import plans_bp
from routes.auth import auth_bp
from models import db, User, Plan, PlanParticipant, Expense
from utils.auth import login_required

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    app.secret_key = "your-very-secret-key"
    CORS(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(plans_bp)    
    app.register_blueprint(auth_bp)
    return app

app = create_app()

expenses = [
    {
        "id": 1,
        "description": "Lunch",
        "amount": 120.0,
        "payer": "Alice",
        "participants": ["Alice", "Bob", "Charlie"]
    },
    {
        "id": 2,
        "description": "Taxi",
        "amount": 60.0,
        "payer": "Bob",
        "participants": ["Bob", "Charlie"]
    }
]

reimbursements = [
    {
        "from": "Charlie",
        "to": "Alice",
        "amount": 40.0
    },
    {
        "from": "Charlie",
        "to": "Bob",
        "amount": 20.0
    }
]


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/expenses")
@login_required
def get_expenses():
    return jsonify(expenses)

@app.route("/api/reimbursements")
@login_required
def get_reimbursements():
    return jsonify(reimbursements)

if __name__ == "__main__":
    app.run(debug=True)
