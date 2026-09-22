/**
 * PSYCHOLOGY — the most easily misread screen in the product.
 *
 * Everything here compares two groups of your own trades. None of it
 * establishes cause, none of it is a diagnosis, and the screen is built so that
 * it cannot be read as either:
 *
 * **The findings are rendered verbatim.** The engine phrases them, in both
 * languages, and each sentence names itself a correlation and carries its
 * sample size. Paraphrasing one into a verdict removes the only safeguard.
 *
 * **Both sample sizes travel with every comparison.** "You lose more when
 * anxious" over six trades against four is not a finding, and a reader who
 * cannot see the six and the four has no way to know that.
 *
 * **A comparison the engine withheld says why.** Below five trades a side it
 * returns nothing, and this screen says "too few", never a zero.
 */

import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { money, percent, ratio, rMultiple, times } from '../../src/api/format';
import type { Comparison, Period, StreakBehaviour } from '../../src/api/types';
import {
  Alert, Card, Empty, Note, PeriodPicker, Pill, ScreenHeader, Section,
} from '../../src/components/primitives';
import { Screen } from '../../src/components/Screen';
import { useOverview } from '../../src/state/useOverview';
import { useResource } from '../../src/state/useResource';
import {
  BORDER, INK, INK_2, INK_FAINT, INK_MUTED, NEG, POS, WARNING,
} from '../../src/theme';

/** The engine's own floor. Stated on screen rather than implied by a blank. */
const MIN_GROUP = 5;

export default function Psychology() {
  const [period, setPeriod] = useState<Period>('ALL');
  const overview = useOverview(period);
  const psych = useResource((client) => client.psychology({ period }), [period]);

  const currency = overview.data?.currency || '$';
  const findings = overview.data?.findings ?? [];
  const data = psych.data;

  const nothing = !data || (
    data.emotions_before.length === 0
    && data.discipline.length === 0
    && data.mistakes.length === 0
    && data.mistake_frequency.length === 0
    && !data.after_losses.n_after
    && !data.after_wins.n_after
    && !data.activity_after_losses.n_bad_start_days
  );

  return (
    <Screen loading={psych.loading} refreshing={psych.refreshing}
            offline={psych.offline} error={psych.error} onRefresh={psych.refresh}>
      <ScreenHeader eyebrow="Sensitor Trading" title="Behaviour"
                    subtitle="Comparisons between groups of your own trades. Nothing here is a diagnosis." />

      <PeriodPicker periods={overview.data?.available_periods ?? ['ALL']} value={period}
                    onChange={(next) => setPeriod(next as Period)} />

      <Note text={`Every comparison on this screen is a correlation. Both groups are your own trades, both sample sizes are shown, and a group smaller than ${MIN_GROUP} trades is withheld rather than reported. None of it establishes cause.`} />

      {/* ── What crossed a threshold ─────────────────────────────── */}
      <Section title="Findings"
               subtitle={findings.length
                 ? 'Phrased by the engine and shown word for word.'
                 : undefined} />
      {findings.length ? (
        findings.map((finding) => (
          <Alert
            key={finding.key}
            level={finding.level}
            title="A correlation in your data"
            body={finding.en}
            footnote={`n = ${finding.n} · Both groups are your own trades; this establishes no cause.`}
          />
        ))
      ) : (
        <Alert level="good" title="Nothing crossed a threshold"
               body="No comparison in this window has two groups large enough to report. That is a statement about this data, not a verdict on your trading." />
      )}

      {nothing ? (
        <View style={styles.gap}>
          <Empty
            title="Nothing else to compare yet"
            body={`This screen reads the emotions, discipline ratings and mistakes you record against a trade, plus what you did after a run of wins or losses. Each comparison needs at least ${MIN_GROUP} trades on both sides.`}
            icon="◌"
          />
        </View>
      ) : (
        <>
          {/* ── After a run ────────────────────────────────────── */}
          <Section title="After a run"
                   subtitle="Whether the size of the next bet changed. Median rather than mean, so one outsized trade does not bend the comparison." />

          <StreakCard
            title={`After ${data!.after_losses.streak_length ?? 2} losses in a row`}
            behaviour={data!.after_losses}
            currency={currency}
            /* Amber only here. Sizing up after losses is the pattern worth
               flagging; the same ratio after wins is an ordinary thing a
               trader does on purpose, and colouring it alarms without cause. */
            flagWhenLarger
          />
          <StreakCard
            title={`After ${data!.after_wins.streak_length ?? 2} wins in a row`}
            behaviour={data!.after_wins}
            currency={currency}
          />

          {data!.activity_after_losses.n_bad_start_days ? (
            <Alert
              level="neutral"
              title="Days that started badly"
              body={`On ${data!.activity_after_losses.n_bad_start_days} day${data!.activity_after_losses.n_bad_start_days! > 1 ? 's' : ''} whose first trade lost, the median was ${ratio(data!.activity_after_losses.median_trades_bad_start, 1)} trades. On ${data!.activity_after_losses.n_good_start_days} day${data!.activity_after_losses.n_good_start_days! > 1 ? 's' : ''} whose first trade won, ${ratio(data!.activity_after_losses.median_trades_good_start, 1)}.`}
              footnote={`"Started badly" stands for the first trade of the day losing — a proxy, and a rough one. This is a correlation between two groups of your own days.`}
            />
          ) : null}

          {/* ── Mistakes ───────────────────────────────────────── */}
          {data!.mistake_frequency.length ? (
            <>
              <Section title="Mistakes you flagged"
                       subtitle="Only what you tagged yourself. A mistake never recorded is absent here, not absent from the book." />
              <Card style={styles.table}>
                {data!.mistake_frequency.map((row, i) => (
                  <View key={row.key} style={[styles.freqRow, i > 0 && styles.border]}>
                    <Text style={styles.freqLabel} numberOfLines={1}>{row.label}</Text>
                    <View style={styles.freqTrack}>
                      <View style={[styles.freqBar, { width: `${Math.max(row.share * 100, 1)}%` }]} />
                    </View>
                    <Text style={styles.freqValue}>
                      {row.count}
                      <Text style={styles.freqShare}>{`  ${percent(row.share, 0)}`}</Text>
                    </Text>
                  </View>
                ))}
              </Card>
            </>
          ) : null}

          {data!.mistakes.length ? (
            <>
              <Section title="What each mistake cost"
                       subtitle="Trades carrying the tag, against every other trade in the window." />
              <Card style={styles.table}>
                {data!.mistakes.map((row, i) => (
                  <ComparisonRow key={row.label} row={row} currency={currency} first={i === 0} />
                ))}
              </Card>
            </>
          ) : null}

          {/* ── Discipline ─────────────────────────────────────── */}
          {data!.discipline.length ? (
            <>
              <Section title="By your own discipline rating"
                       subtitle="The 1–5 you gave the trade when you logged it." />
              <Card style={styles.table}>
                {data!.discipline.map((row, i) => (
                  <ComparisonRow key={row.label} row={row} currency={currency} first={i === 0} />
                ))}
              </Card>
            </>
          ) : null}

          {/* ── Emotions ───────────────────────────────────────── */}
          {data!.emotions_before.length ? (
            <>
              <Section title="By the emotion recorded before entry"
                       subtitle="Before, not after: an emotion logged once the outcome is known is partly a reaction to it." />
              <Card style={styles.table}>
                {data!.emotions_before.map((row, i) => (
                  <ComparisonRow key={row.label} row={row} currency={currency} first={i === 0} />
                ))}
              </Card>
            </>
          ) : null}

          <Text style={styles.foot}>
            These are statistical patterns in your own journal. They are not a
            psychological assessment, and no part of this screen attempts one.
          </Text>
        </>
      )}
    </Screen>
  );
}

