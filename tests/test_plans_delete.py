from backend.models import Plan, PlanParticipant


def test_plan_delete(client, user_factory, plan_factory):
    u = user_factory("owner", password="pw")
    client.post("/login", data={"username": "owner", "password": "pw"}, follow_redirects=True)

    plan = plan_factory(owner=u, name="DeleteMe", participants=["Alice", "Bob"])

    resp = client.delete(f"/plans/api/plans/{plan.hash_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "You left plan DeleteMe."

    # Ensure plan is deleted
    deleted_plan = Plan.query.filter_by(id=plan.id).first()
    assert deleted_plan is None

    # Ensure participants are also deleted
    participants = PlanParticipant.query.filter_by(plan_id=plan.id).all()
    assert len(participants) == 0


def test_plan_delete_unauthorized(client, user_factory, plan_factory):
    owner = user_factory("owner", password="pw")
    user_factory("other", password="pw")
    client.post("/login", data={"username": "other", "password": "pw"}, follow_redirects=True)

    plan = plan_factory(owner=owner, name="NotYours", participants=["Alice", "Bob"])

    resp = client.delete(f"/plans/api/plans/{plan.hash_id}")
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["error"] == "You do not have permission to delete this plan"

    # Ensure plan still exists
    existing_plan = Plan.query.filter_by(id=plan.id).first()
    assert existing_plan is not None


def test_plan_delete_not_owner(client, user_factory, plan_factory):
    owner = user_factory("owner", password="pw")
    member = user_factory("member", password="pw")
    client.post("/login", data={"username": "member", "password": "pw"}, follow_redirects=True)
    plan = plan_factory(owner=owner, name="GroupTrip", participants=[member, "Alice", "Bob"])
    resp = client.delete(f"/plans/api/plans/{plan.hash_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "You left plan GroupTrip."
    # Ensure member is removed from participants
    participant = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=member.id).first()
    assert participant is None
    # Ensure plan still exists
    existing_plan = Plan.query.filter_by(id=plan.id).first()
    assert existing_plan is not None


def test_plan_delete_owner_with_members(client, user_factory, plan_factory):
    owner = user_factory("owner", password="pw")
    member = user_factory("member", password="pw")
    client.post("/login", data={"username": "owner", "password": "pw"}, follow_redirects=True)
    plan = plan_factory(owner=owner, name="FamilyTrip", participants=[member, "Alice", "Bob"])
    resp = client.delete(f"/plans/api/plans/{plan.hash_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "You left plan FamilyTrip."
    # Ensure plan is existing
    existing_plan = Plan.query.filter_by(id=plan.id).first()
    assert existing_plan is not None
    # Ensure owner is removed from participants
    owner_participant = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=owner.id).first()
    assert owner_participant is None
    # Ensure member role is promoted to owner
    new_owner_participant = PlanParticipant.query.filter_by(
        plan_id=plan.id, user_id=member.id
    ).first()
    assert new_owner_participant is not None
    assert new_owner_participant.role == "owner"
    # Ensure other participants still exist
    other_participants = PlanParticipant.query.filter(
        PlanParticipant.plan_id == plan.id, PlanParticipant.role == "member"
    ).all()
    assert len(other_participants) == 3


def test_plan_delete_not_found(client, user_factory):
    user_factory("owner", password="pw")
    client.post("/login", data={"username": "owner", "password": "pw"}, follow_redirects=True)

    resp = client.delete("/plans/api/plans/INVALIDHASH")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "Plan not found"
