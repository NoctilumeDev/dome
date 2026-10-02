const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../src/views/assistant/BookAssistant.vue'), 'utf8');
const script = source.match(/<script>([\s\S]*?)<\/script>/)[1].replace('export default', 'component =');
const sandbox = {}; vm.createContext(sandbox); vm.runInContext(script, sandbox);
const component = sandbox.component;
function instance(post) {
  const page = component.data();
  Object.assign(page, { $axios: { post }, $message: { warning() {}, error() {} } });
  for (const [name, fn] of Object.entries(component.methods)) page[name] = fn.bind(page);
  return page;
}
const verified = { data: { code: 200, data: { intent: 'MY_BORROWS', answer: '已核验', records: [{ bookName: 'Java' }], total: 12, returnedCount: 1, truncated: true, databaseVerified: true } } };
function deferred() { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; }

for (const mode of ['api', 'network']) test(`a ${mode} failure removes previously verified facts`, async () => {
  let failed = false;
  const page = instance(async () => {
    if (!failed) return verified;
    if (mode === 'api') return { data: { code: 400, msg: '失败' } };
    throw new Error('network');
  });
  page.question = '我的借阅'; await page.askQuestion(); assert.equal(page.databaseVerified, true);
  failed = true; page.question = '新问题'; await page.askQuestion();
  assert.equal(page.hasResult, false); assert.equal(page.databaseVerified, false);
  assert.equal(page.answer, ''); assert.equal(page.records.length, 0); assert.equal(page.total, 0);
});

test('rapid repeat cannot create competing requests and clears old facts while pending', async () => {
  const pending = deferred(); let calls = 0;
  const page = instance(() => { calls++; return pending.promise; });
  page.question = '我的借阅'; page.databaseVerified = true; page.answer = '旧答案';
  const first = page.askQuestion(); await page.askQuestion();
  assert.equal(calls, 1); assert.equal(page.databaseVerified, false); assert.equal(page.answer, '');
  pending.resolve(verified); await first; assert.equal(page.loading, false);
  assert.equal(page.total, 12); assert.equal(page.returnedCount, 1); assert.equal(page.truncated, true);
});

for (const mode of ['reset', 'destroy']) test(`${mode} invalidates an outstanding response`, async () => {
  const pending = deferred(); const page = instance(() => pending.promise);
  page.question = '我的借阅'; const first = page.askQuestion();
  if (mode === 'reset') page.resetForm(); else component.beforeDestroy.call(page);
  pending.resolve(verified); await first;
  assert.equal(page.hasResult, false); assert.equal(page.answer, '');
});

test('business records use their matching columns and plain text rendering', () => {
  const page = instance(); page.intent = 'MY_FEEDBACK';
  assert.equal(component.computed.recordColumns.call(page).some(c => c.prop === 'content'), true);
  assert.equal(page.formatRecordCell({}, { property: 'status' }, 1), '已回复');
  assert.equal(source.includes('v-html'), false);
});
