/* ============================================================
   CampusQueue — Toast component
   Small pop-up message shown at the top of the page.
   Needs an empty <div id="toast-stack"></div> on the page.
   ============================================================ */
function showToast(message) {
  const stack = document.getElementById("toast-stack");
  if (!stack) return;
  const toast = document.createElement("div");
  toast.className = "toast";
  const dot = document.createElement("div");
  dot.className = "dot";
  const text = document.createElement("div");
  text.textContent = message;
  toast.append(dot, text);
  stack.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("leaving");
    setTimeout(() => toast.remove(), 250);
  }, 5000);
}
