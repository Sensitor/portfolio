/**
 * A lesson's blocks, read on a phone.
 *
 * Text is what a phone reads well, so text is rendered here: paragraphs,
 * headings, lists, bold, callouts (an opinion and a debate keep their frame,
 * as on the platform), figures (the original SVG), formulas (as written).
 * The interactive blocks (exercises, simulators, charts) say they open on the
 * platform rather than pretending: a simulator squeezed into a phone, or a
 * chart without its data, would teach less than the sentence that points to it.
 *
 * A video opens in the browser only when asked, so reading the lesson sends
 * nothing to the video host; its transcript is shown in full.
 */

import React from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { SvgXml } from 'react-native-svg';

import type { LessonBlock } from '../api/types';
import { ACCENT, BORDER, INK, INK_2, INK_MUTED, SURFACE, SURFACE_2, WARNING } from '../theme';

const CALLOUT_TITLES: Record<string, string> = {
  note: 'À retenir', definition: 'Définition', example: 'Exemple', warning: 'Attention',
  mistake: 'Erreur fréquente', recap: 'Récapitulatif', method: 'Hypothèse de méthode',
  opinion: 'Opinion du fondateur', debate: 'Débat',
};
const PLATFORM = 'À faire sur la plateforme web : les exercices, les simulateurs et les graphiques y sont interactifs.';

