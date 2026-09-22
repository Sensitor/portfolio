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

/**
 * What these functions accept.
 *
 * Wider than `Undefinable` by one case, and the case matters: the engine
 * returns `{}` for a whole section it declined to compute, so a field can
 * arrive missing as well as null. Both mean the same thing — no figure — and
 * both must render as a dash. Narrowing this to `number | null` would push an
 * `?? 0` into every screen reading an optional field, which is the one thing
 * this file exists to prevent.
 */
export type Figure = Undefinable | undefined;

/** What an undefined figure looks like. Never a zero. */
export const DASH = '—';

const SYMBOLS: Record<string, string> = {
  USD: '$', EUR: '€', GBP: '£', JPY: '¥', CHF: 'CHF ', CAD: 'CA$',
  AUD: 'A$', NZD: 'NZ$', SEK: 'kr ', NOK: 'kr ', PLN: 'zł ',
};

/**
 * The prefix for an amount.
 *
 * The API reports a currency **code** — `"USD"` — because that is what the
 * account carries. Passing it straight through produced "USD158,777.59" on
 * every screen, which is the sort of thing that survives a typecheck and a
 * test suite and dies the moment somebody looks at it.
 *
 * An unknown code is returned as-is with a space rather than guessed at: a
 * wrong symbol is worse than an unfamiliar code, because it reads as a
 * different currency.
 */
export function currencySymbol(currency: string | null | undefined): string {
  if (!currency) return '$';
  if (currency.length !== 3) return currency;          // already a symbol
  return SYMBOLS[currency.toUpperCase()] ?? `${currency.toUpperCase()} `;
}

export function money(value: Figure, currency = '$', decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  const sign = value < 0 ? '-' : '';
  const body = Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return `${sign}${currencySymbol(currency)}${body}`;
}

export function percent(value: Figure, decimals = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return `${(value * 100).toFixed(decimals)}%`;
}

export function ratio(value: Figure, decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return value.toFixed(decimals);
}

/** An R multiple, always signed. `null` means the trade had no stop. */
export function rMultiple(value: Figure, decimals = 2): string {
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
export function profitFactor(value: Figure, lang: 'en' | 'fr' = 'en'): string {
  if (value === null || value === undefined) {
    return lang === 'fr' ? 'indéfini' : 'undefined';
  }
  return value.toFixed(2);
}

export function duration(minutes: Figure, lang: 'en' | 'fr' = 'en'): string {
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

/**
 * A timestamp, short enough for a list row.
 *
 * The server sends the broker's own clock, already offset-corrected at import.
 * Parsed and reformatted in the device's locale rather than shown raw: an ISO
 * string in a journal row is four characters of information in twenty-five.
 */
export function stamp(iso: string | null | undefined): string {
  if (!iso) return DASH;
  const at = new Date(iso);
  if (Number.isNaN(at.getTime())) return DASH;
  return at.toLocaleDateString(undefined, { day: '2-digit', month: 'short' })
    + ' · '
    + at.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export function dayOnly(iso: string | null | undefined): string {
  if (!iso) return DASH;
  const at = new Date(iso);
  if (Number.isNaN(at.getTime())) return DASH;
  return at.toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' });
}

/** A multiple — "2.4×". Undefined stays a dash, never 1. */
export function times(value: Figure, decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return `${value.toFixed(decimals)}×`;
}

/** A count out of a total, with the share — "4 of 31 · 13%". */
export function outOf(count: number | undefined, total: number | undefined): string {
  if (count === undefined || total === undefined || total === 0) return DASH;
  return `${count} of ${total} · ${percent(count / total, 0)}`;
}
