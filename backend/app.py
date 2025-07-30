from flask import Flask, jsonify, render_template
from flask_cors import CORS
from routes.plans import plans_bp



app = Flask(__name__)
CORS(app)

app.register_blueprint(plans_bp)

# Mock data for now
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/expenses")
def get_expenses():
    return jsonify(expenses)

if __name__ == "__main__":
    app.run(debug=True)