// ── After a run of wins or losses ───────────────────────────────────────────

function StreakCard({ title, behaviour, currency, flagWhenLarger }: {
  title: string;
  behaviour: StreakBehaviour;
  currency: string;
  flagWhenLarger?: boolean;
}) {
  if (!behaviour.n_after) {
    return (
      <Card style={styles.streakEmpty}>
        <Text style={styles.streakTitle}>{title}</Text>
        <Text style={styles.plain}>
          Too few trades followed such a run to compare — the engine needs at
          least {MIN_GROUP} on each side, and withholds the comparison rather
          than reporting a number it cannot stand behind.
        </Text>
      </Card>
    );
  }

  const r = behaviour.risk_ratio ?? null;
  const larger = r !== null && r > 1;
  const notable = r !== null && Math.abs(r - 1) >= 0.15;
  const after = behaviour.outcome_after;
  const other = behaviour.outcome_other;

  return (
    <Card style={styles.streak}>
      <View style={styles.streakHead}>
        <Text style={styles.streakTitle}>{title}</Text>
        {notable ? (
          <Pill
            text={`${times(r, 2)} the usual size`}
            tone={flagWhenLarger && larger && r! >= 1.25 ? 'warning' : 'neutral'}
          />
        ) : (
          <Pill text="no meaningful difference" tone="neutral" />
        )}
      </View>

      <View style={styles.compare}>
        <Side
          heading="after the run"
          risk={money(behaviour.median_risk_after, currency, 0)}
          n={behaviour.n_after}
          winRate={after?.win_rate}
          avgPnl={after?.avg_pnl}
          currency={currency}
        />
        <View style={styles.divider} />
        <Side
          heading="every other trade"
          risk={money(behaviour.median_risk_other, currency, 0)}
          n={other?.n ?? 0}
          winRate={other?.win_rate}
          avgPnl={other?.avg_pnl}
          currency={currency}
        />
      </View>

      {/* The per-group stop counts exist in the after-losses comparison and
          not in the after-wins one. Defaulting them to 0 printed "over the 0
          and 0 trades" under two medians that were plainly computed from
          something — the exact `?? 0` this codebase is built to avoid. When
          the counts are absent the sentence simply does not claim them. */}
      <Text style={styles.streakFoot}>
        {behaviour.n_after_with_risk !== undefined && behaviour.n_other_with_risk !== undefined
          ? `Median risk, over the ${behaviour.n_after_with_risk} and ${behaviour.n_other_with_risk} trades in each group that had a stop. `
          : 'Median risk, over the trades in each group that had a stop. '}
        This is a correlation between two groups of your own trades.
      </Text>
    </Card>
  );
}

