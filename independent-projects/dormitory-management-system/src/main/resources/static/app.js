const tabs = document.querySelectorAll('.tab-btn');
const currentUser = { id: null, role: null };
const searchParams = new URLSearchParams(window.location.search);
let cachedBuildings = [];
let cachedFloors = [];
let cachedDormitories = [];
let cachedUsers = [];
let cachedBeds = [];
let actionTipTimer = null;

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function setUserTip(message) {
  document.getElementById('userInfo').textContent = message;
}

function getTextSnippet(text) {
  if (!text) return '';
  return text.substring(0, 200);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function statusLabel(status) {
  const labels = {
    VACANT: '空闲',
    OCCUPIED: '已入住',
    MAINTENANCE: '维修中',
    PENDING: '待审核',
    APPROVED: '已通过',
    REJECTED: '已驳回',
    PROCESSING: '处理中',
    DONE: '已完成',
    UNPAID: '未缴费',
    PAID: '已缴费',
    ALL: '全体',
    BUILDING: '指定楼栋'
  };
  return labels[status] || status || '-';
}

function roleLabel(role) {
  return {
    ADMIN: '管理员',
    DORM_MANAGER: '宿舍管理员',
    STUDENT: '学生'
  }[role] || role || '';
}

function preferenceLabel(value) {
  return value ? String(value).replaceAll(',', '、') : '-';
}

function readStudentPreference() {
  return {
    atmosphere: document.getElementById('studentAtmosphere').value,
    sleepHabit: document.getElementById('studentSleepHabit').value,
    cleanliness: document.getElementById('studentCleanliness').value,
    hobby: document.getElementById('studentHobby').value
  };
}

function readDormPreferenceTags() {
  return [
    document.getElementById('dormAtmosphere').value,
    document.getElementById('dormSleepHabit').value,
    document.getElementById('dormCleanliness').value,
    document.getElementById('dormHobby').value
  ].join(',');
}

function repairStatusLabel(status) {
  return status === 'PENDING' ? '待处理' : statusLabel(status);
}

function getActionTipBox() {
  let box = document.getElementById('actionTip');
  if (!box) {
    box = document.createElement('div');
    box.id = 'actionTip';
    box.className = 'action-tip';
    box.setAttribute('role', 'status');
    box.setAttribute('aria-live', 'polite');
    document.body.appendChild(box);
  }
  return box;
}

function setActionTip(message, level = 'info') {
  const box = getActionTipBox();
  box.className = `action-tip action-tip-${level}`;
  box.setAttribute('role', level === 'error' ? 'alert' : 'status');
  box.textContent = message;
  box.style.display = 'block';
  clearTimeout(actionTipTimer);
  actionTipTimer = setTimeout(() => {
    box.style.display = 'none';
  }, level === 'error' ? 5000 : 2200);
}

function setButtonState(btn, busy, busyText = '处理中...') {
  if (!btn) return;
  if (busy) {
    if (!btn.dataset.originText) {
      btn.dataset.originText = btn.textContent;
    }
    btn.disabled = true;
    btn.textContent = busyText;
  } else {
    btn.disabled = false;
    if (btn.dataset.originText) {
      btn.textContent = btn.dataset.originText;
      delete btn.dataset.originText;
    }
  }
}

async function runAction(actionName, action, options = {}) {
  const { button = null, retries = 1, autoToast = true } = options;
  let attempt = 0;
  while (true) {
    attempt++;
    try {
      setButtonState(button, true, '处理中...');
      if (autoToast) {
        setActionTip(`正在${actionName}...`, 'info');
      }
      const result = await action();
      setActionTip(`${actionName}成功`, 'success');
      return result;
    } catch (error) {
      const msg = error && error.message ? error.message : '请求失败';
      const canRetry = attempt <= retries;
      if (canRetry) {
        const confirmRetry = window.confirm(`${actionName}失败（${msg}）。是否重试？`);
        if (confirmRetry) {
          setActionTip(`重试中（第${attempt}次）`, 'warn');
          await sleep(300);
          continue;
        }
      }
      if (autoToast) {
        setActionTip(`${actionName}失败：${msg}`, 'error');
      }
      throw error;
    } finally {
      setButtonState(button, false);
    }
  }
}

function showLocalTip(message, level = 'warn') {
  if (!message) return;
  setActionTip(message, level);
}

function toNumberOrNull(input) {
  const value = input == null ? '' : String(input).trim();
  if (!value) return null;
  const num = Number(value);
  if (Number.isNaN(num)) return null;
  return num;
}

function bedStatusClass(status) {
  const state = (status || '').toUpperCase();
  if (state === 'VACANT') {
    return 'bed-status bed-status-vacant';
  }
  if (state === 'OCCUPIED') {
    return 'bed-status bed-status-occupied';
  }
  if (state === 'MAINTENANCE') {
    return 'bed-status bed-status-maintenance';
  }
  return 'bed-status';
}

function trimOrNull(value) {
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

function findById(cache, id) {
  return (cache || []).find(item => String(item.id) === String(id));
}

function isAdminOrManager() {
  return currentUser.role === 'ADMIN' || currentUser.role === 'DORM_MANAGER';
}

function isAdmin() {
  return currentUser.role === 'ADMIN';
}

function fillSelect(selectId, items, labelField, placeholder) {
  const select = document.getElementById(selectId);
  if (!select) {
    return;
  }
  const opts = [`<option value="">${placeholder || '请选择'}</option>`].concat(
    (items || []).map(item => `<option value="${escapeHtml(item.id)}">${escapeHtml(labelField(item))}</option>`)
  );
  select.innerHTML = opts.join('');
}

function applyAdminPrivileges() {
  document.querySelectorAll('[data-roles]').forEach(element => {
    const roles = element.dataset.roles.split(',').map(x => x.trim());
    element.hidden = !roles.includes(currentUser.role);
  });
  const billTitle = document.getElementById('billListTitle');
  if (billTitle) billTitle.textContent = currentUser.role === 'STUDENT' ? '我的账单' : '账单列表';
}

function readCachedMe() {
  try {
    const raw = sessionStorage.getItem('dorm_me');
    if (!raw) {
      return null;
    }
    const cached = JSON.parse(raw);
    if (cached && cached.id && cached.username && cached.role) {
      return cached;
    }
  } catch (err) {
    sessionStorage.removeItem('dorm_me');
  }
  return null;
}

function saveCachedMe(me) {
  sessionStorage.setItem('dorm_me', JSON.stringify({
    id: me.id,
    username: me.username,
    fullName: me.fullName,
    role: me.role
  }));
}

function clearCachedMe() {
  sessionStorage.removeItem('dorm_me');
}

tabs.forEach(btn => {
  btn.addEventListener('click', () => {
    const panelId = btn.getAttribute('data-panel');
    document.querySelectorAll('.panel').forEach(p => p.style.display = 'none');
    document.getElementById(panelId).style.display = 'block';
    tabs.forEach(tab => tab.setAttribute('aria-selected', String(tab === btn)));
  });
});

async function api(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const hasBody = options.body != null && method !== 'GET' && method !== 'HEAD';
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const res = await fetch('/api' + path, {
    credentials: 'same-origin',
    method,
    headers,
    body: hasBody ? options.body : undefined
  });

  const rawBody = await res.text();
  let data = {};
  try {
    data = rawBody ? JSON.parse(rawBody) : {};
  } catch (e) {
    data = { message: getTextSnippet(rawBody) || '响应不是合法 JSON' };
  }

  if (!res.ok) {
    if (res.status === 401 && window.location.pathname.includes('index.html')) {
      const from = new URLSearchParams(window.location.search);
      from.set('reason', 'expired');
      window.location.replace(`login.html?${from.toString()}`);
    }
    throw new Error(data && data.message ? data.message : `请求失败（${res.status}）`);
  }
  return data;
}

async function init() {
  let me = readCachedMe();
  const shouldRetryOnce = searchParams.get('fromLogin') === '1';
  const maxRetries = shouldRetryOnce ? 8 : 1;
  const retryIntervalMs = 250;

  const readMe = async () => {
    return api('/auth/me', { method: 'GET' });
  };

  try {
    for (let i = 0; i < maxRetries; i++) {
      try {
        me = me || await readMe();
        break;
      } catch (e) {
        if (i === maxRetries - 1) {
          if (shouldRetryOnce) {
            setUserTip('会话初始化未完成');
            await sleep(500);
          }
          throw e;
        }
        await sleep(retryIntervalMs);
      }
    }
  } catch (e) {
    clearCachedMe();
    if (shouldRetryOnce) {
      window.location.replace('login.html?reason=session');
    } else {
      window.location.replace('login.html?reason=logout');
    }
    return;
  }

  try {
    currentUser.id = me.id;
    currentUser.role = me.role;
    setUserTip(`${me.fullName || me.username}（${roleLabel(me.role)}）`);
    saveCachedMe(me);
    applyAdminPrivileges();

    const createLoadTasks = () => isAdminOrManager() ? [
        loadAdminData(), loadBuildingsDorms(), loadDashboard(), loadBeds(),
        loadMoveApplications(), loadRepairs(), loadBills(), loadNotices()
      ] : [
        loadBuildingsDorms(), loadDashboard(), loadBeds(), loadMoveApplications(),
        loadRepairs(), loadBills(), loadNotices()
      ];

    const results = await Promise.allSettled(createLoadTasks());
    const failedTasks = results.filter(r => r.status === 'rejected');
    if (failedTasks.length > 0 && shouldRetryOnce) {
      await sleep(300);
      const retryResults = await Promise.allSettled(createLoadTasks());
      const stillFailed = retryResults.filter(r => r.status === 'rejected');
      if (stillFailed.length > 0) {
        const firstError = stillFailed[0].reason ? stillFailed[0].reason.message : '未知错误';
        setUserTip(`部分数据加载失败：${firstError}`);
      }
    } else if (failedTasks.length > 0) {
      const firstError = failedTasks[0].reason ? failedTasks[0].reason.message : '未知错误';
      setUserTip(`部分数据加载失败：${firstError}`);
    }

    document.getElementById('panel-dashboard').style.display = 'block';
    document.querySelectorAll('.panel').forEach(panel => {
      if (panel.id !== 'panel-dashboard') {
        panel.style.display = 'none';
      }
    });
  } catch (e) {
    clearCachedMe();
    const firstError = e?.message || '页面初始化异常';
    setUserTip(`页面初始化异常：${firstError}`);
  }
}

async function loadBuildingsDorms() {
  const buildingSelect = document.getElementById('moveinDorm');
  const dorms = cachedDormitories.length > 0
    ? cachedDormitories
    : await api('/dormitories');
  buildingSelect.innerHTML = '<option value="">优先选择宿舍（可空）</option>' +
    dorms.map(d => `<option value="${escapeHtml(d.id)}">${escapeHtml(d.dormCode)}</option>`).join('');
  fillSelect('bedDormSelect', dorms, d => d.dormCode, '请选择宿舍');
}

function selectRecommendedDorm(dormitoryId) {
  const select = document.getElementById('moveinDorm');
  select.value = String(dormitoryId);
  showLocalTip('已把该宿舍设为意向宿舍，你仍可以改选其他宿舍', 'success');
}

async function recommendDormitories(btn) {
  await runAction('推荐宿舍', async () => {
    const result = await api('/dormitories/recommend', {
      method: 'POST',
      body: JSON.stringify(readStudentPreference())
    });
    const wrap = document.getElementById('recommendationWrap');
    if (!result.recommendations || result.recommendations.length === 0) {
      wrap.innerHTML = `<p class="help-text">${escapeHtml(result.message || '当前没有可推荐的宿舍')}</p>`;
      return;
    }
    wrap.innerHTML = result.recommendations.map(item => `
      <div class="recommendation-item">
        <strong>${escapeHtml(item.dormCode)} · ${escapeHtml(item.score)}分</strong>
        <span>${escapeHtml(item.building)} ${escapeHtml(item.floor)}，特点：${escapeHtml(preferenceLabel(item.preferenceTags))}</span>
        <span>${escapeHtml(item.reason)}</span>
        <button type="button" onclick="selectRecommendedDorm(${Number(item.id)})">采用这个推荐</button>
      </div>
    `).join('');
  }, { button: btn });
}

function renderAdminTables() {
  const buildingWrap = document.getElementById('buildingWrap');
  const floorWrap = document.getElementById('floorWrap');
  const dormWrap = document.getElementById('dormWrap');
  const userWrap = document.getElementById('userWrap');

  const buildingMap = new Map((cachedBuildings || []).map(b => [b.id, b.name]));
  const floorMap = new Map((cachedFloors || []).map(f => [f.id, f.name]));

  buildingWrap.innerHTML = '<table><thead><tr><th>ID</th><th>名称</th><th>地址</th><th>操作</th></tr></thead><tbody>' +
    cachedBuildings.map(b => {
      const ops = isAdmin()
        ? `<button class=\"inline-action\" onclick=\"editBuilding(this, ${b.id})\">编辑</button><button class=\"inline-action danger\" onclick=\"deleteBuilding(this, ${b.id})\">删除</button>`
        : '-';
      return `<tr><td>${escapeHtml(b.id)}</td><td>${escapeHtml(b.name)}</td><td>${escapeHtml(b.address || '')}</td><td>${ops}</td></tr>`;
    }).join('') +
    '</tbody></table>';
  floorWrap.innerHTML = '<table><thead><tr><th>ID</th><th>楼层</th><th>所属楼栋</th><th>操作</th></tr></thead><tbody>' +
    cachedFloors.map(f => {
      const ops = isAdmin()
        ? `<button class=\"inline-action\" onclick=\"editFloor(this, ${f.id})\">编辑</button><button class=\"inline-action danger\" onclick=\"deleteFloor(this, ${f.id})\">删除</button>`
        : '-';
      return `<tr><td>${escapeHtml(f.id)}</td><td>${escapeHtml(f.name)}</td><td>${escapeHtml(buildingMap.get(f.buildingId) || '')}</td><td>${ops}</td></tr>`;
    }).join('') +
    '</tbody></table>';
  dormWrap.innerHTML = '<table><thead><tr><th>ID</th><th>宿舍号</th><th>所属楼栋</th><th>所属楼层</th><th>容量</th><th>宿舍特点</th><th>操作</th></tr></thead><tbody>' +
    cachedDormitories.map(d => {
      const ops = isAdmin()
        ? `<button class=\"inline-action\" onclick=\"editDorm(this, ${d.id})\">编辑</button><button class=\"inline-action danger\" onclick=\"deleteDorm(this, ${d.id})\">删除</button>`
        : '-';
      const buildingName = buildingMap.get(d.buildingId) || '';
      const floorName = floorMap.get(d.floorId) || '';
      return `<tr><td>${escapeHtml(d.id)}</td><td>${escapeHtml(d.dormCode)}</td><td>${escapeHtml(buildingName)}</td><td>${escapeHtml(floorName)}</td><td>${escapeHtml(d.capacity || '-')}</td><td>${escapeHtml(preferenceLabel(d.preferenceTags))}</td><td>${ops}</td></tr>`;
    }).join('') +
    '</tbody></table>';
  userWrap.innerHTML = '<table><thead><tr><th>ID</th><th>用户名</th><th>姓名</th><th>角色</th><th>归属楼栋</th></tr></thead><tbody>' +
    cachedUsers.map(u => `<tr><td>${escapeHtml(u.id)}</td><td>${escapeHtml(u.username)}</td><td>${escapeHtml(u.fullName)}</td><td>${escapeHtml(roleLabel(u.role))}</td><td>${escapeHtml(buildingMap.get(u.buildingId) || '-')}</td></tr>`).join('') +
    '</tbody></table>';
}

function syncAdminSelects() {
  fillSelect('floorBuilding', cachedBuildings, b => b.name, '选择楼栋');
  fillSelect('dormBuilding', cachedBuildings, b => b.name, '选择楼栋');
  fillSelect('userBuilding', cachedBuildings, b => b.name, '选择归属楼栋');
  fillSelect('noticeBuilding', cachedBuildings, b => b.name, '选择楼栋（按楼栋公告）');
  const students = cachedUsers.filter(u => u.role === 'STUDENT');
  fillSelect('assignStudent', students, u => `${u.fullName}（${u.username}）`, '请选择学生');
  fillSelect('billStudentId', students, u => `${u.fullName}（${u.username}）`, '请选择学生');
  const currentDormBuilding = document.getElementById('dormBuilding')?.value;
  if (currentDormBuilding) {
    const filtered = cachedFloors.filter(f => String(f.buildingId) === String(currentDormBuilding));
    fillSelect('dormFloor', filtered, f => `${f.name}`, '先选楼层');
  } else {
    fillSelect('dormFloor', [], () => '', '先选楼栋');
  }
}

function onDormBuildingChange() {
  const dormBuilding = document.getElementById('dormBuilding');
  const dormFloor = document.getElementById('dormFloor');
  if (!dormBuilding || !dormFloor) return;
  const filtered = cachedFloors.filter(f => String(f.buildingId) === String(dormBuilding.value));
  fillSelect('dormFloor', filtered, f => `${f.name}`, '先选楼层');
  if (dormFloor.value && !filtered.some(item => String(item.id) === String(dormFloor.value))) {
    dormFloor.value = '';
  }
}

async function loadAdminData() {
  cachedBuildings = await api('/buildings');
  cachedFloors = await api('/floors');
  cachedDormitories = await api('/dormitories');
  cachedUsers = await api('/users');
  renderAdminTables();
  syncAdminSelects();
  loadBuildingsDorms();
}

async function loadDashboard() {
  const d = await api('/dashboard');
  const cards = document.getElementById('dashboardCards');
  cards.innerHTML = [
    { t: '床位总数', v: d.totalBeds },
    { t: '已入住', v: d.occupiedBeds },
    { t: '空置', v: d.vacantBeds },
    { t: '维修中', v: d.maintenanceBeds || 0 },
    { t: '入住率', v: d.occupancyRate + '%' },
    { t: '待处理入住', v: d.pendingMoveIn },
    { t: '待处理退宿', v: d.pendingMoveOut },
    { t: '待处理报修', v: d.pendingRepair || 0 },
    { t: '本月新增入住申请', v: d.monthlyMoveIn || 0 },
    { t: '本月新增退宿申请', v: d.monthlyMoveOut || 0 }
  ].map(item => `<div class="card"><h3>${escapeHtml(item.t)}</h3><p>${escapeHtml(item.v)}</p></div>`).join('');
  const buildingWrap = document.getElementById('buildingStats');
  buildingWrap.innerHTML = '<h3>每栋楼入住率</h3>' +
    '<table><thead><tr><th>宿舍楼</th><th>总床位</th><th>已占用</th><th>入住率</th></tr></thead><tbody>' +
    d.buildingStats.map(x =>
      `<tr><td>${escapeHtml(x.building)}</td><td>${escapeHtml(x.totalBeds)}</td><td>${escapeHtml(x.occupiedBeds)}</td><td>${escapeHtml(x.occupancyRate)}%</td></tr>`).join('') +
    '</tbody></table>';
}

async function loadBeds() {
  const beds = await api('/beds');
  cachedBeds = beds;
  if (currentUser.role === 'STUDENT') {
    const myBeds = beds.filter(b => String(b.occupantId) === String(currentUser.id));
    fillSelect('moveoutBedId', myBeds, b => `${b.dormitory} · ${b.bedNo}`, '当前没有入住床位');
  }
  const wrap = document.getElementById('bedsWrap');
  wrap.innerHTML = '<table><thead><tr><th>宿舍</th><th>床位</th><th>状态</th><th>入住学生</th><th>操作</th></tr></thead><tbody>' +
    beds.map(b => {
      const actions = [];
      if (isAdminOrManager()) {
        if (b.status === 'VACANT') {
          actions.push(`<button class=\"inline-action\" onclick=\"quickAssign(this, ${b.id})\">分配到此床</button>`);
          actions.push(`<button class=\"inline-action\" onclick=\"setBedStatus(this, ${b.id}, 'MAINTENANCE')\">设为维修中</button>`);
        } else if (b.status === 'OCCUPIED') {
          actions.push(`<button class=\"inline-action\" onclick=\"quickRelease(this, ${b.id})\">腾空</button>`);
        } else if (b.status === 'MAINTENANCE') {
          actions.push(`<button class=\"inline-action\" onclick=\"setBedStatus(this, ${b.id}, 'VACANT')\">恢复空闲</button>`);
        }
        actions.push(`<button class=\"inline-action\" onclick=\"editBed(this, ${b.id})\">编辑</button>`);
        if (b.status === 'VACANT') {
          actions.push(`<button class=\"inline-action danger\" onclick=\"deleteBed(this, ${b.id})\">删除</button>`);
        } else if (b.status === 'MAINTENANCE' && !b.occupantName) {
          actions.push(`<button class=\"inline-action danger\" onclick=\"deleteBed(this, ${b.id})\">删除</button>`);
        }
      }
      const buttons = actions.join('');
      const statusText = b.status || '-';
      return `<tr><td>${escapeHtml(b.dormitory)}</td><td>${escapeHtml(b.bedNo)}</td><td><span class="${bedStatusClass(statusText)}">${escapeHtml(statusLabel(statusText))}</span></td><td>${escapeHtml(b.occupantName || '-')}</td><td>${buttons || '-'}</td></tr>`;
    }).join('') + '</tbody></table>';
}

async function quickAssign(btn, bedId) {
  if (currentUser.role !== 'ADMIN' && currentUser.role !== 'DORM_MANAGER') {
    showLocalTip('仅管理员或宿管可分配床位', 'warn');
    return;
  }
  const studentId = document.getElementById('assignStudent')?.value;
  if (!studentId) {
    showLocalTip('请先选择要分配的学生', 'warn');
    return;
  }
  await runAction('分配床位', async () => {
    await api(`/beds/${bedId}/occupy`, {
      method: 'PATCH',
      body: JSON.stringify({ studentId: Number(studentId) })
    });
    await loadBeds();
    await loadDashboard();
  }, { button: btn });
}

async function quickRelease(btn, bedId) {
  if (currentUser.role !== 'ADMIN' && currentUser.role !== 'DORM_MANAGER') {
    showLocalTip('仅管理员或宿管可腾退床位', 'warn');
    return;
  }
  await runAction('腾退床位', async () => {
    await api(`/beds/${bedId}/release`, { method: 'PATCH', body: JSON.stringify({}) });
    await loadBeds();
    await loadDashboard();
  }, { button: btn });
}

async function setBedStatus(btn, bedId, status) {
  if (!isAdminOrManager()) {
    showLocalTip('仅管理员或宿管可变更床位状态', 'warn');
    return;
  }
  const actionName = status === 'MAINTENANCE' ? '设为维修中' : '恢复空闲';
  await runAction(actionName, async () => {
    await api(`/beds/${bedId}/state`, { method: 'PATCH', body: JSON.stringify({ status }) });
    await loadBeds();
    await loadDashboard();
  }, { button: btn });
}

async function editBed(btn, id) {
  if (!isAdminOrManager()) {
    showLocalTip('仅管理员或宿管可编辑床位', 'warn');
    return;
  }
  const target = findById(cachedBeds, id);
  if (!target) {
    showLocalTip('未找到当前床位', 'warn');
    return;
  }
  const bedNo = trimOrNull(prompt('编辑床号', target.bedNo));
  if (!bedNo) {
    return;
  }
  const dormitoryId = trimOrNull(prompt('所属宿舍ID（不改请留空）', String(target.dormitoryId || '')));
  const payload = { bedNo };
  if (dormitoryId) {
    const did = toNumberOrNull(dormitoryId);
    if (did === null) {
      showLocalTip('所属宿舍ID格式不对', 'warn');
      return;
    }
    payload.dormitoryId = did;
  }
  await runAction('编辑床位', async () => {
    await api(`/beds/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
    await loadBeds();
    await loadDashboard();
  }, { button: btn });
}

async function deleteBed(btn, id) {
  if (!isAdminOrManager()) {
    showLocalTip('仅管理员或宿管可删除床位', 'warn');
    return;
  }
  const ok = window.confirm('确认删除该床位吗？');
  if (!ok) {
    return;
  }
  await runAction('删除床位', async () => {
    await api(`/beds/${id}`, { method: 'DELETE', body: JSON.stringify({}) });
    await loadBeds();
    await loadDashboard();
  }, { button: btn });
}

async function editBuilding(btn, id) {
  if (!isAdmin()) {
    showLocalTip('仅管理员可编辑宿舍楼', 'warn');
    return;
  }
  const target = findById(cachedBuildings, id);
  const name = trimOrNull(prompt('编辑宿舍楼名称', target ? target.name : ''));
  if (!name) {
    return;
  }
  const address = trimOrNull(prompt('编辑宿舍楼地址', target ? (target.address || '') : ''));
  const payload = { name };
  if (address) {
    payload.address = address;
  }
  await runAction('编辑宿舍楼', async () => {
    await api(`/buildings/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
    await refreshAdminData();
  }, { button: btn });
}

async function deleteBuilding(btn, id) {
  if (!isAdmin()) {
    showLocalTip('仅管理员可删除宿舍楼', 'warn');
    return;
  }
  const ok = window.confirm('确认删除该宿舍楼吗？');
  if (!ok) {
    return;
  }
  await runAction('删除宿舍楼', async () => {
    await api(`/buildings/${id}`, { method: 'DELETE', body: JSON.stringify({}) });
    await refreshAdminData();
  }, { button: btn });
}

async function editFloor(btn, id) {
  if (!isAdmin()) {
    showLocalTip('仅管理员可编辑楼层', 'warn');
    return;
  }
  const target = findById(cachedFloors, id);
  const name = trimOrNull(prompt('编辑楼层名称', target ? target.name : ''));
  if (!name) {
    return;
  }
  const buildingId = trimOrNull(prompt('所属楼栋ID（不改请留空）', target ? String(target.buildingId || '') : ''));
  const payload = { name };
  if (buildingId) {
    const bid = toNumberOrNull(buildingId);
    if (bid === null) {
      showLocalTip('所属楼栋ID格式不对', 'warn');
      return;
    }
    payload.buildingId = bid;
  }
  await runAction('编辑楼层', async () => {
    await api(`/floors/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
    await refreshAdminData();
  }, { button: btn });
}

async function deleteFloor(btn, id) {
  if (!isAdmin()) {
    showLocalTip('仅管理员可删除楼层', 'warn');
    return;
  }
  const ok = window.confirm('确认删除该楼层吗？');
  if (!ok) {
    return;
  }
  await runAction('删除楼层', async () => {
    await api(`/floors/${id}`, { method: 'DELETE', body: JSON.stringify({}) });
    await refreshAdminData();
  }, { button: btn });
}

async function editDorm(btn, id) {
  if (!isAdmin()) {
    showLocalTip('仅管理员可编辑宿舍', 'warn');
    return;
  }
  const target = findById(cachedDormitories, id);
  const dormCode = trimOrNull(prompt('编辑宿舍号', target ? target.dormCode : ''));
  if (!dormCode) {
    return;
  }
  const buildingId = trimOrNull(prompt('所属楼栋ID（不改请留空）', target ? String(target.buildingId || '') : ''));
  const floorId = trimOrNull(prompt('所属楼层ID（不改请留空）', target ? String(target.floorId || '') : ''));
  const capacity = trimOrNull(prompt('容量（不改请留空）', target ? String(target.capacity || '') : ''));
  const preferenceTags = trimOrNull(prompt('宿舍特点（用逗号分隔）', target ? (target.preferenceTags || '') : ''));
  const payload = { dormCode };
  if (buildingId) {
    const bid = toNumberOrNull(buildingId);
    if (bid === null) {
      showLocalTip('所属楼栋ID格式不对', 'warn');
      return;
    }
    payload.buildingId = bid;
  }
  if (floorId) {
    const fid = toNumberOrNull(floorId);
    if (fid === null) {
      showLocalTip('所属楼层ID格式不对', 'warn');
      return;
    }
    payload.floorId = fid;
  }
  if (capacity) {
    const cap = toNumberOrNull(capacity);
    if (cap === null || cap <= 0) {
      showLocalTip('容量需填写正整数', 'warn');
      return;
    }
    payload.capacity = cap;
  }
  if (preferenceTags) {
    payload.preferenceTags = preferenceTags;
  }
  await runAction('编辑宿舍', async () => {
    await api(`/dormitories/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
    await refreshAdminData();
  }, { button: btn });
}

async function deleteDorm(btn, id) {
  if (!isAdmin()) {
    showLocalTip('仅管理员可删除宿舍', 'warn');
    return;
  }
  const ok = window.confirm('确认删除该宿舍吗？');
  if (!ok) {
    return;
  }
  await runAction('删除宿舍', async () => {
    await api(`/dormitories/${id}`, { method: 'DELETE', body: JSON.stringify({}) });
    await refreshAdminData();
  }, { button: btn });
}

async function loadMoveApplications() {
  const moveIn = await api('/move-in');
  const moveOut = await api('/move-out');
  const wrap = document.getElementById('moveAppWrap');
  const html = [
    '<h4>入住申请</h4>',
    '<table><thead><tr><th>ID</th><th>学生</th><th>个人偏好</th><th>意向宿舍</th><th>原因</th><th>状态</th><th>备注</th><th>操作</th></tr></thead><tbody>',
    ...moveIn.map(a => {
      const isPending = a.status === 'PENDING';
      const ops = isPending && ['ADMIN', 'DORM_MANAGER'].includes(currentUser.role)
        ? `<button class="inline-action" onclick="approveMoveIn(this, ${a.id})">通过</button>
           <button class="inline-action" onclick="rejectMoveIn(this, ${a.id})">驳回</button>`
        : '-';
      return `<tr><td>${escapeHtml(a.id)}</td><td>${escapeHtml(a.student || '-')}</td><td>${escapeHtml(preferenceLabel(a.preferenceTags))}</td><td>${escapeHtml(a.preferredDormitory || '-')}</td><td>${escapeHtml(a.reason)}</td><td>${escapeHtml(statusLabel(a.status))}</td><td>${escapeHtml(a.comment || '-')}</td><td>${ops}</td></tr>`;
    }).join(''),
    '</tbody></table>',
    '<h4>退宿申请</h4>',
    '<table><thead><tr><th>ID</th><th>学生</th><th>床位</th><th>原因</th><th>状态</th><th>操作</th></tr></thead><tbody>',
    ...moveOut.map(a => {
      const isPending = a.status === 'PENDING';
      const ops = isPending && ['ADMIN', 'DORM_MANAGER'].includes(currentUser.role)
          ? `<button class="inline-action" onclick="approveMoveOut(this, ${a.id})">通过</button>
           <button class="inline-action" onclick="rejectMoveOut(this, ${a.id})">驳回</button>`
        : '-';
      return `<tr><td>${escapeHtml(a.id)}</td><td>${escapeHtml(a.student || '-')}</td><td>${escapeHtml(a.bed || '-')}</td><td>${escapeHtml(a.reason)}</td><td>${escapeHtml(statusLabel(a.status))}</td><td>${ops}</td></tr>`;
    }).join(''),
    '</tbody></table>'
  ].join('');
  wrap.innerHTML = html;
}

async function approveMoveIn(btn, id) {
  await runAction('审批入住申请', async () => {
    await api(`/move-in/${id}/approve`, { method: 'PATCH', body: JSON.stringify({}) });
    await loadMoveApplications();
    await loadBeds();
    await loadDashboard();
  }, { button: btn });
}

async function rejectMoveIn(btn, id) {
  await runAction('驳回入住申请', async () => {
    await api(`/move-in/${id}/reject`, { method: 'PATCH', body: JSON.stringify({ comment: '驳回' }) });
    await loadMoveApplications();
    await loadDashboard();
  }, { button: btn });
}

async function approveMoveOut(btn, id) {
  await runAction('审批退宿申请', async () => {
    await api(`/move-out/${id}/approve`, { method: 'PATCH', body: JSON.stringify({ comment: '通过' }) });
    await loadMoveApplications();
    await loadBeds();
    await loadDashboard();
  }, { button: btn });
}

async function rejectMoveOut(btn, id) {
  await runAction('驳回退宿申请', async () => {
    await api(`/move-out/${id}/reject`, { method: 'PATCH', body: JSON.stringify({ comment: '驳回' }) });
    await loadMoveApplications();
    await loadDashboard();
  }, { button: btn });
}

async function loadRepairs() {
  const arr = await api('/repairs');
  const wrap = document.getElementById('repairWrap');
  wrap.innerHTML = '<table><thead><tr><th>ID</th><th>学生</th><th>位置</th><th>描述</th><th>状态</th><th>处理</th></tr></thead><tbody>' +
    arr.map(r => {
      let ops = '-';
      if (isAdminOrManager() && r.status === 'PENDING') {
        ops = `<button class="inline-action" onclick="updateRepair(this, ${r.id}, 'PROCESSING')">受理</button>`;
      } else if (isAdminOrManager() && r.status === 'PROCESSING') {
        ops = `<button class="inline-action" onclick="updateRepair(this, ${r.id}, 'DONE')">完成</button>`;
      }
      return `<tr><td>${escapeHtml(r.id)}</td><td>${escapeHtml(r.student || '-')}</td><td>${escapeHtml(r.location)}</td><td>${escapeHtml(r.description)}</td><td>${escapeHtml(repairStatusLabel(r.status))}</td><td>${ops}</td></tr>`;
    }).join('') + '</tbody></table>';
}

async function updateRepair(btn, id, status) {
  const actionName = status === 'DONE' ? '完成报修' : '受理报修';
  await runAction(actionName, async () => {
    await api(`/repairs/${id}/process`, { method: 'PATCH', body: JSON.stringify({ status }) });
    await loadRepairs();
  }, { button: btn });
}

async function loadBills() {
  const bills = currentUser.role === 'STUDENT'
    ? await api(`/bills?studentId=${currentUser.id}`)
    : await api('/bills');
  const wrap = document.getElementById('billWrap');
  wrap.innerHTML = '<table><thead><tr><th>ID</th><th>学生</th><th>月度</th><th>总计</th><th>状态</th><th>操作</th></tr></thead><tbody>' +
    bills.map(b => {
      const actionText = currentUser.role === 'STUDENT' ? '模拟缴费' : '标记已缴';
      const btn = b.state === 'UNPAID' ? `<button class="inline-action" onclick="payBill(this, ${b.id})">${actionText}</button>` : '-';
      return `<tr><td>${escapeHtml(b.id)}</td><td>${escapeHtml(b.studentName)}</td><td>${escapeHtml(b.month)}</td><td>${escapeHtml(b.total)}</td><td>${escapeHtml(statusLabel(b.state))}</td><td>${btn}</td></tr>`;
    }).join('') + '</tbody></table>';
}

async function payBill(btn, id) {
  await runAction('缴费', async () => {
    await api(`/bills/${id}/pay`, { method: 'PATCH', body: JSON.stringify({}) });
    await loadBills();
    await loadDashboard();
  }, { button: btn });
}

async function loadNotices() {
  const list = await api('/notices');
  const wrap = document.getElementById('noticeWrap');
  wrap.innerHTML = list.map(n => {
    const scope = n.scope === 'BUILDING' ? `指定楼栋：${n.building || '-'}` : '全体';
    return `<div class="card"><h3>${escapeHtml(n.title)}</h3><p>${escapeHtml(n.content)}</p><small>${escapeHtml(scope)}</small></div>`;
  }).join('');
}

async function refreshAdminData() {
  await loadAdminData();
  setUserTip('系统数据已刷新');
  await sleep(800);
  await loadBuildingsDorms();
}

async function addBuilding() {
  if (!isAdmin()) {
    showLocalTip('仅管理员可新增宿舍楼', 'warn');
    return;
  }
  const name = document.getElementById('buildingName').value.trim();
  const address = document.getElementById('buildingAddress').value.trim();
  if (!name) {
    showLocalTip('请输入宿舍楼名称', 'warn');
    return;
  }
  await runAction('新增宿舍楼', async () => {
    await api('/buildings', { method: 'POST', body: JSON.stringify({ name, address }) });
    document.getElementById('buildingName').value = '';
    document.getElementById('buildingAddress').value = '';
    await refreshAdminData();
  }, { button: document.getElementById('addBuildingBtn') });
}

async function addFloor() {
  if (!isAdmin()) {
    showLocalTip('仅管理员可新增楼层', 'warn');
    return;
  }
  const buildingId = document.getElementById('floorBuilding').value;
  const name = document.getElementById('floorName').value.trim();
  if (!buildingId || !name) {
    showLocalTip('请选择楼栋并填写楼层名称', 'warn');
    return;
  }
  await runAction('新增楼层', async () => {
    await api('/floors', { method: 'POST', body: JSON.stringify({ name, building: { id: Number(buildingId) } }) });
    document.getElementById('floorName').value = '';
    await refreshAdminData();
  }, { button: document.getElementById('addFloorBtn') });
}

async function addDorm() {
  if (!isAdmin()) {
    showLocalTip('仅管理员可新增宿舍', 'warn');
    return;
  }
  const dormCode = document.getElementById('dormCode').value.trim();
  const buildingId = document.getElementById('dormBuilding').value;
  const floorId = document.getElementById('dormFloor').value;
  const capacity = Number(document.getElementById('dormCapacity').value || 0);
  const preferenceTags = readDormPreferenceTags();
  if (!dormCode || !buildingId || !floorId || capacity <= 0) {
    showLocalTip('请完整填写宿舍信息', 'warn');
    return;
  }
  await runAction('新增宿舍', async () => {
    await api('/dormitories', {
      method: 'POST',
      body: JSON.stringify({ dormCode, capacity, preferenceTags, building: { id: Number(buildingId) }, floor: { id: Number(floorId) } })
    });
    document.getElementById('dormCode').value = '';
    document.getElementById('dormCapacity').value = '6';
    await refreshAdminData();
  }, { button: document.getElementById('addDormBtn') });
}

async function addAdminBed() {
  if (!isAdminOrManager()) {
    showLocalTip('仅管理员/宿管可新增床位', 'warn');
    return;
  }
  const dormitoryId = document.getElementById('bedDormSelect').value;
  const bedNo = document.getElementById('bedNo').value.trim();
  if (!dormitoryId || !bedNo) {
    showLocalTip('请选择宿舍并填写床位号', 'warn');
    return;
  }
  await runAction('新增床位', async () => {
    await api('/beds', { method: 'POST', body: JSON.stringify({ dormitoryId: Number(dormitoryId), bedNo }) });
    document.getElementById('bedNo').value = '';
    await loadBeds();
    await loadDashboard();
  }, { button: document.getElementById('addBedBtn') });
}

async function addUser() {
  if (!isAdmin()) {
    showLocalTip('仅管理员可新增用户', 'warn');
    return;
  }
  const username = document.getElementById('userUsername').value.trim();
  const password = document.getElementById('userPassword').value.trim();
  const fullName = document.getElementById('userFullName').value.trim();
  const role = document.getElementById('userRole').value;
  const buildingId = document.getElementById('userBuilding').value;
  if (!username || !password || !fullName || !role) {
    showLocalTip('请完整填写用户信息', 'warn');
    return;
  }
  const payload = { username, password, fullName, role };
  if (buildingId) {
    payload.building = { id: Number(buildingId) };
  }
  await runAction('新增用户', async () => {
    await api('/users', { method: 'POST', body: JSON.stringify(payload) });
    document.getElementById('userUsername').value = '';
    document.getElementById('userPassword').value = '';
    document.getElementById('userFullName').value = '';
    document.getElementById('userBuilding').value = '';
    await refreshAdminData();
  }, { button: document.getElementById('addUserBtn') });
}

document.getElementById('submitMoveIn').addEventListener('click', async (e) => {
  const reason = document.getElementById('moveinReason').value.trim();
  const preferredDormitoryId = document.getElementById('moveinDorm').value;
  const preference = readStudentPreference();
  const payload = { reason, preferenceTags: Object.values(preference).join(',') };
  if (preferredDormitoryId) {
    payload.preferredDormitoryId = Number(preferredDormitoryId);
  }
  if (!reason) {
    showLocalTip('请填写入住原因', 'warn');
    return;
  }
  await runAction('提交入住申请', async () => {
    await api('/move-in', { method: 'POST', body: JSON.stringify(payload) });
    document.getElementById('moveinReason').value = '';
    document.getElementById('recommendationWrap').innerHTML = '';
    await loadMoveApplications();
  }, { button: e.currentTarget });
});

document.getElementById('recommendDormBtn').addEventListener('click', async (e) => {
  await recommendDormitories(e.currentTarget);
});

document.getElementById('submitMoveOut').addEventListener('click', async (e) => {
  const reason = document.getElementById('moveoutReason').value.trim();
  const bedId = toNumberOrNull(document.getElementById('moveoutBedId').value);
  if (!bedId) {
    showLocalTip('当前没有可退宿的床位', 'warn');
    return;
  }
  if (!reason) {
    showLocalTip('请填写退宿原因', 'warn');
    return;
  }
  await runAction('提交退宿申请', async () => {
    await api('/move-out', { method: 'POST', body: JSON.stringify({ reason, bedId }) });
    document.getElementById('moveoutReason').value = '';
    document.getElementById('moveoutBedId').value = '';
    await loadMoveApplications();
  }, { button: e.currentTarget });
});

document.getElementById('submitRepair').addEventListener('click', async (e) => {
  const location = document.getElementById('repairLocation').value.trim();
  const description = document.getElementById('repairDesc').value.trim();
  if (!location || !description) {
    showLocalTip('请填写报修位置和问题描述', 'warn');
    return;
  }
  await runAction('提交报修', async () => {
    await api('/repairs', { method: 'POST', body: JSON.stringify({ location, description }) });
    document.getElementById('repairLocation').value = '';
    document.getElementById('repairDesc').value = '';
    await loadRepairs();
  }, { button: e.currentTarget });
});

document.getElementById('addBill').addEventListener('click', async (e) => {
  const studentId = document.getElementById('billStudentId').value.trim();
  const month = document.getElementById('billMonth').value.trim();
  const electricity = document.getElementById('billElec').value.trim();
  const water = document.getElementById('billWater').value.trim();
  const otherFee = document.getElementById('billOther').value.trim();
  if (!studentId) {
    showLocalTip('请先选择学生', 'warn');
    return;
  }
  if (!month) {
    showLocalTip('请选择账单月份', 'warn');
    return;
  }
  const fees = [electricity, water, otherFee].map(Number);
  if (fees.some(value => Number.isNaN(value) || value < 0)) {
    showLocalTip('费用应为不小于 0 的数字', 'warn');
    return;
  }
  await runAction('录入账单', async () => {
    await api('/bills', {
      method: 'POST',
      body: JSON.stringify({ studentId, month, electricity, water, otherFee })
    });
    document.getElementById('billStudentId').value = '';
    document.getElementById('billMonth').value = '';
    document.getElementById('billElec').value = '0';
    document.getElementById('billWater').value = '0';
    document.getElementById('billOther').value = '0';
    await loadBills();
  }, { button: e.currentTarget });
});

document.getElementById('addNotice').addEventListener('click', async (e) => {
  const title = document.getElementById('noticeTitle').value.trim();
  const content = document.getElementById('noticeContent').value.trim();
  const scope = document.getElementById('noticeScope').value;
  const buildingId = document.getElementById('noticeBuilding').value;
  if (!title || !content) {
    showLocalTip('请填写标题和内容', 'warn');
    return;
  }
  if (scope === 'BUILDING' && !buildingId) {
    showLocalTip('按楼栋发布公告请先选择楼栋', 'warn');
    return;
  }
  const payload = { title, content, scope };
  if (scope === 'BUILDING' && buildingId) {
    payload.buildingId = Number(buildingId);
  }
  await runAction('发布公告', async () => {
    await api('/notices', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    document.getElementById('noticeTitle').value = '';
    document.getElementById('noticeContent').value = '';
    await loadNotices();
  }, { button: e.currentTarget });
});

document.getElementById('addBuildingBtn').addEventListener('click', addBuilding);
document.getElementById('addFloorBtn').addEventListener('click', addFloor);
document.getElementById('addDormBtn').addEventListener('click', addDorm);
document.getElementById('addBedBtn').addEventListener('click', addAdminBed);
document.getElementById('addUserBtn').addEventListener('click', addUser);
document.getElementById('refreshAdminData').addEventListener('click', refreshAdminData);
document.getElementById('dormBuilding').addEventListener('change', onDormBuildingChange);

document.getElementById('refreshBeds').addEventListener('click', loadBeds);

document.getElementById('logoutBtn').addEventListener('click', async () => {
  await api('/auth/logout', { method: 'POST', body: JSON.stringify({}) });
  clearCachedMe();
  window.location.href = 'login.html';
});

init();
