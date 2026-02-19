<template>
  <div class="page-container">
    <van-nav-bar title="食物识别" left-arrow @click-left="router.back()" />

    <div class="page-content">
      <!-- 拍照区域 -->
      <div v-if="!analyzing && !result" class="capture-section card">
        <div class="capture-area" @click="triggerFileInput">
          <van-icon name="photograph" size="48" color="#1989fa" />
          <p class="capture-title">拍摄食物照片</p>
          <p class="capture-hint">拍照或从相册选择，AI 将为你分析营养成分</p>
        </div>
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          capture="environment"
          class="hidden-input"
          @change="onFileSelected"
        />

        <!-- 餐次选择 -->
        <div class="meal-type-row">
          <span class="meal-label">餐次：</span>
          <van-radio-group v-model="mealType" direction="horizontal">
            <van-radio name="breakfast">早餐</van-radio>
            <van-radio name="lunch">午餐</van-radio>
            <van-radio name="dinner">晚餐</van-radio>
            <van-radio name="snack">加餐</van-radio>
          </van-radio-group>
        </div>
      </div>

      <!-- 分析中 -->
      <div v-if="analyzing" class="analyzing-section card">
        <van-image
          v-if="previewUrl"
          :src="previewUrl"
          width="100%"
          height="200"
          fit="cover"
          radius="8"
          style="margin-bottom: 16px"
        />
        <div class="analyzing-indicator">
          <div class="bhp-typing-dots">
            <span></span><span></span><span></span>
          </div>
          <p class="analyzing-text">AI 食物识别中...</p>
          <p class="analyzing-hint">视觉模型分析需要 10-20 秒，请耐心等待</p>
        </div>
      </div>

      <!-- 结果卡片 -->
      <div v-if="result" class="result-section">
        <!-- 食物图片 -->
        <div class="result-image card">
          <van-image
            :src="result.image_url"
            width="100%"
            height="200"
            fit="cover"
            radius="8"
          />
          <div class="food-name">{{ result.food_name || '未识别' }}</div>
          <van-tag v-if="result.meal_type" type="primary" size="medium" style="margin-top:4px">
            {{ mealTypeLabel(result.meal_type) }}
          </van-tag>
        </div>

        <!-- 营养数据 4 宫格 -->
        <div class="nutrition-grid card">
          <div class="nutrition-item calories">
            <div class="nutrition-value">{{ formatNum(result.calories) }}</div>
            <div class="nutrition-label">热量 (kcal)</div>
          </div>
          <div class="nutrition-item protein">
            <div class="nutrition-value">{{ formatNum(result.protein) }}</div>
            <div class="nutrition-label">蛋白质 (g)</div>
          </div>
          <div class="nutrition-item fat">
            <div class="nutrition-value">{{ formatNum(result.fat) }}</div>
            <div class="nutrition-label">脂肪 (g)</div>
          </div>
          <div class="nutrition-item carbs">
            <div class="nutrition-value">{{ formatNum(result.carbs) }}</div>
            <div class="nutrition-label">碳水 (g)</div>
          </div>
        </div>

        <!-- 膳食纤维 -->
        <div v-if="result.fiber" class="fiber-row card">
          <span>膳食纤维</span>
          <span class="fiber-value">{{ formatNum(result.fiber) }} g</span>
        </div>

        <!-- 营养建议 -->
        <div v-if="result.advice" class="advice-card card">
          <div class="advice-title">营养建议</div>
          <div class="advice-text">{{ result.advice }}</div>
        </div>

        <!-- 食物明细 -->
        <div v-if="result.foods && result.foods.length" class="foods-detail card">
          <div class="detail-title">食物明细</div>
          <div v-for="(food, idx) in result.foods" :key="idx" class="food-item">
            <span class="food-item-name">{{ food.name }}</span>
            <span class="food-item-portion">{{ food.portion }}</span>
            <span class="food-item-cal">{{ food.calories }} kcal</span>
          </div>
        </div>

        <!-- 任务自动完成横幅 -->
        <Transition name="task-banner">
          <div v-if="taskCompleted" class="task-complete-banner">
            <van-icon name="checked" size="20" color="#fff" />
            <div class="task-complete-info">
              <div class="task-complete-title">今日营养任务已自动完成!</div>
              <div class="task-complete-detail">+{{ taskInfo?.points_earned || 10 }}积分 · 连续{{ taskInfo?.streak || 1 }}天</div>
            </div>
          </div>
        </Transition>

        <!-- 再拍一张 -->
        <van-button
          type="primary"
          block
          round
          size="large"
          style="margin-top: 16px"
          @click="resetCapture"
        >
          再拍一张
        </van-button>
      </div>

      <!-- 历史记录 -->
      <div class="history-section">
        <div class="history-header">
          <h3>历史记录</h3>
        </div>
        <van-loading v-if="loadingHistory" size="20" style="text-align:center;padding:20px" />
        <template v-else-if="history.length">
          <div
            v-for="item in history"
            :key="item.id"
            class="history-item card"
            @click="showHistoryDetail(item)"
          >
            <van-image
              :src="item.image_url"
              width="60"
              height="60"
              fit="cover"
              radius="6"
            />
            <div class="history-info">
              <div class="history-food">{{ item.food_name || '未识别' }}</div>
              <div class="history-meta">
                <span v-if="item.calories">{{ formatNum(item.calories) }} kcal</span>
                <span v-if="item.meal_type" class="history-meal">{{ mealTypeLabel(item.meal_type) }}</span>
              </div>
              <div class="history-time">{{ formatTime(item.created_at) }}</div>
            </div>
          </div>
          <div v-if="history.length < historyTotal" class="load-more" @click="loadHistory">
            加载更多
          </div>
        </template>
        <div v-else class="history-empty">暂无识别记录</div>
      </div>
    </div>

    <!-- 历史详情弹窗 -->
    <van-popup v-model:show="showDetail" position="bottom" round :style="{ height: '75%' }">
      <div v-if="detailItem" class="detail-popup">
        <div class="detail-popup-header">
          <h3>{{ detailItem.food_name || '食物详情' }}</h3>
          <van-icon name="cross" @click="showDetail = false" />
        </div>
        <div class="detail-popup-body">
          <van-image :src="detailItem.image_url" width="100%" height="200" fit="cover" radius="8" />
          <div class="nutrition-grid" style="margin-top:12px">
            <div class="nutrition-item calories">
              <div class="nutrition-value">{{ formatNum(detailItem.calories) }}</div>
              <div class="nutrition-label">热量 (kcal)</div>
            </div>
            <div class="nutrition-item protein">
              <div class="nutrition-value">{{ formatNum(detailItem.protein) }}</div>
              <div class="nutrition-label">蛋白质 (g)</div>
            </div>
            <div class="nutrition-item fat">
              <div class="nutrition-value">{{ formatNum(detailItem.fat) }}</div>
              <div class="nutrition-label">脂肪 (g)</div>
            </div>
            <div class="nutrition-item carbs">
              <div class="nutrition-value">{{ formatNum(detailItem.carbs) }}</div>
              <div class="nutrition-label">碳水 (g)</div>
            </div>
          </div>
          <div v-if="detailItem.advice" class="advice-card" style="margin-top:12px">
            <div class="advice-title">营养建议</div>
            <div class="advice-text">{{ detailItem.advice }}</div>
          </div>
        </div>
      </div>
    </van-popup>

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import TabBar from '@/components/common/TabBar.vue'
import api from '@/api/index'

