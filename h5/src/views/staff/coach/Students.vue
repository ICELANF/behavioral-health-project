<template>
  <div class="students-page">
    <!-- 左侧：学员列表 -->
    <div class="list-panel">
      <div class="panel-header">
        <h2>学员列表</h2>
        <div class="search-box">
          <input v-model="searchQ" type="text" placeholder="搜索学员名..." class="search-input" />
        </div>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="filteredStudents.length === 0" class="empty">暂无学员</div>
      <div v-else class="student-rows">
        <div
          v-for="s in filteredStudents"
          :key="s.id"
          class="student-row"
          :class="{ selected: selectedId === s.id }"
          @click="selectStudent(s)"
        >
          <div class="s-avatar">{{ (s.name || s.full_name || '?')[0] }}</div>
          <div class="s-info">
            <div class="s-name">{{ s.name || s.full_name }}</div>
            <div class="s-meta">
              <span class="stage-tag">{{ s.stage_label || s.stage || '未知' }}</span>
              <span class="risk-tag" :class="riskClass(s.risk_level)">{{ s.risk_level || 'R0' }}</span>
            </div>
          </div>
          <div class="s-action-count">{{ s.micro_action_7d ?? 0 }}次/7天</div>
        </div>
      </div>
    </div>

    <!-- 右侧：学员详情 -->
    <div class="detail-panel" :class="{ active: !!selectedStudent }">
      <div v-if="!selectedStudent" class="detail-empty">
        <div class="detail-empty-icon">👈</div>
        <p>点击左侧学员查看详情</p>
      </div>
      <template v-else>
        <div class="detail-header">
          <div class="detail-avatar">{{ (selectedStudent.name || selectedStudent.full_name || '?')[0] }}</div>
          <div class="detail-info">
            <h2>{{ selectedStudent.name || selectedStudent.full_name }}</h2>
            <div class="detail-tags">
              <span class="stage-tag">{{ selectedStudent.stage_label || selectedStudent.stage }}</span>
              <span class="risk-tag" :class="riskClass(selectedStudent.risk_level)">{{ selectedStudent.risk_level }}</span>
            </div>
          </div>
          <div class="detail-actions">
            <button class="act-btn act-primary" @click="openAssignModal">分配评估</button>
            <button class="act-btn act-secondary" @click="openNoteModal">开处方</button>
          </div>
        </div>

        <!-- Tabs -->
        <div class="detail-tabs">
          <button v-for="t in ['概况', '评估', '笔记', '健康']" :key="t" class="tab-btn" :class="{ active: activeTab === t }" @click="activeTab = t">{{ t }}</button>
        </div>

        <div class="detail-body">
          <!-- 概况 -->
          <template v-if="activeTab === '概况'">
            <div class="info-grid">
              <div class="info-item"><span class="info-k">ID</span><span class="info-v">{{ selectedStudent.id }}</span></div>
              <div class="info-item"><span class="info-k">阶段</span><span class="info-v">{{ selectedStudent.stage }}</span></div>
              <div class="info-item"><span class="info-k">7日微行动</span><span class="info-v">{{ selectedStudent.micro_action_7d ?? '-' }}</span></div>
              <div class="info-item"><span class="info-k">风险等级</span><span class="info-v">{{ selectedStudent.risk_level }}</span></div>
            </div>
          </template>

          <!-- 评估 -->
          <template v-else-if="activeTab === '评估'">
            <div v-if="assessmentLoading" class="loading">加载中...</div>
            <div v-else-if="assignments.length === 0" class="empty">暂无评估记录</div>
            <div v-else>
              <div v-for="a in assignments" :key="a.id" class="list-item">
                <div class="li-title">{{ a.scale_name || a.scale_id }}</div>
                <div class="li-meta">{{ a.status }} · {{ a.created_at?.slice(0, 10) }}</div>
              </div>
            </div>
          </template>

          <!-- 笔记 -->
          <template v-else-if="activeTab === '笔记'">
            <div v-if="notesLoading" class="loading">加载中...</div>
            <div v-else-if="notes.length === 0" class="empty">暂无笔记</div>
            <div v-else>
              <div v-for="n in notes" :key="n.id" class="list-item">
                <div class="li-title">{{ n.content || n.note }}</div>
                <div class="li-meta">{{ n.created_at?.slice(0, 10) }}</div>
              </div>
            </div>
          </template>

          <!-- 健康 -->
          <template v-else-if="activeTab === '健康'">
            <div class="empty">健康数据图表（接入健康API后展示）</div>
          </template>
        </div>
      </template>
    </div>

    <!-- 分配评估 Modal -->
    <div v-if="showAssignModal" class="modal-overlay" @click.self="showAssignModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>分配评估</h3>
          <button class="modal-close" @click="showAssignModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div v-for="s in scales" :key="s.key" class="checkbox-item">
            <input type="checkbox" :id="'scale-' + s.key" v-model="selectedScales" :value="s.key" />
            <label :for="'scale-' + s.key">{{ s.label }}</label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="act-btn act-secondary" @click="showAssignModal = false">取消</button>
          <button class="act-btn act-primary" :disabled="selectedScales.length === 0" @click="submitAssign">确认分配</button>
        </div>
      </div>
    </div>

    <!-- 处方 Modal -->
    <div v-if="showNoteModal" class="modal-overlay" @click.self="showNoteModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>开具行为处方</h3>
          <button class="modal-close" @click="showNoteModal = false">✕</button>
        </div>
        <div class="modal-body">
          <textarea v-model="noteContent" rows="5" placeholder="请输入行为处方内容..." class="note-textarea"></textarea>
        </div>
        <div class="modal-footer">
          <button class="act-btn act-secondary" @click="showNoteModal = false">取消</button>
          <button class="act-btn act-primary" :disabled="!noteContent.trim()" @click="submitNote">提交处方</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const students = ref<any[]>([])
