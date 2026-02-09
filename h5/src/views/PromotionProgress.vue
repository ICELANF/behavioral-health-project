<template>
  <div class="promotion-progress">
    <van-nav-bar title="晋级进度" left-arrow @click-left="$router.back()" />

    <!-- 当前等级 -->
    <div class="level-card">
      <div class="level-title">当前角色</div>
      <div class="level-name">{{ currentRole }}</div>
      <div class="level-arrow" v-if="nextRole">→ {{ nextRole }}</div>
    </div>

    <!-- 四维雷达图 -->
    <div class="radar-card" v-if="rule">
      <div ref="radarChartRef" class="radar-chart"></div>
    </div>

    <!-- 四维进度 -->
    <van-cell-group title="晋级条件进度" inset>
      <!-- 学分 -->
      <div class="progress-section">
        <div class="section-title">学分</div>
        <van-cell title="总学分">
          <template #value>
            <van-progress
              :percentage="calcPercent(progress.total_credits, rule?.credits?.total_min)"
              stroke-width="8"
              :show-pivot="false"
            />
            <span class="progress-text">{{ progress.total_credits || 0 }} / {{ rule?.credits?.total_min || '-' }}</span>
          </template>
        </van-cell>
        <van-cell title="必修学分">
          <template #value>
            <van-progress
              :percentage="calcPercent(progress.mandatory_credits, rule?.credits?.mandatory_min)"
              stroke-width="8"
              :show-pivot="false"
            />
            <span class="progress-text">{{ progress.mandatory_credits || 0 }} / {{ rule?.credits?.mandatory_min || '-' }}</span>
          </template>
        </van-cell>
      </div>

      <!-- 积分 -->
      <div class="progress-section">
        <div class="section-title">积分</div>
        <van-cell title="成长积分">
          <template #value>
            <van-progress
              :percentage="calcPercent(progress.growth_points, rule?.points?.growth_min)"
              stroke-width="8"
              color="#52c41a"
              :show-pivot="false"
            />
            <span class="progress-text">{{ progress.growth_points || 0 }} / {{ rule?.points?.growth_min || '-' }}</span>
          </template>
        </van-cell>
        <van-cell title="贡献积分">
          <template #value>
            <van-progress
              :percentage="calcPercent(progress.contribution_points, rule?.points?.contribution_min)"
              stroke-width="8"
              color="#fa8c16"
              :show-pivot="false"
            />
            <span class="progress-text">{{ progress.contribution_points || 0 }} / {{ rule?.points?.contribution_min || '-' }}</span>
          </template>
        </van-cell>
        <van-cell title="影响力积分">
          <template #value>
            <van-progress
              :percentage="calcPercent(progress.influence_points, rule?.points?.influence_min)"
              stroke-width="8"
              color="#722ed1"
              :show-pivot="false"
            />
            <span class="progress-text">{{ progress.influence_points || 0 }} / {{ rule?.points?.influence_min || '-' }}</span>
          </template>
        </van-cell>
      </div>

      <!-- 同道者 -->
      <div class="progress-section">
        <div class="section-title">同道者</div>
        <van-cell title="毕业同道者">
          <template #value>
            <van-progress
              :percentage="calcPercent(progress.companions_graduated, rule?.companions?.graduated_min)"
              stroke-width="8"
              color="#eb2f96"
              :show-pivot="false"
            />
            <span class="progress-text">{{ progress.companions_graduated || 0 }} / {{ rule?.companions?.graduated_min || '-' }}</span>
          </template>
        </van-cell>
      </div>
    </van-cell-group>

    <!-- 申请按钮 -->
    <div class="apply-section">
      <van-button
        type="primary"
        block
        round
        size="large"
        :loading="applying"
        :disabled="!canApply"
        @click="handleApply"
      >
        {{ canApply ? '申请晋级' : '条件未达标' }}
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import * as echarts from 'echarts'
import { promotionApi } from '@/api/credit-promotion'

const progress = ref<Record<string, any>>({})
const rule = ref<Record<string, any> | null>(null)
const eligibility = ref<Record<string, any> | null>(null)
const applying = ref(false)
const radarChartRef = ref<HTMLElement | null>(null)
let radarChart: echarts.ECharts | null = null

const currentRole = computed(() => {
  const r = progress.value.current_role || progress.value.from_role || '-'
  return roleLabel(r)
})

