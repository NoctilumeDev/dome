<template>
  <div class="feature-shell">
    <section class="toolbar" @keydown.enter.prevent="handleFilter">
      <div class="toolbar-field">
        <span class="toolbar-label">图书名称</span>
        <el-input v-model="queryDto.name" class="toolbar-input" size="small" placeholder="书名" clearable @clear="handleFilter" />
      </div>
      <div class="toolbar-field">
        <span class="toolbar-label">作者</span>
        <el-input v-model="queryDto.author" class="toolbar-input" size="small" placeholder="作者" clearable @clear="handleFilter" />
      </div>
      <div class="toolbar-field">
        <span class="toolbar-label">分类</span>
        <el-input v-model="queryDto.category" class="toolbar-input" size="small" placeholder="分类" clearable @clear="handleFilter" />
      </div>
      <div class="toolbar-actions">
        <el-button class="btn-ghost" size="small" @click="handleFilter">搜索</el-button>
        <el-button class="btn-ghost" size="small" @click="resetCondition">重置</el-button>
      </div>
    </section>

    <p class="system-section-title">馆藏图书</p>
    <p v-if="bookError" class="list-error" role="alert">{{ bookError }} <el-button type="text" @click="fetchBooks">重试</el-button></p>
    <el-table row-key="id" :data="bookTableData" class="system-table" stripe border style="margin-top: 10px;" v-loading="bookLoading" :empty-text="bookError ? '图书尚未加载' : '没有符合条件的图书，试试重置条件'">
      <el-table-column label="封面" width="100">
        <template slot-scope="scope">
          <el-image v-if="scope.row.cover" :src="getImageUrl(scope.row.cover)" style="width: 60px;height: 80px;" fit="cover"></el-image>
          <span v-else style="color: #909399;">无封面</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="书名" width="150"></el-table-column>
      <el-table-column prop="author" label="作者" width="120"></el-table-column>
      <el-table-column prop="publisher" label="出版社" width="150"></el-table-column>
      <el-table-column prop="category" label="分类" width="100"></el-table-column>
      <el-table-column prop="availableCount" label="可借数" width="80">
        <template slot-scope="scope">
          <span :style="{ color: scope.row.availableCount > 0 ? '#13ce66' : '#e6a23c' }">
            {{ scope.row.availableCount }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="简介" min-width="200" show-overflow-tooltip></el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template slot-scope="scope">
          <el-button type="primary" size="mini" @click="handleBorrow(scope.row)" :disabled="scope.row.availableCount <= 0 || isPending('borrow', scope.row.id)" :loading="isPending('borrow', scope.row.id)">{{ scope.row.availableCount > 0 ? '借阅' : '暂不可借' }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      class="system-pagination"
      :current-page="currentPage"
      :page-sizes="[5, 10]"
      :page-size="pageSize"
      :total="totalItems"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <p class="system-section-title" style="margin-top: 30px;">我的借阅记录</p>
    <el-table row-key="id" :data="borrowTableData" class="system-table" stripe border v-loading="borrowLoading">
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
      <el-table-column label="操作" width="100" fixed="right">
        <template slot-scope="scope">
          <el-button v-if="!scope.row.status" type="text" :loading="isPending('return', scope.row.id)" @click="handleReturn(scope.row)">还书</el-button>
          <span v-else style="color: #909399;">已归还</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
export default {
    data() {
        return {
            userId: null,
            bookTableData: [],
            bookLoading: false,
            bookError: '',
            bookRequestId: 0,
            pendingOperations: [],
            borrowTableData: [],
            borrowLoading: false,
            queryDto: {},
            currentPage: 1,
            pageSize: 10,
            totalItems: 0,
        };
    },
    created() {
        this.initUserId();
        this.fetchBooks();
    },
    beforeDestroy() { this.bookRequestId += 1; },
    methods: {
        getImageUrl(url) {
            if (!url) return '';
            if (url.startsWith('http')) return url;
            return 'http://localhost:22090' + url;
        },
        isOverdue(row) {
            if (row.status) return false;
            if (!row.dueDate) return false;
            return new Date(row.dueDate) < new Date();
        },
        async initUserId() {
            try {
                const res = await this.$axios.get('user/auth');
                if (res.data.code === 200) {
                    this.userId = res.data.data.id;
                    this.fetchBorrowRecords();
                }
            } catch (e) { this.$message.error('读取登录信息失败，请重新登录'); }
        },
        async fetchBooks() {
            const requestId = ++this.bookRequestId;
            this.bookLoading = true;
            this.bookError = '';
            try {
                const params = { current: this.currentPage, size: this.pageSize, ...this.queryDto };
                const response = await this.$axios.post('/book/query', params);
                const { data } = response;
                if (requestId !== this.bookRequestId) return;
                if (data.code === 200) {
                    this.bookTableData = data.data || [];
                    this.totalItems = data.total || 0;
                } else { throw new Error(data.msg || '查询失败'); }
            } catch (error) {
                if (requestId !== this.bookRequestId) return;
                this.bookTableData = [];
                this.totalItems = 0;
                this.bookError = '图书加载失败，请重试';
            } finally {
                if (requestId === this.bookRequestId) this.bookLoading = false;
            }
        },
        async fetchBorrowRecords() {
            if (!this.userId) {
                return;
            }
            this.borrowLoading = true;
            try {
                const params = { current: 1, size: 100, userId: this.userId };
                const response = await this.$axios.post('/borrowRecord/query', params);
                const { data } = response;
                if (data.code === 200) {
                    this.borrowTableData = data.data || [];
                }
            } catch (error) {
                console.error('查询借阅记录异常:', error);
            } finally {
                this.borrowLoading = false;
            }
        },
        async handleBorrow(row) {
            if (row.availableCount <= 0 || this.isPending('borrow', row.id)) return;
            this.pendingOperations.push('borrow:' + row.id);
            try {
                const confirmed = await this.$swalConfirm({
                    title: '确认借阅',
                    text: '确认借阅《' + row.name + '》？',
                    icon: 'question',
                });
                if (!confirmed) return;
                const response = await this.$axios.post('/borrowRecord/borrow/' + row.id);
                if (response.data.code === 200) {
                    this.$swal.fire({ title: '借阅成功', text: response.data.msg, icon: 'success', showConfirmButton: false, timer: 1500 });
                    this.fetchBooks();
                    this.fetchBorrowRecords();
                } else {
                    this.$message.error(response.data.msg);
                }
            } catch (e) {
                this.$message.error('借阅请求异常');
            } finally { this.pendingOperations = this.pendingOperations.filter(key => key !== 'borrow:' + row.id); }
        },
        async handleReturn(row) {
            if (this.isPending('return', row.id)) return;
            this.pendingOperations.push('return:' + row.id);
            try {
                const confirmed = await this.$swalConfirm({
                    title: '归还图书',
                    text: '确认归还《' + row.bookName + '》？',
                    icon: 'warning',
                });
                if (!confirmed) return;
                const response = await this.$axios.post('/borrowRecord/return/' + row.id);
                if (response.data.code === 200) {
                    this.$swal.fire({ title: '归还成功', text: response.data.msg, icon: 'success', showConfirmButton: false, timer: 1500 });
                    this.fetchBooks();
                    this.fetchBorrowRecords();
                } else {
                    this.$message.error(response.data.msg);
                }
            } catch (e) {
                this.$message.error('归还请求异常');
            } finally { this.pendingOperations = this.pendingOperations.filter(key => key !== 'return:' + row.id); }
        },
        handleFilter() { this.currentPage = 1; this.fetchBooks(); },
        isPending(action, id) { return this.pendingOperations.includes(action + ':' + id); },
        resetCondition() { this.queryDto = {}; this.currentPage = 1; this.fetchBooks(); },
        handleSizeChange(val) { this.pageSize = val; this.currentPage = 1; this.fetchBooks(); },
        handleCurrentChange(val) { this.currentPage = val; this.fetchBooks(); },
    },
};
</script>
