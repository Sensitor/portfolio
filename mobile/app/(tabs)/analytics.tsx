/**
 * ANALYTICS — where the money came from.
 *
 * One question, asked eleven ways: which group of trades carried the book?
 * The server groups; this screen ranks nothing it was not given already.
 *
 * The rule this screen exists to respect: **a table sorted by win rate always
 * puts a two-trade bucket on top.** Every row carries `n` and the server's
 * `reliable` flag, small buckets are faded *and* counted, and the screen never
 * promotes one to "your best setup" — that is how a journal teaches someone the
 * wrong lesson and then watches them size up on it.
 */

import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { money, percent, profitFactor, rMultiple } from '../../src/api/format';
import type { BreakdownRow, Dimension, Period } from '../../src/api/types';
import { BreakdownBars } from '../../src/components/charts';
import {
  Card, Empty, Meter, Note, PeriodPicker, ScreenHeader, Section,
} from '../../src/components/primitives';
import { Screen } from '../../src/components/Screen';
import { useOverview } from '../../src/state/useOverview';
import { useResource } from '../../src/state/useResource';
import {
  BORDER, GOOD, INK, INK_2, INK_FAINT, INK_MUTED, NEG, POS, RADIUS_PILL,
  SURFACE_3, WARNING,
} from '../../src/theme';

const DIMENSIONS: { key: Dimension; label: string; blurb: string }[] = [
  { key: 'symbol', label: 'Instrument', blurb: 'What you trade.' },
  { key: 'setup', label: 'Setup', blurb: 'The setups you tagged. Untagged trades are not in this table.' },
  { key: 'session', label: 'Session', blurb: 'Asian, London, New York — by the broker clock, offset-corrected at import.' },
  { key: 'weekday', label: 'Weekday', blurb: 'The day of the week the trade was opened.' },
  { key: 'hour', label: 'Hour', blurb: 'The hour the trade was opened. Thin buckets are the norm here.' },
  { key: 'direction', label: 'Direction', blurb: 'Long against short.' },
  { key: 'timeframe', label: 'Timeframe', blurb: 'The timeframe you recorded. Untagged trades are not in this table.' },
  { key: 'risk_band', label: 'Risk band', blurb: 'Grouped by how much was risked, over the trades that had a stop.' },
];

export default function Analytics() {
  const [period, setPeriod] = useState<Period>('ALL');
  const [dimension, setDimension] = useState<Dimension>('symbol');

  const overview = useOverview(period);
  const rows = useResource(
    (client) => client.breakdown(dimension, { period }),
    [period, dimension],
  );

  const currency = overview.data?.currency || '$';
  const data = rows.data ?? [];
  const chosen = DIMENSIONS.find((d) => d.key === dimension)!;
  const thin = data.filter((r) => !r.reliable).length;

  return (
    <Screen loading={rows.loading} refreshing={rows.refreshing}
            offline={rows.offline} error={rows.error} onRefresh={rows.refresh}>
      <ScreenHeader eyebrow="Sensitor Trading" title="Analytics"
                    subtitle="Performance grouped by anything the journal records." />

      <PeriodPicker periods={overview.data?.available_periods ?? ['ALL']} value={period}
                    onChange={(next) => setPeriod(next as Period)} />

      <ScrollView horizontal showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.dims}>
        {DIMENSIONS.map((d) => (
          <Pressable key={d.key} onPress={() => setDimension(d.key)}
                     style={[styles.dim, d.key === dimension && styles.dimActive]}>
            <Text style={[styles.dimText, d.key === dimension && styles.dimTextActive]}>
              {d.label}
            </Text>
          </Pressable>
        ))}
      </ScrollView>

      {data.length === 0 ? (
        <View style={styles.gap}>
          <Empty
            title={`Nothing grouped by ${chosen.label.toLowerCase()}`}
            body={`${chosen.blurb} No trade in this window carries one, so there is nothing to compare.`}
            icon="◌"
          />
        </View>
      ) : (
        <>
          <Section title={`Net P&L by ${chosen.label.toLowerCase()}`}
                   subtitle={chosen.blurb} />
          <Card>
            <BreakdownBars rows={data} currency={currency} />
          </Card>

          <Section title="Every group"
                   subtitle="Sorted as the engine returned it. The number beside each name is how many trades it rests on." />
          <Card style={styles.table}>
            {data.map((row, i) => (
              <GroupRow key={row.key} row={row} currency={currency} first={i === 0} />
            ))}
          </Card>

          {thin > 0 ? (
            <Note text={`${thin} of ${data.length} group${data.length > 1 ? 's' : ''} ${thin > 1 ? 'are' : 'is'} below the sample threshold — faded above, and marked "thin" below. A win rate over four trades is a coincidence, not a finding, and this screen will not rank one as your best.`} />
          ) : (
            <Note text="Every group here clears the sample threshold. That makes them comparable; it does not make them predictive." />
          )}
        </>
      )}
    </Screen>
  );
}

