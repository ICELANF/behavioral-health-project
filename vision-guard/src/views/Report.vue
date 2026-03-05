<template>
  <div class="report-page">
    <div class="header-mini"><span>📊</span> 监测报告</div>
    <div class="content">
      <!-- Stats -->
      <div class="stats-grid fu">
        <div v-for="s in stats" :key="s.label" class="stat-card">
          <div class="stat-icon">{{ s.icon }}</div>
          <div>
            <span class="stat-val" :style="{ color: s.color }">{{ s.val }}</span>
            <span class="stat-unit">{{ s.unit }}</span>
          </div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>

      <!-- Comparison -->
      <div class="card fu fu-1">
        <div class="card-title">📊 与对照组对比（课题数据）</div>
        <div v-for="c in comparisons" :key="c.label" style="margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px">
            <span style="font-weight:600;color:var(--ink)">{{ c.label }}</span>
            <span style="color:var(--sub)">{{ c.unit }}</span>
          </div>
          <div style="display:flex;gap:4px;align-items:center">
            <div :style="{ width: c.ours * 1.4 + 'px', height: '10px', background: 'var(--teal)', borderRadius: '5px' }" />
            <span style="font-size:11px;color:var(--teal);font-weight:700">{{ c.ours }}%</span>
          </div>
          <div style="display:flex;gap:4px;align-items:center;margin-top:3px">
            <div :style="{ width: c.ctrl * 1.4 + 'px', height: '10px', background: 'var(--border)', borderRadius: '5px' }" />
            <span style="font-size:11px;color:var(--sub)">{{ c.ctrl }}% 对照</span>
          </div>
        </div>
        <div style="font-size:11px;color:var(--sub);margin-top:4px;font-style:italic">
          * 数据来自试点学校，干预组 vs 对照组
        </div>
      </div>

      <!-- Expert advice -->
      <div class="card fu fu-2">
        <div class="card-title">👨‍⚕️ 专家建议</div>
        <div class="expert-box">
          本月行为数据良好，户外活动时间接近推荐目标。建议重点关注<strong>近距离用眼习惯</strong>，
          尤其是作业时间的阅读距离。下次视力检查时间：2026年3月15日。
        </div>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
const stats = [
  { icon: '🌳', val: '1.6', unit: 'h/天', label: '平均户外时间', color: 'var(--green)' },
  { icon: '📱', val: '1.8', unit: 'h/天', label: '屏幕时间', color: 'var(--amber)' },
  { icon: '👁️', val: '-0.25', unit: 'D', label: '屈光进展（年）', color: 'var(--teal)' },
  { icon: '📏', val: '0.12', unit: 'mm', label: '眼轴增长（年）', color: 'var(--red)' },
]

const comparisons = [
  { label: '户外时间', ours: 78, ctrl: 52, unit: '%达标率' },
  { label: '屈光进展', ours: 65, ctrl: 45, unit: '%控制有效' },
  { label: '问卷依从', ours: 89, ctrl: 74, unit: '%应答率' },
]
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 8px;
}
.content { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.stat-card {
  background: white; border-radius: 14px; padding: 14px;
  border: 1px solid var(--border); text-align: center;
}
.stat-icon { font-size: 24px; margin-bottom: 6px; }
.stat-val { font-size: 22px; font-weight: 900; }
.stat-unit { font-size: 11px; color: var(--sub); margin-left: 2px; }
.stat-label { font-size: 11px; color: var(--sub); margin-top: 2px; }
.expert-box {
  background: var(--teal-l); border-radius: 12px; padding: 14px;
  font-size: 13px; color: var(--ink); line-height: 1.7;
  border-left: 4px solid var(--teal);
}
</style>
