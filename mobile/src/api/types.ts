/**
 * The shapes the Sensitor API returns.
 *
 * Hand-written rather than generated, and narrow on purpose: these are the
 * fields the app reads. Generating the full OpenAPI surface would produce
 * hundreds of types nobody imports and would still need this file's most
 * important property — that every field the engine can leave undefined is
 * typed `| null`, so the compiler refuses to let a screen render one as a
 * number.
 *
 * That is the point of typing this at all. `profitFactor: number` would compile
 * a screen that prints `0.00` when the answer is "there were no losing trades",
 * and a trader reading that would conclude their system loses money.
 */

/** A figure the engine reports as undefined rather than zero. */
export type Undefinable = number | null;

export interface Meta {
  product: string;
  version: string;
  schema_version: number;
  auth_mode: 'single' | 'multi';
  /** False when a single-user deployment has no API key: no session can be had. */
  issues_sessions: boolean;
}

export interface Session {
  token: string;
  email: string;
  expires_days: number;
}

export interface Me {
  email: string;
  tier: string;
  display_name: string | null;
  last_login_at: string | null;
}

export interface TradingMetrics {
  /** Always read this first. Every other figure is meaningless without it. */
  n: number;
  n_wins: number | null;
  n_losses: number | null;
  net_pnl: Undefinable;
  gross_profit: Undefinable;
  gross_loss: Undefinable;
  win_rate: Undefinable;
  /** null when there are no losing trades — a division with no denominator. */
  profit_factor: Undefinable;
  expectancy: Undefinable;
  avg_win: Undefinable;
  avg_loss: Undefinable;
  payoff_ratio: Undefinable;
  /** null when no trade had a stop. Never render as 0. */
  avg_r: Undefinable;
  total_r: Undefinable;
  /** What share of the book the R figures actually describe. */
  r_coverage: Undefinable;
  n_with_r: number | null;
  max_drawdown: Undefinable;
  max_drawdown_r: Undefinable;
  max_win_streak: number | null;
  max_loss_streak: number | null;
  current_streak: number | null;
  median_holding_minutes: Undefinable;
  first_trade: string | null;
  last_trade: string | null;
  symbols: number | null;
}

export interface CurvePoint {
  at: string;
  equity: number;
}

export interface DayPnL {
  date: string;
  pnl: number;
  n: number;
}

export interface BreakdownRow {
  key: string;
  label: string;
  /** The sample size. Shown, never hidden. */
  n: number;
  /** False below the threshold — mark these, do not rank them with the rest. */
  reliable: boolean;
  net_pnl: Undefinable;
  win_rate: Undefinable;
  expectancy: Undefinable;
  profit_factor: Undefinable;
  avg_r: Undefinable;
  total_r: Undefinable;
}

/**
 * A psychology finding.
 *
 * `en` and `fr` are written by the engine. Each states that it is a
 * correlation and carries its sample size. Render one verbatim — paraphrasing
 * it into a verdict removes the only safeguard on the most easily misread
 * screen in the product.
 */
export interface Finding {
  key: string;
  level: 'good' | 'neutral' | 'warning' | 'critical' | string;
  en: string;
  fr: string;
  n: number;
  interpretation: 'correlation';
}

export interface Trade {
  id: string;
  symbol: string;
  direction: 'long' | 'short';
  entry_price: number;
  exit_price: number | null;
  size: number;
  stop_loss: number | null;
  take_profit: number | null;
  opened_at: string | null;
  closed_at: string | null;
  pnl: Undefinable;
  /** null when the trade had no stop. */
  r_multiple: Undefinable;
  r_multiple_gross: Undefinable;
  risk_amount: Undefinable;
  duration_minutes: Undefinable;
  session: string | null;
  account_id: string | null;
  account_currency: string;
  setups: string[];
  mistakes: string[];
  timeframe: string | null;
  notes: string | null;
  source: string;
}

export interface TradingAccount {
  id: string;
  name: string;
  broker: string | null;
  currency: string;
  last_synced_at: string | null;
  last_sync_trades: number | null;
}

/** Everything a home screen needs, from one request. */
export interface Overview {
  etag: string;
  period: string;
  available_periods: string[];
  currency: string;
  metrics: TradingMetrics;
  equity: CurvePoint[];
  r_curve: CurvePoint[];
  daily: DayPnL[];
  by_symbol: BreakdownRow[];
  findings: Finding[];
  open_positions: number;
  accounts: TradingAccount[];
  notes: {
    r_coverage: Undefinable;
    undefined_is_null: boolean;
    findings_are_correlations: boolean;
  };
}

export interface TradeDelta {
  etag: string;
  /** Store this as the next cursor — the server's clock, not the phone's. */
  server_time: string;
  since: string | null;
  trades: Trade[];
  count: number;
  complete: boolean;
}

export interface Portfolio {
  id: number;
  name: string;
  holdings: Record<string, number>;
  mode: string;
  currency: string;
  notes: string | null;
  client_name: string | null;
  created_at: string;
  updated_at: string;
}

export type Period = '7D' | '30D' | '90D' | '6M' | '1Y' | 'ALL';
