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
          <text class="fs-ai-tip-text">💡 AI通过照片识别食物种类与热量，拍照后可补充烹饪方式以提升精度。预包装食品请拍营养成分表标签。</text>
        </view>

        <!-- 拍照前配置（餐次 + 预包装开关） -->
        <view v-if="!photoResult">
          <view class="fs-config-row">
            <view class="fs-config-item">
              <text class="fs-config-label">餐次</text>
              <picker :range="mealLabels" :value="mealIdx" @change="mealIdx = $event.detail.value">
                <view class="fs-config-picker">{{ mealLabels[mealIdx] }} ▾</view>
              </picker>
            </view>
            <view class="fs-config-item fs-config-item--toggle">
              <text class="fs-config-label">预包装食品</text>
              <switch :checked="isPackaged" @change="isPackaged = ($event as any).detail.value" color="#1565C0" style="transform:scale(0.85)" />
            </view>
          </view>
          <view class="fs-photo-area" @tap="takePhoto">
            <text class="fs-photo-icon">{{ isPackaged ? '🏷️' : '📷' }}</text>
            <text class="fs-photo-hint">{{ isPackaged ? '拍摄营养成分表标签' : '拍照或从相册选择' }}</text>
            <text class="fs-photo-sub">拍照后将提示选择烹饪方式</text>
          </view>
        </view>

        <!-- 识别结果 -->
        <view v-else class="fs-result-area">
          <image class="fs-food-image" :src="photoPreview" mode="aspectFill" />
          <!-- 烹饪方式标签（可重新选） -->
          <view class="fs-cooking-tag" @tap="reopenCookingModal">
            <text class="fs-cooking-tag-text">{{ cookingIdx > 0 ? '🍳 ' + cookingMethods[cookingIdx].label : '🍳 未选烹饪方式（点击补充）' }}</text>
          </view>
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
              <view class="fs-btn fs-btn--retry" @tap="resetPhoto">重新拍摄</view>
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

      <!-- 今日摄入 + 热量平衡入口 -->
      <view class="fs-summary-card">
        <view class="fs-summary-header">
          <text class="fs-card-title" style="margin-bottom:0;">📊 今日摄入</text>
          <view class="fs-diary-link" @tap="goDiary">
            <text class="fs-diary-link-text">热量平衡 →</text>
          </view>
        </view>
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
        <view class="fs-balance-hint">
          <text class="fs-balance-hint-text">💡 饮食日记中可查看今日热量平衡审计（摄入 vs 支出）</text>
        </view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>

    <!-- 烹饪方式弹窗（拍照后自动弹出） -->
    <view v-if="cookingModal" class="fs-mask">
      <view class="fs-cooking-modal" @tap.stop>
        <text class="fs-modal-title">请选择烹饪方式</text>
        <text class="fs-modal-sub">烹饪方式有助于AI更准确估算热量</text>
        <view class="fs-cooking-grid">
          <view
            v-for="m in cookingOptions"
            :key="m.idx"
            class="fs-cooking-opt"
            :class="{ 'fs-cooking-opt--active': cookingIdx === m.idx }"
            @tap="selectCooking(m.idx)"
          >
            <text class="fs-cooking-opt-icon">{{ m.icon }}</text>
            <text class="fs-cooking-opt-label">{{ m.label }}</text>
          </view>
        </view>
        <view class="fs-modal-skip" @tap="selectCooking(0)">跳过 · AI自行估算</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { httpReq as http, getToken, apiHost as API_HOST } from '@/api/request'

const mealTypes = [
  { label: '早餐',     key: 'breakfast' },
  { label: '上午点心', key: 'morning_snack' },
  { label: '午餐',     key: 'lunch' },
  { label: '下午点心', key: 'afternoon_snack' },
  { label: '晚餐',     key: 'dinner' },
  { label: '夜宵',     key: 'supper' },
]
const mealLabels = mealTypes.map(m => m.label)

