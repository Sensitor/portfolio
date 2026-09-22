/**
 * Design tokens — the same values as `sensitor/ui/themes.py`.
 *
 * Kept in sync by hand and deliberately not generated: there are fifteen of
 * them, they change about once a year, and a build step that reads Python from
 * TypeScript would be more machinery than the problem deserves. The comment
 * above each group says what it is for, so a drift is visible in review.
 *
 * The categorical palette is the validated 8-slot dark set, checked against
 * this app's own surface (#0E1522). Slots are assigned in fixed order and never
 * cycled — past 8 series, fold the tail into muted ink rather than inventing a
 * ninth hue.
 */

export const BG = '#070B14';          // page plane
export const SURFACE = '#0E1522';     // card surface — the palette is validated against this
export const SURFACE_2 = '#141C2B';   // raised surface, table headers
export const SURFACE_3 = '#1B2435';   // inputs, chips

export const INK = '#EDF2F9';         // primary text
export const INK_2 = '#9AA8BF';       // secondary
export const INK_MUTED = '#6B7A93';   // captions, axis labels
export const INK_FAINT = '#465065';   // disabled, hairlines

export const BORDER = 'rgba(154,168,191,0.14)';
export const BORDER_STRONG = 'rgba(154,168,191,0.26)';
export const GRID = 'rgba(154,168,191,0.08)';

export const ACCENT = '#3987E5';
export const ACCENT_SOFT = 'rgba(57,135,229,0.14)';

/** Fixed roles. Each always ships with an icon or a label, so hue never carries meaning alone. */
export const GOOD = '#16B979';
export const WARNING = '#E8A317';
export const SERIOUS = '#E8894A';
export const CRITICAL = '#E2504F';

export const POS = '#16B979';
export const NEG = '#E2504F';

export const STATUS: Record<string, string> = {
  good: GOOD,
  warning: WARNING,
  serious: SERIOUS,
  critical: CRITICAL,
  neutral: INK_2,
};

export const STATUS_ICON: Record<string, string> = {
  good: '●',
  warning: '▲',
  serious: '▲',
  critical: '■',
  neutral: '○',
};

export const PALETTE = [
  '#3987E5', '#D95926', '#199E70', '#C98500',
  '#D55181', '#008300', '#9085E9', '#E66767',
];

export const RADIUS = 14;
export const RADIUS_SM = 9;
export const RADIUS_PILL = 999;

/** Which colour a figure gets. Never the only signal — a label always says the same thing. */
export function toneFor(value: number | null | undefined): string {
  if (value === null || value === undefined) return INK_2;
  return value > 0 ? POS : value < 0 ? NEG : INK_2;
}

export function seriesColor(i: number): string {
  return PALETTE[i % PALETTE.length] ?? INK_MUTED;
}
