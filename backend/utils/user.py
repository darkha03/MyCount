from backend.models import Plan, PlanParticipant, Expense, db


def delete_guest_user(user):
    """
    Deletes a user and cascades deletions to their plans and related data.
    """
    try:
        for p in Plan.query.filter_by(created_by=user.id).all():
            db.session.delete(p)
        Expense.query.filter(Expense.payer_id == user.id).delete(synchronize_session=False)
        PlanParticipant.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
