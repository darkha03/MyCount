from backend.models import Plan, PlanParticipant, Expense, ExpenseShare, db


def delete_guest_user(user):
    """
    Deletes a user and cascades deletions to their plans and related data.
    """
    try:
        username = user.username

        # Plans the guest created (remove everything linked to them)
        owned_plans = Plan.query.filter_by(created_by=user.id).all()
        # Detach plan objects so later attribute access (e.g., plan.id in tests)
        # does not trigger a refresh after the rows are deleted.
        for p in owned_plans:
            db.session.expunge(p)
        plan_ids = [p.id for p in owned_plans]
        if plan_ids:
            # Remove expense shares first to avoid FK issues when deleting expenses
            expense_ids_subq = db.session.query(Expense.id).filter(Expense.plan_id.in_(plan_ids))
            ExpenseShare.query.filter(ExpenseShare.expense_id.in_(expense_ids_subq)).delete(
                synchronize_session=False
            )
            Expense.query.filter(Expense.plan_id.in_(plan_ids)).delete(synchronize_session=False)
            PlanParticipant.query.filter(PlanParticipant.plan_id.in_(plan_ids)).delete(
                synchronize_session=False
            )
            Plan.query.filter(Plan.id.in_(plan_ids)).delete(synchronize_session=False)

        # Remove expenses authored by the guest in other plans (match by payer name/id)
        guest_expense_ids = [
            e.id
            for e in Expense.query.filter(
                (Expense.payer_id == user.id) | (Expense.payer_name == username)
            ).all()
        ]
        if guest_expense_ids:
            ExpenseShare.query.filter(ExpenseShare.expense_id.in_(guest_expense_ids)).delete(
                synchronize_session=False
            )
            Expense.query.filter(Expense.id.in_(guest_expense_ids)).delete(
                synchronize_session=False
            )

        # Remove any lingering shares/participants that mention this guest
        ExpenseShare.query.filter_by(name=username).delete(synchronize_session=False)
        PlanParticipant.query.filter_by(user_id=user.id).delete(synchronize_session=False)

        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
