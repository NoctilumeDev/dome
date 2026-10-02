<template>
  <div class="register-wrap">
    <div class="register-card">
      <h2 class="register-title">读者注册</h2>
      <el-form label-width="80px" @submit.native.prevent="registerFunc" @keydown.enter.native.prevent="registerFunc">
        <el-form-item label="账号">
          <el-input v-model="act" clearable placeholder="4-16位字符"></el-input>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="name" clearable placeholder="昵称"></el-input>
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="pwd" type="password" show-password placeholder="不少于6位"></el-input>
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="pwdConfirm" type="password" show-password placeholder="请再次输入密码"></el-input>
        </el-form-item>
        <el-button type="primary" class="btn-primary" style="width:100%;" :loading="loading" @click="registerFunc">立即注册</el-button>
        <div class="register-footer">
          <el-button type="text" :disabled="loading" @click="$router.push('/login')">返回登录</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
import request from "@/utils/request.js";
export default {
    name: "Register",
    data() { return { act: '', pwd: '', pwdConfirm: '', name: '', loading: false } },
    methods: {
        async registerFunc() {
            if (this.loading) return;
            if (!this.act.trim() || !this.pwd || !this.pwdConfirm || !this.name.trim()) { this.$message.error('请填写完整信息'); return; }
            if (this.pwd !== this.pwdConfirm) { this.$message.error('前后密码不一致'); return; }
            if (this.pwd.length < 6) { this.$message.error('密码至少6位'); return; }
            const paramDTO = { userAccount: this.act.trim(), userPwd: this.pwd, userName: this.name.trim() };
            this.loading = true;
            try {
                const { data } = await request.post(`user/register`, paramDTO);
                if (data.code !== 200) { this.$message.error(data.msg); return; }
                this.$message.success('注册成功');
                this.$router.push('/login');
            } catch (error) { this.$message.error('注册请求出错'); }
            finally { this.loading = false; }
        }
    }
};
</script>

<style scoped lang="scss">
.register-wrap {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.register-card {
  width: min(460px, 100%);
  max-width: 100%;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e5eaf2;
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
  padding: 28px;
}

.register-title {
  margin: 0 0 18px;
}

.register-footer {
  margin-top: 12px;
  text-align: center;
  color: #607086;
}

.link-action {
  cursor: pointer;
  color: #3f8cff;
}

.link-action:hover {
  color: #296bcd;
}

@media (max-width: 520px) {
  .register-wrap {
    padding: 10px;
  }

  .register-card {
    padding: 22px 16px;
    border-radius: 14px;
  }
}
</style>
