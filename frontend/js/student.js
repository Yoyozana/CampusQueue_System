/* ============================================================
   CampusQueue — student pages (pages/student-*.html)
   Each page says which one it is with <body data-page="...">:
   dashboard, my-queue, join-queue, notifications, profile, help.
   ============================================================ */

const studentPage = document.body.dataset.page;

/* ---------- service cards (Dashboard + Join Queue) ---------- */
function renderStudentServices() {
  const grid = document.getElementById("services-grid");
  if (!grid) return;
  const mine = Queue.myActiveTicket();
  renderServiceCards(grid, {
    unit: "students waiting",
    cardClass: s => (mine && mine.service === s.id ? "is-joined" : ""),
    button: (s, status) => {
      if (status !== "open") return { label: "Not accepting tickets", disabled: true };
      if (mine && mine.service === s.id) return { label: "✓ Joined", disabled: true };
      return { label: "Join Queue", onClick: () => safely(async () => {
        const t = await Queue.join(s.id);
        showToast(`Joined ${s.name}. Your ticket is ${t.number}.`);
        refreshStudent();
      }, "Could not join the queue.") };
    },
  });
}

/* ---------- "your current queue" card (Dashboard) ---------- */
function renderCurrentQueue() {
  const wrap = document.getElementById("current-queue-wrap");
  if (!wrap) return;
  const t = Queue.myActiveTicket();
  if (!t) { wrap.innerHTML = ""; return; }
  const s = Queue.service(t.service) || { name: t.serviceName || "Queue", location: t.location || "" };
  const pos = Queue.position(t);
  wrap.innerHTML = `
    <div class="current-queue-card">
      <div class="top-row">
        <div>
          <div class="queue-title">${escapeHtml(s.name)} <span class="joined-tag">✓ ${t.status === "called" ? "Called" : "Joined"}</span></div>
          <div class="queue-loc">${escapeHtml(s.location)}</div>
        </div>
        <button type="button" class="btn-leave" data-leave>Leave Queue</button>
      </div>
      <div class="ticket-block">
        <div><div class="stat-mini">TICKET NUMBER</div><div class="ticket-num-big">${escapeHtml(t.number)}</div></div>
        <div class="stat-mini">YOUR POSITION<strong>${pos || "—"}</strong></div>
        <div class="stat-mini">EST. WAIT<strong>${t.status === "called" ? "Now" : waitBand(pos)}</strong></div>
      </div>
    </div>`;
}

