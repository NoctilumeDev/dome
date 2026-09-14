import axios from "axios"
import { getToken, clearToken } from "@/utils/storage.js";
import router from "@/router";

const URL_API = process.env.VUE_APP_API_BASE_URL || 'http://localhost:22090/api/book-manage-sys-api/v1.0'

const request = axios.create({
  baseURL: URL_API,
  timeout: 8000
});

// 请求拦截器：自动附加 token
request.interceptors.request.use(config => {
  const token = getToken();
  if (token !== null) {
    config.headers["token"] = token;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// 响应拦截器：统一错误处理 + token 过期跳转
request.interceptors.response.use(response => {
  return response;
}, error => {
  if (error.response) {
    const { status, data } = error.response;
    if (status === 401 || (data && (data.code === 401 || data.msg === '身份认证异常，请先登录'))) {
      clearToken();
      router.push('/login');
    }
  }
  return Promise.reject(error);
});

export default request;
