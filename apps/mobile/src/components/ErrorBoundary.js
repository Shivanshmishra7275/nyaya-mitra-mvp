/**
 * src/components/ErrorBoundary.js
 * =================================
 * React Error Boundary that catches uncaught JS errors in the component tree
 * and shows a friendly recovery screen instead of a blank crash.
 */
import React from 'react';
import { View, Text, Pressable, StyleSheet, ScrollView } from 'react-native';
import { COLORS } from '../theme/colors';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // In production you'd send this to Sentry / Crashlytics
    console.error('[ErrorBoundary] Caught error:', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <ScrollView contentContainerStyle={styles.container}>
          <Text style={styles.icon}>⚠️</Text>
          <Text style={styles.title}>Something went wrong</Text>
          <Text style={styles.subtitle}>
            Nyaya Mitra encountered an unexpected error.
          </Text>
          {__DEV__ && this.state.error && (
            <View style={styles.devBox}>
              <Text style={styles.devTitle}>Developer Info:</Text>
              <Text style={styles.devText}>
                {this.state.error.toString()}
              </Text>
            </View>
          )}
          <Pressable style={styles.btn} onPress={this.handleReset}>
            <Text style={styles.btnText}>↺ Tap to Restart</Text>
          </Pressable>
        </ScrollView>
      );
    }
    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: COLORS.screenBg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  icon: { fontSize: 56, marginBottom: 16 },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  devBox: {
    width: '100%',
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    padding: 12,
    marginBottom: 24,
  },
  devTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#991B1B',
    marginBottom: 4,
  },
  devText: { fontSize: 11, color: '#7F1D1D', lineHeight: 16 },
  btn: {
    backgroundColor: COLORS.brandAccent,
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
  },
  btnText: {
    color: COLORS.textOnDark,
    fontSize: 16,
    fontWeight: '700',
  },
});