const nextRole = computed(() => {
  return rule.value ? roleLabel(rule.value.to_role) : ''
})

const canApply = computed(() => {
  return eligibility.value?.eligible === true
})

function roleLabel(r: string) {
  const map: Record<string, string> = {
    observer: '观察者', grower: '成长者', sharer: '分享者',
    coach: '教练', promoter: '推广者', master: '大师',
    OBSERVER: '观察者', GROWER: '成长者', SHARER: '分享者',
    COACH: '教练', PROMOTER: '推广者', MASTER: '大师',
  }
  return map[r] || r
}

function calcPercent(current: number | undefined, required: number | undefined) {
  if (!required || required === 0) return 0
  const c = current || 0
  return Math.min(Math.round((c / required) * 100), 100)
}

async function loadProgress() {
  try {
    const res = await promotionApi.getProgress()
    progress.value = res
    rule.value = res.next_level_rule || null
  } catch (e) {
    console.error('加载进度失败', e)
  }
}

async function checkEligibility() {
  try {
    const res = await promotionApi.checkEligibility()
    eligibility.value = res
  } catch (e) {
    console.error('校验失败', e)
  }
}

async function handleApply() {
  applying.value = true
  try {
    await promotionApi.apply()
    showSuccessToast('晋级申请已提交')
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (typeof detail === 'object' && detail.message) {
      showToast(detail.message)
    } else {
      showToast('申请失败')
    }
  } finally {
    applying.value = false
  }
}

function renderRadar() {
  if (!radarChartRef.value || !rule.value) return

  if (!radarChart) {
    radarChart = echarts.init(radarChartRef.value)
  }

  const r = rule.value
  const p = progress.value

  const indicators = [
    { name: '学分', max: r.credits?.total_min || 100 },
    { name: '成长积分', max: r.points?.growth_min || 100 },
    { name: '贡献积分', max: r.points?.contribution_min || 100 },
    { name: '影响力', max: r.points?.influence_min || 100 },
    { name: '同道者', max: r.companions?.graduated_min || 4 },
  ]

  const values = [
    Math.min(p.total_credits || 0, indicators[0].max),
    Math.min(p.growth_points || 0, indicators[1].max),
    Math.min(p.contribution_points || 0, indicators[2].max),
    Math.min(p.influence_points || 0, indicators[3].max),
    Math.min(p.companions_graduated || 0, indicators[4].max),
  ]

  radarChart.setOption({
    radar: {
      indicator: indicators,
      shape: 'polygon',
      radius: '65%',
      axisName: { color: '#666', fontSize: 11 },
      splitArea: { areaStyle: { color: ['rgba(24,144,255,0.05)', 'rgba(24,144,255,0.1)'] } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: values,
            name: '当前进度',
            areaStyle: { color: 'rgba(24,144,255,0.3)' },
            lineStyle: { color: '#1890ff' },
            itemStyle: { color: '#1890ff' },
          },
          {
            value: indicators.map((i) => i.max),
            name: '晋级要求',
            lineStyle: { color: '#fa541c', type: 'dashed' },
            itemStyle: { color: '#fa541c' },
            areaStyle: { color: 'rgba(250,84,28,0.05)' },
          },
        ],
      },
    ],
    legend: {
      data: ['当前进度', '晋级要求'],
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
  })
}

watch([progress, rule], () => {
  nextTick(renderRadar)
})

onMounted(() => {
  loadProgress()
  checkEligibility()
})
</script>

<style scoped>
.promotion-progress {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 80px;
}
.level-card {
  margin: 12px 16px;
  padding: 20px;
  background: linear-gradient(135deg, #faad14, #fa541c);
  border-radius: 12px;
  color: #fff;
  text-align: center;
}
.level-title { font-size: 12px; opacity: 0.8; }
.level-name { font-size: 28px; font-weight: bold; margin: 4px 0; }
.level-arrow { font-size: 16px; opacity: 0.9; }
.radar-card {
  margin: 12px 16px;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
}
.radar-chart {
  width: 100%;
  height: 280px;
}
.progress-section {
  padding: 0 0 8px 0;
}
.section-title {
  padding: 12px 16px 4px;
  font-size: 13px;
  color: #999;
  font-weight: 500;
}
.progress-text {
  font-size: 12px;
  color: #666;
  display: block;
  text-align: right;
  margin-top: 2px;
}
.apply-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
}
</style>
