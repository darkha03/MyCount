import openpyxl
from io import BytesIO
from backend.models import PlanParticipant, ExpenseShare
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


def build_plan_xlsx_stream(plan, expenses):
    """Create an XLSX workbook for a plan and return a BytesIO stream."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Plan {plan.name} Expenses"

    # Prepare participant columns
    plan_participants = PlanParticipant.query.filter_by(plan_id=plan.id).all()
    plan_participant_names = [p.name for p in plan_participants]

    # Header
    header = ["Date", "Description", "Amount", "Payer"] + plan_participant_names
    ws.append(header)

    # Rows
    for exp in expenses:
        shares = ExpenseShare.query.filter_by(expense_id=exp.id).all()
        share_map = {s.name: (s.amount if s.amount is not None else 0) for s in shares}

        row = [
            exp.date.strftime("%Y-%m-%d") if getattr(exp, "date", None) else "",
            exp.description or "",
            float(exp.amount or 0),
            exp.payer_name or "",
        ]

        for pname in plan_participant_names:
            amt = share_map.get(pname, 0)
            try:
                row.append(float(amt))
            except Exception:
                row.append(0.0)

        ws.append(row)

    # Numeric formatting for amount and shares
    participant_count = len(plan_participant_names)
    amount_col_idx = 3
    last_share_col_idx = amount_col_idx + participant_count
    for row_cells in ws.iter_rows(min_row=2, min_col=amount_col_idx, max_col=last_share_col_idx):
        for cell in row_cells:
            cell.number_format = "0.00"

    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if cell.value is not None:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[column].width = max_length + 2

    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return out


def build_plan_csv(plan, expenses):
    """Build CSV content for a plan's expenses.

    Returns a string containing CSV data with header:
    date,description,amount,payer,<participant1>,<participant2>,...
    Each row contains the expense fields and one column per plan participant
    with the participant's share for that expense (formatted with two decimals).
    """
    import csv
    import io

    plan_participants = PlanParticipant.query.filter_by(plan_id=plan.id).all()
    plan_participant_names = [p.name for p in plan_participants]

    output = io.StringIO()
    writer = csv.writer(output)

    header = ["date", "description", "amount", "payer"] + plan_participant_names
    writer.writerow(header)

    for exp in expenses:
        shares = ExpenseShare.query.filter_by(expense_id=exp.id).all()
        share_map = {s.name: (s.amount if s.amount is not None else 0) for s in shares}

        row = [
            exp.date.isoformat() if getattr(exp, "date", None) else "",
            exp.description or "",
            f"{(exp.amount or 0):.2f}",
            exp.payer_name or "",
        ]

        for pname in plan_participant_names:
            amt = share_map.get(pname, 0)
            try:
                row.append(f"{float(amt):.2f}")
            except Exception:
                row.append("0.00")

        writer.writerow(row)

    csv_text = output.getvalue()
    output.close()
    return csv_text
