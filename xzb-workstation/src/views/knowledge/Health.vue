<template>
  <div class="health-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      知识库健康度报告
    </div>
    <div class="content">
      <div class="card fu" style="text-align:center;padding:24px">
        <div class="score-ring">{{ report.coverage_rate }}%</div>
        <div style="font-size:13px;color:var(--sub);margin-top:8px">覆盖率</div>
      </div>

      <div class="card fu fu-1">
        <div class="stat-row">
          <div class="stat-item">
            <div class="stat-val">{{ report.total }}</div>
            <div class="stat-lbl">总条目</div>
          </div>
          <div class="stat-item">
            <div class="stat-val" style="color:var(--xzb-green)">{{ report.confirmed }}</div>
            <div class="stat-lbl">已确认</div>
          </div>
          <div class="stat-item">
            <div class="stat-val" style="color:var(--xzb-amber)">{{ report.needs_review }}</div>
            <div class="stat-lbl">待审查</div>
          </div>
        </div>
      </div>

      <div class="card fu fu-2">
        <div class="card-title">新鲜度</div>
        <div class="health-bar">
          <div class="health-fill" :style="{ width: report.freshness_rate + '%' }" />
        </div>
        <div style="font-size:12px;color:var(--sub);margin-top:6px">{{ report.freshness_rate }}% 的知识处于最新状态</div>
      </div>

      <button class="btn-outline fu fu-3" style="width:100%;text-align:center" @click="router.push('/knowledge')">
        查看全部知识
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { knowledgeHealthReport } from '@/api/xzb'

const router = useRouter()

const report = ref({
  total: 0, confirmed: 0, needs_review: 0,
  coverage_rate: 0, freshness_rate: 0,
})

onMounted(async () => {
  try {
    const res = await knowledgeHealthReport()
    report.value = {
      ...res.data,
      coverage_rate: Math.round((res.data.coverage_rate || 0) * 100),
      freshness_rate: Math.round((res.data.freshness_rate || 0) * 100),
    }
  } catch { /* not registered */ }
})
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 10px;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.score-ring {
  width: 96px; height: 96px; border-radius: 50%; margin: 0 auto;
  border: 6px solid var(--xzb-primary); display: flex;
  align-items: center; justify-content: center;
  font-size: 28px; font-weight: 900; color: var(--xzb-primary);
}
.stat-row { display: flex; gap: 8px; }
.stat-item { flex: 1; text-align: center; padding: 12px 0; }
.stat-val { font-size: 28px; font-weight: 900; color: var(--ink); }
.stat-lbl { font-size: 11px; color: var(--sub); margin-top: 4px; font-weight: 600; }
.health-bar { height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.health-fill { height: 100%; background: var(--grad-header); border-radius: 4px; transition: width .8s; }
</style>
