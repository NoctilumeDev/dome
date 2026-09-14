<template>
  <div class="system-layout">
    <aside class="system-sidebar">
      <h3 class="system-sidebar-title">图书管理</h3>
      <button
        v-for="(item, idx) in adminRoutes"
        :key="idx"
        class="system-menu-item"
        :class="{ 'is-active': currentPath === item.path }"
        @click="handleRouteSelect(item.path)"
      >
        <i v-if="item.icon" :class="item.icon"></i>
        <span>{{ item.name }}</span>
      </button>
    </aside>

    <div class="system-main">
      <header class="system-topbar">
        <span class="page-title">{{ tag }}</span>
        <div>
          <span v-if="userInfo.name" class="user-name">您好，{{ userInfo.name }}</span>
          <el-button class="btn-ghost" size="small" @click="loginOut">退出</el-button>
        </div>
      </header>
      <section class="system-content">
        <section v-if="isLandingPage" class="home-panel">
          <header class="panel-title-wrap">
            <h2 class="panel-title">账号概览</h2>
            <span class="panel-subtitle">主页核心指标与账号信息</span>
          </header>
          <section class="module-grid module-grid-summary">
            <article class="module-card system-card module-card-mini">
              <p class="module-label">当前角色</p>
              <p class="module-value">管理员</p>
              <p class="module-desc">账号：{{ userInfo.id || '--' }}</p>
            </article>
            <article class="module-card system-card module-card-mini">
              <p class="module-label">姓名</p>
              <p class="module-value">{{ userInfo.name || '--' }}</p>
              <p class="module-desc">可直接切换到常用模块入口</p>
            </article>
            <article class="module-card system-card module-card-mini">
              <p class="module-label">系统状态</p>
              <p class="module-value">运行中</p>
              <p class="module-desc">前后端联调正常</p>
            </article>
          </section>
        </section>

        <section v-if="isLandingPage" class="home-panel">
          <header class="panel-title-wrap">
            <h2 class="panel-title">管理模块</h2>
            <span class="panel-subtitle">按模块快速进入对应工作台</span>
          </header>
          <section class="module-grid module-grid-modules">
            <article
              class="module-card module-card-action system-card"
              v-for="(item, idx) in homeModules"
              :key="item.path"
              :class="{ 'module-card-active': currentPath === item.path }"
              @click="handleRouteSelect(item.path)"
            >
              <div class="module-card-header">
                <span class="module-index">{{ idx + 1 }}</span>
                <i :class="item.icon" class="module-icon"></i>
                <span>{{ item.name }}</span>
              </div>
              <p class="module-title">{{ item.title }}</p>
              <p class="module-desc">{{ item.desc }}</p>
              <span class="module-enter">进入模块 <i class="el-icon-arrow-right"></i></span>
            </article>
          </section>
        </section>

        <section v-else class="home-panel module-workspace">
          <header class="panel-title-wrap">
            <h2 class="panel-title">功能入口</h2>
            <span class="panel-subtitle">当前页面内容</span>
          </header>
          <div class="system-card module-view-card">
          <router-view></router-view>
          </div>
        </section>
      </section>
    </div>
  </div>
</template>

