export const clone = (value) => JSON.parse(JSON.stringify(value));
export function createStore(name, seed, storage = globalThis.localStorage) {
  const key = `dome-demo-v1:${name}`;
  let data;
  try {
    data = JSON.parse(storage.getItem(key));
  } catch (_) {
    /* Start with fresh sample data. */
  }
  if (!data || data.version !== 1) data = { ...seed(), version: 1 };
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
