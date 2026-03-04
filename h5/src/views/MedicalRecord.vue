<template>
  <div class="mr-page">
    <van-nav-bar title="理性就医" left-arrow @click-left="goBack()" />

    <!-- Tab -->
    <van-tabs v-model:active="activeTab" sticky>
      <van-tab title="我的用药" name="meds" />
      <van-tab title="就诊记录" name="visits" />
    </van-tabs>

    <!-- ═══ 用药 Tab ═══ -->
    <div v-show="activeTab === 'meds'" class="tab-content">

      <!-- 依从统计 -->
      <div class="adherence-card" v-if="adherence">
        <div class="adh-item">
          <span class="adh-val" :style="{ color: adherenceColor }">
            {{ adherence.adherence_rate != null ? adherence.adherence_rate + '%' : '—' }}
          </span>
          <span class="adh-label">近7日依从率</span>
        </div>
        <div class="adh-divider"></div>
        <div class="adh-item">
          <span class="adh-val">{{ adherence.active_medications ?? 0 }}</span>
          <span class="adh-label">在用药物</span>
        </div>
        <div class="adh-divider"></div>
        <div class="adh-item">
          <span class="adh-val">{{ adherence.taken ?? 0 }}/{{ adherence.total_expected ?? 0 }}</span>
          <span class="adh-label">本周次数</span>
        </div>
      </div>

      <!-- 用药列表 -->
      <div class="section-header">
        <span class="section-title">在用药物</span>
        <button class="add-btn" @click="openAddMed">+ 添加</button>
      </div>

      <van-loading v-if="loadingMeds" size="20" class="center-loader" />
      <van-empty v-else-if="!medications.length" description="还没有用药记录" />
      <template v-else>
        <div v-for="m in medications" :key="m.id" class="med-card">
          <div class="med-header">
            <span class="med-name">{{ m.name }}</span>
            <span class="med-dosage">{{ m.dosage }}</span>
          </div>
          <div class="med-freq" v-if="m.frequency">{{ m.frequency }}</div>
          <div class="med-last" v-if="m.last_taken_at">
            上次打卡：{{ formatTime(m.last_taken_at) }}
            <span :class="m.last_taken ? 'taken-yes' : 'taken-no'">
              {{ m.last_taken ? '✓ 已服' : '✗ 漏服' }}
            </span>
          </div>
          <div class="med-actions">
            <button class="med-btn med-btn-take" @click="checkin(m.id, true)">✓ 已服药</button>
            <button class="med-btn med-btn-miss" @click="checkin(m.id, false)">✗ 漏服</button>
            <button class="med-btn med-btn-stop" @click="deactivate(m.id)">停用</button>
          </div>
        </div>
      </template>
    </div>

    <!-- ═══ 就诊 Tab ═══ -->
    <div v-show="activeTab === 'visits'" class="tab-content">
      <div class="section-header">
        <span class="section-title">就诊记录</span>
        <button class="add-btn" @click="openAddVisit">+ 记录</button>
      </div>

      <van-loading v-if="loadingVisits" size="20" class="center-loader" />
      <van-empty v-else-if="!visits.length" description="还没有就诊记录" />
      <template v-else>
        <div v-for="v in visits" :key="v.id" class="visit-card" @click="viewVisit(v)">
          <div class="visit-date">{{ v.visit_date }}</div>
          <div class="visit-hospital">{{ v.hospital || '医院' }} {{ v.department ? '· ' + v.department : '' }}</div>
          <div class="visit-diag" v-if="v.diagnosis">{{ v.diagnosis }}</div>
          <div class="visit-next" v-if="v.next_visit">下次复诊：{{ v.next_visit }}</div>
          <span class="visit-shared" v-if="v.is_shared">已分享给教练</span>
        </div>
      </template>
    </div>

    <!-- ═══ 添加药物弹窗 ═══ -->
    <van-popup v-model:show="showAddMed" position="bottom" round :style="{ maxHeight: '85vh', overflowY: 'auto' }">
      <div class="popup-inner">
        <div class="popup-title">添加药物 <span class="popup-close" @click="showAddMed = false">✕</span></div>
        <van-field v-model="medForm.name" label="药物名称" placeholder="如：二甲双胍" clearable />
        <van-field v-model="medForm.dosage" label="剂量" placeholder="如：500mg" clearable />
        <van-field v-model="medForm.frequency" label="服用频率" placeholder="如：每日2次，餐后服用" clearable />
        <van-field v-model="medForm.note" type="textarea" :rows="2" label="备注" placeholder="医嘱或特殊说明" />
        <div class="popup-actions">
          <van-button plain round @click="showAddMed = false">取消</van-button>
          <van-button type="primary" round :loading="submitting" :disabled="!medForm.name.trim()" @click="submitMed">添加</van-button>
        </div>
      </div>
    </van-popup>

    <!-- ═══ 添加就诊弹窗 ═══ -->
    <van-popup v-model:show="showAddVisit" position="bottom" round :style="{ maxHeight: '90vh', overflowY: 'auto' }">
      <div class="popup-inner">
        <div class="popup-title">就诊记录 <span class="popup-close" @click="showAddVisit = false">✕</span></div>
        <van-field v-model="visitForm.visit_date" label="就诊日期" placeholder="YYYY-MM-DD" clearable />
        <van-field v-model="visitForm.hospital" label="医院" placeholder="医院名称" clearable />
        <van-field v-model="visitForm.department" label="科室" placeholder="如：内分泌科" clearable />
        <van-field v-model="visitForm.doctor_name" label="医生" placeholder="医生姓名（选填）" clearable />
        <van-field v-model="visitForm.chief_complaint" type="textarea" :rows="2" label="主诉" placeholder="你去就诊的主要原因" />
        <van-field v-model="visitForm.diagnosis" type="textarea" :rows="2" label="诊断结果" placeholder="医生的诊断" />
        <van-field v-model="visitForm.prescription" type="textarea" :rows="2" label="处方/医嘱" placeholder="医生开的药物或建议" />
        <van-field v-model="visitForm.next_visit" label="下次复诊" placeholder="YYYY-MM-DD（选填）" clearable />
        <div class="share-toggle-row">
          <span>{{ visitForm.is_shared ? '已分享给教练（可见）' : '仅自己可见' }}</span>
          <van-switch v-model="visitForm.is_shared" size="20px" />
        </div>
        <div class="popup-actions">
          <van-button plain round @click="showAddVisit = false">取消</van-button>
          <van-button type="primary" round :loading="submitting" :disabled="!visitForm.visit_date || !visitForm.hospital" @click="submitVisit">保存</van-button>
        </div>
      </div>
    </van-popup>

    <!-- ═══ 就诊详情 ═══ -->
    <van-popup v-model:show="showVisitDetail" position="bottom" round :style="{ maxHeight: '85vh', overflowY: 'auto' }">
      <div class="popup-inner" v-if="selectedVisit">
        <div class="popup-title">就诊摘要 <span class="popup-close" @click="showVisitDetail = false">✕</span></div>
        <div class="visit-detail-row"><span class="vd-label">日期</span><span>{{ selectedVisit.visit_date }}</span></div>
        <div class="visit-detail-row"><span class="vd-label">医院/科室</span><span>{{ selectedVisit.hospital }} {{ selectedVisit.department }}</span></div>
        <div class="visit-detail-row" v-if="selectedVisit.doctor_name"><span class="vd-label">医生</span><span>{{ selectedVisit.doctor_name }}</span></div>
        <div class="visit-detail-row" v-if="selectedVisit.chief_complaint"><span class="vd-label">主诉</span><span>{{ selectedVisit.chief_complaint }}</span></div>
        <div class="visit-detail-row" v-if="selectedVisit.diagnosis"><span class="vd-label">诊断</span><span>{{ selectedVisit.diagnosis }}</span></div>
        <div class="visit-detail-row" v-if="selectedVisit.prescription"><span class="vd-label">处方</span><span>{{ selectedVisit.prescription }}</span></div>
        <div class="visit-detail-row" v-if="selectedVisit.next_visit"><span class="vd-label">复诊</span><span>{{ selectedVisit.next_visit }}</span></div>
        <div class="share-hint" v-if="selectedVisit.is_shared">✅ 此记录已分享给您的教练</div>
        <div class="popup-actions">
          <van-button round plain @click="showVisitDetail = false">关闭</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import api from '@/api/index'
