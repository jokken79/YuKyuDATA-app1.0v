import { Auth } from '../../static/js/modules/auth.js';

describe('Auth module cookie-based session', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="login-modal" class="active"></div>
      <div id="login-error" style="display:none"></div>
      <form id="login-form">
        <input id="login-username" name="username" value="admin" />
        <input name="password" value="secret" />
        <button type="submit">Login</button>
      </form>
      <meta name="csrf-token" content="csrf-123" />
    `;

    global.fetch = jest.fn();
    jest.spyOn(window, 'dispatchEvent');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('checkSession uses verify endpoint with credentials include', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true });
    const uiCallback = jest.fn();

    await Auth.init(uiCallback);
    await Promise.resolve();

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/verify', {
      method: 'GET',
      credentials: 'include'
    });
  });

  test('handleLogin sends credentials include and does not store token in localStorage', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');

    const form = document.getElementById('login-form');
    form.username = form.querySelector('[name="username"]');
    form.password = form.querySelector('[name="password"]');
    await Auth.handleLogin({ preventDefault: jest.fn(), target: form });

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/login', expect.objectContaining({
      method: 'POST',
      credentials: 'include',
      headers: expect.objectContaining({ 'Content-Type': 'application/json' })
    }));
    expect(setItemSpy).not.toHaveBeenCalledWith('access_token', expect.anything());
  });



  test('fetchWithAuth includes CSRF header for mutating methods', async () => {
    global.fetch.mockResolvedValueOnce({ status: 200, ok: true });

    await Auth.fetchWithAuth('/api/v1/employees', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'x' })
    });

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/employees', expect.objectContaining({
      method: 'POST',
      credentials: 'include',
      headers: expect.objectContaining({
        'X-CSRF-Token': 'csrf-123'
      })
    }));
  });

  test('fetchWithAuth does not force CSRF header for GET requests', async () => {
    global.fetch.mockResolvedValueOnce({ status: 200, ok: true });

    await Auth.fetchWithAuth('/api/v1/employees', { method: 'GET' });

    const calledWith = global.fetch.mock.calls[0][1];
    expect(calledWith.headers['X-CSRF-Token']).toBeUndefined();
  });

  test('logout calls backend endpoint with credentials include', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true });

    await Auth.logout();

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/logout', expect.objectContaining({
      method: 'POST',
      credentials: 'include',
      headers: expect.objectContaining({
        'X-CSRF-Token': 'csrf-123'
      })
    }));
  });
});
