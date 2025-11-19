document.addEventListener("DOMContentLoaded", () => {
  const list = document.getElementById("plan-list");
  const addform = document.getElementById("add-plan-form");
  const input = document.getElementById("plan-name");
  const participantsList = document.getElementById("participants-list");
  const addParticipantBtn = document.getElementById("add-participant-btn");
  const joinBtn = document.getElementById("join-plan-btn");
  const joinResponse = document.getElementById("join-response");
  const joinFooter = document.getElementById("join-footer");
  const joinForm = document.getElementById("join-plan-form");
  const modifyForm = document.getElementById("modify-plan-form");
  const modifyPlanNameInput = document.getElementById("modify-plan-name");
  const modifyParticipantsList = document.getElementById("modify-participants-list");
  const addModifyParticipantBtn = document.getElementById("add-modify-participant-btn");
  const sharePlanModal = document.getElementById('sharePlanModal');
  const sharePlanHashInput = document.getElementById('share-plan-hash-id');
  const copyPlanHashBtn = document.getElementById('copy-plan-hash-btn');
  const copyFeedback = document.getElementById('copy-feedback');
  let currentModifyPlanId = null;
  let currentModifyPlanCurrentUserId = null;

  function clearElement(el) {
    if (!el) return;
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  // Helper to handle JSON responses: resolve with parsed JSON on OK,
  // otherwise try to extract an error message and throw.
  function handleJsonResponse(res) {
    if (res.ok) return res.json();
    return res.json().then(j => {
      const msg = (j && j.error) ? j.error : (res.statusText || 'Request failed');
      throw new Error(msg);
    }).catch(() => {
      throw new Error(res.statusText || 'Request failed');
    });
  }

  // Helper to handle responses that may not return JSON body on success
  function handleNoContentResponse(res) {
    if (res.ok) return res;
    return res.json().then(j => {
      throw new Error(j && j.error ? j.error : (res.statusText || 'Request failed'));
    }).catch(() => {
      throw new Error(res.statusText || 'Request failed');
    });
  }

  function refreshYouIndicators() {
    const rows = Array.from(modifyParticipantsList.querySelectorAll('.participant-row'));
    let yourRow = null;
    rows.forEach(r => {
      const inp = r.querySelector('input');
      const action = r.querySelector('.action-div');
      if (!action || !inp) return;
      clearElement(action);
      const userId = inp.dataset.userId || '';
      if (String(userId) === String(currentModifyPlanCurrentUserId) && currentModifyPlanCurrentUserId) {
        const badge = document.createElement('button');
        badge.type = 'button';
        badge.className = 'btn btn-sm btn-success';
        badge.textContent = 'You';
        badge.disabled = true;
        action.appendChild(badge);
        yourRow = r;
      } else {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-outline-secondary set-to-me-btn';
        btn.textContent = 'Swap';
        if ( inp.dataset.userId.length !== 0 ){
          btn.disabled = true;
        } else {
          btn.disabled = false;
        }
        btn.onclick = () => {
          if (inp.dataset.role === 'owner') {
            if (!confirm('This participant is the owner. Assigning yourself will transfer ownership. Continue?')) return;
          }
          inp.dataset.userId = currentModifyPlanCurrentUserId ? String(currentModifyPlanCurrentUserId) : '';
          inp.dataset.role = yourRow ? yourRow.querySelector('input').dataset.role : 'member';
          if (yourRow) {
            yourRow.querySelector('input').dataset.userId = "";
            yourRow.querySelector('input').dataset.role = "member";
          }
          refreshYouIndicators();
        };
        action.appendChild(btn);
      }
    });
  }

  // Validate an array of names: ensure non-empty and no duplicates (case-insensitive)
  function validateParticipantNames(names) {
    const trimmed = names.map(n => (n || '').trim());
    for (let i = 0; i < trimmed.length; i++) {
      if (!trimmed[i]) return { ok: false, message: `Participant ${i + 1} must have a name.` };
    }
    const lower = trimmed.map(n => n.toLowerCase());
    const set = new Set(lower);
    if (set.size !== lower.length) return { ok: false, message: 'Duplicate participant names detected.' };
    return { ok: true };
  }

  function showModalError(elId, message) {
    const container = document.getElementById(elId);
    if (!container) return;
    clearElement(container);
    const err = document.createElement('div');
    err.className = 'alert alert-danger';
    err.setAttribute('role','alert');
    err.textContent = message;
    container.appendChild(err);
  }

  function hideModalError(elId) {
    const container = document.getElementById(elId);
    if (!container) return;
    clearElement(container);
  }
  const resetJoinBtn = document.getElementById("reset-join-btn");
  if (resetJoinBtn) {
    resetJoinBtn.onclick = function() {
      joinForm.reset();
      clearElement(joinResponse);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.id = 'join-plan-btn';
      btn.className = 'btn btn-secondary m-3';
      btn.textContent = 'Search Plan';
      joinResponse.appendChild(btn);

      const confirmJoinBtn = document.getElementById("confirm-join-btn");
      if (confirmJoinBtn) {
        confirmJoinBtn.remove();
      }
      const joinBtn = document.getElementById("join-plan-btn");
      if (joinBtn) {
        joinBtn.onclick = joinBtnHandler;
      }
    };
  }

  function loadPlans() {
    fetch("/plans/api/plans")
    .then(handleJsonResponse)
    .then(data => {
      clearElement(list);
      data.forEach(plan => {
        const col = document.createElement("div");
        col.className = "col";

        const card = document.createElement('div');
        card.className = 'card mb-3 h-100';
        card.style.cursor = 'pointer';

        const body = document.createElement('div');
        body.className = 'card-body';

        const title = document.createElement('h4');
        title.className = 'card-title';
        title.textContent = plan.name || '';

        const created = document.createElement('p');
        created.className = 'card-text';
        created.textContent = plan.created_at ? (plan.created_at.slice(8,10) + '/' + plan.created_at.slice(5,7) + '/' + plan.created_at.slice(0,4)) : '';

        const participantsP = document.createElement('p');
        participantsP.className = 'card-text';
        participantsP.textContent = `Participants: ${Array.isArray(plan.participants) ? plan.participants.join(', ') : ''}`;

        const totalP = document.createElement('p');
        totalP.className = 'card-text';
        totalP.textContent = `Total Expenses: $${plan.total_expenses ? plan.total_expenses.toFixed(2) : '0.00'}`;

        const actions = document.createElement('div');
        actions.className = 'd-flex justify-content-end gap-2';

        const viewLink = document.createElement('a');
        viewLink.className = 'btn btn-primary';
        viewLink.href = `/plans/${plan.hash_id}`;
        viewLink.textContent = 'View Plan';

        const modifyBtn = document.createElement('button');
        modifyBtn.className = 'btn btn-sm btn-outline-primary modify-plan-btn';
        modifyBtn.setAttribute('data-id', plan.hash_id);
        modifyBtn.textContent = 'Modify';

        const shareBtn = document.createElement('button');
        shareBtn.className = 'btn btn-sm btn-outline-primary share-plan-btn';
        shareBtn.setAttribute('data-id', plan.hash_id);
        shareBtn.textContent = 'Share';

        const delBtn = document.createElement('button');
        delBtn.className = 'btn btn-danger btn-sm delete-plan-btn';
        delBtn.setAttribute('data-id', plan.hash_id);
        delBtn.textContent = 'Delete';

        actions.appendChild(viewLink);
        actions.appendChild(modifyBtn);
        actions.appendChild(shareBtn);
        actions.appendChild(delBtn);

        body.appendChild(title);
        const createdWrapper = document.createElement('p');
        createdWrapper.className = 'card-text';
        createdWrapper.appendChild(document.createTextNode('Created at: '));
        createdWrapper.appendChild(document.createTextNode(created.textContent));
        body.appendChild(createdWrapper);
        body.appendChild(participantsP);
        body.appendChild(totalP);
        body.appendChild(actions);

        card.appendChild(body);
        col.appendChild(card);

        card.onclick = () => { window.location.href = `/plans/${plan.hash_id}`; };

        // Prevent card click when delete is pressed
        delBtn.onclick = (e) => {
          e.stopPropagation();
          if (confirm("Are you sure you want to delete this plan?")) {
            deletePlan(plan.hash_id);
          }
        };

        list.appendChild(col);
      });
      attachModifyHandlers();
      attachShareHandlers();
    }).catch(err => {
      alert('Failed to load plans: ' + (err && err.message ? err.message : 'Network error'));
    });
  }

  function attachModifyHandlers() {
    document.querySelectorAll('.modify-plan-btn').forEach(btn => {
      btn.onclick = function(e) {
        e.stopPropagation();
        currentModifyPlanId = btn.getAttribute("data-id");
        fetch(`/plans/api/plans/${currentModifyPlanId}`)
          .then(handleJsonResponse)
          .then(plan => {
            modifyPlanNameInput.value = plan.name;
            clearElement(modifyParticipantsList);
            // plan.participants is an array of objects: {id, name, user_id, role}
            plan.participants.forEach((p, idx) => {
              const row = document.createElement('div');
              row.className = 'd-flex gap-2 align-items-center mb-2 participant-row';

              const input = document.createElement('input');
              input.type = 'text';
              input.className = 'form-control participant-input';
              input.required = true;
              input.value = p.name || '';
              input.placeholder = `Participant ${idx + 1}`;
              input.dataset.ppId = p.id || '';
              input.dataset.userId = p.user_id === null ? '' : String(p.user_id);
              input.dataset.role = p.role || 'member';

              const actionDiv = document.createElement('div');
              actionDiv.className = 'd-flex align-items-center action-div';

              row.appendChild(input);
              row.appendChild(actionDiv);
              modifyParticipantsList.appendChild(row);
            });

            // store current user's id for use by Set-to-me buttons
            currentModifyPlanCurrentUserId = plan.current_user_id;
            refreshYouIndicators();
            const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modifyPlanModal'));
            modal.show();
          }).catch(err => {
            showModalError('modify-plan-error', 'Failed to load plan: ' + (err && err.message ? err.message : 'Network error'));
          });
      };
    });
  }
  addModifyParticipantBtn.onclick = () => {
    const count = modifyParticipantsList.querySelectorAll('.participant-row').length + 1;
    const row = document.createElement('div');
    row.className = 'd-flex gap-2 align-items-center mb-2 participant-row';
    const input = document.createElement("input");
    input.type = "text";
    input.className = "form-control participant-input";
    input.placeholder = `Participant ${count}`;
    input.required = true;
    input.dataset.ppId = '';
    input.dataset.userId = '';
    input.dataset.role = 'member';
    const actionDiv = document.createElement('div');
    actionDiv.className = 'd-flex align-items-center action-div';
    // hide modify errors when typing
    input.addEventListener('input', () => hideModalError('modify-plan-error'));
    row.appendChild(input);
    row.appendChild(actionDiv);
    modifyParticipantsList.appendChild(row);
    refreshYouIndicators();
  };

  function attachShareHandlers() {
    document.querySelectorAll('.share-plan-btn').forEach(btn => {
      btn.onclick = function(e) {
        e.stopPropagation();
        const hashId = btn.getAttribute("data-id");
        sharePlanHashInput.value = hashId;
        copyFeedback.style.display = "none";
        const modal = bootstrap.Modal.getOrCreateInstance(sharePlanModal);
        modal.show();
      };
    });
  }

  copyPlanHashBtn.onclick = function() {
    navigator.clipboard.writeText(sharePlanHashInput.value)
      .then(() => {
        copyFeedback.style.display = "block";
        setTimeout(() => { copyFeedback.style.display = "none"; }, 1500);
      })
      .catch(() => {
        // Optionally, show an error message or fallback
        copyFeedback.style.display = "none";
        alert("Failed to copy to clipboard. Please copy manually.");
      });
  };

  function joinBtnHandler(e) {
    e.preventDefault();
    const planHashId = document.getElementById("plan-hash-id").value;
    fetch(`/plans/api/plans/${planHashId}/join`, {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    })
    .then(handleJsonResponse)
    .then(data =>{
      clearElement(joinResponse);
      const selLabel = document.createElement('label');
      selLabel.className = 'form-label';
      selLabel.textContent = 'Select Your Name';
      joinResponse.appendChild(selLabel);
      if (Array.isArray(data) && data.length > 0) {
        const select = document.createElement("select");
        select.className = "form-select mb-2";
        select.name = "participant_name";
        data.forEach(participant => {
          if (participant.id === null) {
            const option = document.createElement("option");
            option.value = participant.name;
            option.textContent = participant.name;
            select.appendChild(option);
          }
        });
        joinResponse.appendChild(select);
        const confirmJoinBtn = document.createElement("button");
        confirmJoinBtn.type = "submit";
        confirmJoinBtn.className = "btn btn-primary";
        confirmJoinBtn.id = "confirm-join-btn";
        confirmJoinBtn.textContent = "Join Plan";
        joinFooter.appendChild(confirmJoinBtn);
        confirmJoinBtn.onclick = e => {
          joinForm.onsubmit(e);
        };
      } else {
        clearElement(joinResponse);
        const err = document.createElement('div');
        err.className = 'alert alert-danger';
        err.textContent = data.error || 'Unknown error';
        joinResponse.appendChild(err);
      }
    }).catch(err => {
      clearElement(joinResponse);
      const errEl = document.createElement('div');
      errEl.className = 'alert alert-danger';
      errEl.textContent = err && err.message ? err.message : 'Failed to fetch plan';
      joinResponse.appendChild(errEl);
    });
  }

  window.deletePlan = function(id) {
    fetch(`/plans/api/plans/${id}`, { method: "DELETE" })
      .then(handleNoContentResponse)
      .then(() => loadPlans())
      .catch(err => alert('Failed to delete plan: ' + (err && err.message ? err.message : 'Network error')));
  };

  addParticipantBtn.onclick = () => {
    const count = participantsList.querySelectorAll('.participant-input').length + 1;
    const input = document.createElement("input");
    input.type = "text";
    input.className = "form-control mb-2 participant-input";
    input.placeholder = `Participant ${count}`;
    input.required = true;
    input.addEventListener('input', () => hideModalError('add-plan-error'));
    participantsList.appendChild(input);
  };

  addform.onsubmit = e => {
    e.preventDefault();
    const planName = input.value;
    const participantInputs = participantsList.querySelectorAll(".participant-input");
    const participants = Array.from(participantInputs).map(p => p.value.trim());

    // client-side validation
    const valid = validateParticipantNames(participants);
    if (!valid.ok) {
      showModalError('add-plan-error', valid.message);
      return;
    }
    hideModalError('add-plan-error');

    fetch("/plans/api/plans", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: planName, participants })
    }).then(handleJsonResponse).then(() => {
      input.value = "";
      clearElement(participantsList);
      const pinput = document.createElement('input');
      pinput.type = 'text';
      pinput.className = 'form-control mb-2 participant-input';
      pinput.placeholder = 'Participant 1 (You)';
      pinput.required = true;
      // hide any existing error when the user starts typing
      pinput.addEventListener('input', () => hideModalError('add-plan-error'));
      participantsList.appendChild(pinput);
      const modal = bootstrap.Modal.getInstance(document.getElementById('addPlanModal'));
      modal.hide();
      loadPlans();
    }).catch(err => {
      showModalError('add-plan-error', err && err.message ? err.message : 'Failed to create plan');
    });
  };

  // Reset Add Plan modal inputs when it is hidden so stale values don't leak
  // into future create operations.
  const addModalEl = document.getElementById('addPlanModal');
  addModalEl.addEventListener('hidden.bs.modal', () => {
    input.value = '';
    clearElement(participantsList);
    const pinput = document.createElement('input');
    pinput.type = 'text';
    pinput.className = 'form-control mb-2 participant-input';
    pinput.placeholder = 'Participant 1 (You)';
    pinput.required = true;
    pinput.addEventListener('input', () => hideModalError('add-plan-error'));
    participantsList.appendChild(pinput);
    hideModalError('add-plan-error');
  });

  joinBtn.onclick = e => {
    joinBtnHandler(e);
  };

  joinForm.onsubmit = e => {
    e.preventDefault();
    const planHashId = document.getElementById("plan-hash-id").value;
    const selectedName = joinForm.participant_name.value;      
    fetch(`/plans/api/plans/${planHashId}/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ participant_name: selectedName })
    }).then(handleJsonResponse).then(() => {
      const modal = bootstrap.Modal.getInstance(document.getElementById('joinPlanModal'));
      modal.hide();
      loadPlans();
    }).catch(err => {
      clearElement(joinResponse);
      const errEl = document.createElement('div');
      errEl.className = 'alert alert-danger';
      errEl.textContent = err && err.message ? err.message : 'Failed to join plan';
      joinResponse.appendChild(errEl);
    });
  };

  modifyForm.onsubmit = e => {
    e.preventDefault();
    const planName = modifyPlanNameInput.value;
    const rows = Array.from(modifyParticipantsList.querySelectorAll('.participant-row'));
    const names = rows.map(r => {
      const inp = r.querySelector('input');
      return inp ? inp.value.trim() : '';
    });

    // client-side validation
    const valid = validateParticipantNames(names);
    if (!valid.ok) {
      showModalError('modify-plan-error', valid.message);
      return;
    }
    hideModalError('modify-plan-error');

    const participants = rows.map(r => {
      const inp = r.querySelector('input');
      const ppId = inp.dataset.ppId || '';
      const userId = inp.dataset.userId ? Number(inp.dataset.userId) : null;
      const role = inp.dataset.role || 'member';
      return { id: ppId ? Number(ppId) : undefined, name: inp.value.trim(), user_id: userId, role };
    }).filter(p => p.name);

    const payload = { name: planName, participants: participants };

    fetch(`/plans/api/plans/${currentModifyPlanId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then(handleJsonResponse).then(() => {
      const modal = bootstrap.Modal.getInstance(document.getElementById('modifyPlanModal'));
      modal.hide();
      loadPlans();
    }).catch(err => {
      showModalError('modify-plan-error', err && err.message ? err.message : 'Failed to modify plan');
    });
  };
  // Clear Modify Plan modal when hidden to avoid leaving stale participant
  // inputs in the DOM which could be picked up elsewhere.
  const modifyModalEl = document.getElementById('modifyPlanModal');
  modifyModalEl.addEventListener('hidden.bs.modal', () => {
    clearElement(modifyParticipantsList);
    modifyPlanNameInput.value = '';
    currentModifyPlanId = null;
    currentModifyPlanCurrentUserId = null;
    hideModalError('modify-plan-error');
  });
  loadPlans();
});
