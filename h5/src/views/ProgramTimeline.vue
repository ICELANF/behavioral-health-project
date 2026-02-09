<template>
  <div class="page-container">
    <van-nav-bar title="行为轨迹" left-arrow @click-left="$router.back()">
      <template #right>
        <van-icon name="bar-chart-o" size="20" @click="$router.push(`/program/${eid}/progress`)" />
      </template>
    </van-nav-bar>

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <template v-else-if="timeline.length">
        <div v-for="day in timeline" :key="day.day_number" class="day-card">
          <div class="day-header">
            <div class="day-badge" :class="{ milestone: day.is_milestone, today: day.is_today }">
              Day {{ day.day_number }}
            </div>
            <span class="day-date">{{ day.date }}</span>
            <van-tag v-if="day.is_milestone" type="warning" size="small" round>里程碑</van-tag>
            <van-tag v-if="day.is_today" type="primary" size="small" round>今天</van-tag>
          </div>

          <div v-if="day.pushes && day.pushes.length" class="day-pushes">
            <div v-for="push in day.pushes" :key="push.slot" class="push-item" :class="{ answered: push.answered }">
              <div class="push-left">
                <span class="slot-icon">{{ slotIcon(push.slot) }}</span>
                <span class="slot-label">{{ slotLabel(push.slot) }}</span>
              </div>
              <div class="push-right">
                <van-icon v-if="push.answered" name="success" color="#07c160" />
                <van-icon v-else name="clock-o" color="#c8c9cc" />
              </div>
            </div>
          </div>

          <div v-if="day.summary" class="day-summary">{{ day.summary }}</div>
        </div>
      </template>

      <van-empty v-else description="暂无轨迹数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { programApi } from '@/api/program'

const route = useRoute()
const eid = route.params.id as string

const loading = ref(true)
const timeline = ref<any[]>([])

const slotIcon = (s: string) => {
  const m: Record<string, string> = { morning: '\u{2600}', noon: '\u{1F324}', evening: '\u{1F319}', immediate: '\u{26A1}' }
  return m[s] || '\u{1F4E8}'
}
const slotLabel = (s: string) => {
  const m: Record<string, string> = { morning: '早间', noon: '午间', evening: '晚间', immediate: '即时' }
  return m[s] || s
}

onMounted(async () => {
  try {
    const res: any = await programApi.getTimeline(eid)
    timeline.value = res.days || res || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-container { min-height: 100vh; background: #f5f5f5; }
.page-content { padding: 12px; }
.loading { text-align: center; padding: 60px 0; }

.day-card {
  background: #fff; border-radius: 12px; padding: 14px; margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.day-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.day-badge {
  width: 56px; text-align: center; font-size: 12px; font-weight: 700;
  padding: 2px 8px; border-radius: 10px; background: #f0f0f0; color: #666;
}
.day-badge.milestone { background: #fff7e6; color: #fa8c16; }
.day-badge.today { background: #e6f7ff; color: #1989fa; }
.day-date { font-size: 12px; color: #999; }

.day-pushes { display: flex; flex-direction: column; gap: 6px; }
.push-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 10px; border-radius: 8px; background: #fafafa;
}
.push-item.answered { background: #f6ffed; }
.push-left { display: flex; align-items: center; gap: 6px; }
.slot-icon { font-size: 16px; }
.slot-label { font-size: 13px; color: #333; }

.day-summary { font-size: 12px; color: #666; margin-top: 8px; line-height: 1.5; }
</style>
