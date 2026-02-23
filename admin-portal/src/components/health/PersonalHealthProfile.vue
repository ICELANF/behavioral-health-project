<template>
  <div class="personal-health-profile" :class="{ embedded }">
    <!-- Page header (only when not embedded) -->
    <div v-if="!embedded" class="profile-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>个人健康档案</h2>
      <div class="header-actions">
        <button v-if="!editing" class="edit-btn" @click="editing = true">编辑</button>
        <button v-else class="save-btn" @click="saveProfile">保存</button>
        <button class="logout-btn" @click="doLogout">退出登录</button>
      </div>
    </div>

    <!-- Inline edit toggle (when embedded) -->
    <div v-if="embedded" class="embedded-toolbar">
      <h3 class="embedded-title">个人健康档案</h3>
      <button v-if="!editing" class="edit-btn" @click="editing = true">编辑</button>
      <button v-else class="save-btn" @click="saveProfile">保存</button>
    </div>

    <div class="profile-sections">
      <!-- Avatar Upload -->
      <div class="section-card avatar-section">
        <div class="avatar-upload-area" @click="triggerAvatarUpload">
          <div class="avatar-preview">
            <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" alt="头像" />
            <span v-else class="avatar-initials">{{ avatarInitials }}</span>
          </div>
          <div class="avatar-info">
            <div class="avatar-label">{{ avatarUrl ? '点击更换头像' : '点击上传头像' }}</div>
            <div class="avatar-hint">支持 JPG/PNG/WebP，最大 2MB</div>
          </div>
          <span class="avatar-edit-icon">📷</span>
        </div>
        <input
          ref="avatarInput"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          style="display:none"
          @change="handleAvatarFile"
        />
        <div v-if="avatarUploading" class="avatar-uploading">上传中...</div>
      </div>

      <!-- Basic Info -->
      <div class="section-card">
        <h3 class="section-title">基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>姓名</label>
            <input v-if="editing" v-model="profile.name" class="info-input" />
            <span v-else class="info-value">{{ profile.name }}</span>
          </div>
          <div class="info-item">
            <label>性别</label>
            <select v-if="editing" v-model="profile.gender" class="info-input">
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
            <span v-else class="info-value">{{ profile.gender === 'male' ? '男' : '女' }}</span>
          </div>
          <div class="info-item">
            <label>年龄</label>
            <input v-if="editing" v-model.number="profile.age" type="number" class="info-input" />
            <span v-else class="info-value">{{ profile.age }} 岁</span>
          </div>
          <div class="info-item">
            <label>身高</label>
            <input v-if="editing" v-model="profile.height" class="info-input" placeholder="cm" />
            <span v-else class="info-value">{{ profile.height }} cm</span>
          </div>
          <div class="info-item">
            <label>体重</label>
            <input v-if="editing" v-model="profile.weight" class="info-input" placeholder="kg" />
            <span v-else class="info-value">{{ profile.weight }} kg</span>
          </div>
          <div class="info-item">
            <label>BMI</label>
            <span class="info-value" :class="bmiClass">{{ bmiValue }} ({{ bmiLabel }})</span>
          </div>
        </div>
      </div>

      <!-- Medical History -->
      <div class="section-card">
        <h3 class="section-title">病程记录</h3>
        <div class="info-grid">
          <div class="info-item full">
            <label>主要诊断（最多5项）</label>
            <template v-if="editing">
              <div class="diag-list">
                <div v-for="(_, idx) in profile.diagnoses" :key="idx" class="diag-row">
                  <span class="diag-num">{{ idx + 1 }}.</span>
                  <select v-model="profile.diagnoses[idx]" class="info-input diag-select">
                    <option value="">请选择诊断</option>
                    <optgroup v-for="cat in diagnosisCategories" :key="cat.label" :label="cat.label">
                      <option v-for="d in cat.items" :key="d" :value="d" :disabled="profile.diagnoses.includes(d) && profile.diagnoses[idx] !== d">{{ d }}</option>
                    </optgroup>
                  </select>
                  <button v-if="profile.diagnoses[idx]" class="diag-clear" @click="profile.diagnoses[idx] = ''">×</button>
                </div>
                <div class="diag-row">
                  <span class="diag-num">✎</span>
                  <input
                    v-model="customDiagnosis"
                    class="info-input diag-select"
                    placeholder="手动填写其他诊断，回车添加"
                    @keydown.enter="addCustomDiagnosis"
                  />
                  <button class="diag-add-btn" :disabled="!customDiagnosis.trim()" @click="addCustomDiagnosis">+</button>
                </div>
              </div>
            </template>
            <template v-else>
              <div v-if="activeDiagnoses.length > 0" class="diag-tags-view">
                <span v-for="(d, i) in activeDiagnoses" :key="i" class="diag-tag-view">{{ d }}</span>
              </div>
              <span v-else class="info-value">暂无</span>
            </template>
          </div>
          <div class="info-item full">
            <label>确诊时间</label>
            <input v-if="editing" v-model="profile.diagnosisDate" type="date" class="info-input" />
            <span v-else class="info-value">{{ profile.diagnosisDate || '暂无' }}</span>
          </div>
          <div class="info-item full">
            <label>病史备注</label>
            <textarea v-if="editing" v-model="profile.medicalNotes" class="info-textarea" rows="3"></textarea>
            <span v-else class="info-value">{{ profile.medicalNotes || '暂无' }}</span>
          </div>
        </div>
      </div>

      <!-- Medications -->
      <div class="section-card">
        <h3 class="section-title">用药情况</h3>
        <div v-if="editing && recommendedMeds.length > 0" class="med-recommend">
          <p class="recommend-label">常用药物（点击快速添加）:</p>
          <div class="recommend-tags">
            <button
              v-for="rm in recommendedMeds"
              :key="rm.name"
              class="recommend-tag"
              :class="{ added: isMedAdded(rm.name) }"
              @click="quickAddMed(rm)"
            >
              {{ isMedAdded(rm.name) ? '✓ ' : '+ ' }}{{ rm.name }}
              <span class="recommend-dose">{{ rm.dosage }}</span>
            </button>
          </div>
        </div>
        <div v-for="(med, i) in profile.medications" :key="i" class="med-item">
          <template v-if="editing">
            <div class="med-edit-row">
              <input v-model="med.name" class="med-input" placeholder="药物名称" />
              <select v-model="med.dosage" class="med-input med-input-sm">
                <option value="">剂量</option>
                <option v-for="d in getDosageOptions(med.name)" :key="d" :value="d">{{ d }}</option>
              </select>
              <select v-model="med.frequency" class="med-input med-input-sm">
                <option value="">频次</option>
                <option v-for="f in frequencyOptions" :key="f" :value="f">{{ f }}</option>
              </select>
              <button class="remove-btn" @click="profile.medications.splice(i, 1)">×</button>
            </div>
          </template>
          <template v-else>
            <div class="med-info">
              <span class="med-name">{{ med.name }}</span>
              <span class="med-dosage">{{ med.dosage }}</span>
              <span class="med-freq">{{ med.frequency }}</span>
            </div>
          </template>
        </div>
        <button v-if="editing" class="add-btn" @click="addMedication">+ 手动添加药物</button>
        <p v-if="profile.medications.length === 0 && !editing" class="empty-text">暂无用药记录</p>
      </div>

      <!-- Allergies -->
      <div class="section-card">
        <h3 class="section-title">过敏史</h3>
        <div class="tags-wrapper">
          <span v-for="(allergy, i) in profile.allergies" :key="i" class="allergy-tag">
            {{ allergy }}
            <button v-if="editing" class="tag-remove" @click="profile.allergies.splice(i, 1)">×</button>
          </span>
          <input
            v-if="editing"
            v-model="newAllergy"
            class="tag-input"
            placeholder="输入后回车添加"
            @keydown.enter="addAllergy"
          />
        </div>
        <p v-if="profile.allergies.length === 0 && !editing" class="empty-text">暂无过敏记录</p>
      </div>

      <!-- Emergency Contact -->
      <div class="section-card">
        <h3 class="section-title">紧急联系人</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>姓名</label>
            <input v-if="editing" v-model="profile.emergencyContact.name" class="info-input" />
            <span v-else class="info-value">{{ profile.emergencyContact.name || '暂无' }}</span>
          </div>
          <div class="info-item">
            <label>关系</label>
            <input v-if="editing" v-model="profile.emergencyContact.relation" class="info-input" />
            <span v-else class="info-value">{{ profile.emergencyContact.relation || '暂无' }}</span>
          </div>
          <div class="info-item">
            <label>电话</label>
            <input v-if="editing" v-model="profile.emergencyContact.phone" class="info-input" />
            <span v-else class="info-value">{{ profile.emergencyContact.phone || '暂无' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { profileApi } from '@/api/index'
import request from '@/api/request'
import { message } from 'ant-design-vue'
import { useCurrentUser } from '@/composables/useCurrentUser'

const props = defineProps({
  embedded: { type: Boolean, default: true }
})

const { handleLogout } = useCurrentUser()
const doLogout = () => handleLogout()

const editing = ref(false)
const newAllergy = ref('')
const loading = ref(true)
const customDiagnosis = ref('')

// ═══════════════════════════════════════════════════
// 头像上传
// ═══════════════════════════════════════════════════
const avatarUrl = ref(localStorage.getItem('admin_avatar') || '')
const avatarUploading = ref(false)
const avatarInput = ref(null)

const avatarInitials = computed(() => {
  const name = localStorage.getItem('admin_name') || localStorage.getItem('admin_username') || ''
  return name.length > 2 ? name.slice(-2) : name || '?'
})

function triggerAvatarUpload() {
  if (avatarInput.value) avatarInput.value.click()
}

async function handleAvatarFile(e) {
  const file = e.target.files?.[0]
  if (!file) return

  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    message.error('仅支持 JPG/PNG/WebP 格式')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    message.error('文件过大，最大 2MB')
    return
  }

  avatarUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await request.post('/v1/upload/avatar', formData)
    const url = res.data?.url || ''
    if (url) {
      avatarUrl.value = url
      localStorage.setItem('admin_avatar', url)
      message.success('头像更新成功')
    }
  } catch (err) {
    const msg = err?.response?.data?.detail || '头像上传失败'
    message.error(msg)
  } finally {
    avatarUploading.value = false
    if (avatarInput.value) avatarInput.value.value = ''
  }
}

