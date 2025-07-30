from flask import Blueprint, jsonify, request, render_template
import secrets

def generate_hash_id(length=8):
    return secrets.token_urlsafe(length)[:length]

plans_bp = Blueprint(
    "plans",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/plans"  # Optional prefix
)

# Temporary mock plans
plans = [
    {"id": 1, "name": "Trip to Hanoi", "hash_id": generate_hash_id(), "participants": ["Alice", "Bob", "Charlie"]},
    {"id": 2, "name": "Birthday Party", "hash_id": generate_hash_id(), "participants": ["Alice", "Bob", "Charlie", "David"]},
]
expenses = [
        {"id": 1, "name": "Lunch", "amount": 120.0, "payer": "Alice", "participants": ["Alice", "Bob", "Charlie"], "amount_details": {"Alice": 40.0, "Bob": 40.0, "Charlie": 40.0}},
        {"id": 2, "name": "Taxi", "amount": 60.0, "payer": "Bob", "participants": ["Bob", "Charlie"], "amount_details": {"Bob": 30.0, "Charlie": 30.0}},
]

# Routes for plans management
@plans_bp.route("/", methods=["GET"])
def get_plans():
    return render_template("plans/dashboard.html")
@plans_bp.route("/api/plans", methods=["GET"])
def get_plans_api():
    return jsonify(plans)
@plans_bp.route("/api/plans", methods=["POST"])
def add_plan():
    data = request.get_json()
    new_id = max(p["id"] for p in plans) + 1 if plans else 1
    new_plan = {"id": new_id, "name": data["name"], "hash_id": generate_hash_id()}
    plans.append(new_plan)
    return jsonify(new_plan), 201
@plans_bp.route("/api/plans/<int:plan_id>", methods=["DELETE"])
def delete_plan(plan_id):
    global plans
    plans = [p for p in plans if p["id"] != plan_id]
    return jsonify({"message": f"Plan {plan_id} deleted."}), 200

# Route to view a specific plan
@plans_bp.route("/<hash_id>", methods=["GET"])
def view_plan(hash_id):
    for plan in plans:
        if plan["hash_id"] == hash_id:
            return render_template("plans/view_plan.html", plan=plan, expenses=expenses)
    return jsonify({"error": "Plan not found"}), 404

@plans_bp.route("/api/plans/<hash_id>/expenses", methods=["GET"])
def get_plan_expenses_api(hash_id):
    # This is a placeholder for actual expense retrieval logic
    for plan in plans:
        if plan["hash_id"] == hash_id:
            # In a real application, you would filter expenses by the plan
            # Here we return all expenses for simplicity
            return jsonify(expenses)
    return jsonify({"error": "Plan not found"}), 404

@plans_bp.route("/<hash_id>/section/expenses", methods=["GET"])
def get_plan_expenses(hash_id):
    # This is a placeholder for actual expense retrieval logic
    for plan in plans:
        if plan["hash_id"] == hash_id:
            # In a real application, you would filter expenses by the plan
            # Here we return all expenses for simplicity
            return render_template("plans/expenses.html", expenses=expenses, plan=plan)

@plans_bp.route("/<hash_id>/section/expenses", methods=["POST"])
def add_plan_expense(hash_id):
    data = request.get_json()
    global expenses
    new_expense = {
        "id": len(expenses) + 1,  # Simple ID generation for demo purposes
        "name": data["name"],
        "amount": data["amount"],
        "payer": data["payer"],
        "participants": data["participants"],
        "amount_details" : {
            participant: float(amount)
            for participant, amount in zip(data["participants"], data["amounts"])
        }
    }
    # Here you would typically save the expense to a database
    expenses.append(new_expense)
    return jsonify(new_expense), 201

@plans_bp.route("/<hash_id>/section/expenses/<int:expense_id>", methods=["DELETE"])
def delete_plan_expense(hash_id, expense_id):
    global expenses
    expenses = [e for e in expenses if e["id"] != expense_id]
    return jsonify({"message": f"Expense {expense_id} deleted."}), 200

@plans_bp.route("/<hash_id>/section/expenses/<int:expense_id>", methods=["PUT"])
def update_plan_expense(hash_id, expense_id):
    data = request.get_json()
    for expense in expenses:
        if expense["id"] == expense_id:
            expense.update(data)
            return jsonify(expense), 200
    return jsonify({"error": "Expense not found"}), 404

@plans_bp.route("/<hash_id>/section/expenses/<int:expense_id>", methods=["GET"])
def get_plan_expense(hash_id, expense_id):
    plan = next((p for p in plans if p["hash_id"] == hash_id), None)
    for expense in expenses:
        if expense["id"] == expense_id:
            return render_template("/plans/expense.html", expense=expense, plan=plan)
    return jsonify({"error": "Expense not found"}), 404

# Routes for reimbursements

def calculate_reimbursements(balances):
    creditors = []
    debtors = []
    reimbursements = []

    # Separate into creditors and debtors
    for person, balance in balances.items():
        if balance > 0:
            creditors.append([person, balance])
        elif balance < 0:
            debtors.append([person, -balance])  # store positive debt

    # Greedy algorithm
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor, debt = debtors[i]
        creditor, credit = creditors[j]

        amount = min(debt, credit)
        reimbursements.append({
            "from": debtor,
            "to": creditor,
            "amount": round(amount, 2)
        })

        debtors[i][1] -= amount
        creditors[j][1] -= amount

        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    return reimbursements

@plans_bp.route("/<hash_id>/section/reimbursements", methods=["GET"])
def get_plan_reimbursements(hash_id):
    # Placeholder for actual reimbursement retrieval logic
    global expenses
    balances = calculate_balance(expenses)
    reimbursements = calculate_reimbursements(balances)
    return render_template("plans/reimbursements.html", hash_id=hash_id, reimbursements=reimbursements)

# Route for plan statistics

def calculate_balance(expenses):
    balances = {}
    for expense in expenses:
        payer = expense["payer"]
        amount = expense["amount"]
        participants = expense["participants"]
        amount_details = expense['amount_details']
        
        for participant in participants:
            if participant not in balances:
                balances[participant] = 0
            if participant == payer:
                balances[participant] += amount - amount_details[participant]
            else:
                balances[participant] -= amount_details[participant]
        if payer not in participants:
            balances[payer] += amount
    for k in balances:
        balances[k] = round(balances[k], 2)
    return balances

def calculate_expense(expenses):
    total_expense = {}
    for expense in expenses:
        participants = expense["participants"]
        amount_details = expense['amount_details']
        for participant in participants:
            if participant not in total_expense:
                total_expense[participant] = 0
            total_expense[participant] += amount_details[participant]
    for k in total_expense:
        total_expense[k] = round(total_expense[k], 2)
    return total_expense

def calculate_real_expense(expenses):
    real_expense = {}
    for expense in expenses:
        payer = expense["payer"]
        amount = expense["amount"]
        if payer not in real_expense:
            real_expense[payer] = 0
        real_expense[payer] += amount
    for k in real_expense:
        real_expense[k] = round(real_expense[k], 2)
    return real_expense

@plans_bp.route("/<hash_id>/section/statistics", methods=["GET"])
def get_plan_statistics(hash_id):
    # Placeholder for actual statistics retrieval logic
    global expenses
    balances = calculate_balance(expenses)
    total_expense = calculate_expense(expenses)
    real_expense = calculate_real_expense(expenses)
    return render_template("plans/statistics.html", hash_id=hash_id, balances=balances, total_expense=total_expense, real_expense=real_expense)