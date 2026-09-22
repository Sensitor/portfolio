/**
 * The visual atoms every screen is built from.
 *
 * The rule this file exists to enforce: **a figure is never rendered alone.**
 * A number by itself asks the reader to supply a scale they do not have — is
 * 1.93 a good profit factor? is 18% volatility high? A card pairs the figure
 * with a fill meter that places it in its range, a caption that says what it is
 * measured against, and where there is history, the shape of it.
 *
 * `Meter`, `Sparkline` and `Delta` are the three ways of supplying that scale.
 */

import React from 'react';
import { StyleSheet, Text, View, type ViewStyle } from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

import {
  ACCENT, BORDER, INK, INK_2, INK_FAINT, INK_MUTED, NEG, POS, RADIUS,
  RADIUS_PILL, RADIUS_SM, STATUS, STATUS_ICON, SURFACE, SURFACE_2, SURFACE_3,
} from '../theme';

/** What an undefined figure looks like. Never a zero. */
export const DASH = '—';

// ── Card ────────────────────────────────────────────────────────────────────

export function Card({ children, style }: {
  children: React.ReactNode;
  style?: ViewStyle;
}) {
  return <View style={[styles.card, style]}>{children}</View>;
}

// ── Meter ───────────────────────────────────────────────────────────────────

/**
 * A segmented fill bar.
 *
 * Segments rather than a smooth bar, matching the desktop: discrete blocks are
 * easier to compare across a row of cards than two continuous bars of slightly
 * different length.
 */
export function Meter({ fraction, color = ACCENT, segments = 16 }: {
  fraction: number | null | undefined;
  color?: string;
  segments?: number;
}) {
  if (fraction === null || fraction === undefined || Number.isNaN(fraction)) {
    return <View style={styles.meterSpacer} />;
  }
  const filled = Math.round(Math.max(0, Math.min(1, fraction)) * segments);
  return (
    <View style={styles.meter}>
      {Array.from({ length: segments }, (_, i) => (
        <View
          key={i}
          style={[styles.segment, { backgroundColor: i < filled ? color : 'rgba(154,168,191,0.13)' }]}
        />
      ))}
    </View>
  );
}

// ── Sparkline ───────────────────────────────────────────────────────────────

export function Sparkline({ values, color = ACCENT, width = 92, height = 28 }: {
  values: number[];
  color?: string;
  width?: number;
  height?: number;
}) {
  if (!values || values.length < 2) return null;

  const low = Math.min(...values);
  const high = Math.max(...values);
  const span = high - low || 1;

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width;
    const y = height - ((v - low) / span) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  return (
    <Svg width={width} height={height}>
      <Path d={`M ${points.join(' L ')}`} stroke={color} strokeWidth={1.6} fill="none" />
    </Svg>
  );
}

// ── Delta ───────────────────────────────────────────────────────────────────

