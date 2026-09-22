/**
 * OVERVIEW — the hero screen.
 *
 * Within a few seconds: what the book made, how often it wins, what one trade
 * is worth, how deep the worst stretch went, and what crossed a threshold.
 *
 * Two figures carry a caveat rather than a value when the data does not support
 * one — profit factor with no losses, R with no stop — and both are rendered as
 * such rather than quietly becoming a number.
 */

import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { duration, money, percent, profitFactor, rCoverageNote, rMultiple }
  from '../../src/api/format';
import type { Period } from '../../src/api/types';
import { BreakdownBars, DailyBars, EquityChart } from '../../src/components/charts';
import {
  Alert, Card, DASH, Empty, MetricCard, Note, PeriodPicker, ScreenHeader, Section,
} from '../../src/components/primitives';
import { Screen } from '../../src/components/Screen';
import { useOverview } from '../../src/state/useOverview';
import { useSession } from '../../src/state/session';
import { ACCENT, CRITICAL, GOOD, INK_2, INK_MUTED, WARNING } from '../../src/theme';

export default function Overview() {
  const [period, setPeriod] = useState<Period>('ALL');
  const { data, loading, refreshing, offline, error, refresh } = useOverview(period);
  const { email } = useSession();

  const metrics = data?.metrics;
  const currency = data?.currency || '$';
  const equity = data?.equity ?? [];
  const curve = equity.map((p) => p.equity);

  return (
    <Screen loading={loading} refreshing={refreshing} offline={offline}
            error={error} onRefresh={refresh}>
      <ScreenHeader eyebrow="Sensitor Trading" title="Overview"
                    subtitle={email ?? undefined} />

      <PeriodPicker
        periods={data?.available_periods ?? ['ALL']}
        value={period}
        onChange={(next) => setPeriod(next as Period)}
      />

      {!metrics || metrics.n === 0 ? (
        <View style={styles.gap}>
          <Empty
            title="No trades yet"
            body="Add a trade in the journal, or import a history from MetaTrader 5, to unlock the analytics."
            icon="◌"
          />
        </View>
      ) : (
        <>
          <View style={styles.grid}>
            <MetricCard
              label="Net P&L"
              value={money(metrics.net_pnl, currency)}
              spark={curve}
              sparkColor={(metrics.net_pnl ?? 0) >= 0 ? GOOD : CRITICAL}
              caption={`${metrics.n} trades`}
            />
            <MetricCard
              label="Win rate"
              value={percent(metrics.win_rate)}
              meter={metrics.win_rate}
              // The colour follows expectancy, not the win rate: a 70% win
              // rate with a 0.3 payoff ratio loses money.
              meterColor={(metrics.expectancy ?? 0) > 0 ? GOOD : WARNING}
              caption={`${metrics.n_wins ?? 0}W / ${metrics.n_losses ?? 0}L`}
            />
          </View>

          <View style={styles.grid}>
            <MetricCard
              label="Profit factor"
              value={profitFactor(metrics.profit_factor)}
              meter={metrics.profit_factor === null ? null
                     : Math.min((metrics.profit_factor ?? 0) / 3, 1)}
              meterColor={(metrics.profit_factor ?? 0) >= 1.5 ? GOOD
                          : (metrics.profit_factor ?? 0) >= 1 ? WARNING : CRITICAL}
              caption={metrics.profit_factor === null ? 'no losing trades yet'
                       : `${money(metrics.gross_profit, currency, 0)} / ${money(Math.abs(metrics.gross_loss ?? 0), currency, 0)}`}
            />
            <MetricCard
              label="Expectancy"
              value={money(metrics.expectancy, currency)}
              meter={metrics.expectancy === null ? null
                     : Math.min(Math.max((metrics.expectancy ?? 0) / Math.max(Math.abs(metrics.avg_win ?? 1), Math.abs(metrics.avg_loss ?? 1)), -1), 1) * 0.5 + 0.5}
              meterColor={(metrics.expectancy ?? 0) >= 0 ? GOOD : CRITICAL}
              caption="per trade"
            />
          </View>

          <View style={styles.grid}>
            <MetricCard
              label="Average R"
              value={rMultiple(metrics.avg_r)}
              meter={metrics.avg_r === null ? null
                     : Math.min(Math.max((metrics.avg_r ?? 0), -1), 1) * 0.5 + 0.5}
              meterColor={(metrics.avg_r ?? 0) >= 0 ? GOOD : CRITICAL}
              // The coverage is on the card, not in a footnote: a 0.4R average
              // over a fifth of the book must never read as the whole picture.
              caption={`${percent(metrics.r_coverage, 0)} had a stop`}
            />
            <MetricCard
              label="Max drawdown"
              value={money(metrics.max_drawdown, currency)}
              caption={metrics.max_drawdown_r !== null
                       ? rMultiple(metrics.max_drawdown_r) : `${metrics.n} trades`}
              compact
            />
          </View>

          {rCoverageNote(metrics) ? <Note text={rCoverageNote(metrics)!} /> : null}

          {/* ── What crossed a threshold ─────────────────────────────── */}
          <Section title="Things to review"
                   subtitle={data?.findings.length ? undefined
                             : 'Nothing in this view is outside the range the product flags.'} />
          {data?.findings.length ? (
            <>
              {data.findings.map((finding) => (
                <Alert
                  key={finding.key}
                  level={finding.level}
                  title="A correlation in your data"
                  /* Rendered verbatim. Each sentence already names itself a
                     correlation and carries its sample size; paraphrasing one
                     into a verdict removes the only safeguard here. */
                  body={finding.en}
                  footnote={`n = ${finding.n} · Both groups are your own trades; this establishes no cause.`}
                />
              ))}
            </>
          ) : (
            <Alert level="good" title="Nothing crossed a threshold"
                   body="No behavioural comparison has two groups large enough to report. That is a statement about this data, not a verdict on your trading." />
          )}

          {/* ── Equity ───────────────────────────────────────────────── */}
          <Section title="Equity curve" subtitle={`${metrics.n} trades · ${data?.period}`} />
          <Card>
            <EquityChart points={equity} currency={currency} />
          </Card>

          {data?.daily?.length ? (
            <>
              <Section title="Daily P&L" />
              <Card>
                <DailyBars days={data.daily} />
                {/* "The most recent", not "the", and the difference is not
                    pedantry: the endpoint sends the last 90 trading days, and
                    this book has 151. The first version of this caption read
                    "90 trading days" and quietly described a third of the
                    window as the whole of it. */}
                <Text style={styles.footnote}>
                  The most recent {data.daily.length} trading days · after commission and swap
                </Text>
              </Card>
            </>
          ) : null}

          {/* ── By instrument ────────────────────────────────────────── */}
          {data?.by_symbol?.length ? (
            <>
              <Section title="By instrument" />
              <Card>
                <BreakdownBars rows={data.by_symbol} currency={currency} />
              </Card>
              <Note text="Each row carries the number of trades behind it. A bucket below the sample threshold is faded — its win rate is a coincidence, not a finding." />
            </>
          ) : null}

          {data?.open_positions ? (
            <Note text={`${data.open_positions} open position${data.open_positions > 1 ? 's' : ''} — excluded from every figure above, because a position with no exit has no result to measure.`} />
          ) : null}
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', gap: 10, marginTop: 10 },
  gap: { marginTop: 16 },
  footnote: { fontSize: 10, color: INK_MUTED, marginTop: 8 },
});
