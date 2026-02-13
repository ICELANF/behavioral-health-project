<!--
  专家入驻申请状态页
  路由: /expert-application-status
-->
<template>
  <div class="application-status">
    <van-nav-bar title="申请状态" left-arrow @click-left="$router.push('/')" />

    <van-loading v-if="loading" class="loading-center" vertical>加载中...</van-loading>

    <div v-else-if="!application" class="empty-state">
      <van-empty description="暂无入驻申请">
        <van-button type="primary" round size="small" @click="$router.push('/expert-register')">
          申请入驻
        </van-button>
      </van-empty>
    </div>

    <div v-else class="status-page">
      <!-- 品牌卡片 -->
      <div class="brand-card" :style="{ background: application.brand_colors?.bg || '#F0F7FF' }">
        <div class="brand-avatar" :style="{ background: application.brand_colors?.primary || '#1E40AF' }">
          {{ application.brand_avatar || '🏥' }}
        </div>
        <div class="brand-name">{{ application.brand_name }}</div>
        <div class="brand-title">{{ application.expert_title }}</div>
      </div>

      <!-- 状态显示 -->
      <div class="status-section">
        <div class="status-badge" :class="statusClass">
          {{ statusText }}
        </div>
        <div class="status-time" v-if="application.applied_at">
          提交时间: {{ formatTime(application.applied_at) }}
        </div>
      </div>

      <!-- 进度条 -->
      <van-cell-group inset title="申请进度" style="margin-top: 16px">
        <van-step direction="vertical" :active="progressStep" active-color="#1E40AF">
          <van-steps direction="vertical" :active="progressStep" active-color="#1E40AF">
            <van-step>提交申请</van-step>
            <van-step>平台审核中 (1-3 个工作日)</van-step>
            <van-step>{{ application.application_status === 'rejected' ? '需要补充材料' : '审核通过' }}</van-step>
            <van-step>开通工作室</van-step>
          </van-steps>
        </van-step>
      </van-cell-group>

      <!-- 拒绝原因 -->
      <div v-if="application.application_status === 'rejected'" class="reject-reason">
        <van-cell-group inset>
          <van-cell title="拒绝原因" :label="rejectReason" />
        </van-cell-group>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <van-button
          v-if="application.application_status === 'pending_review'"
          block round plain type="primary"
          @click="$router.push('/expert-register')"
        >
          修改申请材料
        </van-button>
        <van-button
          v-if="application.application_status === 'rejected'"
          block round type="primary"
          @click="$router.push('/expert-register')"
        >
          重新申请
        </van-button>
        <van-button
          v-if="application.application_status === 'approved'"
          block round type="primary"
          @click="goToManage"
        >
          进入管理后台
        </van-button>
        <van-button block round plain @click="$router.push('/')">
          返回首页
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()
const loading = ref(true)
const application = ref<any>(null)

const statusClass = computed(() => {
  const s = application.value?.application_status
  if (s === 'pending_review') return 'status-pending'
  if (s === 'approved') return 'status-approved'
  if (s === 'rejected') return 'status-rejected'
  return 'status-pending'
})

const statusText = computed(() => {
  const s = application.value?.application_status
  if (s === 'pending_review') return '待审核中'
  if (s === 'approved') return '审核通过'
  if (s === 'rejected') return '审核未通过'
  return s || '未知'
})

const progressStep = computed(() => {
  const s = application.value?.application_status
  if (s === 'pending_review') return 1
  if (s === 'approved') return 3
  if (s === 'rejected') return 2
  return 0
})

const rejectReason = computed(() => {
  return application.value?.application_data?.reject_reason || '暂无详细原因'
})

function formatTime(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function goToManage() {
  // 跳转到管理后台
  const tid = application.value?.tenant_id
  if (tid) {
    window.location.href = `/expert/dashboard/${tid}`
  }
}

async function fetchStatus() {
  loading.value = true
  try {
    const res = await request.get('/v1/expert-registration/my-application')
    application.value = res.data?.data || null
  } catch {
    application.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStatus()
})
</script>

<style scoped>
.application-status {
  min-height: 100vh;
  background: #f7f8fa;
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}
.empty-state {
  padding: 40px 0;
}
.status-page {
  padding: 16px;
}
.brand-card {
  border-radius: 16px;
  padding: 24px;
  text-align: center;
}
.brand-avatar {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  margin: 0 auto 12px;
}
.brand-name {
  font-size: 18px;
  font-weight: 600;
  color: #323233;
}
.brand-title {
  font-size: 13px;
  color: #646566;
  margin-top: 4px;
}
.status-section {
  text-align: center;
  padding: 16px 0;
}
.status-badge {
  display: inline-block;
  padding: 6px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}
.status-pending {
  background: #FFF7E6;
  color: #D48806;
}
.status-approved {
  background: #F6FFED;
  color: #389E0D;
}
.status-rejected {
  background: #FFF1F0;
  color: #CF1322;
}
.status-time {
  font-size: 12px;
  color: #969799;
  margin-top: 8px;
}
.reject-reason {
  margin-top: 16px;
}
.action-buttons {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