/** `**bold**` and `*italic*` in a line, as nested Text. */
function Inline({ text, style }: { text: string; style?: object }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g).filter(Boolean);
  return (
    <Text style={[styles.text, style]}>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <Text key={i} style={styles.bold}>{part.slice(2, -2)}</Text>;
        }
        if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
          return <Text key={i} style={styles.italic}>{part.slice(1, -1)}</Text>;
        }
        return part.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/`([^`]+)`/g, '$1');
      })}
    </Text>
  );
}

/** The Markdown subset the lessons use, line by line. */
export function Markdown({ text }: { text: string }) {
  const lines = text.split('\n');
  const out: React.ReactNode[] = [];
  let paragraph: string[] = [];
  const flush = () => {
    if (paragraph.length) {
      out.push(<Inline key={`p${out.length}`} text={paragraph.join(' ')} style={styles.paragraph} />);
      paragraph = [];
    }
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) { flush(); continue; }
    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line);
    const numbered = /^\s*(\d+)\.\s+(.*)$/.exec(line);
    if (heading) {
      flush();
      const level = heading[1] ?? '#';
      out.push(<Inline key={`h${out.length}`} text={heading[2] ?? ''}
                       style={level.length <= 2 ? styles.h2 : styles.h3} />);
    } else if (bullet || numbered) {
      flush();
      const marker = bullet ? '•' : `${numbered?.[1] ?? ''}.`;
      const body = (bullet ? bullet[1] : numbered?.[2]) ?? '';
      out.push(
        <View key={`l${out.length}`} style={styles.item}>
          <Text style={styles.marker}>{marker}</Text>
          <Inline text={body} style={styles.itemText} />
        </View>,
      );
    } else if (line.startsWith('|')) {
      flush();
      if (!/^\|[\s:|-]+\|$/.test(line)) {
        const cells = line.split('|').map((c) => c.trim()).filter(Boolean);
        out.push(<Inline key={`t${out.length}`} text={cells.join('  ·  ')} style={styles.tableRow} />);
      }
    } else {
      paragraph.push(line.trim());
    }
  }
  flush();
  return <View>{out}</View>;
}

function Video({ block }: { block: LessonBlock }) {
  const minutes = block.duration_minutes ? ` · ${block.duration_minutes} min` : '';
  return (
    <View style={styles.card}>
      <Text style={styles.rubric}>VIDÉO{minutes.toUpperCase()} · {block.host || 'SERVICE TIERS'}</Text>
      {block.title ? <Text style={styles.h3}>{block.title}</Text> : null}
      <Pressable accessibilityRole="link" onPress={() => block.url && Linking.openURL(block.url)}>
        <Text style={styles.link}>Lire la vidéo sur {block.host || 'le service tiers'}</Text>
      </Pressable>
      <Text style={styles.small}>Rien n'est envoyé à {block.host || 'ce service'} avant d'ouvrir la vidéo.</Text>
      {block.text ? <Markdown text={block.text} /> : null}
      {block.transcript ? (
        <View style={styles.transcript}>
          <Text style={styles.rubric}>TRANSCRIPTION</Text>
          <Markdown text={block.transcript} />
        </View>
      ) : null}
    </View>
  );
}

export function LessonBlocks({ blocks }: { blocks: LessonBlock[] }) {
  let figure = 0;
  let pointed = false;
  return (
    <View>
      {blocks.map((block, index) => {
        switch (block.kind) {
          case 'markdown':
            return <Markdown key={index} text={block.text} />;
          case 'callout': {
            const style = block.style ?? 'note';
            const framed = style === 'opinion' || style === 'debate';
            return (
              <View key={index} style={[styles.callout, framed && styles.calloutFramed]}>
                <Text style={styles.calloutTitle}>{block.title || CALLOUT_TITLES[style] || 'À retenir'}</Text>
                <Markdown text={block.text} />
              </View>
            );
          }
          case 'figure':
            figure += 1;
            return (
              <View key={index} style={styles.figure}>
                {block.svg ? <SvgXml xml={block.svg} width="100%" height={220} /> : null}
                <Text style={styles.small}>Figure {figure}. </Text>
                <Markdown text={block.text} />
              </View>
            );
          case 'formula':
            return <Text key={index} style={styles.formula}>{block.text}</Text>;
          case 'video':
            return <Video key={index} block={block} />;
          default:
            // Exercises, simulators, charts: once per lesson, the pointer to the platform.
            if (pointed) return null;
            pointed = true;
            return (
              <View key={index} style={styles.platform}>
                <Text style={styles.small}>{PLATFORM}</Text>
              </View>
            );
        }
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  text: { color: INK, fontSize: 15.5, lineHeight: 23 },
  paragraph: { marginBottom: 12 },
  bold: { fontWeight: '700', color: INK },
  italic: { fontStyle: 'italic' },
  h2: { fontSize: 19, fontWeight: '700', marginTop: 14, marginBottom: 8 },
  h3: { fontSize: 16.5, fontWeight: '700', marginTop: 10, marginBottom: 6 },
  item: { flexDirection: 'row', marginBottom: 6, paddingRight: 8 },
  marker: { color: ACCENT, width: 22, fontSize: 15.5, lineHeight: 23 },
  itemText: { flex: 1 },
  tableRow: { fontSize: 13.5, color: INK_2, paddingVertical: 4, borderBottomWidth: 1, borderBottomColor: BORDER },
  callout: { backgroundColor: SURFACE, borderLeftWidth: 3, borderLeftColor: ACCENT, padding: 12, borderRadius: 6,
             marginVertical: 10 },
  calloutFramed: { borderLeftColor: WARNING, backgroundColor: SURFACE_2 },
  calloutTitle: { color: INK_2, fontSize: 11.5, fontWeight: '700', letterSpacing: 0.8, marginBottom: 6,
                  textTransform: 'uppercase' },
  figure: { marginVertical: 12, backgroundColor: '#F3F0E8', borderRadius: 6, padding: 8 },
  formula: { fontFamily: 'Courier', color: INK, backgroundColor: SURFACE_2, padding: 10, marginVertical: 8,
             borderRadius: 6 },
  card: { backgroundColor: SURFACE, padding: 12, borderRadius: 6, marginVertical: 10 },
  rubric: { color: INK_MUTED, fontSize: 11, fontWeight: '700', letterSpacing: 0.8, marginBottom: 6 },
  link: { color: ACCENT, fontSize: 15, fontWeight: '700', marginVertical: 6 },
  small: { color: INK_MUTED, fontSize: 12.5, lineHeight: 18 },
  transcript: { marginTop: 10, borderTopWidth: 1, borderTopColor: BORDER, paddingTop: 10 },
  platform: { borderWidth: 1, borderColor: BORDER, borderRadius: 6, padding: 10, marginVertical: 10 },
});
