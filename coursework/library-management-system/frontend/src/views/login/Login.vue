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
      <div class="visit-card">在线访客序号：{{ visitorCount }}</div>
    </div>
    <div class="login-panel">
      <h1 class="login-title">欢迎回来</h1>
      <p class="login-tip">请先登录后继续使用系统</p>
      <el-form class="login-form" @submit.native.prevent="login">
        <el-form-item label="账号" label-width="44px">
          <el-input v-model="act" clearable prefix-icon="el-icon-user" placeholder="请输入账号"></el-input>
        </el-form-item>
        <el-form-item label="密码" label-width="44px">
          <el-input v-model="pwd" type="password" show-password prefix-icon="el-icon-lock" placeholder="请输入密码"></el-input>
        </el-form-item>
        <div class="login-actions">
          <el-button type="primary" class="btn-primary login-action" @click="login">立即登录</el-button>
          <el-button class="btn-ghost login-action" @click="$router.push('/register')">前往注册</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
import request from "@/utils/request.js";
import { setToken } from "@/utils/storage.js";
const ADMIN_ROLES = [0, 1, 3, 4];
export default {
    name: "Login",
    data() {
        return {
            act: '', pwd: '',
            visitorCount: Math.floor(Math.random() * 9000) + 1000,
        }
    },
    methods: {
        async login() {
            if (!this.act || !this.pwd) {
                this.$message.error('账号或密码不能为空');
                return;
            }
            try {
                const { data } = await request.post('user/login', { userAccount: this.act, userPwd: this.pwd });
                if (data.code !== 200) {
                    this.$message.error(data.msg);
                    return;
                }
                setToken(data.data.token);
                this.$message.success('登录成功！');
                if (ADMIN_ROLES.includes(data.data.role)) { this.$router.push('/admin'); }
                else { this.$router.push('/user'); }
            } catch (e) {
                this.$message.error('登录出错');
            }
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
