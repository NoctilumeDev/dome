<template>
  <div class="feature-shell">
    <p class="system-section-title">我的借阅记录</p>
    <section class="toolbar">
      <span class="toolbar-label">状态</span>
      <el-select v-model="statusFilter" size="small" class="toolbar-input" placeholder="全部" clearable @change="handleFilter">
        <el-option label="全部" :value="null"></el-option>
        <el-option label="借阅中" :value="false"></el-option>
        <el-option label="已归还" :value="true"></el-option>
      </el-select>
      <span class="toolbar-label">逾期</span>
      <el-select v-model="overdueFilter" size="small" class="toolbar-input" placeholder="全部" clearable @change="handleFilter">
        <el-option label="全部" :value="null"></el-option>
        <el-option label="逾期" :value="true"></el-option>
        <el-option label="未逾期" :value="false"></el-option>
      </el-select>
      <div class="toolbar-actions">
        <el-button class="btn-ghost" size="small" @click="resetCondition">条件重置</el-button>
      </div>
    </section>

    <el-table row-key="id" :data="tableData" class="system-table" stripe border v-loading="loading">
      <el-table-column prop="bookName" label="书名" width="200"></el-table-column>
      <el-table-column prop="borrowTime" label="借阅时间" width="168"></el-table-column>
      <el-table-column prop="dueDate" label="应还日期" width="168">
        <template slot-scope="scope">
          <span :style="{ color: isOverdue(scope.row) ? '#f56c6c' : '#303133' }">
            {{ scope.row.dueDate || '--' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="returnTime" label="归还时间" width="168">
        <template slot-scope="scope">
          <span>{{ scope.row.returnTime || '--' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="108">
        <template slot-scope="scope">
          <el-tag v-if="scope.row.status" type="success" size="small">已归还</el-tag>
          <el-tag v-else-if="isOverdue(scope.row)" type="danger" size="small">已逾期</el-tag>
          <el-tag v-else type="warning" size="small">借阅中</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template slot-scope="scope">
          <span v-if="!scope.row.status" class="text-button" @click="handleReturn(scope.row)">还书</span>
          <span v-else style="color: #909399;">已归还</span>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin: 20px 0;float: right;"
      :current-page="currentPage"
      :page-sizes="[5, 10]"
      :page-size="pageSize"
      :total="totalItems"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script>
export default {
    data() {
        return {
            tableData: [],
            loading: false,
            currentPage: 1,
            pageSize: 10,
            totalItems: 0,
            statusFilter: null,
            overdueFilter: null,
            userId: null,
        };
    },
    created() {
        this.initUserId();
    },
    methods: {
        initUserId() {
            this.$axios.get('user/auth').then(res => {
                if (res.data.code === 200) {
                    this.userId = res.data.data.id;
                    this.fetchData();
                }
            });
        },
        isOverdue(row) {
            if (row.status) return false;
            if (!row.dueDate) return false;
            return new Date(row.dueDate) < new Date();
        },
        async fetchData() {
            if (!this.userId) return;
            this.loading = true;
            try {
                const params = {
                    current: this.currentPage,
                    size: this.pageSize,
                    userId: this.userId,
                    status: this.statusFilter,
                    overdue: this.overdueFilter,
                };
                const response = await this.$axios.post('/borrowRecord/query', params);
                const { data } = response;
                if (data.code === 200) {
                    this.tableData = data.data || [];
                    this.totalItems = data.total || 0;
                }
            } catch (error) {
                console.error('查询借阅记录异常:', error);
            } finally {
                this.loading = false;
            }
        },
        async handleReturn(row) {
            const confirmed = await this.$swalConfirm({
                title: '归还图书',
                text: '确认归还《' + row.bookName + '》？',
                icon: 'warning',
            });
            if (confirmed) {
                try {
                    const response = await this.$axios.post('/borrowRecord/return/' + row.id);
                    if (response.data.code === 200) {
                        this.$swal.fire({
                            title: '归还成功',
                            text: response.data.msg,
                            icon: 'success',
                            showConfirmButton: false,
                            timer: 1500,
                        });
                        this.fetchData();
                    } else {
                        this.$message.error(response.data.msg);
                    }
                } catch (e) {
                    this.$message.error('归还操作失败');
                }
            }
        },
        handleFilter() {
            this.currentPage = 1;
            this.fetchData();
        },
        resetCondition() {
            this.statusFilter = null;
            this.overdueFilter = null;
            this.fetchData();
        },
        handleSizeChange(val) {
            this.pageSize = val;
            this.currentPage = 1;
            this.fetchData();
        },
        handleCurrentChange(val) {
            this.currentPage = val;
            this.fetchData();
        },
    },
};
</script>
