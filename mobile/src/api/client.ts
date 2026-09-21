/**
 * The Sensitor API client.
 *
 * No dependencies — `fetch` and `AbortController` are both in the React Native
 * runtime, so this file adds nothing to the bundle and runs unchanged in Node
 * for testing.
 *
 * What it does beyond wrapping fetch is the part that matters on a phone:
 *
 * **It caches by ETag.** Every mobile endpoint returns one. The client sends it
 * back in `If-None-Match`, and on a 304 returns the copy it already has without
 * the server sending a body. Most openings of an app find nothing changed;
 * this is what makes those free.
 *
 * **It never throws a bare network error at a screen.** Everything rejects with
 * an `ApiError` carrying a status and a message the caller can show. A screen
 * needs to distinguish "you are signed out" from "the server is unreachable" —
 * one means show the sign-in form, the other means show the cached data and a
 * retry.
 *
 * **It times out.** A request with no deadline on a flaky connection is a
 * spinner that never stops.
 */

import type {
  BreakdownRow, CurvePoint, DayPnL, Finding, Me, Meta, Overview, Period,
  Portfolio, Session, Trade, TradeDelta, TradingAccount, TradingMetrics,
} from './types';

export class ApiError extends Error {
  readonly status: number;
  readonly offline: boolean;

  constructor(message: string, status: number, offline = false) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.offline = offline;
  }

  /** The session is gone. A screen should send the person to sign in. */
  get unauthenticated(): boolean {
    return this.status === 401;
  }

  /** Nothing the caller can fix by retrying differently. */
  get permanent(): boolean {
    return this.status >= 400 && this.status < 500 && this.status !== 429;
  }
}

export interface ClientOptions {
  baseUrl: string;
  token?: string | null;
  timeoutMs?: number;
  /** Called whenever a request comes back 401, so the app can sign out once. */
  onUnauthenticated?: () => void;
}

interface CacheEntry {
  etag: string;
  body: unknown;
}

export interface TradingQuery {
  period?: Period;
  account?: string | null;
  symbol?: string | null;
  lang?: 'en' | 'fr';
}

export class SensitorClient {
  private baseUrl: string;
  private token: string | null;
  private timeoutMs: number;
  private onUnauthenticated?: () => void;
  private cache = new Map<string, CacheEntry>();