// ═══════════════════════════════════════════════════
// 诊断分类 (代谢性 + 循环系统 + 中医骨科)
// ═══════════════════════════════════════════════════
const diagnosisCategories = [
  {
    label: '代谢性疾病',
    items: [
      '2型糖尿病', '高脂血症', '痛风', '甲状腺功能减退',
      '代谢综合征', '肥胖症', '1型糖尿病',
    ],
  },
  {
    label: '循环系统疾病',
    items: [
      '高血压', '冠心病', '心房颤动', '慢性心力衰竭',
      '动脉粥样硬化', '脑卒中后遗症', '外周动脉疾病',
    ],
  },
  {
    label: '中医骨科疾病',
    items: [
      '颈椎病', '腰椎间盘突出症', '膝骨关节炎',
      '肩周炎', '骨质疏松症', '类风湿关节炎', '强直性脊柱炎',
    ],
  },
]

// ═══════════════════════════════════════════════════
// 诊断→常用药物映射
// ═══════════════════════════════════════════════════
const diagnosisMedMap = {
  '2型糖尿病': [
    { name: '二甲双胍', dosage: '500mg/次', frequency: '每日2次' },
    { name: '格列美脲', dosage: '2mg/次', frequency: '每日1次' },
    { name: '阿卡波糖', dosage: '50mg/次', frequency: '每日3次' },
    { name: '西格列汀', dosage: '100mg/次', frequency: '每日1次' },
    { name: '达格列净', dosage: '10mg/次', frequency: '每日1次' },
  ],
  '1型糖尿病': [
    { name: '门冬胰岛素', dosage: '遵医嘱', frequency: '餐前注射' },
    { name: '甘精胰岛素', dosage: '遵医嘱', frequency: '每日1次' },
  ],
  '高脂血症': [
    { name: '阿托伐他汀', dosage: '20mg/次', frequency: '每日1次' },
    { name: '瑞舒伐他汀', dosage: '10mg/次', frequency: '每日1次' },
    { name: '非诺贝特', dosage: '200mg/次', frequency: '每日1次' },
    { name: '依折麦布', dosage: '10mg/次', frequency: '每日1次' },
  ],
  '痛风': [
    { name: '别嘌醇', dosage: '100mg/次', frequency: '每日1次' },
    { name: '非布司他', dosage: '40mg/次', frequency: '每日1次' },
    { name: '秋水仙碱', dosage: '0.5mg/次', frequency: '每日2次' },
    { name: '苯溴马隆', dosage: '50mg/次', frequency: '每日1次' },
  ],
  '甲状腺功能减退': [
    { name: '左甲状腺素钠', dosage: '50μg/次', frequency: '每日1次(空腹)' },
  ],
  '代谢综合征': [
    { name: '二甲双胍', dosage: '500mg/次', frequency: '每日2次' },
    { name: '阿托伐他汀', dosage: '10mg/次', frequency: '每日1次' },
    { name: '奥利司他', dosage: '120mg/次', frequency: '每日3次(餐时)' },
  ],
  '肥胖症': [
    { name: '奥利司他', dosage: '120mg/次', frequency: '每日3次(餐时)' },
    { name: '司美格鲁肽', dosage: '遵医嘱', frequency: '每周1次' },
  ],
  '高血压': [
    { name: '氨氯地平', dosage: '5mg/次', frequency: '每日1次' },
    { name: '缬沙坦', dosage: '80mg/次', frequency: '每日1次' },
    { name: '美托洛尔', dosage: '25mg/次', frequency: '每日2次' },
    { name: '氢氯噻嗪', dosage: '12.5mg/次', frequency: '每日1次' },
    { name: '依那普利', dosage: '10mg/次', frequency: '每日1次' },
  ],
  '冠心病': [
    { name: '阿司匹林', dosage: '100mg/次', frequency: '每日1次' },
    { name: '氯吡格雷', dosage: '75mg/次', frequency: '每日1次' },
    { name: '硝酸甘油', dosage: '0.5mg/次', frequency: '必要时舌下含服' },
    { name: '阿托伐他汀', dosage: '20mg/次', frequency: '每日1次' },
    { name: '美托洛尔', dosage: '25mg/次', frequency: '每日2次' },
  ],
  '心房颤动': [
    { name: '华法林', dosage: '遵医嘱(INR监测)', frequency: '每日1次' },
    { name: '利伐沙班', dosage: '20mg/次', frequency: '每日1次' },
    { name: '胺碘酮', dosage: '200mg/次', frequency: '每日1-3次' },
    { name: '美托洛尔', dosage: '25mg/次', frequency: '每日2次' },
  ],
  '慢性心力衰竭': [
    { name: '沙库巴曲缬沙坦', dosage: '50mg/次', frequency: '每日2次' },
    { name: '比索洛尔', dosage: '2.5mg/次', frequency: '每日1次' },
    { name: '螺内酯', dosage: '20mg/次', frequency: '每日1次' },
    { name: '达格列净', dosage: '10mg/次', frequency: '每日1次' },
  ],
  '动脉粥样硬化': [
    { name: '阿司匹林', dosage: '100mg/次', frequency: '每日1次' },
    { name: '阿托伐他汀', dosage: '20mg/次', frequency: '每日1次' },
  ],
  '脑卒中后遗症': [
    { name: '阿司匹林', dosage: '100mg/次', frequency: '每日1次' },
    { name: '氯吡格雷', dosage: '75mg/次', frequency: '每日1次' },
    { name: '阿托伐他汀', dosage: '20mg/次', frequency: '每日1次' },
  ],
  '外周动脉疾病': [
    { name: '阿司匹林', dosage: '100mg/次', frequency: '每日1次' },
    { name: '西洛他唑', dosage: '100mg/次', frequency: '每日2次' },
  ],
  '颈椎病': [
    { name: '塞来昔布', dosage: '200mg/次', frequency: '每日1次' },
    { name: '甲钴胺', dosage: '0.5mg/次', frequency: '每日3次' },
    { name: '独活寄生丸', dosage: '1丸/次', frequency: '每日2次' },
    { name: '颈复康颗粒', dosage: '1袋/次', frequency: '每日2次' },
  ],
  '腰椎间盘突出症': [
    { name: '双氯芬酸钠', dosage: '75mg/次', frequency: '每日1次' },
    { name: '甲钴胺', dosage: '0.5mg/次', frequency: '每日3次' },
    { name: '腰痛宁胶囊', dosage: '4粒/次', frequency: '每日1次' },
    { name: '活血止痛胶囊', dosage: '4粒/次', frequency: '每日2次' },
  ],
  '膝骨关节炎': [
    { name: '氨基葡萄糖', dosage: '750mg/次', frequency: '每日2次' },
    { name: '塞来昔布', dosage: '200mg/次', frequency: '每日1次' },
    { name: '硫酸软骨素', dosage: '400mg/次', frequency: '每日3次' },
    { name: '仙灵骨葆胶囊', dosage: '3粒/次', frequency: '每日2次' },
  ],
  '肩周炎': [
    { name: '布洛芬', dosage: '400mg/次', frequency: '每日3次' },
    { name: '舒筋活血片', dosage: '4片/次', frequency: '每日3次' },
  ],
  '骨质疏松症': [
    { name: '碳酸钙D3', dosage: '600mg/次', frequency: '每日1次' },
    { name: '阿仑膦酸钠', dosage: '70mg/次', frequency: '每周1次' },
    { name: '骨化三醇', dosage: '0.25μg/次', frequency: '每日1次' },
    { name: '仙灵骨葆胶囊', dosage: '3粒/次', frequency: '每日2次' },
  ],
  '类风湿关节炎': [
    { name: '甲氨蝶呤', dosage: '10mg/次', frequency: '每周1次' },
    { name: '来氟米特', dosage: '20mg/次', frequency: '每日1次' },
    { name: '塞来昔布', dosage: '200mg/次', frequency: '每日1次' },
    { name: '雷公藤多苷', dosage: '20mg/次', frequency: '每日3次' },
  ],
  '强直性脊柱炎': [
    { name: '柳氮磺吡啶', dosage: '1g/次', frequency: '每日2次' },
    { name: '塞来昔布', dosage: '200mg/次', frequency: '每日1次' },
    { name: '甲氨蝶呤', dosage: '10mg/次', frequency: '每周1次' },
  ],
}

