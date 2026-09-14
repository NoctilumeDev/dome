<template>
  <div class="feature-shell">
    <p class="system-section-title">数据概览</p>
    <div class="metric-grid">
      <article class="metric-card">
        <p class="metric-card-title">图书总数</p>
        <p class="metric-card-value">{{ overviewCards[0].value }}</p>
      </article>
      <article class="metric-card">
        <p class="metric-card-title">用户总数</p>
        <p class="metric-card-value">{{ overviewCards[1].value }}</p>
      </article>
      <article class="metric-card">
        <p class="metric-card-title">借阅中</p>
        <p class="metric-card-value">{{ overviewCards[2].value }}</p>
      </article>
      <article class="metric-card">
        <p class="metric-card-title">书架总数</p>
        <p class="metric-card-value">{{ overviewCards[3].value }}</p>
      </article>
    </div>
  </div>
</template>
<script>
export default {
    data() {
        return {
            overviewCards: [
                { value: 0 },
                { value: 0 },
                { value: 0 },
                { value: 0 },
            ],
        }
    },
    created() {
        this.loadOverview();
    },
    methods: {
        async loadOverview() {
            try {
                const bookRes = await this.$axios.post('/book/query', { current: 1, size: 1 });
                if (bookRes.data.code === 200) this.overviewCards[0].value = bookRes.data.total || 0;
                const userRes = await this.$axios.post('/user/query', { current: 1, size: 1 });
                if (userRes.data.code === 200) this.overviewCards[1].value = userRes.data.total || 0;
                const borrowRes = await this.$axios.post('/borrowRecord/query', { current: 1, size: 1, status: false });
                if (borrowRes.data.code === 200) this.overviewCards[2].value = borrowRes.data.total || 0;
                const shelfRes = await this.$axios.post('/bookshelf/query', { current: 1, size: 1 });
                if (shelfRes.data.code === 200) this.overviewCards[3].value = shelfRes.data.total || 0;
            } catch (err) {
                console.error(err);
            }
        },
    },
};
</script>
