/* ============================================================
   CampusQueue — Sidebar + topbar component
   ------------------------------------------------------------
   Every student and admin page has:
     <nav class="sidebar" id="sidebar" data-role="student|admin" data-active="page-key"></nav>
   and this fills it in, so the menu is written once for all pages.
   ============================================================ */

const NAV = {
  student: {
    portal: "STUDENT PORTAL",
    roleLabel: "Student",
    items: [
      ["dashboard", "student-dashboard.html", "🏠", "Dashboard"],
      ["my-queue", "student-my-queue.html", "📋", "My Queue"],
      ["join-queue", "student-join-queue.html", "➕", "Join Queue"],
      ["notifications", "student-notifications.html", "🔔", "Notifications"],
      ["profile", "student-profile.html", "👤", "Profile"],
      ["help", "student-help.html", "❓", "Help"],
    ],
  },
  admin: {
    portal: "ADMIN PORTAL",
    roleLabel: "Administrator",
    items: [
      ["dashboard", "admin-dashboard.html", "🏠", "Dashboard"],
      ["queues", "admin-queues.html", "📑", "Queues"],
      ["tickets", "admin-tickets.html", "🎟️", "Tickets"],
      ["users", "admin-users.html", "👥", "Users"],
      ["reports", "admin-reports.html", "📊", "Reports"],
      ["actions", "admin-actions.html", "🗂️", "Admin Actions"],
    ],
  },
};

function renderSidebar() {
  const nav = document.getElementById("sidebar");
  if (!nav) return;
  const role = nav.dataset.role;
  const active = nav.dataset.active;
  const cfg = NAV[role];
  const user = Session.user;
  const name = user ? (user.full_name || user.username) : "Guest";

  const links = cfg.items.map(([key, href, icon, label]) => `
    <a class="nav-item${key === active ? " active" : ""}" href="${href}"${key === active ? ' aria-current="page"' : ""}>
      <span class="icon" aria-hidden="true">${icon}</span> ${label}${key === "notifications" ? ' <span class="badge" id="sidebar-notif-badge">0</span>' : ""}
    </a>`).join("");

  nav.innerHTML = `
    <div class="brand-mini"><div class="crest-sm"><img src="../assets/wsu-mark.png" alt="WSU"></div><div class="name">Campus Queue<span>${cfg.portal}</span></div></div>
    ${links}
    <a class="nav-item" href="../index.html" id="logout-link"><span class="icon" aria-hidden="true">🚪</span> Logout</a>
    <div class="sidebar-footer"><div class="avatar-circle">${escapeHtml(initialsOf(name).slice(0, 2))}</div><div class="who">${escapeHtml(name)}<div class="role">${cfg.roleLabel}</div></div></div>
  `;
  wireLogout("logout-link");
  renderBadges();
}

// Unread-notification counts in the sidebar and the topbar bell (student pages).
function renderBadges() {
  const unread = Notifications.unreadCount();
  const side = document.getElementById("sidebar-notif-badge");
  if (side) side.textContent = unread;
  const top = document.getElementById("topbar-badge");
  if (top) { top.textContent = unread; top.style.display = unread ? "inline-block" : "none"; }
}

// Pop up any notifications for this user that haven't been shown yet.
function showNewNotifications() {
  Notifications.takeUnshown().forEach(n => showToast(n.message));
  renderBadges();
}
