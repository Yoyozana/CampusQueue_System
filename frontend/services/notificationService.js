/* ============================================================
   CampusQueue — Notification service
   Notifications are created by the backend and stored in MySQL.
   Which ones have already popped up is remembered per user in this
   browser, so the same pop-up isn't shown twice.
   ============================================================ */

const Notifications = {
  _items: [],

  async load() {
    const data = await Api.get("/api/notifications");
    this._items = (data.notifications || []).map(n => {
      const m = /^(\p{Extended_Pictographic}\uFE0F?)\s*(.*)$/u.exec(n.message || "");
      return {
        id: n.id,
        icon: m ? m[1] : "🔔",
        message: m ? m[2] : n.message,
        time: parseTime(n.created_at),
        read: !!n.read,
      };
    });
  },
  list() { return this._items; },
  unreadCount() { return this._items.filter(n => !n.read).length; },
  async markAllRead() {
    await Api.post("/api/notifications/read-all");
    this._items.forEach(n => { n.read = true; });
  },
  _shownKey() { const u = Session.user; return "shownNotifications." + (u ? u.id : "guest"); },
  /** Unread notifications not yet shown as a pop-up in this browser; marks them shown. */
  takeUnshown() {
    const shown = new Set(Session.get(this._shownKey()) || []);
    const fresh = this._items.filter(n => !n.read && !shown.has(n.id));
    fresh.forEach(n => shown.add(n.id));
    Session.set(this._shownKey(), [...shown].slice(-200));
    return fresh.reverse();
  },
};
