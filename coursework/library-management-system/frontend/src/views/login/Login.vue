<template>
  <div class="login-wrap">
    <div class="login-side">
      <div class="brand">
        <div class="brand-badge">LIB</div>
        <div>
          <p class="brand-title">图书管理系统</p>
          <p class="brand-sub">读者与管理员统一入口，借阅、归还、库存与权限一体化管理。</p>
        </div>
      </div>
      <ul class="feature-list">
        <li>借阅操作原子化，库存不会出现负数</li>
        <li>借还记录与罚款自动计算</li>
        <li>支持用户、图书、分类、书架一体化后台管理</li>
      </ul>
      <div class="visit-card">让每一本好书，遇见它的读者。</div>
    </div>
    <div class="login-panel">
      <section v-if="failure" class="login-failure" role="alert" aria-live="polite">
        <div class="failure-code">{{ failure.code }}</div>
        <h1 class="login-title">{{ failure.title }}</h1>
        <p>{{ failure.description }}</p>
        <div class="login-actions">
          <el-button class="login-action" type="primary" :loading="loading" @click="login">重新尝试</el-button>
          <el-button class="login-action" :disabled="loading" @click="failure = null">返回登录</el-button>
        </div>
      </section>
      <template v-else>
      <h1 class="login-title">欢迎回来</h1>
      <p class="login-tip">请先登录后继续使用系统</p>
      <p v-if="loginMessage" class="login-message" role="alert">{{ loginMessage }}</p>
      <el-form class="login-form" @submit.native.prevent="login" @keydown.enter.native.prevent="login">
        <el-form-item label="账号" label-width="44px">
          <el-input v-model="act" clearable prefix-icon="el-icon-user" placeholder="请输入账号"></el-input>
        </el-form-item>
        <el-form-item label="密码" label-width="44px">
          <el-input v-model="pwd" type="password" show-password prefix-icon="el-icon-lock" placeholder="请输入密码"></el-input>
        </el-form-item>
        <div class="login-actions">
          <el-button type="primary" class="btn-primary login-action" :loading="loading" @click="login">立即登录</el-button>
          <el-button class="btn-ghost login-action" :disabled="loading" @click="$router.push('/register')">前往注册</el-button>
        </div>
      </el-form>
      </template>
    </div>
  </div>
</template>

<script>
import request from "@/utils/request.js";
import { setToken } from "@/utils/storage.js";
const ADMIN_ROLES = [0, 1];
export default {
    name: "Login",
    data() {
        return {
            act: '', pwd: '',
            loading: false,
            failure: null, loginMessage: '',
        }
    },
    methods: {
        describeFailure(error) {
            const status = Number(error.response && error.response.status);
            const copy = {
                403: ['登录请求被拒绝', '当前账号或登录入口不允许访问。请返回检查账号，或联系管理员。'],
                404: ['找不到登录服务', '登录接口不存在或地址已变更。请联系管理员检查服务地址。'],
                429: ['登录请求过于频繁', '请稍等片刻再尝试，避免连续提交。'],
                500: ['登录服务出现故障', '服务暂时无法完成登录，请稍后重试。'],
                502: ['登录服务暂不可达', '服务连接暂时异常，请稍后重试。'],
                503: ['登录服务暂不可用', '服务可能正在维护，请稍后重试。'],
                504: ['登录服务响应超时', '服务没有及时响应，请稍后重试。'],
            };
            if (copy[status]) return { code: String(status), title: copy[status][0], description: copy[status][1] };
            if (status) return { code: String(status), title: '暂时无法登录', description: '登录请求没有完成，请返回登录或稍后重试。' };
            if (error.code === 'INVALID_RESPONSE') return { code: '响应异常', title: '登录响应不完整', description: '服务没有返回有效的登录信息。请重试，或联系管理员检查服务。' };
            if (['ECONNABORTED', 'ETIMEDOUT'].includes(error.code)) return { code: '连接超时', title: '登录服务响应超时', description: '请检查网络连接，稍后重试。' };
            return { code: '连接失败', title: '暂时连接不上登录服务', description: '请检查网络连接；本地运行时请确认后端已启动。' };
        },
        async login() {
            if (this.loading) return;
            if (!this.act.trim() || !this.pwd) {
                this.$message.error('账号或密码不能为空');
                return;
            }
            this.loading = true;
            this.loginMessage = '';
            try {
                const { data } = await request.post('user/login', { userAccount: this.act.trim(), userPwd: this.pwd });
                if (!data || typeof data !== 'object' || typeof data.code !== 'number') {
                    throw Object.assign(new Error('Invalid login response'), { code: 'INVALID_RESPONSE' });
                }
                if (data.code !== 200) {
                    if ([403, 404, 429].includes(data.code) || data.code >= 500) {
                        this.failure = this.describeFailure({ response: { status: data.code } });
                    } else {
                        this.failure = null;
                        this.loginMessage = data.msg || '账号或密码不正确，请检查后重试。';
                    }
                    return;
                }
                if (!data.data || !data.data.token || ![0, 1, 2].includes(data.data.role)) {
                    throw Object.assign(new Error('Incomplete session'), { code: 'INVALID_RESPONSE' });
                }
                this.failure = null;
                setToken(data.data.token);
                this.$message.success('登录成功！');
                if (ADMIN_ROLES.includes(data.data.role)) { this.$router.push('/admin'); }
                else { this.$router.push('/user'); }
            } catch (e) {
                if (e.response && [400, 401, 422].includes(e.response.status)) {
                    this.failure = null;
                    this.loginMessage = e.response.status === 401 ? '账号或密码不正确，请检查后重试。' : '登录信息未通过检查，请返回核对账号和密码。';
                } else this.failure = this.describeFailure(e);
            } finally { this.loading = false; }
        },
    }
};
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  width: min(1040px, calc(100% - 32px));
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(360px, 1fr);
  align-content: center;
  align-items: stretch;
  gap: 16px;
  padding: clamp(20px, 4vh, 44px) 0;
}

