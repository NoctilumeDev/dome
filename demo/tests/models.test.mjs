import test from 'node:test';
import assert from 'node:assert/strict';
import { createLibraryModel } from '../library/adapter.mjs';
import { createDormitoryModel } from '../dormitory/adapter.mjs';
import { createQingyeModel } from '../qingye/model.mjs';
function memory() {
  const map = new Map();
  return { getItem: (key) => map.get(key) || null, setItem: (key, value) => map.set(key, value) };
}
test('library borrow/return updates availability exactly once and persists', () => {
  const storage = memory(),
    m = createLibraryModel(storage),
    start = m.handle('/book/query', 'POST', {}).data[0].availableCount;
  m.handle('/borrowRecord/borrow/1', 'POST');
  assert.throws(() => m.handle('/borrowRecord/borrow/1', 'POST'), /已经借阅/);
  assert.equal(m.handle('/book/query', 'POST', {}).data[0].availableCount, start - 1);
  m.handle('/borrowRecord/return/1', 'POST');
  assert.throws(() => m.handle('/borrowRecord/return/1', 'POST'), /已经归还/);
  assert.equal(
    createLibraryModel(storage).handle('/book/query', 'POST', {}).data[0].availableCount,
    start
  );
});
test('library zero-result queries and different reader records stay separate', () => {
  const m = createLibraryModel(memory());
  assert.equal(m.handle('/book/query', 'POST', { name: '123456' }).total, 0);
  m.handle('/borrowRecord/borrow/1', 'POST');
  m.switchRole(3);
  assert.equal(m.handle('/borrowRecord/query', 'POST', {}).total, 0);
  assert.throws(() => m.handle('/unknown', 'POST'), /未接入/);
});
test('dormitory student application can be approved from a staff role', () => {
  const m = createDormitoryModel(memory());
  m.handle('/move-in', 'POST', { reason: '新学期入住', preferredDormitoryId: 1 });
  m.switchRole(2);
  m.handle('/move-in/1/approve', 'PATCH');
  assert.equal(m.handle('/beds').find((b) => b.occupantId === 3).status, 'OCCUPIED');
  assert.throws(() => m.handle('/move-in/1/approve', 'PATCH'), /已处理/);
  m.switchRole(3);
  assert.throws(() => m.handle('/move-in', 'POST', { reason: '重复' }), /已有/);
});
test('qingye registration, read-all and selected trash restore retain their state', () => {
  const m = createQingyeModel(memory());
  m.handle('/activities/1/registration', 'POST');
  assert.equal(m.handle('/activities/1').myRegistration.status, 'REGISTERED');
  m.handle('/notifications/read-all', 'POST');
  assert.ok(m.handle('/notifications').every((n) => n.readAt));
  const first = m.handle('/notifications')[0].id,
    count = m.handle('/notifications').length;
  m.handle('/notifications/clear', 'POST', { ids: [first] });
  assert.equal(m.handle('/notifications').length, count - 1);
  assert.equal(m.handle('/notifications/trash').items.length, 1);
  m.handle('/notifications/restore', 'POST', { ids: [first] });
  assert.equal(m.handle('/notifications').length, count);
});
test('qingye member application and loan lifecycle work between identities', () => {
  const m = createQingyeModel(memory());
  m.handle('/clubs/1/join', 'POST');
  m.switchRole(2);
  m.handle('/clubs/1/members/1/decision', 'POST', { approve: true, role: 'MEMBER' });
  const a = m.handle('/activities/1');
  m.handle('/loans', 'POST', {
    activityId: 1,
    equipmentId: 1,
    quantity: 1,
    reason: '拍摄活动',
    plannedStart: a.startTime,
    plannedEnd: a.endTime,
  });
  m.switchRole(3);
  m.handle('/loans/1/decision', 'POST', { approve: true });
  m.handle('/loans/1/checkout', 'POST');
  assert.equal(m.handle('/equipment')[0].borrowedQuantity, 1);
  m.handle('/loans/1/return', 'POST');
  assert.equal(m.handle('/equipment')[0].borrowedQuantity, 0);
});
test('reset only resets one project and questions never contact a model', () => {
  const storage = memory(),
    library = createLibraryModel(storage),
    qingye = createQingyeModel(storage);
  library.handle('/borrowRecord/borrow/1', 'POST');
  qingye.handle('/activities/1/registration', 'POST');
  qingye.reset();
  assert.equal(createLibraryModel(storage).handle('/borrowRecord/query', 'POST', {}).total, 1);
  const answer = library.handle('/book/assistant/query', 'POST', {
    question: '三体放在哪里？',
  }).data;
  assert.equal(answer.modelCalled, false);
  assert.equal(answer.books[0].name, '三体');
});
