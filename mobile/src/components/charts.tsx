/**
 * Charts, drawn with `react-native-svg` so one implementation runs on the
 * device and in the browser preview.
 *
 * Two things carried over from the desktop charts, because they were learned
 * the hard way there:
 *
 * **The axis gets headroom per side, not a symmetric range.** A book where one
 * instrument lost $51 against another's $243 gain drawn on −330…+330 spends
 * half its width on emptiness and shrinks every bar that matters.
 *
 * **A bucket below the sample threshold is faded *and* carries its count.**
 * Opacity alone does not survive a colourblind reader; the number does.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Line, Path, Rect } from 'react-native-svg';

import type { BreakdownRow, CurvePoint } from '../api/types';
import { money } from '../api/format';
import { ACCENT, BORDER, GRID, INK_2, INK_FAINT, INK_MUTED, NEG, POS } from '../theme';

// ── Equity curve ────────────────────────────────────────────────────────────

export function EquityChart({ points, height = 170, currency = '$' }: {
  points: CurvePoint[];
  height?: number;
  currency?: string;
}) {
  const [width, setWidth] = React.useState(0);
  if (!points || points.length < 2) return null;

  const values = points.map((p) => p.equity);
  const low = Math.min(...values, 0);
  const high = Math.max(...values, 0);
  const span = high - low || 1;
  const finalValue = values[values.length - 1] ?? 0;
  const colour = finalValue >= 0 ? POS : NEG;

  const x = (i: number) => (i / (values.length - 1)) * width;
  const y = (v: number) => height - ((v - low) / span) * height;

  const line = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  const area = `M ${line.join(' L ')} L ${width},${y(low)} L 0,${y(low)} Z`;

  return (
    <View onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
      {width > 0 ? (
        <Svg width={width} height={height}>
          {/* The zero line, where it falls inside the range. A curve that never
              went negative should not imply it did. */}
          {low < 0 && high > 0 ? (
            <Line x1={0} y1={y(0)} x2={width} y2={y(0)}
                  stroke={BORDER} strokeWidth={1} />
          ) : null}
          <Path d={area} fill={colour} fillOpacity={0.10} />
          <Path d={`M ${line.join(' L ')}`} stroke={colour} strokeWidth={2.2} fill="none" />
        </Svg>
      ) : <View style={{ height }} />}
      <View style={styles.axis}>
        <Text style={styles.axisLabel}>{money(low, currency, 0)}</Text>
        <Text style={styles.axisLabel}>{money(high, currency, 0)}</Text>
      </View>
    </View>
  );
}

// ── Daily bars ──────────────────────────────────────────────────────────────

export function DailyBars({ days, height = 92 }: {
  days: { date: string; pnl: number; n: number }[];
  height?: number;
}) {
  const [width, setWidth] = React.useState(0);
  if (!days || days.length === 0) return null;

  const span = Math.max(...days.map((d) => Math.abs(d.pnl))) || 1;
  const zero = height / 2;
  const slot = width / days.length;
  const barWidth = Math.max(1.5, Math.min(8, slot * 0.62));

  return (
    <View onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
      {width > 0 ? (
        <Svg width={width} height={height}>
          <Line x1={0} y1={zero} x2={width} y2={zero} stroke={BORDER} strokeWidth={1} />
          {days.map((day, i) => {
            const magnitude = (Math.abs(day.pnl) / span) * (height / 2 - 2);
            return (
              <Rect
                key={day.date}
                x={i * slot + (slot - barWidth) / 2}
                y={day.pnl >= 0 ? zero - magnitude : zero}
                width={barWidth}
                height={Math.max(1, magnitude)}
                rx={1.5}
                fill={day.pnl >= 0 ? POS : NEG}
              />
            );
          })}
        </Svg>
      ) : <View style={{ height }} />}
    </View>
  );
}

// ── Breakdown bars ──────────────────────────────────────────────────────────

export function BreakdownBars({ rows, currency = '$', metric = 'net_pnl' }: {
  rows: BreakdownRow[];
  currency?: string;
  metric?: 'net_pnl' | 'expectancy';
}) {
  const usable = rows.filter((r) => r[metric] !== null && r[metric] !== undefined);
  if (usable.length === 0) return null;

  const values = usable.map((r) => r[metric] as number);
  const low = Math.min(...values, 0);
  const high = Math.max(...values, 0);
  // Headroom per side, not a symmetric range — see the module docstring.
  const negativeSpan = Math.abs(low) || 1;
  const positiveSpan = high || 1;
  const total = negativeSpan + positiveSpan;
  const zeroAt = (negativeSpan / total) * 100;

  return (
    <View style={styles.breakdown}>
      {usable.map((row) => {
        const value = row[metric] as number;
        const share = (Math.abs(value) / total) * 100;
        const positive = value >= 0;
        return (
          <View key={row.key} style={styles.breakdownRow}>
            {/* The count is a sibling, not a nested span. Nested, it shared
                the label's single line and was the part that got truncated —
                "Break of Structure (…" — which drops the one number that says
                whether the bar beside it means anything. The name may be cut;
                the sample size may not. */}
            <View style={styles.breakdownLabelBox}>
              <Text style={[styles.breakdownLabel, !row.reliable && styles.dim]}
                    numberOfLines={1}>
                {row.label}
              </Text>
              <Text style={styles.breakdownCount}>{`  ${row.n}`}</Text>
            </View>
            <View style={styles.track}>
              <View style={[styles.zeroLine, { left: `${zeroAt}%` }]} />
              <View
                style={[
                  styles.bar,
                  {
                    left: positive ? `${zeroAt}%` : `${zeroAt - share}%`,
                    width: `${Math.max(share, 0.6)}%`,
                    backgroundColor: positive ? POS : NEG,
                    // Faded *and* counted: opacity alone does not survive a
                    // colourblind reader, so the label carries `n` as well.
                    opacity: row.reliable ? 1 : 0.42,
                  },
                ]}
              />
            </View>
            <Text style={[styles.breakdownValue, { color: positive ? POS : NEG }]}
                  numberOfLines={1}>
              {money(value, currency, 0)}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  axis: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  axisLabel: { fontSize: 9.5, color: INK_FAINT },
  breakdown: { gap: 9, marginTop: 4 },
  breakdownRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  breakdownLabelBox: {
    width: 116, flexDirection: 'row', alignItems: 'baseline',
  },
  breakdownLabel: { flexShrink: 1, fontSize: 11, color: INK_2 },
  breakdownCount: { color: INK_FAINT, fontSize: 10 },
  dim: { color: INK_MUTED },
  track: { flex: 1, height: 11, justifyContent: 'center' },
  zeroLine: {
    position: 'absolute', top: 0, bottom: 0, width: 1,
    backgroundColor: 'rgba(154,168,191,0.22)',
  },
  bar: { position: 'absolute', height: 11, borderRadius: 3 },
  breakdownValue: { width: 62, fontSize: 10.5, fontWeight: '600', textAlign: 'right' },
});
