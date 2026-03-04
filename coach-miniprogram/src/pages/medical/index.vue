<template>
  <view class="md-page">
    <!-- Navbar -->
    <view class="md-navbar">
      <view class="md-nav-back" @tap="goBack">←</view>
      <text class="md-nav-title">理性就医</text>
      <view class="md-nav-right"></view>
    </view>

    <!-- Tab -->
    <view class="md-tabs">
      <view class="md-tab" :class="{ active: activeTab === 'meds' }" @tap="activeTab = 'meds'"><text>我的用药</text></view>
      <view class="md-tab" :class="{ active: activeTab === 'visits' }" @tap="activeTab = 'visits'"><text>就诊记录</text></view>
    </view>

    <scroll-view scroll-y class="md-scroll">
      <!-- ═ 用药 Tab ═ -->
      <template v-if="activeTab === 'meds'">
        <!-- 依从统计 -->
        <view class="md-adh-card" v-if="adherence">
          <view class="md-adh-item">
            <text class="md-adh-val" :style="{ color: adherenceColor }">{{ adherence.adherence_rate != null ? adherence.adherence_rate + '%' : '—' }}</text>
            <text class="md-adh-label">近7日依从率</text>
          </view>
          <view class="md-adh-div"></view>
          <view class="md-adh-item">
            <text class="md-adh-val">{{ adherence.active_medications || 0 }}</text>
            <text class="md-adh-label">在用药物</text>
          </view>
          <view class="md-adh-div"></view>
          <view class="md-adh-item">
            <text class="md-adh-val">{{ adherence.taken || 0 }}/{{ adherence.total_expected || 0 }}</text>
            <text class="md-adh-label">本周次数</text>
          </view>
        </view>

        <view class="md-sec-header">
          <text class="md-sec-title">在用药物</text>
          <view class="md-add-btn" @tap="openAddMed"><text>+ 添加</text></view>
        </view>
        <view v-if="loadingMeds" class="md-loading"><text>加载中…</text></view>
        <view v-else-if="!medications.length" class="md-empty"><text>还没有用药记录</text></view>
        <view v-for="m in medications" :key="m.id" class="md-med-card">
          <view class="md-med-row">
            <text class="md-med-name">{{ m.name }}</text>
            <text class="md-med-dose">{{ m.dosage }}</text>
          </view>
          <text v-if="m.frequency" class="md-med-freq">{{ m.frequency }}</text>
          <view v-if="m.reminder_time" class="md-reminder-tag">
            <text>⏰ 每日 {{ m.reminder_time.slice(0,5) }} 提醒</text>
          </view>
          <view v-if="m.last_taken_at" class="md-med-last">
            <text>上次：{{ formatTime(m.last_taken_at) }}</text>
            <text :class="m.last_taken ? 'md-taken-yes' : 'md-taken-no'">{{ m.last_taken ? ' ✓已服' : ' ✗漏服' }}</text>
          </view>
          <view class="md-med-btns">
            <view class="md-btn md-btn-take" @tap="checkin(m.id, true)"><text>✓ 已服药</text></view>
            <view class="md-btn md-btn-miss" @tap="checkin(m.id, false)"><text>✗ 漏服</text></view>
            <view class="md-btn md-btn-stop" @tap="deactivate(m.id)"><text>停用</text></view>
          </view>
        </view>
      </template>

      <!-- ═ 就诊 Tab ═ -->
      <template v-if="activeTab === 'visits'">
        <view class="md-sec-header">
          <text class="md-sec-title">就诊记录</text>
          <view class="md-add-btn" @tap="openAddVisit"><text>+ 记录</text></view>
        </view>
        <view v-if="loadingVisits" class="md-loading"><text>加载中…</text></view>
        <view v-else-if="!visits.length" class="md-empty"><text>还没有就诊记录</text></view>
        <view v-for="v in visits" :key="v.id" class="md-visit-card" @tap="viewVisit(v)">
          <text class="md-visit-date">{{ v.visit_date }}</text>
          <text class="md-visit-hosp">{{ v.hospital || '医院' }}{{ v.department ? ' · ' + v.department : '' }}</text>
          <text v-if="v.diagnosis" class="md-visit-diag">{{ v.diagnosis }}</text>
          <view class="md-visit-foot">
            <text v-if="v.next_visit" class="md-visit-next">复诊：{{ v.next_visit }}</text>
            <view v-if="v.is_shared" class="md-shared-tag"><text>已分享教练</text></view>
          </view>
        </view>
      </template>

      <view style="height:120rpx;"></view>
    </scroll-view>

    <!-- 添加药物弹窗 -->
    <view class="md-overlay" v-if="showAddMed" @tap="showAddMed = false">
      <view class="md-sheet" @tap.stop>
        <view class="md-sheet-head"><text class="md-sheet-title">添加药物</text><view @tap="showAddMed = false"><text class="md-close">✕</text></view></view>
        <view class="md-field"><text class="md-field-lb">药物名称</text><input class="md-input" v-model="medForm.name" placeholder="如：二甲双胍" /></view>
        <view class="md-field"><text class="md-field-lb">剂量</text><input class="md-input" v-model="medForm.dosage" placeholder="如：500mg" /></view>
        <view class="md-field"><text class="md-field-lb">频率</text><input class="md-input" v-model="medForm.frequency" placeholder="如：每日2次，餐后" /></view>
        <view class="md-field md-field-col"><text class="md-field-lb">备注</text><textarea class="md-ta" v-model="medForm.note" placeholder="医嘱或特殊说明" /></view>
        <view class="md-field">
          <text class="md-field-lb">服药提醒</text>
          <picker mode="time" :value="medForm.reminder_time || '08:00'" @change="(e:any) => medForm.reminder_time = e.detail.value">
            <view class="md-time-picker">
              <text>{{ medForm.reminder_time || '不设提醒' }}</text>
              <text class="md-time-arrow">›</text>
            </view>
          </picker>
          <view v-if="medForm.reminder_time" class="md-time-clear" @tap="medForm.reminder_time = ''"><text>清除</text></view>
        </view>
        <view class="md-submit-btn" :class="{ disabled: !medForm.name.trim() }" @tap="submitMed"><text>{{ submitting ? '添加中…' : '添加药物' }}</text></view>
      </view>
    </view>

    <!-- 添加就诊弹窗 -->
    <view class="md-overlay" v-if="showAddVisit" @tap="showAddVisit = false">
      <view class="md-sheet" @tap.stop>
        <view class="md-sheet-head"><text class="md-sheet-title">就诊记录</text><view @tap="showAddVisit = false"><text class="md-close">✕</text></view></view>
        <scroll-view scroll-y style="max-height:65vh;">
          <view class="md-field"><text class="md-field-lb">就诊日期</text><input class="md-input" v-model="visitForm.visit_date" placeholder="YYYY-MM-DD" /></view>
          <view class="md-field"><text class="md-field-lb">医院</text><input class="md-input" v-model="visitForm.hospital" placeholder="医院名称" /></view>
          <view class="md-field"><text class="md-field-lb">科室</text><input class="md-input" v-model="visitForm.department" placeholder="如：内分泌科" /></view>
          <view class="md-field"><text class="md-field-lb">医生</text><input class="md-input" v-model="visitForm.doctor_name" placeholder="医生姓名（选填）" /></view>
          <view class="md-field md-field-col"><text class="md-field-lb">主诉</text><textarea class="md-ta" v-model="visitForm.chief_complaint" placeholder="就诊主要原因" /></view>
          <view class="md-field md-field-col"><text class="md-field-lb">诊断结果</text><textarea class="md-ta" v-model="visitForm.diagnosis" placeholder="医生的诊断" /></view>
          <view class="md-field md-field-col"><text class="md-field-lb">处方/医嘱</text><textarea class="md-ta" v-model="visitForm.prescription" placeholder="药物或建议" /></view>
          <view class="md-field"><text class="md-field-lb">下次复诊</text><input class="md-input" v-model="visitForm.next_visit" placeholder="YYYY-MM-DD（选填）" /></view>
          <view class="md-share-row">
            <text class="md-share-label">{{ visitForm.is_shared ? '已分享给教练' : '仅自己可见' }}</text>
            <switch :checked="visitForm.is_shared" @change="(e:any) => visitForm.is_shared = e.detail.value" color="#1565c0" style="transform:scale(0.8)" />
          </view>
          <view class="md-submit-btn" :class="{ disabled: !visitForm.visit_date || !visitForm.hospital }" @tap="submitVisit"><text>{{ submitting ? '保存中…' : '保存记录' }}</text></view>
        </scroll-view>
      </view>
    </view>

    <!-- 就诊详情弹窗 -->
    <view class="md-overlay" v-if="showVisitDetail" @tap="showVisitDetail = false">
      <view class="md-sheet" @tap.stop v-if="selectedVisit">
        <view class="md-sheet-head"><text class="md-sheet-title">就诊摘要</text><view @tap="showVisitDetail = false"><text class="md-close">✕</text></view></view>
        <view class="md-detail-row"><text class="md-detail-lb">日期</text><text>{{ selectedVisit.visit_date }}</text></view>
        <view class="md-detail-row"><text class="md-detail-lb">医院/科室</text><text>{{ selectedVisit.hospital }} {{ selectedVisit.department }}</text></view>
        <view v-if="selectedVisit.doctor_name" class="md-detail-row"><text class="md-detail-lb">医生</text><text>{{ selectedVisit.doctor_name }}</text></view>
        <view v-if="selectedVisit.chief_complaint" class="md-detail-row"><text class="md-detail-lb">主诉</text><text>{{ selectedVisit.chief_complaint }}</text></view>
        <view v-if="selectedVisit.diagnosis" class="md-detail-row"><text class="md-detail-lb">诊断</text><text>{{ selectedVisit.diagnosis }}</text></view>
        <view v-if="selectedVisit.prescription" class="md-detail-row"><text class="md-detail-lb">处方</text><text>{{ selectedVisit.prescription }}</text></view>
        <view v-if="selectedVisit.next_visit" class="md-detail-row"><text class="md-detail-lb">复诊</text><text>{{ selectedVisit.next_visit }}</text></view>
        <text v-if="selectedVisit.is_shared" class="md-shared-hint">✅ 此记录已分享给您的教练</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const activeTab = ref('meds')
