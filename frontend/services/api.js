/* ============================================================
   CampusQueue — API client (api.js)
   One place that talks to the Flask backend. Every request:
     - sends the saved access token
     - refreshes the token automatically when it expires
     - turns every failure into an ApiError with a message
   ============================================================ */

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;   // 0 = could not reach the server
    this.data = data || {};
  }
}

const Api = {
  base() {
    const b = (window.CQ_CONFIG && window.CQ_CONFIG.API_BASE_URL) || "";
    return b.replace(/\/+$/, "");
  },

  async _send(method, path, body, token) {
    const headers = { "Content-Type": "application/json" };
    if (token) headers.Authorization = "Bearer " + token;
    let res;
    try {
      res = await fetch(this.base() + path, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch (networkErr) {
      throw new ApiError("Can't reach the CampusQueue server. Check your internet connection or that the backend is running.", 0);
    }
    let data = {};
    try { data = await res.json(); } catch (e) { }
    return { res, data };
  },

  async _refresh() {
    const refreshToken = Session.get("refreshToken");
    if (!refreshToken) return false;
    try {
      const { res, data } = await this._send("POST", "/api/auth/refresh", undefined, refreshToken);
      if (!res.ok || !data.access_token) return false;
      Session.set("accessToken", data.access_token);
      return true;
    } catch (e) {
      return false;
    }
  },

  /** request("GET", "/api/queues") → parsed JSON, or throws ApiError. */
  async request(method, path, body, { auth = true } = {}) {
    if (auth && Session.isIdleExpired) {
      Session.signOut();
      throw new ApiError("Please log in again.", 401);
    }
    let { res, data } = await this._send(method, path, body, auth ? Session.get("accessToken") : null);

    // Access token expired → try once to refresh it, then repeat the request.
    if (auth && (res.status === 401 || res.status === 422)) {
      if (await this._refresh()) {
        ({ res, data } = await this._send(method, path, body, Session.get("accessToken")));
      }
      if (res.status === 401 || res.status === 422) {
        Session.signOut();
        throw new ApiError("Your session has expired. Please log in again.", 401, data);
      }
    }

    if (!res.ok) {
      throw new ApiError(data.error || data.message || `Request failed (${res.status}).`, res.status, data);
    }
    return data;
  },

  get(path) { return this.request("GET", path); },
  post(path, body) { return this.request("POST", path, body); },
  patch(path, body) { return this.request("PATCH", path, body); },
};