  constructor(options: ClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, '');
    this.token = options.token ?? null;
    this.timeoutMs = options.timeoutMs ?? 15_000;
    this.onUnauthenticated = options.onUnauthenticated;
  }

  setToken(token: string | null): void {
    this.token = token;
    if (!token) {
      // A cached overview belongs to whoever was signed in when it was
      // fetched. Keeping it across a sign-out would show one person's journal
      // to the next, which is the exact failure the server is built to prevent
      // — and the client is the other half of that.
      this.cache.clear();
    }
  }

  getToken(): string | null {
    return this.token;
  }

  // ── Plumbing ─────────────────────────────────────────────────────────────

  // `object` rather than `Record<string, unknown>`: an interface without an
  // index signature is not assignable to that Record, so requiring it would
  // force every query type to carry `[key: string]: unknown` — which is exactly
  // the escape hatch that lets a typo compile.
  private url(path: string, query?: object): string {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query ?? {})) {
      if (value !== undefined && value !== null && value !== '') {
        search.set(key, String(value));
      }
    }
    const qs = search.toString();
    return `${this.baseUrl}${path}${qs ? `?${qs}` : ''}`;
  }

  private async request<T>(
    path: string,
    { query, method = 'GET', body, cacheable = false }: {
      query?: object;
      method?: string;
      body?: unknown;
      cacheable?: boolean;
    } = {},
  ): Promise<T> {
    const url = this.url(path, query);
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    if (body !== undefined) headers['Content-Type'] = 'application/json';

    const cached = cacheable ? this.cache.get(url) : undefined;
    if (cached) headers['If-None-Match'] = cached.etag;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    let response: Response;
    try {
      response = await fetch(url, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });
    } catch (cause) {
      // Unreachable, refused, or timed out. Status 0 and `offline` let a screen
      // fall back to what it already has instead of showing a failure.
      throw new ApiError(
        cause instanceof Error && cause.name === 'AbortError'
          ? 'the request timed out'
          : 'could not reach the server',
        0,
        true,
      );
    } finally {
      clearTimeout(timer);
    }

    if (response.status === 304 && cached) {
      return cached.body as T;
    }

    if (response.status === 401) {
      this.onUnauthenticated?.();
      throw new ApiError('your session has expired', 401);
    }

    if (!response.ok) {
      throw new ApiError(await readDetail(response), response.status);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const payload = (await response.json()) as T;
    if (cacheable) {
      const etag = response.headers.get('etag');
      if (etag) this.cache.set(url, { etag, body: payload });
    }
    return payload;
  }

  // ── Meta ─────────────────────────────────────────────────────────────────

  meta(): Promise<Meta> {
    return this.request<Meta>('/meta');
  }

  health(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  // ── Auth ─────────────────────────────────────────────────────────────────

  /**
   * Exchange credentials for a session, and keep it.
   *
   * `apiKey` is for single-user deployments, which issue no session without
   * one. `meta().issues_sessions` says in advance whether signing in is even
   * possible, so a client can explain the situation rather than showing a
   * failure it cannot account for.
   */
  async signIn(email: string, password?: string, apiKey?: string): Promise<Session> {
    const session = await this.request<Session>('/auth/sign-in', {
      method: 'POST',
      body: { email, password: password ?? null, api_key: apiKey ?? null },
    });
    this.setToken(session.token);
    return session;
  }

  async signUp(email: string, password: string): Promise<Session> {
    const session = await this.request<Session>('/auth/sign-up', {
      method: 'POST',
      body: { email, password },
    });
    this.setToken(session.token);
    return session;
  }

  async signOut(): Promise<void> {
    try {
      await this.request<void>('/auth/sign-out', { method: 'POST' });
    } finally {
      // Cleared even if the call failed. A token the server may still honour is
      // worse kept on the device than dropped from it.
      this.setToken(null);
    }
  }

  me(): Promise<Me> {
    return this.request<Me>('/auth/me');
  }

  // ── Mobile ───────────────────────────────────────────────────────────────

  /** The home screen, in one request, cached by ETag. */
  overview(query: TradingQuery & { curve_points?: number } = {}): Promise<Overview> {
    return this.request<Overview>('/mobile/overview', { query, cacheable: true });
  }

  /** The current data version — a tiny poll to decide whether to fetch at all. */
  version(): Promise<{ etag: string }> {
    return this.request<{ etag: string }>('/mobile/version');
  }

  /**
   * Trades changed since a cursor.
   *
   * Pass the `server_time` from the previous response, never a locally
   * generated timestamp: a phone whose clock runs fast would ask for changes
   * since a moment that has not happened and silently miss everything written
   * in between.
   */
  tradeDelta(since?: string | null, limit = 200, account?: string | null): Promise<TradeDelta> {
    return this.request<TradeDelta>('/mobile/trades', {
      query: { since, limit, account },
    });
  }

  // ── Trading ──────────────────────────────────────────────────────────────

  metrics(query: TradingQuery = {}): Promise<TradingMetrics> {
    return this.request<TradingMetrics>('/trading/metrics', { query });
  }

  equity(query: TradingQuery = {}): Promise<CurvePoint[]> {
    return this.request<CurvePoint[]>('/trading/equity', { query });
  }

  daily(query: TradingQuery = {}): Promise<DayPnL[]> {
    return this.request<DayPnL[]>('/trading/daily', { query });
  }

  breakdown(dimension: string, query: TradingQuery = {}): Promise<BreakdownRow[]> {
    return this.request<BreakdownRow[]>(`/trading/breakdown/${dimension}`, { query });
  }

  findings(query: TradingQuery = {}): Promise<Finding[]> {
    return this.request<Finding[]>('/trading/findings', { query });
  }

  risk(query: TradingQuery = {}): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('/trading/risk', { query });
  }

  trades(query: TradingQuery & { limit?: number; offset?: number } = {}): Promise<{
    trades: Trade[]; total: number; limit: number; offset: number;
  }> {
    return this.request('/trading/trades', { query });
  }

  accounts(): Promise<TradingAccount[]> {
    return this.request<TradingAccount[]>('/trading/accounts');
  }

  periods(): Promise<Period[]> {
    return this.request<Period[]>('/trading/periods');
  }

  // ── Portfolios ───────────────────────────────────────────────────────────

  portfolios(): Promise<Portfolio[]> {
    return this.request<Portfolio[]>('/portfolios');
  }

  portfolio(id: number): Promise<Portfolio> {
    return this.request<Portfolio>(`/portfolios/${id}`);
  }
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === 'string') return body.detail;
    if (Array.isArray(body.detail)) return 'that request was not valid';
  } catch {
    // A non-JSON error body is not worth surfacing raw.
  }
  return `request failed (${response.status})`;
}
