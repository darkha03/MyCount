from flask import Blueprint, jsonify, request, render_template, session
from backend.utils.auth import login_required
from backend.models import db, User, Plan, PlanParticipant, Expense, ExpenseShare
from .helpers import (
    validate_participant_name_list,
    validate_participants_payload,
    apply_participants_updates,
)
import secrets
from datetime import datetime


def generate_hash_id(length=8):
    return secrets.token_urlsafe(length)[:length]


plans_bp = Blueprint(
    "plans",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/plans",
)


# Routes for plans management
@plans_bp.route("/", methods=["GET"])
@login_required
def get_plans():
    return render_template("plans/dashboard.html")


# Get all the plans for the logged in user
@plans_bp.route("/api/plans", methods=["GET"])
@login_required
def get_plans_api():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user_plans = []
    for participation in user.participations:
        plan = db.session.get(Plan, participation.plan_id)
        if plan:
            participant = PlanParticipant.query.filter_by(plan_id=plan.id).all()
            expenses = Expense.query.filter_by(plan_id=plan.id).all()
            user_plans.append(
                {
                    "id": plan.id,
                    "name": plan.name,
                    "hash_id": plan.hash_id,
                    "created_at": plan.created_at.isoformat(),
                    "participants": [p.name for p in participant],
                    "total_expenses": sum(
                        e.amount for e in expenses if e.description != "Reimbursement"
                    ),
                }
            )
    return jsonify(user_plans)


# Add a new plan
@plans_bp.route("/api/plans", methods=["POST"])
@login_required
def add_plan():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    hash_id = generate_hash_id()
    participants = data.get("participants", [])  # List of participant usernames
    ok, msg = validate_participant_name_list(participants)
    if not ok:
        return jsonify({"error": msg}), 400
    # Create new plan
    plan = Plan(name=data["name"], hash_id=hash_id, created_by=user.id)
    db.session.add(plan)
    db.session.flush()  # assign plan.id without committing

    # Add creator as participant
    participant = PlanParticipant(
        user_id=user.id,
        plan_id=plan.id,
        role="owner",
        name=participants[0] if participants else username,
    )
    db.session.add(participant)
    # Add other participants
    for participant_name in participants[1:]:
        participant = PlanParticipant(
            user_id=None, plan_id=plan.id, role="member", name=participant_name
        )
        db.session.add(participant)
    # Commit everything at once
    db.session.commit()

    return jsonify({"name": plan.name, "hash_id": plan.hash_id}), 201


# Get a specific plan
@plans_bp.route("/api/plans/<plan_id>", methods=["GET"])
@login_required
def get_plan(plan_id):
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    plan = Plan.query.filter_by(hash_id=plan_id).first()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    participant = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=user.id).first()
    if not participant:
        return jsonify({"error": "You are not a participant of this plan"}), 403
    participants = []
    for p in PlanParticipant.query.filter_by(plan_id=plan.id).all():
        participants.append({"id": p.id, "name": p.name, "user_id": p.user_id, "role": p.role})

    plan_data = {
        "id": plan.id,
        "name": plan.name,
        "hash_id": plan.hash_id,
        "created_at": plan.created_at.isoformat(),
        "participants": participants,
        "current_user_id": user.id,
    }
    return jsonify(plan_data), 200


# Modify a plan
@plans_bp.route("/api/plans/<plan_id>", methods=["PUT"])
@login_required
def modify_plan(plan_id):
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    plan = Plan.query.filter_by(hash_id=plan_id).first()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    participant = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=user.id).first()
    if not participant:
        return jsonify({"error": "You are not a participant of this plan"}), 403
    data = request.get_json()
    plan.name = data.get("name", plan.name)

    # If participants list provided, apply updates. Expected format:
    # participants: [{"id": <pp_id>, "name": "Name",
    # "user_id": <user_id or null>, "role": "member"}, ...]
    participants_data = data.get("participants")
    if participants_data is not None:
        ok, msg = validate_participants_payload(participants_data)
        if not ok:
            return jsonify({"error": msg}), 400
        apply_participants_updates(plan, participants_data)

    db.session.commit()
    return jsonify({"message": f"Plan {plan.name} updated."}), 200


# Delete a plan (leave the plan)
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
        return jsonify({"error": "You do not have permission to delete this plan"}), 403
    # Remove user_id from participant to mark as left
    participant.user_id = None
    # If user is owner, set next participant as owner
    if participant.role == "owner":
        next_participant = (
            PlanParticipant.query.filter_by(plan_id=plan.id)
            .filter(PlanParticipant.user_id.isnot(None))
            .first()
        )
        if next_participant:
            participant.role = "member"
            next_participant.role = "owner"
        else:
            # No participants left, delete the plan
            ExpenseShare.query.filter(
                ExpenseShare.expense_id.in_(db.session.query(Expense.id).filter_by(plan_id=plan.id))
            ).delete(synchronize_session=False)
            Expense.query.filter_by(plan_id=plan.id).delete(synchronize_session=False)
            PlanParticipant.query.filter_by(plan_id=plan.id).delete(synchronize_session=False)
            db.session.delete(plan)
    db.session.commit()
    return jsonify({"message": f"You left plan {plan.name}."}), 200


