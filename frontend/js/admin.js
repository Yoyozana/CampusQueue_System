/* ============================================================
   CampusQueue — admin pages (pages/admin-*.html)
   Each page says which one it is with <body data-page="...">:
   select (choose today's queue), dashboard, queues, tickets,
   users, reports, actions.
   ============================================================ */

const adminPage = document.body.dataset.page;
const todaysQueue = () => Queue.todaysQueue();

/* ---------- choose today's queue (admin-select-queue.html) ---------- */
function renderQueueSelect() {
  const grid = document.getElementById("queue-select-grid");
  if (!grid) return;
  const user = Session.user;
  const nameEl = document.getElementById("admin-name");
  if (nameEl) nameEl.textContent = user ? (user.full_name || user.username) : "";
  wireLogout("logout-link");
  renderServiceCards(grid, {
    unit: "waiting",
    cardClass: s => (todaysQueue() === s.id ? "is-selected" : ""),
    button: s => ({
      label: todaysQueue() === s.id ? "✓ Managing today — open dashboard" : "Manage this queue today",
      onClick: () => safely(async () => {
        if (todaysQueue() !== s.id) await Queue.selectTodaysQueue(s.id);
        location.href = "admin-dashboard.html";
      }, "Could not select that queue."),
    }),
  });
}

/* A message on pages that need a queue chosen first. */
function needQueueHtml() {
  return `<div class="empty-state">No queue selected for this session. <a href="admin-select-queue.html">Choose the queue you're managing today</a>.</div>`;
}

/* ---------- Dashboard ---------- */
function renderStats() {
  const wrap = document.getElementById("admin-stats");
  if (!wrap) return;
  const all = Queue.allTickets();
  const open = Queue.services().filter(s => s.status === "open").length;
  const waiting = all.filter(t => t.status === "waiting").length;
  const served = all.filter(t => t.status === "served").length;
  const skipped = all.filter(t => t.status === "skipped").length;
  wrap.innerHTML = `
    <div class="stat-card c1"><div class="num">${open}</div><div class="lbl">Open Queues</div></div>
    <div class="stat-card c2"><div class="num">${waiting}</div><div class="lbl">Total Waiting</div></div>
    <div class="stat-card c3"><div class="num">${served}</div><div class="lbl">Served Today</div></div>
    <div class="stat-card c4"><div class="num">${skipped}</div><div class="lbl">Skipped / No-show</div></div>`;
}

