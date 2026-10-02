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
    reset.addEventListener('click', () => {
      if (confirm('重置当前项目的演示数据？其他项目的数据会保留。')) options.reset();
    });
    bar.append(back, label, select, reset);
    document.body.prepend(bar);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render);
})();
