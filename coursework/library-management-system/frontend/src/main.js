import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import 'element-ui/lib/theme-chalk/index.css';
import request from '@/utils/request'

Vue.config.productionTip = false;
Vue.prototype.$axios = request;

// 保留已有调用方式，统一使用 Element UI 的提示与确认框。
const swalPlugin = {
  install(Vue) {
    Vue.prototype.$swal = {
      fire(options = {}) {
        const { title, text, icon } = options;
        const fullText = title ? title + (text ? '\n' + text : '') : text || '';
        Vue.prototype.$message({ message: fullText, type: ['error', 'success', 'warning', 'info'].includes(icon) ? icon : 'info' });
      }
    };
    Vue.prototype.$swalConfirm = function(options = {}) {
      return this.$confirm(options.text || '是否继续此操作？', options.title || '确认操作', {
        confirmButtonText: '确定', cancelButtonText: '取消',
        type: options.icon === 'warning' ? 'warning' : 'info',
        closeOnClickModal: false,
      }).then(() => true).catch(() => false);
    };
  },
};
Vue.use(swalPlugin);

new Vue({
  router,
  render: h => h(App)
}).$mount("#app");