const loadingMeds = ref(false)
const loadingVisits = ref(false)
const submitting = ref(false)
const showAddMed = ref(false)
const showAddVisit = ref(false)
const showVisitDetail = ref(false)
const medications = ref<any[]>([])
const visits = ref<any[]>([])
const adherence = ref<any>(null)
const selectedVisit = ref<any>(null)

const adherenceColor = computed(() => {
  const r = adherence.value?.adherence_rate
  if (r == null) return '#999'
  return r >= 80 ? '#16a34a' : r >= 60 ? '#d97706' : '#dc2626'
})

const medForm = reactive({ name: '', dosage: '', frequency: '', note: '', reminder_time: '' })
const visitForm = reactive({
  visit_date: new Date().toISOString().slice(0, 10),
  hospital: '', department: '', doctor_name: '',
  chief_complaint: '', diagnosis: '', prescription: '',
  next_visit: '', is_shared: false,
})

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

function formatTime(iso: string) {
  if (!iso) return ''
  const diff = (Date.now() - new Date(iso).getTime()) / 1000 / 60
  if (diff < 60) return `${Math.round(diff)}分钟前`
  if (diff < 1440) return `${Math.round(diff / 60)}小时前`
  return `${Math.round(diff / 1440)}天前`
}

function openAddMed() { Object.assign(medForm, { name: '', dosage: '', frequency: '', note: '' }); showAddMed.value = true }
function openAddVisit() {
  Object.assign(visitForm, { visit_date: new Date().toISOString().slice(0, 10), hospital: '', department: '', doctor_name: '', chief_complaint: '', diagnosis: '', prescription: '', next_visit: '', is_shared: false })
  showAddVisit.value = true
}
function viewVisit(v: any) { selectedVisit.value = v; showVisitDetail.value = true }