<script>
import request from "@/utils/request.js";
import router from "@/router/index";
import { clearToken } from "@/utils/storage"
export default {
    name: "AdminHome",
    data() {
        return {
            adminRoutes: [],
            currentPath: '',
            userInfo: { id: null, url: '', name: '', role: null },
            tag: '首页',
            homeModules: [
                { name: '数据总览', icon: 'el-icon-data-analysis', title: '数据总览', desc: '查看图书、用户、借阅与书架核心指标。', path: '/adminLayout' },
                { name: '借阅管理', icon: 'el-icon-document-copy', title: '借阅管理', desc: '处理借还与逾期监控，维护借阅记录。', path: '/borrowManage' },
                { name: '图书管理', icon: 'el-icon-notebook-2', title: '图书管理', desc: '新增、编辑图书，控制库存与可借数量。', path: '/bookManage' },
                { name: '用户管理', icon: 'el-icon-user-solid', title: '用户管理', desc: '管理系统用户、冻结状态与消息推送。', path: '/userManage' },
                { name: '分类管理', icon: 'el-icon-menu', title: '分类管理', desc: '维护图书分类结构与展示层级。', path: '/categoryManage' },
                { name: '书架管理', icon: 'el-icon-s-grid', title: '书架管理', desc: '管理实体书架信息、位置与容量。', path: '/bookshelfManage' },
                { name: '图书问答', icon: 'el-icon-chat-dot-round', title: '图书问答', desc: '用自然语言查询数据库里的图书信息。', path: '/bookAssistant' },
            ],
        };
    },
    created() {
        this.adminRoutes = router.options.routes.filter(r => r.path == '/admin')[0].children;
        this.currentPath = this.$route.path;
        this.updateTagByPath();
        this.tokenCheckLoad();
    },
    watch: {
        $route() {
            this.currentPath = this.$route.path;
            this.updateTagByPath();
        },
    },
    computed: {
        isLandingPage() {
            return this.$route.path === '/admin';
        },
    },
    methods: {
    async tokenCheckLoad() {
            try {
                const res = await request.get('user/auth');
                if (res.data.code !== 200) { this.$router.push('/login'); return; }
                const { id, userAvatar: url, userName: name, userRole: role } = res.data.data;
                this.userInfo = { id, url, name, role };
            } catch (e) { this.$router.push('/login'); }
        },
        handleRouteSelect(path) {
            const item = this.adminRoutes.find(r => r.path === path) || this.homeModules.find(r => r.path === path);
            if (item) this.tag = item.name;
            this.currentPath = path;
            this.$router.push(path);
        },
        updateTagByPath() {
            const item = this.adminRoutes.find(r => r.path === this.$route.path);
            this.tag = item ? item.name : '首页';
        },
        async loginOut() {
            if (confirm('确认退出？')) {
                clearToken();
                this.$router.push("/login");
            }
        },
    }
};
</script>

<style scoped lang="scss">
.user-name {
  margin-right: 12px;
  color: #334155;
}

.system-content {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.home-panel {
  min-width: 0;
  border: 1px solid #dbe7ff;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  padding: 14px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
}

.panel-title-wrap {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.panel-title {
  margin: 0;
  font-size: 16px;
  color: #0f172a;
  font-weight: 700;
}

.panel-subtitle {
  font-size: 12px;
  color: #64748b;
}

.module-grid {
  min-width: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 12px;
}

.module-grid-summary {
  grid-template-columns: repeat(3, minmax(190px, 1fr));
}

.module-grid-modules {
  grid-template-columns: repeat(3, minmax(220px, 1fr));
}

.module-view-card {
  padding: 14px;
  min-width: 0;
  overflow: hidden;
}

.module-workspace {
  width: 100%;
}

.module-card {
  cursor: default;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.module-card-action {
  cursor: pointer;
}

.module-card-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.1);
  border-color: #d7e4ff;
}

.module-card-active {
  border-color: #93c5fd;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.18);
}

.module-card-mini {
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.module-card-header {
  display: grid;
  grid-template-columns: 24px 20px auto;
  align-items: center;
  gap: 6px 10px;
  color: #1f2937;
  margin-bottom: 8px;
}

.module-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #eef2ff;
  color: #4338ca;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.module-label {
  color: var(--text-sub);
  font-size: 12px;
  margin-bottom: 10px;
}

.module-value {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.module-title {
  margin: 0 0 4px;
  color: #111827;
  font-size: 16px;
}

.module-desc {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.module-enter {
  margin-top: 10px;
  color: var(--primary-color);
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.module-icon {
  font-size: 20px;
}

@media (max-width: 1100px) {
  .module-grid {
    grid-template-columns: repeat(2, minmax(160px, 1fr));
  }
  .module-grid-modules {
    grid-template-columns: repeat(2, minmax(200px, 1fr));
  }
}

@media (max-width: 720px) {
  .module-grid {
    grid-template-columns: 1fr;
  }
  .home-panel {
    padding: 12px;
  }
  .panel-title-wrap {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