const profile = reactive({
  name: '',
  gender: 'male',
  age: 0,
  height: '',
  weight: '',
  diagnoses: ['', '', '', '', ''],
  diagnosisDate: '',
  medicalNotes: '',
  medications: [],
  allergies: [],
  emergencyContact: { name: '', relation: '', phone: '' },
})

const activeDiagnoses = computed(() => profile.diagnoses.filter(d => d))

function addCustomDiagnosis() {
  const val = customDiagnosis.value.trim()
  if (!val) return
  const idx = profile.diagnoses.findIndex(d => !d)
  if (idx === -1) {
    message.warning('最多只能添加5项诊断')
    return
  }
  profile.diagnoses[idx] = val
  customDiagnosis.value = ''
}

const recommendedMeds = computed(() => {
  const seen = new Set()
  const result = []
  for (const diag of activeDiagnoses.value) {
    const meds = diagnosisMedMap[diag] || []
    for (const m of meds) {
      if (!seen.has(m.name)) {
        seen.add(m.name)
        result.push(m)
      }
    }
  }
  return result
})

function isMedAdded(name) {
  return profile.medications.some(m => m.name === name)
}

function quickAddMed(rm) {
  if (isMedAdded(rm.name)) {
    profile.medications = profile.medications.filter(m => m.name !== rm.name)
  } else {
    profile.medications.push({ ...rm })
  }
}