const selectedId = ref<number | null>(null)
const selectedStudent = ref<any>(null)
const searchQ = ref('')
const activeTab = ref('概况')

const assignments = ref<any[]>([])
const assessmentLoading = ref(false)
const notes = ref<any[]>([])
const notesLoading = ref(false)

const showAssignModal = ref(false)
const selectedScales = ref<string[]>([])
const scales = [
  { key: 'ttm7', label: 'TTM行为阶段评估（7段）' },
  { key: 'big5', label: 'Big5人格量表' },
  { key: 'bpt6', label: '行为倾向测评' },
  { key: 'capacity', label: '营养行为能力' },
  { key: 'spi', label: '运动阶段指数' },
]

const showNoteModal = ref(false)
const noteContent = ref('')

const filteredStudents = computed(() => {
  if (!searchQ.value) return students.value
  const q = searchQ.value.toLowerCase()
  return students.value.filter(s => (s.name || s.full_name || '').toLowerCase().includes(q))
})

function riskClass(risk: any) {
  const n = parseInt(String(risk ?? '0').replace(/\D/g, '') || '0')
  if (n >= 4) return 'risk-r4'
  if (n === 3) return 'risk-r3'
  if (n === 2) return 'risk-r2'
  return 'risk-r1'
}

function selectStudent(s: any) {
  selectedId.value = s.id
  selectedStudent.value = s
  activeTab.value = '概况'
  assignments.value = []
  notes.value = []
}

watch(activeTab, async (tab) => {
  if (!selectedStudent.value) return
  if (tab === '评估' && assignments.value.length === 0) {
    assessmentLoading.value = true
    try {
      const res: any = await api.get(`/api/v1/assessment-assignments/coach-list?student_id=${selectedStudent.value.id}`)
      assignments.value = res.items || res || []
    } catch { assignments.value = [] }
    assessmentLoading.value = false
  }
  if (tab === '笔记' && notes.value.length === 0) {
    notesLoading.value = true
    try {
      const res: any = await api.get(`/api/v1/coach/students/${selectedStudent.value.id}/notes`)
      notes.value = res.items || res || []
    } catch { notes.value = [] }
    notesLoading.value = false
  }
})

function openAssignModal() { selectedScales.value = []; showAssignModal.value = true }
function openNoteModal() { noteContent.value = ''; showNoteModal.value = true }

async function submitAssign() {
  if (!selectedStudent.value || selectedScales.value.length === 0) return
  try {
    await api.post('/api/v1/assessment-assignments/assign', {
      student_id: selectedStudent.value.id,
      scale_ids: selectedScales.value,
    })
    showAssignModal.value = false
    alert('评估已分配')
  } catch (e: any) {
    alert(e.response?.data?.detail || '分配失败')
  }
}

