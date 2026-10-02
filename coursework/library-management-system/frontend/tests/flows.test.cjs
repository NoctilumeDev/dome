const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..', 'src');
const toQueryRange = vm.runInNewContext(fs.readFileSync(path.join(root, 'utils/queryTime.js'), 'utf8').replace('export function', 'function') + '\ntoQueryRange;', { Date });
function component(file, bindings = {}) {
  const source = fs.readFileSync(path.join(root, 'views', file), 'utf8');
  const script = source.match(/<script>([\s\S]*?)<\/script>/)[1].replace(/^import .*;?$/gm, '').replace('export default', 'module.exports =');
  const module = { exports: {} }; vm.runInNewContext(script, { module, toQueryRange, console, Date, ...bindings });
  const def = module.exports;
  const state = def.data();
  for (const [name, method] of Object.entries(def.methods)) state[name] = method.bind(state);
  state.$message = Object.assign(() => {}, { error() {}, success() {} });
  state.$swal = { fire() {} }; state.$swalConfirm = async () => true;
  return { state, def };
}
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };

test('calendar filter preserves the selected local day and inclusive bounds', () => {
  const dates = [new Date(2026, 9, 2), new Date(2026, 9, 3)];
  const range = toQueryRange(dates);
  assert.equal(range.startTime, '2026-10-02T00:00:00');
  assert.equal(range.endTime, '2026-10-03T23:59:59');
  assert.equal(toQueryRange(null).startTime, null);
});

for (const file of ['BookManage.vue', 'UserManage.vue', 'CategoryManage.vue', 'BookshelfManage.vue']) {
  test(file + ' single-row deletion does not include or change the existing selection', async () => {
    const { state } = component('admin/' + file);
    const selected = [{ id: 11 }, { id: 12 }]; state.selectedRows = selected;
    const sent = []; state.$axios = { post: async (url, ids) => { sent.push(Array.from(ids)); return { data: { code: 200 } }; } };
    state.fetchFreshData = state.fetchData = async () => {};
    await state.handleDelete({ id: 99, name: '只删这本', userName: '只删此人' });
    await new Promise(setImmediate);
    assert.deepEqual(sent, [[99]]);
    assert.equal(state.selectedRows, selected);
  });
}

test('late catalogue responses cannot replace a newer search', async () => {
  const { state } = component('user/BookBorrow.vue');
  const old = deferred(), recent = deferred(); let calls = 0;
  state.$axios = { post: () => (++calls === 1 ? old.promise : recent.promise) };
  const first = state.fetchBooks(); state.queryDto = { name: '三体' }; const second = state.fetchBooks();
  recent.resolve({ data: { code: 200, data: [{ id: 4, availableCount: 0 }], total: 1 } }); await second;
  old.resolve({ data: { code: 200, data: [{ id: 1 }], total: 5 } }); await first;
  assert.equal(state.bookTableData[0].id, 4);
  assert.equal(state.totalItems, 1);
  assert.equal(state.bookLoading, false);
});

test('catalogue failures clear obsolete rows and allow retry', async () => {
  const { state } = component('user/BookBorrow.vue'); state.bookTableData = [{ id: 1 }]; state.totalItems = 1;
  state.$axios = { post: async () => { throw Error('offline'); } }; await state.fetchBooks();
  assert.equal(state.bookTableData.length, 0); assert.equal(state.totalItems, 0); assert.ok(state.bookError);
  state.$axios.post = async () => ({ data: { code: 200, data: [{ id: 4 }], total: 1 } }); await state.fetchBooks();
  assert.equal(state.bookTableData[0].id, 4); assert.equal(state.bookError, '');
});

test('repeat borrowing while confirmation is open submits only once and releases its lock', async () => {
  const { state } = component('user/BookBorrow.vue'); const confirmation = deferred(); let sent = 0;
  state.$swalConfirm = () => confirmation.promise;
  state.$axios = { post: async () => { sent++; return { data: { code: 200 } }; } };
  state.fetchBooks = state.fetchBorrowRecords = () => {};
  const row = { id: 4, name: '三体', availableCount: 1 };
  const first = state.handleBorrow(row); await state.handleBorrow(row); confirmation.resolve(true); await first;
  assert.equal(sent, 1); assert.equal(state.pendingOperations.length, 0);
});

test('batch deletion keeps the IDs shown at confirmation even if selection changes', async () => {
  const { state } = component('admin/BookManage.vue'); const confirmation = deferred();
  state.selectedRows = [{ id: 11, name: '甲' }, { id: 12, name: '乙' }];
  let text; state.$swalConfirm = options => { text = options.text; return confirmation.promise; };
  const sent = []; state.$axios = { post: async (url, ids) => { sent.push(Array.from(ids)); return { data: { code: 200 } }; } };
  state.fetchFreshData = async () => {};
  const operation = state.batchDelete(); state.selectedRows = [{ id: 99, name: '丙' }];
  confirmation.resolve(true); await operation;
  assert.match(text, /2 本图书：甲、乙/); assert.deepEqual(sent, [[11, 12]]);
});

test('login trims the account, preserves the password and prevents duplicate requests', async () => {
  const response = deferred(); const sent = [], tokens = [], routes = [];
  const { state } = component('login/Login.vue', {
    request: { post: async (url, body) => { sent.push({ ...body }); return response.promise; } },
    setToken: token => tokens.push(token),
  });
  state.$router = { push: route => routes.push(route) }; state.act = '  admin  '; state.pwd = ' secret ';
  const first = state.login(); await state.login();
  assert.equal(sent.length, 1); assert.deepEqual(sent[0], { userAccount: 'admin', userPwd: ' secret ' });
  response.resolve({ data: { code: 200, data: { token: 'test-token', role: 0 } } }); await first;
  assert.deepEqual(tokens, ['test-token']); assert.deepEqual(routes, ['/admin']); assert.equal(state.loading, false);
});

test('failed login permits retry and never installs a session', async () => {
  let count = 0;
  const { state } = component('login/Login.vue', {
    request: { post: async () => { count++; throw Error('offline'); } },
    setToken: () => { throw Error('must not install failed session'); },
  });
  state.act = 'zhangsan'; state.pwd = '123456'; await state.login(); await state.login();
  assert.equal(count, 2); assert.equal(state.loading, false);
});

test('clearing filters returns every paged list to its first page', () => {
  for (const file of ['admin/BookManage.vue', 'admin/UserManage.vue', 'admin/BorrowManage.vue', 'admin/BookshelfManage.vue', 'admin/CategoryManage.vue', 'user/BookBorrow.vue', 'user/MyBorrows.vue']) {
    const { state } = component(file); state.currentPage = 5; let requestedPage;
    state.fetchFreshData = state.fetchData = state.fetchBooks = () => { requestedPage = state.currentPage; };
    const reset = state.resetQueryCondition || state.resetCondition;
    reset(); assert.equal(state.currentPage, 1, file); assert.equal(requestedPage, 1, file);
  }
});
