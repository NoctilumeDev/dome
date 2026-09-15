<template>
  <div class="feature-shell assistant-page">
    <section class="assistant-hero system-card">
      <div class="hero-copy">
        <div class="eyebrow">LIBRARY INTELLIGENCE</div>
        <h2>馆藏智能问答</h2>
        <p>DeepSeek 是可选的语义理解层，只负责提高自然语言召回；最终答案始终以馆藏数据库为准。</p>
      </div>
      <div class="trust-flow" aria-label="问答安全处理流程">
        <span><i class="el-icon-lock"></i> 本地范围过滤</span>
        <span><i class="el-icon-finished"></i> 意图白名单</span>
        <span><i class="el-icon-tickets"></i> 参数化查询</span>
        <span><i class="el-icon-coin"></i> 数据库事实回答</span>
      </div>
      <div class="degradation-note" aria-label="模型降级说明">
        <div class="degradation-icon"><i class="el-icon-set-up"></i></div>
        <div class="degradation-copy">
          <p class="section-kicker">GRACEFUL DEGRADATION</p>
          <h3>可降级，但不越过安全边界</h3>
          <p>DeepSeek 可用时负责理解口语和提高查全率；未配置或暂时不可用时，系统改用本地规则，复杂表达可能漏检，但范围过滤、参数化查询和数据库事实回答保持不变。</p>
        </div>
        <div class="tradeoff-tags">
          <span class="is-stable">安全性保持</span>
          <span class="is-variable">自然语言召回降低</span>
        </div>
      </div>
    </section>

    <section class="assistant-console system-card">
      <div class="question-section">
        <div class="section-heading">
          <div>
            <p class="section-kicker">ASK THE CATALOG</p>
            <h3>你想查询什么？</h3>
          </div>
          <span class="scope-badge">仅限馆藏相关问题</span>
        </div>

        <div class="prompt-grid">
          <button
            v-for="prompt in promptExamples"
            :key="prompt"
            type="button"
            class="prompt-chip"
            @click="question = prompt"
          >
            {{ prompt }}
          </button>
        </div>

        <el-input
          v-model="question"
          type="textarea"
          :rows="4"
          :maxlength="120"
          show-word-limit
          resize="none"
          placeholder="例如：书名《三体》、作者：余华、分类：编程"
          class="assistant-input"
          @keydown.ctrl.enter.native="askQuestion"
        />

        <div class="composer-footer">
          <p><i class="el-icon-info"></i> 天气、股票、闲聊等问题会在本地直接拒绝，不消耗模型 API。</p>
          <div class="toolbar-actions">
            <el-button class="btn-ghost action-button" :disabled="loading" @click="resetForm">清空</el-button>
            <el-button class="btn-primary action-button" :loading="loading" @click="askQuestion">
              {{ loading ? '正在核验馆藏' : '查询馆藏' }}
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="hasResult" class="result-section">
      <div class="result-status">
        <span :class="['verification-pill', databaseVerified ? 'is-verified' : 'is-refused']">
          <i :class="databaseVerified ? 'el-icon-circle-check' : 'el-icon-warning-outline'"></i>
          {{ databaseVerified ? '数据库已核验' : '本地范围已处理' }}
        </span>
        <span v-if="databaseVerified" class="result-count">本次返回 {{ total }} 条馆藏记录</span>
        <span v-if="planningSource" :class="['source-pill', modelCalled ? 'is-model' : 'is-local']">
          <i :class="modelCalled ? 'el-icon-connection' : 'el-icon-cpu'"></i>
          {{ modelCallLabel }}
        </span>
        <span v-if="intent" class="intent-tag">{{ intentLabel }}</span>
      </div>

      <div class="answer-panel">
        <div class="assistant-avatar"><i class="el-icon-reading"></i></div>
        <div>
          <p class="answer-label">馆藏助手</p>
          <p class="assistant-answer">{{ answer }}</p>
        </div>
      </div>

      <p v-if="modelNote" class="model-note">
        <i class="el-icon-document-checked"></i> {{ modelNote }}
      </p>

      <el-collapse v-if="generatedSql" class="sql-collapse">
        <el-collapse-item name="sql">
          <template slot="title">
            <span class="sql-title"><i class="el-icon-tickets"></i> 查看实际执行的参数化 SQL</span>
          </template>
          <pre class="assistant-sql">{{ generatedSql }}</pre>
        </el-collapse-item>
      </el-collapse>

      <div v-if="books.length" class="table-wrap">
        <el-table :data="books" class="system-table" stripe>
          <el-table-column prop="name" label="书名" min-width="180"></el-table-column>
          <el-table-column prop="author" label="作者" min-width="140"></el-table-column>
          <el-table-column prop="category" label="分类" width="100"></el-table-column>
          <el-table-column prop="bookshelfName" label="所属书架" min-width="120"></el-table-column>
          <el-table-column prop="location" label="馆藏位置" min-width="150"></el-table-column>
          <el-table-column prop="publisher" label="出版社" min-width="170"></el-table-column>
          <el-table-column prop="isbn" label="ISBN" min-width="145"></el-table-column>
          <el-table-column prop="availableCount" label="可借" width="88" align="center">
            <template slot-scope="scope">
              <span :class="['stock-value', scope.row.availableCount > 0 ? 'has-stock' : 'no-stock']">
                {{ scope.row.availableCount }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="馆藏简介" min-width="220" show-overflow-tooltip></el-table-column>
        </el-table>
      </div>
      </div>

      <div v-else class="assistant-empty">
        <div class="empty-orbit"><i class="el-icon-search"></i></div>
        <div>
          <h3>等待你的馆藏问题</h3>
          <p>可以查具体书名，也可以按作者、分类、出版社或可借状态筛选。</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
const INTENT_LABELS = {
  SEARCH_BOOK: '查找图书',
  FIND_AUTHOR: '作者检索',
  FIND_CATEGORY: '分类检索',
  CHECK_AVAILABILITY: '可借状态',
  RECOMMEND_BOOK: '馆藏推荐',
  FIND_LOCATION: '位置查询',
  LIST_CATALOG: '馆藏总览',
  LIST_USERS: '用户查询',
  BORROW_OVERVIEW: '借阅查询',
  MY_BORROWS: '我的借阅',
  RECENT_RETURNS: '最近归还',
  DUE_SOON: '即将到期',
  MY_DUE_SOON: '我的到期',
  OVERDUE_BORROWS: '逾期查询',
  SEARCH_REVIEWS: '书评查询',
  MY_REVIEWS: '我的书评',
  FEEDBACK_OVERVIEW: '反馈查询',
  MY_FEEDBACK: '我的反馈',
  FORBIDDEN: '权限受限',
  OUT_OF_SCOPE: '超出范围',
};

export default {
  name: 'BookAssistant',
  data() {
    return {
      question: '',
      loading: false,
      books: [],
      total: 0,
      generatedSql: '',
      modelNote: '',
      planningSource: '',
      modelCalled: false,
      answer: '',
      intent: '',
      databaseVerified: false,
      hasResult: false,
      promptExamples: [
        '《三体》放在哪里？',
        '哪些书没还？',
        '给我推荐一些计算机的书籍',
        '谁快要逾期了？',
      ],
    };
  },
  computed: {
    intentLabel() {
      return INTENT_LABELS[this.intent] || this.intent;
    },
    modelCallLabel() {
      if (!this.modelCalled) return '本地解析 · API 0 次';
      return this.planningSource === 'DEEPSEEK'
        ? 'DeepSeek 调用成功'
        : 'DeepSeek 调用失败 · 已本地降级';
    },
  },
  methods: {
    async askQuestion() {
      const question = this.question.trim();
      if (!question) {
        this.$message.warning('请先输入你的馆藏问题');
        return;
      }

      this.loading = true;
      try {
        const response = await this.$axios.post('/book/assistant/query', { question });
        const payload = response.data;
        if (payload.code !== 200 || !payload.data) {
          this.$message.error(payload.msg || '查询失败，请稍后重试');
          return;
        }

        const result = payload.data;
        this.books = result.books || [];
        this.total = result.total || 0;
        this.generatedSql = result.generatedSql || '';
        this.modelNote = result.modelNote || '';
        this.planningSource = result.planningSource || '';
        this.modelCalled = result.modelCalled === true;
        this.answer = result.answer || '馆藏查询已完成。';
        this.intent = result.intent || '';
        this.databaseVerified = result.databaseVerified === true;
        this.hasResult = true;
      } catch (error) {
        const message = error.response && error.response.data && error.response.data.msg;
        this.$message.error(message || '请求异常，请稍后再试');
      } finally {
        this.loading = false;
      }
    },
    resetForm() {
      this.question = '';
      this.books = [];
      this.total = 0;
      this.generatedSql = '';
      this.modelNote = '';
      this.planningSource = '';
      this.modelCalled = false;
      this.answer = '';
      this.intent = '';
      this.databaseVerified = false;
      this.hasResult = false;
    },
  },
};
</script>

<style scoped lang="scss">
.assistant-page {
  --assistant-ink: #17324d;
  --assistant-blue: #2457d6;
  --assistant-cyan: #0d9488;
  --assistant-soft: #eef6ff;
  --assistant-line: #dce8f5;
}

.assistant-hero {
  position: relative;
  overflow: hidden;
  padding: 28px 30px;
  border: 1px solid #cfe0f2;
  background:
    radial-gradient(circle at 88% 18%, rgba(13, 148, 136, 0.16), transparent 30%),
    linear-gradient(125deg, #f8fbff 0%, #edf5ff 54%, #f7fffd 100%);
}

.assistant-hero::after {
  content: '';
  position: absolute;
  right: -54px;
  bottom: -72px;
  width: 220px;
  height: 220px;
  border: 32px solid rgba(36, 87, 214, 0.07);
  border-radius: 50%;
}

.hero-copy {
  position: relative;
  z-index: 1;
  max-width: 720px;
}

.eyebrow,
.section-kicker {
  margin: 0 0 8px;
  color: var(--assistant-blue);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.hero-copy h2,
.section-heading h3,
.assistant-empty h3 {
  margin: 0;
  color: var(--assistant-ink);
}

.hero-copy h2 {
  font-size: 30px;
  letter-spacing: -0.04em;
}

.hero-copy p {
  margin: 10px 0 0;
  color: #587089;
  font-size: 14px;
  line-height: 1.7;
}

.trust-flow {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 24px;
}

.trust-flow span {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 0;
  min-height: 32px;
  padding: 7px 10px;
  border: 1px solid rgba(36, 87, 214, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: #36516c;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  text-align: center;
  overflow-wrap: anywhere;
}

.degradation-note {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(36, 87, 214, 0.12);
}

.degradation-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #e9f8f3;
  color: #087a67;
  font-size: 19px;
}

.degradation-copy h3 {
  margin: 0;
  color: var(--assistant-ink);
  font-size: 16px;
  overflow-wrap: anywhere;
}

.degradation-copy p:last-child {
  margin: 7px 0 0;
  color: #60758a;
  font-size: 12px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

.tradeoff-tags {
  display: grid;
  gap: 7px;
  justify-items: end;
}

.tradeoff-tags span {
  padding: 6px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.tradeoff-tags .is-stable {
  background: #e9f8f3;
  color: #087a67;
}

.tradeoff-tags .is-variable {
  background: #fff7e8;
  color: #9a6113;
}

.assistant-console {
  margin-top: 16px;
  padding: 24px;
}

.result-section,
.assistant-empty {
  margin-top: 22px;
  padding-top: 20px;
  border-top: 1px solid var(--assistant-line);
}

.section-heading,
.composer-footer,
.result-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.section-heading > div,
.degradation-copy,
.answer-panel > div:last-child {
  min-width: 0;
}

.section-heading h3 {
  font-size: 19px;
}

.scope-badge,
.verification-pill,
.intent-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.scope-badge {
  padding: 7px 11px;
  background: #fff7e8;
  color: #9a6113;
  line-height: 1.4;
  text-align: center;
  white-space: normal;
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin: 18px 0 12px;
}

.prompt-chip {
  padding: 8px 12px;
  border: 1px solid var(--assistant-line);
  border-radius: 9px;
  background: #f8fbff;
  color: #49657f;
  font: inherit;
  font-size: 12px;
  line-height: 1.45;
  overflow-wrap: anywhere;
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.prompt-chip:hover {
  border-color: #8db1e8;
  color: var(--assistant-blue);
  transform: translateY(-1px);
}

.assistant-input {
  width: 100%;
}

.assistant-input ::v-deep .el-textarea__inner {
  padding: 14px 15px 28px;
  border-color: var(--assistant-line);
  border-radius: 12px;
  color: var(--assistant-ink);
  font-family: inherit;
  line-height: 1.7;
}

.assistant-input ::v-deep .el-textarea__inner:focus {
  border-color: #7da6e8;
  box-shadow: 0 0 0 3px rgba(36, 87, 214, 0.08);
}

.composer-footer {
  align-items: flex-end;
  margin-top: 14px;
}

.composer-footer p {
  flex: 1 1 320px;
  min-width: 0;
  margin: 0;
  color: #74879a;
  font-size: 12px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-actions .el-button + .el-button {
  margin-left: 0;
}

.action-button {
  min-width: 104px;
  height: 38px;
}

.result-status {
  justify-content: flex-start;
}

.verification-pill {
  padding: 7px 11px;
}

.verification-pill.is-verified {
  background: #e9f8f3;
  color: #087a67;
}

.verification-pill.is-refused {
  background: #fff4e5;
  color: #a05a0b;
}

.result-count {
  color: #60758a;
  font-size: 12px;
}

.source-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.source-pill.is-local {
  background: #eef3f8;
  color: #526b83;
}

.source-pill.is-model {
  background: #e9f8f3;
  color: #087a67;
}

.intent-tag {
  margin-left: auto;
  padding: 6px 10px;
  background: #edf3ff;
  color: var(--assistant-blue);
}

.answer-panel {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 13px;
  margin-top: 18px;
  padding: 4px 0 4px 16px;
  border-left: 3px solid #8db1e8;
}

.assistant-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: var(--assistant-ink);
  color: #fff;
  font-size: 18px;
}

.answer-label {
  margin: 0 0 6px;
  color: #6d8296;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.assistant-answer {
  margin: 0;
  color: #1d3852;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-line;
  overflow-wrap: anywhere;
}

.model-note {
  margin: 12px 2px 0;
  color: #60758a;
  font-size: 12px;
}

.sql-collapse {
  margin-top: 12px;
  border-color: var(--assistant-line);
}

.sql-title {
  color: #526b83;
  font-size: 12px;
  font-weight: 600;
}

.assistant-sql {
  margin: 0 0 12px;
  padding: 13px 14px;
  overflow-x: auto;
  border: 1px dashed #c7d9ec;
  border-radius: 10px;
  background: #f6f9fc;
  color: #29445f;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.table-wrap {
  margin-top: 18px;
  overflow-x: auto;
}

.stock-value {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 25px;
  border-radius: 7px;
  font-weight: 700;
}

.stock-value.has-stock {
  background: #e9f8f3;
  color: #087a67;
}

.stock-value.no-stock {
  background: #fff1e8;
  color: #b45309;
}

.assistant-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 150px;
  color: #7a8ea2;
  text-align: left;
}

.empty-orbit {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  border: 1px solid #cfe0f2;
  border-radius: 50%;
  background: var(--assistant-soft);
  color: var(--assistant-blue);
  font-size: 22px;
}

.assistant-empty h3 {
  font-size: 17px;
}

.assistant-empty p {
  margin: 6px 0 0;
  font-size: 13px;
}

@media (max-width: 1050px) {
  .trust-flow,
  .prompt-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .degradation-note {
    grid-template-columns: 40px minmax(0, 1fr);
  }

  .tradeoff-tags {
    grid-column: 2;
    display: flex;
    flex-wrap: wrap;
    justify-items: start;
  }

  .composer-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar-actions {
    align-self: flex-end;
  }
}

@media (max-width: 760px) {
  .assistant-hero,
  .assistant-console {
    padding: 19px;
  }

  .hero-copy h2 {
    font-size: 25px;
  }

  .degradation-note {
    grid-template-columns: 1fr;
  }

  .tradeoff-tags {
    grid-column: auto;
    display: flex;
    flex-wrap: wrap;
    justify-items: start;
  }

  .section-heading {
    align-items: flex-start;
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .action-button {
    width: 100%;
  }

  .intent-tag {
    margin-left: 0;
  }

  .assistant-empty {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .trust-flow,
  .prompt-grid {
    grid-template-columns: 1fr;
  }

  .result-status {
    align-items: flex-start;
    flex-direction: column;
  }

  .answer-panel {
    grid-template-columns: 1fr;
  }
}
</style>
