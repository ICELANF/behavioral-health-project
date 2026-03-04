<template>
  <view class="fs-page">
    <view class="fs-navbar">
      <view class="fs-back" @tap="goBack">←</view>
      <text class="fs-title">饮食记录</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="fs-scroll">
      <!-- 拍照识别 -->
      <view class="fs-photo-card">
        <text class="fs-card-title">📷 拍照识别</text>

        <!-- AI说明 -->
        <view class="fs-ai-tip">
          <text class="fs-ai-tip-text">💡 AI通过照片的图形和色彩识别食物，混合菜肴或烹饪方式会影响估算精度，建议拍照前补充烹饪方式。预包装食品请拍摄营养成分表标签，精度更高。</text>
        </view>

        <!-- 拍照前配置 -->
        <view v-if="!photoResult">
          <view class="fs-config-row">
            <view class="fs-config-item">
              <text class="fs-config-label">餐次</text>
              <picker :range="mealLabels" :value="mealIdx" @change="mealIdx = $event.detail.value">
                <view class="fs-config-picker">{{ mealLabels[mealIdx] }} ▾</view>
              </picker>
            </view>
            <view class="fs-config-item">
              <text class="fs-config-label">烹饪方式</text>
              <picker :range="cookingLabels" :value="cookingIdx" @change="cookingIdx = $event.detail.value">
                <view class="fs-config-picker">{{ cookingLabels[cookingIdx] }} ▾</view>
              </picker>
            </view>
          </view>
          <view class="fs-config-toggle">
            <text class="fs-toggle-label">📦 预包装食品（拍营养成分表标签）</text>
            <switch :checked="isPackaged" @change="isPackaged = ($event as any).detail.value" color="#1565C0" />
          </view>
          <view class="fs-photo-area" @tap="takePhoto">
            <text class="fs-photo-icon">{{ isPackaged ? '🏷️' : '📷' }}</text>
            <text class="fs-photo-hint">{{ isPackaged ? '拍摄营养成分表标签' : '拍照或从相册选择' }}</text>
            <text class="fs-photo-sub">点击开始</text>
          </view>
        </view>

        <!-- 识别结果 -->
        <view v-else class="fs-result-area">
          <image class="fs-food-image" :src="photoPreview" mode="aspectFill" />
          <view class="fs-food-info">
            <text class="fs-food-name">{{ photoResult.food_name || '识别中…' }}</text>
            <view v-if="photoResult.nutrition" class="fs-calories-row">
              <text class="fs-calories-val">{{ photoResult.nutrition.calories ?? '—' }}</text>
              <text class="fs-calories-unit">kcal</text>
            </view>
            <view class="fs-detail-toggle" @tap="showDetail = !showDetail">
              <text class="fs-detail-toggle-text">{{ showDetail ? '收起营养明细 ▴' : '查看营养明细 ▾' }}</text>
            </view>
            <view v-if="showDetail && photoResult.nutrition" class="fs-nutrients">
              <view class="fs-nut-item">
                <text class="fs-nut-val">{{ photoResult.nutrition.carbs ?? '—' }}g</text>
                <text class="fs-nut-label">碳水化合物</text>
              </view>
              <view class="fs-nut-item">
                <text class="fs-nut-val">{{ photoResult.nutrition.protein ?? '—' }}g</text>
                <text class="fs-nut-label">蛋白质</text>
              </view>
              <view class="fs-nut-item">
                <text class="fs-nut-val">{{ photoResult.nutrition.fat ?? '—' }}g</text>
                <text class="fs-nut-label">脂肪</text>
              </view>
            </view>
            <text v-if="photoResult.advice" class="fs-advice">{{ photoResult.advice }}</text>
            <view class="fs-result-actions">
              <view class="fs-btn fs-btn--retry" @tap="photoResult=null; photoPreview=''">重新拍摄</view>
              <view class="fs-btn fs-btn--save" @tap="saveRecord">保存记录</view>
            </view>
          </view>
        </view>
      </view>

      <!-- 手动添加 -->
      <view class="fs-manual-card">
        <text class="fs-card-title">📝 手动添加</text>
        <view class="fs-row">
          <view class="fs-field flex2">
            <text class="fs-field-label">食物名称 *</text>
            <input class="fs-field-input" v-model="manualForm.name" placeholder="如: 白米饭(200g)" maxlength="50" />
          </view>
          <view class="fs-field">
            <text class="fs-field-label">餐次</text>
            <picker :range="mealLabels" :value="mealIdx" @change="mealIdx = $event.detail.value">
              <view class="fs-field-picker">{{ mealLabels[mealIdx] }}</view>
            </picker>
          </view>
        </view>
        <view class="fs-row">
          <view class="fs-field"><text class="fs-field-label">热量(kcal)</text><input class="fs-field-input" type="number" v-model="manualForm.calories" placeholder="如: 350" maxlength="4" /></view>
          <view class="fs-field"><text class="fs-field-label">碳水(g)</text><input class="fs-field-input" type="digit" v-model="manualForm.carbs" placeholder="如: 75" maxlength="4" /></view>
        </view>
        <view class="fs-row">
          <view class="fs-field"><text class="fs-field-label">蛋白质(g)</text><input class="fs-field-input" type="digit" v-model="manualForm.protein" placeholder="如: 8" maxlength="4" /></view>
          <view class="fs-field"><text class="fs-field-label">脂肪(g)</text><input class="fs-field-input" type="digit" v-model="manualForm.fat" placeholder="如: 1" maxlength="4" /></view>
        </view>
        <view class="fs-submit-btn" :class="{ 'fs-submit-btn--loading': submitting }" @tap="saveManual">
          {{ submitting ? '保存中…' : '添加到饮食日记' }}
        </view>
      </view>

      <!-- 今日摄入摘要 -->
      <view class="fs-summary-card">
        <text class="fs-card-title">📊 今日摄入</text>
        <view class="fs-summary-row">
          <view class="fs-sum-item">
            <text class="fs-sum-val">{{ todaySummary.calories }}</text>
            <text class="fs-sum-label">kcal</text>
          </view>
          <view class="fs-sum-divider"></view>
          <view class="fs-sum-item">
            <text class="fs-sum-val">{{ todaySummary.carbs }}g</text>
            <text class="fs-sum-label">碳水</text>
          </view>
          <view class="fs-sum-divider"></view>
          <view class="fs-sum-item">
            <text class="fs-sum-val">{{ todaySummary.protein }}g</text>
            <text class="fs-sum-label">蛋白质</text>
          </view>
          <view class="fs-sum-divider"></view>
          <view class="fs-sum-item">
            <text class="fs-sum-val">{{ todaySummary.fat }}g</text>
            <text class="fs-sum-label">脂肪</text>
          </view>
        </view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { httpReq as http, getToken, apiHost as API_HOST } from '@/api/request'

