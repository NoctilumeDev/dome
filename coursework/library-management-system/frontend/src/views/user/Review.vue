<template>
  <div class="feature-shell">
    <section class="review-editor">
      <div><p class="system-section-title">{{ form.id ? '修改书评' : '发布书评' }}</p><p class="review-tip">每本书可发布一条书评，内容可随时修改。</p></div>
      <el-select v-model="form.bookId" filterable placeholder="请选择图书" :disabled="Boolean(form.id)" style="width:100%;">
        <el-option v-for="book in books" :key="book.id" :label="book.name + ' · ' + book.author" :value="book.id"></el-option>
      </el-select>
      <el-rate v-model="form.rating" show-text></el-rate>
      <el-input v-model="form.content" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="写下你的阅读感受" />
      <div class="review-actions"><el-button class="btn-ghost" size="small" @click="resetForm">取消</el-button><el-button class="btn-primary" size="small" @click="saveReview">{{ form.id ? '保存修改' : '发布书评' }}</el-button></div>
    </section>
    <p class="system-section-title">我的书评</p>
    <el-table :data="tableData" row-key="id" class="system-table" border stripe>
      <el-table-column prop="bookName" label="图书" min-width="160"></el-table-column>
      <el-table-column label="评分" width="150"><template slot-scope="scope"><el-rate :value="scope.row.rating" disabled></el-rate></template></el-table-column>
      <el-table-column prop="content" label="书评内容" min-width="260"></el-table-column>
      <el-table-column prop="updateTime" label="更新时间" width="168"></el-table-column>
      <el-table-column label="操作" width="120"><template slot-scope="scope"><span class="text-button" @click="editReview(scope.row)">编辑</span><span class="text-button danger-text" @click="deleteReview(scope.row)">删除</span></template></el-table-column>
    </el-table>
  </div>
</template>
<script>
export default {
  data() { return { form: { id: null, bookId: null, rating: 5, content: '' }, books: [], tableData: [] }; },
  created() { this.fetchBooks(); this.fetchReviews(); },
  methods: {
    async fetchBooks() { const res = await this.$axios.post('/book/query', { current: 1, size: 100 }); if (res.data.code === 200) this.books = res.data.data || []; },
    async fetchReviews() { const res = await this.$axios.post('/review/mine', { current: 1, size: 100 }); if (res.data.code === 200) this.tableData = res.data.data || []; },
    resetForm() { this.form = { id: null, bookId: null, rating: 5, content: '' }; },
    editReview(row) { this.form = { id: row.id, bookId: row.bookId, rating: row.rating, content: row.content }; },
    async saveReview() {
      if (!this.form.bookId || !this.form.content.trim()) { this.$message.warning('请选择图书并填写书评'); return; }
      const res = this.form.id ? await this.$axios.put('/review', this.form) : await this.$axios.post('/review/submit', this.form);
      if (res.data.code === 200) { this.$message.success(res.data.msg); this.resetForm(); this.fetchReviews(); } else this.$message.error(res.data.msg);
    },
    async deleteReview(row) { const ok = await this.$swalConfirm({ title: '删除书评', text: '删除后不可恢复，是否继续？' }); if (!ok) return; const res = await this.$axios.delete('/review/' + row.id); if (res.data.code === 200) { this.$message.success(res.data.msg); this.fetchReviews(); } else this.$message.error(res.data.msg); }
  }
};
</script>
<style scoped>
.review-editor { display:grid; gap:14px; padding:18px; margin-bottom:22px; border:1px solid var(--line-color); border-radius:12px; background:#f8fbff; }
.review-tip { margin:-5px 0 0; color:var(--text-muted); font-size:13px; }.review-actions{display:flex;justify-content:flex-end;gap:8px}.danger-text{margin-left:12px;color:#f56c6c}
</style>
