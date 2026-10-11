/* ============================================================
   CampusQueue — Queue service (queueService.js)
   Loads queues and tickets from the Flask API into a small in-memory
   cache, then the pages read from that cache. Every action (join,
   leave, call next, serve, skip, pause/close) is saved in MySQL, so
   nothing is lost when a tab closes or the student changes device.
   ============================================================ */

const ICONS = { REG: "🏛️", FIN: "💳", ADV: "🎓", ACC: "🏠", SC: "🪪" };

function mapTicket(t) {
  return {
    id: t.id,
    seq: t.sequence_number || 0,
    number: t.ticket_number,
    service: t.queue_id,
    status: t.status,
    position: t.position || 0,
    user: t.student_name || t.student_username || "",
    username: t.student_username || "",
    createdAt: parseTime(t.joined_at),
    calledAt: parseTime(t.called_at),
    resolvedAt: parseTime(t.served_at),
    serviceName: t.service_name,
    location: t.location,
  };
}

const Queue = {
  _services: [],
  _myTickets: [],
  _allTickets: [],
  _actions: [],
  _todaysQueueId: null,

  /* ---------- loading from the database ---------- */
  async loadServices() {
    const data = await Api.get("/api/queues");
    this._services = (data.queues || []).map(q => ({
      id: q.id,
      name: q.service_name || q.queue_name,
      queueName: q.queue_name,
      location: q.location || "",
      prefix: q.prefix,
      icon: ICONS[q.prefix] || "📋",
      status: q.status,
      waitingCount: q.waiting_count || 0,
      servingNumber: q.serving_ticket_number || null,
      currentAdminId: q.current_admin_id,
    }));
  },
  async loadMyTickets() {
    const data = await Api.get("/api/queues/my-tickets");
    this._myTickets = (data.tickets || []).map(mapTicket);
  },
  async loadStudent() {
    await Promise.all([this.loadServices(), this.loadMyTickets(), Notifications.load()]);
  },
  async loadAdmin() {
    const [, tickets, actions, mine] = await Promise.all([
      this.loadServices(),
      Api.get("/api/admin/tickets"),
      Api.get("/api/admin/actions"),
      Api.get("/api/admin/my-queue"),
    ]);
    this._allTickets = (tickets.tickets || []).map(mapTicket);
    this._actions = actions.actions || [];
    this._todaysQueueId = mine.queue ? mine.queue.id : null;
  },

  /* ---------- reading the cache ---------- */
  services() { return this._services; },
  service(id) { return this._services.find(s => s.id === Number(id)) || null; },
  status(id) { const s = this.service(id); return s ? s.status : "closed"; },
  todaysQueue() { return this._todaysQueueId; },

  allTickets() { return this._allTickets.slice().sort((a, b) => b.createdAt - a.createdAt); },
  waiting(id) {
    return this._allTickets.filter(t => t.service === Number(id) && t.status === "waiting")
      .sort((a, b) => a.seq - b.seq || a.createdAt - b.createdAt);
  },
  waitingCount(id) { const s = this.service(id); return s ? s.waitingCount : 0; },
  serving(id) {
    const fromAdmin = this._allTickets.find(t => t.service === Number(id) && t.status === "called");
    if (fromAdmin) return fromAdmin;
    const s = this.service(id);
    return s && s.servingNumber ? { number: s.servingNumber } : null;
  },
  recent(id) {
    return this._allTickets.filter(t => t.service === Number(id) && (t.status === "served" || t.status === "skipped"))
      .sort((a, b) => (b.resolvedAt || 0) - (a.resolvedAt || 0));
  },
  position(ticket) { return ticket && ticket.status === "waiting" ? ticket.position : 0; },

  myHistory() { return this._myTickets; },
  myActiveTicket() { return this._myTickets.find(t => t.status === "waiting" || t.status === "called") || null; },
  myLatestTicket() { return this.myActiveTicket() || this._myTickets[0] || null; },

  /* ---------- student actions ---------- */
  async join(id) {
    const current = this.myActiveTicket();
    if (current && current.service === Number(id)) return current;
    if (current && current.status === "waiting") await this.leave();
    else if (current) throw new ApiError("You're being served right now — finish that ticket before joining another queue.", 409);
    const data = await Api.post(`/api/queues/${id}/join`);
    await this.loadStudent();
    return mapTicket(data.ticket);
  },
  async leave() {
    const mine = this.myActiveTicket();
    if (!mine) return null;
    const data = await Api.post(`/api/queues/tickets/${mine.id}/cancel`);
    await this.loadStudent();
    return mapTicket(data.ticket);
  },

  /* ---------- admin actions ---------- */
  async selectTodaysQueue(id) {
    await Api.post(`/api/admin/queues/${id}/select`);
    this._todaysQueueId = Number(id);
  },
  async callNext(id) {
    const data = await Api.post(`/api/admin/queues/${id}/call-next`);
    await this.loadAdmin();
    if (!data.ticket) return { error: data.message || "No students waiting in this queue." };
    return mapTicket(data.ticket);
  },
  async serve(ticketId) {
    const data = await Api.post(`/api/admin/tickets/${ticketId}/serve`);
    await this.loadAdmin();
    return mapTicket(data.ticket);
  },
  async skip(ticketId) {
    const data = await Api.post(`/api/admin/tickets/${ticketId}/skip`);
    await this.loadAdmin();
    return mapTicket(data.ticket);
  },
  async setStatus(id, status) {
    await Api.patch(`/api/admin/queues/${id}/status`, { status });
    await this.loadAdmin();
  },

  /* ---------- admin audit log ---------- */
  adminLog() {
    return this._actions.map(a => ({
      text: a.action_description,
      by: a.admin_name || (a.admin_id ? "Admin #" + a.admin_id : "admin"),
      time: parseTime(a.action_time),
    }));
  },

  /* ---------- reports (from the tickets in the database) ---------- */
  report() {
    const list = this._allTickets;
    const served = list.filter(t => t.status === "served");
    const skipped = list.filter(t => t.status === "skipped");
    const waits = served.filter(t => t.calledAt && t.createdAt).map(t => t.calledAt - t.createdAt);
    const avgMs = waits.length ? waits.reduce((a, b) => a + b, 0) / waits.length : null;
    const resolved = served.length + skipped.length;
    const busiest = this._services.slice().sort((a, b) => b.waitingCount - a.waitingCount)[0];
    return {
      averageWait: avgMs == null ? null : `${Math.floor(avgMs / 60000)}m ${Math.round((avgMs % 60000) / 1000)}s`,
      servedPercent: resolved ? Math.round((served.length / resolved) * 100) : null,
      skipPercent: resolved ? Math.round((skipped.length / resolved) * 100) : null,
      busiest: busiest && busiest.waitingCount > 0 ? { name: busiest.name, waiting: busiest.waitingCount } : null,
    };
  },
};
