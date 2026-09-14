<template>
  <div class="feature-shell">
    <section class="toolbar">
      <span class="toolbar-label">图书名称</span>
      <el-input v-model="queryDto.name" class="toolbar-input" size="small" placeholder="书名" clearable @clear="handleFilter" />
      <span class="toolbar-label">作者</span>
      <el-input v-model="queryDto.author" class="toolbar-input" size="small" placeholder="作者" clearable @clear="handleFilter" />
      <span class="toolbar-label">分类</span>
      <el-input v-model="queryDto.category" class="toolbar-input" size="small" placeholder="分类" clearable @clear="handleFilter" />
      <div class="toolbar-actions">
        <el-button class="btn-ghost" size="small" @click="handleFilter">搜索</el-button>
        <el-button class="btn-ghost" size="small" @click="resetCondition">重置</el-button>
      </div>
    </section>

    <p class="system-section-title">可借图书</p>
    <el-table row-key="id" :data="bookTableData" class="system-table" stripe border style="margin-top: 10px;" v-loading="bookLoading">
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
      <el-table-column label="操作" width="180">
        <template slot-scope="scope">
          <el-button type="primary" size="mini" @click="handleBorrow(scope.row)" :disabled="scope.row.availableCount <= 0">借阅</el-button>
          <el-button v-if="scope.row.availableCount <= 0" type="warning" size="mini" @click="handleReserve(scope.row)">预约</el-button>
          <el-button size="mini" @click="handleFavorite(scope.row)" :type="scope.row._favorited ? 'info' : 'default'">
            {{ scope.row._favorited ? '已收藏' : '收藏' }}
          </el-button>
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
      <el-table-column label="操作" width="100">
        <template slot-scope="scope">
          <span v-if="!scope.row.status" class="text-button" @click="handleReturn(scope.row)">还书</span>
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
        initUserId() {
            const userInfoStr = sessionStorage.getItem('userInfo');
            if (userInfoStr) {
                try {
                    const userInfo = JSON.parse(userInfoStr);
                    this.userId = userInfo.id;
                } catch (e) { }
            }
            if (!this.userId) {
                this.$axios.get('user/auth').then(res => {
                    if (res.data.code === 200) {
                        this.userId = res.data.data.id;
                    }
                });
            }
        },
        async fetchBooks() {
            this.bookLoading = true;
            try {
                const params = { current: this.currentPage, size: this.pageSize, ...this.queryDto };
                const response = await this.$axios.post('/book/query', params);
                const { data } = response;
                if (data.code === 200) {
                    const books = (data.data || []).filter(book => book.availableCount > 0);
                    for (let book of books) {
                        try {
                            const favRes = await this.$axios.get('/bookFavorite/isFavorited/' + book.id);
                            book._favorited = favRes.data.code === 200 ? favRes.data.data : false;
                        } catch { book._favorited = false; }
                    }
                    this.bookTableData = books;
                    this.totalItems = data.total || 0;
                }
            } catch (error) {
                console.error('查询图书异常:', error);
            } finally {
                this.bookLoading = false;
            }
            this.fetchBorrowRecords();
        },
        async fetchBorrowRecords() {
            if (!this.userId) {
                setTimeout(() => { if (this.userId) this.fetchBorrowRecords(); }, 500);
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
            const confirmed = await this.$swal.fire({
                title: '确认借阅',
                text: '确认借阅《' + row.name + '》？',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: '确认',
                cancelButtonText: '取消',
            });
            if (!confirmed.value) return;
            try {
                const response = await this.$axios.post('/borrowRecord/borrow/' + row.id);
                if (response.data.code === 200) {
                    this.$swal.fire({ title: '借阅成功', text: response.data.msg, icon: 'success', showConfirmButton: false, timer: 1500 });
                    this.fetchBooks();
                } else {
                    this.$message.error(response.data.msg);
                }
            } catch (e) {
                this.$message.error('借阅请求异常');
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
                        this.$swal.fire({ title: '归还成功', text: response.data.msg, icon: 'success', showConfirmButton: false, timer: 1500 });
                        this.fetchBooks();
                    } else {
                        this.$message.error(response.data.msg);
                    }
                } catch (e) {
                    this.$message.error('归还请求异常');
                }
            }
        },
        async handleReserve(row) {
            try {
                const response = await this.$axios.post('/bookReservation/reserve/' + row.id);
                if (response.data.code === 200) {
                    this.$message.success(response.data.msg);
                } else {
                    this.$message.error(response.data.msg);
                }
            } catch (e) {
                this.$message.error('预约操作失败');
            }
        },
        async handleFavorite(row) {
            if (row._favorited) {
                try {
                    const response = await this.$axios.post('/bookFavorite/remove/' + row.id);
                    if (response.data.code === 200) {
                        row._favorited = false;
                        this.$message.success('取消收藏成功');
                    } else {
                        this.$message.error(response.data.msg);
                    }
                } catch (e) {
                    this.$message.error('取消收藏失败');
                }
            } else {
                try {
                    const response = await this.$axios.post('/bookFavorite/add/' + row.id);
                    if (response.data.code === 200) {
                        row._favorited = true;
                        this.$message.success('收藏成功');
                    } else {
                        this.$message.error(response.data.msg);
                    }
                } catch (e) {
                    this.$message.error('收藏失败');
                }
            }
        },
        handleFilter() { this.currentPage = 1; this.fetchBooks(); },
        resetCondition() { this.queryDto = {}; this.fetchBooks(); },
        handleSizeChange(val) { this.pageSize = val; this.currentPage = 1; this.fetchBooks(); },
        handleCurrentChange(val) { this.currentPage = val; this.fetchBooks(); },
    },
};
</script>
