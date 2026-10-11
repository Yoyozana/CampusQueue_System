/* ============================================================
   CampusQueue — Frontend configuration
   API_BASE_URL is where the Flask backend lives.
   -when Flask serves this frontend itself (open http://localhost:5000 locally, or Render URL live).
   - If you host the frontend separately (Netlify, Live Server on
     port 5500...), put the backend address here, e.g.
     "http://localhost:5000" or "https://campusqueue-api.onrender.com",
     and add the frontend address to CORS_ORIGINS on the backend.
   ============================================================ */
window.CQ_CONFIG = {
  API_BASE_URL: "",
  REFRESH_SECONDS: 8,   // how often pages pull fresh data from the database
};
