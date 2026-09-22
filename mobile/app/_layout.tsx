/**
 * The root: theme, safe areas, session, and the gate.
 *
 * The gate is the only place that decides which half of the app you see. While
 * the stored token is being checked the screen stays blank rather than showing
 * the sign-in form — flashing it at someone who is already signed in reads as a
 * bug, and on a cold start that check takes a Keychain read plus one request.
 */

import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { SessionProvider, useSession } from '../src/state/session';
import { ACCENT, BG } from '../src/theme';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <SessionProvider>
        <StatusBar style="light" />
        <Gate />
      </SessionProvider>
    </SafeAreaProvider>
  );
}

function Gate() {
  const { status } = useSession();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (status === 'checking') return;
    const inTabs = segments[0] === '(tabs)';
    if (status === 'signed-out' && inTabs) router.replace('/sign-in');
    if (status === 'signed-in' && !inTabs) router.replace('/');
  }, [status, segments, router]);

  if (status === 'checking') {
    return (
      <View style={{ flex: 1, backgroundColor: BG, justifyContent: 'center' }}>
        <ActivityIndicator color={ACCENT} />
      </View>
    );
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: BG },
        animation: 'fade',
      }}
    />
  );
}
