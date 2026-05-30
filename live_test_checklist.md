# Nyaya Mitra Live Test Checklist (Admin/Dev)

Use this checklist immediately after deploying to a live URL (e.g., via `localtunnel` or Render) to verify the production environment is sound.

## Backend Verification
- [ ] **Health Endpoint:** Visit `https://<YOUR_LIVE_URL>/health`
  - Expected: `{"status":"ok","version":"...","retrieval_mode":"...","chunks_loaded":2005}`
- [ ] **Admin Endpoint:** Visit `https://<YOUR_LIVE_URL>/api/v1/admin/debug/corpus`
  - Expected: Should show `total_chunks` > 0 and list of `unique_sources_detected`.

## Frontend Verification
- [ ] **Environment Update:** Update `EXPO_PUBLIC_API_BASE_URL` in `nyaya-mitra-app/.env` to point to the live HTTPS URL.
- [ ] **Restart Bundler:** Restart the Expo bundler (`npx expo start -c`) to clear cache and apply the new URL.
- [ ] **Physical Device:** Open the app on a real Android/iOS device using Expo Go.
- [ ] **BYOK Test:** Enter an API key and tap "Test Connection".
  - *Success confirms:* CORS is configured correctly, and the network allows the connection.
- [ ] **Full Query Test:** Send a message.
  - *Success confirms:* The LLM service is working, the vector store loaded correctly on the server, and JSON parsing is intact.

## Security Audit
- [ ] **No Raw Keys in Logs:** Check the terminal output of the backend (uvicorn or localtunnel logs). Verify that the Gemini API key is *never* printed in full (should show `AIza...abcd`).
- [ ] **CORS Block (Optional):** Try hitting the `/api/v1/legal-query` endpoint from an unauthorized origin (e.g., a random codepen) to ensure it is rejected if `ALLOWED_ORIGINS` is strictly set.
