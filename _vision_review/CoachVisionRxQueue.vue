<template>
  <!--
    CoachVisionRxQueue.vue — 视力行为处方审核队列
    路由: /admin/coach/vision-rx-queue
    角色: Coach（健康教练）
    核心: risk_level 排序 + 处方预览 + 一键确认推送
  -->
  <div class="coach-vision-rx-queue">

    <div class="queue-header">
      <h2 class="page-title">视力行为处方审核</h2>
      <div class="filter-row">
        <button
          v-for="level in riskFilters"
          :key="level.value"
          class="filter-btn"
          :class="{ active: activeFilter === level.value }"
          @click="activeFilter = level.value"
        >
          <span>{{ level.icon }}</span> {{ level.label }}
          <span class="badge" v-if="countByLevel[level.value]">
            {{ countByLevel[level.value] }}
          </span>
        </button>
      </div>
    </div>

    <!-- 处方列表 -->
    <div class="rx-list">
      <div
        v-for="rx in filteredQueue"
        :key="rx.id"
        class="rx-card"
        :class="`risk-${rx.risk_level.toLowerCase()}`"
      >
        <!-- 卡片头 -->
        <div class="rx-card-header">
          <div class="student-info">
            <span class="student-name">{{ rx.student_name }}</span>
            <span class="student-meta">{{ rx.age }}岁 · {{ rx.school_grade }}</span>
          </div>
          <div class="risk-tag">
            <span>{{ riskIcon(rx.risk_level) }}</span>
            {{ rx.risk_level }}
          </div>
        </div>

        <!-- 触发依据 -->
        <div class="rx-trigger">
          <span class="trigger-label">触发原因：</span>
          <span class="trigger-text">{{ rx.trigger_description }}</span>
        </div>

        <!-- 三格式处方预览（Tab 切换） -->
        <div class="rx-preview">
          <div class="rx-tabs">
            <button
              v-for="fmt in ['student', 'parent', 'coach']"
              :key="fmt"
              class="rx-tab"
              :class="{ active: rx._activeTab === fmt }"
              @click="rx._activeTab = fmt"
            >
              {{ { student: '学生版', parent: '家长版', coach: '教练版' }[fmt] }}
            </button>
          </div>

          <!-- 学生版 -->
          <div v-if="rx._activeTab === 'student'" class="rx-content student-rx">
            <p>🎯 <strong>本周目标：</strong>{{ rx.student_rx.target_this_week }}</p>
            <div class="action-cards">
              <div v-for="card in rx.student_rx.action_cards" :key="card.title" class="action-card">
                {{ card.title }} <span class="pts">+{{ card.points }}</span>
              </div>
            </div>
            <p class="expert-voice">💬 {{ rx.student_rx.expert_voice }}</p>
          </div>

          <!-- 家长版 -->
          <div v-if="rx._activeTab === 'parent'" class="rx-content parent-rx">
            <p>⚠️ <strong>风险说明：</strong>{{ rx.parent_rx.risk_description }}</p>
            <ul class="parent-task-list">
              <li v-for="task in rx.parent_rx.parent_tasks" :key="task">{{ task }}</li>
            </ul>
            <p class="expert-summary-text">👨‍⚕️ {{ rx.parent_rx.expert_summary }}</p>
          </div>

          <!-- 教练版 -->
          <div v-if="rx._activeTab === 'coach'" class="rx-content coach-rx">
            <p><strong>触发数据：</strong>{{ JSON.stringify(rx.coach_rx.trigger_evidence) }}</p>
            <p><strong>智伴推荐：</strong>{{ rx.coach_rx.xzb_recommendation }}</p>
            <div class="coach-actions">
              <p class="coach-action-title">需确认事项：</p>
              <ul>
                <li v-for="action in rx.coach_rx.coach_actions_required" :key="action">
                  {{ action }}
                </li>
              </ul>
            </div>
            <p class="auto-reminder">🔔 {{ rx.coach_rx.auto_reminder }}</p>
          </div>
        </div>

        <!-- 教练备注 -->
        <div class="coach-note-input">
          <textarea
            v-model="rx._coachNote"
            placeholder="添加教练备注（可选，会附加到家长消息中）"
            rows="2"
          />
        </div>

        <!-- 操作按钮 -->
        <div class="rx-actions">
          <button
            class="btn-approve"
            :disabled="rx._submitting"
            @click="approveRx(rx)"
          >
            ✅ 确认推送
          </button>
          <button
            class="btn-edit"
            @click="editRx(rx)"
          >
            ✏️ 修改目标
          </button>
          <button
            class="btn-reject"
            @click="rejectRx(rx)"
          >
            ❌ 暂缓
          </button>
        </div>

        <!-- 状态标记 -->
        <div class="rx-status" v-if="rx._status">
          <span :class="`status-${rx._status}`">{{ statusLabel[rx._status] }}</span>
        </div>
      </div>

      <div class="empty-queue" v-if="filteredQueue.length === 0">
        <p>当前筛选下无待审核处方 🎉</p>
      </div>
    </div>

  </div>