function renderDashDetail() {
  const wrap = document.getElementById("admin-dash-detail");
  if (!wrap) return;
  const id = todaysQueue();
  if (!id) { wrap.innerHTML = needQueueHtml(); return; }
  const s = Queue.service(id);
  const status = Queue.status(id);
  const serving = Queue.serving(id);
  const waiting = Queue.waiting(id);
  const recent = Queue.recent(id).slice(0, 5);

  wrap.innerHTML = `
    <div class="admin-queue-detail">
      <div class="head-row">
        <div><strong>${escapeHtml(s.name)}</strong> <span class="status-pill status-${status} pill-gap">${status}</span>
          <div class="helper" style="margin:0.15rem 0 0;">${escapeHtml(s.location)}</div>
        </div>
        <div class="head-actions">
          <button type="button" class="btn-call-next" data-action="call-next" ${status !== "open" ? "disabled" : ""}
            title="${status !== "open" ? `Queue is ${status} — reopen it to call the next student` : "Call the next waiting student"}">Call Next</button>
          <a class="pill-btn" href="admin-select-queue.html">Switch Queue</a>
        </div>
      </div>
      <div class="serving-inline">
        <div><div class="helper" style="margin:0;">Currently Serving</div><div class="num">${serving ? escapeHtml(serving.number) : "—"}</div></div>
        <div><div class="helper" style="margin:0;">Waiting</div><div class="num">${waiting.length}</div></div>
        ${serving ? `
          <div class="serving-actions">
            <button type="button" class="pill-btn ok" data-action="serve" data-ticket="${serving.id}">✓ Mark Served</button>
            <button type="button" class="pill-btn danger" data-action="skip" data-ticket="${serving.id}">Skip</button>
          </div>` : ""}
      </div>
      <div class="sub-label">Next in queue</div>
      ${waiting.length ? `
        <div class="table-scroll"><table>
          <thead><tr><th>Ticket</th><th>Status</th><th>Joined</th></tr></thead>
          <tbody>${waiting.slice(0, 5).map(t => `<tr><td class="ticket-num">${escapeHtml(t.number)}</td><td>Waiting</td><td>${timeAgo(t.createdAt)}</td></tr>`).join("")}</tbody>
        </table></div>` : `<div class="empty-state">No one waiting.</div>`}
      <div class="sub-label">Recently served / completed</div>
      ${recent.length ? `
        <div class="table-scroll"><table>
          <thead><tr><th>Ticket</th><th>Outcome</th><th>Time</th></tr></thead>
          <tbody>${recent.map(t => `<tr><td class="ticket-num">${escapeHtml(t.number)}</td><td>${t.status === "served" ? "✓ Served" : "⤺ Skipped"}</td><td>${timeAgo(t.resolvedAt)}</td></tr>`).join("")}</tbody>
        </table></div>` : `<div class="empty-state">No one served yet in this queue.</div>`}
      <div class="queue-controls">
        <button type="button" class="pill-btn warn" data-action="status" data-status="paused">Pause Queue</button>
        <button type="button" class="pill-btn danger" data-action="status" data-status="closed">Close Queue</button>
        <button type="button" class="pill-btn" data-action="status" data-status="open">Reopen</button>
        <a class="pill-btn" href="admin-tickets.html">View All Tickets</a>
      </div>
    </div>`;
}

/* ---------- Queues ---------- */
function renderQueuesPage() {
  const grid = document.getElementById("admin-queues-grid");
  if (!grid) return;
  const id = todaysQueue();
  if (!id) { grid.innerHTML = needQueueHtml(); return; }
  const s = Queue.service(id);
  const status = Queue.status(id);
  grid.innerHTML = `
    <div class="service-card">
      <div class="icon-badge" aria-hidden="true">${escapeHtml(s.icon)}</div>
      <span class="status-pill status-${escapeHtml(status)}">${escapeHtml(status)}</span>
      <div class="s-name">${escapeHtml(s.name)} <span class="prefix">(${s.prefix})</span></div>
      <div class="s-loc">${escapeHtml(s.location)}</div>
      <div class="s-count">${Queue.waitingCount(id)} waiting</div>
      <div>
        <button type="button" class="pill-btn" data-action="status" data-status="open">Open</button>
        <button type="button" class="pill-btn warn" data-action="status" data-status="paused">Pause</button>
        <button type="button" class="pill-btn danger" data-action="status" data-status="closed">Close</button>
      </div>
    </div>`;
}

/* ---------- Tickets ---------- */
function renderTicketsPage() {
  const wrap = document.getElementById("all-tickets-table");
  if (!wrap) return;
  const rows = Queue.allTickets();
  if (!rows.length) { wrap.innerHTML = `<div class="empty-state">No tickets issued yet.</div>`; return; }
  wrap.innerHTML = `
    <div class="table-scroll"><table>
      <thead><tr><th>Ticket</th><th>Queue</th><th>Student</th><th>Status</th><th>Issued</th></tr></thead>
      <tbody>${rows.map(t => `<tr><td class="ticket-num">${escapeHtml(t.number)}</td><td>${escapeHtml((Queue.service(t.service) || {}).name || "")}</td><td>${escapeHtml(t.user)}${t.username ? ` <span class="helper">(${escapeHtml(t.username)})</span>` : ""}</td><td>${escapeHtml(t.status)}</td><td>${timeAgo(t.createdAt)}</td></tr>`).join("")}</tbody>
    </table></div>`;
}

