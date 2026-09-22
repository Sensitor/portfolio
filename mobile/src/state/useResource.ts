/**
 * One fetch, four states.
 *
 * `useOverview` does this for the home payload; the other tabs each read a
 * different endpoint, and without a shared hook every one of them would grow
 * its own copy of the same try/catch — which is where the distinction that
 * matters gets lost.
 *
 * That distinction: **offline is not an error.** A dropped connection keeps the
 * last data on screen and sets `offline`; anything else clears nothing and sets
 * `error`. A screen that conflates them either blanks a readable page because a
 * tunnel ended, or reports "could not reach the server" for a 422.
 */

import { useCallback, useEffect, useState, type DependencyList } from 'react';

import type { ApiError, SensitorClient } from '../api/client';
import { useSession } from './session';

export interface Resource<T> {
  data: T | null;
  loading: boolean;
  refreshing: boolean;
  /** The server could not be reached. `data` may still hold the last copy. */
  offline: boolean;
  error: string | null;
  refresh(): void;
}

export function useResource<T>(
  fetcher: (client: SensitorClient) => Promise<T>,
  deps: DependencyList,
): Resource<T> {
  const { client } = useSession();
  const [state, setState] = useState<Omit<Resource<T>, 'refresh'>>({
    data: null, loading: true, refreshing: false, offline: false, error: null,
  });

  // The fetcher is a fresh closure every render, so it cannot be a dependency
  // itself — the caller's `deps` are what actually decide when to refetch.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fetcher, [client, ...deps]);

  const load = useCallback(async (mode: 'initial' | 'refresh') => {
    setState((s) => ({
      ...s,
      loading: mode === 'initial' && !s.data,
      refreshing: mode === 'refresh',
    }));
    try {
      const data = await run(client);
      setState({ data, loading: false, refreshing: false, offline: false, error: null });
    } catch (caught) {
      const api = caught as ApiError;
      setState((s) => ({
        ...s,
        loading: false,
        refreshing: false,
        offline: !!api.offline,
        error: api.offline ? null : api.message,
      }));
    }
  }, [client, run]);

  useEffect(() => { void load('initial'); }, [load]);

  const refresh = useCallback(() => { void load('refresh'); }, [load]);
  return { ...state, refresh };
}
