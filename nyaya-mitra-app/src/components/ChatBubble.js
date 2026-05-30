/**
 * src/components/ChatBubble.js
 * =============================
 * Renders either a user bubble or an AI response card based on `role`.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Clipboard,
  Alert,
} from 'react-native';
import { COLORS } from '../theme/colors';

// ─── User message bubble ─────────────────────────────────────────────────────

export function UserBubble({ text }) {
  return (
    <View style={styles.userWrapper}>
      <View style={styles.userBubble}>
        <Text style={styles.userText}>{text}</Text>
      </View>
    </View>
  );
}

// ─── AI response card ─────────────────────────────────────────────────────────

export function AiCard({ content, onRetry }) {
  const [copied, setCopied] = useState(false);

  if (typeof content === 'string') {
    // Error / plain-text fallback
    return (
      <View style={[styles.aiCard, styles.errorCard]}>
        <Text style={styles.badge}>⚠️ ERROR</Text>
        <Text style={styles.errorText}>{content}</Text>
        {onRetry && (
          <Pressable style={styles.retryBtn} onPress={onRetry}>
            <Text style={styles.retryText}>↺ Retry</Text>
          </Pressable>
        )}
      </View>
    );
  }

  const { explanation = '', citations = [], suggested_next_steps = [], retrieval_note } = content;

  const validCitations = citations.filter((c) => typeof c === 'string' && c.trim().length > 0);
  const validSteps = suggested_next_steps.filter((s) => typeof s === 'string' && s.trim().length > 0);

  const handleCopy = () => {
    const fullText = [
      explanation,
      validCitations.length ? '\nSources:\n' + validCitations.join('\n') : '',
      validSteps.length ? '\nNext Steps:\n' + validSteps.join('\n') : '',
    ]
      .filter(Boolean)
      .join('\n');
    Clipboard.setString(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <View style={styles.aiCard}>
      {/* Header row */}
      <View style={styles.cardHeader}>
        <Text style={styles.badge}>⚖️ NYAYA MITRA</Text>
        <Pressable onPress={handleCopy} style={styles.copyBtn} accessibilityLabel="Copy answer">
          <Text style={styles.copyText}>{copied ? '✓ Copied' : '⎘ Copy'}</Text>
        </Pressable>
      </View>

      {/* Legal disclaimer */}
      <View style={styles.disclaimerBanner}>
        <Text style={styles.disclaimerText}>
          ⚠️ Legal information only — not legal advice. Consult a lawyer.
        </Text>
      </View>

      {/* Main explanation */}
      <Text style={styles.explanation}>{explanation}</Text>

      {/* Citations */}
      {validCitations.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>📜 CITED SOURCES</Text>
          <View style={styles.pillRow}>
            {validCitations.map((cite, i) => (
              <View key={i} style={styles.pill}>
                <Text style={styles.pillText}>{cite}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Suggested next steps */}
      {validSteps.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>✅ SUGGESTED NEXT STEPS</Text>
          {validSteps.map((step, i) => (
            <View key={i} style={styles.stepRow}>
              <View style={styles.stepBullet}>
                <Text style={styles.stepNum}>{i + 1}</Text>
              </View>
              <Text style={styles.stepText}>{step}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Retrieval note (debug / transparency) */}
      {retrieval_note && (
        <Text style={styles.retrievalNote}>🔍 {retrieval_note}</Text>
      )}
    </View>
  );
}

// ─── Error card (role === 'error') ────────────────────────────────────────────

export function ErrorCard({ content, onRetry }) {
  return (
    <View style={[styles.aiCard, styles.errorCard]}>
      <Text style={styles.errorText}>{content}</Text>
      {onRetry && (
        <Pressable style={styles.retryBtn} onPress={onRetry}>
          <Text style={styles.retryText}>↺ Retry</Text>
        </Pressable>
      )}
    </View>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  // User bubble
  userWrapper: { alignItems: 'flex-end', marginVertical: 4 },
  userBubble: {
    backgroundColor: COLORS.brandMid,
    borderRadius: 18,
    borderBottomRightRadius: 4,
    paddingHorizontal: 14,
    paddingVertical: 10,
    maxWidth: '82%',
  },
  userText: { color: COLORS.textOnDark, fontSize: 15, lineHeight: 22 },

  // AI card
  aiCard: {
    backgroundColor: COLORS.cardBg,
    borderRadius: 16,
    borderTopLeftRadius: 4,
    padding: 14,
    maxWidth: '94%',
    alignSelf: 'flex-start',
    marginVertical: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  errorCard: { backgroundColor: '#FEF2F2' },

  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  badge: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.brandDark,
    letterSpacing: 0.5,
  },
  copyBtn: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    backgroundColor: COLORS.stepBg,
  },
  copyText: { fontSize: 11, color: COLORS.brandAccent, fontWeight: '600' },

  disclaimerBanner: {
    backgroundColor: '#FFF9C4',
    borderRadius: 6,
    padding: 6,
    marginBottom: 10,
  },
  disclaimerText: { fontSize: 10, color: '#7B6900', lineHeight: 14 },

  explanation: { fontSize: 15, color: COLORS.textPrimary, lineHeight: 23 },

  section: {
    marginTop: 14,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: 10,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.textSecondary,
    letterSpacing: 1,
    marginBottom: 8,
  },

  pillRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  pill: {
    backgroundColor: COLORS.citationBg,
    borderWidth: 1,
    borderColor: COLORS.citationBorder,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  pillText: { color: COLORS.citationText, fontSize: 12, fontWeight: '700' },

  stepRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 8, gap: 8 },
  stepBullet: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: COLORS.brandAccent,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  stepNum: { color: COLORS.textOnDark, fontSize: 11, fontWeight: '700' },
  stepText: { flex: 1, fontSize: 14, color: COLORS.textPrimary, lineHeight: 21 },

  retrievalNote: {
    fontSize: 10,
    color: COLORS.textSecondary,
    marginTop: 10,
    fontStyle: 'italic',
  },

  errorText: { color: '#B91C1C', fontSize: 14, lineHeight: 21 },
  retryBtn: {
    marginTop: 10,
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: COLORS.brandAccent,
    borderRadius: 8,
  },
  retryText: { color: COLORS.textOnDark, fontSize: 13, fontWeight: '600' },
});