</template>


<script setup>
import { ref, computed, onMounted, reactive } from 'vue'

const riskFilters = [
  { value: 'ALL', label: '全部', icon: '📋' },
  { value: 'URGENT', label: '紧急', icon: '🔴' },
  { value: 'ALERT', label: '警示期', icon: '🟠' },
  { value: 'WATCH', label: '观察期', icon: '🟡' },
]

const activeFilter = ref('ALL')
const rxQueue = ref([])

const filteredQueue = computed(() => {
  if (activeFilter.value === 'ALL') return rxQueue.value
  return rxQueue.value.filter(rx => rx.risk_level === activeFilter.value)
})

const countByLevel = computed(() => {
  const counts = { URGENT: 0, ALERT: 0, WATCH: 0, NORMAL: 0 }
  rxQueue.value.forEach(rx => { counts[rx.risk_level] = (counts[rx.risk_level] || 0) + 1 })
  return counts
})

function riskIcon(level) {
  return { NORMAL: '🟢', WATCH: '🟡', ALERT: '🟠', URGENT: '🔴' }[level] || '⚪'
}

const statusLabel = {
  approved: '✅ 已推送',
  rejected: '⏸ 已暂缓',
  editing: '✏️ 编辑中',
}

async function approveRx(rx) {
  rx._submitting = true
  try {
    // await axios.post(`/v1/vision/rx/${rx.id}/approve`, {
    //   coach_note: rx._coachNote,
    // })
    rx._status = 'approved'
    // 从列表中延迟移除
    setTimeout(() => {
      rxQueue.value = rxQueue.value.filter(r => r.id !== rx.id)
    }, 2000)
  } finally {
    rx._submitting = false
  }
}

function editRx(rx) {
  // 跳转到目标调整页
  // router.push(`/admin/vision/goals/${rx.student_id}`)
  rx._status = 'editing'
}

async function rejectRx(rx) {
  // await axios.post(`/v1/vision/rx/${rx.id}/reject`)
  rx._status = 'rejected'
  setTimeout(() => {
    rxQueue.value = rxQueue.value.filter(r => r.id !== rx.id)
  }, 2000)
}

onMounted(async () => {
  // const res = await axios.get('/v1/vision/rx/coach-queue')
  // rxQueue.value = res.data.map(rx => ({ ...rx, _activeTab: 'coach', _coachNote: '', _submitting: false, _status: null }))

  // Mock 数据
  rxQueue.value = [
    {
      id: 'rx-001',
      student_id: 'u-001',
      student_name: '王小明',
      age: 11,
      school_grade: '小学五年级',
      risk_level: 'ALERT',
      trigger_description: '右眼近3个月增加0.75D，连续7天户外时间<60分钟',
      student_rx: {
        target_this_week: '每天出门两次，合计超过120分钟',
        action_cards: [
          { title: '午饭后出门 15 分钟', points: 10 },
          { title: '完成今日眼保健操', points: 5 },
        ],
        expert_voice: '李主任说：你现在需要认真对待了，我相信你可以做到！',
      },
      parent_rx: {
        risk_description: '孩子当前处于警示期，过去3个月度数增加0.75D',
        parent_tasks: [
          '本周调整晚饭后安排，陪孩子户外活动至少30分钟',
          '将作业台灯照度调整至500lux以上',
        ],
        expert_summary: '如下次检查度数再增>0.5D，需讨论角膜塑形镜选项',
      },
      coach_rx: {
        trigger_evidence: { exam_id: 'v-3892', right_eye: -3.25, prev: -2.50 },
        xzb_recommendation: '基于11岁+进展速率，建议执行户外强化方案',
        coach_actions_required: [
          '与家长沟通干预选项（包括0.01%阿托品转介可能性）',
          '屏幕限制从150分钟/天降至90分钟/天',
          '30天后安排随访',
        ],
        auto_reminder: '若30天内未收到新检查记录，自动触发 Job 28 重新评估',
      },
      _activeTab: 'coach',
      _coachNote: '',
      _submitting: false,
      _status: null,
    },
    {
      id: 'rx-002',
      student_id: 'u-002',
      student_name: '李晓雨',
      age: 14,
      school_grade: '初中二年级',
      risk_level: 'WATCH',
      trigger_description: '叶黄素连续5天<目标50%，屏幕时间连续3天>目标150%',
      student_rx: {
        target_this_week: '每天吃够护眼食物，屏幕时间控制在90分钟内',
        action_cards: [
          { title: '今天摄入叶黄素≥10mg', points: 10 },
          { title: '娱乐屏幕控制在30分钟内', points: 15 },
        ],
        expert_voice: '医生说：你的状态还好，注意这两个点就行。',
      },
      parent_rx: {
        risk_description: '孩子处于观察期，用眼习惯需要调整',
        parent_tasks: [
          '检查冰箱中是否有富含叶黄素的食物（菠菜、玉米、蛋黄）',
          '与孩子协商晚上娱乐屏幕时间上限',
        ],
        expert_summary: '本次处方重点：营养补充+屏幕管理，暂无需就医',
      },
      coach_rx: {
        trigger_evidence: { trigger: 'behavior_gap_job28', lutein_days: 5, screen_days: 3 },
        xzb_recommendation: '营养+屏幕双向干预，优先级WATCH',
        coach_actions_required: [
          '确认家长了解叶黄素食物来源',
          '与学员沟通屏幕使用协议',
        ],
        auto_reminder: '7天后 Job 28 自动复查，若未改善升级为 ALERT 处方',
      },
      _activeTab: 'coach',
      _coachNote: '',
      _submitting: false,
      _status: null,
    },
  ]
})
</script>


