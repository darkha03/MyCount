import json
from backend.models import Plan, PlanParticipant


def test_create_plan_minimal(client, user_factory):
    # Need a logged in user first
    user_factory("owner", password="pw")
    # Login user (session creation)
    client.post("/login", data={"username": "owner", "password": "pw"}, follow_redirects=True)

    payload = {"name": "Vacation", "participants": []}
    resp = client.post(
        "/plans/api/plans", data=json.dumps(payload), content_type="application/json"
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Vacation"
    assert "hash_id" in data

    # The plan should have exactly one participant (owner) even if list empty
    plan = Plan.query.filter_by(hash_id=data["hash_id"]).first()
    assert plan is not None
    participants = PlanParticipant.query.filter_by(plan_id=plan.id).all()
    assert len(participants) == 1
    assert participants[0].role == "owner"


def test_get_plans_api(client, user_factory, plan_factory):
    u = user_factory("alice", password="pw")
    client.post("/login", data={"username": "alice", "password": "pw"}, follow_redirects=True)

    # Make plan where alice is owner
    plan_factory(owner=u, name="Trip", participants=["Alice", "Bob"])

    resp = client.get("/plans/api/plans")
    assert resp.status_code == 200
    plans = resp.get_json()
    assert isinstance(plans, list)
    assert len(plans) == 1
    assert plans[0]["name"] == "Trip"
    assert "total_expenses" in plans[0]
