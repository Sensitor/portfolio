/**
 * JOURNAL — the trades themselves.
 *
 * Every other tab summarises. This one shows the rows those summaries were
 * computed from, newest close first, so a figure that looks wrong can be
 * traced to the trades behind it.
 *
 * Two decisions worth stating:
 *
 * **The instrument filter is applied by the server, not by this screen.** A
 * page holds the most recent hundred trades; filtering that locally would silently
 * describe a slice of a slice. The chip vocabulary comes from a separate,
 * unfiltered request, so selecting EURUSD never removes EURUSD from the list of
 * things you can select.
 *
 * **A trade with no stop shows a dash where its R would be.** Not 0.00 — the
 * amount risked is unknown, and a column of zeros would drag an average that
 * the overview correctly refuses to compute.
 */

import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { DASH, duration, money, rMultiple, stamp } from '../../src/api/format';
import type { Period, Trade } from '../../src/api/types';
import {
  Card, Empty, PeriodPicker, Pill, ScreenHeader, Section,
} from '../../src/components/primitives';
import { Screen } from '../../src/components/Screen';
import { useResource } from '../../src/state/useResource';
import {
  BORDER, INK, INK_2, INK_FAINT, INK_MUTED, NEG, POS, RADIUS_PILL, SURFACE_3,
} from '../../src/theme';

const PAGE = 100;

export default function Journal() {
  const [period, setPeriod] = useState<Period>('ALL');
  const [symbol, setSymbol] = useState<string | null>(null);
  const [limit, setLimit] = useState(PAGE);

  // The vocabulary: every instrument traded in the window, whatever is
  // currently selected. Keyed on the period alone, so it survives a selection.
  const vocab = useResource(
    (client) => Promise.all([
      client.breakdown('symbol', { period }),
      client.periods(),
    ]),
    [period],
  );

  const page = useResource(
    (client) => client.trades({ period, symbol, limit }),
    [period, symbol, limit],
  );

  const symbols = vocab.data?.[0] ?? [];
  const periods = vocab.data?.[1] ?? ['ALL'];
  const trades = page.data?.trades ?? [];
  const total = page.data?.total ?? 0;
  // Each trade carries the currency its account is denominated in. `money()`
  // turns the code into a symbol, so the row shows the account's own currency
  // rather than a dollar sign assumed for everyone.
  const currency = trades[0]?.account_currency ?? 'USD';

  const choose = (next: string | null) => {
    setSymbol(next);
    setLimit(PAGE);        // a new filter starts at the top of its own list
  };

  return (
    <Screen loading={page.loading} refreshing={page.refreshing}
            offline={page.offline} error={page.error} onRefresh={page.refresh}>
      <ScreenHeader eyebrow="Sensitor Trading" title="Journal"
                    subtitle={total ? `${total} closed trade${total > 1 ? 's' : ''} in this window`
                                    : undefined} />

      <PeriodPicker periods={periods} value={period}
                    onChange={(next) => { setPeriod(next as Period); setLimit(PAGE); }} />

      {symbols.length > 1 ? (
        <View style={styles.chips}>
          <Chip label="All" active={symbol === null} onPress={() => choose(null)} />
          {symbols.map((row) => (
            <Chip
              key={row.key}
              label={row.label}
              count={row.n}
              active={symbol === row.key}
              onPress={() => choose(symbol === row.key ? null : row.key)}
            />
          ))}
        </View>
      ) : null}

      {trades.length === 0 ? (
        <View style={styles.gap}>
          <Empty
            title={symbol ? `No ${symbol} trades in this window` : 'No trades in this window'}
            body={symbol
              ? 'Clear the instrument filter, or widen the period.'
              : 'Widen the period, or import a history from MetaTrader 5 on the desktop app.'}
            icon="◌"
          />
        </View>
      ) : (
        <>
          <Section title="Closed trades"
                   subtitle={`Newest close first · showing ${trades.length} of ${total}`} />
          <Card style={styles.list}>
            {trades.map((trade, i) => (
              <TradeRow key={trade.id} trade={trade} currency={currency} first={i === 0} />
            ))}
          </Card>

          {trades.length < total ? (
            <Pressable style={styles.more} onPress={() => setLimit((n) => n + PAGE)}>
              <Text style={styles.moreText}>
                Show {Math.min(PAGE, total - trades.length)} more
              </Text>
            </Pressable>
          ) : (
            <Text style={styles.end}>
              That is every closed trade in this window.
            </Text>
          )}
        </>
      )}
    </Screen>
  );
}

