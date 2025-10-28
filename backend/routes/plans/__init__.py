from flask import Blueprint, jsonify, request, render_template, session
from backend.utils.auth import login_required
from backend.models import db, User, Plan, PlanParticipant, Expense, ExpenseShare
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
@login_required
def get_plans():
    return render_template("plans/dashboard.html")

#Get all the plans for the logged in user
@plans_bp.route("/api/plans", methods=["GET"])
@login_required
def get_plans_api():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user_plans = []
    for participation in user.participations:
        plan = Plan.query.get(participation.plan_id)
        if plan:
            user_plans.append({
                "id": plan.id,
                "name": plan.name,
                "hash_id": plan.hash_id,
                "created_at": plan.created_at.isoformat()
            })
    return jsonify(user_plans)

#Add a new plan
@plans_bp.route("/api/plans", methods=["POST"])
@login_required
def add_plan():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    hash_id = generate_hash_id()
    participants = data.get("participants", []) # List of participant usernames
    # Create new plan
    plan = Plan(name=data["name"], hash_id=hash_id, created_by=user.id)
    db.session.add(plan)
    db.session.flush()  # assign plan.id without committing

    # Add creator as participant
    participant = PlanParticipant(user_id=user.id, plan_id=plan.id, role="owner", name=participants[0] if participants else username)
    db.session.add(participant)
    # Add other participants
    for participant_name in participants[1:]:
        participant = PlanParticipant(user_id=None, plan_id=plan.id, role="member", name=participant_name)
        db.session.add(participant)
    # Commit everything at once
    db.session.commit()

    return jsonify({"name": plan.name, "hash_id": plan.hash_id}), 201

@plans_bp.route("/api/plans/<plan_id>", methods=["DELETE"])
@login_required
def delete_plan(plan_id):
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    plan = Plan.query.filter_by(hash_id=plan_id).first()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    participant = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=user.id).first()
    if not participant:
        return jsonify({"error: You are not a participant of this plan"}), 403
    db.session.delete(participant)  # Remove user from participants
    db.session.commit()
    return jsonify({"message": f"You left plan {plan.name}."}), 200

# Route to view a specific plan
@plans_bp.route("/<hash_id>", methods=["GET"])
@login_required
def view_plan(hash_id):
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    for plan in user.participations:
        if plan.plan.hash_id == hash_id:
            return render_template("plans/view_plan.html", plan=plan.plan)
    return jsonify({"error": "Plan not found"}), 404

@plans_bp.route("/api/plans/<hash_id>/expenses", methods=["GET"])
@login_required
def get_plan_expenses_api(hash_id):
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    for plan in user.participations:
        if plan.plan.hash_id == hash_id:
            plan_expenses = Expense.query.filter_by(plan_id=plan.plan.id).all()
            expenses_list = []
            for expense in plan_expenses:
                expenses_list.append({
                    "id": expense.id,
                    "name": expense.name,
                    "amount": expense.amount,
                    "payer": expense.payer,
                    "participants": expense.participants,
                    "amount_details": expense.amount_details
                })
            return jsonify(expenses_list)
    return jsonify({"error": "Plan not found"}), 404

# Render expenses page
@plans_bp.route("/<hash_id>/section/expenses", methods=["GET"])
@login_required
def get_plan_expenses(hash_id):
    user = User.query.filter_by(username=session.get("username")).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    for plan in user.participations:
        if plan.plan.hash_id == hash_id:
            plan_expenses = Expense.query.filter_by(plan_id=plan.plan.id).all()
            expenses_list = []
            for expense in plan_expenses:
                expenses_list.append({
                    "id": expense.id,
                    "name": expense.description,
                    "amount": expense.amount,
                    "payer": expense.payer_name,
                })
            participant = PlanParticipant.query.filter_by(plan_id=plan.plan.id).all()
            participant_names = [p.name for p in participant]
            return render_template("plans/expenses.html", expenses=expenses_list, plan=plan.plan, participants=participant_names)
    return jsonify({"error": "Plan not found"}), 404

