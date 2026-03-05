<template>
  <div class="edu-page">
    <div class="header-mini"><span>📚</span> 护眼知识</div>
    <div class="content">
      <div class="card fu">
        <div class="card-title">📌 本周推荐</div>
        <div v-for="(a, i) in articles" :key="i" class="article">
          <div class="article__thumb" :style="{ background: a.bg }">{{ a.emoji }}</div>
          <div class="article__body">
            <span class="article__tag">{{ a.tag }}</span>
            <div class="article__title">{{ a.title }}</div>
            <div class="article__meta">{{ a.meta }}</div>
          </div>
        </div>
      </div>

      <div class="card fu fu-1">
        <div class="card-title">🏫 学校通知</div>
        <div v-for="n in notices" :key="n.date" class="notice">
          <div class="notice__date">{{ n.date }}</div>
          <div>
            <span class="notice__type" :class="{ important: n.type === '重要' }">{{ n.type }}</span>
            <span class="notice__title">{{ n.title }}</span>
          </div>
        </div>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
const articles = [
  { tag: '户外活动', title: '每天2小时户外：为什么阳光是近视最好的"药"？', meta: '科普 · 3分钟', emoji: '☀️', bg: '#FFF8E1' },
  { tag: '用眼习惯', title: '20-20-20法则：最简单的护眼操作手册', meta: '指南 · 2分钟', emoji: '👁️', bg: '#E3F2FD' },
  { tag: '研究进展', title: '近视防控干预试点：首批数据解读', meta: '课题 · 5分钟', emoji: '📊', bg: '#E8F5E9' },
  { tag: '家长必读', title: '孩子看书距离不够？三个家庭小改造', meta: '实用 · 4分钟', emoji: '🏠', bg: '#FCE4EC' },
]

const notices = [
  { date: '03.05', title: '本学期护眼行为打卡继续进行', type: '通知' },
  { date: '03.01', title: '第二次视力检查：3月15日，请家长配合', type: '重要' },
]
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 8px;
}
.content { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.article {
  display: flex; gap: 12px; padding: 12px 0;
  border-bottom: 1px solid #F2F7F6; cursor: pointer;
}
.article:last-child { border-bottom: none; }
.article__thumb {
  width: 70px; height: 52px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 28px;
}
.article__body { flex: 1; }
.article__tag {
  font-size: 10px; color: var(--teal); background: var(--teal-l);
  padding: 2px 6px; border-radius: 4px; font-weight: 600;
}
.article__title { font-size: 13px; font-weight: 600; color: var(--ink); line-height: 1.4; margin-top: 4px; }
.article__meta { font-size: 11px; color: var(--sub); margin-top: 4px; }

.notice {
  display: flex; gap: 12px; padding: 10px 0;
  border-bottom: 1px solid #F2F7F6; align-items: flex-start;
}
.notice__date { font-size: 11px; color: var(--sub); white-space: nowrap; margin-top: 2px; }
.notice__type {
  font-size: 10px; background: #E8F0EF; color: var(--sub);
  padding: 1px 6px; border-radius: 4px; margin-right: 6px;
}
.notice__type.important { background: var(--red-l); color: var(--red); }
.notice__title { font-size: 13px; color: var(--ink); }
</style>