<style scoped>
.coach-vision-rx-queue {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 16px;
  color: #1a1a2e;
}

.filter-row {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  background: white;
  font-size: 13px;
  cursor: pointer;
  transition: all .2s;
}

.filter-btn.active {
  background: #1a1a2e;
  color: white;
  border-color: #1a1a2e;
}

.badge {
  background: #ef4444;
  color: white;
  border-radius: 10px;
  padding: 1px 6px;
  font-size: 11px;
  font-weight: 700;
}

/* 处方卡片 */
.rx-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
  border-left: 4px solid #e5e7eb;
}

.rx-card.risk-urgent { border-left-color: #ef4444; }
.rx-card.risk-alert  { border-left-color: #f97316; }
.rx-card.risk-watch  { border-left-color: #eab308; }
.rx-card.risk-normal { border-left-color: #22c55e; }

.rx-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.student-name { font-size: 16px; font-weight: 700; display: block; }
.student-meta { font-size: 12px; color: #888; }

.risk-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  background: #f3f4f6;
}

.rx-trigger {
  font-size: 13px;
  color: #555;
  background: #fef9c3;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 12px;
}

.trigger-label { font-weight: 600; }

/* Tab */
.rx-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e5e7eb;
  margin-bottom: 12px;
}

.rx-tab {
  padding: 8px 16px;
  border: none;
  background: none;
  font-size: 14px;
  color: #888;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.rx-tab.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
  font-weight: 600;
}

.rx-content { font-size: 14px; line-height: 1.7; color: #333; }

.action-cards { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }

.action-card {
  background: #eff6ff;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 13px;
  color: #1d4ed8;
  display: flex;
  align-items: center;
  gap: 6px;
}

.pts {
  background: #3b82f6;
  color: white;
  border-radius: 10px;
  padding: 1px 6px;
  font-size: 11px;
}

.expert-voice {
  color: #6d28d9;
  font-style: italic;
  font-size: 13px;
  margin: 8px 0 0;
}

.parent-task-list { padding-left: 16px; margin: 8px 0; }
.parent-task-list li { margin-bottom: 4px; }

.expert-summary-text { color: #0369a1; font-size: 13px; }

.coach-actions { background: #f8faff; border-radius: 8px; padding: 10px 12px; margin: 8px 0; }
.coach-action-title { font-weight: 600; margin: 0 0 6px; font-size: 13px; }
.coach-actions ul { padding-left: 16px; margin: 0; }
.coach-actions li { margin-bottom: 4px; font-size: 13px; }

.auto-reminder { color: #9333ea; font-size: 12px; margin: 8px 0 0; }

/* 教练备注 */
.coach-note-input { margin: 12px 0; }

.coach-note-input textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  resize: none;
  outline: none;
  box-sizing: border-box;
}

.coach-note-input textarea:focus { border-color: #3b82f6; }

/* 操作按钮 */
.rx-actions { display: flex; gap: 10px; margin-top: 12px; }

.btn-approve, .btn-edit, .btn-reject {
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity .2s;
}

.btn-approve {
  background: #22c55e;
  color: white;
  flex: 1;
}

.btn-edit {
  background: #f3f4f6;
  color: #374151;
}

.btn-reject {
  background: #fef2f2;
  color: #dc2626;
}

.btn-approve:disabled { opacity: .5; cursor: not-allowed; }

/* 状态 */
.rx-status { text-align: center; margin-top: 8px; font-size: 14px; font-weight: 600; }
.status-approved { color: #16a34a; }
.status-rejected  { color: #dc2626; }
.status-editing   { color: #d97706; }

.empty-queue { text-align: center; padding: 40px; color: #aaa; }
</style>
