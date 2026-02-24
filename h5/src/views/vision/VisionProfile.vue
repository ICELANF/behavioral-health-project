<template>
  <div class="vision-profile">
    <van-nav-bar title="视力档案" left-arrow @click-left="$router.back()" />

    <van-loading v-if="loading" class="page-loading" />

    <template v-else>
      <!-- 风险等级卡片 -->
      <div class="risk-banner" :class="`risk-${profile.current_risk_level}`">
        <div class="risk-icon">
          <van-icon :name="riskIcon" size="28" />
        </div>
        <div class="risk-info">
          <div class="risk-title">{{ riskText }}</div>
          <div class="risk-desc">{{ riskDesc }}</div>
        </div>
      </div>

      <!-- 基本信息 -->
      <van-cell-group inset title="基本信息">
        <van-cell title="视力学生" :value="profile.is_vision_student ? '是' : '否'" />
        <van-cell title="近视起始年龄" :value="profile.myopia_onset_age ? `${profile.myopia_onset_age} 岁` : '未记录'" is-link @click="editOnsetAge" />
        <van-cell title="TTM 阶段" :value="stageText(profile.ttm_vision_stage)" />
        <van-cell title="最近检查" :value="profile.last_exam_date || '暂无'" />
        <van-cell title="加入时间" :value="profile.enrolled_at?.slice(0, 10) || '-'" />
      </van-cell-group>

      <!-- 监护人列表 -->
      <van-cell-group inset title="我的监护人">
        <van-cell
          v-for="g in guardians"
          :key="g.binding_id"
          :title="g.guardian_name"
          :label="g.relationship"
          is-link
        >
          <template #right-icon>
            <van-tag v-if="g.can_input_behavior" type="primary" size="mini">可代打卡</van-tag>
          </template>
        </van-cell>
        <van-empty v-if="!guardians.length" description="暂无监护人" image-size="60" />
      </van-cell-group>

      <!-- 专家绑定 -->
      <van-cell-group inset title="专家绑定">
        <van-cell
          title="绑定专家"
          :value="profile.expert_user_id ? `ID: ${profile.expert_user_id}` : '未绑定'"
        />
      </van-cell-group>

      <!-- 备注 -->
      <van-cell-group inset title="备注">
        <van-field
          v-model="notes"
          type="textarea"
          rows="2"
          autosize
          placeholder="个人视力相关备注"
          @blur="saveNotes"
        />
      </van-cell-group>

      <!-- 操作按钮 -->
      <div class="actions">
        <van-button plain type="primary" block @click="$router.push('/vision/exam')">
          录入检查记录
        </van-button>
      </div>
    </template>

    <!-- 近视起始年龄编辑弹窗 -->
    <van-dialog
      v-model:show="showOnsetDialog"
      title="近视起始年龄"
      show-cancel-button
      @confirm="saveOnsetAge"
    >
      <van-field v-model="onsetAgeInput" type="digit" placeholder="输入年龄" />
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import { visionApi } from '@/api/vision'

const loading = ref(true)
const profile = ref<any>({})
const guardians = ref<any[]>([])
const notes = ref('')
const showOnsetDialog = ref(false)
const onsetAgeInput = ref('')

const riskText = computed(() => {
  const map: Record<string, string> = { normal: '正常', watch: '关注', alert: '警惕', urgent: '紧急' }
  return map[profile.value.current_risk_level] || '正常'
})

const riskDesc = computed(() => {
  const map: Record<string, string> = {
    normal: '视力状况良好，继续保持',
    watch: '需要关注用眼习惯',
    alert: '建议尽快进行专业检查',
    urgent: '请立即预约眼科检查',
  }
  return map[profile.value.current_risk_level] || ''
})

const riskIcon = computed(() => {
  const map: Record<string, string> = { normal: 'passed', watch: 'info-o', alert: 'warning-o', urgent: 'close' }
  return map[profile.value.current_risk_level] || 'info-o'
})

function stageText(s: string) {
  const map: Record<string, string> = { S0: 'S0 前意向', S1: 'S1 意向', S2: 'S2 准备', S3: 'S3 行动', S4: 'S4 维持' }
  return map[s] || s || '-'
}

function editOnsetAge() {
  onsetAgeInput.value = profile.value.myopia_onset_age?.toString() || ''
  showOnsetDialog.value = true
}

async function saveOnsetAge() {
  const age = parseInt(onsetAgeInput.value)
  if (isNaN(age) || age < 0 || age > 30) {
    showToast('请输入 0-30 的年龄')
    return
  }
  try {
    await visionApi.updateProfile({ myopia_onset_age: age })
    profile.value.myopia_onset_age = age
    showSuccessToast('已更新')
  } catch {
    showToast('更新失败')
  }
}

async function saveNotes() {
  if (notes.value === (profile.value.notes || '')) return
  try {
    await visionApi.updateProfile({ notes: notes.value })
  } catch { /* ignore */ }
}

async function loadProfile() {
  try {
    const res: any = await visionApi.getMyProfile()
    profile.value = res || {}
    guardians.value = res?.guardians || []
    notes.value = res?.notes || ''
  } catch {
    showToast('加载档案失败')
  }
  loading.value = false
}

onMounted(loadProfile)
</script>

<style scoped>
.vision-profile {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 60px;
}
.risk-banner {
  margin: 16px;
  padding: 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: #fff;
}
.risk-normal { background: linear-gradient(135deg, #52c41a, #73d13d); }
.risk-watch { background: linear-gradient(135deg, #1890ff, #40a9ff); }
.risk-alert { background: linear-gradient(135deg, #fa8c16, #ffa940); }
.risk-urgent { background: linear-gradient(135deg, #ff4d4f, #ff7875); }
.risk-title { font-size: 18px; font-weight: 600; }
.risk-desc { font-size: 13px; opacity: 0.9; margin-top: 4px; }
.actions { padding: 16px; }
.page-loading {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}
</style>
