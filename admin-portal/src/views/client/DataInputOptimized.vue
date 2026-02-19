<template>
  <div class="data-input-optimized">
    <!-- 导航栏 -->
    <div class="nav-header">
      <div class="nav-back" @click="goBack">
        <LeftOutlined />
      </div>
      <h1 class="nav-title">记录数据</h1>
      <div class="nav-right"></div>
    </div>

    <!-- 步骤1：选择数据类型 -->
    <div v-if="step === 1" class="step-container">
      <div class="step-content">
        <div class="step-header">
          <div class="step-title">📝 要记录什么？</div>
          <div class="step-subtitle">选择一种数据类型开始记录</div>
        </div>

        <div class="data-type-grid">
          <div
            v-for="type in dataTypes"
            :key="type.id"
            class="type-card"
            :class="{ selected: selectedType === type.id }"
            @click="selectType(type)"
          >
            <div class="type-icon">{{ type.icon }}</div>
            <div class="type-info">
              <div class="type-name">{{ type.name }}</div>
              <div class="type-desc">{{ type.desc }}</div>
            </div>
            <div class="type-check" v-if="selectedType === type.id">
              <CheckCircleFilled />
            </div>
          </div>
        </div>
      </div>

      <div class="step-footer">
        <a-button
          type="primary"
          size="large"
          block
          :disabled="!selectedType"
          @click="goToInput"
        >
          下一步
        </a-button>
      </div>
    </div>

    <!-- 步骤2：输入数据 -->
    <div v-if="step === 2" class="step-container">
      <div class="step-content">
        <!-- 血糖输入 - 使用 BigNumberInput 组件 -->
        <div v-if="selectedType === 'glucose'" class="input-section">
          <!-- 测量时间快捷选择 -->
          <div class="quick-options">
            <div class="option-label">测量时间</div>
            <div class="option-buttons">
              <div
                v-for="option in glucoseTimeOptions"
                :key="option.value"
                class="option-btn"
                :class="{ active: inputData.glucoseTime === option.value }"
                @click="inputData.glucoseTime = option.value"
              >
                {{ option.label }}
              </div>
            </div>
          </div>

          <BigNumberInput
            v-model="inputData.glucoseValue"
            label="血糖值"
            subtitle="输入您的血糖测量结果"
            icon="🩸"
            unit="mmol/L"
            :step="0.1"
            :hint="historicalAverage.glucose ? `您近7天的平均值是 <strong>${historicalAverage.glucose}</strong> mmol/L` : ''"
            :historical-value="parseFloat(historicalAverage.glucose)"
            :quick-values="[5.0, 5.5, 6.0, 6.5, 7.0]"
          />
        </div>

        <!-- 体重输入 - 使用 BigNumberInput 组件 -->
        <div v-if="selectedType === 'weight'" class="input-section">
          <BigNumberInput
            v-model="inputData.weightValue"
            label="体重"
            subtitle="输入您今天的体重"
            icon="⚖️"
            unit="kg"
            :step="0.1"
            :hint="historicalAverage.weight ? `上次记录：<strong>${historicalAverage.weight}</strong> kg ${weightTrend}` : ''"
            :historical-value="parseFloat(historicalAverage.weight)"
            :quick-values="[70.0, 72.5, 75.0, 77.5, 80.0]"
          />
        </div>

        <!-- 血压输入 -->
        <div v-if="selectedType === 'bloodPressure'" class="input-section">
          <div class="input-header">
            <div class="input-icon">💓</div>
            <div>
              <div class="input-title">血压</div>
              <div class="input-subtitle">输入收缩压和舒张压</div>
            </div>
          </div>

          <div class="double-input">
            <div class="half-input">
              <div class="big-input-label">收缩压 (高压)</div>
              <a-input
                v-model:value="inputData.systolic"
                size="large"
                placeholder="120"
                class="big-number-input"
                type="number"
              />
              <div class="input-unit">mmHg</div>
            </div>
            <div class="half-input">
              <div class="big-input-label">舒张压 (低压)</div>
              <a-input
                v-model:value="inputData.diastolic"
                size="large"
                placeholder="80"
                class="big-number-input"
                type="number"
              />
              <div class="input-unit">mmHg</div>
            </div>
          </div>
        </div>

        <!-- 运动输入 - 使用 BigNumberInput 组件 -->
        <div v-if="selectedType === 'exercise'" class="input-section">
          <div class="quick-options">
            <div class="option-label">运动类型</div>
            <div class="option-buttons">
              <div
                v-for="option in exerciseTypeOptions"
                :key="option.value"
                class="option-btn"
                :class="{ active: inputData.exerciseType === option.value }"
                @click="inputData.exerciseType = option.value"
              >
                {{ option.icon }} {{ option.label }}
              </div>
            </div>
          </div>

          <BigNumberInput
            v-model="inputData.exerciseDuration"
            label="运动时长"
            subtitle="记录今天的运动"
            icon="🏃"
            unit="分钟"
            :step="1"
            placeholder="30"
            :hint="`建议每天运动 <strong>30</strong> 分钟以上`"
            :quick-values="[15, 30, 45, 60, 90]"
          />
        </div>

        <!-- 心情输入 -->
        <div v-if="selectedType === 'mood'" class="input-section">
          <div class="input-header">
            <div class="input-icon">😊</div>
            <div>
              <div class="input-title">心情日记</div>
              <div class="input-subtitle">记录今天的心情和感受</div>
            </div>
          </div>

          <div class="mood-selector">
            <div class="mood-label">今天感觉怎么样？</div>
            <div class="mood-options">
              <div
                v-for="mood in moodOptions"
                :key="mood.value"
                class="mood-item"
                :class="{ active: inputData.moodLevel === mood.value }"
                @click="inputData.moodLevel = mood.value"
              >
                <div class="mood-emoji">{{ mood.emoji }}</div>
                <div class="mood-label-text">{{ mood.label }}</div>
              </div>
            </div>
          </div>

          <div class="mood-note">
            <div class="note-label">补充说明（选填）</div>
            <a-textarea
              v-model:value="inputData.moodNote"
              placeholder="说说今天发生了什么..."
              :rows="4"
              :maxlength="200"
            />
          </div>
        </div>

        <!-- 饮食输入 -->
        <div v-if="selectedType === 'meal'" class="input-section">
          <div class="input-header">
            <div class="input-icon">🍽️</div>
            <div>
              <div class="input-title">饮食记录</div>
              <div class="input-subtitle">记录今天吃了什么</div>
            </div>
          </div>

          <div class="meal-input">
            <a-textarea
              v-model:value="inputData.mealDescription"
              placeholder="描述今天的饮食..."
              :rows="6"
              :maxlength="300"
            />
          </div>
        </div>
      </div>

      <div class="step-footer">
        <a-button size="large" @click="step = 1" class="back-btn">
          返回
        </a-button>
        <a-button
          type="primary"
          size="large"
          :disabled="!isInputValid"
          @click="submitData"
          class="submit-btn"
        >
          提交
        </a-button>
      </div>
    </div>

    <!-- 步骤3：查看反馈 -->
    <div v-if="step === 3" class="step-container">
      <div class="success-content">
        <div class="success-icon">✅</div>
        <div class="success-title">提交成功！</div>
        <div class="success-subtitle">数据已成功记录</div>

        <!-- 趋势对比卡片 -->
        <div v-if="trendData" class="trend-card">
          <div class="trend-header">
            <div class="trend-title">数据对比</div>
          </div>
          <div class="trend-content">
            <div class="trend-item">
              <div class="trend-label">本次数值</div>
              <div class="trend-value current">{{ trendData.current }}</div>
            </div>
            <div class="trend-divider">vs</div>
            <div class="trend-item">
              <div class="trend-label">平均值</div>
              <div class="trend-value average">{{ trendData.average }}</div>
            </div>
          </div>
          <div class="trend-status">
            {{ trendData.statusText }}
          </div>
        </div>

        <div class="action-buttons">
          <a-button size="large" @click="continueRecord" block>
            继续记录
          </a-button>
          <a-button type="primary" size="large" @click="goToProgress" block>
            查看进展
            <ArrowRightOutlined />
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LeftOutlined,
  CheckCircleFilled,
  ArrowRightOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { healthApi } from '@/api/health'