.login-side,
.login-panel {
  border-radius: 20px;
  background: #fff;
  border: 1px solid #e5eaf2;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}

.login-side {
  padding: 36px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-badge {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(140deg, #3f8cff, #7c8fff);
  color: #fff;
  font-weight: 700;
  letter-spacing: 1px;
  display: grid;
  place-items: center;
}

.brand-title {
  margin: 0;
  font-size: 26px;
  line-height: 1.2;
  font-weight: 600;
  color: #1f2937;
}

.brand-sub {
  margin: 6px 0 0;
  color: #5f6a78;
  font-size: 13px;
}

.feature-list {
  margin: 32px 0 18px;
  padding-left: 16px;
  color: #334155;
  line-height: 1.85;
}

.visit-card {
  align-self: flex-start;
  margin-top: auto;
  padding: 12px 14px;
  border-radius: 8px;
  background: #f4f7ff;
  border: 1px solid #dce5ff;
  color: #3656b5;
  font-weight: 600;
}

.login-panel {
  padding: clamp(28px, 4vw, 48px);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-title {
  margin: 0 0 8px;
  font-size: 28px;
  line-height: 1.2;
}

.login-tip {
  margin: 0 0 22px;
  color: #607086;
}

.login-failure { padding: 12px 0; }
.failure-code { color: #3656b5; font-size: 42px; font-weight: 700; margin-bottom: 18px; }
.login-failure p { color: #607086; line-height: 1.8; margin-bottom: 24px; }
.login-message { padding: 12px; border-radius: 10px; background: #fff4ef; color: #a34d2b; line-height: 1.6; }

.login-actions {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.login-action {
  width: 100%;
  height: 44px;
  border-radius: 10px;
}

.login-actions .login-action + .login-action {
  margin-left: 0;
}

@media (max-width: 1000px) {
  .login-wrap {
    grid-template-columns: 1fr;
    max-width: 680px;
  }

  .login-side {
    padding: 26px;
  }

  .feature-list {
    margin: 20px 0 16px;
  }
}

@media (max-width: 560px) {
  .login-wrap {
    width: min(100% - 20px, 480px);
    gap: 10px;
    padding: 10px 0;
  }

  .login-side,
  .login-panel {
    padding: 22px;
    border-radius: 14px;
  }

  .brand-title {
    font-size: 22px;
  }

  .feature-list,
  .visit-card {
    display: none;
  }

  .login-actions {
    grid-template-columns: 1fr;
  }
}
</style>
