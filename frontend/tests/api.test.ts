import test from 'node:test';
import assert from 'node:assert/strict';
import { loadJob } from '../src/api.ts';

test('stalled job exits with a retry error instead of polling forever', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ job_id: 'stalled', status: 'loading' });
  try {
    await assert.rejects(loadJob('/api/schedule/2024', undefined, new AbortController().signal, 20), /time limit.*retry/i);
  } finally { globalThis.fetch = original; }
});
test('job timeout also aborts a fetch that never returns', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (_url, init) => new Promise((_resolve, reject) => {
    init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true });
  });
  try {
    await assert.rejects(loadJob('/api/schedule/2024', undefined, new AbortController().signal, 20), /time limit.*retry/i);
  } finally { globalThis.fetch = original; }
});
test('successful jobs return data and user cancellation remains an AbortError', async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => Response.json(++calls === 1 ? { job_id: 'ready' } : { status: 'done', data: ['Bahrain'] });
  try {
    assert.deepEqual(await loadJob('/api/schedule/2024', undefined, new AbortController().signal, 100), { id: 'ready', data: ['Bahrain'] });
    const controller = new AbortController(); controller.abort();
    await assert.rejects(loadJob('/api/schedule/2024', undefined, controller.signal, 100), { name: 'AbortError' });
  } finally { globalThis.fetch = original; }
});
