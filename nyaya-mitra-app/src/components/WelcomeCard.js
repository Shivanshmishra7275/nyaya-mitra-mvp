/**
 * src/components/WelcomeCard.js
 * ==============================
 * Full-screen welcome splash shown on first launch when chat history is empty.
 * Explains what Nyaya Mitra is and prompts the user to get started.
 * Disappears as soon as the first message arrives.
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
} from 'react-native';
import { COLORS } from '../theme/colors';

const LAW_TOPICS = [
  { icon: '📜', label: 'Bharatiya Nyaya Sanhita (BNS)' },
  { icon: '🏛️', label: 'Bharatiya Nagarik Suraksha Sanhita (BNSS)' },
  { icon: '📋', label: 'Bharatiya Sakshya Adhiniyam (BSA)' },
  { icon: '🇮🇳', label: 'Constitution of India' },
];

const SAMPLE_QUERIES = [
  'What is the punishment for theft under BNS?',
  'What are my rights if I am arrested?',
  'How is bail granted under BNSS?',
  'What evidence is admissible in court?',
];

export function WelcomeCard({ onSampleQuery }) {
  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.container}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero */}
      <View style={styles.hero}>
        <Text style={styles.heroIcon}>⚖️</Text>
        <Text style={styles.heroTitle}>Namaste 🙏</Text>
        <Text style={styles.heroSubtitle}>
          I am <Text style={styles.heroAccent}>Nyaya Mitra</Text>, your free AI legal
          guide for Indian law.
        </Text>
      </View>

      {/* What I cover */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>📚 What I Cover</Text>
        {LAW_TOPICS.map((t) => (
          <View key={t.label} style={styles.topicRow}>
            <Text style={styles.topicIcon}>{t.icon}</Text>
            <Text style={styles.topicLabel}>{t.label}</Text>
          </View>
        ))}
      </View>

      {/* Try asking */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>💡 Try Asking</Text>
        {SAMPLE_QUERIES.map((q) => (
          <Pressable
            key={q}
            style={({ pressed }) => [styles.sampleBtn, pressed && styles.sampleBtnPressed]}
            onPress={() => onSampleQuery(q)}
          >
            <Text style={styles.sampleText}>"{q}"</Text>
            <Text style={styles.sampleArrow}>→</Text>
          </Pressable>
        ))}
      </View>

      {/* Disclaimer */}
      <View style={styles.disclaimer}>
        <Text style={styles.disclaimerText}>
          ⚠️ <Text style={styles.bold}>Important:</Text> I provide legal{' '}
          <Text style={styles.bold}>information</Text>, not legal{' '}
          <Text style={styles.bold}>advice</Text>. Always consult a qualified lawyer for
          your specific situation.
        </Text>
      </View>

      {/* BYOK note */}
      <View style={styles.byokNote}>
        <Text style={styles.byokText}>
          🔑 <Text style={styles.bold}>Free to use:</Text> Enter your own Gemini API
          key (tap the 🔑 icon above). Get a free key at{' '}
          <Text style={styles.link}>aistudio.google.com/app/apikey</Text>
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1, backgroundColor: COLORS.screenBg },
  container: {
    padding: 16,
    paddingBottom: 32,
    gap: 16,
  },

  // Hero
  hero: {
    backgroundColor: COLORS.brandDark,
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
  },
  heroIcon: { fontSize: 52, marginBottom: 8 },
  heroTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: COLORS.textOnDark,
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 15,
    color: COLORS.textOnBrand,
    textAlign: 'center',
    lineHeight: 22,
  },
  heroAccent: { fontWeight: '800', color: '#7DD3FC' },

  // Card
  card: {
    backgroundColor: COLORS.cardBg,
    borderRadius: 16,
    padding: 16,
    gap: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.brandDark,
    marginBottom: 4,
    letterSpacing: 0.3,
  },

  // Topics
  topicRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 4,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  topicIcon: { fontSize: 18, width: 28 },
  topicLabel: { fontSize: 14, color: COLORS.textPrimary, flex: 1, lineHeight: 20 },

  // Sample queries
  sampleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.stepBg,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  sampleBtnPressed: { backgroundColor: COLORS.citationBg },
  sampleText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.brandMid,
    fontStyle: 'italic',
    lineHeight: 18,
  },
  sampleArrow: { fontSize: 16, color: COLORS.brandAccent },

  // Disclaimer
  disclaimer: {
    backgroundColor: '#FFF9C4',
    borderRadius: 12,
    padding: 14,
  },
  disclaimerText: { fontSize: 13, color: '#7B6900', lineHeight: 19 },

  // BYOK note
  byokNote: {
    backgroundColor: COLORS.citationBg,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.citationBorder,
  },
  byokText: { fontSize: 13, color: COLORS.citationText, lineHeight: 19 },
  link: { textDecorationLine: 'underline' },
  bold: { fontWeight: '700' },
});
