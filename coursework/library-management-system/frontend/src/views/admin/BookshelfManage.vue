<template>
  <div class="feature-shell">
    <section class="toolbar">
      <span class="toolbar-label">书架名称</span>
      <el-input
        v-model="queryDto.name"
        size="small"
        class="toolbar-input"
        placeholder="书架名称"
        clearable
        @clear="handleFilter"
      />
      <div class="toolbar-actions">
        <el-button class="btn-ghost" size="small" @click="handleFilter">立即查询</el-button>
        <el-button class="btn-ghost" size="small" @click="add">新增书架</el-button>
        <el-button
          size="small"
          :disabled="!selectedRows.length"
          type="danger"
          class="btn-danger-soft"
          @click="batchDelete"
        >批量删除</el-button>
        <el-button class="btn-ghost" size="small" @click="resetCondition">条件重置</el-button>
      </div>
    </section>

    <el-table :data="tableData" row-key="id" class="system-table" border stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55"></el-table-column>
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="name" label="书架名称" width="170"></el-table-column>
      <el-table-column prop="location" label="所在位置" width="160"></el-table-column>
      <el-table-column prop="capacity" label="容量" width="100"></el-table-column>
      <el-table-column prop="description" label="备注" width="200"></el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="180"></el-table-column>
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
      :page-sizes="[5, 10]"
      :page-size="pageSize"
      :total="totalItems"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <el-dialog :show-close="false" :visible.sync="dialogVisible" width="30%" custom-class="system-dialog">
      <p slot="title" class="dialog-card-title">{{ !isEdit ? '新增书架' : '编辑书架' }}</p>
      <div style="padding:0 20px;">
        <span class="dialog-hover">书架名称</span>
        <input class="dialog-input" v-model="form.name" placeholder="书架名称" />
        <span class="dialog-hover">所在位置</span>
        <input class="dialog-input" v-model="form.location" placeholder="所在位置" />
        <span class="dialog-hover">容量</span>
        <input class="dialog-input" v-model.number="form.capacity" type="number" placeholder="容量" />
        <span class="dialog-hover">备注</span>
        <input class="dialog-input" v-model="form.description" placeholder="备注" />
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button class="btn-primary" size="small" v-if="!isEdit" @click="saveOperation">新增</el-button>
        <el-button class="btn-primary" size="small" v-else @click="updateOperation">修改</el-button>
        <el-button class="btn-ghost" size="small" @click="dialogVisible = false">取消</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
    data() {
        return {
            form: { name: '', location: '', capacity: 100, description: '' },
            currentPage: 1,
            pageSize: 10,
            totalItems: 0,
            dialogVisible: false,
            isEdit: false,
            tableData: [],
            selectedRows: [],
            queryDto: {},
        };
    },
    created() {
        this.fetchData();
    },
    methods: {
        async fetchData() {
            try {
                const params = { current: this.currentPage, size: this.pageSize, ...this.queryDto };
                const response = await this.$axios.post('/bookshelf/query', params);
                const { data } = response;
                if (data.code === 200) {
                    this.tableData = data.data || [];
                    this.totalItems = data.total || 0;
                }
            } catch (error) {
                console.error('查询书架异常:', error);
            }
        },
        handleSelectionChange(selection) { this.selectedRows = selection; },
        async batchDelete() {
            if (!this.selectedRows.length) { this.$message('未选中任何数据'); return; }
            const confirmed = await this.$swalConfirm({ title: '删除书架', text: '删除后不可恢复，是否继续？', icon: 'warning' });
            if (confirmed) {
                try {
                    let ids = this.selectedRows.map(e => e.id);
                    const response = await this.$axios.post('/bookshelf/batchDelete', ids);
                    if (response.data.code === 200) {
                        this.$swal.fire({ title: '删除提示', text: response.data.msg, icon: 'success', showConfirmButton: false, timer: 2000 });
                        this.fetchData();
                    }
                } catch (e) {
                    this.$message.error('删除失败');
                }
            }
        },
        async saveOperation() {
            try {
                const response = await this.$axios.post('/bookshelf/save', this.form);
                if (response.data.code === 200) {
                    this.dialogVisible = false;
                    this.$message.success(response.data.msg);
                    this.fetchData();
                    this.form = { name: '', location: '', capacity: 100, description: '' };
                } else {
                    this.$message.error(response.data.msg);
                }
            } catch (error) {
                this.$message.error('新增失败');
            }
        },
        async updateOperation() {
            try {
                const response = await this.$axios.put('/bookshelf/update', this.form);
                if (response.data.code === 200) {
                    this.dialogVisible = false;
                    this.$message.success(response.data.msg);
                    this.fetchData();
                    this.form = { name: '', location: '', capacity: 100, description: '' };
                } else {
                    this.$message.error(response.data.msg);
                }
            } catch (error) {
                this.$message.error('修改失败');
            }
        },
        add() { this.isEdit = false; this.form = { name: '', location: '', capacity: 100, description: '' }; this.dialogVisible = true; },
        handleEdit(row) { this.isEdit = true; this.form = { ...row }; this.dialogVisible = true; },
        handleDelete(row) { this.selectedRows = [row]; this.batchDelete(); },
        handleFilter() { this.currentPage = 1; this.fetchData(); },
        resetCondition() { this.queryDto = {}; this.fetchData(); },
        handleSizeChange(val) { this.pageSize = val; this.currentPage = 1; this.fetchData(); },
        handleCurrentChange(val) { this.currentPage = val; this.fetchData(); },
    },
};
</script>

