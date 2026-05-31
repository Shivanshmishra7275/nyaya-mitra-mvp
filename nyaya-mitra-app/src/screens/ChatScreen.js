/**
 * src/screens/ChatScreen.js
 * ==========================
 * The main chat interface screen.
 * Composed of focused sub-components — ChatScreen itself is pure layout.
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  FlatList,
  TextInput,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  Text,
  ActivityIndicator,
  StyleSheet,
  Alert,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useChat } from '../hooks/useChat';
import { useServerHealth } from '../hooks/useServerHealth';
import { UserBubble, AiCard } from '../components/ChatBubble';
import { ApiKeyModal } from '../components/ApiKeyModal';
import { loadKeySecurely } from '../services/keyStorage';
import { COLORS } from '../theme/colors';

export default function ChatScreen() {
  const [apiKey, setApiKey] = useState('');
  const [keyModalVisible, setKeyModalVisible] = useState(false);
  const [inputText, setInputText] = useState('');

  // Load persisted API key from SECURE storage on mount (opt-in by user in modal)
  // Chat history is loaded separately inside useChat via AsyncStorage.
  useEffect(() => {
    loadKeySecurely()
      .then((saved) => { if (saved) setApiKey(saved); })
      .catch(() => {});
  }, []);

  const {
    messages,
    isLoading,
    flatListRef,
    sendMessage,
    retryLast,
    clearChat,
  } = useChat(apiKey);

  // Server connectivity — polls every 30s, shows banner proactively
  const { isConnected, serverInfo, checkNow } = useServerHealth(apiKey);

  const handleSend = () => {
    if (!inputText.trim() || isLoading) return;
    sendMessage(inputText.trim());
    setInputText('');
  };

  const handleClearChat = () => {
    Alert.alert('Clear Chat', 'Are you sure you want to clear all messages?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Clear', style: 'destructive', onPress: clearChat },
    ]);
  };

  const renderItem = ({ item }) => {
    if (item.role === 'user') return <UserBubble text={item.content} />;
    if (item.role === 'error') return <AiCard content={item.content} onRetry={retryLast} />;
    return <AiCard content={item.content} />;
  };

  // Server status pill color logic
  const statusColor =
    isConnected === null ? '#94A3B8' :   // checking — grey
    isConnected ? '#22C55E' :             // connected — green
    '#EF4444';                            // disconnected — red
  const statusLabel =
    isConnected === null ? '⏳' :
    isConnected ? '🟢' :
    '🔴';

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" backgroundColor={COLORS.brandDark} />

      {/* ── Header ───────────────────────────────────────────────────────── */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.logo}>⚖️</Text>
          <View>
            <Text style={styles.title}>Nyaya Mitra</Text>
            <Text style={styles.subtitle}>AI Legal Guide · Indian Law</Text>
          </View>
        </View>
        <View style={styles.headerActions}>
          {/* Server status dot — tap to re-check */}
          <Pressable
            style={styles.statusDot}
            onPress={checkNow}
            accessibilityLabel={`Server ${isConnected ? 'connected' : 'disconnected'}. Tap to re-check.`}
          >
            <Text style={{ fontSize: 14 }}>{statusLabel}</Text>
          </Pressable>
          {/* API Key button */}
          <Pressable
            style={[styles.iconBtn, apiKey ? styles.iconBtnActive : null]}
            onPress={() => setKeyModalVisible(true)}
            accessibilityLabel="Set API Key"
          >
            <Text style={styles.iconBtnText}>🔑</Text>
          </Pressable>
          {/* Clear chat */}
          <Pressable style={styles.iconBtn} onPress={handleClearChat} accessibilityLabel="Clear chat">
            <Text style={styles.iconBtnText}>🗑</Text>
          </Pressable>
        </View>
      </View>

      {/* ── Server offline banner ─────────────────────────────────────────── */}
      {isConnected === false && (
        <Pressable style={styles.offlineBanner} onPress={checkNow}>
          <Text style={styles.offlineText}>
            📡 Cannot reach server. Tap to retry. · Check EXPO_PUBLIC_API_BASE_URL
          </Text>
        </Pressable>
      )}

      {/* ── No key warning ───────────────────────────────────────────────── */}
      {!apiKey && (
        <Pressable style={styles.noKeyBanner} onPress={() => setKeyModalVisible(true)}>
          <Text style={styles.noKeyText}>
            🔑 Tap here to enter your Gemini API key to start chatting
          </Text>
        </Pressable>
      )}

      {/* ── Chat area ────────────────────────────────────────────────────── */}
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.messageList}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          ListFooterComponent={
            isLoading ? (
              <View style={styles.typingRow}>
                <ActivityIndicator size="small" color={COLORS.brandAccent} />
                <Text style={styles.typingText}> Nyaya Mitra is thinking…</Text>
              </View>
            ) : null
          }
        />

        {/* ── Input bar ────────────────────────────────────────────────── */}
        <View style={styles.inputBar}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Ask a legal question…"
            placeholderTextColor={COLORS.textSecondary}
            multiline
            maxLength={1000}
            returnKeyType="send"
            onSubmitEditing={handleSend}
          />
          <Pressable
            style={[
              styles.sendBtn,
              (!inputText.trim() || isLoading) && styles.sendBtnDisabled,
            ]}
            onPress={handleSend}
            disabled={!inputText.trim() || isLoading}
            accessibilityLabel="Send message"
          >
            {isLoading ? (
              <ActivityIndicator size="small" color={COLORS.textOnDark} />
            ) : (
              <Text style={styles.sendIcon}>➤</Text>
            )}
          </Pressable>
        </View>
      </KeyboardAvoidingView>

      {/* ── BYOK Modal ───────────────────────────────────────────────────── */}
      <ApiKeyModal
        visible={keyModalVisible}
        currentKey={apiKey}
        onSave={setApiKey}
        onClose={() => setKeyModalVisible(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.brandDark },
  flex: { flex: 1 },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.brandDark,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.brandMid,
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  logo: { fontSize: 26 },
  title: { fontSize: 18, fontWeight: '700', color: COLORS.textOnDark },
  subtitle: { fontSize: 11, color: COLORS.textOnBrand, marginTop: 1 },
  headerActions: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  statusDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.brandMid,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.brandMid,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBtnActive: { backgroundColor: '#1B5E20' },
  iconBtnText: { fontSize: 16 },

  // Offline banner
  offlineBanner: {
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  offlineText: { fontSize: 12, color: '#991B1B', textAlign: 'center' },

  // No key banner
  noKeyBanner: {
    backgroundColor: '#FFF3CD',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  noKeyText: { fontSize: 13, color: '#856404', textAlign: 'center' },

  // Messages
  messageList: {
    flexGrow: 1,
    backgroundColor: COLORS.screenBg,
    paddingHorizontal: 12,
    paddingVertical: 16,
    gap: 4,
  },

  // Typing indicator
  typingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: COLORS.cardBg,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginTop: 4,
    marginBottom: 4,
  },
  typingText: { color: COLORS.textSecondary, fontSize: 14, fontStyle: 'italic' },

  // Input bar
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: COLORS.cardBg,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    gap: 8,
  },
  textInput: {
    flex: 1,
    minHeight: 42,
    maxHeight: 120,
    backgroundColor: COLORS.inputBg,
    borderWidth: 1,
    borderColor: COLORS.inputBorder,
    borderRadius: 21,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: COLORS.textPrimary,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.brandAccent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: { backgroundColor: COLORS.inputBorder },
  sendIcon: { color: COLORS.textOnDark, fontSize: 18, marginLeft: 2 },
});
