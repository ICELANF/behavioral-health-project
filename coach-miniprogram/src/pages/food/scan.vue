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
        <view class="fs-photo-area" @tap="takePhoto" v-if="!photoResult">
          <text class="fs-photo-icon">📷</text>
          <text class="fs-photo-hint">拍照识别食物</text>
          <text class="fs-photo-sub">AI自动识别食物种类和营养成分</text>
        </view>
        <view v-else class="fs-result-area">
          <image class="fs-food-image" :src="photoPreview" mode="aspectFill" />
          <view class="fs-food-info">
            <text class="fs-food-name">{{ photoResult.food_name || '识别中…' }}</text>
            <view class="fs-nutrients" v-if="photoResult.nutrition">
              <view class="fs-nut-item"><text class="fs-nut-val">{{ photoResult.nutrition.calories ?? '—' }}</text><text class="fs-nut-label">卡路里</text></view>
              <view class="fs-nut-item"><text class="fs-nut-val">{{ photoResult.nutrition.carbs ?? '—' }}g</text><text class="fs-nut-label">碳水</text></view>
              <view class="fs-nut-item"><text class="fs-nut-val">{{ photoResult.nutrition.protein ?? '—' }}g</text><text class="fs-nut-label">蛋白质</text></view>
              <view class="fs-nut-item"><text class="fs-nut-val">{{ photoResult.nutrition.fat ?? '—' }}g</text><text class="fs-nut-label">脂肪</text></view>
            </view>
            <view class="fs-result-actions">
              <view class="fs-btn fs-btn--retry" @tap="photoResult=null; photoPreview=''">重新拍照</view>
              <view class="fs-btn fs-btn--save" @tap="saveRecord">保存记录</view>
            </view>
          </view>
        </view>
      </view>

      <!-- 手动添加 -->
      <view class="fs-manual-card">
        <text class="fs-manual-title">📝 手动添加</text>
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
          <view class="fs-field"><text class="fs-field-label">卡路里(kcal)</text><input class="fs-field-input" type="number" v-model="manualForm.calories" placeholder="如: 350" maxlength="4" /></view>
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

      <!-- 今日饮食摘要 -->
      <view class="fs-summary-card">
        <text class="fs-summary-title">📊 今日摄入</text>
        <view class="fs-summary-row">
          <view class="fs-sum-item">
            <text class="fs-sum-val" style="color:#E74C3C;">{{ todaySummary.calories }}</text>
            <text class="fs-sum-label">卡路里</text>
          </view>
          <view class="fs-sum-item">
            <text class="fs-sum-val" style="color:#E67E22;">{{ todaySummary.carbs }}g</text>
            <text class="fs-sum-label">碳水</text>
          </view>
          <view class="fs-sum-item">
            <text class="fs-sum-val" style="color:#27AE60;">{{ todaySummary.protein }}g</text>
            <text class="fs-sum-label">蛋白质</text>
          </view>
          <view class="fs-sum-item">
            <text class="fs-sum-val" style="color:#9B59B6;">{{ todaySummary.fat }}g</text>
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

// 餐次：label 显示中文，key 传给后端
const mealTypes = [
  { label: '早餐',    key: 'breakfast' },
  { label: '上午点心', key: 'morning_snack' },
  { label: '午餐',    key: 'lunch' },
  { label: '下午点心', key: 'afternoon_snack' },
  { label: '晚餐',    key: 'dinner' },
  { label: '夜宵',    key: 'supper' },
]
const mealLabels = mealTypes.map(m => m.label)
const mealIdx = ref(0)
const photoPreview = ref('')
const photoResult = ref<any>(null)
const submitting = ref(false)
const manualForm = reactive({ name: '', calories: '', carbs: '', protein: '', fat: '' })
const todaySummary = ref({ calories: 0, carbs: 0, protein: 0, fat: 0 })

function takePhoto() {
  uni.chooseImage({
    count: 1,
    sourceType: ['camera', 'album'],
    success: async (res) => {
      photoPreview.value = res.tempFilePaths[0]
      uni.showLoading({ title: 'AI识别中…' })
      try {
        // 上传图片并分析
        const uploadRes: any = await new Promise((resolve, reject) => {
          uni.uploadFile({
            url: API_HOST + '/api/v1/food/analyze',
            filePath: res.tempFilePaths[0],
            name: 'image',
            header: { 'Authorization': 'Bearer ' + getToken() },
            success: (r: any) => {
              const data = typeof r.data === 'string' ? JSON.parse(r.data) : r.data
              resolve(data)
            },
            fail: reject,
          })
        })
        photoResult.value = uploadRes
      } catch {
        // 模拟识别结果（降级）
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
        food_name: photoResult.value.food_name,
        meal_type: mealTypes[mealIdx.value].key,
        image_url: photoPreview.value,
        nutrition: photoResult.value.nutrition,
        recorded_at: new Date().toISOString(),
      },
    })
    photoResult.value = null
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
          carbs: manualForm.carbs ? parseFloat(manualForm.carbs) : null,
          protein: manualForm.protein ? parseFloat(manualForm.protein) : null,
          fat: manualForm.fat ? parseFloat(manualForm.fat) : null,
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
.fs-page { min-height: 100vh; background: #F5F6FA; }
.fs-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #196F3D 0%, #27AE60 100%); color: #fff; }
.fs-back  { font-size: 40rpx; padding: 16rpx; }
.fs-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.fs-scroll { height: calc(100vh - 180rpx); }

.fs-photo-card { margin: 24rpx; background: #fff; border-radius: 20rpx; overflow: hidden; }
.fs-photo-area { padding: 64rpx; text-align: center; border: 4rpx dashed #D5F5E3; margin: 16rpx; border-radius: 16rpx; }
.fs-photo-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.fs-photo-hint { display: block; font-size: 30rpx; font-weight: 600; color: #27AE60; }
.fs-photo-sub  { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 8rpx; }

.fs-result-area { display: flex; gap: 0; flex-direction: column; }
.fs-food-image  { width: 100%; height: 300rpx; }
.fs-food-info   { padding: 24rpx; }
.fs-food-name   { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.fs-nutrients   { display: flex; gap: 8rpx; margin-bottom: 20rpx; }
.fs-nut-item    { flex: 1; background: #F5F6FA; border-radius: 10rpx; padding: 12rpx; text-align: center; }
.fs-nut-val     { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.fs-nut-label   { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.fs-result-actions { display: flex; gap: 16rpx; }
.fs-btn { flex: 1; text-align: center; padding: 20rpx 0; border-radius: 12rpx; font-size: 26rpx; font-weight: 600; }
.fs-btn--retry { background: #F0F0F0; color: #5B6B7F; }
.fs-btn--save  { background: #27AE60; color: #fff; }

.fs-manual-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.fs-manual-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }
.fs-row { display: flex; gap: 16rpx; margin-bottom: 16rpx; }
.fs-field { flex: 1; }
.fs-field.flex2 { flex: 2; }
.fs-field-label  { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 8rpx; }
.fs-field-input  { width: 100%; background: #F5F6FA; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 26rpx; box-sizing: border-box; }
.fs-field-picker { background: #F5F6FA; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 26rpx; color: #2C3E50; }
.fs-submit-btn { margin-top: 8rpx; background: #27AE60; color: #fff; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.fs-submit-btn--loading { background: #A9DFBF; }

.fs-summary-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.fs-summary-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.fs-summary-row { display: flex; }
.fs-sum-item { flex: 1; text-align: center; }
.fs-sum-val   { display: block; font-size: 36rpx; font-weight: 700; }
.fs-sum-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
</style>
