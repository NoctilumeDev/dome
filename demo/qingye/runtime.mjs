import { createQingyeModel } from './model.mjs';
// Repository-owned page logic is compiled at build time; no visitor-supplied code is evaluated.
const model = createQingyeModel();
const { Vue, QingyeTemplates: templates, QingyeSources: sources } = window;
const cache = {};
let page,
  vm,
  tabHidden = false,
  routingVersion = 0;
const app = {
  globalData: { user: model.me() },
  setSession(session) {
    wx.setStorageSync('qingye-token', session.token);
    wx.setStorageSync('qingye-user', session.user);
    this.globalData.user = session.user;
  },
  logout() {
    wx.removeStorageSync('qingye-token');
    wx.removeStorageSync('qingye-user');
    this.globalData.user = null;
    wx.reLaunch({ url: '/pages/login/index' });
  },
};
const storageKey = (key) => 'dome-demo-wx:' + key;
const toast = (title) => {
  const node = document.getElementById('qy-toast');
  node.textContent = title;
  node.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (node.hidden = true), 2400);
};
function navigate(url) {
  location.hash = url.replace(/^\//, '');
}
function dialog(options) {
  const node = document.getElementById('qy-dialog'),
    input = document.getElementById('qy-dialog-input');
  document.getElementById('qy-dialog-text').textContent = options.content;
  input.hidden = !options.editable;
  input.value = '';
  input.placeholder = options.placeholderText || '审核意见（可选）';
  node.returnValue = '';
  node.addEventListener(
    'close',
    () =>
      options.success?.({
        confirm: node.returnValue === 'confirm',
        cancel: node.returnValue !== 'confirm',
        content: input.value,
      }),
    { once: true }
  );
  node.showModal();
}
const wx = {
  getStorageSync(key) {
    try {
      return JSON.parse(sessionStorage.getItem(storageKey(key)));
    } catch (_) {
      return null;
    }
  },
  setStorageSync(key, value) {
    sessionStorage.setItem(storageKey(key), JSON.stringify(value));
  },
  removeStorageSync(key) {
    sessionStorage.removeItem(storageKey(key));
  },
  navigateTo: ({ url }) => navigate(url),
  switchTab: ({ url }) => navigate(url),
  reLaunch: ({ url }) => navigate(url),
  navigateBack() {
    if (history.state?.qingye) history.back();
    else navigate('/pages/home/index');
  },
  showToast: ({ title }) => toast(title),
  showModal: dialog,
  stopPullDownRefresh() {},
  hideKeyboard() {
    document.activeElement?.blur();
  },
  pageScrollTo({ selector }) {
    document.querySelector(selector)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  },
  login({ fail }) {
    fail?.();
  },
};
window.wx = wx;
window.getApp = () => app;
window.getCurrentPages = () => (page ? [page] : []);
window.Page = (definition) => {
  page = {
    ...definition,
    data: definition.data,
    route: '',
    setData(values) {
      setData(this, values);
    },
    getTabBar() {
      return {
        setData(values) {
          if ('hidden' in values) tabHidden = values.hidden;
          updateTabs();
        },
      };
    },
  };
};
function setData(controller, values) {
  for (const [key, value] of Object.entries(values)) {
    const parts = key.replace(/\[(\d+)\]/g, '.$1').split('.');
    let target = controller.data;
    for (const part of parts.slice(0, -1)) {
      if (!target[part]) Vue.set(target, part, {});
      target = target[part];
    }
    Vue.set(target, parts.at(-1), value);
  }
}
function resolve(parent, name) {
  const parts = parent.split('/').slice(0, -1);
  for (const p of name.split('/')) {
    if (p === '..') parts.pop();
    else if (p !== '.') parts.push(p);
  }
  return parts.join('/').replace(/\.js$/, '');
}
function requireModule(id) {
  if (cache[id]) return cache[id].exports;
  if (id === 'utils/request')
    return {
      guard() {
        if (!wx.getStorageSync('qingye-token')) {
          wx.reLaunch({ url: '/pages/login/index' });
          return false;
        }
        return true;
      },
      async request(path, method, body) {
        try {
          const data = model.handle(path, method, body);
          if (path === '/auth/demo') configure();
          return data;
        } catch (e) {
          toast(e.message);
          throw e;
        }
      },
      confirm(content, editable = false) {
        return new Promise((resolve) =>
          dialog({
            content,
            editable,
            success: (result) => resolve(result.confirm ? result.content || true : false),
          })
        );
      },
    };
  if (id === 'utils/keyboard')
    return {
      keyboard() {
        return {
          focus(selector) {
            if (selector)
              document
                .querySelector(selector)
                ?.scrollIntoView({ block: 'center', behavior: 'smooth' });
          },
          blur() {},
          change() {},
          reset() {},
        };
      },
    };
  const module = { exports: {} };
  cache[id] = module;
  if (!sources[id]) throw new Error('Browser source missing: ' + id);
  sources[id](module, module.exports, (name) => requireModule(resolve(id, name)));
  return module.exports;
}
function dataset(node) {
  return Object.fromEntries(
    Object.entries(node?.dataset || {}).map(([key, value]) => [
      key,
      /^\d+$/.test(value) ? Number(value) : value,
    ])
  );
}
function eventDetail(event) {
  if (event?.detail && typeof event.detail === 'object') return event;
  const target = event?.currentTarget;
  return {
    detail: {
      value: target?.type === 'checkbox' ? target.checked : target?.value,
      ...(event && !event.type ? event : {}),
    },
    currentTarget: { dataset: dataset(target) },
  };
}
const helpers = {
  __asset(value) {
    return String(value || '').replace(/^\/assets\//, 'assets/');
  },
};
Vue.component('activity-card', {
  props: { item: Object, variant: { type: String, default: 'row' } },
  data: () => ({ failed: false }),
  template: templates['activity-card'].template,
  methods: {
    ...helpers,
    __event(name) {
      if (name === 'imageError') this.failed = true;
      else if (name === 'open') this.$emit('open', { id: this.item.id });
    },
  },
});
Vue.component('qy-picker', {
  props: ['range', 'value', 'mode', 'disabled'],
  template:
    '<div class="qy-picker"><slot></slot><input v-if="mode === \'date\' || mode === \'time\'" :type="mode" :value="value" :disabled="disabled" @change="change"><select v-else :value="value" :disabled="disabled" @change="change"><option v-for="(item,index) in range" :key="index" :value="index">{{item}}</option></select></div>',
  methods: {
    change(e) {
      const data = Object.fromEntries(
        Object.entries(this.$attrs)
          .filter(([k]) => k.startsWith('data-'))
          .map(([k, v]) => [k.slice(5), v])
      );
      this.$emit('change', {
        detail: {
          value: ['date', 'time'].includes(this.mode) ? e.target.value : Number(e.target.value),
        },
        currentTarget: { dataset: data },
      });
    },
  },
});
const globalStyle = document.createElement('style');
globalStyle.textContent = templates.globalCSS + '\n' + templates['activity-card'].css;
document.head.appendChild(globalStyle);
const pageStyle = document.createElement('style');
document.head.appendChild(pageStyle);
function updateTabs() {
  const current = page?.route.split('/')[1],
    tabs = document.getElementById('qy-tabs');
  tabs.hidden = tabHidden || !['home', 'clubs', 'me'].includes(current);
  tabs.style.display = tabs.hidden ? 'none' : 'flex';
  tabs
    .querySelectorAll('button')
    .forEach((b) => b.classList.toggle('selected', b.dataset.route === current));
  document.getElementById('qy-back').hidden = ['home', 'me', 'login'].includes(current);
}
async function render() {
  const version = ++routingVersion;
  if (page) {
    page.onHide?.();
    page.onUnload?.();
  }
  tabHidden = false;
  vm?.$destroy();
  const match = location.hash.slice(1).match(/^\/?pages\/(\w+)\/index(?:\?(.*))?$/);
  const name = match && templates[match[1]] ? match[1] : 'home';
  const id = `pages/${name}/index`;
  delete cache[id];
  requireModule(id);
  const controller = page;
  controller.route = id;
  for (const key of templates[name].keys)
    if (!(key in controller.data)) controller.data[key] = undefined;
  const root = document.getElementById('qingye-app');
  root.innerHTML = '<div id="qy-view"></div>';
  vm = new Vue({
    el: '#qy-view',
    data: controller.data,
    template: templates[name].template,
    methods: {
      ...helpers,
      __event(method, original) {
        if (original?.isComposing) return;
        if (controller[method]) return controller[method](eventDetail(original));
      },
    },
  });
  pageStyle.textContent = templates[name].css;
  document.getElementById('qy-title').textContent = {
    home: '青野',
    clubs: '青野 · 社团',
    me: '青野 · 我的',
    activity: '校园活动',
    equipment: '器材室',
    workbench: '校园工作台',
    editor: '校园工作台',
    notifications: '我的消息',
    assistant: '问问青野',
    login: '青野',
  }[name];
  if (name === 'assistant') {
    const note = document.createElement('p');
    note.className = 'footnote';
    note.style.padding = '0 18px';
    note.textContent = '浏览器演示：本地样例匹配，未调用真实模型。';
    root.prepend(note);
  }
  history.replaceState({ qingye: name !== 'home' }, '');
  updateTabs();
  await controller.onLoad?.(Object.fromEntries(new URLSearchParams(match?.[2] || '')));
  if (version !== routingVersion) return;
  await controller.onShow?.();
  updateTabs();
}
function configure() {
  app.globalData.user = model.me();
  window.DomeDemo.configure({
    roles: model.store.data.users
      .filter((u) => u.id !== 4)
      .map((u) => ({ id: u.id, label: u.name })),
    current: model.me().id,
    switchRole(id) {
      model.switchRole(id);
      app.setSession({ token: `demo-user-${id}`, user: model.me() });
      navigate('/pages/home/index');
      if (page?.route === 'pages/home/index') render();
      configure();
    },
    reset() {
      model.reset();
      app.setSession({ token: 'demo-user-1', user: model.me() });
      navigate('/pages/home/index');
      render();
      configure();
    },
  });
}
function resize() {
  document.documentElement.style.setProperty('--rpx', Math.min(innerWidth, 430) / 750 + 'px');
}
addEventListener('resize', resize);
resize();
document.getElementById('qy-tabs').addEventListener('click', (e) => {
  const button = e.target.closest('button');
  if (button) {
    const route = button.dataset.route;
    if (route === 'clubs' && page?.route !== 'pages/clubs/index')
      app.globalData.clubReturnTo = '/' + page.route;
    navigate(`/pages/${route}/index`);
  }
});
document
  .getElementById('qy-back')
  .addEventListener('click', () =>
    page?.route === 'pages/clubs/index'
      ? navigate(app.globalData.clubReturnTo || '/pages/home/index')
      : wx.navigateBack()
  );
addEventListener('hashchange', render);
if (!wx.getStorageSync('qingye-token'))
  app.setSession({ token: `demo-user-${model.me().id}`, user: model.me() });
configure();
await render();