/* ---------- My Queue ---------- */
function renderMyQueue() {
  const wrap = document.getElementById("myqueue-wrap");
  if (!wrap) return;
  const t = Queue.myLatestTicket();
  if (!t) {
    wrap.innerHTML = `<div class="empty-state">You haven't joined a queue yet. Go to <a href="student-join-queue.html">Join Queue</a> to get a ticket.</div>`;
    return;
  }
  const s = Queue.service(t.service) || { name: t.serviceName || "Queue", location: t.location || "" };
  const pos = Queue.position(t);
  const serving = Queue.serving(t.service);
  const tierLabels = { 1: "You're next", 2: "Almost next", 3: "Getting closer" };
  const active = t.status === "waiting" || t.status === "called";

  wrap.innerHTML = `
    <div class="queue-detail-card">
      <div class="queue-head">${escapeHtml(s.name)}<div class="loc">${escapeHtml(s.location)}</div></div>
      <div class="serving-box"><div class="label">Currently Serving</div><div class="num">${serving ? escapeHtml(serving.number) : "—"}</div></div>
      <div class="your-ticket-box"><div class="label">Your Ticket</div><div class="num">${escapeHtml(t.number)}</div></div>
      ${pos && pos <= 3 ? `<div class="tier-banner tier-${pos}">${tierLabels[pos]}</div>` : ""}
      ${t.status === "called" ? `<div class="tier-banner tier-called">It's your turn! Please proceed to the ${escapeHtml(s.name)} desk.</div>` : ""}
      <div class="detail-row"><span>People ahead of you</span><strong>${pos ? pos - 1 : "—"}</strong></div>
      <div class="detail-row"><span>Estimated wait</span><strong>${t.status === "called" ? "Now" : waitBand(pos)}</strong></div>
      <div class="detail-row"><span>Status</span><strong>${escapeHtml(STATUS_LABELS[t.status] || t.status)}</strong></div>
      ${active ? `<button type="button" class="btn-leave btn-block" data-leave>Leave Queue</button>` : `<a class="btn-join" style="display:block; text-align:center; text-decoration:none; margin-top:1rem;" href="student-join-queue.html">Join a queue</a>`}
      <div class="info-strip">🔔 You will be notified when it's almost your turn.</div>
    </div>
    ${renderHistoryTable()}`;
}

/* ---------- ticket history (from the database) ---------- */
function renderHistoryTable() {
  const rows = Queue.myHistory();
  if (!rows.length) return "";
  return `
    <div class="sub-label" style="margin-top:1.5rem;">My ticket history</div>
    <div class="table-scroll"><table>
      <thead><tr><th>Ticket</th><th>Service</th><th>Status</th><th>Joined</th></tr></thead>
      <tbody>${rows.map(t => `<tr><td class="ticket-num">${escapeHtml(t.number)}</td><td>${escapeHtml(t.serviceName || (Queue.service(t.service) || {}).name || "")}</td><td>${escapeHtml(STATUS_LABELS[t.status] || t.status)}</td><td>${timeAgo(t.createdAt)}</td></tr>`).join("")}</tbody>
    </table></div>`;
}

/* ---------- Notifications ---------- */
function renderNotificationsPage() {
  const list = document.getElementById("notifications-list");
  if (!list) return;
  const items = Notifications.list();
  if (!items.length) { list.innerHTML = `<div class="empty-state">No notifications yet — join a queue to see one appear.</div>`; return; }
  list.innerHTML = items.map(n => `
    <div class="notification-item${n.read ? "" : " unread"}">
      <div class="n-icon">${escapeHtml(n.icon)}</div>
      <div><div>${escapeHtml(n.message)}</div><div class="time">${timeAgo(n.time)}</div></div>
    </div>`).join("");
}

/* ---------- Profile ---------- */
function renderProfile() {
  const wrap = document.getElementById("profile-details");
  if (!wrap) return;
  const user = Session.user;
  if (!user) {
    wrap.innerHTML = `<div class="empty-state">You're not logged in. <a href="../index.html">Log in</a> to see your account.</div>`;
    return;
  }
  wrap.innerHTML = `
    <div class="detail-row"><span>Full name</span><strong>${escapeHtml(user.full_name || "—")}</strong></div>
    <div class="detail-row"><span>Username</span><strong>${escapeHtml(user.username)}</strong></div>
    <div class="detail-row"><span>Student number</span><strong>${escapeHtml(user.student_number || "—")}</strong></div>
    <div class="detail-row"><span>Email</span><strong>${escapeHtml(user.email || "—")}</strong></div>
    <div class="detail-row"><span>Role</span><strong>${user.role === "admin" ? "Administrator" : "Student"}</strong></div>`;
}

/* ---------- start-up ---------- */
function refreshStudent() {
  renderCurrentQueue();
  renderStudentServices();
  renderMyQueue();
  renderNotificationsPage();
  showNewNotifications();
}

document.addEventListener("click", e => {
  if (e.target.closest("[data-leave]")) {
    safely(async () => {
      const t = await Queue.leave();
      if (t) showToast(`You left the queue. Ticket ${t.number} was cancelled.`);
      refreshStudent();
    }, "Could not leave the queue.");
  }
});

const markAllButton = document.getElementById("mark-all-read");
if (markAllButton) markAllButton.addEventListener("click", () => safely(async () => {
  await Notifications.markAllRead();
  renderNotificationsPage(); renderBadges();
}, "Could not mark notifications as read."));

/* Load everything from the database, then keep it fresh. */
async function reloadStudent() {
  await safely(async () => { await Queue.loadStudent(); refreshStudent(); }, "Could not load your queue data.");
}

if (requireRole("student", "../index.html")) {
  renderSidebar();
  renderProfile();
  reloadStudent();
  setInterval(reloadStudent, (window.CQ_CONFIG.REFRESH_SECONDS || 8) * 1000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) reloadStudent(); });
}