import { BigNumberInput } from '@/components/health'

const router = useRouter()

// patientId no longer needed — real endpoints are JWT-scoped

// 当前步骤
const step = ref(1)

// 数据类型
const dataTypes = [
  { id: 'glucose', icon: '🩸', name: '血糖', desc: '记录血糖测量值' },
  { id: 'weight', icon: '⚖️', name: '体重', desc: '记录今日体重' },
  { id: 'bloodPressure', icon: '💓', name: '血压', desc: '记录血压值' },
  { id: 'exercise', icon: '🏃', name: '运动', desc: '记录运动时长' },
  { id: 'mood', icon: '😊', name: '心情', desc: '记录心情日记' },
  { id: 'meal', icon: '🍽️', name: '饮食', desc: '记录饮食信息' }
]

const selectedType = ref<string | null>(null)

// 快捷选项
const glucoseTimeOptions = [
  { label: '早餐前', value: 'before_breakfast' },
  { label: '早餐后', value: 'after_breakfast' },
  { label: '午餐前', value: 'before_lunch' },
  { label: '午餐后', value: 'after_lunch' },
  { label: '晚餐前', value: 'before_dinner' },
  { label: '晚餐后', value: 'after_dinner' },
  { label: '睡前', value: 'before_sleep' }
]

const exerciseTypeOptions = [
  { label: '步行', value: 'walking', icon: '🚶' },
  { label: '跑步', value: 'running', icon: '🏃' },
  { label: '骑行', value: 'cycling', icon: '🚴' },
  { label: '游泳', value: 'swimming', icon: '🏊' },
  { label: '瑜伽', value: 'yoga', icon: '🧘' },
  { label: '其他', value: 'other', icon: '💪' }
]

