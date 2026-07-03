/**
 * src/config/api.js
 * ==================
 * Centralized API configuration for Nyaya Mitra.
 *
 * HOW TO CONFIGURE FOR PHYSICAL DEVICES:
 * ----------------------------------------
 * Physical devices cannot reach your laptop via 127.0.0.1 or 10.0.2.2.
 * You MUST set EXPO_PUBLIC_API_BASE_URL to your machine's LAN IP address.
 *
 * Step 1: Find your machine's LAN IP
 *   Windows: Open cmd → run `ipconfig` → look for "IPv4 Address" (e.g. 192.168.1.42)
 *   Mac:     Open terminal → run `ifconfig en0` → look for "inet"
 *
 * Step 2: Create nyaya-mitra-app/.env (copy from .env.example)
 *   EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
 *
 * Step 3: Start backend on all interfaces (not just 127.0.0.1)
 *   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
 *
 * Platform defaults (when EXPO_PUBLIC_API_BASE_URL is NOT set):
 *   Android emulator: http://10.0.2.2:8000   ← routes to host localhost
 *   iOS simulator:    http://localhost:8000    ← simulator shares host network
 *   Physical device:  !! WILL FAIL !!         ← must set env var
 *
 * Production:
 *   EXPO_PUBLIC_API_BASE_URL=https://nyaya-mitra-api.onrender.com
 */
import { Platform } from 'react-native';

// Expo SDK 49+ exposes EXPO_PUBLIC_ prefixed vars on process.env automatically.
// These are baked in at build time — restart `expo start` after changing .env.
const ENV_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL;

function getDefaultBaseUrl() {
  if (ENV_BASE_URL && ENV_BASE_URL.trim() !== '') {
    return ENV_BASE_URL.trim();
  }

  // Warn in dev when no env var is set — physical device will fail
  if (typeof __DEV__ !== 'undefined' && __DEV__) {
    if (Platform.OS === 'android') {
      // 10.0.2.2 works for Android EMULATOR only, not physical devices
      console.warn(
        '[Nyaya Mitra] EXPO_PUBLIC_API_BASE_URL not set. ' +
        'Using Android emulator default (10.0.2.2). ' +
        'Physical devices require setting your LAN IP in nyaya-mitra-app/.env'
      );
      return 'http://10.0.2.2:8000';
    }
    // iOS simulator shares host network stack, so localhost works
    console.warn(
      '[Nyaya Mitra] EXPO_PUBLIC_API_BASE_URL not set. ' +
      'Using localhost. Physical iOS devices require your LAN IP in nyaya-mitra-app/.env'
    );
    return 'http://localhost:8000';
  }

  // Production or no __DEV__ context — safest default
  return 'http://localhost:8000';
}

export const API_BASE_URL = getDefaultBaseUrl();
export const LEGAL_QUERY_URL = `${API_BASE_URL}/api/v1/legal-query`;
export const HEALTH_URL = `${API_BASE_URL}/health`;
