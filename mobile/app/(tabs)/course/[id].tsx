/**
 * A course: its modules and lessons, each marked done, readable or locked.
 *
 * A lesson the account cannot open (premium without the level) says so; it is
 * not hidden, and nothing pretends it can be read.
 */

import { useLocalSearchParams, useRouter } from 'expo-router';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Card, Meter, Pill, ScreenHeader, Section } from '../../../src/components/primitives';
import { Screen } from '../../../src/components/Screen';
import { useResource } from '../../../src/state/useResource';
import { INK, INK_2, INK_MUTED } from '../../../src/theme';

const ACCESS: Record<string, string> = { public: 'Libre', member: 'Membres', premium: 'Premium' };

export default function Course() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const course = useResource((client) => client.course(String(id)), [id]);
  const data = course.data;
  const done = new Set(data?.progress?.completed ?? []);

  return (
    <Screen loading={course.loading} refreshing={course.refreshing}
            offline={course.offline} error={course.error} onRefresh={course.refresh}>
      <Pressable accessibilityRole="link" onPress={() => router.back()}>
        <Text style={styles.back}>‹ Academy</Text>
      </Pressable>
      {data ? (
        <>
          <ScreenHeader eyebrow={data.level_label} title={data.title} subtitle={data.summary} />
          {data.progress ? (
            <View style={styles.progress}>
              <Meter fraction={data.progress.fraction} />
              <Text style={styles.meta}>{data.progress.done} sur {data.progress.total} leçons terminées</Text>
            </View>
          ) : null}
          {data.modules.map((module) => (
            <View key={module.id}>
              <Section title={`Chapitre ${module.number} · ${module.title}`} subtitle={module.summary} />
              {module.lessons.map((lesson) => (
                <Pressable key={lesson.id} accessibilityRole="button"
                           onPress={() => router.push(`/lesson/${data.id}/${lesson.id}`)}>
                  <Card style={styles.card}>
                    <Text style={styles.title}>{lesson.number}. {lesson.title}</Text>
                    <Text style={styles.summary} numberOfLines={2}>{lesson.summary}</Text>
                    <View style={styles.row}>
                      {done.has(lesson.id) ? <Pill text="Terminée" tone="good" icon />
                        : <Pill text={ACCESS[lesson.access] ?? lesson.access} />}
                      {lesson.duration_minutes ? <Text style={styles.meta}>{lesson.duration_minutes} min</Text> : null}
                    </View>
                  </Card>
                </Pressable>
              ))}
            </View>
          ))}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { color: INK_2, fontSize: 14, marginBottom: 8 },
  card: { marginBottom: 8 },
  title: { color: INK, fontSize: 15.5, fontWeight: '700', marginBottom: 4 },
  summary: { color: INK_2, fontSize: 13.5, lineHeight: 19 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 8 },
  meta: { color: INK_MUTED, fontSize: 12.5 },
  progress: { marginBottom: 6, gap: 6 },
});