const moodOptions = [
  { value: 5, emoji: '😄', label: '很开心' },
  { value: 4, emoji: '🙂', label: '开心' },
  { value: 3, emoji: '😐', label: '一般' },
  { value: 2, emoji: '😔', label: '不太好' },
  { value: 1, emoji: '😢', label: '很难过' }
]

// 输入数据
const inputData = ref({
  glucoseValue: '',
  glucoseTime: 'before_breakfast',
  weightValue: '',
  systolic: '',
  diastolic: '',
  exerciseType: 'walking',
  exerciseDuration: '',
  moodLevel: 3,
  moodNote: '',
  mealDescription: ''
})

// 历史数据
const historicalAverage = ref({
  glucose: '',
  weight: '',
  bloodPressure: ''
})

const weightTrend = computed(() => {
  const current = parseFloat(String(inputData.value.weightValue))
  const last = parseFloat(historicalAverage.value.weight)
  if (!current || !last) return ''
  const diff = current - last
  if (diff > 0) return `📈 增加了 ${diff.toFixed(1)} kg`
  if (diff < 0) return `📉 减少了 ${Math.abs(diff).toFixed(1)} kg`
  return '➡️ 保持不变'
})

// 加载历史数据
const loadHistoricalData = async (type: string) => {
  try {
    if (type === 'glucose') {
      const data = await healthApi.getGlucoseHistory({ period: '7d' })
      const records = data?.records || data?.items || (Array.isArray(data) ? data : [])
      if (data?.average) {
        historicalAverage.value.glucose = data.average.toFixed(1)
      } else if (records.length > 0) {
        const avg = records.reduce((s: number, r: any) => s + (r.value || 0), 0) / records.length
        historicalAverage.value.glucose = avg.toFixed(1)
      }
    } else if (type === 'weight') {
      const data = await healthApi.getWeightHistory({ period: '7d' })
      const records = data?.records || data?.items || (Array.isArray(data) ? data : [])
      if (records.length > 0) {
        const lastRecord = records[records.length - 1]
        historicalAverage.value.weight = (lastRecord.value || lastRecord.weight || 0).toFixed(1)
      }
    }
  } catch (error) {
    console.error('加载历史数据失败:', error)
  }
}

