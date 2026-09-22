/**
 * RISK — how the book was bet, not what it returned.
 *
 * Five questions, in the order they matter: how much is risked per trade, how
 * steady that is, whether the stops held, how much was exposed at once, and
 * whether the worst losing run was actually unusual.
 *
 * Three things this screen is careful about:
 *
 * **Stop discipline is measured on gross R, and says so.** Commission alone
 * pushes a trade stopped at exactly −1R past −1R net; judged that way, a
 * disciplined trader looks like one whose stops never hold.
 *
 * **The expected losing run is an approximation, and says so.** It assumes
 * independent trades, which a trader's own state makes false. It is here
 * because the usual reason someone abandons a working system is a run that was
 * statistically unremarkable — an order of magnitude is enough for that.
 *
 * **A section the engine declined to compute says why.** `{}` back from the
 * server means the sample was too small, and printing zeros in its place would
 * describe a book nobody traded.
 */

import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  DASH, dayOnly, money, outOf, percent, rMultiple, ratio, stamp, times,
} from '../../src/api/format';
import type { Period } from '../../src/api/types';
import {
  Alert, Card, Empty, MetricCard, Note, PeriodPicker, ScreenHeader, Section,
} from '../../src/components/primitives';
import { Screen } from '../../src/components/Screen';
import { useOverview } from '../../src/state/useOverview';
import { useResource } from '../../src/state/useResource';
import {
  CRITICAL, GOOD, INK_2, INK_FAINT, INK_MUTED, WARNING,
} from '../../src/theme';