// ═══════════════════════════════════════════════════
// 用药剂量选项
// ═══════════════════════════════════════════════════
const medDosageMap = {
  '二甲双胍': ['250mg', '500mg', '850mg', '1000mg'],
  '格列美脲': ['1mg', '2mg', '4mg'],
  '阿卡波糖': ['25mg', '50mg', '100mg'],
  '西格列汀': ['25mg', '50mg', '100mg'],
  '达格列净': ['5mg', '10mg'],
  '门冬胰岛素': ['遵医嘱', '4IU', '6IU', '8IU', '10IU'],
  '甘精胰岛素': ['遵医嘱', '10IU', '14IU', '18IU', '22IU'],
  '阿托伐他汀': ['10mg', '20mg', '40mg'],
  '瑞舒伐他汀': ['5mg', '10mg', '20mg'],
  '非诺贝特': ['160mg', '200mg'],
  '依折麦布': ['10mg'],
  '别嘌醇': ['50mg', '100mg', '200mg', '300mg'],
  '非布司他': ['20mg', '40mg', '80mg'],
  '秋水仙碱': ['0.5mg'],
  '苯溴马隆': ['25mg', '50mg'],
  '左甲状腺素钠': ['25μg', '50μg', '75μg', '100μg'],
  '奥利司他': ['60mg', '120mg'],
  '司美格鲁肽': ['0.25mg', '0.5mg', '1.0mg', '2.4mg'],
  '氨氯地平': ['2.5mg', '5mg', '10mg'],
  '缬沙坦': ['40mg', '80mg', '160mg'],
  '美托洛尔': ['12.5mg', '25mg', '47.5mg', '50mg'],
  '氢氯噻嗪': ['12.5mg', '25mg'],
  '依那普利': ['5mg', '10mg', '20mg'],
  '阿司匹林': ['75mg', '100mg'],
  '氯吡格雷': ['75mg'],
  '硝酸甘油': ['0.3mg', '0.5mg'],
  '华法林': ['遵医嘱', '1mg', '2mg', '2.5mg', '3mg', '5mg'],
  '利伐沙班': ['10mg', '15mg', '20mg'],
  '胺碘酮': ['200mg'],
  '沙库巴曲缬沙坦': ['25mg', '50mg', '100mg', '200mg'],
  '比索洛尔': ['1.25mg', '2.5mg', '5mg', '10mg'],
  '螺内酯': ['20mg', '40mg'],
  '西洛他唑': ['50mg', '100mg'],
  '塞来昔布': ['100mg', '200mg'],
  '甲钴胺': ['0.5mg'],
  '独活寄生丸': ['1丸'],
  '颈复康颗粒': ['1袋'],
  '双氯芬酸钠': ['25mg', '50mg', '75mg'],
  '腰痛宁胶囊': ['4粒'],
  '活血止痛胶囊': ['4粒'],
  '氨基葡萄糖': ['250mg', '500mg', '750mg'],
  '硫酸软骨素': ['200mg', '400mg'],
  '仙灵骨葆胶囊': ['3粒'],
  '布洛芬': ['200mg', '400mg', '600mg'],
  '舒筋活血片': ['4片'],
  '碳酸钙D3': ['600mg'],
  '阿仑膦酸钠': ['70mg'],
  '骨化三醇': ['0.25μg', '0.5μg'],
  '甲氨蝶呤': ['7.5mg', '10mg', '15mg'],
  '来氟米特': ['10mg', '20mg'],
  '雷公藤多苷': ['10mg', '20mg'],
  '柳氮磺吡啶': ['0.5g', '1g'],
}

