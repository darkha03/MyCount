let expenseListenerAttached = false;
let expenseDeleteListenerAttached = false;

function initExpenseDeleteListener(planId) {
  const planContent = document.getElementById("plan-content");
  if (!planContent) return;
  if (expenseDeleteListenerAttached) return;
  planContent.addEventListener("click", function(e) {
    const deleteButton = e.target.closest(".btn-danger");
    if (deleteButton) {
      if (!confirm("Are you sure you want to delete this expense?")) {
        return;
      }
      fetch(`/plans/${planId}/section/expenses/${deleteButton.dataset.id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json"
      }})
      .then(res => {
        if (!res.ok) {
          throw new Error("Failed to delete expense");
        }
        return res.json();
      })
      .then(() => {
        window.location.href = `/plans/${planId}`;
      })
      .catch(err => {
        alert("Error deleting expense: " + err.message);
      });
    }
  })
  expenseDeleteListenerAttached = true;
}
function initExpenseClickListener(planId) {
  const planContent = document.getElementById("plan-content");
  if (!planContent) return;
  if (expenseListenerAttached) return; // Prevent multiple listeners

  planContent.addEventListener("click", function(e) {
    const expenseDiv = e.target.closest(".expense-item");
    if (expenseDiv) {
      const li = expenseDiv.querySelector("li[data-id]");
      const expenseId = li ? li.getAttribute("data-id") : null;
      if (expenseId) {
        loadExpenseDetails(planId, expenseId);
      }
    }
  });
  expenseListenerAttached = true;
}

function loadExpenseDetails(planId, expenseId) {
  const planContent = document.getElementById("plan-content");
  if (!planContent) return;
  fetch(`/plans/${planId}/section/expenses/${expenseId}`)
    .then(res => res.text())
    .then(html => {
      planContent.innerHTML = html;
      initExpenseDeleteListener(planId); // Reinitialize delete listener
      initExpensesForm(planId, options = {method: "PUT", url: `/plans/${planId}/section/expenses/${expenseId}`, 
            modalId:"modifyExpenseModal", onSuccess: () => loadExpenseDetails(planId, expenseId)});
    });
}

function initExpensesForm(planId, options = {}) {
  const form = document.getElementById("add-expense-form");
  if (!form) return;

  const input = document.getElementById("expense-name");
  const participantsList = document.getElementById("participants-list");
  const splitEvenlyCheckbox = document.getElementById("split-evenly");
  const expenseAmountInput = document.getElementById("expense-amount");
  const participantCheckboxes = Array.from(participantsList.querySelectorAll(".form-check-input"));

  function updateSplitAmounts() {
    const total = parseFloat(expenseAmountInput.value) || 0;
    const participantRows = Array.from(participantsList.querySelectorAll(".d-flex"));
    const checkedRows = participantRows.filter(row => row.querySelector(".form-check-input").checked);
    const amountInputs = checkedRows.map(row => row.querySelector(".participant-amount"));

    
      const split = checkedRows.length > 0 ? (total / checkedRows.length) : 0;
      amountInputs.forEach(input => {
        input.value = split.toFixed(2);
        //input.disabled = true;
      });

  }

  splitEvenlyCheckbox.addEventListener("change", (e) =>{
    const isChecked = e.target.checked;
    const participantRows = Array.from(participantsList.querySelectorAll(".d-flex"));
    const amountInputs = participantRows.map(row => row.querySelector(".participant-amount"));

    if (isChecked) {
      amountInputs.forEach(input => {
        input.disabled = true;
        input.value = "0.00"; // Reset to 0 when split evenly
      });
      updateSplitAmounts();
    } else {
      amountInputs.forEach(input => {
        input.disabled = false; // Enable inputs for manual entry
      });
    }
  });
  expenseAmountInput.addEventListener("input", updateSplitAmounts);
  participantsList.addEventListener("change", (e) => {
    if (e.target.classList.contains("form-check-input")) {
      updateSplitAmounts();
    }
  });
  participantCheckboxes.forEach(checkbox => {
    checkbox.addEventListener("change", (e) => {
      const row = e.target.closest(".d-flex");
      const amountInput = row.querySelector(".participant-amount");
      if (!e.target.checked) {
        amountInput.disabled = true;
        amountInput.value = "0.00";
      }
      else {
        amountInput.disabled = false;
      }
      });
    updateSplitAmounts();
  });

  participantsList.addEventListener("input", (e) => {
    if (!splitEvenlyCheckbox.checked && e.target.classList.contains("participant-amount")) {
      const total = parseFloat(expenseAmountInput.value) || 0;
      const participantRows = Array.from(participantsList.querySelectorAll(".d-flex"));
      const checkedRows = participantRows.filter(row => row.querySelector(".form-check-input").checked);
      const amountInputs = checkedRows.map(row => row.querySelector(".participant-amount"));

      const changedInput = e.target;
      const changedIndex = amountInputs.indexOf(changedInput);

      let remaining = total - (parseFloat(changedInput.value) || 0);

      amountInputs.forEach((input, idx) => {
        if (idx !== changedIndex) {
          amountInputs[idx].value = remaining / (amountInputs.length - 1) || 0;
        }
      });

      
    }
  });

  // Initial fill
  updateSplitAmounts();

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const expenseName = input.value;
    const expenseAmount = expenseAmountInput.value;
    const payer = document.getElementById("expense-payer").value;
    const date = document.getElementById("expense-date").value;
    const participants = Array.from(participantsList.querySelectorAll(".participant-input")).map(input => input.value);
    const amounts = Array.from(participantsList.querySelectorAll(".participant-amount")).map(input => input.value);

    fetch(options.url || `/plans/${planId}/section/expenses`, {
      method: options.method || "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        name: expenseName,
        amount: parseFloat(expenseAmount),
        payer: payer,
        date: date,
        participants: participants,
        amounts: amounts
      })
    })
    .then(() => {
      // Optionally reset form here
      const modal = document.getElementById(options.modalId || "addExpenseModal");
      const bsModal = bootstrap.Modal.getInstance(modal) || bootstrap.Modal.getOrCreateInstance(modal);
      bsModal.hide();
      if (typeof options.onSuccess === "function") {
        options.onSuccess();
      } else {
        loadExpenses(planId);
      }
    });
  });
}

function loadExpenses(planId) {
  fetch(`/plans/${planId}/section/expenses`)
    .then(res => res.text())
    .then(html => {
      const planContent = document.getElementById("plan-content");
      planContent.innerHTML = html;
      initExpenseClickListener(planId);
      initExpensesForm(planId);
    });
}

function initExpensesSection(planId) {
  loadExpenses(planId);
}

let reimbursementListenerAttached = false;

function loadReimbursements(planId) {
  fetch(`/plans/${planId}/section/reimbursements`)
    .then(res => res.text())
    .then(html => {
      const planContent = document.getElementById("plan-content");
      planContent.innerHTML = html;
    });
}

function initReimbursementSection(planId) {
  const planContent = document.getElementById("plan-content");
  if (!planContent) return;
  if (reimbursementListenerAttached) return;

  planContent.addEventListener("click", function(e) {
    if (e.target.classList.contains("paid-btn")) {
      const from = e.target.getAttribute("data-from");
      const to = e.target.getAttribute("data-to");
      const amount = e.target.getAttribute("data-amount");
      fetch(`/plans/${planId}/section/expenses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: "Reimbursement",
          amount: amount,
          payer: from,
          date: new Date().toISOString().split('T')[0],
          participants: [to],
          amounts: [amount]
        })
      })
      .then(() => {
        loadReimbursements(planId);
      });
    }
  });
  reimbursementListenerAttached = true;
}