import { useGoBack } from '@/composables/useGoBack'

const { goBack } = useGoBack()

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
  if (r >= 80) return '#16a34a'
  if (r >= 60) return '#d97706'
  return '#dc2626'
})

const medForm = reactive({ name: '', dosage: '', frequency: '', note: '' })
const visitForm = reactive({
  visit_date: new Date().toISOString().slice(0, 10),
  hospital: '', department: '', doctor_name: '',
  chief_complaint: '', diagnosis: '', prescription: '',
  next_visit: '', is_shared: false,
})

function formatTime(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const diff = (Date.now() - d.getTime()) / 1000 / 60
  if (diff < 60) return `${Math.round(diff)}分钟前`
  if (diff < 1440) return `${Math.round(diff / 60)}小时前`
  return `${Math.round(diff / 1440)}天前`
}

function openAddMed() {
  Object.assign(medForm, { name: '', dosage: '', frequency: '', note: '' })
  showAddMed.value = true
}
function openAddVisit() {
  Object.assign(visitForm, {
    visit_date: new Date().toISOString().slice(0, 10),
    hospital: '', department: '', doctor_name: '',
    chief_complaint: '', diagnosis: '', prescription: '',
    next_visit: '', is_shared: false,
  })
  showAddVisit.value = true
}
function viewVisit(v: any) {
  selectedVisit.value = v
  showVisitDetail.value = true
}