function getDosageOptions(medName) {
  if (!medName) return ['遵医嘱']
  return medDosageMap[medName] || ['遵医嘱', '5mg', '10mg', '25mg', '50mg', '100mg', '200mg', '500mg']
}

const frequencyOptions = ['每日1次', '每日2次', '每日3次', '每日4次', '每周1次', '必要时', '遵医嘱']

async function loadProfile() {
  loading.value = true
  try {
    const data = await profileApi.getProfile()
    if (data) {
      profile.name = data.display_name || data.name || data.username || ''
      profile.gender = data.gender || 'male'
      profile.age = data.age ?? 0
      profile.height = String(data.height ?? '')
      profile.weight = String(data.weight ?? '')
      const rawDiag = data.diagnoses || data.diagnosis || data.primary_diagnosis || ''
      if (Array.isArray(rawDiag)) {
        for (let i = 0; i < 5; i++) profile.diagnoses[i] = rawDiag[i] || ''
      } else if (rawDiag) {
        profile.diagnoses[0] = rawDiag
        for (let i = 1; i < 5; i++) profile.diagnoses[i] = ''
      }
      profile.diagnosisDate = data.diagnosis_date || data.diagnosisDate || ''
      profile.medicalNotes = data.medical_notes || data.medicalNotes || ''
      if (Array.isArray(data.medications)) profile.medications = data.medications
      if (Array.isArray(data.allergies)) profile.allergies = data.allergies
      if (data.emergency_contact || data.emergencyContact) {
        const ec = data.emergency_contact || data.emergencyContact
        profile.emergencyContact.name = ec.name || ''
        profile.emergencyContact.relation = ec.relation || ''
        profile.emergencyContact.phone = ec.phone || ''
      }
      if (data.avatar_url) {
        avatarUrl.value = data.avatar_url
        localStorage.setItem('admin_avatar', data.avatar_url)
      }
    }
  } catch (e) {
    console.error('加载个人档案失败:', e)
  }
  loading.value = false
}