const router = useRouter()

// 状态
const fileInput = ref<HTMLInputElement | null>(null)
const mealType = ref('lunch')
const analyzing = ref(false)
const previewUrl = ref('')
const result = ref<any>(null)

// 任务自动完成
const taskCompleted = ref(false)
const taskInfo = ref<any>(null)

// 历史
const loadingHistory = ref(false)
const history = ref<any[]>([])
const historyTotal = ref(0)
const historyOffset = ref(0)

// 详情弹窗
const showDetail = ref(false)
const detailItem = ref<any>(null)

function triggerFileInput() {
  fileInput.value?.click()
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 预览
  previewUrl.value = URL.createObjectURL(file)
  analyzing.value = true
  result.value = null

  // 构建 FormData
  const formData = new FormData()
  formData.append('file', file)
  if (mealType.value) {
    formData.append('meal_type', mealType.value)
  }

  try {
    const res: any = await api.post('/api/v1/food/recognize', formData, {
      timeout: 120000,
    })
    result.value = res
    // 检查是否自动完成了营养任务
    if (res.task_completed) {
      taskCompleted.value = true
      taskInfo.value = res.task_info
    }
    showToast({ message: '分析完成', type: 'success' })
    // 刷新历史
    historyOffset.value = 0
    await loadHistory(true)
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '分析失败，请重试'
    showToast({ message: msg, type: 'fail' })
    result.value = null
  } finally {
    analyzing.value = false
    // 重置 input 以允许再次选同一张图
    input.value = ''
  }
}

function resetCapture() {
  result.value = null
  previewUrl.value = ''
  taskCompleted.value = false
  taskInfo.value = null
}

async function loadHistory(reset = false) {
  if (reset) {
    historyOffset.value = 0
    history.value = []
  }
  loadingHistory.value = history.value.length === 0
  try {
    const res: any = await api.get('/api/v1/food/history', {
      params: { limit: 10, offset: historyOffset.value },
    })
    if (reset) {
      history.value = res.items || []
    } else {
      history.value.push(...(res.items || []))
    }
    historyTotal.value = res.total || 0
    historyOffset.value = history.value.length
  } catch {
    /* ignore */
  } finally {
    loadingHistory.value = false
  }
}

