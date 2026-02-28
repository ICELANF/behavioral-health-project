<template>
  <view class="jo-page">

    <!-- 导航栏 -->
    <view class="jo-navbar safe-area-top">
      <view class="jo-navbar__back" @tap="goBack">
        <text class="jo-navbar__arrow">‹</text>
      </view>
      <text class="jo-navbar__title">成长路径</text>
      <view class="jo-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="jo-body">

      <!-- 当前等级大卡片 -->
      <view class="jo-hero">
        <view class="jo-hero__badge" :style="{ background: currentColor + '18', borderColor: currentColor }">
          <text class="jo-hero__level" :style="{ color: currentColor }">L{{ currentLevel }}</text>
        </view>
        <text class="jo-hero__name">{{ currentLevelLabel }}</text>
        <text class="jo-hero__desc">{{ levelDescriptions[currentLevel] || '' }}</text>
      </view>

      <!-- 六级路径垂直时间线 -->
      <view class="jo-card">
        <text class="jo-card__title">六级四同道路径</text>
        <view class="jo-timeline">
          <view
            v-for="(stage, idx) in STAGES"
            :key="stage.key"
            class="jo-tl-item"
            :class="{
              'jo-tl-item--done': stage.level < currentLevel,
              'jo-tl-item--active': stage.level === currentLevel,
              'jo-tl-item--future': stage.level > currentLevel,
            }"
          >
            <!-- 连线 -->
            <view class="jo-tl-rail" v-if="idx > 0">
              <view
                class="jo-tl-rail__fill"
                :style="{ height: stage.level <= currentLevel ? '100%' : '0%' }"
              ></view>
            </view>
            <!-- 节点 -->
            <view class="jo-tl-dot">
              <text v-if="stage.level < currentLevel" class="jo-tl-dot__check">✓</text>
              <text v-else class="jo-tl-dot__num">{{ stage.level }}</text>
            </view>
            <!-- 内容 -->
            <view class="jo-tl-content">
              <text class="jo-tl-content__name">{{ stage.label }}</text>
              <text class="jo-tl-content__cond" v-if="stage.level > currentLevel">{{ stage.requirement }}</text>
              <text class="jo-tl-content__tag" v-else-if="stage.level === currentLevel">当前等级</text>
              <text class="jo-tl-content__tag jo-tl-content__tag--done" v-else>已达成</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 三维积分总览 -->
      <view class="jo-card">
        <text class="jo-card__title">三维积分</text>
        <view class="jo-points">
          <view class="jo-points__item" v-for="pt in pointCards" :key="pt.key">
            <text class="jo-points__val" :style="{ color: pt.color }">{{ pt.value }}</text>
            <text class="jo-points__label">{{ pt.label }}</text>
          </view>
        </view>
      </view>

      <!-- 查看晋级详情按钮 -->
      <view class="jo-action">
        <view class="jo-action__btn" @tap="goProgress">
          <text>查看晋级详情</text>
        </view>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'
import { ROLE_COLOR, LEVEL_LABEL, formatPoints } from '@/utils/level'

const STAGES = [
  { key: 'observer',   level: 1, label: 'L1 观察者', requirement: '完成注册即可' },
  { key: 'grower',     level: 2, label: 'L2 成长者', requirement: '成长积分 ≥ 100' },
  { key: 'sharer',     level: 3, label: 'L3 分享者', requirement: '成长积分 ≥ 500，邀请 1 位同道者' },
  { key: 'coach',      level: 4, label: 'L4 教练',   requirement: '成长积分 ≥ 800，通过教练认证考试' },
  { key: 'promoter',   level: 5, label: 'L5 促进师', requirement: '贡献积分 ≥ 1500，督导 3 位教练' },
  { key: 'master',     level: 6, label: 'L6 大师',   requirement: '综合积分 ≥ 3000，学术论文发表' },
]

const levelDescriptions: Record<number, string> = {
  1: '开启行为健康之旅，观察与记录是第一步',
  2: '持续成长，建立健康行为习惯',
  3: '分享健康知识，帮助身边的人',
  4: '成为专业教练，指导他人行为改变',
  5: '引领社区，培养更多教练',
  6: '行为健康大师，推动学术与实践',
}

const overview = ref<any>(null)

const currentLevel = computed(() => overview.value?.current_level ?? 1)
const currentLevelLabel = computed(() => LEVEL_LABEL[currentLevel.value] || '观察者')
const currentColor = computed(() => {
  const stage = STAGES.find(s => s.level === currentLevel.value)
  return stage ? (ROLE_COLOR[stage.key] || '#10b981') : '#10b981'
})

