/**
 * Who is signed in, and the client they talk through.
 *
 * One provider at the root. Every screen reads the client from here rather than
 * constructing its own, because the client holds the ETag cache — a second
 * instance would have an empty one and re-download everything the first already
 * has.
 *
 * The token is restored from the Keychain on launch, so reopening the app does
 * not mean signing in again. `status` distinguishes "still checking" from
 * "signed out": rendering the sign-in screen during the check would flash it at
 * someone who is already signed in.
 */

import React, {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
} from 'react';

import { ApiError, SensitorClient } from '../api/client';
import type { Meta } from '../api/types';
import { clearToken, loadBaseUrl, loadToken, saveBaseUrl, saveToken } from '../storage';

const DEFAULT_BASE_URL =
  process.env.EXPO_PUBLIC_SENSITOR_API_URL ?? 'http://localhost:8000';

type Status = 'checking' | 'signed-out' | 'signed-in';

interface SessionValue {
  status: Status;
  email: string | null;
  client: SensitorClient;
  baseUrl: string;
  meta: Meta | null;
  signIn(email: string, password?: string, apiKey?: string): Promise<void>;
  signOut(): Promise<void>;
  setBaseUrl(url: string): Promise<void>;
}

const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>('checking');
  const [email, setEmail] = useState<string | null>(null);
  const [baseUrl, setBaseUrlState] = useState(DEFAULT_BASE_URL);
  const [meta, setMeta] = useState<Meta | null>(null);

  const client = useMemo(
    () => new SensitorClient({
      baseUrl,
      // A 401 from anywhere means the session is gone. Handled once, here,
      // rather than in each screen's error branch.
      onUnauthenticated: () => {
        void clearToken();
        setEmail(null);
        setStatus('signed-out');
      },
    }),
    [baseUrl],
  );

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const storedBase = await loadBaseUrl();
      if (storedBase && !cancelled) {
        setBaseUrlState(storedBase);
        return;   // the client rebuilds, and this effect runs again
      }

      // What the deployment can do, so the sign-in screen can explain itself.
      try {
        const info = await client.meta();
        if (!cancelled) setMeta(info);
      } catch { /* offline — the screen says so */ }

      const token = await loadToken();
      if (!token) {
        if (!cancelled) setStatus('signed-out');
        return;
      }

      client.setToken(token);
      try {
        const me = await client.me();
        if (!cancelled) { setEmail(me.email); setStatus('signed-in'); }
      } catch (error) {
        // An expired token signs out. An unreachable server does not — the
        // person is still signed in, they simply have no connection, and
        // throwing them to the sign-in screen would lose their session over a
        // dropped tunnel.
        const api = error as ApiError;
        if (!cancelled) {
          if (api.offline) { setEmail('…'); setStatus('signed-in'); }
          else { await clearToken(); setStatus('signed-out'); }
        }
      }
    })();

    return () => { cancelled = true; };
  }, [client]);

  const signIn = useCallback(async (address: string, password?: string, apiKey?: string) => {
    const session = await client.signIn(address, password, apiKey);
    await saveToken(session.token);
    setEmail(session.email);
    setStatus('signed-in');
  }, [client]);

  const signOut = useCallback(async () => {
    try { await client.signOut(); } finally {
      await clearToken();
      setEmail(null);
      setStatus('signed-out');
    }
  }, [client]);

  const setBaseUrl = useCallback(async (url: string) => {
    const cleaned = url.trim().replace(/\/+$/, '');
    await saveBaseUrl(cleaned);
    await clearToken();          // a token from one server is meaningless at another
    setEmail(null);
    setStatus('signed-out');
    setBaseUrlState(cleaned);
  }, []);

  const value = useMemo<SessionValue>(
    () => ({ status, email, client, baseUrl, meta, signIn, signOut, setBaseUrl }),
    [status, email, client, baseUrl, meta, signIn, signOut, setBaseUrl],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error('useSession must be used inside a SessionProvider');
  return value;
}
