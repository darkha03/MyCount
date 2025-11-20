document.addEventListener("DOMContentLoaded", () => {
  const content = document.getElementById("plan-content");
  const planId = content ? (content.dataset.planId || content.getAttribute('data-plan-id')) : null;
  console.log("Plan ID:", planId);

  // Load default section (expenses) when the page first loads
  if (planId) {
    try { initExpensesSection(planId); } catch (e) {}
  }

  const navLinks = document.querySelectorAll(".col-md-3 .nav-link");
  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();

      navLinks.forEach(l => l.classList.remove("active"));
      link.classList.add("active");

      const section = link.dataset.section;
      fetch(`/plans/${planId}/section/${section}`)
        .then(res => {
          if (!res.ok) return res.text().then(t => { throw new Error(t || res.statusText); });
          return res.text();
        })
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
        })
        .catch(err => {
          console.error('Failed to load section', err);
          while (content.firstChild) content.removeChild(content.firstChild);
          const alertDiv = document.createElement('div');
          alertDiv.className = 'alert alert-danger';
          alertDiv.textContent = 'Failed to load section: ' + (err.message || 'Unknown error');
          content.appendChild(alertDiv);
        });
    });
  });
});