# Add expense to a plan
@plans_bp.route("/<hash_id>/section/expenses", methods=["POST"])
@login_required
def add_plan_expense(hash_id):
    user = User.query.filter_by(username=session.get("username")).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    for plan in user.participations:
        if plan.plan.hash_id == hash_id:
            data = request.get_json()
            print(f"Received expense data: {data}")
            new_expense = Expense(
                description=data["name"],
                amount=data["amount"],
                payer_name=data["payer"],
                plan_id=plan.plan.id,
            )
            db.session.add(new_expense)
            db.session.flush()  # assign new_expense.id without committing
            for participant, amount in zip(data["participants"], data["amounts"]):
                expense_participant = ExpenseShare(
                    expense_id=new_expense.id,
                    name=participant,
                    amount=amount
                )
                db.session.add(expense_participant)
            db.session.commit()
            print(f"New expense added to plan {hash_id}: {new_expense}")
    return jsonify({"message": "Expense added"}), 201

@plans_bp.route("/<hash_id>/section/expenses/<int:expense_id>", methods=["DELETE"])
@login_required
def delete_plan_expense(hash_id, expense_id):
    user = User.query.filter_by(username=session.get("username")).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    for plan in user.participations:
        if plan.plan.hash_id == hash_id:
            expense = Expense.query.filter_by(id=expense_id, plan_id=plan.plan.id).first()
            if not expense:
                return jsonify({"error": "Expense not found"}), 404
            db.session.delete(expense)
            db.session.commit()
            print(f"Expense {expense_id} deleted from plan {hash_id}")
            return jsonify({"message": "Expense deleted"}), 200
    return jsonify({"error": "Plan not found"}), 404

@plans_bp.route("/<hash_id>/section/expenses/<int:expense_id>", methods=["PUT"])
@login_required
def update_plan_expense(hash_id, expense_id):
    data = request.get_json()
    user = User.query.filter_by(username=session.get("username")).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    for plan in user.participations:
        if plan.plan.hash_id == hash_id:
            expense = Expense.query.filter_by(id=expense_id, plan_id=plan.plan.id).first()
            if not expense:
                return jsonify({"error": "Expense not found"}), 404
            # Update expense details
            expense.description = data.get("name", expense.description)
            expense.amount = data.get("amount", expense.amount)
            expense.payer_name = data.get("payer", expense.payer)
            # Update shares
            ExpenseShare.query.filter_by(expense_id=expense.id).delete()
            for participant, amount in zip(data["participants"], data["amounts"]):
                expense_participant = ExpenseShare(
                    expense_id=expense.id,
                    name=participant,
                    amount=amount
                )
                db.session.add(expense_participant)
            db.session.commit()
            print(f"Expense {expense_id} updated in plan {hash_id}")
            return jsonify({"message": "Expense updated"}), 200
    return jsonify({"error": "Expense not found"}), 404

@plans_bp.route("/<hash_id>/section/expenses/<int:expense_id>", methods=["GET"])
@login_required
def get_plan_expense(hash_id, expense_id):
    user = User.query.filter_by(username=session.get("username")).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    for plan in user.participations:
        if plan.plan.hash_id == hash_id:
            expense = Expense.query.filter_by(id=expense_id, plan_id=plan.plan.id).first()
            if expense:
                participant = ExpenseShare.query.filter_by(expense_id=expense.id).all()
                participant_names = [p.name for p in participant]
                participant_amounts = [p.amount for p in participant]
                expense_data = {
                    "id": expense.id,
                    "name": expense.description,
                    "amount": expense.amount,
                    "payer": expense.payer_name,
                    "participants": participant_names,
                    "amounts": participant_amounts
                }
            return render_template("/plans/expense.html", expense=expense_data, plan=plan.plan, zip=zip)
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
@login_required
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
@login_required
def get_plan_statistics(hash_id):
    # Placeholder for actual statistics retrieval logic
    global expenses
    balances = calculate_balance(expenses)
    total_expense = calculate_expense(expenses)
    real_expense = calculate_real_expense(expenses)
    return render_template("plans/statistics.html", hash_id=hash_id, balances=balances, total_expense=total_expense, real_expense=real_expense)