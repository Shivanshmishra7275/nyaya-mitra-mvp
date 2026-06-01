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
} from 'react-native';
import * as Clipboard from 'expo-clipboard';
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

  const {
    answer = '',
    legal_gps = '',
    issue_graph = [],
    opposition_view = [],
    strategy_tree = [],
    confidence,
    next_actions = [],
    scope_status = 'in_scope',

    legal_mapping = [],
    explanation = '',
    weaknesses = [],
    strategy_paths = [],
    lawyer_brief = '',
    citations = [],
    retrieval_note,
  } = content;

  const cleanList = (items) =>
    (Array.isArray(items) ? items : []).filter(
      (v) => typeof v === 'string' && v.trim().length > 0
    );

  const validCitations = cleanList(citations);
  const validMappings = cleanList(legal_mapping);
  const validIssues = cleanList(issue_graph);
  const validOpposition = cleanList(opposition_view);
  const validNextActions = cleanList(next_actions);

  const summaryText = answer || explanation;
  const detailText = answer && explanation && answer !== explanation ? explanation : '';
  const strategyNodes = Array.isArray(strategy_tree) && strategy_tree.length > 0
    ? strategy_tree
    : strategy_paths;

  const scopeMeta = {
    in_scope: { label: 'In scope', style: styles.scopeIn },
    partial_scope: { label: 'Partial scope', style: styles.scopePartial },
    out_of_scope: { label: 'Out of scope', style: styles.scopeOut },
  };
  const scopeKey = scopeMeta[scope_status] ? scope_status : 'in_scope';
  const scopeLabel = scopeMeta[scopeKey].label;
  const scopeStyle = scopeMeta[scopeKey].style;

  const handleCopyBrief = async () => {
    await Clipboard.setStringAsync(lawyer_brief);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <View style={styles.aiCard}>
      {/* Header row */}
      <View style={styles.cardHeader}>
        <Text style={styles.badge}>⚖️ NYAYA MITRA INTELLIGENCE</Text>
        <View style={[styles.scopePill, scopeStyle]}>
          <Text style={styles.scopeText}>{scopeLabel}</Text>
        </View>
      </View>

      {/* Legal disclaimer */}
      <View style={styles.disclaimerBanner}>
        <Text style={styles.disclaimerText}>
          ⚠️ Legal information only — not legal advice. Consult a lawyer.
        </Text>
      </View>

      {/* Legal Mapping (GPS) */}
      {validMappings.length > 0 && (
        <View style={styles.mappingRow}>
          <Text style={styles.mappingIcon}>📍</Text>
          <Text style={styles.mappingText}>{validMappings.join(' • ')}</Text>
        </View>
      )}

      {/* Legal GPS */}
      {legal_gps ? (
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Legal GPS</Text>
          <Text style={styles.infoText}>{legal_gps}</Text>
        </View>
      ) : null}

      {/* Summary / Answer */}
      {summaryText ? (
        <Text style={styles.explanation}>{summaryText}</Text>
      ) : null}

      {/* Detail explanation (optional) */}
      {detailText ? (
        <Text style={styles.detailText}>{detailText}</Text>
      ) : null}

      {/* Weaknesses Alert */}
      {weaknesses.length > 0 && (
        <View style={styles.weaknessBox}>
          <Text style={styles.weaknessTitle}>⚠️ CASE WEAKNESSES & GAPS</Text>
          {weaknesses.map((weakness, i) => (
            <Text key={i} style={styles.weaknessItem}>• {weakness}</Text>
          ))}
        </View>
      )}

      {/* Strategy Paths */}
      {Array.isArray(strategyNodes) && strategyNodes.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>🧭 STRATEGY OPTIONS</Text>
          {strategyNodes.map((path, i) => (
            <View key={i} style={styles.strategyCard}>
              <Text style={styles.strategyName}>{path.path_name}</Text>
              <Text style={styles.strategyDetail}><Text style={styles.bold}>When:</Text> {path.when_suitable}</Text>
              <Text style={styles.strategyDetail}><Text style={styles.bold}>Benefit:</Text> {path.benefit}</Text>
              <Text style={styles.strategyDetail}><Text style={styles.bold}>Risk:</Text> {path.risk}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Issue graph */}
      {validIssues.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>🧩 ISSUE GRAPH</Text>
          {validIssues.map((item, i) => (
            <Text key={i} style={styles.listItem}>• {item}</Text>
          ))}
        </View>
      )}

      {/* Opposition view */}
      {validOpposition.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>🛡 OPPOSITION VIEW</Text>
          {validOpposition.map((item, i) => (
            <Text key={i} style={styles.listItem}>• {item}</Text>
          ))}
        </View>
      )}

      {/* Confidence */}
      {confidence?.label && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>📊 CONFIDENCE</Text>
          <Text style={styles.infoText}>{confidence.label} — {confidence.reason || ''}</Text>
        </View>
      )}

      {/* Next actions */}
      {validNextActions.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>✅ NEXT ACTIONS</Text>
          {validNextActions.map((item, i) => (
            <Text key={i} style={styles.listItem}>• {item}</Text>
          ))}
        </View>
      )}

      {/* Lawyer Brief */}
      {lawyer_brief ? (
        <View style={styles.section}>
          <View style={styles.briefHeader}>
            <Text style={styles.sectionLabel}>💼 LAWYER CONSULTATION BRIEF</Text>
            <Pressable onPress={handleCopyBrief} style={styles.copyBtn} accessibilityLabel="Copy brief">
              <Text style={styles.copyText}>{copied ? '✓ Copied' : '⎘ Copy Brief'}</Text>
            </Pressable>
          </View>
          <View style={styles.briefBox}>
            <Text style={styles.briefText}>{lawyer_brief}</Text>
          </View>
        </View>
      ) : null}

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

  mappingRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12, backgroundColor: '#E3F2FD', padding: 8, borderRadius: 8 },
  mappingIcon: { fontSize: 14, marginRight: 6 },
  mappingText: { fontSize: 12, color: '#0277BD', fontWeight: '600', flexShrink: 1 },

  explanation: { fontSize: 15, color: COLORS.textPrimary, lineHeight: 23, marginBottom: 12 },

  weaknessBox: { backgroundColor: '#FFEBEE', padding: 12, borderRadius: 8, marginBottom: 12, borderWidth: 1, borderColor: '#FFCDD2' },
  weaknessTitle: { fontSize: 11, fontWeight: '700', color: '#C62828', marginBottom: 6 },
  weaknessItem: { fontSize: 13, color: '#B71C1C', lineHeight: 20 },

  strategyCard: { backgroundColor: '#FAFAFA', borderWidth: 1, borderColor: '#EEEEEE', borderRadius: 8, padding: 10, marginBottom: 8 },
  strategyName: { fontSize: 14, fontWeight: '700', color: COLORS.brandDark, marginBottom: 4 },
  strategyDetail: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 18, marginBottom: 2 },
  bold: { fontWeight: '600', color: COLORS.textPrimary },

  briefHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  briefBox: { backgroundColor: '#F5F5F5', padding: 12, borderRadius: 8, borderLeftWidth: 3, borderLeftColor: COLORS.brandAccent },
  briefText: { fontSize: 14, color: '#424242', lineHeight: 20, fontStyle: 'italic' },

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
  infoRow: { marginBottom: 10 },
  infoLabel: { fontSize: 10, fontWeight: '700', color: COLORS.textSecondary, marginBottom: 4 },
  infoText: { fontSize: 13, color: COLORS.textPrimary, lineHeight: 18 },
  detailText: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 20, marginBottom: 10 },
  listItem: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 19, marginBottom: 2 },
  scopePill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
  },
  scopeText: { fontSize: 10, fontWeight: '700', color: '#0B0B0B' },
  scopeIn: { backgroundColor: '#C8E6C9' },
  scopePartial: { backgroundColor: '#FFE0B2' },
  scopeOut: { backgroundColor: '#FFCDD2' },

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
