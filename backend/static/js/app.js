// frontend/js/app.js

const BASE_URL = "";

function displayExpenses() {
  const container = document.getElementById("expense-list");
  container.innerHTML = `<h3>Expense List</h3>`;

  fetch(`${BASE_URL}/api/expenses`)
    .then(response => response.json())
    .then(data => {
      data.forEach(expense => {
        const div = document.createElement("div");
        div.className = "expense-item";
        div.innerHTML = `
          <strong>${expense.payer}</strong> paid $${expense.amount} for ${expense.description}
          <hr>
        `;
        container.appendChild(div);
      });
    })
    .catch(err => console.error("Failed to load expenses", err));
}

function displayReimbursment() {
  const container = document.getElementById("reimbursment");
  container.innerHTML = `<h3>Reimbursment Summary</h3>`;
  fetch(`${BASE_URL}/api/reimbursements`)
    .then(response => response.json())
    .then(data => {
      data.forEach(entry => {
        const div = document.createElement("div");
        div.className = "reimbursment-item";
        div.innerHTML = `
          <strong>${entry.from}</strong> owed ${entry.to} $${entry.amount}
          <hr>
        `;
        container.appendChild(div);
      });
    })
    .catch(err => console.error("Failed to load reimbursment", err));
}

function displayPlanOverview() {
  const container = document.getElementById("plan-overview");
  container.innerHTML = `<h3>Plan Overview</h3>`;
  fetch(`${BASE_URL}/plans/api/plans`)
    .then(response => response.json())
    .then(data => {
      const div = document.createElement("div");
      div.className = "plan-overview-item";
      div.innerHTML = `
        <p>Total Expenses: $${data.total_expenses}</p>
        <p>Number of Participants: ${data.participant_count}</p>
        <hr>
      `;
      container.appendChild(div);
    })
    .catch(err => console.error("Failed to load plan overview", err));
  }

displayExpenses();
displayReimbursment();