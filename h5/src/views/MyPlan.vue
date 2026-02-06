<template>
  <div class="page-container">
    <van-nav-bar title="我的管理方案" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <!-- 方案列表 (无 assignment_id 时) -->
      <template v-if="!currentId">
        <van-loading v-if="loadingList" class="loading" />
        <template v-else-if="planList.length">
          <div
            v-for="plan in planList"
            :key="plan.id"
            class="plan-list-item card"
            @click="loadPlanDetail(plan.id)"
          >
            <div class="plan-list-header">
              <van-icon name="notes-o" size="24" color="#1989fa" />
              <div class="plan-list-info">
                <div class="plan-list-title">{{ plan.coach_name }} 的管理方案</div>
                <div class="plan-list-time">{{ formatTime(plan.pushed_at) }}</div>
              </div>
              <van-icon name="arrow" color="#c8c9cc" />
            </div>
            <div class="plan-list-scales">
              <van-tag v-for="s in plan.scales" :key="s" size="small" type="primary" style="margin-right:4px">
                {{ s.toUpperCase() }}
              </van-tag>
            </div>
          </div>
        </template>
        <van-empty v-else description="暂无管理方案" />
      </template>

      <!-- 方案详情 -->
      <template v-if="currentId">
        <van-loading v-if="loadingDetail" class="loading" />
        <template v-else-if="detail">
          <!-- 头部 -->
          <div class="card plan-header">
            <div class="plan-coach">教练: {{ detail.coach_name }}</div>
            <div class="plan-time">推送于 {{ formatTime(detail.pushed_at) }}</div>
            <div v-if="detail.stage_decision" class="plan-stage">
              当前阶段: {{ detail.stage_decision.to_stage }}
              <van-tag v-if="detail.stage_decision.is_transition" type="success" size="small" style="margin-left:4px">阶段跃迁</van-tag>
            </div>
          </div>

          <!-- Tab 切换 -->
          <van-tabs v-model:active="activeTab" animated>
            <van-tab title="管理目标">
              <template v-if="detail.goals?.length">
                <div v-for="item in detail.goals" :key="item.id" class="plan-item card">
                  <div class="plan-item-header">
                    <van-icon name="aim" size="20" color="#1890ff" />
                    <span class="plan-item-domain">{{ item.content?.domain_name || item.domain }}</span>
                    <van-tag v-if="item.is_modified" type="primary" size="small">教练修改</van-tag>
                  </div>
                  <div class="plan-item-body">
                    <div class="plan-item-goal">{{ item.content?.core_goal || item.content?.modified_text }}</div>
                    <div v-if="item.content?.strategy" class="plan-item-strategy">
                      策略: {{ item.content.strategy }}
                    </div>
                  </div>
                  <div v-if="item.coach_note" class="plan-item-note">
                    <van-icon name="chat-o" size="14" /> {{ item.coach_note }}
                  </div>
                </div>
              </template>
              <van-empty v-else description="暂无管理目标" />
            </van-tab>

            <van-tab title="行为处方">
              <template v-if="detail.prescriptions?.length">
                <div v-for="item in detail.prescriptions" :key="item.id" class="plan-item card">
                  <div class="plan-item-header">
                    <van-icon name="medel" size="20" color="#52c41a" />
                    <span class="plan-item-domain">{{ item.content?.domain_name || item.domain }}</span>
                    <van-tag v-if="item.is_modified" type="primary" size="small">教练修改</van-tag>
                  </div>
                  <div class="plan-item-body">
                    <template v-if="item.content?.modified_text">
                      <div>{{ item.content.modified_text }}</div>
                    </template>
                    <template v-else>
                      <div v-if="item.content?.recommended_behaviors?.length" class="rx-section">
                        <div class="rx-label rx-good">推荐行为</div>
                        <div v-for="(b, i) in item.content.recommended_behaviors" :key="'r'+i" class="rx-behavior">
                          <van-icon name="success" size="14" color="#52c41a" />
                          {{ typeof b === 'string' ? b : b.name || b.title || JSON.stringify(b) }}
                        </div>
                      </div>
                      <div v-if="item.content?.contraindicated_behaviors?.length" class="rx-section" style="margin-top:8px">
                        <div class="rx-label rx-bad">禁忌行为</div>
                        <div v-for="(b, i) in item.content.contraindicated_behaviors" :key="'c'+i" class="rx-behavior">
                          <van-icon name="cross" size="14" color="#ff4d4f" />
                          {{ typeof b === 'string' ? b : b.name || b.title || JSON.stringify(b) }}
                        </div>
                      </div>
                    </template>
                  </div>
                  <div v-if="item.coach_note" class="plan-item-note">
                    <van-icon name="chat-o" size="14" /> {{ item.coach_note }}
                  </div>
                </div>
              </template>
              <van-empty v-else description="暂无行为处方" />
            </van-tab>

            <van-tab title="指导建议">
              <template v-if="detail.suggestions?.length">
                <div v-for="item in detail.suggestions" :key="item.id" class="plan-item card">
                  <div class="plan-item-header">
                    <van-icon name="bulb-o" size="20" color="#faad14" />
                    <span class="plan-item-domain">{{ item.content?.domain_name || item.domain }}</span>
                    <van-tag v-if="item.is_modified" type="primary" size="small">教练修改</van-tag>
                  </div>
                  <div class="plan-item-body">
                    <template v-if="item.content?.modified_text">
                      <div>{{ item.content.modified_text }}</div>
                    </template>
                    <template v-else-if="item.content?.advice?.length">
                      <div v-for="(adv, i) in item.content.advice" :key="i" class="advice-item">
                        <span class="advice-num">{{ i + 1 }}</span>
                        {{ typeof adv === 'string' ? adv : adv.title || adv.content || JSON.stringify(adv) }}
                      </div>
                    </template>
                  </div>
                  <div v-if="item.coach_note" class="plan-item-note">
                    <van-icon name="chat-o" size="14" /> {{ item.coach_note }}
                  </div>
                </div>
              </template>
              <van-empty v-else description="暂无指导建议" />
            </van-tab>
          </van-tabs>

          <!-- 返回按钮 -->
          <div class="plan-actions" v-if="!routeAssignmentId">
            <van-button plain block round @click="currentId = null; detail = null">
              返回方案列表
            </van-button>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/index'

