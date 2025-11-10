from backend.routes.plans import calculate_balance, calculate_expense, calculate_real_expense


def test_statistics_reimbursement_excluded():
    expenses = [
        {
            "id": 1,
            "name": "Dinner",
            "amount": 60.0,
            "payer": "Alice",
            "participants": ["Alice", "Bob"],
            "amount_details": {"Alice": 30.0, "Bob": 30.0},
        },
        {
            "id": 2,
            "name": "Reimbursement",
            "amount": 30.0,
            "payer": "Bob",
            "participants": ["Alice", "Bob"],
            "amount_details": {"Alice": 30.0, "Bob": 0.0},
        },
    ]

    balances = calculate_balance(expenses)
    total = calculate_expense(expenses)
    real = calculate_real_expense(expenses)

    # Total expense should exclude the Reimbursement entry
    assert total == {"Alice": 30.0, "Bob": 30.0}

    # Balance: After reimbursement, Alice should owe 0, Bob should owe 0
    assert balances.get("Alice") == 0
    assert balances.get("Bob") == 0

    # Real expense: Dinner 60 by Alice, reimbursement 30 from Bob makes totals equalized
    assert real.get("Alice") == 30.0
    assert real.get("Bob") == 30.0