// idx 0 = 未选择（留给"跳过"）, 1-8 = 实际方式
const cookingMethods = [
  { label: '未选择',   key: '' },
  { label: '蒸',       key: '蒸' },
  { label: '煮',       key: '煮' },
  { label: '炒',       key: '炒' },
  { label: '炸',       key: '炸' },
  { label: '烤/煎',    key: '烤煎' },
  { label: '凉拌/生食', key: '凉拌生食' },
  { label: '汤/炖',    key: '汤炖' },
  { label: '其他',     key: '其他' },
]
// 弹窗显示项（含 emoji + 在 cookingMethods 中的 idx）
const cookingOptions: Array<{ idx: number; label: string; icon: string }> = [
  { idx: 1, label: '蒸',       icon: '♨️' },
  { idx: 2, label: '煮',       icon: '🫕' },
  { idx: 3, label: '炒',       icon: '🥘' },
  { idx: 4, label: '炸',       icon: '🍟' },
  { idx: 5, label: '烤/煎',    icon: '🍳' },
  { idx: 6, label: '凉拌/生食', icon: '🥗' },
  { idx: 7, label: '汤/炖',    icon: '🍲' },
  { idx: 8, label: '其他',     icon: '🍽️' },
]

const mealIdx        = ref(0)
const cookingIdx     = ref(0)
const isPackaged     = ref(false)
const showDetail     = ref(false)
const cookingModal   = ref(false)
const pendingFile    = ref('')          // 等待烹饪方式选择的临时文件路径
const photoPreview   = ref('')
const photoResult    = ref<any>(null)
const submitting     = ref(false)
const manualForm     = reactive({ name: '', calories: '', carbs: '', protein: '', fat: '' })
const todaySummary   = ref({ calories: 0, carbs: 0, protein: 0, fat: 0 })

// ── 拍照 → 弹出烹饪方式弹窗（预包装食品跳过） ──────────────
function takePhoto() {
  uni.chooseImage({
    count: 1,
    sourceType: ['camera', 'album'],
    success: (res) => {
      const filePath = res.tempFilePaths[0]
      photoPreview.value = filePath
      pendingFile.value  = filePath
      cookingIdx.value   = 0         // 每次重置

      if (isPackaged.value) {
        // 预包装：无需选烹饪方式，直接分析
        analyzePhoto(filePath)
      } else {
        // 普通食物：弹出烹饪方式弹窗
        cookingModal.value = true
      }
    },
  })
}

// 用户在弹窗选择烹饪方式（0 = 跳过）
function selectCooking(idx: number) {
  cookingIdx.value   = idx
  cookingModal.value = false
  analyzePhoto(pendingFile.value)
}

// 结果页点击烹饪方式标签 → 重新弹窗
function reopenCookingModal() {
  if (!pendingFile.value) return
  cookingModal.value = true
}

// 重新拍摄
function resetPhoto() {
  photoResult.value  = null
  photoPreview.value = ''
  pendingFile.value  = ''
  cookingIdx.value   = 0
}