const route = useRoute()
const routeAssignmentId = ref<number | null>(null)
const currentId = ref<number | null>(null)
const activeTab = ref(0)

const loadingList = ref(false)
const loadingDetail = ref(false)
const planList = ref<any[]>([])
const detail = ref<any>(null)

function formatTime(str: string) {
  if (!str) return ''
  const d = new Date(str)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour}小时前`
  return str.replace('T', ' ').slice(0, 16)
}

async function loadPlanList() {
  loadingList.value = true
  try {
    const res: any = await api.get('/api/v1/assessment-assignments/pushed-list')
    planList.value = res.assignments || []
  } catch {
    planList.value = []
  } finally {
    loadingList.value = false
  }
}

async function loadPlanDetail(id: number) {
  currentId.value = id
  loadingDetail.value = true
  try {
    const res: any = await api.get(`/api/v1/assessment-assignments/${id}/result`)
    detail.value = res
  } catch {
    detail.value = null
  } finally {
    loadingDetail.value = false
  }
}

onMounted(() => {
  const aid = route.query.assignment_id || route.query.id
  if (aid) {
    routeAssignmentId.value = Number(aid)
    loadPlanDetail(Number(aid))
  } else {
    loadPlanList()
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading { text-align: center; padding: 60px 0; }

.plan-list-item {
  padding: $spacing-md;
  margin-bottom: $spacing-sm;
  cursor: pointer;

  &:active { background: #f7f7f7; }

  .plan-list-header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }

  .plan-list-info {
    flex: 1;

    .plan-list-title { font-size: $font-size-md; font-weight: 500; }
    .plan-list-time { font-size: $font-size-xs; color: $text-color-placeholder; margin-top: 2px; }
  }

  .plan-list-scales {
    margin-top: 8px;
    padding-left: 32px;
  }
}

.plan-header {
  padding: $spacing-md;
  margin-bottom: $spacing-sm;

  .plan-coach { font-size: $font-size-md; font-weight: 600; }
  .plan-time { font-size: $font-size-xs; color: $text-color-placeholder; margin-top: 2px; }
  .plan-stage { font-size: $font-size-sm; color: #1890ff; margin-top: 6px; }
}

.plan-item {
  padding: $spacing-md;
  margin-bottom: $spacing-sm;

  .plan-item-header {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: 8px;

    .plan-item-domain { font-weight: 600; font-size: $font-size-md; }
  }

  .plan-item-body {
    font-size: $font-size-sm;
    color: $text-color;
    line-height: 1.6;

    .plan-item-goal {
      font-size: 15px;
      font-weight: 500;
      color: #1a1a1a;
    }

    .plan-item-strategy {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-top: 4px;
    }
  }

  .plan-item-note {
    margin-top: 8px;
    padding: 8px 12px;
    background: #fffbe6;
    border-radius: 6px;
    font-size: $font-size-xs;
    color: #8c6600;
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.rx-section {
  .rx-label {
    font-size: $font-size-xs;
    font-weight: 600;
    margin-bottom: 4px;

    &.rx-good { color: #52c41a; }
    &.rx-bad { color: #ff4d4f; }
  }

  .rx-behavior {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: $font-size-sm;
    padding: 2px 0;
  }
}

.advice-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  font-size: $font-size-sm;

  .advice-num {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #1989fa;
    color: #fff;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
}

.plan-actions {
  margin-top: $spacing-lg;
  padding: 0 $spacing-md;
}
</style>
