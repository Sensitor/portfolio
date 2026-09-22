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

/**
 * The risk summary.
 *
 * Every sub-object is optional, and so is nearly every field inside one. That
 * is not defensive typing — it mirrors the engine, which returns `{}` for a
 * section it cannot compute rather than a shape full of zeros. `drift` needs
 * ten trades with a stop before it means anything; `streaks` needs ten trades
 * at all. A screen that types these as present will render "0 concurrent
 * positions" for a book the engine declined to measure.
 */
export interface RiskProfile {
  n: number;
  n_with_stop?: number;
  coverage?: Undefinable;
  no_stop_count?: number;
  mean_risk?: Undefinable;
  median_risk?: Undefinable;
  min_risk?: Undefinable;
  max_risk?: Undefinable;
  risk_spread?: Undefinable;
  /** Coefficient of variation. null below the sample threshold — not zero. */
  consistency?: Undefinable;
  largest_vs_median?: Undefinable;
}

export interface RiskDrift {
  start_median?: number;
  end_median?: number;
  change?: number;
  direction?: 'up' | 'down' | 'stable' | string;
  n_points?: number;
  from?: string;
  to?: string;
}

export interface StopDiscipline {
  n_with_r?: number;
  n_losses?: number;
  n_beyond_stop?: number;
  share_beyond_stop?: Undefinable;
  worst_loss_r?: Undefinable;
  avg_loss_r?: Undefinable;
  /** Always "gross" — see the API docs. Costs alone push a clean stop past -1R. */
  measured_on?: string;
  beyond_stop_trades?: string[];
}

export interface Exposure {
  max_concurrent?: number;
  max_concurrent_at?: string;
  max_concurrent_symbols?: string[];
  max_simultaneous_risk?: Undefinable;
  max_simultaneous_risk_at?: string;
}

export interface Activity {
  n_days?: number;
  mean_per_day?: number;
  median_per_day?: number;
  max_per_day?: number;
  busiest_day?: string;
  counts_by_day?: Record<string, number>;
}

export interface StreakContext {
  observed_max_losses?: number;
  expected_max_losses?: number;
  unusual?: boolean;
  win_rate?: Undefinable;
  n?: number;
}

export interface RiskSummary {
  profile: RiskProfile;
  drift: RiskDrift;
  stops: StopDiscipline;
  exposure: Exposure;
  activity: Activity;
  streaks: StreakContext;
}

/**
 * Behavioural comparisons.
 *
 * Every one of these compares two groups of the caller's own trades and
 * carries both sample sizes. `interpretation` is the literal string
 * `"correlation"` in the engine, and a screen renders the word rather than
 * deciding for itself what the comparison means.
 */
export interface GroupOutcome {
  n: number;
  net_pnl?: Undefinable;
  avg_pnl?: Undefinable;
  win_rate?: Undefinable;
  avg_r?: Undefinable;
  n_with_r?: number;
  avg_risk?: Undefinable;
  n_with_risk?: number;
}

export interface Comparison {
  label: string;
  labels?: Record<string, string>;
  display?: string;
  phase?: string;
  group: GroupOutcome;
  rest: GroupOutcome;
  avg_pnl_delta: Undefinable;
  win_rate_delta: Undefinable;
  avg_r_delta: Undefinable;
  interpretation: 'correlation';
}

export interface MistakeCount {
  key: string;
  label: string;
  count: number;
  share: number;
}

/** After a run of losses, or of wins. `{}` when either group is too small. */
export interface StreakBehaviour {
  streak_length?: number;
  n_after?: number;
  n_after_with_risk?: number;
  n_other_with_risk?: number;
  median_risk_after?: Undefinable;
  median_risk_other?: Undefinable;
  risk_ratio?: Undefinable;
  outcome_after?: GroupOutcome;
  outcome_other?: GroupOutcome;
  interpretation?: 'correlation';
}

export interface DayStartBehaviour {
  n_bad_start_days?: number;
  n_good_start_days?: number;
  median_trades_bad_start?: number;
  median_trades_good_start?: number;
  interpretation?: 'correlation';
  /** What stands in for "a bad day" — stated, because it is a proxy. */
  proxy?: string;
}

export interface PsychologySummary {
  emotions_before: Comparison[];
  discipline: Comparison[];
  mistakes: Comparison[];
  mistake_frequency: MistakeCount[];
  after_losses: StreakBehaviour;
  after_wins: StreakBehaviour;
  activity_after_losses: DayStartBehaviour;
}

export interface TradesPage {
  trades: Trade[];
  total: number;
  limit: number;
  offset: number;
}

/** The dimensions `/trading/breakdown/{dimension}` accepts. */
export type Dimension =
  | 'symbol' | 'setup' | 'combination' | 'session' | 'weekday' | 'hour'
  | 'month' | 'timeframe' | 'direction' | 'regime' | 'risk_band';

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
