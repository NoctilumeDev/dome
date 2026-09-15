<template>
  <div class="feature-shell">
    <section class="feedback-compose">
      <div>
        <p class="system-section-title">提交反馈</p>
        <p class="feedback-tip">欢迎反馈使用问题或改进建议，管理员处理后会在下方回复。</p>
      </div>
      <el-input v-model="content" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="请描述你的问题或建议" />
      <div class="feedback-actions">
        <el-button class="btn-ghost" size="small" @click="content = ''">清空</el-button>
        <el-button class="btn-primary" size="small" :loading="submitting" @click="submitFeedback">提交反馈</el-button>
      </div>
    </section>

    <p class="system-section-title feedback-list-title">我的反馈记录</p>
    <el-table :data="tableData" row-key="id" class="system-table" border stripe v-loading="loading">
      <el-table-column prop="content" label="反馈内容" min-width="240"></el-table-column>
      <el-table-column prop="createTime" label="提交时间" width="168"></el-table-column>
      <el-table-column label="状态" width="100">
        <template slot-scope="scope">
          <el-tag :type="scope.row.status === 1 ? 'success' : 'warning'" size="small">
            {{ scope.row.status === 1 ? '已回复' : '待处理' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="管理员回复" min-width="260">
        <template slot-scope="scope">{{ scope.row.reply || '暂未回复' }}</template>
      </el-table-column>
      <el-table-column prop="replyTime" label="回复时间" width="168">
        <template slot-scope="scope">{{ scope.row.replyTime || '--' }}</template>
      </el-table-column>
    </el-table>
    <el-pagination class="system-pagination" :current-page="currentPage" :page-size="pageSize" :page-sizes="[5, 10]"
      :total="totalItems" layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange" @current-change="handleCurrentChange" />
  </div>
</template>

<script>
export default {
  data() {
    return { content: '', submitting: false, loading: false, tableData: [], currentPage: 1, pageSize: 5, totalItems: 0 };
  },
  created() { this.fetchData(); },
  methods: {
    async submitFeedback() {
      const content = this.content.trim();
      if (!content) { this.$message.warning('请先填写反馈内容'); return; }
      this.submitting = true;
      try {
        const response = await this.$axios.post('/feedback/submit', { content });
        if (response.data.code === 200) {
          this.$message.success(response.data.msg || '反馈提交成功');
          this.content = '';
          this.currentPage = 1;
          this.fetchData();
        } else { this.$message.error(response.data.msg); }
      } catch (error) { this.$message.error('反馈提交失败'); }
      finally { this.submitting = false; }
    },
    async fetchData() {
      this.loading = true;
      try {
        const response = await this.$axios.post('/feedback/mine', { current: this.currentPage, size: this.pageSize });
        if (response.data.code === 200) {
          this.tableData = response.data.data || [];
          this.totalItems = response.data.total || 0;
        }
      } catch (error) { console.error('查询反馈记录异常:', error); }
      finally { this.loading = false; }
    },
    handleSizeChange(value) { this.pageSize = value; this.currentPage = 1; this.fetchData(); },
    handleCurrentChange(value) { this.currentPage = value; this.fetchData(); }
  }
};
</script>

<style scoped>
.feedback-compose { display: grid; gap: 14px; padding: 18px; margin-bottom: 22px; border: 1px solid var(--line-color); border-radius: 12px; background: #f8fbff; }
.feedback-tip { margin: -5px 0 0; color: var(--text-muted); font-size: 13px; }
.feedback-actions { display: flex; justify-content: flex-end; gap: 8px; }
.feedback-list-title { margin-top: 0; }
@media (max-width: 640px) { .feedback-actions { display: grid; grid-template-columns: 1fr 1fr; } .feedback-actions .el-button { width: 100%; } }
</style>
