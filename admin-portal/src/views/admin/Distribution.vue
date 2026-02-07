<template>
  <div class="distribution">
    <div class="page-header">
      <h2>分配管理</h2>
      <a-button type="primary" @click="showAutoRuleModal = true">自动分配规则</a-button>
    </div>

    <!-- Stats -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6"><a-card size="small"><a-statistic title="待分配患者" :value="pendingPatients.length" value-style="color: #d46b08" :loading="loadingPending" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="已分配总数" :value="assignedCount" :loading="loadingStats" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="教练平均负载" :value="avgLoad" :precision="1" :loading="loadingStats" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="待审批转移" :value="transferRequests.length" value-style="color: #cf1322" :loading="loadingTransfers" /></a-card></a-col>
    </a-row>

    <a-row :gutter="16">
      <!-- Pending patients queue -->
      <a-col :span="10">
        <a-card title="待分配患者队列" :loading="loadingPending">
          <div v-for="patient in pendingPatients" :key="patient.id" class="patient-item">
            <div class="patient-info">
              <a-avatar :size="28">{{ patient.name[0] }}</a-avatar>
              <div>
                <div class="patient-name">{{ patient.name }}</div>
                <div class="patient-meta">
                  <a-tag size="small" :color="patient.risk === '高' ? 'red' : patient.risk === '中' ? 'orange' : 'green'">{{ patient.risk }}风险</a-tag>
                  <span>{{ patient.domain }}</span>
                </div>
              </div>
            </div>
            <div class="patient-actions">
              <a-select v-model:value="patient.assignedCoach" placeholder="选择教练" size="small" style="width: 120px">
                <a-select-option v-for="c in availableCoaches" :key="c.id" :value="c.id">
                  {{ c.name }} ({{ c.currentLoad }}/{{ c.maxLoad }})
                </a-select-option>
              </a-select>
              <a-button size="small" type="primary" :disabled="!patient.assignedCoach" :loading="assigningId === patient.id" @click="assignPatient(patient)">分配</a-button>
            </div>
          </div>
          <a-empty v-if="pendingPatients.length === 0" description="暂无待分配患者" />
        </a-card>
      </a-col>

      <!-- Coach capacity -->
      <a-col :span="14">
        <a-card title="教练容量看板" :loading="loadingCoaches">
          <div v-for="coach in availableCoaches" :key="coach.id" class="coach-capacity-item">
            <div class="coach-info">
              <a-avatar :size="28" :style="{ background: coach.color }">{{ coach.name[0] }}</a-avatar>
              <div>
                <span class="coach-name">{{ coach.name }}</span>
                <span class="coach-level">{{ coach.level }}</span>
              </div>
            </div>
            <div class="capacity-bar-wrapper">
              <a-progress :percent="(coach.currentLoad / coach.maxLoad) * 100" :stroke-color="coach.currentLoad >= coach.maxLoad * 0.9 ? '#ff4d4f' : coach.currentLoad >= coach.maxLoad * 0.7 ? '#faad14' : '#52c41a'" :show-info="false" size="small" />
              <span class="capacity-text">{{ coach.currentLoad }} / {{ coach.maxLoad }}</span>
            </div>
            <div class="coach-domains">
              <a-tag v-for="d in coach.domains" :key="d" size="small">{{ d }}</a-tag>
            </div>
          </div>
          <a-empty v-if="availableCoaches.length === 0" description="暂无教练" />
        </a-card>
      </a-col>
    </a-row>

    <!-- Transfer Approval -->
    <a-card title="转移审批" style="margin-top: 16px" v-if="transferRequests.length > 0" :loading="loadingTransfers">
      <div v-for="req in transferRequests" :key="req.id" class="transfer-item">
        <div class="transfer-info">
          <span class="transfer-patient">{{ req.patientName }}</span>
          <span class="transfer-arrow">{{ req.fromCoach }} → {{ req.toCoach }}</span>
          <span class="transfer-reason">原因: {{ req.reason }}</span>
        </div>
        <div class="transfer-actions">
          <a-button size="small" type="primary" @click="approveTransfer(req)">批准</a-button>
          <a-button size="small" danger @click="rejectTransfer(req)">拒绝</a-button>
        </div>
      </div>
    </a-card>

    <!-- Auto Rule Modal -->
    <a-modal v-model:open="showAutoRuleModal" title="自动分配规则" @ok="saveRules" okText="保存">
      <a-form layout="vertical">
        <a-form-item label="分配策略">
          <a-radio-group v-model:value="autoRules.strategy">
            <a-radio value="load_balance">负载均衡（优先分配给低负载教练）</a-radio>
            <a-radio value="domain_match">领域匹配（优先匹配专长领域）</a-radio>
            <a-radio value="risk_match">风险匹配（高风险分配给教练）</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="教练最大负载">
          <a-input-number v-model:value="autoRules.maxLoad" :min="1" :max="50" />
        </a-form-item>
        <a-form-item label="自动分配">
          <a-switch v-model:checked="autoRules.enabled" />
          <span style="margin-left: 8px; color: #999">{{ autoRules.enabled ? '已开启' : '已关闭' }}</span>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const showAutoRuleModal = ref(false)
