/**
 * The client against a live server.
 *
 * Typechecking proves the shapes line up with what this file claims. It does
 * not prove they line up with what the server sends — that needs a real
 * request, which is what this does. Run it with a uvicorn process on
 * SENSITOR_API_URL.
 *
 *   npx tsx mobile/tests/integration.ts
 */

import { ApiError, SensitorClient } from '../src/api/client';

const BASE = process.env.SENSITOR_API_URL ?? 'http://localhost:8610';
const EMAIL = process.env.SENSITOR_TEST_EMAIL ?? 'phone@example.com';
const PASSWORD = process.env.SENSITOR_TEST_PASSWORD ?? 'correct-horse-battery';

let passed = 0;
let failed = 0;

function check(name: string, condition: boolean, detail = ''): void {
  if (condition) {
    passed += 1;
    console.log(`  ok    ${name}`);
  } else {
    failed += 1;
    console.log(`  FAIL  ${name}${detail ? `   ${detail}` : ''}`);
  }
}

async function main(): Promise<number> {
  let signedOutCalls = 0;
  const client = new SensitorClient({
    baseUrl: BASE,
    onUnauthenticated: () => { signedOutCalls += 1; },
  });

  console.log('\nMeta and health');
  const health = await client.health();
  check('health responds', health.status === 'ok');
  const meta = await client.meta();
  check('meta reports the schema version', meta.schema_version >= 3);
  check('and the auth mode', meta.auth_mode === 'multi');
  check('and that sessions are available', meta.issues_sessions === true);

  console.log('\nUnauthenticated access');
  try {
    await client.overview();
    check('an unauthenticated request is refused', false);
  } catch (error) {
    const api = error as ApiError;
    check('an unauthenticated request is refused', api.unauthenticated);
    check('and the callback fired once', signedOutCalls === 1);
  }

  console.log('\nSign in');
  const wrong = new SensitorClient({ baseUrl: BASE });
  try {
    await wrong.signIn(EMAIL, 'not-the-password');
    check('a wrong password is refused', false);
  } catch (error) {
    check('a wrong password is refused', (error as ApiError).status === 401);
  }

  const session = await client.signIn(EMAIL, PASSWORD);
  check('a correct password returns a token', session.token.length > 20);
  check('and the client keeps it', client.getToken() === session.token);
  const me = await client.me();
  check('the token identifies the right person', me.email === EMAIL);

  console.log('\nOverview in one request');
  const started = Date.now();
  const overview = await client.overview({ period: 'ALL' });
  const firstMs = Date.now() - started;
  check('metrics arrive', overview.metrics.n > 0, `n=${overview.metrics.n}`);
  check('an equity curve arrives', overview.equity.length > 0);
  check('it is thinned for a phone', overview.equity.length <= 400,
        `${overview.equity.length} points for ${overview.metrics.n} trades`);
  check('a breakdown arrives', overview.by_symbol.length > 0);
  check('every breakdown row carries its sample size',
        overview.by_symbol.every((r) => typeof r.n === 'number' && r.n > 0));
  check('and whether it is reliable',
        overview.by_symbol.every((r) => typeof r.reliable === 'boolean'));
  check('accounts arrive', overview.accounts.length === 1);
  check('the payload states that undefined is null',
        overview.notes.undefined_is_null === true);

  console.log('\nETag caching');
  const again = Date.now();
  const cached = await client.overview({ period: 'ALL' });
  const secondMs = Date.now() - again;
  check('a repeat returns the same etag', cached.etag === overview.etag);
  check('with the same metrics', cached.metrics.n === overview.metrics.n);
  check('and is faster than the first fetch', secondMs <= firstMs,
        `${firstMs}ms then ${secondMs}ms`);

  console.log('\nIncremental sync');
  const first = await client.tradeDelta(null, 50);
  check('a first page arrives', first.trades.length === 50);
  check('it carries a server cursor', first.server_time.length > 0);
  check('and says it is incomplete', first.complete === false);

  const nothingNew = await client.tradeDelta(first.server_time, 50);
  check('nothing has changed since the cursor', nothingNew.count === 0,
        `got ${nothingNew.count}`);
  check('and that page is complete', nothingNew.complete === true);

  console.log('\nUndefined survives as null');
  const trades = first.trades;
  const withoutStop = trades.filter((t) => t.stop_loss === null);
  check('some trades had no stop', withoutStop.length > 0);
  check('and their R is null, not zero',
        withoutStop.every((t) => t.r_multiple === null));
  check('r_coverage is reported',
        overview.metrics.r_coverage !== null && overview.metrics.r_coverage < 1);

  console.log('\nFindings are passed through verbatim');
  const findings = await client.findings();
  check('findings arrive', findings.length > 0, `${findings.length}`);
  for (const finding of findings) {
    check(`'${finding.key}' states it is a correlation`,
          finding.en.toLowerCase().includes('correlation')
          && finding.fr.toLowerCase().includes('corrélation'));
    check(`'${finding.key}' carries its sample size`,
          finding.n > 0 && finding.en.includes(String(finding.n)));
    check(`'${finding.key}' is marked as a correlation`,
          finding.interpretation === 'correlation');
  }

  console.log('\nSign out');
  await client.signOut();
  check('the token is dropped', client.getToken() === null);
  try {
    await client.overview();
    check('the old session no longer works', false);
  } catch (error) {
    check('the old session no longer works', (error as ApiError).unauthenticated);
  }

  console.log('\nUnreachable server');
  const offline = new SensitorClient({ baseUrl: 'http://127.0.0.1:59999', timeoutMs: 2000 });
  try {
    await offline.health();
    check('an unreachable server raises', false);
  } catch (error) {
    const api = error as ApiError;
    check('an unreachable server raises', api instanceof ApiError);
    check('and is flagged offline rather than as a failure', api.offline === true);
    check('with status 0 so a screen can tell the difference', api.status === 0);
  }

  console.log(`\n${passed + failed} checks, ${failed} failures`);
  return failed === 0 ? 0 : 1;
}

main().then((code) => process.exit(code)).catch((error) => {
  console.error('\nthe suite itself failed:', error);
  process.exit(1);
});