function loadStatistics(planId) {
  fetch(`/plans/${planId}/section/statistics`)
    .then(res => res.text())
    .then(html => {
      const planContent = document.getElementById("plan-content");
      planContent.innerHTML = html;
      renderBalanceChart();
    });
    
}

function renderStatisticChart() {
  const canvas = document.getElementById('balanceChart');
  if (!canvas) return;  
  const balanceList = document.getElementById('balance-list');
  const totalExpenseList = document.getElementById('total-expense-list');
  const realExpenseList = document.getElementById('real-expense-list');
  if (!balanceList && !totalExpenseList && !realExpenseList) {
    console.warn("Required lists are missing in the DOM.");
    const ctx = canvas.getContext && canvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const labels = [];
  const balaceData = [];
  const totalExpenseData = [];
  const realExpenseData = [];

  if (balanceList){
    balanceList.querySelectorAll('li').forEach(item => {
      const name = item.querySelector('.participant-name')?.textContent.trim();
      const amount = item.querySelector('.participant-amount')?.textContent.trim();
      if (name && amount) {
        labels.push(name);
        balaceData.push(parseFloat(amount));
      }
    });
  }

  if (totalExpenseList) {
    totalExpenseList.querySelectorAll('li').forEach(item => {
      const name = item.querySelector('.participant-name')?.textContent.trim();
      const amount = item.querySelector('.participant-amount')?.textContent.trim();
      if (name && amount) {
        totalExpenseData.push(parseFloat(amount));
      }
    });
  }

  if (realExpenseList) {
    realExpenseList.querySelectorAll('li').forEach(item => {
      const name = item.querySelector('.participant-name')?.textContent.trim();
      const amount = item.querySelector('.participant-amount')?.textContent.trim();
      if (name && amount) {
        realExpenseData.push(parseFloat(amount));
      }
    });
  }

  console.log("Rendering chart with labels:", labels);
  console.log("Rendering chart with data:", balaceData, totalExpenseData, realExpenseData);
 
  if (labels.length === 0) {
    console.info("No labeled data to render chart");
    const ctx = canvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }
  const planTotal = (totalExpenseData.length ? totalExpenseData.reduce((a,b)=>a+b,0)
                    : (balaceData.length ? balaceData.reduce((a,b)=>a+b,0) : 0));
  console.log("Plan total for horizontal line:", planTotal);
  
  const ctx = canvas.getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Balance',
        data: balaceData,
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      },
      {
        label: 'Total Expense',
        data: totalExpenseData,
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1
      },
      {
        label: 'Real Expense',
        data: realExpenseData,
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Plan total expense: $${planTotal.toFixed(2)}`,
          font: { size: 16 }
        },
        legend: { position: 'top' }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

function initStatisticsSection() {
  renderStatisticChart();
}