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
  'My neighbour threatened me after hitting my car. I don\'t have a video. What should I do?',
  'Someone filed a fake FIR against my brother for theft. He was out of town. What is our strategy?',
  'I was scammed online by a fake investment site. What sections apply and how to file?',
];

const FeatureItem = ({ icon, text }) => (
  <View style={styles.featureItem}>
    <Text style={styles.featureIcon}>{icon}</Text>
    <Text style={styles.featureText}>{text}</Text>
  </View>
);

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
          I am <Text style={styles.heroAccent}>Nyaya Mitra</Text>, your AI Case
          Intelligence Assistant for Indian law.
        </Text>
      </View>

      {/* Features */}
      <View style={styles.features}>
        <FeatureItem icon="📍" text="Maps facts to BNS, BNSS, BSA sections" />
        <FeatureItem icon="⚠️" text="Finds weaknesses & missing evidence" />
        <FeatureItem icon="🧭" text="Suggests strategic legal paths" />
        <FeatureItem icon="💼" text="Generates a structured lawyer brief" />
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

  // Features
  features: {
    backgroundColor: COLORS.cardBg,
    borderRadius: 16,
    padding: 16,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 2,
  },
  featureIcon: { fontSize: 18, width: 24, textAlign: 'center' },
  featureText: { fontSize: 13, color: COLORS.textPrimary, flex: 1, lineHeight: 18, fontWeight: '500' },

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
