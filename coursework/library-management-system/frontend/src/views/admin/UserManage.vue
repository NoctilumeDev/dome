<template>
  <div class="feature-shell">
    <section class="toolbar">
      <span class="toolbar-label">用户名</span>
      <el-input
        v-model="userQueryDto.userName"
        size="small"
        class="toolbar-input"
        placeholder="用户名"
        clearable
        @clear="handleFilterClear"
      />
      <span class="toolbar-label">注册时间</span>
      <el-date-picker
        v-model="searchTime"
        size="small"
        class="toolbar-input"
        type="daterange"
        range-separator="至"
        start-placeholder="起始时间"
        end-placeholder="结束时间"
      />
      <div class="toolbar-actions">
        <el-button class="btn-ghost" size="small" @click="handleFilter">立即查询</el-button>
        <el-button class="btn-ghost" size="small" @click="add">新增用户</el-button>
        <el-button
          size="small"
          :disabled="!selectedRows.length"
          type="danger"
          class="btn-danger-soft"
          @click="batchDelete"
        >批量删除</el-button>
        <el-button class="btn-ghost" size="small" @click="resetQueryCondition">条件重置</el-button>
      </div>
    </section>

    <el-table :data="tableData" row-key="id" class="system-table" border stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55"></el-table-column>
      <el-table-column prop="userAvatar" width="68" label="头像">
        <template slot-scope="scope">
          <el-avatar :size="30" :src="scope.row.userAvatar" style="margin-top: 10px;"></el-avatar>
        </template>
      </el-table-column>
      <el-table-column prop="userName" width="148" label="名称"></el-table-column>
      <el-table-column prop="userAccount" width="128" label="账号"></el-table-column>
      <el-table-column prop="userRole" width="88" label="角色">
        <template slot-scope="scope">
          <span>{{ getRoleName(scope.row.userRole) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="isLogin" width="108" label="冻结">
        <template slot-scope="scope">
          <el-switch @change="handleSwitchChange(scope.row.id, scope.row.isLogin, true)"
            style="user-select: none;" v-model="scope.row.isLogin" active-color="#f56c6c"
            inactive-color="rgb(226, 226, 226)"
          />
        </template>
      </el-table-column>
      <el-table-column :sortable="true" prop="createTime" width="168" label="注册于"></el-table-column>
      <el-table-column label="操作">
        <template slot-scope="scope">
          <span class="text-button" @click="handleEdit(scope.row)">编辑</span>
          <span class="text-button" style="margin-left: 10px;" @click="handleDelete(scope.row)">删除</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      style="margin: 20px 0;float: right;"
      :current-page="currentPage"
      :page-sizes="[5, 7]"
      :page-size="pageSize"
      :total="totalItems"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <!-- 操作面板 -->
    <el-dialog :show-close="false" :visible.sync="dialogUserOperaion" width="28%" custom-class="system-dialog">
      <p slot="title" class="dialog-card-title">{{ !isOperation ? '新增新用户' : '编辑用户信息' }}</p>
      <div style="padding:0 20px;">
        <el-row class="dialog-form-item">
          <el-upload class="avatar-uploader" :action="uploadUrl" :headers="uploadHeaders" :show-file-list="false" :on-success="handleAvatarSuccess">
            <img v-if="data.userAvatar" :src="data.userAvatar" class="dialog-avatar">
            <i v-else class="el-icon-plus avatar-uploader-icon"></i>
          </el-upload>
        </el-row>
        <el-row class="dialog-form-item">
          <span class="dialog-hover">用户名</span>
          <input class="dialog-input" v-model="data.userName" placeholder="用户名" />
          <span class="dialog-hover">账号</span>
          <input class="dialog-input" v-model="data.userAccount" placeholder="账号" />
          <span class="dialog-hover">密码</span>
          <input class="dialog-input" v-model="userPwd" type="password" placeholder="密码" />
        </el-row>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button class="btn-primary" size="small" v-if="!isOperation" @click="addOperation">新增</el-button>
        <el-button class="btn-primary" size="small" v-else @click="updateOperation">修改</el-button>
        <el-button class="btn-ghost" size="small" @click="dialogUserOperaion = false">取消</el-button>
      </span>
    </el-dialog>

    <!-- 消息推送 -->
    <el-dialog :show-title="false" :show-close="false" :visible.sync="dialogMessageOperation" width="24%" custom-class="system-dialog">
      <p class="dialog-card-title" style="padding: 20px 0  0 20px;">消息推送</p>
      <div style="padding:0 20px;">
        <el-row class="dialog-form-item">
          <span class="dialog-hover">消息内容</span>
          <el-input type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="消息内容"
            v-model="data.content">
          </el-input>
        </el-row>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button class="btn-primary" size="small" @click="messagePushOperation">确定推送</el-button>
        <el-button class="btn-ghost" size="small" @click="dialogMessageOperation = false">取消</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
    data() {
        return {
            userPwd: '',
            data: { userAvatar: '' },
            filterText: '',
            currentPage: 1,
            pageSize: 7,
            totalItems: 0,
            dialogMessageOperation: false,
            dialogUserOperaion: false, // 开关
            isOperation: false, // 开关-标识新增或修改
            tableData: [],
            searchTime: [],
            selectedRows: [],
            userQueryDto: {}, // 搜索条件
        };
    },
    watch: {
        dialogUserOperaion(v1, v2) {
            if (!v1) {
                this.isOperation = !this.isOperation;
            }
            if (!v1 && v2) {
                this.data = {};
            }
        },
    },
    created() {
        this.fetchFreshData();
    },
    computed: {
        uploadUrl() {
            return (process.env.VUE_APP_API_BASE_URL || 'http://localhost:22090/api/book-manage-sys-api/v1.0') + '/file/upload';
        },
        uploadHeaders() {
            const token = sessionStorage.getItem('token');
            return token ? { token } : {};
        }
    },
    methods: {
        getRoleName(role) {
            const roleMap = { 1: '管理员', 2: '读者' };
            return roleMap[role] || '未知';
        },
        messagePushOperation() {
            const messages = []
            const message = {
                receiverId: this.data.id,
                content: this.data.content
            }
            messages.push(message);
            this.$axios.post('/message/systemInfoSave', messages).then(response => {
                const { data } = response;
                if (data.code === 200) {
                    this.$swal.fire({
                        title: '消息推送',
                        text: '推送成功',
                        icon: 'success',
                        showConfirmButton: false,
                        timer: 1000,
                    });
                    this.dialogMessageOperation = false;
                    this.data = {};
                }
            })
        },
        handleAvatarSuccess(res, file) {
            if (res.code !== 200) {
                this.$message.error(`用户头像上传异常`);
                return;
            }
            this.$message.success(`用户头像上传成功`);
            this.data.userAvatar = res.data;
        },
        async handleSwitchChange(id, status, operation) {
            try {
                let param = { id: id }
                if (operation) {
                    param.isLogin = status;
                } else {
                    param.isWord = status;
                }
                const response = await this.$axios.put(`/user/backUpdate`, param);
                if (response.data.code === 200) {
                    this.$swal.fire({
                        title: operation ? '冻结状态' : '评论状态',
                        text: operation ? '冻结状态操作成功' : '评论状态操作成功',
                        icon: 'success',
                        showConfirmButton: false,
                        timer: 1000,
                    });
                }
            } catch (e) {
                console.error(`更新用户状态异常：${e}`);
            }
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection;
        },
        async batchDelete() {
            if (!this.selectedRows.length) {
                this.$message(`未选中任何数据`);
                return;
            }
            const confirmed = await this.$swalConfirm({
                title: '删除用户数据',
                text: `删除后不可恢复，是否继续？`,
                icon: 'warning',
            });
            if (confirmed) {
                try {
                    let ids = this.selectedRows.map(entity => entity.id);
                    const response = await this.$axios.post(`/user/batchDelete`, ids);
                    if (response.data.code === 200) {
                        this.$swal.fire({
                            title: '删除提示',
                            text: response.data.msg,
                            icon: 'success',
                            showConfirmButton: false,
                            timer: 2000,
                        });
                        await this.fetchFreshData();
                        return;
                    }
                } catch (e) {
                    this.$swal.fire({
                        title: '错误提示',
                        text: e,
                        icon: 'error',
                        showConfirmButton: false,
                        timer: 2000,
                    });
                    console.error(`用户信息删除异常：`, e);
                }
            }
        },
        resetQueryCondition() {
            this.userQueryDto = {};
            this.searchTime = [];
            this.fetchFreshData();
        },
        async updateOperation() {
            if (this.userPwd !== '') {
                this.data.userPwd = this.userPwd;
            } else {
                this.data.userPwd = null;
            }
            try {
                const response = await this.$axios.put('/user/backUpdate', this.data);
                this.$swal.fire({
                    title: '用户信息修改',
                    text: response.data.msg,
                    icon: response.data.code === 200 ? 'success' : 'error',
                    showConfirmButton: false,
                    timer: 1000,
                });
                if (response.data.code === 200) {
                    this.closeDialog();
                    await this.fetchFreshData();
                    this.clearFormData();
                }
            } catch (error) {
                console.error('提交表单时出错:', error);
                this.$message.error('提交失败，请稍后再试！');
            }
        },
        async addOperation() {
            if (this.userPwd !== '') {
                this.data.userPwd = this.userPwd;
            } else {
                this.data.userPwd = null;
            }
            try {
                const response = await this.$axios.post('/user/insert', this.data);
                this.$message[response.data.code === 200 ? 'success' : 'error'](response.data.msg);
                if (response.data.code === 200) {
                    this.closeDialog();
                    await this.fetchFreshData();
                    this.clearFormData();
                }
            } catch (error) {
                console.error('提交表单时出错:', error);
                this.$message.error('提交失败，请稍后再试！');
            }
        },
        closeDialog() {
            this.dialogUserOperaion = false;
        },
        clearFormData() {
            this.data = {};
        },
        async fetchFreshData() {
            try {
                this.tableData = [];
                let startTime = null;
                let endTime = null;
                if (this.searchTime != null && this.searchTime.length === 2) {
                    const [startDate, endDate] = await Promise.all(this.searchTime.map(date => date.toISOString()));
                    startTime = `${startDate.split('T')[0]}T00:00:00`;
                    endTime = `${endDate.split('T')[0]}T23:59:59`;
                }
                const params = {
                    current: this.currentPage,
                    size: this.pageSize,
                    key: this.filterText,
                    startTime: startTime,
                    endTime: endTime,
                    ...this.userQueryDto
                };
                const response = await this.$axios.post('/user/query', params);
                const { data } = response;
                this.tableData = data.data;
                this.totalItems = data.total;
            } catch (error) {
                console.error('查询用户信息异常:', error);
            }
        },
        add() {
            this.dialogUserOperaion = true;
        },
        handleFilter() {
            this.currentPage = 1;
            this.fetchFreshData();
        },
        handleFilterClear() {
            this.filterText = '';
            this.handleFilter();
        },
        handleSizeChange(val) {
            this.pageSize = val;
            this.currentPage = 1;
            this.fetchFreshData();
        },
        handleCurrentChange(val) {
            this.currentPage = val;
            this.fetchFreshData();
        },
        messagePush(row) {
            this.dialogMessageOperation = true;
            this.data = { ...row };
        },
        handleEdit(row) {
            this.dialogUserOperaion = true;
            this.isOperation = true;
            row.userPwd = null;
            this.data = { ...row }
        },
        handleDelete(row) {
            this.selectedRows.push(row);
            this.batchDelete();
        }
    },
};
</script>

<style scoped lang="scss">
.dialog-avatar {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  object-fit: cover;
}
</style>