// ── A group ─────────────────────────────────────────────────────────────────

function GroupRow({ row, currency, first }: {
  row: BreakdownRow; currency: string; first: boolean;
}) {
  const net = row.net_pnl ?? 0;
  return (
    <View style={[styles.row, !first && styles.rowBorder]}>
      <View style={styles.rowHead}>
        <Text style={[styles.label, !row.reliable && styles.labelThin]} numberOfLines={1}>
          {row.label}
        </Text>
        <View style={styles.rowHeadRight}>
          {!row.reliable ? <Text style={styles.thin}>thin</Text> : null}
          <Text style={styles.n}>{`n = ${row.n}`}</Text>
          <Text style={[styles.net, { color: net >= 0 ? POS : NEG }]}>
            {money(row.net_pnl, currency, 0)}
          </Text>
        </View>
      </View>

      <Meter
        fraction={row.win_rate}
        // The colour follows expectancy, not the win rate: a 70% win rate with
        // a 0.3 payoff ratio loses money, and colouring it green would say the
        // opposite of what the row shows.
        color={(row.expectancy ?? 0) > 0 ? GOOD : WARNING}
        segments={20}
      />

      <View style={styles.figures}>
        <Figure label="win rate" value={percent(row.win_rate, 0)} />
        <Figure label="expectancy" value={money(row.expectancy, currency, 0)} />
        <Figure label="avg R" value={rMultiple(row.avg_r, 2)} />
        <Figure label="PF" value={profitFactor(row.profit_factor)} />
      </View>
    </View>
  );
}

function Figure({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.figure}>
      <Text style={styles.figureValue} numberOfLines={1}>{value}</Text>
      <Text style={styles.figureLabel} numberOfLines={1}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  gap: { marginTop: 16 },
  dims: { gap: 6, paddingVertical: 8, paddingRight: 16 },
  dim: {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: RADIUS_PILL,
    backgroundColor: SURFACE_3,
  },
  dimActive: { backgroundColor: 'rgba(57,135,229,0.22)' },
  dimText: { fontSize: 11.5, fontWeight: '700', color: INK_MUTED },
  dimTextActive: { color: INK },
  table: { paddingVertical: 2 },
  row: { paddingVertical: 12 },
  rowBorder: { borderTopWidth: 1, borderTopColor: BORDER },
  rowHead: {
    flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between',
    gap: 8, marginBottom: 8,
  },
  rowHeadRight: { flexDirection: 'row', alignItems: 'baseline', gap: 8 },
  label: { flex: 1, fontSize: 13, fontWeight: '700', color: INK },
  labelThin: { color: INK_2 },
  thin: {
    fontSize: 9, fontWeight: '800', letterSpacing: 0.5, color: WARNING,
  },
  n: { fontSize: 10, color: INK_FAINT },
  net: { fontSize: 13, fontWeight: '800', minWidth: 62, textAlign: 'right' },
  figures: { flexDirection: 'row', marginTop: 10, gap: 6 },
  figure: { flex: 1 },
  figureValue: { fontSize: 12.5, fontWeight: '700', color: INK_2 },
  figureLabel: {
    fontSize: 8.5, fontWeight: '700', letterSpacing: 0.7, color: INK_FAINT,
    marginTop: 2, textTransform: 'uppercase',
  },
});
