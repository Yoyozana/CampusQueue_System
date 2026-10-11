/* ============================================================
   CampusQueue — Service card component
   Draws the campus service cards (icon, status, name, location,
   waiting count, button) for the student and admin pages.
   ============================================================ */

/**
 * @param {HTMLElement} grid     container with class "grid"
 * @param {object} opts
 *   unit       "students waiting" (student) or "waiting" (admin)
 *   button     (service) => { label, disabled, onClick }
 *   cardClass  (service) => extra CSS class for the card (optional)
 */
function renderServiceCards(grid, opts) {
  grid.innerHTML = "";
  if (!Queue.services().length) { grid.innerHTML = `<div class="empty-state">No queues found in the database.</div>`; return; }
  Queue.services().forEach(s => {
    const status = Queue.status(s.id);
    const count = Queue.waitingCount(s.id);
    const btn = opts.button(s, status);
    const unit = opts.unit === "students waiting" ? (count === 1 ? "student waiting" : "students waiting") : opts.unit;

    const card = document.createElement("div");
    card.className = "service-card" + (opts.cardClass ? " " + (opts.cardClass(s) || "") : "");
    card.innerHTML = `
      <div class="icon-badge" aria-hidden="true">${escapeHtml(s.icon)}</div>
      <span class="status-pill status-${escapeHtml(status)}">${escapeHtml(status)}</span>
      <div class="s-name">${escapeHtml(s.name)}</div>
      <div class="s-loc">${escapeHtml(s.location)}</div>
      <div class="s-count">${count} ${unit}</div>
      <button type="button" class="btn-join"${btn.disabled ? " disabled" : ""}>${escapeHtml(btn.label)}</button>`;
    card.querySelector(".btn-join").addEventListener("click", () => btn.onClick && btn.onClick());
    grid.appendChild(card);
  });
}
