<template>
  <div class="feature-shell">
    <section class="toolbar">
      <span class="toolbar-label">图书名称</span>
      <el-input
        v-model="bookQueryDto.name"
        class="toolbar-input"
        size="small"
        placeholder="图书名称"
        clearable
        @clear="handleFilterClear"
      />
      <span class="toolbar-label">作者</span>
      <el-input
        v-model="bookQueryDto.author"
        class="toolbar-input"
        size="small"
        placeholder="作者"
        clearable
        @clear="handleFilterClear"
      />
      <span class="toolbar-label">分类</span>
      <el-select
        v-model="bookQueryDto.category"
        size="small"
        class="toolbar-input"
        placeholder="分类"
        clearable
        @clear="handleFilterClear"
      >
        <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.name" />
      </el-select>
      <span class="toolbar-label">入库时间</span>
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
        <el-button class="btn-ghost" size="small" @click="add">新增图书</el-button>
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

    <el-table
      :data="tableData"
      row-key="id"
      class="system-table"
      stripe
      border
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" fixed="left"></el-table-column>
      <el-table-column prop="cover" width="70" label="封面">
        <template slot-scope="scope">
          <el-avatar :size="40" :src="getCoverUrl(scope.row.cover)" style="margin-top: 5px;">
            <template v-if="!scope.row.cover"><span style="font-size:12px;">无图</span></template>
          </el-avatar>
        </template>
      </el-table-column>
      <el-table-column prop="name" width="150" label="图书名称" fixed="left"></el-table-column>
      <el-table-column prop="author" width="100" label="作者"></el-table-column>
      <el-table-column prop="isbn" width="130" label="ISBN"></el-table-column>
      <el-table-column prop="publisher" width="130" label="出版社"></el-table-column>
      <el-table-column prop="category" width="80" label="分类"></el-table-column>
      <el-table-column prop="bookshelfName" width="120" label="所属书架"></el-table-column>
      <el-table-column prop="location" width="150" label="馆藏位置" show-overflow-tooltip></el-table-column>
      <el-table-column prop="totalCount" width="60" label="总量"></el-table-column>
      <el-table-column prop="availableCount" width="60" label="可借">
        <template slot-scope="scope">
          <span :style="{ color: scope.row.availableCount > 0 ? '#13ce66' : '#e6a23c' }">{{ scope.row.availableCount }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" width="160" label="简介" show-overflow-tooltip></el-table-column>
      <el-table-column :sortable="true" prop="createTime" width="160" label="入库时间"></el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template slot-scope="scope">
          <span class="text-button" @click="handleEdit(scope.row)">编辑</span>
          <span class="text-button" style="margin-left: 10px;" @click="handleDelete(scope.row)">删除</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="system-pagination"
      style="margin: 20px 0; float: right;"
      :current-page="currentPage"
      :page-size="pageSize"
      :page-sizes="[5, 7]"
      :total="totalItems"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <el-dialog :show-close="false" :visible.sync="dialogBookOperation" width="420px" custom-class="system-dialog">
      <p slot="title" class="dialog-card-title">{{ !isOperation ? '新增图书' : '编辑图书信息' }}</p>
      <div style="padding:0 20px;">
        <el-row class="dialog-form-item">
          <el-upload class="avatar-uploader" :action="uploadUrl" :headers="uploadHeaders" :show-file-list="false" :on-success="handleCoverSuccess">
            <img v-if="data.cover" :src="data.cover" class="dialog-avatar">
            <i v-else class="el-icon-plus avatar-uploader-icon"></i>
          </el-upload>
        </el-row>
        <el-row class="dialog-form-item">
          <span class="dialog-hover">图书名称</span>
          <input class="dialog-input" v-model="data.name" placeholder="图书名称" />
          <span class="dialog-hover">作者</span>
          <input class="dialog-input" v-model="data.author" placeholder="作者" />
          <span class="dialog-hover">ISBN</span>
          <input class="dialog-input" v-model="data.isbn" placeholder="ISBN号" />
          <span class="dialog-hover">出版社</span>
          <input class="dialog-input" v-model="data.publisher" placeholder="出版社" />
          <span class="dialog-hover">分类</span>
          <el-select size="small" style="width: 100%;" v-model="data.category" placeholder="分类">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.name"></el-option>
          </el-select>
          <span class="dialog-hover">所属书架</span>
          <el-select size="small" style="width: 100%;" v-model="data.bookshelfId" clearable placeholder="请选择书架">
            <el-option
              v-for="shelf in bookshelves"
              :key="shelf.id"
              :label="shelf.name + ' · ' + (shelf.location || '位置未登记')"
              :value="shelf.id"
            ></el-option>
          </el-select>
          <span class="dialog-hover">总数量</span>
          <el-input-number size="small" style="width: 100%;" v-model="data.totalCount" :min="0" :max="9999" placeholder="总数量"></el-input-number>
          <span class="dialog-hover">可借数量</span>
          <el-input-number size="small" style="width: 100%;" v-model="data.availableCount" :min="0" :max="9999" placeholder="可借数量"></el-input-number>
          <span class="dialog-hover">简介</span>
          <el-input type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="图书简介" v-model="data.description">
          </el-input>
        </el-row>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button v-if="!isOperation" class="btn-primary" size="small" @click="saveOperation">新增</el-button>
        <el-button v-else class="btn-primary" size="small" @click="updateOperation">修改</el-button>
        <el-button class="btn-ghost" size="small" @click="dialogBookOperation = false">取消</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
    data() {
        return {
            data: { cover: '', bookshelfId: null },
            currentPage: 1,
            pageSize: 7,
            totalItems: 0,
            dialogBookOperation: false,
            isOperation: false,
            tableData: [],
            searchTime: [],
            selectedRows: [],
            bookQueryDto: {},
            categories: [],
            bookshelves: [],
        };
    },
    watch: {
        dialogBookOperation(v1, v2) {
            if (!v1) {
                this.isOperation = false;
                this.data = {};
            }
        },
    },
    created() {
        this.fetchFreshData();
        this.fetchCategories();
        this.fetchBookshelves();
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
        getCoverUrl(cover) {
            if (!cover) return '';
            if (cover.startsWith('http')) return cover;
            return 'http://localhost:22090' + cover;
        },
        handleCoverSuccess(res, file) {
            if (res.code !== 200) {
                this.$message.error('图书封面上传异常');
                return;
            }
            this.$message.success('图书封面上传成功');
            this.data.cover = res.data;
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection;
        },
        async batchDelete() {
            if (!this.selectedRows.length) {
                this.$message('未选中任何数据');
                return;
            }
            const confirmed = await this.$swalConfirm({
                title: '删除图书数据',
                text: '删除后不可恢复，是否继续？',
                icon: 'warning',
            });
            if (confirmed) {
                try {
                    let ids = this.selectedRows.map(entity => entity.id);
                    const response = await this.$axios.post('/book/batchDelete', ids);
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
                    console.error('图书信息删除异常：', e);
                }
            }
        },
        resetQueryCondition() {
            this.bookQueryDto = {};
            this.searchTime = [];
            this.fetchFreshData();
        },
        clearFormData() {
            this.data = {};
        },
        async saveOperation() {
            // 前端校验
            if (!this.data.name || !this.data.name.trim()) {
                this.$message.warning('图书名称不能为空');
                return;
            }
            if (!this.data.author || !this.data.author.trim()) {
                this.$message.warning('作者不能为空');
                return;
            }
            try {
                const response = await this.$axios.post('/book/save', this.data);
                if (response.data.code === 200) {
                    this.dialogBookOperation = false;
                    await this.fetchFreshData();
                    this.$message.success(response.data.msg);
                    this.clearFormData();
                } else {
                    this.$message.error(response.data.msg);
                }
            } catch (error) {
                console.error('提交表单时出错:', error);
                this.$message.error('提交失败，请稍后再试！');
            }
        },
        async updateOperation() {
            try {
                const response = await this.$axios.put('/book/update', this.data);
                if (response.data.code === 200) {
                    this.dialogBookOperation = false;
                    await this.fetchFreshData();
                    this.$message.success(response.data.msg);
                    this.clearFormData();
                } else {
                    this.$message.error(response.data.msg);
                }
            } catch (error) {
                console.error('提交表单时出错:', error);
                this.$message.error('提交失败，请稍后再试！');
            }
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
                    startTime: startTime,
                    endTime: endTime,
                    ...this.bookQueryDto
                };
                const response = await this.$axios.post('/book/query', params);
                const { data } = response;
                this.tableData = data.data;
                this.totalItems = data.total;
            } catch (error) {
                console.error('查询图书信息异常:', error);
            }
        },
        add() {
            this.isOperation = false;
            this.data = { cover: '', bookshelfId: null };
            this.dialogBookOperation = true;
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
        handleEdit(row) {
            this.dialogBookOperation = true;
            this.isOperation = true;
            this.data = { ...row };
        },
        handleDelete(row) {
            this.selectedRows.push(row);
            this.batchDelete();
        },
        async fetchCategories() {
            try {
                const response = await this.$axios.get('/category/queryAll');
                if (response.data.code === 200) {
                    this.categories = response.data.data || [];
                }
            } catch (error) {
                console.error('查询分类异常:', error);
            }
        },
        async fetchBookshelves() {
            try {
                const response = await this.$axios.get('/bookshelf/queryAll');
                if (response.data.code === 200) {
                    this.bookshelves = response.data.data || [];
                }
            } catch (error) {
                console.error('查询书架异常:', error);
            }
        }
    },
};
</script>
<style scoped lang="scss">
.system-pagination::v-deep .el-pagination__jump,
.system-pagination::v-deep .el-pagination__sizes {
  line-height: 34px;
}

.dialog-avatar {
  width: 120px;
  height: 160px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--line-color);
}

.avatar-uploader {
  display: inline-block;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 120px;
  height: 160px;
  line-height: 160px;
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
}
</style>