async function loadMeds() {
  loadingMeds.value = true
  try { const res: any = await http<any>('/api/v1/medical/medications?active_only=true'); medications.value = res.items || [] }
  catch { medications.value = [] } finally { loadingMeds.value = false }
}
async function loadAdherence() {
  try { adherence.value = await http<any>('/api/v1/medical/adherence?days=7') } catch { adherence.value = null }
}
async function loadVisits() {
  loadingVisits.value = true
  try { const res: any = await http<any>('/api/v1/medical/visits'); visits.value = res.items || [] }
  catch { visits.value = [] } finally { loadingVisits.value = false }
}

async function checkin(medId: number, taken: boolean) {
  try {
    await http(`/api/v1/medical/medications/${medId}/checkin`, { method: 'POST', data: { taken } })
    uni.showToast({ title: taken ? '已记录服药 ✓' : '已记录漏服', icon: 'none' })
    loadMeds(); loadAdherence()
  } catch { uni.showToast({ title: '记录失败', icon: 'none' }) }
}

async function deactivate(medId: number) {
  uni.showModal({
    title: '停用药物', content: '确认停用此药物？', confirmText: '停用', cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await http(`/api/v1/medical/medications/${medId}`, { method: 'DELETE' })
        uni.showToast({ title: '已停用', icon: 'success' })
        loadMeds(); loadAdherence()
      } catch { uni.showToast({ title: '停用失败', icon: 'none' }) }
    }
  })
}

