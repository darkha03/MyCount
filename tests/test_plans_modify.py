from backend.models import PlanParticipant, Plan, db


def test_modify_plan_updates_participants_and_name(client, user_factory, plan_factory):
    owner = user_factory("owner", password="pw")

    client.post("/login", data={"username": "owner", "password": "pw"}, follow_redirects=True)

    plan = plan_factory(owner=owner, name="Trip", participants=["Alice", "Bob"])

    resp = client.get(f"/plans/api/plans/{plan.hash_id}")
    assert resp.status_code == 200
    plan_data = resp.get_json()
    assert "participants" in plan_data

    # Build participants payload: swap to Alice slot, rename Bob -> Bobby,
    # and add a new participant 'Charlie'
    payload_participants = []
    for p in plan_data["participants"]:
        if p["name"] == "Alice":
            payload_participants.append(
                {"id": p["id"], "name": p["name"], "user_id": owner.id, "role": "owner"}
            )
        elif p["name"] == "Bob":
            payload_participants.append(
                {
                    "id": p["id"],
                    "name": "Bobby",
                    "user_id": p.get("user_id"),
                    "role": p.get("role", "member"),
                }
            )
        else:
            payload_participants.append(
                {"id": p["id"], "name": p["name"], "user_id": None, "role": "member"}
            )

    # Add a new participant slot assigned to `other`
    payload_participants.append({"name": "Charlie", "role": "member"})

    payload = {"name": "Trip 2025", "participants": payload_participants}

    resp2 = client.put(f"/plans/api/plans/{plan.hash_id}", json=payload)
    assert resp2.status_code == 200

    # Verify DB: owner was swapped to Alice slot
    assigned = PlanParticipant.query.filter_by(plan_id=plan.id, user_id=owner.id).first()
    assert assigned is not None
    assert assigned.role == "owner" and assigned.name == "Alice"

    # Verify DB: member role was swapped to owner slot
    assigned_owner = PlanParticipant.query.filter_by(plan_id=plan.id, name="owner").first()
    assert assigned_owner is not None
    assert assigned_owner.role == "member" and assigned_owner.user_id is None

    # Verify Bob renamed to Bobby
    renamed = PlanParticipant.query.filter_by(plan_id=plan.id, name="Bobby").first()
    assert renamed is not None

    # Verify new participant Charlie exists and is assigned to `other`
    charlie = PlanParticipant.query.filter_by(plan_id=plan.id, name="Charlie", user_id=None).first()
    assert charlie is not None
    assert charlie.role == "member"

    # Verify plan name updated
    updated_plan = db.session.get(Plan, plan.id)
    assert updated_plan.name == "Trip 2025"
