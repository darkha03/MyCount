from backend.models import PlanParticipant


def test_plan_join_get(client, user_factory, plan_factory):
    owner = user_factory("owner", password="pw")
    user_factory("member", password="pw")
    client.post("/login", data={"username": "member", "password": "pw"}, follow_redirects=True)
    plan = plan_factory(owner=owner, name="JoinMe", participants=["Alice", "Bob"])

    resp = client.get(f"/plans/api/plans/{plan.hash_id}/join")
    assert resp.status_code == 200
    data = resp.get_json()
    # Should be a list of participant dicts with name and id (id may be None for empty slots)
    assert isinstance(data, list)
    assert any(p["name"] == "Alice" for p in data)
    assert any(p["name"] == "Bob" for p in data)
    assert any(p["name"] == "owner" for p in data)


def test_plan_join_post(client, user_factory, plan_factory):
    owner = user_factory("owner", password="pw")
    member = user_factory("member", password="pw")
    client.post("/login", data={"username": "member", "password": "pw"}, follow_redirects=True)
    plan = plan_factory(owner=owner, name="JoinMe", participants=["Alice", "Bob"])

    # Join as "Alice"
    resp = client.post(
        f"/plans/api/plans/{plan.hash_id}/join",
        json={"participant_name": "Alice"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "joined" in data.get("message", "").lower()

    # Verify in DB
    pp = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=member.id).first()
    assert pp is not None
    assert pp.name == "Alice"


def test_plan_join_post_no_slot(client, user_factory, plan_factory):
    owner = user_factory("owner", password="pw")
    member = user_factory("member", password="pw")
    client.post("/login", data={"username": "member", "password": "pw"}, follow_redirects=True)
    plan = plan_factory(owner=owner, name="JoinMe", participants=["Alice", "Bob"])

    # Attempt to join as a name not in the participant list
    resp = client.post(
        f"/plans/api/plans/{plan.hash_id}/join",
        json={"participant_name": "Charlie"},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "no available slot" in data.get("error", "").lower()
    # Verify not in DB
    pp = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=member.id).first()
    assert pp is None


def test_plan_join_post_already_participant(client, user_factory, plan_factory):
    owner = user_factory("owner", password="pw")
    member = user_factory("member", password="pw")
    member2 = user_factory("member2", password="pw2")
    client.post("/login", data={"username": "member", "password": "pw"}, follow_redirects=True)
    plan = plan_factory(owner=owner, name="JoinMe", participants=["Alice", "Bob"])

    # First join as "Alice"
    resp = client.post(
        f"/plans/api/plans/{plan.hash_id}/join",
        json={"participant_name": "Alice"},
    )
    assert resp.status_code == 200

    # Attempt to join again as "Bob"
    resp = client.post(
        f"/plans/api/plans/{plan.hash_id}/join",
        json={"participant_name": "Bob"},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "already a participant" in data.get("error", "").lower()

    # Member2 joins as "Alice" should fail since taken
    client.post("/login", data={"username": "member2", "password": "pw2"}, follow_redirects=True)
    resp = client.post(
        f"/plans/api/plans/{plan.hash_id}/join",
        json={"participant_name": "Alice"},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "no available slot" in data.get("error", "").lower()

    # Verify still only one participant entry
    pps = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=member.id).all()
    assert len(pps) == 1
    pps2 = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=member2.id).all()
    assert len(pps2) == 0