async function submitMed() {
  if (!medForm.name.trim() || submitting.value) return
  submitting.value = true
  try {
    await http('/api/v1/medical/medications', {
      method: 'POST',
      data: {
        name: medForm.name.trim(),
        dosage: medForm.dosage.trim() || undefined,
        frequency: medForm.frequency.trim() || undefined,
        note: medForm.note.trim() || undefined,
        reminder_time: medForm.reminder_time || undefined,
      },
    })
    uni.showToast({ title: '已添加', icon: 'success' })
    showAddMed.value = false
    Object.assign(medForm, { name: '', dosage: '', frequency: '', note: '', reminder_time: '' })
    loadMeds(); loadAdherence()
  } catch { uni.showToast({ title: '添加失败', icon: 'none' }) } finally { submitting.value = false }
}

async function submitVisit() {
  if (!visitForm.visit_date || !visitForm.hospital || submitting.value) return
  submitting.value = true
  try {
    await http('/api/v1/medical/visits', { method: 'POST', data: { visit_date: visitForm.visit_date, hospital: visitForm.hospital, department: visitForm.department || undefined, doctor_name: visitForm.doctor_name || undefined, chief_complaint: visitForm.chief_complaint || undefined, diagnosis: visitForm.diagnosis || undefined, prescription: visitForm.prescription || undefined, next_visit: visitForm.next_visit || undefined, is_shared: visitForm.is_shared } })
    uni.showToast({ title: '记录已保存', icon: 'success' }); showAddVisit.value = false; loadVisits()
  } catch { uni.showToast({ title: '保存失败', icon: 'none' }) } finally { submitting.value = false }
}

onMounted(() => { loadMeds(); loadAdherence(); loadVisits() })
</script>

