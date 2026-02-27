<template>
  <PageShell title="我的学分" :show-back="true">

    <!-- 学分汇总卡片 -->
    <div class="summary-card">
      <div class="total-credits">
        <span class="number">{{ credits.total?.total_credits || 0 }}</span>
        <span class="label">总学分</span>
      </div>
      <div class="credit-row">
        <div class="credit-item">
          <span class="num">{{ credits.total?.mandatory_credits || 0 }}</span>
          <span class="lab">必修</span>
        </div>
        <div class="credit-item">
          <span class="num">{{ credits.total?.elective_credits || 0 }}</span>
          <span class="lab">选修</span>
        </div>
      </div>
    </div>

    <!-- 模块分布 -->
    <van-cell-group title="模块学分分布" inset>
      <van-cell title="M1 行为处方" :value="`${credits.total?.m1_credits || 0} 学分`" />
      <van-cell title="M2 生活方式" :value="`${credits.total?.m2_credits || 0} 学分`" />
      <van-cell title="M3 心智成长" :value="`${credits.total?.m3_credits || 0} 学分`" />
      <van-cell title="M4 教练技术" :value="`${credits.total?.m4_credits || 0} 学分`" />
    </van-cell-group>

    <!-- 按类型细分 -->
    <van-cell-group title="模块类型明细" inset v-if="credits.by_type.length">
      <van-cell
        v-for="item in credits.by_type"
        :key="item.module_type"
        :title="item.module_type"
        :value="`${item.total_earned || 0} / ${item.module_count || 0} 模块`"
      />
    </van-cell-group>

    <!-- 学分记录 -->
    <van-cell-group title="学分记录" inset>
      <van-empty v-if="!records.length" description="暂无学分记录" />
      <van-cell
        v-for="r in records"
        :key="r.id"
        :title="r.module_title"
        :label="`${r.module_type} · ${r.tier || '-'}`"
        :value="`+${r.credit_earned} 学分`"
      />
      <div class="load-more" v-if="hasMore">
        <van-button size="small" @click="loadMore" :loading="loadingMore">加载更多</van-button>
      </div>
    </van-cell-group>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import PageShell from '@/components/common/PageShell.vue'
import { creditApi } from '@/api/credit-promotion'

const credits = reactive<{ total: Record<string, any>; by_type: any[] }>({
  total: {},
  by_type: [],
})
const records = ref<any[]>([])
const recordSkip = ref(0)
const hasMore = ref(true)
const loadingMore = ref(false)

async function loadCredits() {
  try {
    const res = await creditApi.getMyCredits()
    credits.total = res.total || {}
    credits.by_type = res.by_type || []
  } catch (e) {
    console.error('加载学分失败', e)
  }
}

async function loadRecords() {
  try {
    const res = await creditApi.getMyRecords({ skip: recordSkip.value, limit: 20 })
    const items = Array.isArray(res) ? res : []
    records.value.push(...items)
    hasMore.value = items.length >= 20
    recordSkip.value += items.length
  } catch (e) {
    console.error('加载记录失败', e)
  }
}

async function loadMore() {
  loadingMore.value = true
  await loadRecords()
  loadingMore.value = false
}

onMounted(() => {
  loadCredits()
  loadRecords()
})
</script>

<style scoped>
.summary-card {
  margin: 12px 16px;
  padding: 20px;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  border-radius: 12px;
  color: #fff;
  text-align: center;
}
.total-credits .number {
  font-size: 42px;
  font-weight: bold;
}
.total-credits .label {
  display: block;
  font-size: 14px;
  opacity: 0.8;
}
.credit-row {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-top: 12px;
}
.credit-item .num {
  font-size: 22px;
  font-weight: bold;
}
.credit-item .lab {
  display: block;
  font-size: 12px;
  opacity: 0.8;
}
.load-more {
  text-align: center;
  padding: 12px;
}
</style>