/* ---------- Users ---------- */
function renderUsersPage() {
  const body = document.getElementById("users-table-body");
  if (!body) return;
  const people = Users.list();
  body.innerHTML = people.length
    ? people.map(p => `<tr><td>${escapeHtml(p.full_name || p.username)}</td><td>${escapeHtml(p.role)}</td><td>${escapeHtml(p.student_number || "—")}</td></tr>`).join("")
    : `<tr><td colspan="3">No accounts found.</td></tr>`;
}

/* ---------- Reports ---------- */
function renderReportsPage() {
  const wrap = document.getElementById("report-stats");
  if (!wrap) return;
  const r = Queue.report();
  wrap.innerHTML = `
    <div class="stat-card c1"><div class="num">${r.averageWait || "—"}</div><div class="lbl">Avg wait before being called</div></div>
    <div class="stat-card c2"><div class="num">${r.servedPercent != null ? r.servedPercent + "%" : "—"}</div><div class="lbl">Served on first call</div></div>
    <div class="stat-card c3"><div class="num">${r.busiest ? r.busiest.waiting : "—"}</div><div class="lbl">Busiest queue${r.busiest ? ": " + escapeHtml(r.busiest.name) : ""}</div></div>
    <div class="stat-card c4"><div class="num">${r.skipPercent != null ? r.skipPercent + "%" : "—"}</div><div class="lbl">Skip rate</div></div>`;
}

/* ---------- Admin actions (audit log) ---------- */
function renderActionsPage() {
  const wrap = document.getElementById("admin-actions-list");
  if (!wrap) return;
  const log = Queue.adminLog();
  wrap.innerHTML = log.length
    ? log.map(a => `<div class="notification-item"><div class="n-icon">🗂️</div><div><div>${escapeHtml(a.text)}</div><div class="time">${escapeHtml(a.by)} · ${timeAgo(a.time)}</div></div></div>`).join("")
    : `<div class="empty-state">No admin actions recorded yet.</div>`;
}

/* ---------- buttons ---------- */
function refreshAdmin() {
  renderStats(); renderDashDetail(); renderQueuesPage(); renderTicketsPage();
  renderUsersPage(); renderReportsPage(); renderActionsPage();
}

document.addEventListener("click", e => {
  const b = e.target.closest("[data-action]");
  if (!b) return;
  const id = todaysQueue();
  const action = b.dataset.action;
  b.disabled = true;
  safely(async () => {
    if (action === "call-next") {
      const r = await Queue.callNext(id);
      showToast(r.error ? r.error : `Called ${r.number}.`);
    }
    if (action === "serve") { const t = await Queue.serve(Number(b.dataset.ticket)); showToast(`${t.number} marked as served.`); }
    if (action === "skip") { const t = await Queue.skip(Number(b.dataset.ticket)); showToast(`${t.number} skipped (no-show).`); }
    if (action === "status") {
      const status = b.dataset.status;
      if (status === "closed" && !confirm("Close this queue? Everyone still waiting will have their ticket cancelled.")) return;
      await Queue.setStatus(id, status);
      showToast(`${Queue.service(id).name} is now ${status}.`);
    }
  }, "That action failed.").finally(() => { b.disabled = false; refreshAdmin(); });
});

/* ---------- start-up: load from the database, then keep it fresh ---------- */
async function reloadAdmin() {
  await safely(async () => {
    await Promise.all([Queue.loadAdmin(), Users.load()]);
    if (adminPage === "select") { renderQueueSelect(); return; }
    const chosen = Queue.service(todaysQueue());
    const label = document.getElementById("todays-queue-label");
    if (label) label.textContent = chosen ? `Managing: ${chosen.name}` : "";
    refreshAdmin();
  }, "Could not load admin data.");
}

if (requireRole("admin", "../index.html")) {
  if (adminPage !== "select") renderSidebar();
  reloadAdmin();
  setInterval(reloadAdmin, (window.CQ_CONFIG.REFRESH_SECONDS || 8) * 1000);
}
