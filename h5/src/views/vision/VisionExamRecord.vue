<template>
  <div class="vision-exam">
    <van-nav-bar title="视力检查记录" left-arrow @click-left="$router.back()" />

    <van-tabs v-model:active="activeTab">
      <!-- 录入检查 -->
      <van-tab title="录入检查">
        <div class="form-section">
          <van-cell-group inset>
            <van-field
              v-model="form.exam_date"
              label="检查日期"
              placeholder="YYYY-MM-DD"
              :rules="[{ required: true }]"
              @click="showDatePicker = true"
              readonly
              is-link
            />
            <van-field v-model="form.institution" label="检查机构" placeholder="医院/眼科诊所名称" />
            <van-field v-model="form.examiner_name" label="检查医生" placeholder="选填" />
          </van-cell-group>

          <van-cell-group inset title="左眼数据">
            <van-field v-model.number="form.left_eye_sph" label="球镜 (SPH)" type="number" placeholder="如 -2.50" input-align="right">
              <template #button><span class="unit">D</span></template>
            </van-field>
            <van-field v-model.number="form.left_eye_cyl" label="柱镜 (CYL)" type="number" placeholder="散光度数" input-align="right">
              <template #button><span class="unit">D</span></template>
            </van-field>
            <van-field v-model.number="form.left_eye_axial_len" label="眼轴长度" type="number" placeholder="如 24.5" input-align="right">
              <template #button><span class="unit">mm</span></template>
            </van-field>
            <van-field v-model.number="form.left_eye_va" label="视力" type="number" placeholder="5分制, 如 4.8" input-align="right" />
          </van-cell-group>

          <van-cell-group inset title="右眼数据">
            <van-field v-model.number="form.right_eye_sph" label="球镜 (SPH)" type="number" placeholder="如 -2.50" input-align="right">
              <template #button><span class="unit">D</span></template>
            </van-field>
            <van-field v-model.number="form.right_eye_cyl" label="柱镜 (CYL)" type="number" placeholder="散光度数" input-align="right">
              <template #button><span class="unit">D</span></template>
            </van-field>
            <van-field v-model.number="form.right_eye_axial_len" label="眼轴长度" type="number" placeholder="如 24.5" input-align="right">
              <template #button><span class="unit">mm</span></template>
            </van-field>
            <van-field v-model.number="form.right_eye_va" label="视力" type="number" placeholder="5分制, 如 4.8" input-align="right" />
          </van-cell-group>

          <van-cell-group inset>
            <van-field v-model="form.notes" type="textarea" label="备注" placeholder="医生建议等" rows="2" autosize />
          </van-cell-group>

          <div class="submit-area">
            <van-button type="primary" block round :loading="submitting" @click="handleSubmit">
              保存检查记录
            </van-button>
          </div>
        </div>
      </van-tab>

      <!-- 历史记录 -->
      <van-tab title="检查历史">
        <van-loading v-if="loadingHistory" class="page-loading" />
        <van-empty v-else-if="!records.length" description="暂无检查记录" />
        <div v-else class="history-list">
          <div v-for="r in records" :key="r.id" class="exam-card">
            <div class="exam-header">
              <span class="exam-date">{{ r.exam_date }}</span>
              <van-tag :type="riskTagType(r.risk_level)" size="mini">{{ riskLabel(r.risk_level) }}</van-tag>
            </div>
            <div class="exam-body">
              <div class="eye-row">
                <span class="eye-label">左眼</span>
                <span>SPH {{ r.left_eye_sph ?? '-' }}</span>
                <span>CYL {{ r.left_eye_cyl ?? '-' }}</span>
                <span>VA {{ r.left_eye_va ?? '-' }}</span>
              </div>
              <div class="eye-row">
                <span class="eye-label">右眼</span>
                <span>SPH {{ r.right_eye_sph ?? '-' }}</span>
                <span>CYL {{ r.right_eye_cyl ?? '-' }}</span>
                <span>VA {{ r.right_eye_va ?? '-' }}</span>
              </div>
              <div v-if="r.institution" class="exam-meta">{{ r.institution }}</div>
            </div>

            <!-- 趋势提示 (与上一条对比) -->
            <div v-if="r._trend" class="trend-tip" :class="r._trend">
              <van-icon :name="r._trend === 'worse' ? 'arrow-down' : 'arrow-up'" />
              {{ r._trend === 'worse' ? '度数加深' : '度数减轻' }}
            </div>
          </div>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 日期选择器 -->
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker
        v-model="pickerDate"
        title="选择检查日期"
        :min-date="new Date(2020, 0, 1)"
        :max-date="new Date()"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import { visionApi } from '@/api/vision'
