/* ============================================================
   CampusQueue — App state
   The login (user + tokens) is kept in sessionStorage, so it is
   wiped when the student closes the tab or browser: they must sign
   in again next time. After 10 minutes without any activity the
   student is signed out and sent back to the login page.
   ============================================================ */

const IDLE_LIMIT_MS = 10 * 60 * 1000; // 10 minutes

const Session = {
  get(key) {
    try { return JSON.parse(sessionStorage.getItem("cq." + key)); } catch (e) { return null; }
  },
  set(key, value) {
    try { sessionStorage.setItem("cq." + key, JSON.stringify(value)); } catch (e) { /* storage unavailable */ }
  },
  remove(key) {
    try { sessionStorage.removeItem("cq." + key); } catch (e) { /* storage unavailable */ }
  },
  signOut() {
    ["user", "accessToken", "refreshToken", "lastActive"].forEach(k => this.remove(k));
    // Clean up logins saved by older versions of the app.
    try { ["user", "accessToken", "refreshToken"].forEach(k => localStorage.removeItem("cq." + k)); } catch (e) {}
  },
  touch() { this.set("lastActive", Date.now()); },
  get isIdleExpired() {
    const last = this.get("lastActive");
    return !last || Date.now() - last > IDLE_LIMIT_MS;
  },
  get user() { return this.get("user"); },
  get isLoggedIn() { return !!(this.get("accessToken") && this.get("user")) && !this.isIdleExpired; },
};

function loginPageHref() {
  return location.pathname.includes("/pages/") ? "../index.html" : "index.html";
}

/** Sign out after 10 minutes and go to the login page. */
function startIdleWatch() {
  if (startIdleWatch.started) return;
  startIdleWatch.started = true;
  const expire = () => {
    Session.signOut();
    location.replace(loginPageHref() + "?reason=idle");
  };
  let lastWrite = 0;
  const onActivity = () => {
    if (!Session.get("accessToken")) return;
    if (Session.isIdleExpired) { expire(); return; }
    const now = Date.now();
    if (now - lastWrite > 5000) { Session.touch(); lastWrite = now; }
  };
  ["click", "keydown", "mousemove", "scroll", "touchstart"].forEach(ev =>
    window.addEventListener(ev, onActivity, { passive: true }));
  setInterval(() => { if (Session.get("accessToken") && Session.isIdleExpired) expire(); }, 15000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && Session.get("accessToken") && Session.isIdleExpired) expire();
  });
}

function currentUser() {
  return Session.user;
}

/** Send the visitor to the login page if they aren't signed in as `role`. */
function requireRole(role, loginHref) {
  const u = Session.user;
  if (!Session.isLoggedIn || !u) {
    const idle = !!Session.get("accessToken");
    Session.signOut();
    location.replace(loginHref + (idle ? "?reason=idle" : ""));
    return false;
  }
  if (role && u.role !== role) {
    location.replace(u.role === "admin" ? "admin-select-queue.html" : "student-dashboard.html");
    return false;
  }
  Session.touch();
  startIdleWatch();
  return true;
}

function initialsOf(name) {
  const parts = String(name || "").trim().split(/[\s._-]+/).filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return parts.slice(0, 2).map(p => p[0].toUpperCase()).join("");
}

// Any "Log out" link signs the user out.
function wireLogout(linkId) {
  const link = document.getElementById(linkId);
  if (!link) return;
  link.addEventListener("click", async e => {
    e.preventDefault();
    const href = link.getAttribute("href");
    try {
      if (Session.user && Session.user.role === "admin") await Api.post("/api/admin/release");
    } catch (err) {
      console.warn("Could not release queue on logout:", err.message);
    } finally {
      Session.signOut();
      location.href = href;
    }
  });
}

/** Run an async action and show any error as a toast instead of crashing the page. */
async function safely(fn, fallbackMessage) {
  try {
    return await fn();
  } catch (err) {
    console.error(err);
    if (err && err.status === 401) {
      showToast(err.message);
      setTimeout(() => { location.href = loginPageHref(); }, 1200);
      return null;
    }
    showToast((err && err.message) || fallbackMessage || "Something went wrong. Please try again.");
    return null;
  }
}

/* ---------- small shared formatting helpers ---------- */
// Flask sends UTC times without a "Z" — treat them as UTC.
function parseTime(iso) {
  if (!iso) return null;
  const s = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z";
  const t = Date.parse(s);
  return isNaN(t) ? null : t;
}
function timeAgo(ms) {
  if (!ms) return "—";
  const s = Math.floor((Date.now() - ms) / 1000);
  if (s < 5) return "just now";
  if (s < 60) return s + "s ago";
  if (s < 3600) return Math.floor(s / 60) + "m ago";
  if (s < 86400) return Math.floor(s / 3600) + "h ago";
  return new Date(ms).toLocaleDateString();
}
function waitBand(position) {
  return position === 1 ? "0–5 min" : position === 2 ? "5–10 min" : position === 3 ? "10–15 min" : position ? ">15 min" : "—";
}
function escapeHtml(v) {
  return String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const STATUS_LABELS = { waiting: "Joined – Waiting", called: "Called", served: "Served", skipped: "Skipped", cancelled: "Cancelled" };
