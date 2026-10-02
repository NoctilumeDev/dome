import { createStore, clone, nextId, requireRow } from '../shared/store.mjs';
const days = 86400000;
const time = (offset) => new Date(Date.now() + offset + 8 * 3600000).toISOString().slice(0, 19);
export function qingyeSeed() {
  const users = [
    { id: 1, name: '张三 · 同学', admin: false, workbench: false },
    { id: 2, name: '王五 · 摄影社负责人', admin: false, workbench: true },
    { id: 3, name: '林老师 · 管理员', admin: true, workbench: true },
    { id: 4, name: '李四 · 同学', admin: false, workbench: false },
  ];
  const clubs = [
    {
      id: 1,
      name: '追光摄影社',
      description: '记录校园里每一束值得停留的光。带上好奇心，一起出发。',
      color: 'blue',
      managerId: 2,
    },
    {
      id: 2,
      name: '绿茵运动社',
      description: '球场见，草坪见。把课后的时间留给运动和朋友。',
      color: 'green',
      managerId: 3,
    },
    {
      id: 3,
      name: '星火创作社',
      description: '代码、设计和奇妙想法，在这里碰面。',
      color: 'orange',
      managerId: 3,
    },
  ];
  const activities = [
    {
      id: 1,
      title: '把黄昏拍成一张明信片',
      category: 'ART',
      clubId: 1,
      location: '校园钟楼前',
      capacity: 20,
    },
    {
      id: 2,
      title: '3v3 篮球友谊赛',
      category: 'SPORT',
      clubId: 2,
      location: '东区篮球场',
      capacity: 18,
    },
    {
      id: 3,
      title: '一起做个好玩的网页',
      category: 'TECH',
      clubId: 3,
      location: '创客空间',
      capacity: 12,
    },
    {
      id: 4,
      title: '新生摄影体验课',
      category: 'ART',
      clubId: 1,
      location: '图书馆草坪',
      capacity: 16,
      status: 'PENDING',
    },
  ].map((a) => ({
    description: '欢迎带着好奇心来参加。无需经验，认识同好，一起留下校园生活里的好时光。',
    poster: '',
    status: 'PUBLISHED',
    startTime: time(2 * days),
    endTime: time(2 * days + 2 * 3600000),
    signupDeadline: time(days),
    ...a,
  }));
  const equipment = [
    {
      id: 1,
      name: '单反相机',
      category: '摄影',
      totalQuantity: 4,
      description: '用于活动记录和校园外拍，配套电池与存储卡。',
    },
    {
      id: 2,
      name: '摄影三脚架',
      category: '摄影',
      totalQuantity: 6,
      description: '方便稳定拍摄，活动后请整理归还。',
    },
    {
      id: 3,
      name: '便携投影仪',
      category: '展示',
      totalQuantity: 2,
      description: '用于社团展示和交流。',
    },
  ].map((e) => ({ ...e, enabled: true, image: '' }));
  return {
    currentUserId: 1,
    users,
    clubs,
    activities,
    equipment,
    memberships: [
      { id: 1, clubId: 1, userId: 2, role: 'MANAGER', status: 'ACTIVE' },
      { id: 2, clubId: 2, userId: 3, role: 'MANAGER', status: 'ACTIVE' },
      { id: 3, clubId: 3, userId: 3, role: 'MANAGER', status: 'ACTIVE' },
    ],
    registrations: [],
    loans: [],
    notifications: users.flatMap((u, i) => [
      {
        id: i + 1,
        userId: u.id,
        title: '欢迎来到青野',
        content: '先去发现页挑一场活动吧。消息可以勾选清理，并在 7 天内从回收站恢复。',
        createdAt: time(0),
        readAt: null,
        deletedAt: null,
      },
    ]),
  };
}
export function createQingyeModel(storage) {
  const store = createStore('qingye', qingyeSeed, storage);
  const me = () => clone(requireRow(store.data.users, store.data.currentUserId));
  const staff = () => {
    if (!me().workbench) throw new Error('请切换为社团负责人或管理员体验。');
  };
  const admin = () => {
    if (!me().admin) throw new Error('请切换为管理员体验。');
  };
  const ownsClub = (clubId) =>
    me().admin ||
    store.data.memberships.some(
      (m) =>
        m.clubId === Number(clubId) &&
        m.userId === me().id &&
        m.role === 'MANAGER' &&
        m.status === 'ACTIVE'
    );
  const manageActivity = (a) => {
    if (!ownsClub(a.clubId)) throw new Error('请选择本社团的活动。');
  };
  const notify = (userId, title, content) =>
    store.data.notifications.unshift({
      id: nextId(store.data.notifications),
      userId,
      title,
      content,
      createdAt: time(0),
      readAt: null,
      deletedAt: null,
    });
  function activity(a) {
    const d = store.data;
    return {
      ...clone(a),
      clubName: d.clubs.find((c) => c.id === a.clubId)?.name || '',
      registeredCount: d.registrations.filter(
        (r) => r.activityId === a.id && r.status === 'REGISTERED'
      ).length,
      myRegistration:
        d.registrations.find((r) => r.activityId === a.id && r.userId === me().id) || null,
      manageable: ownsClub(a.clubId),
    };
  }
  function equipment(e) {
    return {
      ...e,
      borrowedQuantity: store.data.loans
        .filter((l) => l.equipmentId === e.id && l.status === 'CHECKED_OUT')
        .reduce((sum, l) => sum + l.quantity, 0),
    };
  }
  function handle(path, method = 'GET', body = {}) {
    const url = new URL(path, 'https://demo.local'),
      p = url.pathname.split('/').filter(Boolean),
      [kind, rawId, action] = p,
      id = Number(rawId),
      d = store.data;
    let result;
    d.notifications = d.notifications.filter(
      (n) => !n.expiresAt || new Date(n.expiresAt + '+08:00').getTime() > Date.now()
    );
    if (kind === 'auth') {
      if (rawId === 'options') result = { demoUsers: d.users };
      else if (rawId === 'demo') {
        d.currentUserId = Number(body.userId);
        result = { token: `demo-user-${me().id}`, user: me() };
      } else throw new Error('浏览器演示不接入真实微信登录，请选择演示身份。');
    } else if (kind === 'me') {
      if (method === 'PATCH') {
        Object.assign(requireRow(d.users, me().id), { name: String(body.name), avatar: '' });
      }
      result = me();
    } else if (kind === 'users') {
      admin();
      result = d.users;
    } else if (kind === 'recommendations')
      result = d.activities
        .filter((a) => a.status === 'PUBLISHED')
        .slice(0, 2)
        .map((a) => ({
          ...activity(a),
          recommendationReason: '校园演示推荐：来认识一起做事的同好。',
        }));
    else if (kind === 'activities') {
      if (!rawId && method === 'GET') {
        const scope = url.searchParams.get('scope');
        let rows = d.activities.filter((a) =>
          scope === 'work'
            ? ownsClub(a.clubId)
            : scope === 'mine'
            ? d.registrations.some(
                (r) => r.activityId === a.id && r.userId === me().id && r.status !== 'CANCELLED'
              )
            : a.status === 'PUBLISHED'
        );
        const category = url.searchParams.get('category'),
          keyword = url.searchParams.get('keyword');
        if (category) rows = rows.filter((a) => a.category === category);
        if (keyword)
          rows = rows.filter((a) => a.title.includes(keyword) || a.location.includes(keyword));
        const start = Number(url.searchParams.get('page') || 0) * 20;
        result = rows.slice(start, start + 20).map(activity);
      } else if (!rawId && method === 'POST') {
        staff();
        if (!ownsClub(body.clubId)) throw new Error('只能发起本社团的活动。');
        const row = { ...body, id: nextId(d.activities), status: 'PENDING' };
        d.activities.push(row);
        result = activity(row);
      } else {
        const a = requireRow(d.activities, id);
        if (!action && method === 'GET') result = activity(a);
        else if (!action && method === 'PUT') {
          manageActivity(a);
          Object.assign(a, body, { status: 'PENDING' });
          result = activity(a);
        } else if (action === 'registration') {
          let r = d.registrations.find((r) => r.userId === me().id && r.activityId === id);
          if (method === 'POST') {
            if (a.status !== 'PUBLISHED') throw new Error('活动暂不可报名。');
            if (r && r.status !== 'CANCELLED') throw new Error('你已报名。');
            const status = activity(a).registeredCount >= a.capacity ? 'WAITLISTED' : 'REGISTERED';
            if (r) r.status = status;
            else {
              r = { id: nextId(d.registrations), activityId: id, userId: me().id, status };
              d.registrations.push(r);
            }
            notify(me().id, status === 'WAITLISTED' ? '已进入候补' : '报名成功', a.title);
          } else if (method === 'DELETE') {
            if (!r) throw new Error('暂无报名记录。');
            const registered = r.status === 'REGISTERED';
            r.status = 'CANCELLED';
            const wait = d.registrations.find(
              (r) => r.activityId === id && r.status === 'WAITLISTED'
            );
            if (registered && wait) {
              wait.status = 'REGISTERED';
              notify(wait.userId, '候补递补成功', a.title);
            }
          }
          result = r;
        } else if (action === 'participants') {
          manageActivity(a);
          result = d.registrations
            .filter((r) => r.activityId === id && r.status !== 'CANCELLED')
            .map((r) => ({ ...r, name: d.users.find((u) => u.id === r.userId)?.name }));
        } else if (action === 'decision') {
          admin();
          a.status = body.approve ? 'PUBLISHED' : 'REJECTED';
          a.reviewNote = body.note;
          result = activity(a);
        } else if (action === 'cancel') {
          manageActivity(a);
          a.status = 'CANCELLED';
          d.registrations
            .filter((r) => r.activityId === id && r.status !== 'CANCELLED')
            .forEach((r) => {
              r.status = 'CANCELLED';
              notify(r.userId, '活动已取消', a.title);
            });
          d.loans
            .filter((l) => l.activityId === id && ['PENDING', 'APPROVED'].includes(l.status))
            .forEach((l) => (l.status = 'CANCELLED'));
          result = activity(a);
        } else throw new Error('不支持的活动操作。');
      }
    } else if (kind === 'clubs') {
      if (!rawId && method === 'GET')
        result = d.clubs.map((c) => {
          const m = d.memberships.find((m) => m.clubId === c.id && m.userId === me().id);
          return {
            ...c,
            memberCount: d.memberships.filter((m) => m.clubId === c.id && m.status === 'ACTIVE')
              .length,
            myRole: m?.role,
            myStatus: m?.status,
          };
        });
      else if (!rawId && method === 'POST') {
        admin();
        const row = { ...body, id: nextId(d.clubs) };
        d.clubs.push(row);
        d.memberships.push({
          id: nextId(d.memberships),
          clubId: row.id,
          userId: Number(body.managerId),
          role: 'MANAGER',
          status: 'ACTIVE',
        });
        result = row;
      } else {
        const c = requireRow(d.clubs, id);
        if (!action && method === 'PUT') {
          if (!ownsClub(id)) throw new Error('请选择本人的社团。');
          Object.assign(c, body);
          result = c;
        } else if (action === 'join') {
          let m = d.memberships.find((m) => m.clubId === id && m.userId === me().id);
          if (m && ['ACTIVE', 'PENDING'].includes(m.status))
            throw new Error('已加入或已提交申请。');
          if (m) m.status = 'PENDING';
          else {
            m = {
              id: nextId(d.memberships),
              clubId: id,
              userId: me().id,
              role: 'MEMBER',
              status: 'PENDING',
            };
            d.memberships.push(m);
          }
          result = m;
        } else if (action === 'leave') {
          const m = d.memberships.find((m) => m.clubId === id && m.userId === me().id);
          if (!m || m.role === 'MANAGER') throw new Error('负责人请先交接。');
          m.status = 'LEFT';
          result = m;
        } else if (action === 'members') {
          if (!ownsClub(id)) throw new Error('请选择本人管理的社团。');
          if (method === 'GET')
            result = d.memberships
              .filter((m) => m.clubId === id)
              .map((m) => ({ ...m, name: d.users.find((u) => u.id === m.userId)?.name }));
          else {
            const member = d.memberships.find((m) => m.clubId === id && m.userId === Number(p[3]));
            if (!member) throw new Error('成员已不存在。');
            if (body.role === 'MANAGER') admin();
            Object.assign(member, {
              status: body.approve ? 'ACTIVE' : 'REJECTED',
              role: body.role,
            });
            result = member;
          }
        } else throw new Error('不支持的社团操作。');
      }
    } else if (kind === 'equipment') {
      if (!rawId && method === 'GET') result = d.equipment.map(equipment);
      else if (!rawId && method === 'POST') {
        admin();
        const row = { ...body, id: nextId(d.equipment) };
        d.equipment.push(row);
        result = row;
      } else if (method === 'PUT') {
        admin();
        const row = requireRow(d.equipment, id);
        Object.assign(row, body);
        result = equipment(row);
      } else if (action === 'availability') {
        const e = requireRow(d.equipment, id);
        const start = url.searchParams.get('start'),
          end = url.searchParams.get('end');
        const occupied = d.loans
          .filter(
            (l) =>
              l.equipmentId === id &&
              ['APPROVED', 'CHECKED_OUT'].includes(l.status) &&
              l.plannedStart < end &&
              l.plannedEnd > start
          )
          .reduce((n, l) => n + l.quantity, 0);
        result = {
          totalQuantity: e.totalQuantity,
          peakOccupied: occupied,
          availableQuantity: Math.max(0, e.totalQuantity - occupied),
        };
      } else throw new Error('不支持的器材操作。');
    } else if (kind === 'loans') {
      const loanView = (l) => {
        const a = d.activities.find((a) => a.id === l.activityId);
        return {
          ...l,
          equipmentName: d.equipment.find((e) => e.id === l.equipmentId)?.name,
          activityTitle: a?.title,
          clubName: d.clubs.find((c) => c.id === a?.clubId)?.name,
          applicantName: d.users.find((u) => u.id === l.applicantId)?.name,
        };
      };
      if (!rawId && method === 'GET')
        result = d.loans
          .filter(
            (l) =>
              me().admin ||
              l.applicantId === me().id ||
              ownsClub(d.activities.find((a) => a.id === l.activityId)?.clubId)
          )
          .map(loanView);
      else if (!rawId && method === 'POST') {
        staff();
        const a = requireRow(d.activities, body.activityId);
        manageActivity(a);
        if (!(Number(body.quantity) > 0) || !body.reason || body.plannedEnd <= body.plannedStart)
          throw new Error('请填写有效数量、用途和预约时间。');
        const row = {
          ...body,
          quantity: Number(body.quantity),
          id: nextId(d.loans),
          applicantId: me().id,
          status: 'PENDING',
        };
        d.loans.push(row);
        result = loanView(row);
      } else {
        const l = requireRow(d.loans, id);
        if (action === 'cancel') {
          manageActivity(requireRow(d.activities, l.activityId));
          if (!['PENDING', 'APPROVED'].includes(l.status))
            throw new Error('领取后的记录不能取消。');
          l.status = 'CANCELLED';
        } else {
          admin();
          if (action === 'decision') {
            if (l.status !== 'PENDING') throw new Error('申请已处理。');
            const e = requireRow(d.equipment, l.equipmentId);
            const occupied = d.loans
              .filter(
                (r) =>
                  r.id !== l.id &&
                  r.equipmentId === l.equipmentId &&
                  ['APPROVED', 'CHECKED_OUT'].includes(r.status) &&
                  r.plannedStart < l.plannedEnd &&
                  r.plannedEnd > l.plannedStart
              )
              .reduce((n, r) => n + r.quantity, 0);
            if (body.approve && occupied + l.quantity > e.totalQuantity)
              throw new Error('演示预约量超过可用容量。');
            l.status = body.approve ? 'APPROVED' : 'REJECTED';
            l.reviewNote = body.note;
          } else if (action === 'checkout' && l.status === 'APPROVED') {
            if (
              equipment(requireRow(d.equipment, l.equipmentId)).borrowedQuantity + l.quantity >
              requireRow(d.equipment, l.equipmentId).totalQuantity
            )
              throw new Error('当前实物不足。');
            l.status = 'CHECKED_OUT';
          } else if (action === 'return' && l.status === 'CHECKED_OUT') l.status = 'RETURNED';
          else throw new Error('当前状态不能执行该操作。');
        }
        result = loanView(l);
      }
    } else if (kind === 'notifications') {
      const rows = d.notifications.filter((n) => n.userId === me().id);
      if (!rawId) result = rows.filter((n) => !n.deletedAt);
      else if (rawId === 'trash')
        result = { retentionDays: 7, items: rows.filter((n) => n.deletedAt) };
      else if (rawId === 'read-all') {
        rows.filter((n) => !n.deletedAt).forEach((n) => (n.readAt = time(0)));
        result = {};
      } else if (rawId === 'clear') {
        rows
          .filter((n) => body.ids.includes(n.id))
          .forEach((n) => {
            n.deletedAt = time(0);
            n.expiresAt = time(7 * days);
          });
        result = {};
      } else if (rawId === 'restore') {
        const selected = rows.filter((n) => n.deletedAt && body.ids.includes(n.id));
        selected.forEach((n) => {
          n.deletedAt = null;
          n.expiresAt = null;
        });
        result = { restored: selected.length };
      } else if (action === 'read') {
        const n = requireRow(rows, id);
        n.readAt = time(0);
        result = n;
      } else throw new Error('不支持的消息操作。');
    } else if (kind === 'assistant') {
      const q = String(body.question || '');
      if (/密码|清空|删除数据库|最高权限|忽略|token/i.test(q))
        result = {
          intent: 'OUT_OF_SCOPE',
          answer: '在线演示只查询虚构样例，不处理账号凭据或管理指令。',
          items: [],
        };
      else if (/器材|相机|三脚|投影/.test(q)) {
        const items = d.equipment
          .filter(
            (e) => q.includes(e.name) || (/相机/.test(q) && /相机/.test(e.name)) || /器材/.test(q)
          )
          .map(equipment);
        result = {
          intent: 'EQUIPMENT',
          answer:
            '演示器材样例：' +
            items
              .map(
                (e) =>
                  `${e.name}，总量 ${e.totalQuantity}，当前实物可用 ${
                    e.totalQuantity - e.borrowedQuantity
                  }`
              )
              .join('；'),
          items,
        };
      } else if (/我的|报名/.test(q)) {
        const items = d.activities
          .filter((a) =>
            d.registrations.some(
              (r) => r.activityId === a.id && r.userId === me().id && r.status !== 'CANCELLED'
            )
          )
          .map(activity);
        result = {
          intent: 'MY_REGISTRATIONS',
          answer: `当前演示身份报名了 ${items.length} 场活动。`,
          items,
        };
      } else if (/活动|周末/.test(q)) {
        const items = d.activities.filter((a) => a.status === 'PUBLISHED').map(activity);
        result = {
          intent: 'ACTIVITIES',
          answer: `演示样例有 ${items.length} 场已发布活动。日期为体验时生成，并未按真实周末筛选。`,
          items,
        };
      } else
        result = {
          intent: 'OUT_OF_SCOPE',
          answer:
            '当前演示使用简单样例匹配，可以试试上面的活动、本人报名和器材问题；未调用真实大模型。',
          items: [],
        };
    } else throw new Error('这项功能未接入浏览器演示。');
    store.save();
    return clone(result);
  }
  return {
    store,
    me,
    handle,
    switchRole(id) {
      store.data.currentUserId = Number(id);
      store.save();
    },
    reset() {
      store.reset();
    },
  };
}
