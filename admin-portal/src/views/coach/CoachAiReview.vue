<template>
  <div class="coach-ai-review-page">
    <div class="page-header">
      <a-button type="text" @click="$router.push('/coach-portal')">
        <LeftOutlined /> 返回工作台
      </a-button>
      <h2>AI 干预建议审核</h2>
      <a-tag color="orange">{{ recommendations.filter(r => r.status === 'pending').length }} 条待审核</a-tag>
    </div>

    <div v-if="loading" style="text-align:center;padding:60px 0">
      <a-spin size="large" tip="加载审核列表..." />
    </div>

    <div v-else class="review-list">
      <div
        v-for="rec in recommendations"
        :key="rec.id"
        class="recommendation-card"
        :class="{ 'rec-approved': rec.status === 'approved', 'rec-rejected': rec.status === 'rejected', 'rec-modified': rec.status === 'modified' }"
      >
        <div class="rec-header">
          <span class="rec-type" :class="rec.type">{{ rec.typeLabel }}</span>
          <span class="rec-student">{{ rec.studentName }}</span>
          <span v-if="rec.status !== 'pending'" class="rec-status" :class="'status-' + rec.status">
            {{ { approved: '已批准', rejected: '已驳回', modified: '已修正' }[rec.status] }}
          </span>
        </div>
        <div class="rec-content">
          <div class="rec-ai-label">AI 建议：</div>
          {{ rec.suggestion }}
        </div>

        <!-- 修正输入框 -->
        <div v-if="rec.showModify" class="rec-modify-area">
          <a-textarea
            v-model:value="rec.modifiedText"
            placeholder="输入修正后的建议内容..."
            :rows="3"
          />
          <div class="modify-actions">
            <a-button size="small" type="primary" @click="confirmModify(rec)">确认修正并推送</a-button>
            <a-button size="small" @click="rec.showModify = false">取消</a-button>
          </div>
        </div>

        <!-- 审核操作按钮 -->
        <div v-if="rec.status === 'pending'" class="rec-actions">
          <a-button size="small" type="primary" style="background:#52c41a;border-color:#52c41a" @click="approveRec(rec)">
            批准推送
          </a-button>
          <a-button size="small" @click="rec.showModify = true">
            修正后推送
          </a-button>
          <a-button size="small" danger @click="rejectRec(rec)">
            驳回
          </a-button>
        </div>

        <!-- 已处理状态 -->
        <div v-else class="rec-result">
          <span v-if="rec.status === 'approved'" class="result-text approved">已批准推送给 {{ rec.studentName }}</span>
          <span v-if="rec.status === 'modified'" class="result-text modified">已修正推送：{{ rec.modifiedText }}</span>
          <span v-if="rec.status === 'rejected'" class="result-text rejected">已驳回，不推送</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { LeftOutlined } from '@ant-design/icons-vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const token = localStorage.getItem('admin_token')
const authHeaders = { Authorization: `Bearer ${token}` }

const loading = ref(false)
const recommendations = ref<any[]>([])

const PAGE_SIZE = 30

function approveRec(rec: any) {
  rec.status = 'approved'
  message.success(`已批准推送给 ${rec.studentName}`)
}

function rejectRec(rec: any) {
  rec.status = 'rejected'
  message.warning(`已驳回对 ${rec.studentName} 的建议`)
}

function confirmModify(rec: any) {
  if (!rec.modifiedText?.trim()) {
    message.warning('请输入修正后的建议内容')
    return
  }
  rec.status = 'modified'
  rec.showModify = false
  message.success(`已修正并推送给 ${rec.studentName}`)
}

