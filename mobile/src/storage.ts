/**
 * Where the session token lives.
 *
 * `expo-secure-store` puts it in the iOS Keychain, which is the right place: a
 * bearer token is a credential, and `AsyncStorage` is a plaintext file any
 * process with the app's sandbox can read.
 *
 * SecureStore has no web implementation, so the web build — the one used to
 * look at these screens during development — falls back to `localStorage`.
 * That fallback is *not* secure storage and is never reached on a device; it
 * exists so the preview runs, and it says so rather than pretending otherwise.
 */

import { Platform } from 'react-native';

const KEY = 'sensitor.session';

export async function saveToken(token: string): Promise<void> {
  if (Platform.OS === 'web') {
    try { window.localStorage.setItem(KEY, token); } catch { /* private mode */ }
    return;
  }
  const SecureStore = await import('expo-secure-store');
  await SecureStore.setItemAsync(KEY, token);
}

export async function loadToken(): Promise<string | null> {
  if (Platform.OS === 'web') {
    try { return window.localStorage.getItem(KEY); } catch { return null; }
  }
  const SecureStore = await import('expo-secure-store');
  return SecureStore.getItemAsync(KEY);
}

export async function clearToken(): Promise<void> {
  if (Platform.OS === 'web') {
    try { window.localStorage.removeItem(KEY); } catch { /* private mode */ }
    return;
  }
  const SecureStore = await import('expo-secure-store');
  await SecureStore.deleteItemAsync(KEY);
}

const BASE_KEY = 'sensitor.baseUrl';

/** The server this install talks to. Editable on the sign-in screen. */
export async function saveBaseUrl(url: string): Promise<void> {
  if (Platform.OS === 'web') {
    try { window.localStorage.setItem(BASE_KEY, url); } catch { /* ignore */ }
    return;
  }
  const SecureStore = await import('expo-secure-store');
  await SecureStore.setItemAsync(BASE_KEY, url);
}

export async function loadBaseUrl(): Promise<string | null> {
  if (Platform.OS === 'web') {
    try { return window.localStorage.getItem(BASE_KEY); } catch { return null; }
  }
  const SecureStore = await import('expo-secure-store');
  return SecureStore.getItemAsync(BASE_KEY);
}