export function Delta({ value, label, asPercent = true, higherIsBetter = true }: {
  value: number | null | undefined;
  label?: string;
  asPercent?: boolean;
  higherIsBetter?: boolean;
}) {
  if (value === null || value === undefined) return null;
  const good = higherIsBetter ? value >= 0 : value <= 0;
  const text = asPercent
    ? `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)}%`
    : `${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
  return (
    <Text style={[styles.delta, { color: good ? POS : NEG }]} numberOfLines={1}>
      {text}{label ? <Text style={styles.deltaLabel}>{`  ${label}`}</Text> : null}
    </Text>
  );
}

// ── Metric card ─────────────────────────────────────────────────────────────

/**
 * The atomic unit of every screen.
 *
 * `value` is already formatted — the caller passes what `format.ts` produced,
 * so an undefined figure arrives here as a dash and this component never has to
 * decide what `null` means.
 */
export function MetricCard({
  label, value, meter, meterColor, caption, spark, sparkColor, delta, deltaLabel,
  tone, compact,
}: {
  label: string;
  value: string;
  meter?: number | null;
  meterColor?: string;
  caption?: string;
  spark?: number[];
  sparkColor?: string;
  delta?: number | null;
  deltaLabel?: string;
  tone?: string;
  compact?: boolean;
}) {
  const accent = (tone && STATUS[tone]) || meterColor || ACCENT;
  return (
    <Card style={styles.metricCard}>
      <Text style={styles.metricLabel} numberOfLines={1}>{label.toUpperCase()}</Text>
      <Text style={[styles.metricValue, compact && styles.metricValueSm]} numberOfLines={1}>
        {value}
      </Text>
      {meter !== undefined ? <Meter fraction={meter} color={accent} /> : null}
      <View style={styles.metricFoot}>
        <View style={styles.metricFootLeft}>
          {delta !== undefined && delta !== null
            ? <Delta value={delta} label={deltaLabel} />
            : caption
              ? <Text style={styles.caption} numberOfLines={1}>{caption}</Text>
              : null}
        </View>
        {spark && spark.length > 1
          ? <Sparkline values={spark} color={sparkColor || accent} />
          : delta !== undefined && delta !== null && caption
            ? <Text style={styles.captionFaint} numberOfLines={1}>{caption}</Text>
            : null}
      </View>
    </Card>
  );
}

// ── Section header ──────────────────────────────────────────────────────────

export function Section({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title.toUpperCase()}</Text>
      {subtitle ? <Text style={styles.sectionSub} numberOfLines={2}>{subtitle}</Text> : null}
    </View>
  );
}

// ── Pill ────────────────────────────────────────────────────────────────────

export function Pill({ text, tone = 'neutral', icon = false }: {
  text: string; tone?: string; icon?: boolean;
}) {
  const color = STATUS[tone] ?? INK_2;
  return (
    <View style={[styles.pill, { backgroundColor: `${color}1F` }]}>
      <Text style={[styles.pillText, { color }]} numberOfLines={1}>
        {icon ? `${STATUS_ICON[tone] ?? ''} ` : ''}{text}
      </Text>
    </View>
  );
}

/**
 * The sample size behind a figure.
 *
 * Amber below the threshold rather than hidden. A table sorted by win rate
 * always puts a two-trade bucket on top; marking it is the difference between
 * a reader seeing a coincidence and reading a finding.
 */
export function SampleBadge({ n, reliable }: { n: number; reliable?: boolean }) {
  return <Pill text={`n = ${n}`} tone={reliable === false ? 'warning' : 'neutral'} />;
}

// ── Alert ───────────────────────────────────────────────────────────────────

export function Alert({ level, title, body, footnote }: {
  level: string; title: string; body: string; footnote?: string;
}) {
  const color = STATUS[level] ?? INK_2;
  return (
    <View style={[styles.alert, { borderLeftColor: color }]}>
      <Text style={[styles.alertIcon, { color }]}>{STATUS_ICON[level] ?? '●'}</Text>
      <View style={styles.alertBody}>
        <Text style={styles.alertTitle}>{title}</Text>
        <Text style={styles.alertText}>{body}</Text>
        {footnote ? <Text style={styles.alertFoot}>{footnote}</Text> : null}
      </View>
    </View>
  );
}

// ── Note ────────────────────────────────────────────────────────────────────

/** Where a caveat goes — the approximation, the threshold, the sample. */
export function Note({ text }: { text: string }) {
  return (
    <View style={styles.note}>
      <Text style={styles.noteIcon}>ⓘ</Text>
      <Text style={styles.noteText}>{text}</Text>
    </View>
  );
}

// ── Empty state ─────────────────────────────────────────────────────────────

export function Empty({ title, body, icon = '◎' }: {
  title: string; body: string; icon?: string;
}) {
  return (
    <Card style={styles.empty}>
      <Text style={styles.emptyIcon}>{icon}</Text>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyBody}>{body}</Text>
    </Card>
  );
}

// ── Screen header ───────────────────────────────────────────────────────────

export function ScreenHeader({ eyebrow, title, subtitle }: {
  eyebrow?: string; title: string; subtitle?: string;
}) {
  return (
    <View style={styles.header}>
      {eyebrow ? <Text style={styles.eyebrow}>{eyebrow.toUpperCase()}</Text> : null}
      <Text style={styles.title}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
  );
}

// ── Period pills ────────────────────────────────────────────────────────────

export function PeriodPicker({ periods, value, onChange }: {
  periods: string[]; value: string; onChange(next: string): void;
}) {
  return (
    <View style={styles.periodRow}>
      {periods.map((period) => {
        const active = period === value;
        return (
          <Text
            key={period}
            onPress={() => onChange(period)}
            suppressHighlighting
            style={[styles.period, active && styles.periodActive]}
          >
            {period}
          </Text>
        );
      })}
    </View>
  );
}

export const styles = StyleSheet.create({
  card: {
    backgroundColor: SURFACE,
    borderRadius: RADIUS,
    borderWidth: 1,
    borderColor: BORDER,
    padding: 14,
  },
  metricCard: { flex: 1, minHeight: 104, justifyContent: 'space-between' },
  metricLabel: {
    fontSize: 9.5, fontWeight: '700', letterSpacing: 1.1, color: INK_MUTED,
  },
  metricValue: {
    fontSize: 24, fontWeight: '800', color: INK, letterSpacing: -0.6, marginTop: 5,
  },
  metricValueSm: { fontSize: 18 },
  // The footer row is always emitted, even when empty: cards sit side by side
  // and one without a footer would be visibly shorter than its neighbours.
  metricFoot: {
    flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between',
    marginTop: 8, minHeight: 28,
  },
  metricFootLeft: { flex: 1, justifyContent: 'flex-end' },
  meter: { flexDirection: 'row', gap: 2, marginTop: 8, height: 4 },
  meterSpacer: { height: 12 },
  segment: { flex: 1, height: 4, borderRadius: 2 },
  caption: { fontSize: 10.5, color: INK_MUTED },
  captionFaint: { fontSize: 10.5, color: INK_FAINT },
  delta: { fontSize: 11.5, fontWeight: '700' },
  deltaLabel: { color: INK_FAINT, fontWeight: '500' },
  section: { marginTop: 26, marginBottom: 10 },
  sectionTitle: { fontSize: 11, fontWeight: '800', letterSpacing: 1.3, color: INK },
  sectionSub: { fontSize: 11.5, color: INK_MUTED, marginTop: 4, lineHeight: 16 },
  pill: {
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: RADIUS_PILL,
    alignSelf: 'flex-start',
  },
  pillText: { fontSize: 10, fontWeight: '700' },
  alert: {
    backgroundColor: SURFACE, borderRadius: RADIUS_SM, borderLeftWidth: 3,
    padding: 13, flexDirection: 'row', gap: 10, marginBottom: 8,
  },
  alertIcon: { fontSize: 11, lineHeight: 18 },
  alertBody: { flex: 1 },
  alertTitle: { fontSize: 13, fontWeight: '700', color: INK, marginBottom: 3 },
  alertText: { fontSize: 12.5, color: INK_2, lineHeight: 18 },
  alertFoot: { fontSize: 10.5, color: INK_FAINT, marginTop: 6, lineHeight: 15 },
  note: {
    flexDirection: 'row', gap: 8, backgroundColor: 'rgba(154,168,191,0.04)',
    borderWidth: 1, borderColor: BORDER, borderRadius: RADIUS_SM,
    padding: 11, marginTop: 10,
  },
  noteIcon: { fontSize: 11, color: INK_FAINT },
  noteText: { flex: 1, fontSize: 11, color: INK_MUTED, lineHeight: 16 },
  empty: { alignItems: 'center', paddingVertical: 38, paddingHorizontal: 22 },
  emptyIcon: { fontSize: 30, color: INK_FAINT, marginBottom: 10 },
  emptyTitle: { fontSize: 15, fontWeight: '700', color: INK, marginBottom: 5, textAlign: 'center' },
  emptyBody: { fontSize: 12.5, color: INK_MUTED, textAlign: 'center', lineHeight: 18 },
  header: { marginBottom: 14 },
  eyebrow: { fontSize: 9.5, fontWeight: '800', letterSpacing: 1.4, color: ACCENT },
  title: { fontSize: 26, fontWeight: '800', color: INK, letterSpacing: -0.7, marginTop: 5 },
  subtitle: { fontSize: 12.5, color: INK_MUTED, marginTop: 4, lineHeight: 18 },
  periodRow: { flexDirection: 'row', gap: 6, marginBottom: 4, flexWrap: 'wrap' },
  period: {
    paddingHorizontal: 13, paddingVertical: 6, borderRadius: RADIUS_PILL,
    backgroundColor: SURFACE_3, color: INK_MUTED, fontSize: 11.5, fontWeight: '700',
    overflow: 'hidden',
  },
  periodActive: { backgroundColor: ACCENT, color: '#FFFFFF' },
});
