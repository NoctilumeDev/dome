<template>
  <div class="feature-shell">
    <section class="toolbar">
      <span class="toolbar-label">图书名称</span>
      <el-input
        v-model="borrowQueryDto.bookName"
        size="small"
        class="toolbar-input"
        placeholder="图书名称"
        clearable
        @clear="handleFilterClear"
      />
      <span class="toolbar-label">借阅人</span>
      <el-input
        v-model="borrowQueryDto.userName"
        size="small"
        class="toolbar-input"
        placeholder="借阅人"
        clearable
        @clear="handleFilterClear"
      />
      <span class="toolbar-label">借阅时间</span>
      <el-date-picker
        v-model="searchTime"
        size="small"
        class="toolbar-input"
        type="daterange"
        range-separator="至"
        start-placeholder="起始时间"
        end-placeholder="结束时间"
      />
      <span class="toolbar-label">逾期</span>
      <el-select
        v-model="borrowQueryDto.overdue"
        size="small"
        class="toolbar-input"
        placeholder="全部"
        clearable
        @change="handleFilter"
      >
        <el-option label="全部" :value="null"></el-option>
        <el-option label="逾期" :value="true"></el-option>
        <el-option label="未逾期" :value="false"></el-option>
      </el-select>
      <div class="toolbar-actions">
        <el-button class="btn-ghost" size="small" @click="handleFilter">立即查询</el-button>
        <el-button class="btn-ghost" size="small" @click="resetQueryCondition">条件重置</el-button>
      </div>
    </section>

    <el-table :data="tableData" row-key="id" class="system-table" border stripe>
      <el-table-column prop="bookName" width="188" label="图书名称"></el-table-column>
      <el-table-column prop="userName" width="128" label="借阅人"></el-table-column>
      <el-table-column prop="borrowTime" width="168" label="借阅时间"></el-table-column>
      <el-table-column prop="dueDate" width="168" label="应还日期">
        <template slot-scope="scope">
          <span :style="{ color: (scope.row.status === false && scope.row.dueDate && new Date(scope.row.dueDate) < new Date()) ? '#f56c6c' : '#303133' }">
            {{ scope.row.dueDate || '--' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="returnTime" width="168" label="归还时间">
        <template slot-scope="scope">
          <span>{{ scope.row.returnTime || '--' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" width="108" label="借阅状态">
        <template slot-scope="scope">
          <el-tag :type="scope.row.status ? 'success' : 'warning'" size="small">
            {{ scope.row.status ? '已归还' : '借阅中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template slot-scope="scope">
          <span v-if="!scope.row.status" class="text-button" @click="handleReturn(scope.row)">还书</span>
          <span v-else style="color: #909399;">已归还</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      style="margin: 20px 0;float: right;"
      :current-page="currentPage"
      :page-sizes="[8, 20]"
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
            data: {},
            currentPage: 1,
            pageSize: 8,
            totalItems: 0,
            tableData: [],
            searchTime: [],
            borrowQueryDto: {},
        };
    },
    created() {
        this.fetchFreshData();
    },
    methods: {
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
                            title: '归还提示',
                            text: response.data.msg,
                            icon: 'success',
                            showConfirmButton: false,
                            timer: 2000,
                        });
                        this.fetchFreshData();
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
                    console.error('还书操作异常：', e);
                }
            }
        },
        resetQueryCondition() {
            this.borrowQueryDto = {};
            this.searchTime = [];
            this.fetchFreshData();
        },
        async fetchFreshData() {
            try {
                this.tableData = [];
                let startTime = null;
                let endTime = null;
                if (this.searchTime != null && this.searchTime.length === 2) {
                    const [startDate, endDate] = await Promise.all(this.searchTime.map(date => date.toISOString()));
                    startTime = startDate.split('T')[0] + 'T00:00:00';
                    endTime = endDate.split('T')[0] + 'T23:59:59';
                }
                const params = {
                    current: this.currentPage,
                    size: this.pageSize,
                    startTime: startTime,
                    endTime: endTime,
                    ...this.borrowQueryDto
                };
                const response = await this.$axios.post('/borrowRecord/query', params);
                const { data } = response;
                this.tableData = data.data;
                this.totalItems = data.total;
            } catch (error) {
                console.error('查询借阅记录异常:', error);
            }
        },
        handleFilter() {
            this.currentPage = 1;
            this.fetchFreshData();
        },
        handleFilterClear() {
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
    },
};
</script>