async function submitNote() {
  if (!selectedStudent.value || !noteContent.value.trim()) return
  try {
    await api.post(`/api/v1/coach/students/${selectedStudent.value.id}/notes`, {
      content: '[行为处方] ' + noteContent.value.trim(),
    })
    showNoteModal.value = false
    alert('处方已提交')
  } catch (e: any) {
    alert(e.response?.data?.detail || '提交失败')
  }
}

onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/coach/dashboard')
    students.value = res.students || []
  } catch {
    try {
      const res: any = await api.get('/api/v1/coach/students')
      students.value = res.items || res || []
    } catch { students.value = [] }
  }
  loading.value = false
})
</script>

<style scoped>
.students-page { display: flex; gap: 16px; height: calc(100vh - 56px - 48px); }

.list-panel {
  width: 320px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header { padding: 16px; border-bottom: 1px solid #f3f4f6; }
.panel-header h2 { font-size: 15px; font-weight: 600; margin: 0 0 10px; }

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
}
.search-input:focus { border-color: #3b82f6; }

.student-rows { flex: 1; overflow-y: auto; }

.student-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f9fafb;
  transition: background 0.1s;
}
.student-row:hover { background: #f9fafb; }
.student-row.selected { background: #eff6ff; border-left: 3px solid #3b82f6; }

.s-avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #3b82f6);
  color: #fff; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.s-info { flex: 1; min-width: 0; }
.s-name { font-size: 14px; font-weight: 500; color: #111827; margin-bottom: 4px; }
.s-meta { display: flex; gap: 6px; }
.s-action-count { font-size: 11px; color: #9ca3af; white-space: nowrap; }

/* detail panel */
.detail-panel {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #9ca3af; }
.detail-empty-icon { font-size: 48px; margin-bottom: 12px; }
.detail-empty p { font-size: 14px; }

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-bottom: 1px solid #f3f4f6;
}

.detail-avatar {
  width: 52px; height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #3b82f6);
  color: #fff; font-size: 22px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.detail-info { flex: 1; }
.detail-info h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0 0 6px; }
.detail-tags { display: flex; gap: 8px; }

.detail-actions { display: flex; gap: 8px; }

.detail-tabs {
  display: flex;
  gap: 0;
  padding: 0 20px;
  border-bottom: 1px solid #f3f4f6;
}

.tab-btn {
  padding: 12px 16px;
  border: none;
  background: none;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.tab-btn.active { color: #3b82f6; border-bottom-color: #3b82f6; font-weight: 500; }

.detail-body { flex: 1; overflow-y: auto; padding: 20px; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item { background: #f9fafb; border-radius: 8px; padding: 12px; }
.info-k { font-size: 11px; color: #9ca3af; display: block; margin-bottom: 4px; }
.info-v { font-size: 15px; font-weight: 500; color: #111827; }

.list-item { padding: 12px; border-bottom: 1px solid #f3f4f6; }
.list-item:last-child { border-bottom: none; }
.li-title { font-size: 13px; color: #111827; margin-bottom: 4px; }
.li-meta { font-size: 11px; color: #9ca3af; }

/* tags */
.stage-tag { background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.risk-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.risk-r4 { background: #fee2e2; color: #dc2626; }
.risk-r3 { background: #ffedd5; color: #ea580c; }
.risk-r2 { background: #fef9c3; color: #ca8a04; }
.risk-r1 { background: #dcfce7; color: #16a34a; }

/* buttons */
.act-btn { padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; }
.act-primary { background: #3b82f6; color: #fff; }
.act-primary:hover { background: #2563eb; }
.act-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.act-secondary { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
.act-secondary:hover { background: #e5e7eb; }

/* modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
}
.modal {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 480px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-header h3 { font-size: 16px; font-weight: 600; margin: 0; }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #9ca3af; }
.modal-body { margin-bottom: 20px; }
.modal-footer { display: flex; gap: 8px; justify-content: flex-end; }

.checkbox-item { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f3f4f6; font-size: 14px; }
.checkbox-item:last-child { border-bottom: none; }

.note-textarea {
  width: 100%; padding: 10px; border: 1px solid #e5e7eb; border-radius: 8px;
  font-size: 14px; resize: vertical; outline: none; box-sizing: border-box;
}
.note-textarea:focus { border-color: #3b82f6; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 24px 0; }
</style>