// ── AI 分析 ───────────────────────────────────────────────────
async function analyzePhoto(filePath: string) {
  uni.showLoading({ title: 'AI识别中…' })
  try {
    const uploadRes: any = await new Promise((resolve, reject) => {
      uni.uploadFile({
        url: API_HOST + '/api/v1/food/analyze',
        filePath,
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
    resetPhoto()
    loadSummary()
    uni.showToast({ title: '已保存，可到饮食日记查看热量平衡', icon: 'none', duration: 2500 })
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
          calories: manualForm.calories ? parseInt(manualForm.calories)   : null,
          carbs:    manualForm.carbs    ? parseFloat(manualForm.carbs)    : null,
          protein:  manualForm.protein  ? parseFloat(manualForm.protein)  : null,
          fat:      manualForm.fat      ? parseFloat(manualForm.fat)      : null,
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
      acc.carbs    += (i.nutrition?.carbs    || 0)
      acc.protein  += (i.nutrition?.protein  || 0)
      acc.fat      += (i.nutrition?.fat      || 0)
      return acc
    }, { calories: 0, carbs: 0, protein: 0, fat: 0 })
  } catch (e) { console.warn('[food/scan] loadSummary:', e) }
}

function goDiary() {
  uni.navigateTo({ url: '/food/diary' })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/home/index' })
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
.fs-ai-tip { background: #EEF6FF; border-radius: 12rpx; padding: 14rpx 20rpx; margin-bottom: 16rpx; }
.fs-ai-tip-text { font-size: 22rpx; color: #1565C0; line-height: 1.6; }

/* 配置区 */
.fs-config-row { display: flex; gap: 16rpx; margin-bottom: 12rpx; align-items: flex-end; }
.fs-config-item { flex: 1; }
.fs-config-item--toggle { display: flex; flex-direction: column; }
.fs-config-label { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 6rpx; }
.fs-config-picker { background: #F0F7FF; border-radius: 10rpx; padding: 14rpx 16rpx; font-size: 26rpx; color: #2C3E50; }

/* 拍照区 */
.fs-photo-area { padding: 44rpx; text-align: center; border: 4rpx dashed #BBDEFB; border-radius: 16rpx; }
.fs-photo-icon { display: block; font-size: 76rpx; margin-bottom: 12rpx; }
.fs-photo-hint { display: block; font-size: 30rpx; font-weight: 600; color: #1565C0; }
.fs-photo-sub  { display: block; font-size: 20rpx; color: #90A4AE; margin-top: 6rpx; }

/* 烹饪方式标签（结果页） */
.fs-cooking-tag { background: #FFF8E1; border-radius: 10rpx; padding: 10rpx 16rpx; margin-bottom: 12rpx; display: inline-block; }
.fs-cooking-tag-text { font-size: 24rpx; color: #E65100; }

/* 识别结果 */
.fs-result-area { display: flex; flex-direction: column; }
.fs-food-image  { width: 100%; height: 260rpx; border-radius: 12rpx; margin-bottom: 12rpx; }
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

/* 今日摄入摘要 */
.fs-summary-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16rpx; }
.fs-diary-link { background: #E65100; border-radius: 20rpx; padding: 8rpx 20rpx; }
.fs-diary-link-text { font-size: 22rpx; color: #fff; font-weight: 600; }
.fs-summary-row  { display: flex; align-items: center; margin-bottom: 16rpx; }
.fs-sum-item     { flex: 1; text-align: center; }
.fs-sum-val      { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; }
.fs-sum-label    { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.fs-sum-divider  { width: 1rpx; height: 50rpx; background: #EEF0F3; }
.fs-balance-hint { background: #FFF8E1; border-radius: 10rpx; padding: 12rpx 16rpx; }
.fs-balance-hint-text { font-size: 22rpx; color: #E65100; line-height: 1.5; }

/* 烹饪方式弹窗 */
.fs-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200;
  display: flex; align-items: flex-end;
}
.fs-cooking-modal {
  width: 100%; background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 36rpx 28rpx calc(48rpx + env(safe-area-inset-bottom));
}
.fs-modal-title { display: block; font-size: 32rpx; font-weight: 700; color: #2C3E50; text-align: center; margin-bottom: 8rpx; }
.fs-modal-sub   { display: block; font-size: 22rpx; color: #8E99A4; text-align: center; margin-bottom: 28rpx; }
.fs-cooking-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
  margin-bottom: 24rpx;
}
.fs-cooking-opt {
  display: flex; flex-direction: column; align-items: center;
  background: #F0F7FF; border-radius: 16rpx; padding: 18rpx 8rpx;
  border: 2rpx solid transparent;
}
.fs-cooking-opt--active {
  background: #E3F2FD; border-color: #1565C0;
}
.fs-cooking-opt-icon  { font-size: 36rpx; margin-bottom: 6rpx; }
.fs-cooking-opt-label { font-size: 22rpx; color: #2C3E50; font-weight: 500; }
.fs-modal-skip {
  text-align: center; padding: 20rpx 0;
  font-size: 26rpx; color: #8E99A4; border-top: 1rpx solid #F0F0F0;
}
</style>