// 生成审核数据（与 CoachHome 一致）
function generateSampleRecommendations() {
  const names = [
    '张明华', '王小红', '李建国', '赵芳芳', '刘大伟', '陈晓丽', '杨志强', '黄丽萍',
    '周文博', '吴雅琴', '孙海涛', '马晓东', '朱秀英', '胡建华', '林美玲', '郭志远',
    '何晓燕', '高建平', '罗雪梅', '梁伟明', '谢丽娟', '宋志刚', '唐小芳', '韩大勇',
    '冯雅静', '曹明辉', '彭晓霞', '潘建文', '蒋美华', '邓志豪',
  ]
  const templates = [
    { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}近3天血糖波动较大，建议进行电话跟进，了解饮食和用药情况` },
    { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}处于准备期，建议推送"运动入门指南"课程，强化行为改变动机` },
    { type: 'followup', typeLabel: '跟进提醒', tpl: (n: string) => `${n}已3天未打卡，建议发送关怀消息，了解近况` },
    { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}睡眠质量持续下降，建议关注情绪状态并调整睡眠干预方案` },
    { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}行为执行率较低，建议降低任务难度，采用渐进式目标设定` },
    { type: 'followup', typeLabel: '跟进提醒', tpl: (n: string) => `${n}上次评估已超过30天，建议推送高频快速评估` },
    { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}餐后血糖多次超过13.9mmol/L，建议立即电话了解饮食情况` },
    { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}已进入行动期但动力不足，建议引入同伴激励机制` },
    { type: 'followup', typeLabel: '跟进提醒', tpl: (n: string) => `${n}连续5天运动时间不足，建议调整运动方案或了解阻碍原因` },
    { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}体重连续两周上升，建议重新评估饮食干预方案有效性` },
  ]
  return names.slice(0, PAGE_SIZE).map((name, i) => {
    const t = templates[i % templates.length]
    return {
      id: `ai${String(i + 1).padStart(3, '0')}`,
      type: t.type,
      typeLabel: t.typeLabel,
      studentName: name,
      suggestion: t.tpl(name),
      status: 'pending' as 'pending' | 'approved' | 'modified' | 'rejected',
      showModify: false,
      modifiedText: '',
    }
  })
}

onMounted(async () => {
  loading.value = true
  try {
    // 尝试从 API 加载（未来可扩展）
    const res = await fetch(`${API_BASE}/api/v1/coach/dashboard`, { headers: authHeaders })
    if (!res.ok) throw new Error('API failed')
    const data = await res.json()
    const studentNames = (data.students || [])
      .filter((s: any) => s.priority === 'high' || s.priority === 'medium')
      .slice(0, PAGE_SIZE)
      .map((s: any) => s.name)

    if (studentNames.length > 0) {
      const templates = [
        { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}近3天血糖波动较大，建议进行电话跟进，了解饮食和用药情况` },
        { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}处于准备期，建议推送"运动入门指南"课程，强化行为改变动机` },
        { type: 'followup', typeLabel: '跟进提醒', tpl: (n: string) => `${n}已3天未打卡，建议发送关怀消息，了解近况` },
        { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}睡眠质量持续下降，建议关注情绪状态并调整睡眠干预方案` },
        { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}行为执行率较低，建议降低任务难度，采用渐进式目标设定` },
        { type: 'followup', typeLabel: '跟进提醒', tpl: (n: string) => `${n}上次评估已超过30天，建议推送高频快速评估` },
        { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}餐后血糖多次超过13.9mmol/L，建议立即电话了解饮食情况` },
        { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}已进入行动期但动力不足，建议引入同伴激励机制` },
      ]
      recommendations.value = studentNames.map((name: string, i: number) => {
        const t = templates[i % templates.length]
        return {
          id: `ai${String(i + 1).padStart(3, '0')}`,
          type: t.type, typeLabel: t.typeLabel,
          studentName: name, suggestion: t.tpl(name),
          status: 'pending', showModify: false, modifiedText: '',
        }
      })
    } else {
      recommendations.value = generateSampleRecommendations()
    }
  } catch {
    recommendations.value = generateSampleRecommendations()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.coach-ai-review-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 18px;
}
.review-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.recommendation-card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  padding: 14px 16px;
  transition: box-shadow 0.2s;
}
.recommendation-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.rec-approved { border-left: 3px solid #52c41a; }
.rec-rejected { border-left: 3px solid #ff4d4f; opacity: 0.7; }
.rec-modified { border-left: 3px solid #1890ff; }
.rec-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.rec-type {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  color: #fff;
  font-weight: 600;
}
.rec-type.alert { background: #ff4d4f; }
.rec-type.intervention { background: #1890ff; }
.rec-type.followup { background: #faad14; }
.rec-student {
  font-weight: 600;
  font-size: 14px;
}
.rec-status {
  margin-left: auto;
  font-size: 12px;
  font-weight: 500;
}
.status-approved { color: #52c41a; }
.status-rejected { color: #ff4d4f; }
.status-modified { color: #1890ff; }
.rec-content {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin-bottom: 10px;
}
.rec-ai-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 2px;
}
.rec-modify-area {
  margin-bottom: 10px;
}
.modify-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.rec-actions {
  display: flex;
  gap: 8px;
}
.rec-result {
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 6px;
  font-size: 12px;
}
.result-text.approved { color: #52c41a; }
.result-text.modified { color: #1890ff; }
.result-text.rejected { color: #ff4d4f; }
</style>