const pointCards = computed(() => [
  { key: 'growth',       label: '成长积分', value: formatPoints(overview.value?.growth_points ?? 0),       color: '#10b981' },
  { key: 'contribution', label: '贡献积分', value: formatPoints(overview.value?.contribution_points ?? 0), color: '#3b82f6' },
  { key: 'influence',    label: '影响力积分', value: formatPoints(overview.value?.influence_points ?? 0),    color: '#8b5cf6' },
])

onMounted(async () => {
  await loadOverview()
})

async function loadOverview() {
  try {
    const res = await http.get<any>('/v1/journey/state')
    overview.value = res
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function goProgress() {
  uni.navigateTo({ url: '/pages/journey/progress' })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.jo-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.jo-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.jo-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.jo-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.jo-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.jo-navbar__placeholder { width: 64rpx; }

.jo-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

/* 当前等级大卡片 */
.jo-hero {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 40rpx 32rpx; margin-bottom: 20rpx;
  display: flex; flex-direction: column; align-items: center;
  border: 1px solid var(--border-light);
}
.jo-hero__badge {
  width: 120rpx; height: 120rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 4rpx solid; margin-bottom: 16rpx;
}
.jo-hero__level { font-size: 40rpx; font-weight: 800; }
.jo-hero__name { font-size: 36rpx; font-weight: 800; color: var(--text-primary); margin-bottom: 8rpx; }
.jo-hero__desc { font-size: 26rpx; color: var(--text-secondary); text-align: center; line-height: 1.5; }

/* 卡片 */
.jo-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light);
}
.jo-card__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block; margin-bottom: 20rpx; }

/* 时间线 */
.jo-timeline { padding-left: 8rpx; }

.jo-tl-item {
  display: flex; align-items: flex-start; gap: 20rpx; position: relative;
  padding-bottom: 32rpx;
}
.jo-tl-item:last-child { padding-bottom: 0; }

/* 连线轨道 */
.jo-tl-rail {
  position: absolute; left: 20rpx; top: -32rpx; width: 4rpx; height: 32rpx;
  background: var(--bhp-gray-200); overflow: hidden;
}
.jo-tl-rail__fill { width: 100%; background: var(--bhp-primary-500); transition: height 0.5s; }

/* 圆点 */
.jo-tl-dot {
  width: 44rpx; height: 44rpx; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700; z-index: 2;
  background: var(--bhp-gray-200); color: var(--text-tertiary);
  border: 3rpx solid var(--bhp-gray-300);
}
.jo-tl-dot__check { color: #fff; font-size: 24rpx; }
.jo-tl-dot__num { font-size: 20rpx; }

.jo-tl-item--done .jo-tl-dot {
  background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff;
}
.jo-tl-item--active .jo-tl-dot {
  background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff;
  box-shadow: 0 0 0 6rpx rgba(16,185,129,0.2);
}

/* 内容 */
.jo-tl-content { flex: 1; padding-top: 4rpx; }
.jo-tl-content__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block; }
.jo-tl-content__cond { font-size: 24rpx; color: var(--text-tertiary); display: block; margin-top: 4rpx; }
.jo-tl-content__tag {
  display: inline-block; font-size: 20rpx; font-weight: 700; color: var(--bhp-primary-500);
  background: rgba(16,185,129,0.1); padding: 2rpx 16rpx; border-radius: var(--radius-full); margin-top: 4rpx;
}
.jo-tl-content__tag--done { color: var(--text-tertiary); background: var(--bhp-gray-100); }

.jo-tl-item--future .jo-tl-content__name { color: var(--text-tertiary); }

/* 三维积分 */
.jo-points { display: flex; gap: 16rpx; }
.jo-points__item {
  flex: 1; background: var(--surface-secondary); border-radius: var(--radius-md);
  padding: 20rpx 16rpx; display: flex; flex-direction: column; align-items: center; gap: 6rpx;
}
.jo-points__val { font-size: 36rpx; font-weight: 800; }
.jo-points__label { font-size: 22rpx; color: var(--text-secondary); }

/* 底部按钮 */
.jo-action { padding: 8rpx 0 40rpx; }
.jo-action__btn {
  width: 100%; height: 88rpx; border-radius: var(--radius-lg);
  background: var(--bhp-primary-500); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700; cursor: pointer;
}
.jo-action__btn:active { opacity: 0.85; }
</style>
