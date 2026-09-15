<template>
  <div class="feature-shell">
    <section class="toolbar">
      <span class="toolbar-label">图书</span><el-input v-model="queryDto.bookName" size="small" class="toolbar-input" placeholder="图书名称" clearable />
      <span class="toolbar-label">读者</span><el-input v-model="queryDto.userName" size="small" class="toolbar-input" placeholder="读者姓名" clearable />
      <span class="toolbar-label">评分</span><el-select v-model="queryDto.rating" size="small" class="toolbar-input" placeholder="全部" clearable><el-option v-for="n in 5" :key="n" :label="n + ' 星'" :value="n"></el-option></el-select>
      <div class="toolbar-actions"><el-button class="btn-ghost" size="small" @click="handleFilter">立即查询</el-button><el-button class="btn-ghost" size="small" @click="resetQuery">条件重置</el-button></div>
    </section>
    <el-table :data="tableData" row-key="id" class="system-table" border stripe>
      <el-table-column prop="bookName" label="图书" min-width="150"></el-table-column><el-table-column prop="userName" label="读者" width="110"></el-table-column>
      <el-table-column label="评分" width="150"><template slot-scope="scope"><el-rate :value="scope.row.rating" disabled></el-rate></template></el-table-column>
      <el-table-column prop="content" label="书评内容" min-width="260"></el-table-column><el-table-column prop="updateTime" label="更新时间" width="168"></el-table-column>
      <el-table-column label="操作" width="80"><template slot-scope="scope"><span class="text-button danger-text" @click="deleteReview(scope.row)">删除</span></template></el-table-column>
    </el-table>
    <el-pagination class="system-pagination" :current-page="currentPage" :page-size="pageSize" :page-sizes="[8,20]" :total="totalItems" layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange" @current-change="handleCurrentChange" />
  </div>
</template>
<script>
export default {
  data(){return{queryDto:{},tableData:[],currentPage:1,pageSize:8,totalItems:0}},created(){this.fetchData()},methods:{
    async fetchData(){const res=await this.$axios.post('/review/query',{current:this.currentPage,size:this.pageSize,...this.queryDto});if(res.data.code===200){this.tableData=res.data.data||[];this.totalItems=res.data.total||0}},
    handleFilter(){this.currentPage=1;this.fetchData()},resetQuery(){this.queryDto={};this.currentPage=1;this.fetchData()},handleSizeChange(v){this.pageSize=v;this.currentPage=1;this.fetchData()},handleCurrentChange(v){this.currentPage=v;this.fetchData()},
    async deleteReview(row){const ok=await this.$swalConfirm({title:'删除书评',text:'删除后不可恢复，是否继续？'});if(!ok)return;const res=await this.$axios.delete('/review/'+row.id);if(res.data.code===200){this.$message.success(res.data.msg);this.fetchData()}else this.$message.error(res.data.msg)}
  }};
</script>
<style scoped>.danger-text{color:#f56c6c}</style>
