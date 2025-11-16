document.addEventListener("DOMContentLoaded", () => {
  const content = document.getElementById("plan-content");
  const planId = content ? (content.dataset.planId || content.getAttribute('data-plan-id')) : null;
  console.log("Plan ID:", planId);

  // Load default section (expenses) when the page first loads
  if (planId) {
    try { initExpensesSection(planId); } catch (e) { /* initExpensesSection may be defined elsewhere */ }
  }

  const navLinks = document.querySelectorAll(".col-md-3 .nav-link");
  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();

      navLinks.forEach(l => l.classList.remove("active"));
      link.classList.add("active");

      const section = link.dataset.section;
      fetch(`/plans/${planId}/section/${section}`)
        .then(res => res.text())
        .then(html => {
          try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            content.replaceChildren(...Array.from(doc.body.childNodes));
          } catch (err) {
            while (content.firstChild) content.removeChild(content.firstChild);
            const t = document.createElement('div');
            t.textContent = html;
            content.appendChild(t);
          }
          if (section === "expenses") {
            try { initExpensesSection(planId); } catch (e) { }
          }
          if (section === "reimbursements") {
            try { initReimbursementSection(planId); } catch (e) { }
          }
          if (section === "statistics") {
            try { initStatisticsSection(); } catch (e) { }
          }
        });
    });
  });
});
