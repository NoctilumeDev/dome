<template>
  <div class="system-layout">
    <aside class="system-sidebar">
      <h3 class="system-sidebar-title">读者中心</h3>
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
            <span class="panel-subtitle">阅读者常用信息一览</span>
          </header>
          <section class="module-grid module-grid-summary">
            <article class="module-card system-card module-card-mini">
              <p class="module-label">当前角色</p>
              <p class="module-value">读者</p>
              <p class="module-desc">账号：{{ userInfo.id || '--' }}</p>
            </article>
            <article class="module-card system-card module-card-mini">
              <p class="module-label">名称</p>
              <p class="module-value">{{ userInfo.name || '--' }}</p>
              <p class="module-desc">支持图书检索、借阅与收藏</p>
            </article>
            <article class="module-card system-card module-card-mini">
              <p class="module-label">服务状态</p>
              <p class="module-value">可用</p>
              <p class="module-desc">在线服务已连接到后端</p>
            </article>
          </section>
        </section>

        <section v-if="isLandingPage" class="home-panel">
          <header class="panel-title-wrap">
            <h2 class="panel-title">阅读模块</h2>
            <span class="panel-subtitle">按功能快速进入常用页面</span>
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
import { clearToken, getToken, isCurrentToken } from "@/utils/storage"
export default {
    name: "UserHome",
    data() {
        return {
            adminRoutes: [],
            currentPath: '',
            userInfo: { id: null, url: '', name: '', role: null },
            tag: '首页',
            homeModules: [
                { name: '图书借阅', icon: 'el-icon-reading', title: '图书借阅', desc: '查看可借图书并进行借阅或收藏。', path: '/bookBorrow' },
                { name: '我的借阅', icon: 'el-icon-collection', title: '我的借阅', desc: '管理我的借阅记录、还书与状态。', path: '/myBorrows' },
                { name: '读者反馈', icon: 'el-icon-chat-line-square', title: '读者反馈', desc: '提交使用建议并查看管理员回复。', path: '/user/feedback' },
                { name: '我的书评', icon: 'el-icon-star-off', title: '我的书评', desc: '记录阅读感受并管理自己的书评。', path: '/user/reviews' },
                { name: '读者图书问答', icon: 'el-icon-chat-line-round', title: '图书问答', desc: '用自然语言查询数据库里的图书信息。', path: '/user/bookAssistant' },
            ],
        };
    },
    created() {
        this.adminRoutes = router.options.routes.filter(r => r.path == '/user')[0].children;
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
            return this.$route.path === '/user';
        },
    },
    methods: {
        async tokenCheckLoad() {
            const observedToken = getToken();
            try {
                const res = await request.get('user/auth');
                if (!isCurrentToken(observedToken)) return;
                if (res.data.code !== 200) { this.$router.push('/login'); return; }
                const { id, userAvatar: url, userName: name, userRole: role } = res.data.data;
                this.userInfo = { id, url, name, role };
            } catch (e) {
                if (isCurrentToken(observedToken)) this.$router.push('/login');
            }
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
    grid-template-columns: repeat(2, 1fr);
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