import storage from '@/utils/storage'

const activeTab = ref(0)
const submitting = ref(false)
const loadingHistory = ref(true)
const records = ref<any[]>([])
const showDatePicker = ref(false)

const today = new Date()
const pickerDate = ref([
  today.getFullYear().toString(),
  String(today.getMonth() + 1).padStart(2, '0'),
  String(today.getDate()).padStart(2, '0'),
])

const form = ref({
  exam_date: `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`,
  institution: '',
  examiner_name: '',
  left_eye_sph: null as number | null,
  right_eye_sph: null as number | null,
  left_eye_cyl: null as number | null,
  right_eye_cyl: null as number | null,
  left_eye_axial_len: null as number | null,
  right_eye_axial_len: null as number | null,
  left_eye_va: null as number | null,
  right_eye_va: null as number | null,
  notes: '',
})

function onDateConfirm({ selectedValues }: any) {
  form.value.exam_date = selectedValues.join('-')
  showDatePicker.value = false
}

function riskTagType(level: string) {
  if (level === 'urgent') return 'danger'
  if (level === 'alert') return 'warning'
  if (level === 'watch') return 'primary'
  return 'success'
}

function riskLabel(level: string) {
  const map: Record<string, string> = { normal: '正常', watch: '关注', alert: '警惕', urgent: '紧急' }
  return map[level] || level
}

async function handleSubmit() {
  if (!form.value.exam_date) {
    showToast('请选择检查日期')
    return
  }
  submitting.value = true
  try {
    const res: any = await visionApi.createExam({
      exam_date: form.value.exam_date,
      institution: form.value.institution || undefined,
      examiner_name: form.value.examiner_name || undefined,
      left_eye_sph: form.value.left_eye_sph ?? undefined,
      right_eye_sph: form.value.right_eye_sph ?? undefined,
      left_eye_cyl: form.value.left_eye_cyl ?? undefined,
      right_eye_cyl: form.value.right_eye_cyl ?? undefined,
      left_eye_axial_len: form.value.left_eye_axial_len ?? undefined,
      right_eye_axial_len: form.value.right_eye_axial_len ?? undefined,
      left_eye_va: form.value.left_eye_va ?? undefined,
      right_eye_va: form.value.right_eye_va ?? undefined,
      notes: form.value.notes || undefined,
    })
    showSuccessToast(`已保存 (风险: ${riskLabel(res.risk_level)})`)
    // 切换到历史 tab 并刷新
    activeTab.value = 1
    loadHistory()
  } catch (e: any) {
    showToast(e?.response?.data?.detail || '保存失败')
  } finally {
    submitting.value = false
  }
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const user = storage.getAuthUser()
    const uid = user?.id
    if (!uid) { loadingHistory.value = false; return }
    const res: any = await visionApi.getExamRecords(uid)
    const list = res?.records || []
    // 计算趋势 (与上一条对比)
    for (let i = 0; i < list.length; i++) {
      if (i < list.length - 1) {
        const curr = Math.min(list[i].left_eye_sph ?? 0, list[i].right_eye_sph ?? 0)
        const prev = Math.min(list[i + 1].left_eye_sph ?? 0, list[i + 1].right_eye_sph ?? 0)
        if (curr < prev - 0.25) {
          list[i]._trend = 'worse'
        } else if (curr > prev + 0.25) {
          list[i]._trend = 'better'
        }
      }
    }
    records.value = list
  } catch { /* ignore */ }
  loadingHistory.value = false
}

onMounted(loadHistory)
</script>

<style scoped>
.vision-exam {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 60px;
}
.form-section { padding-top: 12px; }
.unit { font-size: 12px; color: #999; }
.submit-area { padding: 16px; }
.history-list { padding: 12px 16px; }
.exam-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}
.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.exam-date { font-size: 15px; font-weight: 600; }
.eye-row {
  display: flex;
  gap: 12px;
  font-size: 13px;
  padding: 4px 0;
  color: #333;
}
.eye-label {
  font-weight: 500;
  width: 36px;
  flex-shrink: 0;
}
.exam-meta {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
.trend-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  margin-top: 8px;
  padding: 4px 8px;
  border-radius: 4px;
}
.trend-tip.worse { background: #fff2f0; color: #ff4d4f; }
.trend-tip.better { background: #f6ffed; color: #52c41a; }
.page-loading {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}
</style>
