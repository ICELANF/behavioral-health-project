<template>
  <div v-if="loading" style="text-align: center; padding: 60px">
    <a-spin size="large" tip="加载案例数据..." />
  </div>
  <a-empty v-else-if="!auditCase" description="未找到案例数据，请从审核队列进入" />
  <DualSignPanel v-else :audit-case="auditCase" />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import DualSignPanel from './DualSignPanel.vue'
import request from '@/api/request'

const route = useRoute()
const loading = ref(true)
const auditCase = ref<any>(null)

onMounted(async () => {
  const caseId = route.params.id || route.query.caseId
  if (!caseId) {
    loading.value = false
    return
  }
  try {
    const res = await request.get(`/v1/expert/audit/${caseId}`)
    auditCase.value = res.data?.data || res.data
  } catch (e) {
    console.error('加载案例失败:', e)
  } finally {
    loading.value = false
  }
})
</script>