// ── A row ───────────────────────────────────────────────────────────────────

function TradeRow({ trade, currency, first }: {
  trade: Trade; currency: string; first: boolean;
}) {
  const pnl = trade.pnl;
  const won = pnl !== null && pnl !== undefined && pnl > 0;
  const lost = pnl !== null && pnl !== undefined && pnl < 0;
  const tags = [...trade.setups, ...trade.mistakes];

  return (
    <View style={[styles.row, !first && styles.rowBorder]}>
      <View style={styles.rowMain}>
        <View style={styles.rowTop}>
          <Text style={styles.symbol} numberOfLines={1}>{trade.symbol}</Text>
          {/* The arrow carries the direction; the colour does not. Green and
              red mean "made money" and "lost money" everywhere else in this
              app, and a red SHORT beside a green P&L asks the reader to hold
              two meanings for one colour in the same row. */}
          <Text style={styles.direction}>
            {trade.direction === 'long' ? '▲ LONG' : '▼ SHORT'}
          </Text>
        </View>
        <Text style={styles.meta} numberOfLines={1}>
          {stamp(trade.closed_at)}
          {trade.duration_minutes !== null ? ` · ${duration(trade.duration_minutes)}` : ''}
          {trade.session ? ` · ${trade.session}` : ''}
        </Text>
        {tags.length ? (
          <View style={styles.tags}>
            {trade.setups.map((setup) => (
              <Pill key={`s-${setup}`} text={setup} tone="neutral" />
            ))}
            {/* A recorded mistake is amber wherever it appears, on this screen
                and on psychology, so the two cannot be read as different things. */}
            {trade.mistakes.map((mistake) => (
              <Pill key={`m-${mistake}`} text={mistake} tone="warning" />
            ))}
          </View>
        ) : null}
      </View>

      <View style={styles.rowFigures}>
        <Text style={[styles.pnl, { color: won ? POS : lost ? NEG : INK_2 }]}
              numberOfLines={1}>
          {money(pnl, currency, 0)}
        </Text>
        {/* A dash here means the trade had no stop, so there is no amount
            risked to express the result as a multiple of. */}
        <Text style={styles.r} numberOfLines={1}>
          {trade.r_multiple === null ? `${DASH} no stop` : rMultiple(trade.r_multiple, 1)}
        </Text>
      </View>
    </View>
  );
}

function Chip({ label, count, active, onPress }: {
  label: string; count?: number; active: boolean; onPress(): void;
}) {
  return (
    <Pressable onPress={onPress} style={[styles.chip, active && styles.chipActive]}>
      <Text style={[styles.chipText, active && styles.chipTextActive]} numberOfLines={1}>
        {label}{count !== undefined ? <Text style={styles.chipCount}>{`  ${count}`}</Text> : null}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  gap: { marginTop: 16 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  chip: {
    paddingHorizontal: 11, paddingVertical: 5, borderRadius: RADIUS_PILL,
    backgroundColor: SURFACE_3,
  },
  chipActive: { backgroundColor: 'rgba(57,135,229,0.22)' },
  chipText: { fontSize: 11, fontWeight: '700', color: INK_MUTED },
  chipTextActive: { color: INK },
  chipCount: { color: INK_FAINT, fontWeight: '500' },
  list: { paddingVertical: 2 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 11 },
  rowBorder: { borderTopWidth: 1, borderTopColor: BORDER },
  rowMain: { flex: 1 },
  rowTop: { flexDirection: 'row', alignItems: 'baseline', gap: 8 },
  symbol: { fontSize: 14, fontWeight: '700', color: INK },
  direction: { fontSize: 9.5, fontWeight: '800', letterSpacing: 0.6, color: INK_MUTED },
  meta: { fontSize: 10.5, color: INK_MUTED, marginTop: 3 },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 6 },
  rowFigures: { alignItems: 'flex-end', minWidth: 88 },
  pnl: { fontSize: 15, fontWeight: '800', letterSpacing: -0.3 },
  r: { fontSize: 10.5, color: INK_MUTED, marginTop: 3 },
  more: {
    marginTop: 12, paddingVertical: 12, borderRadius: 10, borderWidth: 1,
    borderColor: BORDER, alignItems: 'center',
  },
  moreText: { fontSize: 12, fontWeight: '700', color: INK_2 },
  end: { marginTop: 12, fontSize: 11, color: INK_FAINT, textAlign: 'center' },
});
