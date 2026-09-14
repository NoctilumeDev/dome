import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import 'element-ui/lib/theme-chalk/index.css';
import request from '@/utils/request'

Vue.config.productionTip = false;
Vue.prototype.$axios = request;

// 替代 SweetAlert2：$message 通知 + 原生 confirm
const swalPlugin = {
  install(Vue) {
    Vue.prototype.$swal = {
      fire(options = {}) {
        const { title, text, icon } = options;
        const fullText = title ? title + (text ? '\n' + text : '') : text || '';
        if (icon === 'error') {
          alert('错误：' + fullText);
        } else {
          alert(fullText);
        }
      }
    };
    Vue.prototype.$swalConfirm = function(options = {}) {
      return Promise.resolve(confirm(options.title || '确认操作？'));
    };
  },
};
Vue.use(swalPlugin);

new Vue({
  router,
  render: h => h(App)
}).$mount("#app");