export default function Risk() {
  const [period, setPeriod] = useState<Period>('ALL');
  const overview = useOverview(period);
  const summary = useResource((client) => client.risk({ period }), [period]);

  const currency = overview.data?.currency || '$';
  const profile = summary.data?.profile;
  const stops = summary.data?.stops;
  const exposure = summary.data?.exposure;
  const activity = summary.data?.activity;
  const streaks = summary.data?.streaks;
  const drift = summary.data?.drift;

  const hasStops = !!profile?.n_with_stop;
  const consistency = profile?.consistency ?? null;

  return (
    <Screen loading={summary.loading} refreshing={summary.refreshing}
            offline={summary.offline} error={summary.error} onRefresh={summary.refresh}>
      <ScreenHeader eyebrow="Sensitor Trading" title="Risk"
                    subtitle="How the book was bet, before any of it worked or did not." />

      <PeriodPicker periods={overview.data?.available_periods ?? ['ALL']} value={period}
                    onChange={(next) => setPeriod(next as Period)} />

      {!profile || profile.n === 0 ? (
        <View style={styles.gap}>
          <Empty title="No closed trades in this window"
                 body="Risk is measured on trades that finished. Widen the period, or close a position."
                 icon="◌" />
        </View>
      ) : !hasStops ? (
        <View style={styles.gap}>
          <Empty
            title="No trade in this window recorded a stop"
            body={`All ${profile.n} of them are here, but without a stop there is no amount risked — and every figure on this screen is a share of it.`}
            icon="◌"
          />
        </View>
      ) : (
        <>
          {/* ── Sizing ─────────────────────────────────────────────── */}
          <Section title="Risk per trade"
                   subtitle={`Over the ${profile.n_with_stop} of ${profile.n} trades that had a stop.`} />

          <View style={styles.grid}>
            <MetricCard
              label="Median risk"
              value={money(profile.median_risk, currency, 0)}
              caption={`mean ${money(profile.mean_risk, currency, 0)}`}
            />
            {/* The meter shows the same quantity as the number above it. An
                earlier version filled it with `1 - cv`, so the card read 39%
                over a bar filled to 61% — two different answers to one
                question. Here the bar is the spread and the colour says
                whether that spread is tight. */}
            <MetricCard
              label="Risk spread"
              value={consistency === null ? DASH : percent(consistency, 0)}
              meter={consistency === null ? null : Math.min(consistency, 1)}
              meterColor={consistency !== null && consistency <= 0.35 ? GOOD : WARNING}
              caption={consistency === null
                ? 'needs 8 trades with a stop'
                : 'lower is steadier'}
            />
          </View>

          <View style={styles.grid}>
            <MetricCard
              label="Largest vs median"
              value={times(profile.largest_vs_median, 1)}
              meter={profile.largest_vs_median === null || profile.largest_vs_median === undefined
                ? null : Math.min((profile.largest_vs_median ?? 1) / 5, 1)}
              meterColor={(profile.largest_vs_median ?? 1) <= 2 ? GOOD
                          : (profile.largest_vs_median ?? 1) <= 3 ? WARNING : CRITICAL}
              caption={`${money(profile.max_risk, currency, 0)} at most`}
              compact
            />
            {/* Stated as the coverage rather than the count, for the same
                reason: the bar was drawing 93% under a headline of 65. */}
            <MetricCard
              label="Stop coverage"
              value={percent(profile.coverage, 0)}
              meter={profile.coverage === null || profile.coverage === undefined
                ? null : profile.coverage}
              meterColor={(profile.coverage ?? 0) >= 0.9 ? GOOD : WARNING}
              caption={`${profile.no_stop_count ?? 0} of ${profile.n} had none`}
            />
          </View>

          {(profile.coverage ?? 1) < 1 ? (
            <Note text={`${profile.no_stop_count} trade${(profile.no_stop_count ?? 0) > 1 ? 's' : ''} in this window had no stop. They are counted in the book and absent from every figure on this screen — not because they went well, but because there is no amount risked to compare them against.`} />
          ) : null}

          {/* ── Drift ──────────────────────────────────────────────── */}
          {drift && drift.direction ? (
            <>
              <Section title="Has that been drifting?"
                       subtitle={`Rolling median over ${drift.n_points} windows, ${dayOnly(drift.from)} to ${dayOnly(drift.to)}.`} />
              <Alert
                level={drift.direction === 'stable' ? 'good'
                       : drift.direction === 'up' ? 'warning' : 'neutral'}
                title={drift.direction === 'stable' ? 'Risk per trade has held steady'
                       : drift.direction === 'up' ? 'Risk per trade has been rising'
                       : 'Risk per trade has been falling'}
                body={`The rolling median moved from ${money(drift.start_median, currency, 0)} to ${money(drift.end_median, currency, 0)}, a change of ${percent(drift.change, 0)}. The threshold for calling it a direction rather than noise is ±15%.`}
                footnote="A rising line is not a mistake by itself — an account that grew should risk more. It is a mistake when the account did not."
              />
            </>
          ) : null}

          {/* ── Stops ──────────────────────────────────────────────── */}
          <Section title="Did the stops hold?"
                   subtitle="A loss worse than −1R means the stop did not do its job. Which of the four reasons it was is something only you know." />

          {!stops?.n_losses ? (
            <Card>
              <Text style={styles.plain}>
                No losing trade in this window carries an R multiple, so there is
                nothing to measure a stop against.
              </Text>
            </Card>
          ) : (
            <>
              <View style={styles.grid}>
                <MetricCard
                  label="Past the stop"
                  value={outOf(stops.n_beyond_stop, stops.n_losses)}
                  meter={stops.share_beyond_stop}
                  meterColor={(stops.share_beyond_stop ?? 0) <= 0.05 ? GOOD
                              : (stops.share_beyond_stop ?? 0) <= 0.2 ? WARNING : CRITICAL}
                  caption="losses worse than −1R"
                  compact
                />
                <MetricCard
                  label="Worst loss"
                  value={rMultiple(stops.worst_loss_r, 1)}
                  caption={`average ${rMultiple(stops.avg_loss_r, 2)}`}
                  compact
                />
              </View>
              <Note text={`Measured on gross R — price movement before costs. A trade stopped at exactly −1R lands past −1R net on commission alone, and judging discipline that way would fail every trader who pays one. The 5% tolerance above absorbs ordinary slippage.`} />
            </>
          )}

          {/* ── Exposure ───────────────────────────────────────────── */}
          {exposure?.max_concurrent ? (
            <>
              <Section title="How much was open at once"
                       subtitle="Per-trade risk understates the real one: five trades each risking 1%, taken together on correlated instruments, is not five separate 1% bets." />
              <View style={styles.grid}>
                <MetricCard
                  label="Most at once"
                  value={`${exposure.max_concurrent}`}
                  caption={stamp(exposure.max_concurrent_at)}
                  compact
                />
                <MetricCard
                  label="Risked together"
                  value={money(exposure.max_simultaneous_risk, currency, 0)}
                  caption={profile.median_risk
                    ? `${times((exposure.max_simultaneous_risk ?? 0) / profile.median_risk, 1)} the median trade`
                    : undefined}
                  compact
                />
              </View>
              {exposure.max_concurrent_symbols?.length ? (
                <Note text={`At that moment: ${exposure.max_concurrent_symbols.join(', ')}.`} />
              ) : null}
            </>
          ) : null}

          {/* ── Activity ───────────────────────────────────────────── */}
          {activity?.n_days ? (
            <>
              <Section title="Activity"
                       subtitle={`${activity.n_days} trading day${activity.n_days > 1 ? 's' : ''} in this window.`} />
              <View style={styles.grid}>
                <MetricCard
                  label="Trades per day"
                  value={ratio(activity.median_per_day, 1)}
                  caption={`mean ${ratio(activity.mean_per_day, 1)}`}
                  compact
                />
                <MetricCard
                  label="Busiest day"
                  value={`${activity.max_per_day}`}
                  caption={dayOnly(activity.busiest_day)}
                  compact
                />
              </View>
            </>
          ) : null}

          {/* ── Losing runs ────────────────────────────────────────── */}
          {streaks?.observed_max_losses !== undefined ? (
            <>
              <Section title="Was that losing run unusual?" />
              <Alert
                level={streaks.unusual ? 'warning' : 'good'}
                title={streaks.unusual
                  ? `${streaks.observed_max_losses} losses in a row is longer than this win rate predicts`
                  : `${streaks.observed_max_losses} losses in a row is within what this win rate predicts`}
                body={`At a ${percent(streaks.win_rate, 0)} win rate over ${streaks.n} trades, the longest losing run to expect by chance alone is about ${streaks.expected_max_losses}. The worst observed was ${streaks.observed_max_losses}.`}
                footnote="The estimate assumes trades are independent. They are not — your state carries from one to the next — so read it as an order of magnitude, not a threshold."
              />
            </>
          ) : null}

          <Text style={styles.foot}>
            Every figure on this screen is measured over the {profile.n_with_stop} trades
            in this window that recorded a stop.
          </Text>
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  gap: { marginTop: 16 },
  grid: { flexDirection: 'row', gap: 10, marginTop: 10 },
  plain: { fontSize: 12.5, color: INK_2, lineHeight: 18 },
  foot: {
    marginTop: 22, fontSize: 10.5, color: INK_FAINT, lineHeight: 15,
    textAlign: 'center',
  },
});
