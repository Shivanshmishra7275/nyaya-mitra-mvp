/**
 * src/services/keyStorage.js
 * ===========================
 * Secure API key storage using expo-secure-store.
 *
 * Why expo-secure-store instead of AsyncStorage for the key:
 *  - expo-secure-store uses the platform's secure enclave:
 *    iOS: Keychain Services
 *    Android: EncryptedSharedPreferences / Android Keystore
 *  - AsyncStorage is plain unencrypted SQLite — not appropriate for API keys.
 *  - Chat history remains in AsyncStorage (non-sensitive, large, indexed).
 *
 * Security guarantees:
 *  - The raw key is never logged or returned to the calling code unnecessarily.
 *  - deleteKey() fully removes the stored value.
 *  - If the device does not support secure storage (unlikely), falls back
 *    gracefully to null (key not persisted, session-only).
 */
import * as SecureStore from 'expo-secure-store';

const SECURE_KEY_ITEM = 'nyaya_mitra_gemini_key';

/**
 * Save the API key securely on this device.
 * @param {string} key - The raw Gemini API key to persist.
 * @returns {Promise<boolean>} true on success, false on failure.
 */
export async function saveKeySecurely(key) {
  if (!key || !key.trim()) {
    return deleteKey();
  }
  try {
    await SecureStore.setItemAsync(SECURE_KEY_ITEM, key.trim());
    return true;
  } catch (e) {
    console.warn('[keyStorage] SecureStore.setItemAsync failed:', e?.message);
    return false;
  }
}

/**
 * Load the persisted API key from secure storage.
 * @returns {Promise<string|null>} The key, or null if not saved or unavailable.
 */
export async function loadKeySecurely() {
  try {
    const val = await SecureStore.getItemAsync(SECURE_KEY_ITEM);
    return val || null;
  } catch (e) {
    console.warn('[keyStorage] SecureStore.getItemAsync failed:', e?.message);
    return null;
  }
}

/**
 * Delete the persisted API key from secure storage.
 * @returns {Promise<boolean>}
 */
export async function deleteKey() {
  try {
    await SecureStore.deleteItemAsync(SECURE_KEY_ITEM);
    return true;
  } catch (e) {
    console.warn('[keyStorage] SecureStore.deleteItemAsync failed:', e?.message);
    return false;
  }
}
