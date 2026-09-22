/**
 * The five tabs, mirroring the five Streamlit trading pages.
 *
 * Labels only, no icons: the five are Overview, Journal, Analytics, Risk and
 * Psychology, and there is no icon for "psychology" that a reader decodes
 * faster than the word. A glyph nobody recognises is worse than a short label.
 */

import { Tabs } from 'expo-router';
import React from 'react';

import { ACCENT, BG, BORDER, INK_MUTED, SURFACE } from '../../src/theme';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: ACCENT,
        tabBarInactiveTintColor: INK_MUTED,
        tabBarStyle: {
          backgroundColor: SURFACE,
          borderTopColor: BORDER,
          borderTopWidth: 1,
        },
        tabBarLabelStyle: { fontSize: 10.5, fontWeight: '700' },
        tabBarIconStyle: { display: 'none' },
        sceneStyle: { backgroundColor: BG },
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Overview' }} />
      <Tabs.Screen name="journal" options={{ title: 'Journal' }} />
      <Tabs.Screen name="analytics" options={{ title: 'Analytics' }} />
      <Tabs.Screen name="risk" options={{ title: 'Risk' }} />
      <Tabs.Screen name="psychology" options={{ title: 'Psychology' }} />
    </Tabs>
  );
}