const mealTypes = [
  { label: '早餐',    key: 'breakfast' },
  { label: '上午点心', key: 'morning_snack' },
  { label: '午餐',    key: 'lunch' },
  { label: '下午点心', key: 'afternoon_snack' },
  { label: '晚餐',    key: 'dinner' },
  { label: '夜宵',    key: 'supper' },
]
const mealLabels = mealTypes.map(m => m.label)

const cookingMethods = [
  { label: '未选择', key: '' },
  { label: '蒸',     key: '蒸' },
  { label: '煮',     key: '煮' },
  { label: '炒',     key: '炒' },
  { label: '炸',     key: '炸' },
  { label: '烤/煎',  key: '烤煎' },
  { label: '凉拌/生食', key: '凉拌生食' },
  { label: '汤/炖',  key: '汤炖' },
  { label: '其他',   key: '其他' },
]
const cookingLabels = cookingMethods.map(m => m.label)

const mealIdx    = ref(0)
const cookingIdx = ref(0)
const isPackaged = ref(false)
const showDetail = ref(false)
const photoPreview = ref('')
const photoResult  = ref<any>(null)
const submitting   = ref(false)
const manualForm   = reactive({ name: '', calories: '', carbs: '', protein: '', fat: '' })
const todaySummary = ref({ calories: 0, carbs: 0, protein: 0, fat: 0 })

