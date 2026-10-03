import assert from 'node:assert/strict';
import { test } from 'node:test';
import { build } from 'esbuild';

const bundle = await build({ entryPoints: ['src/api/client.ts'], bundle: true,
  write: false, format: 'esm', platform: 'node', define: { 'import.meta.env': '{}' } });
const client = await import('data:text/javascript;base64,' + Buffer.from(bundle.outputFiles[0].text).toString('base64'));

function storage() {
  const values = new Map();
  globalThis.localStorage = { getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) };
  return values;
}

test('MFA challenge does not authenticate or send an old tenant identity', async () => {
  const values = storage();
  values.set('sl_access_token', 'stale-token');
  values.set('sl_tenant_id', 'another-tenant');
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/v1/auth/login');
    assert.equal(options.headers.Authorization, undefined);
    assert.equal(options.headers['X-Tenant-ID'], undefined);
    return new Response(JSON.stringify({ access_token: '', mfa_required: true }));
  };
  const result = await client.login('owner@example.com', 'test-password');
  assert.equal(result.mfa_required, true);
  assert.equal(client.isLoggedIn(), false);
  assert.equal(values.get('sl_tenant_id'), undefined);
});

test('MFA completion forwards the code and stores only the returned token identity', async () => {
  const values = storage();
  const token = 'header.' + Buffer.from(JSON.stringify({ tenant_id: 'verified-tenant' })).toString('base64') + '.signature';
  globalThis.fetch = async (url, options) => {
    assert.equal(JSON.parse(options.body).mfa_code, '123456');
    return new Response(JSON.stringify({ access_token: token, mfa_required: false }));
  };
  await client.login('owner@example.com', 'test-password', ' 123456 ');
  assert.equal(values.get('sl_access_token'), token);
  assert.equal(values.get('sl_tenant_id'), 'verified-tenant');
});

test('failed MFA does not create a local authenticated session', async () => {
  storage();
  globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'Invalid MFA code' }), { status: 401 });
  await assert.rejects(client.login('owner@example.com', 'test-password', 'invalid'));
  assert.equal(client.isLoggedIn(), false);
});

test('registration does not send a stale session or assign tenant context before login', async () => {
  const values = storage();
  values.set('sl_access_token', 'stale-token');
  globalThis.fetch = async (url, options) => {
    assert.equal(options.headers.Authorization, undefined);
    assert.equal(JSON.parse(options.body).tenant_id, 'new-workspace');
    return new Response(JSON.stringify({ id: 'registered' }));
  };
  await client.register('owner@example.com', 'test-password', 'Owner', 'new-workspace');
  assert.equal(values.get('sl_tenant_id'), undefined);
});
