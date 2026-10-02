import { createStore, clone, nextId, requireRow } from '../shared/store.mjs';
export function dormitorySeed() {
  return {
    currentUserId: 3,
    users: [
      { id: 1, username: 'admin', fullName: '林老师', role: 'ADMIN' },
      { id: 2, username: 'manager', fullName: '王老师', role: 'DORM_MANAGER', building: { id: 1 } },
      { id: 3, username: 'student', fullName: '张三', role: 'STUDENT' },
      { id: 4, username: 'lisi', fullName: '李四', role: 'STUDENT' },
    ],
    buildings: [
      { id: 1, name: '一号宿舍楼', address: '校园东区' },
      { id: 2, name: '二号宿舍楼', address: '校园西区' },
    ],
    floors: [
      { id: 1, name: '一层', building: { id: 1 } },
      { id: 2, name: '二层', building: { id: 2 } },
    ],
    dormitories: [
      {
        id: 1,
        dormCode: '1-101',
        gender: 'MALE',
        capacity: 4,
        floor: { id: 1 },
        preferenceTags: '安静,早睡,整洁,阅读',
      },
      {
        id: 2,
        dormCode: '2-201',
        gender: 'MALE',
        capacity: 4,
        floor: { id: 2 },
        preferenceTags: '活跃,晚睡,整洁,运动',
      },
    ],
    beds: [
      { id: 1, dormitoryId: 1, bedNo: '01', status: 'OCCUPIED', occupantId: 4 },
      { id: 2, dormitoryId: 1, bedNo: '02', status: 'VACANT' },
      { id: 3, dormitoryId: 2, bedNo: '01', status: 'VACANT' },
      { id: 4, dormitoryId: 2, bedNo: '02', status: 'MAINTENANCE' },
    ],
    'move-in': [],
    'move-out': [],
    repairs: [
      {
        id: 1,
        studentId: 3,
        location: '一号楼公共自习室',
        description: '顶灯闪烁，请检查。',
        status: 'PENDING',
      },
    ],
    bills: [
      {
        id: 1,
        studentId: 3,
        month: '2026-10',
        electricity: 25,
        water: 10,
        otherFee: 0,
        total: 35,
        state: 'UNPAID',
      },
    ],
    notices: [
      {
        id: 1,
        title: '欢迎体验宿舍管理',
        content: '可以先申请入住，再切换管理身份审批；报修、账单与公告也可以体验。',
        scope: 'ALL',
      },
    ],
  };
}
export function createDormitoryModel(storage) {
  const store = createStore('dormitory', dormitorySeed, storage);
  const me = () => requireRow(store.data.users, store.data.currentUserId);
  const staff = () => {
    if (me().role === 'STUDENT') throw new Error('请切换到管理身份。');
  };
  const admin = () => {
    if (me().role !== 'ADMIN') throw new Error('请切换到管理员。');
  };
  function enriched(kind, row) {
    const d = store.data;
    const result = clone(row);
    const student = d.users.find((u) => u.id === row.studentId);
    if (student) {
      result.student = student.fullName;
      result.studentName = student.fullName;
    }
    if (kind === 'beds') {
      result.dormitory = d.dormitories.find((r) => r.id === row.dormitoryId)?.dormCode || '';
      result.dormitoryId = row.dormitoryId;
      result.occupantName = d.users.find((u) => u.id === row.occupantId)?.fullName || '';
    }
    if (kind === 'move-in')
      result.preferredDormitory =
        d.dormitories.find((r) => r.id === row.preferredDormitoryId)?.dormCode || '自动分配';
    if (kind === 'move-out') {
      const b = d.beds.find((r) => r.id === row.bedId);
      result.bed = b
        ? `${d.dormitories.find((r) => r.id === b.dormitoryId)?.dormCode} · ${b.bedNo}`
        : '';
    }
    if (kind === 'notices')
      result.building = d.buildings.find((r) => r.id === row.buildingId)?.name || '';
    return result;
  }
  function handle(path, method = 'GET', body = {}) {
    const url = new URL(path, 'https://demo.local');
    const parts = url.pathname.split('/').filter(Boolean),
      [kind, id, action] = parts;
    const d = store.data;
    let result;
    if (kind === 'auth') {
      if (id === 'login') {
        const u = d.users.find((r) => r.username === body.username);
        if (!u || body.password !== '123456')
          throw new Error('演示账号：admin / manager / student，密码 123456。');
        d.currentUserId = u.id;
        result = u;
      } else if (id === 'logout') {
        d.currentUserId = null;
        result = {};
      } else if (id === 'me') result = me();
      else throw new Error('在线演示使用预置账号，请从顶部切换身份。');
    } else if (kind === 'dashboard') {
      const occupied = d.beds.filter((b) => b.status === 'OCCUPIED').length;
      result = {
        totalBeds: d.beds.length,
        occupiedBeds: occupied,
        vacantBeds: d.beds.filter((b) => b.status === 'VACANT').length,
        maintenanceBeds: d.beds.filter((b) => b.status === 'MAINTENANCE').length,
        occupancyRate: Math.round((100 * occupied) / Math.max(1, d.beds.length)),
        pendingMoveIn: d['move-in'].filter((r) => r.status === 'PENDING').length,
        pendingMoveOut: d['move-out'].filter((r) => r.status === 'PENDING').length,
        pendingRepair: d.repairs.filter((r) => r.status !== 'DONE').length,
        unpaidBills: d.bills.filter((r) => r.state === 'UNPAID').length,
        monthlyMoveIn: d['move-in'].length,
        monthlyMoveOut: d['move-out'].length,
        buildingStats: d.buildings.map((building) => {
          const floors = d.floors.filter((f) => f.building?.id === building.id).map((f) => f.id);
          const dorms = d.dormitories.filter((r) => floors.includes(r.floor?.id)).map((r) => r.id);
          const beds = d.beds.filter((b) => dorms.includes(b.dormitoryId));
          const occupiedBeds = beds.filter((b) => b.status === 'OCCUPIED').length;
          return {
            building: building.name,
            totalBeds: beds.length,
            occupiedBeds,
            occupancyRate: Math.round((100 * occupiedBeds) / Math.max(1, beds.length)),
          };
        }),
      };
    } else if (kind === 'dormitories' && id === 'recommend') {
      const tags = Object.values(body);
      result = {
        recommendations: d.dormitories
          .filter((r) => d.beds.some((b) => b.dormitoryId === r.id && b.status === 'VACANT'))
          .map((r) => {
            const floor = d.floors.find((f) => f.id === r.floor?.id);
            return {
              ...r,
              score: tags.filter((t) => r.preferenceTags.includes(t)).length * 25,
              floor: floor?.name,
              building: d.buildings.find((b) => b.id === floor?.building?.id)?.name,
              reason: '按演示样例中的偏好匹配，并保留空闲床位。',
            };
          })
          .sort((a, b) => b.score - a.score),
      };
    } else if (!Object.hasOwn(d, kind) || !Array.isArray(d[kind]))
      throw new Error('这项功能未接入浏览器演示。');
    else if (method === 'GET') {
      let rows = d[kind];
      if (me().role === 'STUDENT' && ['move-in', 'move-out', 'repairs', 'bills'].includes(kind))
        rows = rows.filter((r) => r.studentId === me().id);
      result = rows.map((r) => enriched(kind, r));
    } else if (method === 'POST' && !id) {
      if (['buildings', 'floors', 'dormitories', 'beds', 'users'].includes(kind)) admin();
      if (['bills', 'notices'].includes(kind)) staff();
      const row = { ...body, id: nextId(d[kind]) };
      if (kind === 'beds') row.status = 'VACANT';
      if (['move-in', 'move-out', 'repairs'].includes(kind)) {
        row.studentId = me().id;
        row.status = 'PENDING';
      }
      if (
        kind === 'move-in' &&
        (d.beds.some((b) => b.occupantId === me().id) ||
          d['move-in'].some((a) => a.studentId === me().id && a.status === 'PENDING'))
      )
        throw new Error('你已有入住床位或待审核申请。');
      if (kind === 'move-out') {
        const bed = requireRow(d.beds, body.bedId);
        if (bed.occupantId !== me().id) throw new Error('请选择本人入住的床位。');
      }
      if (kind === 'bills') {
        row.total = Number(body.electricity) + Number(body.water) + Number(body.otherFee);
        row.state = 'UNPAID';
      }
      d[kind].push(row);
      result = enriched(kind, row);
    } else {
      const row = requireRow(d[kind], id);
      if (method === 'DELETE') {
        admin();
        if (kind === 'beds' && row.status === 'OCCUPIED') throw new Error('入住中的床位不能删除。');
        d[kind] = d[kind].filter((r) => r !== row);
        result = {};
      } else if (method === 'PUT') {
        admin();
        Object.assign(row, body);
        result = enriched(kind, row);
      } else if (method === 'PATCH') {
        if (kind !== 'bills') staff();
        if (kind === 'beds') {
          if (action === 'occupy') {
            if (row.status !== 'VACANT') throw new Error('床位不是空闲状态。');
            const student = requireRow(d.users, body.studentId);
            if (d.beds.some((b) => b.occupantId === student.id))
              throw new Error('该学生已经入住。');
            row.status = 'OCCUPIED';
            row.occupantId = student.id;
          } else if (action === 'release') {
            row.status = 'VACANT';
            row.occupantId = null;
          } else if (action === 'state') {
            if (row.status === 'OCCUPIED') throw new Error('请先办理退宿。');
            row.status = body.status;
          } else throw new Error('不支持的床位操作。');
        } else if (['move-in', 'move-out'].includes(kind)) {
          if (row.status !== 'PENDING') throw new Error('申请已处理。');
          if (action === 'approve') {
            if (kind === 'move-in') {
              const bed = d.beds.find(
                (b) =>
                  b.status === 'VACANT' &&
                  (!row.preferredDormitoryId || b.dormitoryId === row.preferredDormitoryId)
              );
              if (!bed) throw new Error('暂无空闲床位，请拒绝或先腾空床位。');
              bed.occupantId = row.studentId;
              bed.status = 'OCCUPIED';
            } else {
              const bed = requireRow(d.beds, row.bedId);
              bed.occupantId = null;
              bed.status = 'VACANT';
            }
            row.status = 'APPROVED';
          } else if (action === 'reject') row.status = 'REJECTED';
          else throw new Error('不支持的申请操作。');
          row.comment = body.comment || '';
        } else if (kind === 'repairs' && action === 'process') row.status = body.status;
        else if (kind === 'bills' && action === 'pay') {
          if (me().role === 'STUDENT' && row.studentId !== me().id)
            throw new Error('只能处理本人演示账单。');
          row.state = 'PAID';
        } else throw new Error('不支持的演示操作。');
        result = enriched(kind, row);
      } else throw new Error('不支持的演示操作。');
    }
    store.save();
    return clone(result);
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
if (typeof window !== 'undefined') {
  const model = createDormitoryModel();
  const fetchOriginal = window.fetch.bind(window);
  window.fetch = async (input, init = {}) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    if (!url.pathname.startsWith('/api/')) return fetchOriginal(input, init);
    let result,
      status = 200;
    try {
      result = model.handle(
        url.pathname.slice(4) + url.search,
        (init.method || 'GET').toUpperCase(),
        init.body ? JSON.parse(init.body) : {}
      );
    } catch (error) {
      result = { message: error.message };
      status = model.store.data.currentUserId ? 400 : 401;
    }
    return new Response(JSON.stringify(result), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  };
  window.DomeDemo.configure({
    roles: [
      { id: 3, label: '张三 · 学生' },
      { id: 2, label: '王老师 · 宿舍管理员' },
      { id: 1, label: '林老师 · 管理员' },
    ],
    current: model.store.data.currentUserId,
    switchRole(id) {
      model.switchRole(id);
      sessionStorage.removeItem('dorm_me');
      location.href = 'index.html';
    },
    reset() {
      model.reset();
      sessionStorage.removeItem('dorm_me');
      location.href = 'index.html';
    },
  });
}
