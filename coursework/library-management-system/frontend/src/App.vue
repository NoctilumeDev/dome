<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style>
:root {
  --primary-color: #3f8cff;
  --primary-color-dark: #296bcd;
  --text-main: #1f2937;
  --text-sub: #59616d;
  --border-color: #ebedf5;
  --line-color: #e5e9f3;
  --bg: #f4f7fb;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --surface: #ffffff;
}

* {
  box-sizing: border-box;
}

html,
body {
  width: 100%;
  min-width: 320px;
  min-height: 100%;
}

#app {
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  font-family: "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", Arial, sans-serif;
  color: var(--text-main);
  background:
    radial-gradient(circle at 0% 0%, #eef4ff 0%, transparent 35%),
    radial-gradient(circle at 100% 0%, #f2f8f8 0%, transparent 40%),
    var(--bg);
}

body {
  margin: 0;
  color: var(--text-main);
  background: transparent;
}

.text-button {
  color: var(--primary-color);
  cursor: pointer;
  font-size: 13px;
}

.text-button:hover {
  color: var(--primary-color-dark);
}

.system-layout {
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  display: flex;
  background: var(--bg);
}

.system-sidebar {
  flex: 0 0 232px;
  width: 232px;
  background: #fff;
  border-right: 1px solid var(--border-color);
  padding: 16px 10px;
  box-shadow: 0 18px 40px rgba(28, 50, 111, 0.06);
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
}

.system-sidebar-title {
  margin: 0 6px 14px 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-main);
}

.system-menu-item {
  width: 100%;
  border: 0;
  border-radius: 8px;
  margin: 4px 0;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: #304156;
  text-align: left;
  cursor: pointer;
  transition: all 0.18s;
}

.system-menu-item.is-active {
  background: linear-gradient(90deg, rgba(63, 140, 255, 0.16), rgba(63, 140, 255, 0.08));
  color: var(--primary-color-dark);
  font-weight: 600;
}

.system-main {
  flex: 1;
  width: calc(100% - 232px);
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.system-topbar {
  height: 56px;
  background: var(--surface);
  padding: 12px 18px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.system-content {
  flex: 1;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  padding: 16px;
  animation: slideFadeIn 300ms ease;
}

.system-card {
  min-width: 0;
  max-width: 100%;
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 16px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
  min-height: 100%;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.feature-shell {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  animation: fadeInUp 260ms ease;
}

.toolbar {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  padding: 14px;
  margin-bottom: 14px;
  border-radius: 12px;
  background: #f7f9ff;
  border: 1px solid var(--border-color);
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.toolbar-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.toolbar-label {
  color: var(--text-sub);
  font-size: 13px;
  white-space: nowrap;
  margin-right: 2px;
}

.toolbar-input {
  flex: 1 1 180px;
  width: auto;
  min-width: 148px;
  max-width: 240px;
}

.toolbar .el-date-editor.toolbar-input {
  flex-basis: 280px;
  min-width: 280px;
  max-width: 320px;
}

.toolbar .el-date-editor--daterange .el-range-input {
  flex: 1 1 0;
  width: 0;
  min-width: 0;
}

.toolbar .el-date-editor--daterange .el-range-separator {
  display: inline-flex;
  flex: 0 0 30px;
  align-self: stretch;
  align-items: center;
  justify-content: center;
  width: 30px;
  min-width: 30px;
  padding: 0 5px;
  color: var(--text-sub);
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.toolbar-actions {
  margin-left: auto;
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.toolbar-actions .el-button + .el-button,
.dialog-footer .el-button + .el-button {
  margin-left: 0;
}

.toolbar-divider {
  flex: 0 0 100%;
  border-top: 1px dashed var(--line-color);
  margin-top: 2px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 12px;
}

.metric-card {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: linear-gradient(130deg, #ffffff, #f9fbff);
  padding: 16px;
  box-shadow: 0 8px 20px rgba(20, 30, 54, 0.06);
}

.metric-card-title {
  color: var(--text-sub);
  font-size: 12px;
}

.metric-card-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.system-section-title {
  font-size: 18px;
  margin: 0 0 12px;
  color: #1f2937;
}

.system-table {
  border-radius: 10px;
  overflow: hidden;
  width: 100%;
  max-width: 100%;
}

.system-table .el-table__body-wrapper {
  max-width: 100%;
  overflow-x: auto;
}

.module-view-card {
  min-width: 0;
  overflow: hidden;
}

.system-pagination {
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.system-dialog {
  border-radius: 12px;
}

.dialog-card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.dialog-form-item {
  margin: 12px 0;
}

.btn-primary {
  background: linear-gradient(90deg, #3f8cff, #5f6cff) !important;
  border: 0 !important;
  color: #fff !important;
}

.btn-ghost {
  background: #f3f7ff !important;
  border: 1px solid #dbe6ff !important;
  color: #4b6385 !important;
}

.btn-danger-soft {
  background: #ffe9ec !important;
  color: #e14363 !important;
  border-color: transparent !important;
}

.top-bar {
  font-size: 13px;
  color: var(--text-sub);
  margin-right: 4px;
  white-space: nowrap;
}

.dialog-title,
.dialog-hover {
  font-size: 13px;
  color: #475569;
}

.dialog-input {
  width: 100%;
  margin: 8px 0 14px;
  border: 1px solid var(--line-color);
  border-radius: 8px;
  padding: 8px 10px;
  outline: none;
}

.dialog-input:focus {
  border-color: #a2c2ff;
  box-shadow: 0 0 0 3px rgba(63, 140, 255, 0.16);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.customer {
  margin: 0 !important;
}

.system-empty {
  display: block;
  width: 100%;
  color: #8792a2;
  text-align: center;
  padding: 24px 0;
}

@keyframes slideFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1200px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(150px, 1fr));
  }

  .toolbar-actions {
    flex: 1 0 100%;
    margin-left: 0;
  }
}

@media (max-width: 900px) {
  .system-sidebar {
    flex-basis: 74px;
    width: 74px;
    padding: 12px 8px;
  }

  .system-main {
    width: calc(100% - 74px);
  }

  .system-sidebar-title,
  .system-menu-item span {
    display: none;
  }

  .system-menu-item {
    justify-content: center;
  }

  .system-content {
    padding: 12px;
  }
}

@media (max-width: 640px) {
  .system-layout {
    display: block;
  }

  .system-sidebar {
    position: sticky;
    top: 0;
    z-index: 30;
    width: 100%;
    height: auto;
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 8px;
    overflow-x: auto;
    border-right: 0;
    border-bottom: 1px solid var(--border-color);
  }

  .system-menu-item {
    flex: 0 0 42px;
    width: 42px;
    margin: 0;
    padding: 10px;
  }

  .system-main {
    width: 100%;
  }

  .system-topbar {
    height: 52px;
    padding: 10px 12px;
  }

  .system-content {
    padding: 10px;
  }

  .system-card {
    padding: 12px;
    border-radius: 10px;
  }

  .toolbar {
    padding: 12px;
    align-items: stretch;
  }

  .toolbar-label {
    flex: 0 0 100%;
    margin-bottom: -5px;
  }

  .toolbar-input,
  .toolbar .el-date-editor.toolbar-input {
    flex: 1 0 100%;
    width: 100%;
    min-width: 0;
    max-width: 100%;
  }

  .toolbar-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
  }

  .toolbar-actions .el-button {
    width: 100%;
  }

  .system-pagination {
    justify-content: center;
  }

  .system-pagination .el-pagination__jump {
    display: none;
  }

  .el-dialog {
    max-width: 520px;
    margin-left: auto;
    margin-right: auto;
  }
}
</style>