function takePhoto() {
  uni.chooseImage({
    count: 1,
    sourceType: ['camera', 'album'],
    success: async (res) => {
      photoPreview.value = res.tempFilePaths[0]
      uni.showLoading({ title: 'AI识别中…' })
      try {
        const uploadRes: any = await new Promise((resolve, reject) => {
          uni.uploadFile({
            url: API_HOST + '/api/v1/food/analyze',
            filePath: res.tempFilePaths[0],
            name: 'image',
            header: { 'Authorization': 'Bearer ' + getToken() },
            formData: {
              meal_type:      mealTypes[mealIdx.value].key,
              cooking_method: cookingMethods[cookingIdx.value].key,
              is_packaged:    isPackaged.value ? 'true' : 'false',
            },
            success: (r: any) => {
              const data = typeof r.data === 'string' ? JSON.parse(r.data) : r.data
              resolve(data)
            },
            fail: reject,
          })
        })
        photoResult.value = uploadRes
        showDetail.value  = false
      } catch {
        photoResult.value = {
          food_name: '混合食物（AI识别失败，请手动补充）',
          nutrition: { calories: null, carbs: null, protein: null, fat: null },
        }
      } finally {
        uni.hideLoading()
      }
    },
  })
}

async function saveRecord() {
  try {
    await http('/api/v1/food/record', {
      method: 'POST',
      data: {
        food_name:      photoResult.value.food_name,
        meal_type:      mealTypes[mealIdx.value].key,
        image_url:      photoPreview.value,
        nutrition:      photoResult.value.nutrition,
        cooking_method: cookingMethods[cookingIdx.value].key || null,
        is_packaged:    isPackaged.value,
        recorded_at:    new Date().toISOString(),
      },
    })
    photoResult.value  = null
    photoPreview.value = ''
    uni.showToast({ title: '饮食记录已保存', icon: 'success' })
    loadSummary()
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}

async function saveManual() {
  if (!manualForm.name.trim()) {
    uni.showToast({ title: '请输入食物名称', icon: 'none' }); return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    await http('/api/v1/food/record', {
      method: 'POST',
      data: {
        food_name: manualForm.name,
        meal_type: mealTypes[mealIdx.value].key,
        nutrition: {
          calories: manualForm.calories ? parseInt(manualForm.calories) : null,
          carbs:    manualForm.carbs    ? parseFloat(manualForm.carbs)  : null,
          protein:  manualForm.protein  ? parseFloat(manualForm.protein): null,
          fat:      manualForm.fat      ? parseFloat(manualForm.fat)    : null,
        },
        recorded_at: new Date().toISOString(),
      },
    })
    Object.assign(manualForm, { name: '', calories: '', carbs: '', protein: '', fat: '' })
    uni.showToast({ title: '已添加到饮食日记', icon: 'success' })
    loadSummary()
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function loadSummary() {
  try {
    const today = new Date().toISOString().slice(0, 10)
    const res = await http<any>(`/api/v1/food/diary?date=${today}`)
    const items = res.items || (Array.isArray(res) ? res : [])
    todaySummary.value = items.reduce((acc: any, i: any) => {
      acc.calories += (i.nutrition?.calories || 0)
      acc.carbs    += (i.nutrition?.carbs || 0)
      acc.protein  += (i.nutrition?.protein || 0)
      acc.fat      += (i.nutrition?.fat || 0)
      return acc
    }, { calories: 0, carbs: 0, protein: 0, fat: 0 })
  } catch (e) { console.warn('[food/scan] loadSummary:', e) }
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => loadSummary())
</script>

<style scoped>
.fs-page { min-height: 100vh; background: #F0F7FF; }
.fs-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%); color: #fff; }
.fs-back  { font-size: 40rpx; padding: 16rpx; }
.fs-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.fs-scroll { height: calc(100vh - 180rpx); }

.fs-photo-card   { margin: 24rpx; background: #fff; border-radius: 20rpx; padding: 24rpx; }
.fs-manual-card  { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.fs-summary-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.fs-card-title   { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }

/* AI提示 */
.fs-ai-tip { background: #EEF6FF; border-radius: 12rpx; padding: 16rpx 20rpx; margin-bottom: 16rpx; }
.fs-ai-tip-text { font-size: 22rpx; color: #1565C0; line-height: 1.6; }

/* 配置区 */
.fs-config-row { display: flex; gap: 16rpx; margin-bottom: 12rpx; }
.fs-config-item { flex: 1; }
.fs-config-label { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 6rpx; }
.fs-config-picker { background: #F0F7FF; border-radius: 10rpx; padding: 14rpx 16rpx; font-size: 26rpx; color: #2C3E50; }
.fs-config-toggle { display: flex; align-items: center; justify-content: space-between; padding: 12rpx 0; margin-bottom: 12rpx; border-top: 1rpx solid #F5F6FA; border-bottom: 1rpx solid #F5F6FA; }
.fs-toggle-label { font-size: 26rpx; color: #2C3E50; }

/* 拍照区 */
.fs-photo-area { padding: 48rpx; text-align: center; border: 4rpx dashed #BBDEFB; border-radius: 16rpx; margin-top: 12rpx; }
.fs-photo-icon { display: block; font-size: 80rpx; margin-bottom: 12rpx; }
.fs-photo-hint { display: block; font-size: 30rpx; font-weight: 600; color: #1565C0; }
.fs-photo-sub  { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 6rpx; }

/* 识别结果 */
.fs-result-area { display: flex; flex-direction: column; }
.fs-food-image  { width: 100%; height: 280rpx; border-radius: 12rpx; margin-bottom: 16rpx; }
.fs-food-name   { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; margin-bottom: 10rpx; }
.fs-calories-row  { display: flex; align-items: baseline; gap: 6rpx; margin-bottom: 12rpx; }
.fs-calories-val  { font-size: 52rpx; font-weight: 700; color: #1565C0; }
.fs-calories-unit { font-size: 22rpx; color: #8E99A4; }
.fs-detail-toggle { padding: 8rpx 0; margin-bottom: 10rpx; }
.fs-detail-toggle-text { font-size: 24rpx; color: #1E88E5; }
.fs-nutrients { display: flex; gap: 10rpx; margin-bottom: 16rpx; }
.fs-nut-item  { flex: 1; background: #F0F7FF; border-radius: 10rpx; padding: 12rpx; text-align: center; }
.fs-nut-val   { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.fs-nut-label { display: block; font-size: 18rpx; color: #8E99A4; margin-top: 4rpx; }
.fs-advice { display: block; font-size: 22rpx; color: #5B6B7F; background: #F9FAFB; border-radius: 10rpx; padding: 12rpx 16rpx; margin-bottom: 16rpx; line-height: 1.5; }
.fs-result-actions { display: flex; gap: 16rpx; }
.fs-btn { flex: 1; text-align: center; padding: 20rpx 0; border-radius: 12rpx; font-size: 26rpx; font-weight: 600; }
.fs-btn--retry { background: #F0F0F0; color: #5B6B7F; }
.fs-btn--save  { background: #E65100; color: #fff; }

/* 手动添加 */
.fs-row { display: flex; gap: 16rpx; margin-bottom: 16rpx; }
.fs-field { flex: 1; }
.fs-field.flex2 { flex: 2; }
.fs-field-label  { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 8rpx; }
.fs-field-input  { width: 100%; background: #F0F7FF; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 26rpx; box-sizing: border-box; }
.fs-field-picker { background: #F0F7FF; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 26rpx; color: #2C3E50; }
.fs-submit-btn { margin-top: 8rpx; background: #E65100; color: #fff; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.fs-submit-btn--loading { background: #FFCC80; color: #E65100; }

/* 今日摄入 */
.fs-summary-row  { display: flex; align-items: center; }
.fs-sum-item     { flex: 1; text-align: center; }
.fs-sum-val      { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; }
.fs-sum-label    { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.fs-sum-divider  { width: 1rpx; height: 50rpx; background: #EEF0F3; }
</style>
