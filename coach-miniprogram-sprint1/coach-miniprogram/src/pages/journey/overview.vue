<template>
  <view class="overview-page">

    <!-- 用户当前等级横幅 -->
    <view class="overview-banner">
      <view class="overview-banner__inner" :style="{ background: currentMeta.color }">
        <view class="overview-banner__icon-wrap">
          <text class="overview-banner__icon">{{ currentMeta.icon }}</text>
        </view>
        <view class="overview-banner__text">
          <text class="overview-banner__level">{{ currentMeta.label }}</text>
          <text class="overview-banner__name">{{ userStore.displayName }}</text>
        </view>
        <view class="overview-banner__actions">
          <view class="overview-banner__btn" @tap="goProgress">
            <text>我的进度 ›</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 成长路径 — 纵向时间线 -->
    <view class="overview-path px-4">
      <text class="overview-path__title">六级成长体系</text>

      <view class="overview-timeline">
        <view
          v-for="(level, idx) in LEVELS"
          :key="level.key"
          class="overview-node"
          :class="{
            'overview-node--done':    getLevelNum(level.key) < currentLevelNum,
            'overview-node--current': getLevelNum(level.key) === currentLevelNum,
            'overview-node--locked':  getLevelNum(level.key) > currentLevelNum,
          }"
          @tap="expandLevel(level.key)"
        >
          <!-- 连接线（非最后一个）-->
          <view class="overview-node__connector" v-if="idx < LEVELS.length - 1">
            <view
              class="overview-node__connector-fill"
              :style="{ height: getLevelNum(level.key) < currentLevelNum ? '100%' : '0%' }"
            ></view>
          </view>

          <!-- 节点圆 -->
          <view class="overview-node__dot-wrap">
            <view
              class="overview-node__dot"
              :style="{
                background: getLevelNum(level.key) <= currentLevelNum ? level.color : '#e5e7eb',
                boxShadow: getLevelNum(level.key) === currentLevelNum
                  ? `0 0 0 6rpx ${level.color}33`
                  : 'none'
              }"
            >
              <text class="overview-node__dot-icon">
                {{ getLevelNum(level.key) < currentLevelNum ? '✓' : level.icon }}
              </text>
            </view>
          </view>

          <!-- 节点内容 -->
          <view class="overview-node__content">
            <view class="overview-node__header">
              <text
                class="overview-node__label"
                :style="{ color: getLevelNum(level.key) <= currentLevelNum ? level.color : '#9ca3af' }"
              >{{ level.label }}</text>
              <text class="overview-node__status" v-if="getLevelNum(level.key) === currentLevelNum">● 当前</text>
              <text class="overview-node__status overview-node__status--done" v-else-if="getLevelNum(level.key) < currentLevelNum">✓ 已达成</text>
            </view>

            <!-- 展开：要求列表 -->
            <view class="overview-node__reqs" v-if="expandedLevel === level.key && level.req">
              <view
                v-for="req in buildReqList(level.key)"
                :key="req.label"
                class="overview-node__req-item"
              >
                <text class="overview-node__req-icon">{{ req.icon }}</text>
                <text class="overview-node__req-text">{{ req.text }}</text>
              </view>
            </view>
            <!-- 收起：简短摘要 -->
            <text
              class="overview-node__summary"
              v-else-if="level.key !== 'L0'"
            >
              {{ buildSummary(level.key) }}
            </text>

            <!-- 展开/收起按钮（非 L0）-->
            <view
              class="overview-node__toggle"
              v-if="level.key !== 'L0'"
              @tap.stop="expandLevel(level.key)"
            >
              <text>{{ expandedLevel === level.key ? '收起 ▲' : '查看要求 ▼' }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 四同道者说明 -->
    <view class="overview-companion px-4">
      <view class="overview-companion__card bhp-card bhp-card--flat">
        <text class="overview-companion__title">四同道者体系</text>
        <text class="overview-companion__desc">
          L3及以上等级的晋升，需要与 4 位同道者建立同伴关系。同道者等级需达到当前目标等级的上一级。
        </text>
        <view class="overview-companion__levels">
          <view class="overview-companion__level-item" v-for="cl in companionLevels" :key="cl.target">
            <text class="overview-companion__level-text">{{ cl.target }} 晋升</text>
            <text class="overview-companion__level-req">需 4 位 ≥{{ cl.minLevel }} 同道者</text>
          </view>
        </view>
        <view class="overview-companion__btn" @tap="goCompanions">
          <text>查看我的同道者 ›</text>
        </view>
      </view>
    </view>

    <!-- 快捷操作 -->
    <view class="overview-shortcuts px-4">
      <view class="overview-shortcut-btn" @tap="goProgress">
        <text class="overview-shortcut-btn__icon">📊</text>
        <text class="overview-shortcut-btn__label">我的进度</text>
      </view>
      <view class="overview-shortcut-btn" @tap="goPromotion">
        <text class="overview-shortcut-btn__icon">🚀</text>
        <text class="overview-shortcut-btn__label">申请晋级</text>
      </view>
      <view class="overview-shortcut-btn" @tap="goHistory">
        <text class="overview-shortcut-btn__icon">📋</text>
        <text class="overview-shortcut-btn__label">申请记录</text>
      </view>
      <view class="overview-shortcut-btn" @tap="goCatalog">
        <text class="overview-shortcut-btn__icon">📚</text>
        <text class="overview-shortcut-btn__label">课程目录</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { LEVEL_META, LEVEL_THRESHOLDS } from '@/api/journey'

const userStore = useUserStore()

const expandedLevel = ref<string | null>(null)

// 角色→等级数字
const ROLE_TO_LEVEL: Record<string, number> = {
  observer: 0, grower: 1, sharer: 2, coach: 3, promoter: 4, supervisor: 4, master: 5
}

const currentLevelNum = computed(() =>
  ROLE_TO_LEVEL[userStore.role] ?? 0
)

const currentMeta = computed(() => {
  const key = `L${currentLevelNum.value}`
  return LEVEL_META[key] || LEVEL_META['L0']
})

const LEVELS = [
  { key: 'L0', label: 'L0 观察员', icon: '👁',  color: '#8c8c8c', req: false },
  { key: 'L1', label: 'L1 成长者', icon: '🌱', color: '#52c41a', req: true },
  { key: 'L2', label: 'L2 分享者', icon: '🌿', color: '#1890ff', req: true },
  { key: 'L3', label: 'L3 教练',   icon: '🏋️', color: '#722ed1', req: true },
  { key: 'L4', label: 'L4 促进师', icon: '🌟', color: '#eb2f96', req: true },
  { key: 'L5', label: 'L5 大师',   icon: '🏆', color: '#faad14', req: true },
]

const companionLevels = [
  { target: 'L3', minLevel: 'L1' },
  { target: 'L4', minLevel: 'L2' },
  { target: 'L5', minLevel: 'L3' },
]

function getLevelNum(key: string): number {
  return parseInt(key.replace('L', '')) || 0
}

function expandLevel(key: string) {
  expandedLevel.value = expandedLevel.value === key ? null : key
}

function buildReqList(levelKey: string) {
  const req = LEVEL_THRESHOLDS[levelKey]
  if (!req) return []
  const items: { icon: string; text: string }[] = []
  if (req.growth > 0)       items.push({ icon: '🌱', text: `成长积分 ≥ ${req.growth}` })
  if (req.contribution > 0) items.push({ icon: '🌿', text: `贡献积分 ≥ ${req.contribution}` })
  if (req.influence > 0)    items.push({ icon: '⭐', text: `影响积分 ≥ ${req.influence}` })
  if (req.exam)             items.push({ icon: '📝', text: '通过等级认证考试' })
  if (req.companions > 0)   items.push({ icon: '👥', text: `${req.companions} 位≥${req.companion_min_level}同道者` })
  return items
}

function buildSummary(levelKey: string): string {
  const req = LEVEL_THRESHOLDS[levelKey]
  if (!req) return ''
  const parts: string[] = []
  if (req.growth > 0)     parts.push(`成长积分${req.growth}`)
  if (req.contribution > 0) parts.push(`贡献积分${req.contribution}`)
  if (req.exam)           parts.push('认证考试')
  if (req.companions > 0) parts.push(`${req.companions}位同道者`)
  return parts.join(' · ')
}

function goProgress()    { uni.navigateTo({ url: '/pages/journey/progress' }) }
function goPromotion()   { uni.navigateTo({ url: '/pages/journey/promotion' }) }
function goHistory()     { uni.navigateTo({ url: '/pages/journey/history' }) }
function goCompanions()  { uni.navigateTo({ url: '/pages/companions/index' }) }
function goCatalog()     { uni.navigateTo({ url: '/pages/learning/catalog' }) }
</script>

<style scoped>
.overview-page { background: var(--surface-secondary); min-height: 100vh; }

/* 横幅 */
.overview-banner { margin-bottom: 16rpx; }
.overview-banner__inner {
  padding: 48rpx 32rpx 40rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}
.overview-banner__icon-wrap {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: rgba(255,255,255,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
}
.overview-banner__icon  { font-size: 48rpx; }
.overview-banner__text  { flex: 1; }
.overview-banner__level { display: block; font-size: 30rpx; font-weight: 700; color: #fff; }
.overview-banner__name  { display: block; font-size: 22rpx; color: rgba(255,255,255,0.85); margin-top: 4rpx; }
.overview-banner__btn {
  background: rgba(255,255,255,0.25);
  border-radius: var(--radius-full);
  padding: 8rpx 20rpx;
  font-size: 22rpx;
  color: #fff;
  cursor: pointer;
}

/* 路径标题 */
.overview-path { padding-top: 8rpx; }
.overview-path__title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 20rpx;
}

/* 时间线 */
.overview-timeline { position: relative; }

.overview-node {
  display: flex;
  gap: 0;
  position: relative;
  margin-bottom: 0;
}

/* 连接线 */
.overview-node__connector {
  position: absolute;
  left: 27rpx;
  top: 56rpx;
  width: 4rpx;
  height: 100%;
  background: var(--bhp-gray-200);
  z-index: 0;
  overflow: hidden;
}
.overview-node__connector-fill {
  width: 100%;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
  transition: height 0.4s;
}

/* 节点圆 */
.overview-node__dot-wrap {
  width: 58rpx;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  padding-top: 4rpx;
  z-index: 1;
}
.overview-node__dot {
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: box-shadow 0.3s;
}
.overview-node__dot-icon { font-size: 26rpx; }

/* 内容 */
.overview-node__content {
  flex: 1;
  padding: 0 0 28rpx 16rpx;
}
.overview-node__header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 8rpx; }
.overview-node__label { font-size: 28rpx; font-weight: 700; }
.overview-node__status {
  font-size: 20rpx;
  color: var(--bhp-primary-500);
  background: var(--bhp-primary-50);
  padding: 2rpx 12rpx;
  border-radius: var(--radius-full);
}
.overview-node__status--done {
  color: var(--bhp-success-600, #16a34a);
  background: var(--bhp-success-50, #f0fdf4);
}

/* 要求列表 */
.overview-node__reqs { display: flex; flex-direction: column; gap: 8rpx; margin-bottom: 8rpx; }
.overview-node__req-item { display: flex; align-items: center; gap: 8rpx; }
.overview-node__req-icon { font-size: 24rpx; }
.overview-node__req-text { font-size: 24rpx; color: var(--text-secondary); }

.overview-node__summary { font-size: 22rpx; color: var(--text-tertiary); line-height: 1.5; }

.overview-node__toggle {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
  display: inline-block;
}

/* 暗色（锁定）*/
.overview-node--locked .overview-node__label { color: #9ca3af !important; }
.overview-node--locked .overview-node__summary { color: #d1d5db; }

/* 四同道者说明 */
.overview-companion { padding-top: 8rpx; }
.overview-companion__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12rpx;
}
.overview-companion__desc { display: block; font-size: 24rpx; color: var(--text-secondary); line-height: 1.6; margin-bottom: 16rpx; }
.overview-companion__levels { display: flex; flex-direction: column; gap: 8rpx; margin-bottom: 16rpx; }
.overview-companion__level-item { display: flex; justify-content: space-between; align-items: center; }
.overview-companion__level-text { font-size: 24rpx; color: var(--text-primary); font-weight: 500; }
.overview-companion__level-req  { font-size: 22rpx; color: var(--text-secondary); }
.overview-companion__btn {
  font-size: 24rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
}

/* 快捷操作 */
.overview-shortcuts {
  padding-top: 16rpx;
  display: flex;
  gap: 12rpx;
}
.overview-shortcut-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 20rpx 12rpx;
  cursor: pointer;
  box-shadow: var(--shadow-card);
}
.overview-shortcut-btn:active { opacity: 0.7; }
.overview-shortcut-btn__icon  { font-size: 36rpx; }
.overview-shortcut-btn__label { font-size: 20rpx; color: var(--text-secondary); }
</style>
