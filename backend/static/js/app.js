// frontend/js/app.js

function displayExpenses(expenses) {
  const container = document.getElementById("expense-list");
  container.innerHTML = "";

  expenses.forEach(expense => {
    const div = document.createElement("div");
    div.className = "expense-item";
    div.innerHTML = `
      <strong>${expense.description}</strong><br>
      Paid by <em>${expense.payer}</em> - $${expense.amount}<br>
      Shared with: ${expense.participants.join(", ")}
      <hr>
    `;
    container.appendChild(div);
  });
}

fetch("http://127.0.0.1:5000/api/expenses")
  .then(response => response.json())
  .then(data => displayExpenses(data))
  .catch(err => console.error("Failed to load expenses", err));
