from backend.models import Plan, PlanParticipant, Expense, db


def delete_guest_user(user):
    """
    Deletes a user and cascades deletions to their plans and related data.
    """
    try:
        # For each plan created by this user, first remove dependent participants
        # so that deleting the plan does not violate foreign key constraints.
        for p in Plan.query.filter_by(created_by=user.id).all():
            PlanParticipant.query.filter_by(plan_id=p.id).delete(synchronize_session=False)
            # Expenses are linked to plans with cascade on the relationship, but
            # remove any explicit expense rows to be safe.
            Expense.query.filter_by(plan_id=p.id).delete(synchronize_session=False)
            db.session.delete(p)

        # Remove any expenses where this user was the payer (in other plans)
        Expense.query.filter(Expense.payer_id == user.id).delete(synchronize_session=False)
        # Remove any remaining plan-participant records that reference this user
        PlanParticipant.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
