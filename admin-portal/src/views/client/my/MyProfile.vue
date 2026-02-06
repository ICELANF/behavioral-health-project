<template>
  <div class="my-profile">
    <div class="profile-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>个人健康档案</h2>
      <button v-if="!editing" class="edit-btn" @click="editing = true">编辑</button>
      <button v-else class="save-btn" @click="saveProfile">保存</button>
    </div>

    <div class="profile-sections">
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
            <label>主要诊断</label>
            <input v-if="editing" v-model="profile.diagnosis" class="info-input" />
            <span v-else class="info-value">{{ profile.diagnosis || '暂无' }}</span>
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
        <div v-for="(med, i) in profile.medications" :key="i" class="med-item">
          <div class="med-info">
            <span class="med-name">{{ med.name }}</span>
            <span class="med-dosage">{{ med.dosage }}</span>
            <span class="med-freq">{{ med.frequency }}</span>
          </div>
          <button v-if="editing" class="remove-btn" @click="profile.medications.splice(i, 1)">×</button>
        </div>
        <button v-if="editing" class="add-btn" @click="addMedication">+ 添加药物</button>
        <p v-if="profile.medications.length === 0" class="empty-text">暂无用药记录</p>
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
import { ref, reactive, computed } from 'vue'

const editing = ref(false)
const newAllergy = ref('')

const profile = reactive({
  name: '张三',
  gender: 'male',
  age: 45,
  height: '172',
  weight: '78',
  diagnosis: '2型糖尿病',
  diagnosisDate: '2023-06-15',
  medicalNotes: '空腹血糖偏高，HbA1c 7.2%，合并轻度高血压',
  medications: [
    { name: '二甲双胍', dosage: '500mg', frequency: '每日两次' },
    { name: '氨氯地平', dosage: '5mg', frequency: '每日一次' },
  ],
  allergies: ['青霉素', '磺胺类'],
  emergencyContact: { name: '李四', relation: '配偶', phone: '13800138000' },
})

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

const saveProfile = () => {
  editing.value = false
  // Would call API to save
}
</script>

<style scoped>
.my-profile { max-width: 600px; margin: 0 auto; padding: 16px; }
.profile-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.profile-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn, .edit-btn, .save-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; font-size: 14px; }
.save-btn { background: #1890ff; color: #fff; border-color: #1890ff; }

.section-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.section-title { font-size: 15px; font-weight: 600; margin: 0 0 12px; color: #333; border-bottom: 1px solid #f5f5f5; padding-bottom: 8px; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-item.full { grid-column: 1 / -1; }
.info-item label { font-size: 12px; color: #999; }
.info-value { font-size: 14px; color: #333; }
.info-input, .info-textarea { padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px; }
.info-textarea { resize: vertical; }

.med-item { display: flex; align-items: center; justify-content: space-between; padding: 8px; background: #fafafa; border-radius: 4px; margin-bottom: 4px; }
.med-info { display: flex; gap: 12px; font-size: 13px; }
.med-name { font-weight: 500; color: #333; }
.med-dosage { color: #1890ff; }
.med-freq { color: #999; }
.remove-btn { width: 24px; height: 24px; border: none; background: #ff4d4f; color: #fff; border-radius: 50%; cursor: pointer; }
.add-btn { width: 100%; padding: 6px; border: 1px dashed #d9d9d9; border-radius: 4px; background: none; cursor: pointer; color: #1890ff; margin-top: 4px; }

.tags-wrapper { display: flex; flex-wrap: wrap; gap: 6px; }
.allergy-tag { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: #fff1f0; color: #cf1322; border-radius: 4px; font-size: 13px; }
.tag-remove { border: none; background: none; color: #cf1322; cursor: pointer; font-size: 14px; padding: 0; }
.tag-input { padding: 4px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; min-width: 140px; }

.empty-text { color: #ccc; font-size: 13px; text-align: center; padding: 8px 0; }
.text-red { color: #cf1322; }
.text-yellow { color: #d4b106; }
.text-green { color: #389e0d; }
</style>