// 监听选中类型变化，加载对应的历史数据
watch(selectedType, (newType) => {
  if (newType && step.value === 2) {
    loadHistoricalData(newType)
  }
})

// 趋势数据
const trendData = ref<any>(null)

// 验证输入
const isInputValid = computed(() => {
  switch (selectedType.value) {
    case 'glucose':
      return !!inputData.value.glucoseValue && parseFloat(String(inputData.value.glucoseValue)) > 0
    case 'weight':
      return !!inputData.value.weightValue && parseFloat(String(inputData.value.weightValue)) > 0
    case 'bloodPressure':
      return !!inputData.value.systolic && !!inputData.value.diastolic
    case 'exercise':
      return !!inputData.value.exerciseDuration && parseInt(String(inputData.value.exerciseDuration)) > 0
    case 'mood':
      return !!inputData.value.moodLevel
    case 'meal':
      return !!inputData.value.mealDescription
    default:
      return false
  }
})

// 选择类型
const selectType = (type: any) => {
  selectedType.value = type.id
}

// 进入输入页
const goToInput = () => {
  step.value = 2
  if (selectedType.value) {
    loadHistoricalData(selectedType.value)
  }
}

// 提交数据
const submitData = async () => {
  message.loading({ content: '正在保存...', key: 'submit' })

  try {
    const timestamp = new Date().toISOString()

    // 根据类型调用不同的 API
    switch (selectedType.value) {
      case 'glucose':
        await healthApi.recordGlucose({
          value: parseFloat(String(inputData.value.glucoseValue)),
          measurement_time: timestamp,
          meal_tag: inputData.value.glucoseTime,
        })
        trendData.value = {
          current: `${inputData.value.glucoseValue} mmol/L`,
          average: `${historicalAverage.value.glucose} mmol/L`,
          status: 'good',
          statusText: '✅ 控制得不错，继续保持'
        }
        break

      case 'weight':
        await healthApi.recordWeight({
          value: parseFloat(String(inputData.value.weightValue)),
          measurement_time: timestamp,
        })
        trendData.value = {
          current: `${inputData.value.weightValue} kg`,
          average: `${historicalAverage.value.weight} kg`,
          status: 'good',
          statusText: weightTrend.value
        }
        break

      case 'bloodPressure':
        await healthApi.recordBloodPressure({
          systolic: parseInt(inputData.value.systolic),
          diastolic: parseInt(inputData.value.diastolic),
          measurement_time: timestamp,
        })
        trendData.value = {
          current: `${inputData.value.systolic}/${inputData.value.diastolic}`,
          average: historicalAverage.value.bloodPressure,
          status: 'good',
          statusText: '✅ 血压正常'
        }
        break

      case 'exercise':
        await healthApi.recordExercise({
          type: inputData.value.exerciseType,
          duration: parseInt(String(inputData.value.exerciseDuration)),
          note: `${inputData.value.exerciseType} ${inputData.value.exerciseDuration}分钟`,
        })
        trendData.value = {
          current: `${inputData.value.exerciseDuration} 分钟`,
          average: '30 分钟',
          status: 'good',
          statusText: '💪 继续保持运动习惯'
        }
        break

      case 'mood':
        await healthApi.recordMood({
          score: inputData.value.moodLevel,
          note: inputData.value.moodNote,
        })
        trendData.value = {
          current: moodOptions.find(m => m.value === inputData.value.moodLevel)?.label || '',
          average: '一般',
          status: 'good',
          statusText: '😊 心情记录已保存'
        }
        break

      case 'meal':
        await healthApi.recordMeal({
          description: inputData.value.mealDescription,
          note: inputData.value.mealDescription,
        })
        trendData.value = {
          current: '已记录',
          average: '',
          status: 'good',
          statusText: '🍽️ 饮食记录已保存'
        }
        break
    }

    message.success({ content: '保存成功！', key: 'submit' })
    step.value = 3

  } catch (error) {
    console.error('保存数据失败:', error)
    message.error({ content: '保存失败，请重试', key: 'submit' })
  }
}