onMounted(loadProfile)

const bmiValue = computed(() => {
  const h = parseFloat(profile.height) / 100
  const w = parseFloat(profile.weight)
  if (!h || !w) return '--'
  return (w / (h * h)).toFixed(1)
})

const bmiLabel = computed(() => {
  const v = parseFloat(bmiValue.value)
  if (isNaN(v)) return ''
  if (v < 18.5) return '偏瘦'
  if (v < 24) return '正常'
  if (v < 28) return '偏胖'
  return '肥胖'
})

const bmiClass = computed(() => {
  const v = parseFloat(bmiValue.value)
  if (isNaN(v)) return ''
  if (v < 18.5 || v >= 28) return 'text-red'
  if (v >= 24) return 'text-yellow'
  return 'text-green'
})

const addMedication = () => {
  profile.medications.push({ name: '', dosage: '', frequency: '' })
}

const addAllergy = () => {
  const val = newAllergy.value.trim()
  if (val && !profile.allergies.includes(val)) {
    profile.allergies.push(val)
    newAllergy.value = ''
  }
}

const saveProfile = async () => {
  try {
    const diagArr = profile.diagnoses.filter(d => d)
    await profileApi.updateProfile({
      display_name: profile.name || undefined,
      gender: profile.gender || undefined,
      age: profile.age || undefined,
      height: profile.height || undefined,
      weight: profile.weight || undefined,
      diagnosis: diagArr[0] || undefined,
      diagnoses: diagArr.length > 0 ? diagArr : undefined,
      diagnosis_date: profile.diagnosisDate || undefined,
      medical_notes: profile.medicalNotes || undefined,
      medications: profile.medications.filter(m => m.name),
      allergies: profile.allergies,
      emergency_contact: (profile.emergencyContact.name || profile.emergencyContact.phone)
        ? profile.emergencyContact : undefined,
    })
    message.success('保存成功')
  } catch (e) {
    console.warn('Failed to save profile', e)
    message.error('保存失败')
  }
  editing.value = false
}
</script>

