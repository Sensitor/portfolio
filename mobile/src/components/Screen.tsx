/**
 * The frame every tab shares: safe areas, pull-to-refresh, and the two states
 * that are easy to get wrong.
 *
 * **Offline is not an error.** A dropped connection keeps whatever is on screen
 * and adds a line saying it may be stale. Blanking the page would punish the
 * person for a tunnel dropping.
 *
 * **Loading is only shown when there is nothing to show.** A refresh over
 * existing data spins the pull-to-refresh control, not the whole screen.
 */

import React from 'react';
import {
  ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ACCENT, BG, INK_FAINT, SURFACE_2, WARNING } from '../theme';
import { Empty } from './primitives';

export function Screen({
  children, loading, refreshing, offline, error, onRefresh,
}: {
  children: React.ReactNode;
  loading?: boolean;
  refreshing?: boolean;
  offline?: boolean;
  error?: string | null;
  onRefresh?(): void;
}) {
  const insets = useSafeAreaInsets();

  if (loading) {
    return (
      <View style={[styles.centred, { paddingTop: insets.top }]}>
        <ActivityIndicator color={ACCENT} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={[
        styles.content,
        { paddingTop: insets.top + 14, paddingBottom: insets.bottom + 90 },
      ]}
      refreshControl={
        onRefresh
          ? <RefreshControl refreshing={!!refreshing} onRefresh={onRefresh}
                            tintColor={ACCENT} />
          : undefined
      }
    >
      {offline ? <Banner text="Offline — showing the last data this device fetched." /> : null}
      {error ? <Empty title="Something went wrong" body={error} icon="◌" /> : null}
      {children}
    </ScrollView>
  );
}

function Banner({ text }: { text: string }) {
  return (
    <View style={styles.banner}>
      <Text style={styles.bannerText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: BG },
  content: { paddingHorizontal: 16 },
  centred: { flex: 1, backgroundColor: BG, alignItems: 'center', justifyContent: 'center' },
  banner: {
    backgroundColor: SURFACE_2, borderLeftWidth: 3, borderLeftColor: WARNING,
    paddingVertical: 9, paddingHorizontal: 12, borderRadius: 6, marginBottom: 12,
  },
  bannerText: { fontSize: 11.5, color: INK_FAINT },
});