// 继续记录
const continueRecord = () => {
  step.value = 1
  selectedType.value = null
  inputData.value = {
    glucoseValue: '',
    glucoseTime: 'before_breakfast',
    weightValue: '',
    systolic: '',
    diastolic: '',
    exerciseType: 'walking',
    exerciseDuration: '',
    moodLevel: 3,
    moodNote: '',
    mealDescription: ''
  }
  trendData.value = null
}

// 查看进展
const goToProgress = () => {
  router.push('/client/progress')
}

// 返回
const goBack = () => {
  router.back()
}
</script>

<style scoped>
.data-input-optimized {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 20px;
}

/* 导航栏 */
.nav-header {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.nav-back {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  transition: background 0.2s;
}

.nav-back:hover {
  background: rgba(255,255,255,0.2);
}

.nav-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
}

.nav-right {
  width: 40px;
}

/* 步骤容器 */
.step-container {
  max-width: 640px;
  margin: 20px auto;
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 100px);
}

.step-content {
  flex: 1;
}

.step-header {
  text-align: center;
  margin-bottom: 32px;
}

.step-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 8px;
}

.step-subtitle {
  font-size: 14px;
  color: #6b7280;
}

/* 数据类型选择 */
.data-type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.type-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px 16px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid #e5e7eb;
  position: relative;
}

.type-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.08);
}

.type-card.selected {
  border-color: #10b981;
  background: #f0fdf4;
}

.type-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 12px;
}

.type-info {
  text-align: center;
}

.type-name {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.type-desc {
  font-size: 12px;
  color: #6b7280;
}

.type-check {
  position: absolute;
  top: 12px;
  right: 12px;
  color: #10b981;
  font-size: 20px;
}

/* 输入区域 */
.input-section {
  margin-bottom: 24px;
}

.input-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.input-icon {
  font-size: 40px;
}

.input-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.input-subtitle {
  font-size: 14px;
  color: #6b7280;
}

/* 快捷选项 */
.quick-options {
  margin-bottom: 24px;
}

.option-label {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 12px;
}

.option-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-btn {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  cursor: pointer;
  transition: all 0.2s;
}

.option-btn:hover {
  background: #e5e7eb;
}

.option-btn.active {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

/* 血压双输入 */
.double-input {
  display: flex;
  gap: 12px;
}

.half-input {
  flex: 1;
}

.big-input-label {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 8px;
}

.big-number-input {
  font-size: 32px !important;
  font-weight: 700 !important;
  text-align: center;
  padding: 16px !important;
}

.input-unit {
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
  margin-top: 8px;
}

/* 心情选择器 */
.mood-selector {
  margin-bottom: 20px;
}

.mood-label {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 12px;
}

.mood-options {
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.mood-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.mood-item:hover {
  background: #f3f4f6;
}

.mood-item.active {
  background: #f0fdf4;
  border-color: #10b981;
}

.mood-emoji {
  font-size: 32px;
}

.mood-label-text {
  font-size: 12px;
  font-weight: 500;
  color: #1f2937;
}

.mood-note {
  margin-top: 20px;
}

.note-label {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 8px;
}

/* 饮食输入 */
.meal-input {
  margin-top: 20px;
}

/* 步骤底部 */
.step-footer {
  padding: 20px 0;
  display: flex;
  gap: 12px;
}

.back-btn {
  flex: 1;
}

.submit-btn {
  flex: 2;
}

/* 成功页面 */
.success-content {
  text-align: center;
  padding: 40px 20px;
}

.success-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.success-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 8px;
}

.success-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 32px;
}

/* 趋势卡片 */
.trend-card {
  background: #fff;
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 32px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.trend-header {
  margin-bottom: 20px;
}

.trend-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.trend-content {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin-bottom: 16px;
}

.trend-item {
  flex: 1;
  text-align: center;
}

.trend-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.trend-value {
  font-size: 24px;
  font-weight: 700;
}

.trend-value.current {
  color: #10b981;
}

.trend-value.average {
  color: #6b7280;
}

.trend-divider {
  font-size: 16px;
  font-weight: 600;
  color: #d1d5db;
  padding: 0 16px;
}

.trend-status {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  padding: 12px;
  background: #f9fafb;
  border-radius: 12px;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
