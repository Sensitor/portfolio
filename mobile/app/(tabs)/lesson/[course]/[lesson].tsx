/**
 * A lesson, to read; then marked as done, and on to the next one.
 *
 * A locked lesson answers 401 or 403 from the server, and the screen says
 * which: sign in, or this lesson is part of Premium access. The sources of the
 * lesson are listed under it, as on the platform.
 */

import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { ApiError } from '../../../../src/api/client';
import { LessonBlocks } from '../../../../src/components/LessonBlocks';
import { Empty, ScreenHeader, Section } from '../../../../src/components/primitives';
import { Screen } from '../../../../src/components/Screen';
import { useSession } from '../../../../src/state/session';
import { useResource } from '../../../../src/state/useResource';
import { ACCENT, BORDER, INK, INK_2, INK_MUTED } from '../../../../src/theme';

export default function Lesson() {
  const { course, lesson } = useLocalSearchParams<{ course: string; lesson: string }>();
  const router = useRouter();
  const { client } = useSession();
  const [saved, setSaved] = useState<string | null>(null);
  const resource = useResource(async (c) => {
    try {
      return { lesson: await c.lesson(String(course), String(lesson)), locked: null as string | null };
    } catch (caught) {
      const status = (caught as ApiError).status;
      if (status === 401) return { lesson: null, locked: 'Connectez-vous pour lire cette leçon.' };
      if (status === 403) return { lesson: null, locked: "Cette leçon fait partie de l'accès Premium." };
      throw caught;
    }
  }, [course, lesson]);
  const data = resource.data?.lesson;

  async function complete() {
    if (!data) return;
    try {
      await client.completeLesson(data.course_id, data.id);
      setSaved('Leçon marquée comme terminée.');
    } catch {
      setSaved("La progression n'a pas pu être enregistrée.");
    }
  }

  return (
    <Screen loading={resource.loading} refreshing={resource.refreshing}
            offline={resource.offline} error={resource.error} onRefresh={resource.refresh}>
      <Pressable accessibilityRole="link" onPress={() => router.back()}>
        <Text style={styles.back}>‹ Le cours</Text>
      </Pressable>
      {resource.data?.locked ? <Empty title="Leçon réservée" body={resource.data.locked} icon="◇" /> : null}
      {data ? (
        <>
          <ScreenHeader eyebrow={`Leçon ${data.number}`} title={data.title} subtitle={data.summary} />
          {data.objectives.length ? (
            <View style={styles.objectives}>
              <Text style={styles.rubric}>À LA FIN DE CETTE LEÇON, VOUS SAUREZ</Text>
              {data.objectives.map((o, i) => <Text key={i} style={styles.objective}>{i + 1}. {o}</Text>)}
            </View>
          ) : null}
          <LessonBlocks blocks={data.blocks} />
          {data.sources.length ? (
            <>
              <Section title="Sources" />
              {data.sources.map((s, i) => <Text key={i} style={styles.source}>{s}</Text>)}
            </>
          ) : null}
          <Pressable accessibilityRole="button" onPress={complete} style={styles.button}>
            <Text style={styles.buttonText}>Marquer comme terminée</Text>
          </Pressable>
          {saved ? <Text style={styles.saved}>{saved}</Text> : null}
          {data.next_id ? (
            <Pressable accessibilityRole="link" onPress={() => router.replace(`/lesson/${data.course_id}/${data.next_id}`)}>
              <Text style={styles.next}>Leçon suivante ›</Text>
            </Pressable>
          ) : null}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  back: { color: INK_2, fontSize: 14, marginBottom: 8 },
  rubric: { color: INK_MUTED, fontSize: 11, fontWeight: '700', letterSpacing: 0.8, marginBottom: 6 },
  objectives: { borderTopWidth: 1, borderBottomWidth: 1, borderColor: BORDER, paddingVertical: 10, marginBottom: 14 },
  objective: { color: INK, fontSize: 14.5, lineHeight: 21, marginBottom: 4 },
  source: { color: INK_2, fontSize: 12.5, lineHeight: 18, marginBottom: 4 },
  button: { backgroundColor: ACCENT, borderRadius: 6, paddingVertical: 12, alignItems: 'center', marginTop: 18 },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  saved: { color: INK_2, fontSize: 13, marginTop: 8, textAlign: 'center' },
  next: { color: ACCENT, fontSize: 15, fontWeight: '700', marginTop: 16, textAlign: 'center' },
});
