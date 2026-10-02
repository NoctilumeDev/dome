export const clone = (value) => JSON.parse(JSON.stringify(value));
export function createStore(name, seed, storage = globalThis.localStorage) {
  const key = `dome-demo-v1:${name}`;
  const fresh = { ...seed(), version: 1 };
  let data;
  try {
    data = JSON.parse(storage.getItem(key));
  } catch (_) {
    /* Start with fresh sample data. */
  }
  const valid =
    data &&
    data.version === 1 &&
    Object.entries(fresh).every(([field, sample]) =>
      Array.isArray(sample)
        ? Array.isArray(data[field]) &&
          data[field].every(
            (row) => row && typeof row === 'object' && Number.isInteger(row.id) && row.id > 0
          )
        : field === 'currentUserId'
        ? data[field] === null || Number.isInteger(data[field])
        : typeof data[field] === typeof sample
    ) &&
    data.users.length > 0 &&
    data.users.every((user) =>
      Object.entries(fresh.users[0]).every(
        ([field, sample]) => typeof user[field] === typeof sample
      )
    ) &&
    (data.currentUserId === null || data.users.some((user) => user.id === data.currentUserId));
  if (!valid) data = fresh;
  return {
    get data() {
      return data;
    },
    save() {
      try {
        storage.setItem(key, JSON.stringify(data));
      } catch (_) {
        /* Private browsing can use memory. */
      }
    },
    reset() {
      data = { ...seed(), version: 1 };
      this.save();
    },
    key,
  };
}
export function nextId(rows) {
  return Math.max(0, ...rows.map((row) => Number(row.id))) + 1;
}
export function requireRow(rows, id) {
  const row = rows.find((r) => Number(r.id) === Number(id));
  if (!row) throw new Error('这条演示记录已不存在，请刷新页面。');
  return row;
}
export function page(rows, query = {}) {
  const size = Math.max(1, Math.min(100, Number(query.size) || 10));
  const start = Math.max(0, (Number(query.current) || 1) - 1) * size;
  return { data: clone(rows.slice(start, start + size)), total: rows.length };
}
