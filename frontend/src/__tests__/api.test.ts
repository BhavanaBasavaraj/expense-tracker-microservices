import { afterEach, describe, expect, it, vi } from 'vitest';
import { registerUser } from '../api';

function stubFetch(status: number, body: unknown) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: async () => body,
  }));
}

const payload = { email: 'a@b.co', first_name: 'A', last_name: 'B', password: 'short' };

describe('API error messages', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('shows FastAPI validation errors (422 list) as readable text, not [object Object]', async () => {
    stubFetch(422, { detail: [{ loc: ['body', 'password'], msg: 'String should have at least 8 characters', type: 'string_too_short' }] });
    await expect(registerUser(payload)).rejects.toThrow('String should have at least 8 characters');
  });

  it('joins several validation messages', async () => {
    stubFetch(422, { detail: [{ msg: 'first problem' }, { msg: 'second problem' }] });
    await expect(registerUser(payload)).rejects.toThrow('first problem; second problem');
  });

  it('still shows plain string details', async () => {
    stubFetch(400, { detail: 'Email already registered' });
    await expect(registerUser(payload)).rejects.toThrow('Email already registered');
  });

  it('falls back when the body is not JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 502, json: async () => { throw new Error('not json'); } }));
    await expect(registerUser(payload)).rejects.toThrow('Registration failed');
  });
});
