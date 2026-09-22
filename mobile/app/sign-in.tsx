/**
 * Sign in.
 *
 * The server is editable here, and that is not a developer affordance: this
 * app talks to *your* deployment, and there is no hosted default to fall back
 * on. Burying the field in a settings screen would make a first run fail with
 * nothing to do about it.
 *
 * What the form asks for depends on what the deployment will accept, read from
 * `/meta`. A single-user server with no API key issues no sessions at all, and
 * the screen says that instead of offering a form that cannot work.
 */

import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import {
  ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView,
  StyleSheet, Text, TextInput, View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ApiError } from '../src/api/client';
import { Card, Note, ScreenHeader } from '../src/components/primitives';
import { useSession } from '../src/state/session';
import {
  ACCENT, BG, BORDER, INK, INK_2, INK_FAINT, INK_MUTED, RADIUS_SM, SURFACE_3,
} from '../src/theme';

export default function SignIn() {
  const { signIn, baseUrl, setBaseUrl, meta } = useSession();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [server, setServer] = useState(baseUrl);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const multiUser = meta?.auth_mode === 'multi';
  const canSignIn = meta?.issues_sessions !== false;

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      if (server.trim().replace(/\/+$/, '') !== baseUrl) {
        await setBaseUrl(server);
        setError('Server changed — tap Sign in again.');
        return;
      }
      await signIn(email.trim(), multiUser ? password : undefined,
                   multiUser ? undefined : apiKey);
      router.replace('/');
    } catch (caught) {
      const api = caught as ApiError;
      setError(api.offline ? 'Could not reach that server.' : api.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + 52 }]}
        keyboardShouldPersistTaps="handled"
      >
        <ScreenHeader
          eyebrow="Sensitor"
          title="Sign in"
          subtitle="Your trading and portfolio analytics, from your own server."
        />

        <Card style={styles.form}>
          <Field label="Server" value={server} onChange={setServer}
                 placeholder="https://your-server" autoCapitalize="none" />

          {canSignIn ? (
            <>
              <Field label="Email" value={email} onChange={setEmail}
                     placeholder="you@example.com" autoCapitalize="none"
                     keyboardType="email-address" />
              {multiUser ? (
                <Field label="Password" value={password} onChange={setPassword}
                       secure placeholder="••••••••" />
              ) : (
                <Field label="API key" value={apiKey} onChange={setApiKey} secure
                       placeholder="SENSITOR_API_TOKEN" autoCapitalize="none" />
              )}

              <Pressable
                onPress={submit}
                disabled={busy || !email.trim()}
                style={({ pressed }) => [
                  styles.button,
                  (busy || !email.trim()) && styles.buttonDisabled,
                  pressed && styles.buttonPressed,
                ]}
              >
                {busy
                  ? <ActivityIndicator color="#FFFFFF" />
                  : <Text style={styles.buttonText}>Sign in</Text>}
              </Pressable>
            </>
          ) : null}

          {error ? <Text style={styles.error}>{error}</Text> : null}
        </Card>

        {/* What this deployment is, stated rather than assumed. An access
            mode nobody can see is how a server ends up open with a text box
            for a login. */}
        {meta ? (
          <Note
            text={
              !canSignIn
                ? 'This server runs in single-user mode with no API key configured, '
                  + 'so it issues no sessions. Set SENSITOR_API_TOKEN on the server, '
                  + 'or run it with SENSITOR_AUTH=multi.'
                : multiUser
                  ? 'Multi-user mode. Accounts are protected by a password, sessions '
                    + 'expire, and no account can reach another\'s data.'
                  : 'Single-user mode. Your email is a label for your data; the API '
                    + 'key is what authorises this device.'
            }
          />
        ) : (
          <Note text="Could not reach that server yet. Check the address and that it is running." />
        )}

        {meta ? (
          <Text style={styles.version}>
            {meta.product} {meta.version} · schema {meta.schema_version}
          </Text>
        ) : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function Field({ label, value, onChange, placeholder, secure, autoCapitalize, keyboardType }: {
  label: string;
  value: string;
  onChange(next: string): void;
  placeholder?: string;
  secure?: boolean;
  autoCapitalize?: 'none' | 'sentences';
  keyboardType?: 'default' | 'email-address';
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor={INK_FAINT}
        secureTextEntry={secure}
        autoCapitalize={autoCapitalize ?? 'sentences'}
        autoCorrect={false}
        keyboardType={keyboardType ?? 'default'}
        style={styles.input}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: BG },
  scroll: { padding: 20, paddingBottom: 60 },
  form: { gap: 14, marginTop: 6 },
  field: { gap: 6 },
  fieldLabel: { fontSize: 11, color: INK_MUTED, fontWeight: '600' },
  input: {
    backgroundColor: SURFACE_3,
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: RADIUS_SM,
    paddingHorizontal: 12,
    paddingVertical: 11,
    color: INK,
    fontSize: 14,
  },
  button: {
    backgroundColor: ACCENT,
    borderRadius: RADIUS_SM,
    paddingVertical: 13,
    alignItems: 'center',
    marginTop: 4,
  },
  buttonDisabled: { opacity: 0.45 },
  buttonPressed: { opacity: 0.85 },
  buttonText: { color: '#FFFFFF', fontWeight: '700', fontSize: 14 },
  error: { color: '#E2504F', fontSize: 12, lineHeight: 17 },
  version: { fontSize: 10, color: INK_FAINT, textAlign: 'center', marginTop: 18 },
});
