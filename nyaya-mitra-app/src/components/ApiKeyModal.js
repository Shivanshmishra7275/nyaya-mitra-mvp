/**
 * src/components/ApiKeyModal.js
 * ==============================
 * BYOK (Bring Your Own Key) modal for entering and testing the Gemini API key.
 *
 * Key persistence: expo-secure-store (Keychain on iOS, EncryptedSharedPreferences on Android).
 * Chat history persistence: AsyncStorage (handled separately in useChat.js — non-sensitive).
 *
 * Security properties:
 *  - Key is only persisted if user explicitly opts in via the toggle.
 *  - Key is never logged or returned unnecessarily.
 *  - Raw key is sent only per-request via Authorization header.
 */
import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Switch,
} from 'react-native';
import { checkHealth } from '../services/api';
import { saveKeySecurely, deleteKey } from '../services/keyStorage';
import { COLORS } from '../theme/colors';

// NOTE: SAVED_KEY_STORAGE (AsyncStorage key) removed here.
// Key persistence now uses expo-secure-store via keyStorage.js.

export function ApiKeyModal({ visible, currentKey, onSave, onClose }) {
  const [draftKey, setDraftKey] = useState(currentKey || '');
  const [showKey, setShowKey] = useState(false);
  const [testStatus, setTestStatus] = useState(null); // null | 'testing' | 'ok' | 'error'
  const [testMessage, setTestMessage] = useState('');
  // Initialize toggle to true if a key is already saved (currentKey is non-empty)
  const [persistKey, setPersistKey] = useState(!!currentKey);

  // Sync draftKey and persistKey when the modal opens with an existing key
  React.useEffect(() => {
    if (visible) {
      setDraftKey(currentKey || '');
      setPersistKey(!!currentKey);
      setTestStatus(null);
      setTestMessage('');
    }
  }, [visible, currentKey]);

  const handleTest = async () => {
    if (!draftKey.trim()) {
      setTestStatus('error');
      setTestMessage('Please enter an API key first.');
      return;
    }
    setTestStatus('testing');
    setTestMessage('');
    try {
      const health = await checkHealth(draftKey.trim());
      setTestStatus('ok');
      setTestMessage(
        `✓ Connected! Server is ${health.status}.\n` +
        `Retrieval: ${health.retrieval_mode}\n` +
        `Chunks: ${health.chunks_loaded}`
      );
    } catch (err) {
      setTestStatus('error');
      setTestMessage(`✗ ${err.message}`);
    }
  };

  const handleSave = async () => {
    const key = draftKey.trim();
    if (persistKey && key) {
      // Save to secure enclave (Keychain / EncryptedSharedPreferences)
      await saveKeySecurely(key);
    } else {
      // User chose not to persist — delete any previously saved key
      await deleteKey();
    }
    onSave(key);
    onClose();
  };

  const handleClear = async () => {
    setDraftKey('');
    setTestStatus(null);
    setTestMessage('');
    await deleteKey();
    onSave('');
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Header */}
            <Text style={styles.title}>🔑 Gemini API Key</Text>

            {/* Warning banner */}
            <View style={styles.warningBanner}>
              <Text style={styles.warningText}>
                ⚠️ BYOK Notice: You are responsible for your own Gemini API key, quota, and billing.
                Your key is sent directly to the backend for each request and is NOT stored on the server.
                {'\n\n'}Get a FREE key at: aistudio.google.com/app/apikey
              </Text>
            </View>

            {/* Key input */}
            <Text style={styles.label}>Your Gemini API Key</Text>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.keyInput}
                value={draftKey}
                onChangeText={setDraftKey}
                placeholder="AIza..."
                placeholderTextColor={COLORS.textSecondary}
                secureTextEntry={!showKey}
                autoCapitalize="none"
                autoCorrect={false}
                autoComplete="off"
              />
              <Pressable onPress={() => setShowKey((v) => !v)} style={styles.eyeBtn}>
                <Text style={styles.eyeText}>{showKey ? '🙈' : '👁'}</Text>
              </Pressable>
            </View>

            {/* Persist option */}
            <View style={styles.persistRow}>
              <Switch
                value={persistKey}
                onValueChange={setPersistKey}
                trackColor={{ true: COLORS.brandAccent }}
              />
              <Text style={styles.persistLabel}>
                Save key on this device (optional — stores in local device storage only)
              </Text>
            </View>

            {/* Test connection */}
            <Pressable
              style={[styles.testBtn, testStatus === 'testing' && styles.btnDisabled]}
              onPress={handleTest}
              disabled={testStatus === 'testing'}
            >
              {testStatus === 'testing' ? (
                <ActivityIndicator size="small" color={COLORS.textOnDark} />
              ) : (
                <Text style={styles.testBtnText}>Test Connection</Text>
              )}
            </Pressable>

            {/* Test result */}
            {testStatus && testStatus !== 'testing' && (
              <View style={[styles.testResult, testStatus === 'ok' ? styles.testOk : styles.testErr]}>
                <Text style={testStatus === 'ok' ? styles.testOkText : styles.testErrText}>
                  {testMessage}
                </Text>
              </View>
            )}

            {/* Action buttons */}
            <View style={styles.actions}>
              <Pressable style={styles.saveBtn} onPress={handleSave}>
                <Text style={styles.saveBtnText}>Save & Close</Text>
              </Pressable>
              <Pressable style={styles.clearBtn} onPress={handleClear}>
                <Text style={styles.clearBtnText}>Clear Key</Text>
              </Pressable>
            </View>

            <Pressable onPress={onClose} style={styles.cancelLink}>
              <Text style={styles.cancelText}>Cancel</Text>
            </Pressable>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: COLORS.cardBg,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '90%',
  },
  title: { fontSize: 20, fontWeight: '700', color: COLORS.brandDark, marginBottom: 12 },
  warningBanner: {
    backgroundColor: '#FFF3CD',
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
  },
  warningText: { fontSize: 12, color: '#856404', lineHeight: 18 },
  label: { fontSize: 13, fontWeight: '600', color: COLORS.textSecondary, marginBottom: 6 },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.inputBorder,
    borderRadius: 10,
    backgroundColor: COLORS.inputBg,
    marginBottom: 12,
  },
  keyInput: {
    flex: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: COLORS.textPrimary,
  },
  eyeBtn: { paddingHorizontal: 12 },
  eyeText: { fontSize: 18 },
  persistRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 10,
  },
  persistLabel: { flex: 1, fontSize: 12, color: COLORS.textSecondary, lineHeight: 16 },
  testBtn: {
    backgroundColor: COLORS.brandMid,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  btnDisabled: { opacity: 0.6 },
  testBtnText: { color: COLORS.textOnDark, fontWeight: '600', fontSize: 14 },
  testResult: { borderRadius: 8, padding: 10, marginBottom: 14 },
  testOk: { backgroundColor: '#D1FAE5' },
  testErr: { backgroundColor: '#FEE2E2' },
  testOkText: { color: '#065F46', fontSize: 13 },
  testErrText: { color: '#991B1B', fontSize: 13 },
  actions: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  saveBtn: {
    flex: 1,
    backgroundColor: COLORS.brandAccent,
    borderRadius: 10,
    paddingVertical: 13,
    alignItems: 'center',
  },
  saveBtnText: { color: COLORS.textOnDark, fontWeight: '700', fontSize: 15 },
  clearBtn: {
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.inputBorder,
    alignItems: 'center',
  },
  clearBtnText: { color: COLORS.textSecondary, fontWeight: '600', fontSize: 14 },
  cancelLink: { alignItems: 'center', paddingVertical: 8 },
  cancelText: { color: COLORS.textSecondary, fontSize: 14 },
});
