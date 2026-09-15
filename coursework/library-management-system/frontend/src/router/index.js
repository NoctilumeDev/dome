import Vue from "vue";
import VueRouter from "vue-router";
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
import { getToken, clearToken } from "@/utils/storage.js";
import jwtDecode from 'jwt-decode';
Vue.use(ElementUI);
Vue.use(VueRouter);

const routes = [
  { path: "/", component: () => import(`@/views/login/Login.vue`) },
  { path: "/login", component: () => import(`@/views/login/Login.vue`) },
  { path: "/register", component: () => import(`@/views/register/Register.vue`) },
  {
    path: "/admin",
    component: () => import(`@/views/admin/Home.vue`),
    meta: { requireAuth: true },
    children: [
      { path: "/adminLayout", name: '数据总览', icon: 'el-icon-data-analysis', component: () => import(`@/views/admin/Main.vue`), meta: { requireAuth: true } },
      { path: "/userManage", name: '用户管理', icon: 'el-icon-user-solid', component: () => import(`@/views/admin/UserManage.vue`), meta: { requireAuth: true } },
      { path: "/categoryManage", name: '分类管理', icon: 'el-icon-menu', component: () => import(`@/views/admin/CategoryManage.vue`), meta: { requireAuth: true } },
      { path: "/bookshelfManage", name: '书架管理', icon: 'el-icon-s-grid', component: () => import(`@/views/admin/BookshelfManage.vue`), meta: { requireAuth: true } },
      { path: "/bookManage", name: '图书管理', icon: 'el-icon-notebook-2', component: () => import(`@/views/admin/BookManage.vue`), meta: { requireAuth: true } },
      { path: "/borrowManage", name: '借阅管理', icon: 'el-icon-document-copy', component: () => import(`@/views/admin/BorrowManage.vue`), meta: { requireAuth: true } },
      { path: "/feedbackManage", name: '反馈管理', icon: 'el-icon-message', component: () => import(`@/views/admin/FeedbackManage.vue`), meta: { requireAuth: true } },
      { path: "/reviewManage", name: '书评管理', icon: 'el-icon-star-off', component: () => import(`@/views/admin/ReviewManage.vue`), meta: { requireAuth: true } },
      { path: "/bookAssistant", name: '图书问答', icon: 'el-icon-chat-dot-round', component: () => import(`@/views/assistant/BookAssistant.vue`), meta: { requireAuth: true } }
    ]
  },
  {
    path: "/user",
    component: () => import(`@/views/user/Home.vue`),
    meta: { requireAuth: true },
    children: [
      { name: '图书借阅', path: "/bookBorrow", icon: 'el-icon-reading', component: () => import(`@/views/user/BookBorrow.vue`), meta: { requireAuth: true } },
      { name: '我的借阅', path: "/myBorrows", icon: 'el-icon-collection', component: () => import(`@/views/user/MyBorrows.vue`), meta: { requireAuth: true } },
      { name: '读者反馈', path: "/user/feedback", icon: 'el-icon-chat-line-square', component: () => import(`@/views/user/Feedback.vue`), meta: { requireAuth: true } },
      { name: '我的书评', path: "/user/reviews", icon: 'el-icon-star-off', component: () => import(`@/views/user/Review.vue`), meta: { requireAuth: true } },
      { name: '读者图书问答', path: "/user/bookAssistant", icon: 'el-icon-chat-dot-round', component: () => import(`@/views/assistant/BookAssistant.vue`), meta: { requireAuth: true } }
    ]
  }
];

const router = new VueRouter({
  routes
});
router.beforeEach((to, from, next) => {
  if (to.meta.requireAuth) {
    const token = getToken();
    if (!token) {
      next("/login");
      return;
    }
    // 解析 JWT 检查是否过期
    try {
      const decoded = jwtDecode(token);
      const now = Math.floor(Date.now() / 1000);
      if (decoded.exp && decoded.exp < now) {
        clearToken();
        next("/login");
        return;
      }
    } catch (e) {
      // token 格式异常，清除并跳转登录
      clearToken();
      next("/login");
      return;
    }
    next();
  }
  else {
    next();
  }
});
export default router;