function Side({ heading, risk, n, winRate, avgPnl, currency }: {
  heading: string;
  risk: string;
  n: number;
  winRate: number | null | undefined;
  avgPnl: number | null | undefined;
  currency: string;
}) {
  return (
    <View style={styles.side}>
      <Text style={styles.sideHeading} numberOfLines={1}>{heading.toUpperCase()}</Text>
      <Text style={styles.sideValue}>{risk}</Text>
      <Text style={styles.sideMeta}>{`n = ${n}`}</Text>
      <Text style={styles.sideMeta}>
        {percent(winRate, 0)} won · {money(avgPnl, currency, 0)} avg
      </Text>
    </View>
  );
}

// ── One group against the rest ──────────────────────────────────────────────

function ComparisonRow({ row, currency, first }: {
  row: Comparison; currency: string; first: boolean;
}) {
  const delta = row.avg_pnl_delta;
  const better = (delta ?? 0) >= 0;
  return (
    <View style={[styles.cmp, !first && styles.border]}>
      <View style={styles.cmpHead}>
        {/* `display` is set on emotion rows, `labels` on discipline ones, and
            the raw key on neither. Without the middle fallback the discipline
            table read "low / medium / high" instead of "Low discipline (1-2)",
            which loses the scale the rating is on. */}
        <Text style={styles.cmpLabel} numberOfLines={1}>
          {row.display ?? row.labels?.en ?? row.label}
        </Text>
        <Text style={[styles.cmpDelta, { color: better ? POS : NEG }]}>
          {delta === null || delta === undefined ? '—'
            : `${better ? '+' : ''}${money(delta, currency, 0)}`}
        </Text>
      </View>
      <Text style={styles.cmpBody}>
        {money(row.group.avg_pnl, currency, 0)} average against{' '}
        {money(row.rest.avg_pnl, currency, 0)} on the rest
        {row.win_rate_delta !== null && row.win_rate_delta !== undefined
          ? ` · ${percent(row.group.win_rate, 0)} won against ${percent(row.rest.win_rate, 0)}`
          : ''}
        {row.avg_r_delta !== null && row.avg_r_delta !== undefined
          ? ` · ${rMultiple(row.group.avg_r, 2)} against ${rMultiple(row.rest.avg_r, 2)}`
          : ''}
      </Text>
      {/* Both sides, always. One number without the other is the difference
          between a comparison and an accusation. */}
      <Text style={styles.cmpSample}>
        {`n = ${row.group.n} in this group · ${row.rest.n} in the rest · correlation`}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  gap: { marginTop: 16 },
  table: { paddingVertical: 2 },
  border: { borderTopWidth: 1, borderTopColor: BORDER },
  plain: { fontSize: 12, color: INK_MUTED, lineHeight: 17 },
  foot: {
    marginTop: 22, fontSize: 10.5, color: INK_FAINT, lineHeight: 15,
    textAlign: 'center',
  },

  streak: { marginBottom: 10 },
  streakEmpty: { marginBottom: 10, gap: 6 },
  streakHead: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    gap: 8, marginBottom: 12,
  },
  streakTitle: { flex: 1, fontSize: 13.5, fontWeight: '700', color: INK },
  streakFoot: { fontSize: 10, color: INK_FAINT, marginTop: 11, lineHeight: 14 },
  compare: { flexDirection: 'row', alignItems: 'stretch' },
  divider: { width: 1, backgroundColor: BORDER, marginHorizontal: 12 },
  side: { flex: 1 },
  sideHeading: { fontSize: 8.5, fontWeight: '800', letterSpacing: 0.9, color: INK_FAINT },
  sideValue: { fontSize: 19, fontWeight: '800', color: INK, marginTop: 4, letterSpacing: -0.4 },
  sideMeta: { fontSize: 10.5, color: INK_MUTED, marginTop: 3 },

  cmp: { paddingVertical: 11 },
  cmpHead: {
    flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', gap: 8,
  },
  cmpLabel: { flex: 1, fontSize: 13, fontWeight: '700', color: INK },
  cmpDelta: { fontSize: 12.5, fontWeight: '800' },
  cmpBody: { fontSize: 11.5, color: INK_2, marginTop: 5, lineHeight: 16 },
  cmpSample: { fontSize: 10, color: INK_FAINT, marginTop: 5 },

  freqRow: { flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 9 },
  freqLabel: { width: 112, fontSize: 11.5, color: INK_2 },
  freqTrack: { flex: 1, height: 9, borderRadius: 3, backgroundColor: 'rgba(154,168,191,0.10)' },
  freqBar: { height: 9, borderRadius: 3, backgroundColor: WARNING },
  freqValue: { width: 62, fontSize: 11.5, fontWeight: '700', color: INK, textAlign: 'right' },
  freqShare: { color: INK_FAINT, fontWeight: '500', fontSize: 10 },
});
