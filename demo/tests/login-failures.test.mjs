import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const mini = 'qingye/miniprogram/';
function library() {
  let mode = 404;
  const installed = [],
    routes = [];
  const module = { exports: {} };
  const script = read('coursework/library-management-system/frontend/src/views/login/Login.vue')
    .match(/<script>([\s\S]*?)<\/script>/)[1]
    .replace(/^import .*;?$/gm, '')
    .replace('export default', 'module.exports =');
  vm.runInNewContext(script, {
    module,
    setToken: (token) => installed.push(token),
    request: {
      post: async () => {
        if (typeof mode === 'number')
          throw { response: { status: mode, data: '<html>proxy error</html>' } };
        if (mode === 'timeout') throw { code: 'ECONNABORTED' };
        if (mode === 'network') throw Error('offline');
        if (mode === 'invalid') return { data: { code: 200, data: {} } };
        if (mode === 'credentials') return { data: { code: 400, msg: '密码错误' } };
        return { data: { code: 200, data: { token: 'test-only-session', role: 2 } } };
      },
    },
  });
  const state = module.exports.data();
  for (const [name, method] of Object.entries(module.exports.methods))
    state[name] = method.bind(state);
  state.$message = { error() {}, success() {} };
  state.$router = { push: (route) => routes.push(route) };
  state.act = '  zhangsan  ';
  state.pwd = ' keep spaces ';
  return {
    state,
    installed,
    routes,
    setMode(value) {
      mode = value;
    },
  };
}
function qingye() {
  let mode = 404,
    page;
  const installed = [],
    routes = [],
    native = { logout: 0, toast: 0, token: '' };
  const wx = {
    getStorageSync: () => native.token,
    showToast() {
      native.toast++;
    },
    switchTab: ({ url }) => routes.push(url),
    login: ({ success }) => success({ code: 'test-only-code' }),
    request(options) {
      queueMicrotask(() => {
        if (mode === 'network' || mode === 'timeout')
          return options.fail({ errMsg: 'request:fail ' + mode });
        if (typeof mode === 'number')
          return options.success({ statusCode: mode, data: '<html>proxy error</html>' });
        let data = options.url.endsWith('/options')
          ? { demoUsers: [{ id: 1, name: '张三' }] }
          : { token: 'test-only-session', user: { id: 1 } };
        if (mode === 'invalid') data = {};
        options.success({ statusCode: 200, data: { code: 0, data } });
      });
    },
  };
  const app = {
    logout() {
      native.logout++;
    },
    setSession: (session) => installed.push(session),
  };
  function load(file, require = () => ({ baseUrl: '' })) {
    const module = { exports: {} };
    vm.runInNewContext(read(mini + file), { module, require, wx, getApp: () => app });
    return module.exports;
  }
  const transport = load('utils/request.js'),
    mapping = load('utils/request-error.js');
  vm.runInNewContext(read(mini + 'pages/login/index.js'), {
    wx,
    getApp: () => app,
    require: (name) => (name.endsWith('request-error') ? mapping : transport),
    Page(value) {
      page = value;
      page.setData = (data) => Object.assign(page.data, data);
    },
  });
  return {
    page,
    native,
    installed,
    routes,
    transport,
    setMode(value) {
      mode = value;
    },
  };
}
function dormitory() {
  let mode = 404;
  const nodes = new Map(),
    installed = [],
    timers = new Map();
  let timerId = 0;
  const node = (id) => {
    if (!nodes.has(id))
      nodes.set(id, {
        value: '',
        hidden: id === 'loginFailure',
        disabled: false,
        dataset: {},
        textContent: '',
        classList: { add() {}, remove() {} },
        setAttribute() {},
        removeAttribute() {},
        addEventListener() {},
        focus() {},
      });
    return nodes.get(id);
  };
  const window = { location: { origin: 'http://local.test', href: '' } };
  const context = {
    document: { getElementById: node, querySelector: () => ({}) },
    window,
    AbortController,
    sessionStorage: { setItem: (...value) => installed.push(value) },
    setTimeout(callback) {
      const id = ++timerId;
      timers.set(id, callback);
      return id;
    },
    clearTimeout(id) {
      timers.delete(id);
    },
    fetch: async (_url, options) => {
      if (mode === 'timeout') {
        [...timers.values()][0]();
        assert.equal(options.signal.aborted, true);
        throw Object.assign(Error('timeout'), { name: 'AbortError' });
      }
      if (mode === 'network') throw Error('offline');
      const status = typeof mode === 'number' ? mode : 200;
      return {
        status,
        ok: status === 200,
        text: async () =>
          mode === 'invalid' || status !== 200
            ? '<html>proxy error</html>'
            : JSON.stringify({ id: 3, username: 'student', role: 'STUDENT' }),
      };
    },
  };
  vm.runInNewContext(
    read(
      'independent-projects/dormitory-management-system/src/main/resources/static/login.html'
    ).match(/<script>([\s\S]*?)<\/script>/)[1] + '\nthis.submitLogin = doLogin;',
    context
  );
  node('username').value = 'student';
  node('password').value = ' keep spaces ';
  return {
    node,
    installed,
    window,
    submit: context.submitLogin,
    setMode(value) {
      mode = value;
    },
  };
}
for (const status of [403, 404, 429, 500, 502, 503, 504]) {
  test(`three login pages classify HTTP ${status}, including an HTML error body, and permit recovery`, async () => {
    const lib = library();
    lib.setMode(status);
    await lib.state.login();
    assert.equal(lib.state.failure.code, String(status));
    assert.equal(lib.state.loading, false);
    assert.equal(lib.installed.length, 0);
    assert.equal(lib.state.pwd, ' keep spaces ');
    lib.setMode('success');
    await lib.state.login();
    assert.equal(lib.state.failure, null);
    assert.equal(lib.routes[0], '/user');
    const q = qingye();
    q.setMode(status);
    await q.page.onLoad();
    assert.equal(q.page.data.failure.code, String(status));
    assert.equal(q.page.data.busy, false);
    assert.equal(q.native.toast, 0);
    q.setMode('success');
    await q.page.retry();
    assert.equal(q.page.data.failure, null);
    assert.equal(q.page.data.accounts.length, 1);
    q.setMode(status);
    await q.page.login('/auth/demo', { userId: 1 });
    assert.equal(q.page.data.failure.code, String(status));
    assert.equal(q.installed.length, 0);
    q.setMode('success');
    await q.page.retry();
    assert.equal(q.installed.length, 1);
    assert.equal(q.routes.length, 1);
    const dorm = dormitory();
    dorm.setMode(status);
    await dorm.submit();
    assert.equal(dorm.node('failureCode').textContent, status);
    assert.equal(dorm.node('loginFailure').hidden, false);
    assert.equal(dorm.node('loginBtn').disabled, false);
    assert.equal(dorm.installed.length, 0);
    assert.equal(dorm.node('password').value, ' keep spaces ');
    dorm.setMode('success');
    await dorm.submit();
    assert.equal(dorm.node('loginFailure').hidden, true);
    assert.equal(dorm.installed.length, 1);
  });
}
for (const kind of ['network', 'timeout', 'invalid']) {
  test(`three login pages distinguish ${kind} without installing an incomplete session`, async () => {
    const code = kind === 'network' ? '连接失败' : kind === 'timeout' ? '连接超时' : '响应异常';
    const lib = library();
    lib.setMode(kind);
    await lib.state.login();
    assert.equal(lib.state.failure.code, code);
    assert.equal(lib.installed.length, 0);
    const q = qingye();
    q.setMode(kind);
    await q.page.login('/auth/demo', { userId: 1 });
    assert.equal(q.page.data.failure.code, code);
    assert.equal(q.installed.length, 0);
    const dorm = dormitory();
    dorm.setMode(kind);
    await dorm.submit();
    assert.equal(dorm.node('failureCode').textContent, code);
    assert.equal(dorm.installed.length, 0);
  });
}
test('incorrect credentials remain on the editable login form', async () => {
  const lib = library();
  lib.setMode('credentials');
  await lib.state.login();
  assert.equal(lib.state.failure, null);
  assert.equal(lib.state.loginMessage, '密码错误');
  lib.setMode(401);
  await lib.state.login();
  assert.equal(lib.state.failure, null);
  assert.match(lib.state.loginMessage, /账号或密码/);
  const dorm = dormitory();
  dorm.setMode(401);
  await dorm.submit();
  assert.equal(dorm.node('loginFailure').hidden, true);
  assert.match(dorm.node('msg').textContent, /用户名或密码/);
  const q = qingye();
  q.native.token = 'existing-test-session';
  q.setMode(401);
  await q.page.login('/auth/demo', { userId: 1 });
  assert.equal(q.native.logout, 0);
  assert.equal(q.page.data.failure.code, '401');
  await assert.rejects(q.transport.request('/me'));
  assert.equal(q.native.logout, 1);
});
test('library public login 401 stays on the login form; an expired protected request still signs out', async () => {
  let onRequest,
    onError,
    cleared = 0;
  const routes = [];
  const client = {
    interceptors: {
      request: {
        use(fn) {
          onRequest = fn;
        },
      },
      response: {
        use(_fn, error) {
          onError = error;
        },
      },
    },
  };
  const script = read('coursework/library-management-system/frontend/src/utils/request.js')
    .replace(/^import .*;?$/gm, '')
    .replace('export default request;', '');
  vm.runInNewContext(script, {
    process: { env: {} },
    axios: { create: () => client },
    getToken: () => 'current-test-session',
    clearTokenIfCurrent: () => {
      cleared++;
      return true;
    },
    router: { push: (route) => routes.push(route) },
  });
  const loginConfig = onRequest({ url: 'user/login', headers: {} });
  await assert.rejects(onError({ response: { status: 401 }, config: loginConfig }));
  assert.equal(cleared, 0);
  assert.equal(routes.length, 0);
  const protectedConfig = onRequest({ url: 'user/auth', headers: {} });
  await assert.rejects(onError({ response: { status: 401 }, config: protectedConfig }));
  assert.equal(cleared, 1);
  assert.equal(routes[0], '/login');
});
