<template>
  <div>
    <van-nav-bar title="评估中心" left-arrow @click-left="$router.back()" />

    <!-- 推荐下一个 -->
    <van-notice-bar v-if="recommended" left-icon="bullhorn-o" @click="$router.push(`/assessment/${recommended.batch_id}`)">
      推荐: {{ recommended.name }} ({{ recommended.estimated_minutes }}分钟)
    </van-notice-bar>

    <!-- 进度 -->
    <div style="padding: 16px;">
      <van-progress :percentage="progressPct" stroke-width="8" />
      <div style="text-align:center; font-size:13px; color:#999; margin-top:6px;">
        已完成 {{ completedCount }} / {{ batches.length }} 个评估批次
      </div>
    </div>

    <!-- 批次列表 -->
    <van-cell-group inset>
      <van-cell v-for="b in batches" :key="b.batch_id" :title="b.name"
        :label="`${b.question_count}题 · 约${b.estimated_minutes}分钟`"
        is-link @click="$router.push(`/assessment/${b.batch_id}`)">
        <template #right-icon>
          <van-tag :type="isCompleted(b.batch_id) ? 'success' : 'default'" size="medium">
            {{ isCompleted(b.batch_id) ? '已完成' : '待完成' }}
          </van-tag>
        </template>
      </van-cell>
    </van-cell-group>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
// v3 store stub
const useUserStore = () => ({ userId: 0, token: localStorage.getItem('access_token') })
// v3 API stub - TODO: wire up
const assessmentApi = { getBatches: async () => ({ data: { data: [] } }), getSession: async () => ({ data: { data: {} } }), recommend: async () => ({ data: { data: null } }) }

const store = useUserStore()
const batches = ref([])
const completedIds = ref([])
const recommended = ref(null)

const completedCount = computed(() => completedIds.value.length)
const progressPct = computed(() => batches.value.length ? Math.round(completedCount.value / batches.value.length * 100) : 0)
const isCompleted = (id) => completedIds.value.includes(id)

onMounted(async () => {
  const [bRes, sRes, rRes] = await Promise.all([
    assessmentApi.batches(),
    assessmentApi.session(store.userId),
    assessmentApi.recommend(store.userId),
  ])
  if (bRes.ok) batches.value = bRes.data
  if (sRes.ok) completedIds.value = sRes.data.completed_batches || []
  if (rRes.ok) recommended.value = rRes.data
})
</script>
