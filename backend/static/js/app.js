// frontend/js/app.js

const BASE_URL = "http://127.0.0.1:5000";

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

displayExpenses();
displayReimbursment();