const autoRules = reactive({ strategy: 'load_balance', maxLoad: 20, enabled: false })

const loadingPending = ref(false)
const loadingCoaches = ref(false)
const loadingTransfers = ref(false)
const loadingStats = ref(false)
const assigningId = ref<number | null>(null)

const pendingPatients = ref<any[]>([])
const availableCoaches = ref<any[]>([])
const transferRequests = ref<any[]>([])

const assignedCount = computed(() => {
  return availableCoaches.value.reduce((sum, c) => sum + (c.currentLoad || 0), 0)
})

const avgLoad = computed(() => {
  if (availableCoaches.value.length === 0) return 0
  return assignedCount.value / availableCoaches.value.length
})

// === API 调用 ===

const loadPendingPatients = async () => {
  loadingPending.value = true
  try {
    const { data } = await request.get('/v1/admin/distribution/pending')
    pendingPatients.value = data.pending || []
  } catch (e: any) {
    console.error('加载待分配列表失败:', e)
    // Fallback mock
    if (!pendingPatients.value.length) {
      pendingPatients.value = [
        { id: 1, name: '钱一', risk: '高', domain: '糖尿病', assignedCoach: undefined },
        { id: 2, name: '孙二', risk: '中', domain: '高血压', assignedCoach: undefined },
      ]
    }
  } finally {
    loadingPending.value = false
  }
}

const loadCoaches = async () => {
  loadingCoaches.value = true
  try {
    const { data } = await request.get('/v1/admin/coaches')
    availableCoaches.value = data.coaches || []
  } catch (e: any) {
    console.error('加载教练列表失败:', e)
    if (!availableCoaches.value.length) {
      availableCoaches.value = [
        { id: 1, name: '王教练', level: 'L3 高级', color: '#722ed1', currentLoad: 12, maxLoad: 20, domains: ['糖尿病', '高血压'] },
        { id: 2, name: '李教练', level: 'L2 中级', color: '#1890ff', currentLoad: 8, maxLoad: 15, domains: ['压力管理'] },
      ]
    }
  } finally {
    loadingCoaches.value = false
  }
}

const loadTransfers = async () => {
  loadingTransfers.value = true
  try {
    const { data } = await request.get('/v1/admin/distribution/transfers')
    transferRequests.value = data.transfers || []
  } catch (e: any) {
    console.error('加载转移请求失败:', e)
  } finally {
    loadingTransfers.value = false
  }
}

const assignPatient = async (patient: any) => {
  if (!patient.assignedCoach) return
  assigningId.value = patient.id
  try {
    await request.post('/v1/admin/distribution/assign', {
      grower_id: patient.id,
      coach_id: patient.assignedCoach,
    })
    const coach = availableCoaches.value.find(c => c.id === patient.assignedCoach)
    if (coach) coach.currentLoad++
    pendingPatients.value = pendingPatients.value.filter(p => p.id !== patient.id)
    message.success(`${patient.name} 已分配给 ${coach?.name || '教练'}`)
  } catch (e: any) {
    message.error(e.response?.data?.detail || '分配失败')
  } finally {
    assigningId.value = null
  }
}

const approveTransfer = async (req: any) => {
  try {
    await request.post(`/v1/admin/distribution/transfers/${req.id}/approve`)
    transferRequests.value = transferRequests.value.filter(r => r.id !== req.id)
    message.success('转移已批准')
    await loadCoaches()
  } catch (e: any) {
    message.error('操作失败')
  }
}

const rejectTransfer = async (req: any) => {
  try {
    await request.post(`/v1/admin/distribution/transfers/${req.id}/reject`)
    transferRequests.value = transferRequests.value.filter(r => r.id !== req.id)
    message.info('转移已拒绝')
  } catch (e: any) {
    message.error('操作失败')
  }
}

const saveRules = () => {
  showAutoRuleModal.value = false
  message.success('规则已保存')
}

onMounted(() => {
  loadPendingPatients()
  loadCoaches()
  loadTransfers()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.patient-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f5f5f5; gap: 8px; }
.patient-info { display: flex; align-items: center; gap: 8px; }
.patient-name { font-weight: 500; font-size: 13px; }
.patient-meta { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #999; }
.patient-actions { display: flex; gap: 4px; align-items: center; }

.coach-capacity-item { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f5f5f5; }
.coach-info { display: flex; align-items: center; gap: 8px; min-width: 120px; }
.coach-name { display: block; font-weight: 500; font-size: 13px; }
.coach-level { font-size: 11px; color: #999; }
.capacity-bar-wrapper { flex: 1; display: flex; align-items: center; gap: 8px; }
.capacity-text { font-size: 12px; color: #666; min-width: 50px; }
.coach-domains { display: flex; gap: 4px; }

.transfer-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f5f5f5; }
.transfer-info { display: flex; flex-direction: column; gap: 2px; }
.transfer-patient { font-weight: 500; }
.transfer-arrow { font-size: 12px; color: #1890ff; }
.transfer-reason { font-size: 12px; color: #999; }
.transfer-actions { display: flex; gap: 4px; }
</style>
