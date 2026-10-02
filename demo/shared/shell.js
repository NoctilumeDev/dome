(function () {
  let options;
  const source = document.currentScript;
  const home = new URL('../index.html', source.src).href;
  window.DomeDemo = {
    configure(value) {
      options = value;
      render();
    },
  };
  function confirmReset(trigger) {
    if (document.getElementById('demo-reset-dialog')) return;
    const dialog = document.createElement('dialog');
    dialog.id = 'demo-reset-dialog';
    dialog.setAttribute('aria-labelledby', 'demo-reset-title');
    dialog.setAttribute('aria-describedby', 'demo-reset-description');
    const title = document.createElement('h2');
    title.id = 'demo-reset-title';
    title.textContent = '重新体验当前项目？';
    const description = document.createElement('p');
    description.id = 'demo-reset-description';
    description.textContent = '当前项目将恢复为初始样例，其他项目的数据会保留。';
    const actions = document.createElement('div');
    actions.className = 'demo-reset-actions';
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.textContent = '取消';
    cancel.addEventListener('click', () => dialog.close());
    const confirm = document.createElement('button');
    confirm.type = 'button';
    confirm.className = 'demo-reset-confirm';
    confirm.textContent = '重置当前项目';
    confirm.addEventListener('click', () => {
      dialog.close();
      options.reset();
    });
    actions.append(cancel, confirm);
    dialog.append(title, description, actions);
    dialog.addEventListener('close', () => {
      dialog.remove();
      trigger.focus();
    });
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) dialog.close();
    });
    document.body.append(dialog);
    dialog.showModal();
    cancel.focus();
  }
  function render() {
    if (!document.body || !options) return;
    document.getElementById('demo-toolbar')?.remove();
    const bar = document.createElement('aside');
    bar.id = 'demo-toolbar';
    bar.setAttribute('aria-label', '在线演示控制栏');
    const back = document.createElement('a');
    back.href = home;
    back.textContent = '← 项目列表';
    const label = document.createElement('span');
    label.className = 'demo-label';
    label.textContent = '交互演示 · 数据仅保存在此浏览器';
    const select = document.createElement('select');
    select.setAttribute('aria-label', '切换演示身份');
    options.roles.forEach((role) => {
      const item = document.createElement('option');
      item.value = role.id;
      item.textContent = role.label;
      select.appendChild(item);
    });
    select.value = options.current;
    select.addEventListener('change', () => options.switchRole(select.value));
    const reset = document.createElement('button');
    reset.type = 'button';
    reset.textContent = '重置演示';
    reset.addEventListener('click', () => confirmReset(reset));
    bar.append(back, label, select, reset);
    document.body.prepend(bar);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render);
})();