async function loadMeds() {
  loadingMeds.value = true
  try {
    const res: any = await api.get('/api/v1/medical/medications', { params: { active_only: true } })
    medications.value = res.items || []
  } catch { medications.value = [] } finally { loadingMeds.value = false }
}

async function loadAdherence() {
  try {
    adherence.value = await api.get('/api/v1/medical/adherence', { params: { days: 7 } })
  } catch { adherence.value = null }
}

async function loadVisits() {
  loadingVisits.value = true
  try {
    const res: any = await api.get('/api/v1/medical/visits')
    visits.value = res.items || []
  } catch { visits.value = [] } finally { loadingVisits.value = false }
}

async function checkin(medId: number, taken: boolean) {
  try {
    await api.post(`/api/v1/medical/medications/${medId}/checkin`, { taken })
    showSuccessToast(taken ? '已记录服药 ✓' : '已记录漏服')
    loadMeds()
    loadAdherence()
  } catch { showFailToast('记录失败') }
}

async function deactivate(medId: number) {
  try {
    await showConfirmDialog({ title: '停用药物', message: '确认停用此药物？', confirmButtonText: '停用', cancelButtonText: '取消' })
    await api.delete(`/api/v1/medical/medications/${medId}`)
    showSuccessToast('已停用')
    loadMeds()
    loadAdherence()
  } catch (e: any) {
    if (e?.toString().includes('cancel')) return
    showFailToast('停用失败')
  }
}

async function submitMed() {
  submitting.value = true
  try {
    await api.post('/api/v1/medical/medications', {
      name: medForm.name.trim(),
      dosage: medForm.dosage.trim() || undefined,
      frequency: medForm.frequency.trim() || undefined,
      note: medForm.note.trim() || undefined,
    })
    showSuccessToast('已添加')
    showAddMed.value = false
    loadMeds()
    loadAdherence()
  } catch { showFailToast('添加失败') } finally { submitting.value = false }
}

