import { createStore, clone, nextId, requireRow, page } from '../shared/store.mjs';
const dateText = (time = Date.now()) => new Date(time).toISOString().replace('T', ' ').slice(0, 19);

export function librarySeed() {
  const users = [
    { id: 1, userAccount: 'admin', userName: '管理员', userRole: 1 },
    { id: 2, userAccount: 'zhangsan', userName: '张三', userRole: 2 },
    { id: 3, userAccount: 'lisi', userName: '李四', userRole: 2 },
  ].map((u) => ({
    ...u,
    userAvatar: '',
    isLogin: true,
    isWord: false,
    createTime: '2026-09-01 10:00:00',
  }));
  const categories = [
    { id: 1, name: '文学' },
    { id: 2, name: '科幻' },
    { id: 3, name: '计算机' },
  ];
  const shelves = [
    { id: 1, name: '文学书架', location: '一楼 A 区', capacity: 100 },
    { id: 2, name: '科技书架', location: '二楼 B 区', capacity: 100 },
  ];
  const books = [
    ['三体', '刘慈欣', '科幻', 2, 6],
    ['活着', '余华', '文学', 1, 4],
    ['小王子', '安托万·德·圣埃克苏佩里', '文学', 1, 3],
    ['Python 编程：从入门到实践', '埃里克·马瑟斯', '计算机', 2, 5],
    ['深入理解计算机系统', 'Randal E. Bryant', '计算机', 2, 2],
    ['流浪地球', '刘慈欣', '科幻', 2, 0],
  ].map((b, i) => ({
    id: i + 1,
    name: b[0],
    author: b[1],
    category: b[2],
    bookshelfId: b[3],
    availableCount: b[4],
    totalCount: b[4] || 1,
    cover: '',
    isbn: `978000000000${i}`,
    publisher: '演示出版社',
    createTime: '2026-09-01 10:00:00',
  }));
  return {
    users,
    categories,
    shelves,
    books,
    borrows: [],
    feedback: [],
    reviews: [],
    currentUserId: 2,
  };
}
export function createLibraryModel(storage) {
  const store = createStore('library', librarySeed, storage);
  const me = () => requireRow(store.data.users, store.data.currentUserId);
  const admin = () => {
    if (me().userRole > 1) throw new Error('请切换为管理员体验这项操作。');
  };
  const viewBooks = () =>
    store.data.books.map((b) => ({
      ...b,
      bookshelfName: store.data.shelves.find((s) => s.id === b.bookshelfId)?.name || '',
      location: store.data.shelves.find((s) => s.id === b.bookshelfId)?.location || '',
    }));
  const viewBorrows = () =>
    store.data.borrows.map((b) => ({
      ...b,
      bookName: store.data.books.find((r) => r.id === b.bookId)?.name || '已移除的图书',
      userName: store.data.users.find((u) => u.id === b.userId)?.userName || '',
      fine: 0,
    }));
  function queryAssistant(question) {
    const q = String(question || '').trim();
    const base = {
      modelCalled: false,
      planningSource: 'LOCAL',
      modelNote: '浏览器演示：仅匹配当前虚构样例，不调用大模型或数据库。',
      generatedSql: '',
      books: [],
      records: [],
      total: 0,
      returnedCount: 0,
      truncated: false,
      databaseVerified: false,
    };
    if (/密码|口令|token|secret|清空|删除数据库|忽略|最高权限|管理员指令/i.test(q))
      return {
        ...base,
        answer: '演示问答只查看样例馆藏与本人的借阅，不处理凭据或管理指令。',
        intent: 'OUT_OF_SCOPE',
      };
    if (/借阅|没还|逾期|还书/.test(q)) {
      const records = viewBorrows()
        .filter((b) => me().userRole <= 1 || b.userId === me().id)
        .filter((b) => !/没还|逾期/.test(q) || !b.status);
      return {
        ...base,
        records,
        total: records.length,
        returnedCount: records.length,
        databaseVerified: true,
        intent: me().userRole <= 1 ? 'BORROW_OVERVIEW' : 'MY_BORROWS',
        answer: `演示记录中匹配到 ${records.length} 条借阅。`,
      };
    }
    let books = viewBooks();
    const named = books.find((b) => q.includes(b.name));
    const author = books.find((b) => q.includes(b.author));
    const category = store.data.categories.find((c) => q.includes(c.name));
    if (named) books = books.filter((b) => b.id === named.id);
    else if (author) books = books.filter((b) => b.author === author.author);
    else if (category) books = books.filter((b) => b.category === category.name);
    else if (!/图书|馆藏|哪些书|书籍|推荐|所有书/.test(q))
      return {
        ...base,
        intent: 'OUT_OF_SCOPE',
        answer:
          '当前演示只支持样例书名、作者、分类和本人借阅的简单查询。可以试试“《三体》放在哪里？”',
      };
    return {
      ...base,
      books,
      total: books.length,
      returnedCount: books.length,
      databaseVerified: true,
      intent: 'SEARCH_BOOK',
      answer: `演示馆藏中匹配到 ${books.length} 本图书。`,
    };
  }
  function handle(path, method = 'GET', body = {}) {
    path = '/' + path.replace(/^\/+/, '').split('?')[0];
    const d = store.data;
    let result;
    if (path === '/user/login') {
      const u = d.users.find((r) => r.userAccount === body.userAccount);
      if (!u || body.userPwd !== '123456')
        throw new Error('演示账号：admin、zhangsan、lisi；密码为 123456。');
      d.currentUserId = u.id;
      result = { token: demoToken(u), role: u.userRole };
    } else if (path === '/user/auth') result = me();
    else if (path === '/user/register') throw new Error('在线演示使用预置身份，可从顶部直接切换。');
    else if (path === '/book/assistant/query') result = queryAssistant(body.question);
    else if (/^\/borrowRecord\/borrow\/\d+$/.test(path)) {
      const b = requireRow(d.books, path.split('/').pop());
      if (d.borrows.some((r) => r.bookId === b.id && r.userId === me().id && !r.status))
        throw new Error('这本书你已经借阅了。');
      if (b.availableCount < 1) throw new Error('当前暂无可借余量。');
      b.availableCount--;
      d.borrows.unshift({
        id: nextId(d.borrows),
        bookId: b.id,
        userId: me().id,
        borrowTime: dateText(),
        dueDate: dateText(Date.now() + 30 * 86400000),
        returnTime: null,
        status: false,
      });
      result = null;
    } else if (/^\/borrowRecord\/return\/\d+$/.test(path)) {
      const r = requireRow(d.borrows, path.split('/').pop());
      if (r.userId !== me().id) admin();
      if (r.status) throw new Error('这条记录已经归还。');
      requireRow(d.books, r.bookId).availableCount++;
      r.status = true;
      r.returnTime = dateText();
      result = null;
    } else if (path === '/borrowRecord/query') {
      let rows = viewBorrows().filter((r) => me().userRole <= 1 || r.userId === me().id);
      if (body.userId) rows = rows.filter((r) => r.userId === Number(body.userId));
      if (body.status !== undefined && body.status !== null && body.status !== '')
        rows = rows.filter((r) => r.status === Boolean(body.status));
      if (body.bookName) rows = rows.filter((r) => r.bookName.includes(body.bookName));
      if (body.userName) rows = rows.filter((r) => r.userName.includes(body.userName));
      if (body.overdue) rows = rows.filter((r) => !r.status && new Date(r.dueDate) < new Date());
      return { code: 200, msg: '演示查询完成', ...page(rows, body) };
    } else if (path === '/book/query') {
      let rows = viewBooks();
      for (const key of ['name', 'author', 'category', 'isbn'])
        if (body[key]) rows = rows.filter((r) => String(r[key]).includes(String(body[key])));
      return { code: 200, msg: '演示查询完成', ...page(rows, body) };
    } else if (['/category/queryAll', '/bookshelf/queryAll'].includes(path))
      result = path.startsWith('/category') ? d.categories : d.shelves;
    else if (
      /^\/(book|category|bookshelf|user)\/(query|save|insert|update|backUpdate|batchDelete)$/.test(
        path
      )
    ) {
      admin();
      const [, kind, action] = path.split('/');
      const key = { book: 'books', category: 'categories', bookshelf: 'shelves', user: 'users' }[
        kind
      ];
      if (kind === 'book' && ['save', 'insert', 'update'].includes(action)) {
        const book = body.id ? { ...requireRow(d.books, body.id), ...body } : body;
        const borrowed = d.borrows.filter((r) => r.bookId === book.id && !r.status).length;
        const available = book.availableCount ?? book.totalCount;
        if (
          !Number.isInteger(book.totalCount) ||
          !Number.isInteger(available) ||
          book.totalCount < 0 ||
          available < 0 ||
          available > book.totalCount - borrowed
        )
          throw new Error('请填写非负整数库存，可借数量不能超过总量减去未归还借阅。');
        body = { ...body, availableCount: available };
      }
      if (action === 'query') {
        let rows = d[key];
        for (const field of ['name', 'userName', 'userAccount'])
          if (body[field]) rows = rows.filter((r) => String(r[field] || '').includes(body[field]));
        return { code: 200, msg: '演示查询完成', ...page(rows, body) };
      }
      if (action === 'batchDelete') {
        if (kind === 'book' && d.borrows.some((r) => !r.status && body.includes(r.bookId)))
          throw new Error('有未归还借阅的图书不能删除。');
        if (kind === 'user' && body.includes(me().id)) throw new Error('不能删除当前演示身份。');
        d[key] = d[key].filter((r) => !body.includes(r.id));
      } else if (['update', 'backUpdate'].includes(action))
        Object.assign(requireRow(d[key], body.id), body);
      else d[key].push({ ...body, id: nextId(d[key]), createTime: new Date().toISOString() });
      result = null;
    } else if (/^\/(feedback|review)\/(mine|query)$/.test(path)) {
      const kind = path.split('/')[1],
        mine = path.endsWith('/mine');
      if (!mine) admin();
      const rows = d[kind === 'review' ? 'reviews' : 'feedback'].filter(
        (r) => !mine || r.userId === me().id
      );
      return { code: 200, msg: '演示查询完成', ...page(rows, body) };
    } else if (/^\/(feedback|review)\/submit$/.test(path)) {
      const kind = path.split('/')[1],
        rows = d[kind === 'review' ? 'reviews' : 'feedback'];
      rows.unshift({
        ...body,
        id: nextId(rows),
        userId: me().id,
        userName: me().userName,
        bookName: d.books.find((b) => b.id === Number(body.bookId))?.name,
        status: 0,
        reply: '',
        createTime: new Date().toISOString(),
      });
      result = null;
    } else if (path === '/feedback/reply') {
      admin();
      Object.assign(requireRow(d.feedback, body.id), { reply: body.reply, status: 1 });
      result = null;
    } else if (path === '/review' && method === 'PUT') {
      const row = requireRow(d.reviews, body.id);
      if (row.userId !== me().id) admin();
      Object.assign(row, body);
      result = null;
    } else if (/^\/(feedback|review)\/\d+$/.test(path) && method === 'DELETE') {
      const key = path.startsWith('/review') ? 'reviews' : 'feedback';
      const row = requireRow(d[key], path.split('/').pop());
      if (row.userId !== me().id) admin();
      d[key] = d[key].filter((r) => r !== row);
      result = null;
    } else throw new Error('这项功能未接入浏览器演示，请查看完整项目源码。');
    store.save();
    return { code: 200, msg: '演示操作完成', data: clone(result) };
  }
  return {
    store,
    handle,
    me,
    switchRole(id) {
      store.data.currentUserId = Number(id);
      store.save();
    },
    reset() {
      store.reset();
    },
  };
}
export function demoToken(user) {
  const encode = (value) =>
    btoa(JSON.stringify(value)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode({
    id: user.id,
    role: user.userRole,
    exp: 4102444800,
  })}.demo`;
}
export function createLibraryAdapter() {
  const model = createLibraryModel();
  function session() {
    sessionStorage.setItem('token', demoToken(model.me()));
    sessionStorage.removeItem('active_key');
  }
  session();
  window.DomeDemo.configure({
    roles: [
      { id: 2, label: '张三 · 读者' },
      { id: 3, label: '李四 · 读者' },
      { id: 1, label: '管理员' },
    ],
    current: model.me().id,
    switchRole(id) {
      model.switchRole(id);
      session();
      location.hash = model.me().userRole <= 1 ? '/admin' : '/user';
      location.reload();
    },
    reset() {
      model.reset();
      session();
      location.hash = '/user';
      location.reload();
    },
  });
  return async (config) => {
    let body = config.data || {};
    if (typeof body === 'string') body = JSON.parse(body);
    let data;
    try {
      data = model.handle(config.url, (config.method || 'get').toUpperCase(), body);
    } catch (error) {
      data = { code: 400, msg: error.message };
    }
    return { data, status: 200, statusText: 'OK', headers: {}, config, request: null };
  };
}
