<template>
  <div class="food-log">
    <div class="header-mini"><span>🍽️</span> 护眼饮食记录</div>
    <div class="content">
      <!-- Nutrient summary -->
      <div class="card fu">
        <div class="card-title">
          今日视力营养达成
          <span class="chip chip--teal">{{ todayStr }}</span>
        </div>
        <div class="nut-grid">
          <NutRing
            v-for="[k, n] in nutEntries" :key="k"
            :pct="nutPct(k)" :color="n.color" :icon="n.icon" :name="n.name"
          />
        </div>
      </div>

      <!-- Add button -->
      <button class="btn-main fu fu-1" @click="router.push('/food/record')">
        <span>📷</span> 记录这一餐
      </button>

      <!-- Today entries -->
      <div class="card fu fu-2" v-if="entries.length > 0">
        <div class="card-title">
          今日饮食记录
          <span class="chip chip--teal">{{ entries.length }}餐</span>
        </div>
        <div v-for="e in entries" :key="e.id" class="log-entry">
          <div class="log-thumb">🍽️</div>
          <div class="log-body">
            <div class="log-meal">{{ e.meal }}</div>
            <div class="log-foods">{{ e.foods }}</div>
          </div>
          <div class="log-time">{{ e.time }}</div>
        </div>
      </div>

      <div class="card fu fu-2" v-else style="text-align:center;padding:32px 20px">
        <div style="font-size:48px;margin-bottom:12px">🥗</div>
        <div style="font-size:14px;font-weight:700;margin-bottom:6px">今天还没有记录</div>
        <div style="font-size:13px;color:var(--sub);line-height:1.6">
          拍一张餐食照片<br/>AI帮你分析视力营养成分
        </div>
      </div>

      <!-- Quick links -->
      <button class="btn-outline fu fu-3" style="width:100%;text-align:center" @click="router.push('/food/survey')">
        📋 本周营养问卷
      </button>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NUTRIENTS } from '@/data/nutrients'
import NutRing from '@/components/NutRing.vue'

const router = useRouter()

interface FoodEntry {
  id: number; meal: string; foods: string; time: string
  nutrients: Record<string, number>
}

const entries = ref<FoodEntry[]>([])

const nutEntries = computed(() => Object.entries(NUTRIENTS))

const todayStr = new Date().toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })

function nutPct(key: string) {
  const total = entries.value.reduce((s, e) => s + (e.nutrients[key] || 0), 0)
  const daily = NUTRIENTS[key]?.daily || 1
  return Math.min(Math.round(total / daily * 100), 100)
}

// Expose for food/record to push entries
defineExpose({ entries })
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 8px;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.nut-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; }
.log-entry {
  display: flex; gap: 10px; padding: 10px 0;
  border-bottom: 1px dashed var(--border); cursor: pointer;
}
.log-entry:last-child { border-bottom: none; }
.log-thumb {
  width: 52px; height: 52px; border-radius: 12px;
  background: var(--teal-l); display: flex;
  align-items: center; justify-content: center; font-size: 26px;
}
.log-body { flex: 1; min-width: 0; }
.log-meal { font-size: 11px; font-weight: 600; color: var(--teal); }
.log-foods { font-size: 13px; font-weight: 600; color: var(--ink); margin: 2px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.log-time { font-size: 10px; color: var(--sub); flex-shrink: 0; }
</style>
