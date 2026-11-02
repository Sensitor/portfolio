/**
 * ACADEMY — the paths and their courses, with the member's progress.
 *
 * In French, like the lessons. A path still in preparation is listed with its
 * state rather than hidden: the programme is the programme, and saying what is
 * not open yet is part of it.
 */

import { useRouter } from 'expo-router';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { AcademyCatalog, AcademyProgress } from '../../src/api/types';
import { Card, Meter, Note, Pill, ScreenHeader, Section } from '../../src/components/primitives';
import { Screen } from '../../src/components/Screen';
import { useResource } from '../../src/state/useResource';
import { INK, INK_2, INK_MUTED } from '../../src/theme';

interface Data {
  catalog: AcademyCatalog;
  progress: AcademyProgress | null;
}

export default function Academy() {
  const router = useRouter();
  const resource = useResource<Data>(async (client) => {
    const [catalog, progress] = await Promise.all([
      client.academyCatalog(),
      client.academyProgress().catch(() => null),
    ]);
    return { catalog, progress };
  }, []);
  const byCourse = new Map((resource.data?.progress?.courses ?? []).map((c) => [c.course_id, c]));
  const next = resource.data?.progress?.next;

  return (
    <Screen loading={resource.loading} refreshing={resource.refreshing}
            offline={resource.offline} error={resource.error} onRefresh={resource.refresh}>
      <ScreenHeader eyebrow="Sensitor Academy" title="Apprendre"
                    subtitle="Le trading, la monnaie et la crypto : des leçons sourcées, à lire où vous êtes." />
      {next?.course_id && next.lesson_id ? (
        <Pressable accessibilityRole="button"
                   onPress={() => router.push(`/lesson/${next.course_id}/${next.lesson_id}`)}>
          <Card>
            <Text style={styles.rubric}>REPRENDRE</Text>
            <Text style={styles.title}>La prochaine leçon de votre parcours</Text>
          </Card>
        </Pressable>
      ) : null}
      {(resource.data?.catalog.paths ?? []).map((path) => (
        <View key={path.id}>
          <Section title={`${path.label} · ${path.title}`} subtitle={path.summary} />
          {path.available ? path.courses.map((course) => {
            const progress = byCourse.get(course.id);
            return (
              <Pressable key={course.id} accessibilityRole="button"
                         onPress={() => router.push(`/course/${course.id}`)}>
                <Card style={styles.card}>
                  <Text style={styles.title}>{course.title}</Text>
                  <Text style={styles.summary} numberOfLines={3}>{course.summary}</Text>
                  <View style={styles.row}>
                    <Pill text={course.level_label} />
                    <Text style={styles.meta}>{course.lessons} leçons</Text>
                  </View>
                  {progress ? (
                    <View style={styles.progress}>
                      <Meter fraction={progress.fraction} />
                      <Text style={styles.meta}>{progress.done} sur {progress.total} terminées</Text>
                    </View>
                  ) : null}
                </Card>
              </Pressable>
            );
          }) : <Note text="Ce parcours est en préparation : il ouvrira quand ses leçons seront prêtes." />}
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: 10 },
  rubric: { color: INK_MUTED, fontSize: 11, fontWeight: '700', letterSpacing: 0.8, marginBottom: 4 },
  title: { color: INK, fontSize: 16.5, fontWeight: '700', marginBottom: 4 },
  summary: { color: INK_2, fontSize: 14, lineHeight: 20 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 8 },
  meta: { color: INK_MUTED, fontSize: 12.5 },
  progress: { marginTop: 10, gap: 6 },
});