<style scoped>
.md-page { min-height: 100vh; background: #F5F6FA; }
.md-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #1565c0 0%, #1e88e5 100%); color: #fff; }
.md-nav-back { font-size: 40rpx; padding: 16rpx; }
.md-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.md-nav-right { width: 72rpx; }
.md-tabs { display: flex; background: #fff; border-bottom: 2rpx solid #f0f0f0; }
.md-tab { flex: 1; text-align: center; padding: 20rpx; font-size: 28rpx; color: #9ca3af; border-bottom: 4rpx solid transparent; margin-bottom: -2rpx; }
.md-tab.active { color: #1565c0; border-bottom-color: #1565c0; font-weight: 700; }
.md-scroll { height: calc(100vh - 240rpx); }

.md-adh-card { display: flex; align-items: center; justify-content: space-around; background: #fff; margin: 16rpx 24rpx; padding: 24rpx; border-radius: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.md-adh-item { text-align: center; }
.md-adh-val { display: block; font-size: 40rpx; font-weight: 800; color: #16a34a; }
.md-adh-label { display: block; font-size: 22rpx; color: #9ca3af; margin-top: 4rpx; }
.md-adh-div { width: 2rpx; height: 60rpx; background: #f3f4f6; }

.md-sec-header { display: flex; align-items: center; justify-content: space-between; padding: 16rpx 24rpx; }
.md-sec-title { font-size: 30rpx; font-weight: 700; color: #2C3E50; }
.md-add-btn { background: #1565c0; padding: 8rpx 24rpx; border-radius: 8rpx; }
.md-add-btn text { font-size: 24rpx; color: #fff; }
.md-loading, .md-empty { text-align: center; padding: 60rpx; font-size: 26rpx; color: #BDC3C7; }

.md-med-card { background: #fff; margin: 0 24rpx 16rpx; padding: 20rpx 24rpx; border-radius: 16rpx; box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.04); }
.md-med-row { display: flex; align-items: baseline; gap: 12rpx; margin-bottom: 6rpx; }
.md-med-name { font-size: 30rpx; font-weight: 700; color: #111; }
.md-med-dose { font-size: 24rpx; color: #6b7280; }
.md-med-freq { display: block; font-size: 24rpx; color: #9ca3af; margin-bottom: 8rpx; }
.md-med-last { display: flex; font-size: 22rpx; color: #bbb; margin-bottom: 16rpx; }
.md-taken-yes { color: #16a34a; font-weight: 600; }
.md-taken-no { color: #dc2626; font-weight: 600; }
.md-med-btns { display: flex; gap: 12rpx; }
.md-btn { flex: 1; text-align: center; padding: 12rpx; border-radius: 10rpx; font-size: 24rpx; font-weight: 600; }
.md-btn-take { background: #dcfce7; color: #16a34a; }
.md-btn-miss { background: #fee2e2; color: #dc2626; }
.md-btn-stop { background: #f3f4f6; color: #9ca3af; }

.md-visit-card { background: #fff; margin: 0 24rpx 16rpx; padding: 20rpx 24rpx; border-radius: 16rpx; box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.04); }
.md-visit-date { display: block; font-size: 22rpx; color: #9ca3af; margin-bottom: 4rpx; }
.md-visit-hosp { display: block; font-size: 30rpx; font-weight: 700; color: #111; margin-bottom: 6rpx; }
.md-visit-diag { display: block; font-size: 26rpx; color: #555; margin-bottom: 8rpx; }
.md-visit-foot { display: flex; align-items: center; gap: 12rpx; }
.md-visit-next { font-size: 22rpx; color: #1565c0; }
.md-shared-tag { background: #dcfce7; padding: 4rpx 12rpx; border-radius: 8rpx; }
.md-shared-tag text { font-size: 20rpx; color: #16a34a; }

.md-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: flex-end; }
.md-sheet { background: #fff; border-radius: 24rpx 24rpx 0 0; width: 100%; max-height: 85vh; padding: 24rpx; box-sizing: border-box; }
.md-sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20rpx; }
.md-sheet-title { font-size: 32rpx; font-weight: 700; color: #111; }
.md-close { font-size: 36rpx; color: #bbb; padding: 8rpx; }
.md-field { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.md-field-col { flex-direction: column; align-items: flex-start; }
.md-field-lb { font-size: 26rpx; color: #646566; min-width: 100rpx; flex-shrink: 0; }
.md-input { flex: 1; font-size: 28rpx; color: #333; }
.md-time-picker { display: flex; align-items: center; justify-content: space-between; flex: 1; background: #f5f5f5; border-radius: 8rpx; padding: 10rpx 16rpx; }
.md-time-arrow { color: #9ca3af; font-size: 32rpx; }
.md-time-clear { margin-left: 12rpx; font-size: 22rpx; color: #dc2626; padding: 8rpx; }
.md-reminder-tag { display: inline-block; background: #f0fff4; color: #16a34a; font-size: 22rpx; padding: 4rpx 12rpx; border-radius: 20rpx; margin-bottom: 8rpx; }
.md-ta { width: 100%; height: 100rpx; font-size: 26rpx; color: #333; background: #fafafa; border-radius: 8rpx; padding: 10rpx; box-sizing: border-box; margin-top: 8rpx; }
.md-share-row { display: flex; align-items: center; justify-content: space-between; padding: 16rpx 0; border-top: 1rpx solid #f0f0f0; margin-top: 8rpx; }
.md-share-label { font-size: 26rpx; color: #555; }
.md-submit-btn { background: #1565c0; color: #fff; text-align: center; padding: 24rpx; border-radius: 12rpx; font-size: 30rpx; font-weight: 700; margin-top: 20rpx; }
.md-submit-btn.disabled { opacity: 0.4; }
.md-detail-row { display: flex; gap: 16rpx; padding: 12rpx 0; border-bottom: 1rpx solid #f5f5f5; }
.md-detail-lb { font-size: 24rpx; color: #9ca3af; min-width: 100rpx; flex-shrink: 0; }
.md-detail-row text:last-child { font-size: 26rpx; color: #333; }
.md-shared-hint { display: block; text-align: center; font-size: 26rpx; color: #16a34a; padding: 20rpx 0; }
</style>