function showHistoryDetail(item: any) {
  detailItem.value = item
  showDetail.value = true
}

function mealTypeLabel(type: string) {
  const map: Record<string, string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '加餐',
  }
  return map[type] || type
}

function formatNum(val: any) {
  if (val == null) return '--'
  return Number(val).toFixed(1)
}

function formatTime(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

onMounted(() => {
  loadHistory(true)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.hidden-input {
  display: none;
}

/* 拍照区域 */
.capture-section {
  text-align: center;
}

.capture-area {
  padding: 40px 20px;
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.3s;

  &:active {
    border-color: #1989fa;
  }

  .capture-title {
    font-size: 16px;
    font-weight: 600;
    margin: 12px 0 4px;
    color: $text-color;
  }

  .capture-hint {
    font-size: 13px;
    color: $text-color-secondary;
  }
}

.meal-type-row {
  display: flex;
  align-items: center;
  margin-top: 16px;
  gap: 8px;

  .meal-label {
    font-size: 14px;
    color: $text-color-secondary;
    flex-shrink: 0;
  }

  :deep(.van-radio) {
    margin-right: 0;
  }
}

/* 分析中 */
.analyzing-section {
  text-align: center;
}

.analyzing-indicator {
  padding: 20px 0;

  .analyzing-text {
    font-size: 16px;
    font-weight: 500;
    margin-top: 16px;
    color: $text-color;
  }

  .analyzing-hint {
    font-size: 13px;
    color: $text-color-secondary;
    margin-top: 4px;
  }
}

/* 结果卡片 */
.result-image {
  .food-name {
    font-size: 20px;
    font-weight: 700;
    margin-top: 12px;
    color: $text-color;
  }
}

.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.nutrition-item {
  text-align: center;
  padding: 14px 8px;
  border-radius: 10px;

  &.calories {
    background: #fff7ed;
    .nutrition-value { color: #ea580c; }
  }

  &.protein {
    background: #eff6ff;
    .nutrition-value { color: #2563eb; }
  }

  &.fat {
    background: #fef2f2;
    .nutrition-value { color: #dc2626; }
  }

  &.carbs {
    background: #f0fdf4;
    .nutrition-value { color: #16a34a; }
  }

  .nutrition-value {
    font-size: 24px;
    font-weight: 700;
  }

  .nutrition-label {
    font-size: 12px;
    color: $text-color-secondary;
    margin-top: 4px;
  }
}

.fiber-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;

  .fiber-value {
    font-weight: 600;
    color: #16a34a;
  }
}

.advice-card {
  border-left: 4px solid #16a34a;
  background: #f0fdf4;

  .advice-title {
    font-size: 14px;
    font-weight: 600;
    color: #16a34a;
    margin-bottom: 6px;
  }

  .advice-text {
    font-size: 14px;
    color: #374151;
    line-height: 1.6;
  }
}

.foods-detail {
  .detail-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .food-item {
    display: flex;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f5f5f5;
    font-size: 14px;

    &:last-child {
      border-bottom: none;
    }
  }

  .food-item-name {
    flex: 1;
    font-weight: 500;
  }

  .food-item-portion {
    color: $text-color-secondary;
    margin-right: 12px;
  }

  .food-item-cal {
    color: #ea580c;
    font-weight: 500;
  }
}

/* 任务自动完成横幅 */
.task-complete-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 12px;
  color: #fff;
}

.task-complete-title {
  font-size: 15px;
  font-weight: 700;
}

.task-complete-detail {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 2px;
}

.task-banner-enter-active {
  animation: bannerSlideDown 0.4s ease-out;
}

@keyframes bannerSlideDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 历史记录 */
.history-section {
  margin-top: 20px;
}

.history-header {
  h3 {
    font-size: $font-size-lg;
    margin-bottom: 8px;
  }
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;

  &:active {
    opacity: 0.7;
  }
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-food {
  font-size: 15px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-meta {
  font-size: 13px;
  color: #ea580c;
  margin-top: 2px;

  .history-meal {
    margin-left: 8px;
    color: $text-color-secondary;
  }
}

.history-time {
  font-size: 12px;
  color: $text-color-placeholder;
  margin-top: 2px;
}

.history-empty {
  text-align: center;
  padding: 20px;
  color: $text-color-placeholder;
  font-size: $font-size-sm;
}

.load-more {
  text-align: center;
  padding: 12px;
  font-size: 14px;
  color: #1989fa;
  cursor: pointer;
}

/* 详情弹窗 */
.detail-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid $border-color;

  h3 {
    margin: 0;
    font-size: 18px;
  }
}

.detail-popup-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
</style>