async function submitVisit() {
  submitting.value = true
  try {
    await api.post('/api/v1/medical/visits', {
      visit_date: visitForm.visit_date,
      hospital: visitForm.hospital,
      department: visitForm.department || undefined,
      doctor_name: visitForm.doctor_name || undefined,
      chief_complaint: visitForm.chief_complaint || undefined,
      diagnosis: visitForm.diagnosis || undefined,
      prescription: visitForm.prescription || undefined,
      next_visit: visitForm.next_visit || undefined,
      is_shared: visitForm.is_shared,
    })
    showSuccessToast('记录已保存')
    showAddVisit.value = false
    loadVisits()
  } catch { showFailToast('保存失败') } finally { submitting.value = false }
}

onMounted(() => {
  loadMeds()
  loadAdherence()
  loadVisits()
})
</script>

<style scoped>
.mr-page { min-height: 100vh; background: #f7f8fa; }
.tab-content { padding: 12px 16px; }

.adherence-card {
  display: flex; align-items: center; justify-content: space-around;
  background: #fff; border-radius: 14px; padding: 16px;
  margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.adh-item { text-align: center; }
.adh-val { display: block; font-size: 22px; font-weight: 800; color: #16a34a; }
.adh-label { display: block; font-size: 12px; color: #9ca3af; margin-top: 2px; }
.adh-divider { width: 1px; height: 40px; background: #f3f4f6; }

.section-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.section-title { font-size: 15px; font-weight: 700; color: #111; }
.add-btn {
  background: #1565c0; color: #fff; border: none; border-radius: 8px;
  padding: 6px 14px; font-size: 13px; cursor: pointer;
}

.center-loader { display: block; text-align: center; padding: 32px; }

.med-card {
  background: #fff; border-radius: 12px; padding: 14px 16px;
  margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.med-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
.med-name { font-size: 15px; font-weight: 700; color: #111; }
.med-dosage { font-size: 13px; color: #6b7280; }
.med-freq { font-size: 12px; color: #9ca3af; margin-bottom: 6px; }
.med-last { font-size: 12px; color: #bbb; margin-bottom: 10px; }
.taken-yes { color: #16a34a; margin-left: 6px; font-weight: 600; }
.taken-no { color: #dc2626; margin-left: 6px; font-weight: 600; }
.med-actions { display: flex; gap: 8px; }
.med-btn { flex: 1; border: none; border-radius: 8px; padding: 7px; font-size: 12px; cursor: pointer; }
.med-btn-take { background: #dcfce7; color: #16a34a; font-weight: 600; }
.med-btn-miss { background: #fee2e2; color: #dc2626; font-weight: 600; }
.med-btn-stop { background: #f3f4f6; color: #9ca3af; }

.visit-card {
  background: #fff; border-radius: 12px; padding: 14px 16px;
  margin-bottom: 10px; cursor: pointer; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: transform 0.2s;
}
.visit-card:active { transform: scale(0.98); }
.visit-date { font-size: 12px; color: #9ca3af; margin-bottom: 4px; }
.visit-hospital { font-size: 15px; font-weight: 700; color: #111; margin-bottom: 4px; }
.visit-diag { font-size: 13px; color: #555; margin-bottom: 4px; }
.visit-next { font-size: 12px; color: #1565c0; }
.visit-shared { font-size: 11px; color: #16a34a; background: #dcfce7; padding: 2px 8px; border-radius: 10px; }

/* popup */
.popup-inner { padding: 16px 16px 32px; }
.popup-title {
  font-size: 16px; font-weight: 700; display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 12px;
}
.popup-close { font-size: 18px; color: #bbb; cursor: pointer; }
.share-toggle-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 0; font-size: 14px; color: #555; border-top: 1px solid #f0f0f0; margin-top: 4px;
}
.popup-actions { display: flex; gap: 12px; justify-content: flex-end; padding-top: 16px; }

/* visit detail */
.visit-detail-row { display: flex; gap: 12px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.vd-label { font-size: 13px; color: #9ca3af; min-width: 60px; flex-shrink: 0; }
.visit-detail-row span:last-child { font-size: 14px; color: #333; }
.share-hint { font-size: 13px; color: #16a34a; text-align: center; padding: 12px 0; }
</style>