<style scoped>
.personal-health-profile { max-width: 600px; margin: 0 auto; padding: 16px; }
.personal-health-profile.embedded { max-width: 900px; }

.profile-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.profile-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn, .edit-btn, .save-btn, .logout-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; font-size: 14px; }
.save-btn { background: #1890ff; color: #fff; border-color: #1890ff; }
.logout-btn { background: #fff; color: #dc2626; border-color: #dc2626; }
.logout-btn:hover { background: #fef2f2; }
.header-actions { display: flex; gap: 8px; }

.embedded-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.embedded-title { font-size: 16px; font-weight: 600; margin: 0; color: #111827; }

.section-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.section-title { font-size: 15px; font-weight: 600; margin: 0 0 12px; color: #333; border-bottom: 1px solid #f5f5f5; padding-bottom: 8px; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-item.full { grid-column: 1 / -1; }
.info-item label { font-size: 12px; color: #999; }
.info-value { font-size: 14px; color: #333; }
.info-input, .info-textarea { padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px; width: 100%; box-sizing: border-box; }
.info-textarea { resize: vertical; }

/* Medication section */
.med-recommend { margin-bottom: 12px; padding: 10px; background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 6px; }
.recommend-label { font-size: 12px; color: #52c41a; font-weight: 500; margin: 0 0 8px; }
.recommend-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.recommend-tag { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border: 1px solid #b7eb8f; border-radius: 14px; background: #fff; cursor: pointer; font-size: 12px; color: #389e0d; transition: all 0.2s; }
.recommend-tag:hover { background: #f6ffed; border-color: #52c41a; }
.recommend-tag.added { background: #52c41a; color: #fff; border-color: #52c41a; }
.recommend-dose { font-size: 11px; color: inherit; opacity: 0.7; }

.med-item { margin-bottom: 6px; }
.med-edit-row { display: flex; gap: 6px; align-items: center; }
.med-input { padding: 6px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; flex: 1; min-width: 0; }
.med-input-sm { flex: 0.6; }
.med-info { display: flex; gap: 12px; font-size: 13px; padding: 8px; background: #fafafa; border-radius: 4px; }
.med-name { font-weight: 500; color: #333; }
.med-dosage { color: #1890ff; }
.med-freq { color: #999; }
.remove-btn { width: 24px; height: 24px; border: none; background: #ff4d4f; color: #fff; border-radius: 50%; cursor: pointer; flex-shrink: 0; font-size: 14px; }
.add-btn { width: 100%; padding: 6px; border: 1px dashed #d9d9d9; border-radius: 4px; background: none; cursor: pointer; color: #1890ff; margin-top: 4px; }

.tags-wrapper { display: flex; flex-wrap: wrap; gap: 6px; }
.allergy-tag { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: #fff1f0; color: #cf1322; border-radius: 4px; font-size: 13px; }
.tag-remove { border: none; background: none; color: #cf1322; cursor: pointer; font-size: 14px; padding: 0; }
.tag-input { padding: 4px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; min-width: 140px; }

.empty-text { color: #ccc; font-size: 13px; text-align: center; padding: 8px 0; }
.text-red { color: #cf1322; }
.text-yellow { color: #d4b106; }
.text-green { color: #389e0d; }

/* Diagnosis multi-row */
.diag-list { display: flex; flex-direction: column; gap: 6px; }
.diag-row { display: flex; align-items: center; gap: 6px; }
.diag-num { width: 20px; font-size: 13px; color: #999; text-align: center; flex-shrink: 0; }
.diag-select { flex: 1; min-width: 0; }
.diag-clear { width: 24px; height: 24px; border: none; background: #ff4d4f; color: #fff; border-radius: 50%; cursor: pointer; flex-shrink: 0; font-size: 14px; line-height: 1; }
.diag-add-btn { padding: 4px 12px; border: 1px solid #1890ff; background: #e6f7ff; color: #1890ff; border-radius: 4px; cursor: pointer; flex-shrink: 0; font-size: 16px; }
.diag-add-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.diag-tags-view { display: flex; flex-wrap: wrap; gap: 6px; }
.diag-tag-view { display: inline-block; padding: 3px 10px; background: #f0f5ff; color: #1d39c4; border: 1px solid #adc6ff; border-radius: 4px; font-size: 13px; }

/* Avatar */
.avatar-section { padding: 16px; }
.avatar-upload-area {
  display: flex; align-items: center; gap: 16px;
  cursor: pointer; padding: 8px; border-radius: 12px; transition: background 0.2s;
}
.avatar-upload-area:hover { background: #f5f5f5; }
.avatar-preview {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; overflow: hidden; border: 3px solid #e5e7eb;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-initials { color: #fff; font-size: 24px; font-weight: 700; }
.avatar-info { flex: 1; }
.avatar-label { font-size: 15px; font-weight: 600; color: #1f2937; margin-bottom: 4px; }
.avatar-hint { font-size: 12px; color: #9ca3af; }
.avatar-edit-icon { font-size: 20px; opacity: 0.5; }
.avatar-uploading { text-align: center; padding: 8px; font-size: 13px; color: #6b7280; }
</style>
