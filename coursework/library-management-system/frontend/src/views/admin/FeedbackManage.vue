<template>
  <div class="feature-shell">
    <section class="toolbar">
      <span class="toolbar-label">读者</span>
      <el-input v-model="queryDto.userName" size="small" class="toolbar-input" placeholder="读者姓名" clearable />
      <span class="toolbar-label">关键词</span>
      <el-input v-model="queryDto.keyword" size="small" class="toolbar-input" placeholder="反馈或回复内容" clearable />
      <span class="toolbar-label">状态</span>
      <el-select v-model="queryDto.status" size="small" class="toolbar-input" placeholder="全部" clearable>
        <el-option label="待处理" :value="0"></el-option>
        <el-option label="已回复" :value="1"></el-option>
      </el-select>
      <div class="toolbar-actions">
        <el-button class="btn-ghost" size="small" @click="handleFilter">立即查询</el-button>
        <el-button class="btn-ghost" size="small" @click="resetQuery">条件重置</el-button>
      </div>
    </section>

    <el-table :data="tableData" row-key="id" class="system-table" border stripe v-loading="loading">
      <el-table-column prop="userName" label="读者" width="110"></el-table-column>
      <el-table-column prop="content" label="反馈内容" min-width="240"></el-table-column>
      <el-table-column prop="createTime" label="提交时间" width="168"></el-table-column>
      <el-table-column label="状态" width="100">
        <template slot-scope="scope"><el-tag :type="scope.row.status === 1 ? 'success' : 'warning'" size="small">{{ scope.row.status === 1 ? '已回复' : '待处理' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="reply" label="管理员回复" min-width="220">
        <template slot-scope="scope">{{ scope.row.reply || '--' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="130" fixed="right">
        <template slot-scope="scope">
          <span class="text-button" @click="openReply(scope.row)">{{ scope.row.status === 1 ? '修改回复' : '回复' }}</span>
          <span class="text-button danger-text" @click="deleteFeedback(scope.row)">删除</span>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination class="system-pagination" :current-page="currentPage" :page-size="pageSize" :page-sizes="[8, 20]"
      :total="totalItems" layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange" @current-change="handleCurrentChange" />

    <el-dialog :visible.sync="replyVisible" :show-close="false" width="460px" custom-class="system-dialog">
      <p slot="title" class="dialog-card-title">回复读者反馈</p>
      <p class="feedback-original">{{ currentFeedback.content }}</p>
      <el-input v-model="reply" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="请输入回复内容" />
      <span slot="footer" class="dialog-footer">
        <el-button class="btn-primary" size="small" @click="saveReply">保存回复</el-button>
        <el-button class="btn-ghost" size="small" @click="replyVisible = false">取消</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
  data() {
    return { queryDto: {}, tableData: [], loading: false, currentPage: 1, pageSize: 8, totalItems: 0, replyVisible: false, currentFeedback: {}, reply: '' };
  },
  created() { this.fetchData(); },
  methods: {
    async fetchData() {
      this.loading = true;
      try {
        const response = await this.$axios.post('/feedback/query', { current: this.currentPage, size: this.pageSize, ...this.queryDto });
        if (response.data.code === 200) { this.tableData = response.data.data || []; this.totalItems = response.data.total || 0; }
      } catch (error) { console.error('查询反馈异常:', error); }
      finally { this.loading = false; }
    },
    openReply(row) { this.currentFeedback = row; this.reply = row.reply || ''; this.replyVisible = true; },
    async saveReply() {
      const reply = this.reply.trim();
      if (!reply) { this.$message.warning('请输入回复内容'); return; }
      try {
        const response = await this.$axios.put('/feedback/reply', { id: this.currentFeedback.id, reply });
        if (response.data.code === 200) { this.$message.success(response.data.msg); this.replyVisible = false; this.fetchData(); }
        else { this.$message.error(response.data.msg); }
      } catch (error) { this.$message.error('回复保存失败'); }
    },
    async deleteFeedback(row) {
      const confirmed = await this.$swalConfirm({ title: '删除反馈记录', text: '删除后不可恢复，是否继续？', icon: 'warning' });
      if (!confirmed) return;
      try {
        const response = await this.$axios.delete('/feedback/' + row.id);
        if (response.data.code === 200) { this.$message.success(response.data.msg); this.fetchData(); }
        else { this.$message.error(response.data.msg); }
      } catch (error) { this.$message.error('反馈删除失败'); }
    },
    handleFilter() { this.currentPage = 1; this.fetchData(); },
    resetQuery() { this.queryDto = {}; this.currentPage = 1; this.fetchData(); },
    handleSizeChange(value) { this.pageSize = value; this.currentPage = 1; this.fetchData(); },
    handleCurrentChange(value) { this.currentPage = value; this.fetchData(); }
  }
};
</script>

<style scoped>
.feedback-original { padding: 12px; margin: 0 0 14px; color: var(--text-sub); line-height: 1.7; border-radius: 8px; background: #f4f7fb; }
.danger-text { margin-left: 12px; color: #f56c6c; }
</style>
