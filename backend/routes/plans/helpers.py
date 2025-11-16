"""Helper utilities for the plans blueprint.

Contains participant validation and update helpers extracted from the
route handlers to keep the routes concise and testable.
"""

from typing import List, Tuple, Optional


def validate_participant_name_list(participants: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate a list of participant names (used by add_plan).

    Returns (True, None) on success or (False, error_message) on failure.
    Validation: must be a list of non-empty strings, names unique (case-insensitive).
    """
    if not isinstance(participants, list):
        return False, "Participants must be a list"
    norm_names = []
    for i, n in enumerate(participants):
        if not isinstance(n, str) or not n.strip():
            return False, f"Participant names must be non-empty strings (index {i})"
        norm_names.append(n.strip().lower())
    if len(set(norm_names)) != len(norm_names):
        return False, "Duplicate participant names detected"
    return True, None


def validate_participants_payload(participants_data: List[dict]) -> Tuple[bool, Optional[str]]:
    """Validate the participants payload used by modify_plan.

    participants_data should be a list of dicts with a non-empty `name` field.
    Names must be unique (case-insensitive).
    """
    if not isinstance(participants_data, list):
        return False, "Participants must be a list"
    seen = set()
    for idx, item in enumerate(participants_data):
        name = (item.get("name") or "").strip()
        if not name:
            return False, f"Participant names must be non-empty (index {idx})"
        key = name.lower()
        if key in seen:
            return False, "Duplicate participant names detected"
        seen.add(key)
    return True, None


def apply_participants_updates(plan, participants_data: List[dict]):
    """Apply updates/creates for participants for the provided ``plan``.

    This mutates PlanParticipant rows and adds new ones to the current DB
    session but does not commit.
    """
    from backend.models import PlanParticipant, db

    existing = {p.id: p for p in PlanParticipant.query.filter_by(plan_id=plan.id).all()}
    for item in participants_data:
        pp_id = item.get("id")
        if pp_id and pp_id in existing:
            pp = existing[pp_id]
            pp.name = item.get("name", pp.name)
            if "user_id" in item:
                pp.user_id = item.get("user_id")
            if "role" in item:
                pp.role = item.get("role")
        else:
            new_pp = PlanParticipant(
                user_id=item.get("user_id"),
                plan_id=plan.id,
                role=item.get("role", "member"),
                name=item.get("name", ""),
            )
            db.session.add(new_pp)
