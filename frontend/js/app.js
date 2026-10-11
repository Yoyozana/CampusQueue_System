/* ============================================================
   CampusQueue — welcome / login page (index.html)
   ============================================================ */
const form = document.getElementById("login-form");
const usernameInput = document.getElementById("login-username");
const passwordInput = document.getElementById("login-password");
const errorBox = document.getElementById("login-error");
const toggleButton = document.getElementById("toggle-password");
const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');

function showLoginError(message) {
  errorBox.textContent = message;
  errorBox.classList.add("visible");
}

function homeFor(user) {
  return user.role === "admin" ? "pages/admin-select-queue.html" : "pages/student-dashboard.html";
}

toggleButton.addEventListener("click", () => {
  const showing = passwordInput.type === "text";
  passwordInput.type = showing ? "password" : "text";
  toggleButton.setAttribute("aria-label", showing ? "Show password" : "Hide password");
});

document.querySelector(".row-forgot a").addEventListener("click", e => {
  e.preventDefault();
  showToast("To reset your password, please contact the WSU ICT service desk.");
});

form.addEventListener("submit", async e => {
  e.preventDefault();
  const username = usernameInput.value.trim();
  const password = passwordInput.value;

  if (username.length > 50 || password.length > 128 || !/^[A-Za-z0-9._@-]+$/.test(username || "x")) {
    showLoginError("Please enter a valid username (letters, numbers, . _ - @ only).");
    usernameInput.focus();
    return;
  }
  if (!username || !password) {
    showLoginError("Please enter your username and password.");
    (username ? passwordInput : usernameInput).focus();
    return;
  }
  errorBox.classList.remove("visible");

  const originalLabel = submitButton ? submitButton.textContent : "";
  if (submitButton) { submitButton.disabled = true; submitButton.textContent = "Signing in…"; }

  try {
    const user = await signIn(username, password);
    location.href = homeFor(user);
  } catch (err) {
    console.error("Login failed:", err);
    showLoginError(err.message || "Login failed. Please try again.");
    passwordInput.value = "";
    passwordInput.focus();
  } finally {
    if (submitButton) { submitButton.disabled = false; submitButton.textContent = originalLabel; }
  }
});

// Explain why the student landed back here.
(() => {
  const reason = new URLSearchParams(location.search).get("reason");
  if (reason === "idle") showLoginError("Please log in again.");
})();

// Still signed in within this same tab (e.g. page refresh)? Go back in.
// Closing the tab or browser clears the login, so they must sign in again.
(async () => {
  try {
    const user = await restoreSession();
    if (user) location.replace(homeFor(user));
  } catch (err) {
    console.warn("Could not restore session:", err);
  }
})();
