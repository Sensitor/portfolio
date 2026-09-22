/**
 * The data every screen reads, fetched once per period.
 *
 * `/mobile/overview` returns a whole screen in one request, so four of the five
 * tabs render from a single payload with no further calls. That is the point of
 * the endpoint: six requests can each land on a different moment, and one
 * cannot, so every figure on screen describes the same set of trades.
 *
 * `refresh` forces a re-fetch. Ordinary loads go through the client's ETag
 * cache, so reopening a tab that has not changed costs a 304 and no body.
 */

import { useCallback, useEffect, useState } from 'react';

import { ApiError } from '../api/client';
import type { Overview, Period } from '../api/types';
import { useSession } from './session';

interface State {
  data: Overview | null;
  loading: boolean;
  refreshing: boolean;
  /** Set when the server could not be reached. `data` may still hold a cached copy. */
  offline: boolean;
  error: string | null;
}

export function useOverview(period: Period) {
  const { client } = useSession();
  const [state, setState] = useState<State>({
    data: null, loading: true, refreshing: false, offline: false, error: null,
  });

  const load = useCallback(async (mode: 'initial' | 'refresh') => {
    setState((s) => ({
      ...s,
      loading: mode === 'initial' && !s.data,
      refreshing: mode === 'refresh',
    }));
    try {
      const data = await client.overview({ period });
      setState({ data, loading: false, refreshing: false, offline: false, error: null });
    } catch (caught) {
      const api = caught as ApiError;
      // Offline keeps whatever is on screen and says so. Clearing it would
      // punish a dropped connection by blanking data the person can still read.
      setState((s) => ({
        ...s,
        loading: false,
        refreshing: false,
        offline: api.offline,
        error: api.offline ? null : api.message,
      }));
    }
  }, [client, period]);

  useEffect(() => { void load('initial'); }, [load]);

  const refresh = useCallback(() => load('refresh'), [load]);
  return { ...state, refresh };
}
