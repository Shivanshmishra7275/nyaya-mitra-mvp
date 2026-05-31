/**
 * App.js
 * =======
 * Nyaya Mitra — Application Root
 *
 * Wraps the entire app in an ErrorBoundary so uncaught JS errors
 * show a friendly recovery screen instead of a blank crash.
 * All business logic lives in src/screens/ChatScreen.js and sub-components.
 */
import React from 'react';
import ChatScreen from './src/screens/ChatScreen';
import { ErrorBoundary } from './src/components/ErrorBoundary';

export default function App() {
  return (
    <ErrorBoundary>
      <ChatScreen />
    </ErrorBoundary>
  );
}
