/**
 * Rendering the values the engine can leave undefined.
 *
 * This file exists because the alternative is every screen writing
 * `metrics.profit_factor.toFixed(2)`, which crashes on null — or worse,
 * `(metrics.profit_factor ?? 0).toFixed(2)`, which does not crash and prints
 * `0.00` when the truth is "there were no losing trades". A trader reading that
 * would conclude their system loses money.
 *
 * So there is one place that turns an undefined figure into a dash, and the
 * screens call it.
 */

import type { BreakdownRow, TradingMetrics, Undefinable } from './types';

/** What an undefined figure looks like. Never a zero. */
export const DASH = '—';

export function money(value: Undefinable, currency = '$', decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  const sign = value < 0 ? '-' : '';
  const body = Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return `${sign}${currency}${body}`;
}

export function percent(value: Undefinable, decimals = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return `${(value * 100).toFixed(decimals)}%`;
}

export function ratio(value: Undefinable, decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return value.toFixed(decimals);
}

/** An R multiple, always signed. `null` means the trade had no stop. */
export function rMultiple(value: Undefinable, decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}R`;
}

/**
 * Profit factor, with the reason when there is not one.
 *
 * The engine returns null when there are no losing trades, because the ratio
 * has no denominator. "Undefined" is the honest label; "∞" puts a meaningless
 * value in a column of meaningful ones.
 */
export function profitFactor(value: Undefinable, lang: 'en' | 'fr' = 'en'): string {
  if (value === null || value === undefined) {
    return lang === 'fr' ? 'indéfini' : 'undefined';
  }
  return value.toFixed(2);
}

export function duration(minutes: Undefinable, lang: 'en' | 'fr' = 'en'): string {
  if (minutes === null || minutes === undefined) return DASH;
  if (minutes < 60) return `${Math.round(minutes)} min`;
  if (minutes < 60 * 24) return `${(minutes / 60).toFixed(1)} h`;
  const days = minutes / (60 * 24);
  return lang === 'fr' ? `${days.toFixed(1)} j` : `${days.toFixed(1)} d`;
}

/**
 * The caveat that belongs beside every R figure.
 *
 * Returns null when R covers the whole book and there is nothing to say.
 */
export function rCoverageNote(
  metrics: Pick<TradingMetrics, 'r_coverage' | 'n_with_r' | 'n'>,
  lang: 'en' | 'fr' = 'en',
): string | null {
  const coverage = metrics.r_coverage;
  if (coverage === null || coverage === undefined || coverage >= 1) return null;
  const share = percent(coverage, 0);
  return lang === 'fr'
    ? `Les chiffres en R ne couvrent que ${share} des trades — ceux ayant eu un stop.`
    : `R figures cover only ${share} of trades — the ones that had a stop.`;
}

/**
 * Whether a breakdown row should be shown as provisional.
 *
 * A table sorted by win rate always puts a two-trade bucket on top. The server
 * says which rows clear its sample threshold; a screen that ignores `reliable`
 * will present a coincidence as a finding.
 */
export function isProvisional(row: Pick<BreakdownRow, 'reliable'>): boolean {
  return !row.reliable;
}

export function sampleLabel(n: number, lang: 'en' | 'fr' = 'en'): string {
  return lang === 'fr' ? `n = ${n} trades` : `n = ${n} trades`;
}