# Join an existing plan
@plans_bp.route("/api/plans/<plan_id>/join", methods=["GET", "POST"])
@login_required
def join_plan(plan_id):
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    plan = Plan.query.filter_by(hash_id=plan_id).first()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    if request.method == "GET":
        existing_participants = PlanParticipant.query.filter_by(plan_id=plan.id).all()
        if any(p.user_id == user.id for p in existing_participants):
            return jsonify({"error": "You are already a participant of this plan."}), 400
        participants_list = [{"name": p.name, "id": p.user_id} for p in existing_participants]
        return jsonify(participants_list), 200
    elif request.method == "POST":
        existing_participant = PlanParticipant.query.filter_by(
            plan_id=plan.id, user_id=user.id
        ).first()
        if existing_participant:
            return jsonify({"error": "You are already a participant of this plan."}), 400
        # Add user as participant
        name = request.json.get("participant_name", username)
        update_participant = PlanParticipant.query.filter_by(
            plan_id=plan.id, name=name, user_id=None
        ).first()
        if update_participant:
            update_participant.user_id = user.id
        else:
            return jsonify({"error": "No available slot with that name to join."}), 400
        db.session.commit()
        return jsonify({"message": f"You have joined the plan '{plan.name}'."}), 200


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
                participant = ExpenseShare.query.filter_by(expense_id=expense.id).all()
                expenses_list.append(
                    {
                        "id": expense.id,
                        "name": expense.description,
                        "amount": expense.amount,
                        "payer": expense.payer_name,
                        "participants": [p.name for p in participant],
                        "amount_details": {p.name: p.amount for p in participant},
                    }
                )
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
            expenses_by_date = {}
            for expense in plan_expenses:
                date_str = expense.date.strftime("%d/%m/%Y")
                if date_str not in expenses_by_date:
                    expenses_by_date[date_str] = []
                expenses_by_date[date_str].append(
                    {
                        "id": expense.id,
                        "name": expense.description,
                        "amount": expense.amount,
                        "payer": expense.payer_name,
                    }
                )
            participant = PlanParticipant.query.filter_by(plan_id=plan.plan.id).all()
            participant_names = [p.name for p in participant]
            sorted_dates = sorted(expenses_by_date.keys(), reverse=True)
            return render_template(
                "plans/expenses.html",
                expenses_by_date=expenses_by_date,
                sorted_dates=sorted_dates,
                plan=plan.plan,
                participants=participant_names,
            )
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
            date_str = data["date"]
            try:
                # If date is in 'YYYY-MM-DD' format
                date_obj = datetime.fromisoformat(date_str)
            except Exception:
                # fallback for other formats, e.g. 'YYYY-MM-DDTHH:MM'
                date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")

            new_expense = Expense(
                description=data["name"],
                amount=data["amount"],
                payer_name=data["payer"],
                date=date_obj,
                plan_id=plan.plan.id,
            )
            db.session.add(new_expense)
            db.session.flush()  # assign new_expense.id without committing
            for participant, amount in zip(data["participants"], data["amounts"]):
                expense_participant = ExpenseShare(
                    expense_id=new_expense.id, name=participant, amount=amount
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
                    expense_id=expense.id, name=participant, amount=amount
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
                    "date": expense.date.isoformat(),
                    "payer": expense.payer_name,
                    "participants": participant_names,
                    "amounts": participant_amounts,
                }
            return render_template(
                "/plans/expense.html", expense=expense_data, plan=plan.plan, zip=zip
            )
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
        reimbursements.append({"from": debtor, "to": creditor, "amount": round(amount, 2)})

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
    expenses = get_plan_expenses_api(hash_id).get_json()
    balances = calculate_balance(expenses)
    reimbursements = calculate_reimbursements(balances)
    return render_template(
        "plans/reimbursements.html", hash_id=hash_id, reimbursements=reimbursements
    )


# Route for plan statistics


def calculate_balance(expenses):
    balances = {}
    for expense in expenses:
        payer = expense["payer"]
        amount = expense["amount"]
        participants = expense["participants"]
        amount_details = expense["amount_details"]

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
        amount_details = expense["amount_details"]
        for participant in participants:
            if participant not in total_expense:
                total_expense[participant] = 0
            if expense["name"] == "Reimbursement":
                continue  # Skip reimbursements in total expense calculation
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
        for participant in expense["participants"]:
            if participant not in real_expense:
                real_expense[participant] = 0
        if expense["name"] == "Reimbursement":
            for participant in expense["participants"]:
                if participant not in real_expense:
                    real_expense[participant] = 0
                real_expense[participant] -= expense["amount_details"][participant]
    for k in real_expense:
        real_expense[k] = round(real_expense[k], 2)
    return real_expense


@plans_bp.route("/<hash_id>/section/statistics", methods=["GET"])
@login_required
def get_plan_statistics(hash_id):
    # Placeholder for actual statistics retrieval logic
    expenses = get_plan_expenses_api(hash_id).get_json()
    balances = calculate_balance(expenses)
    total_expense = calculate_expense(expenses)
    real_expense = calculate_real_expense(expenses)
    balances = dict(sorted(balances.items()))
    total_expense = dict(sorted(total_expense.items()))
    real_expense = dict(sorted(real_expense.items()))
    return render_template(
        "plans/statistics.html",
        hash_id=hash_id,
        balances=balances,
        total_expense=total_expense,
        real_expense=real_expense,
    )
