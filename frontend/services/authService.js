/* ============================================================
   CampusQueue — Auth service (authService.js)
   Logs in against POST /api/auth/login. The role comes from the
   database, not from guessing the username.
   ============================================================ */

/** Returns the signed-in user, or throws an ApiError with message. */
async function signIn(username, password) {
  try {
    const data = await Api.request("POST", "/api/auth/login", { username, password }, { auth: false });
    if (!data.access_token || !data.user) throw new ApiError("The server sent an unexpected response.", 500);
    Session.signOut();
    Session.set("accessToken", data.access_token);
    Session.set("refreshToken", data.refresh_token);
    Session.set("user", data.user);
    Session.touch();
    return data.user;
  } catch (err) {
    if (err instanceof ApiError && err.status === 423) {
      throw new ApiError(err.message || "Your account is locked. Try again later.", 423, err.data);
    }
    if (err instanceof ApiError && err.status === 401) {
      const left = err.data && err.data.attempts_left;
      throw new ApiError(
        typeof left === "number" && left > 0
          ? `Incorrect username or password.`
          : "Incorrect username or password.", 401, err.data);
    }
    if (err instanceof ApiError && err.status === 429) {
      throw new ApiError("Too many sign-in attempts. Please wait a minute and try again.", 429, err.data);
    }
    throw err;
  }
}

/** Checks the saved login is still valid; returns the user or null. */
async function restoreSession() {
  if (!Session.isLoggedIn) { Session.signOut(); return null; }
  try {
    const data = await Api.get("/api/auth/me");
    Session.set("user", data.user);
    return data.user;
  } catch (err) {
    if (err.status === 0) return Session.user; // offline: keep the saved user
    Session.signOut();
    return null;
  }
}
