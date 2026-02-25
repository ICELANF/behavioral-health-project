<template>
  <div class="page-container">
    <van-nav-bar title="我的行为状态" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <template v-else-if="profile">
        <!-- 阶段展示 (温暖的进度) -->
        <div class="stage-card card">
          <div class="stage-visual">
            <div class="stage-circle" :class="stageClass">
              <span class="stage-emoji">{{ stageEmoji }}</span>
            </div>
            <h2 class="stage-name">{{ profile.stage?.name }}</h2>
            <p class="stage-desc">{{ profile.stage?.description }}</p>
          </div>

          <!-- 阶段之旅 -->
          <div class="journey-bar">
            <div
              v-for="(s, idx) in stageJourney"
              :key="s.code"
              class="journey-step"
              :class="{ active: s.code === profile.stage?.current, passed: idx < currentStageIdx }"
            >
              <div class="step-circle" />
              <span class="step-name">{{ s.name }}</span>
            </div>
          </div>
        </div>

        <!-- 领域指引卡片 -->
        <div class="domains-section">
          <h3>你的改变方向</h3>
          <div class="domain-cards">
            <div
              v-for="domain in domainCards"
              :key="domain.key"
              class="domain-item card"
            >
              <div class="domain-icon">
                <van-icon :name="domain.icon" size="28" :color="domain.color" />
              </div>
              <div class="domain-info">
                <div class="domain-title">{{ domain.title }}</div>
                <div class="domain-tip">{{ domain.tip }}</div>
              </div>
              <div class="domain-micro" v-if="domain.microAction">
                <span class="micro-label">微行动</span>
                <span class="micro-text">{{ domain.microAction }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 今日微行动快捷入口 -->
        <div class="micro-actions-section">
          <div class="section-header">
            <h3>今日微行动</h3>
            <router-link to="/tasks" class="view-all">查看全部</router-link>
          </div>
          <van-loading v-if="loadingTasks" size="20" />
          <template v-else-if="todayTasks.length > 0">
            <div class="today-progress">
              <span>{{ todayCompleted }}/{{ todayTasks.length }} 已完成</span>
              <van-progress
                :percentage="todayProgressRate"
                stroke-width="4"
                color="#07c160"
                track-color="#ebedf0"
                :show-pivot="false"
              />
            </div>
            <div
              v-for="task in todayTasks.slice(0, 3)"
              :key="task.id"
              class="micro-task-item"
              :class="{ done: task.status === 'completed' }"
            >
              <div class="micro-check" :class="{ checked: task.status === 'completed' }" @click="quickComplete(task)">
                <van-icon v-if="task.status === 'completed'" name="success" />
              </div>
              <div class="micro-info">
                <span class="micro-title">{{ task.title }}</span>
                <van-tag size="small" :type="domainTagType(task.domain)">{{ domainLabel(task.domain) }}</van-tag>
              </div>
            </div>
          </template>
          <div v-else class="micro-empty">
            <span>今日暂无微行动</span>
          </div>
        </div>

        <!-- 重新评估 -->
        <van-button
          type="primary"
          block
          round
          plain
          class="reassess-btn"
          @click="$router.push('/behavior-assessment')"
        >
          重新评估
        </van-button>
      </template>

      <!-- 未评估 -->
      <template v-else>
        <div class="empty-state card">
          <van-icon name="aim" size="64" color="#d9d9d9" />
          <h3>还没有评估数据</h3>
          <p>完成一次行为评估，了解你的改变阶段</p>
          <van-button type="primary" round @click="$router.push('/behavior-assessment')">
            开始评估
          </van-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showSuccessToast } from 'vant'
import api from '@/api/index'

const loading = ref(true)
const loadingTasks = ref(false)
const profile = ref<any>(null)
const todayTasks = ref<any[]>([])

const todayCompleted = computed(() => todayTasks.value.filter(t => t.status === 'completed').length)
const todayProgressRate = computed(() => {
  if (todayTasks.value.length === 0) return 0
  return Math.round((todayCompleted.value / todayTasks.value.length) * 100)
})

function domainLabel(domain: string) {
  const map: Record<string, string> = {
    nutrition: '营养', exercise: '运动', sleep: '睡眠',
    emotion: '情绪', stress: '压力', cognitive: '认知', social: '社交',
  }
  return map[domain] || domain
}
function domainTagType(domain: string) {
  const map: Record<string, string> = {
    nutrition: 'success', exercise: 'warning', sleep: 'primary',
    emotion: 'danger', stress: 'primary',
  }
  return map[domain] || 'default'
}

async function loadTodayTasks() {
  loadingTasks.value = true
  try {
    const res: any = await api.get('/api/v1/micro-actions/today')
    todayTasks.value = res.tasks || []
  } catch {
    todayTasks.value = []
  } finally {
    loadingTasks.value = false
  }
}

async function quickComplete(task: any) {
  if (task.status === 'completed') return
  try {
    await api.post(`/api/v1/micro-actions/${task.id}/complete`)
    task.status = 'completed'
    showSuccessToast('完成!')
  } catch { /* ignore */ }
}

const stageJourney = [
  { code: 'S0', name: '觉醒' },
  { code: 'S1', name: '松动' },
  { code: 'S2', name: '探索' },
  { code: 'S3', name: '准备' },
  { code: 'S4', name: '行动' },
  { code: 'S5', name: '坚持' },
  { code: 'S6', name: '融入' },
]

const STAGE_EMOJIS: Record<string, string> = {
  S0: '\u{1F331}', S1: '\u{1F33F}', S2: '\u{1F33B}',
  S3: '\u{1F33C}', S4: '\u{1F3C3}', S5: '\u{2B50}', S6: '\u{1F308}',
}

const currentStageIdx = computed(() => {
  const code = profile.value?.stage?.current
  return stageJourney.findIndex(s => s.code === code)
})

const stageClass = computed(() => {
  const idx = currentStageIdx.value
  if (idx <= 1) return 'stage-early'
  if (idx <= 3) return 'stage-mid'
  return 'stage-late'
})

const stageEmoji = computed(() => {
  return STAGE_EMOJIS[profile.value?.stage?.current] || '\u{1F331}'
})

// 领域卡片数据
const DOMAIN_CONFIG: Record<string, { title: string; icon: string; color: string; tips: Record<string, string>; microActions: Record<string, string> }> = {
  nutrition: {
    title: '营养管理',
    icon: 'coupon-o',
    color: '#52c41a',
    tips: {
      S0: '每天多喝一杯水，就是好的开始',
      S1: '注意观察一下自己每天吃了什么',
      S2: '试着在一餐中多加一种蔬菜',
      S3: '制定一个简单的每周食谱',
      S4: '坚持记录饮食日志',
      S5: '你已经建立了良好的饮食习惯',
      S6: '分享你的健康食谱给身边的人',
    },
    microActions: {
      S0: '今天多喝一杯水',
      S1: '拍一张你今天吃的午餐',
      S2: '午餐加一种蔬菜',
      S3: '写下明天的午餐计划',
      S4: '记录今天的三餐',
      S5: '尝试一道新的健康菜谱',
      S6: '帮助一位朋友规划一餐',
    },
  },
  exercise: {
    title: '运动养成',
    icon: 'fire-o',
    color: '#fa8c16',
    tips: {
      S0: '从站起来走一走开始',
      S1: '散步也是很好的运动',
      S2: '试着每天多走500步',
      S3: '计划每周三次轻度运动',
      S4: '保持你的运动计划',
      S5: '你的运动习惯已经很棒了',
      S6: '带朋友一起运动',
    },
    microActions: {
      S0: '站起来伸个懒腰',
      S1: '饭后走5分钟',
      S2: '今天多走1000步',
      S3: '做10分钟拉伸',
      S4: '完成今天的运动计划',
      S5: '挑战一个新运动',
      S6: '组织一次朋友运动',
    },
  },
  sleep: {
    title: '睡眠调节',
    icon: 'clock-o',
    color: '#722ed1',
    tips: {
      S0: '注意一下自己每天几点睡觉',
      S1: '好的睡眠是健康的基础',
      S2: '试着每天在同一时间上床',
      S3: '建立一个睡前放松仪式',
      S4: '保持规律的作息时间',
      S5: '你的睡眠习惯已经很好了',
      S6: '分享你的好睡眠秘诀',
    },
    microActions: {
      S0: '记录今晚的入睡时间',
      S1: '今晚提前15分钟上床',
      S2: '睡前放下手机10分钟',
      S3: '尝试睡前深呼吸3分钟',
      S4: '保持今天的作息时间',
      S5: '优化卧室睡眠环境',
      S6: '帮助家人改善睡眠',
    },
  },
  emotion: {
    title: '情绪调节',
    icon: 'smile-o',
    color: '#eb2f96',
    tips: {
      S0: '每天留意一下自己的情绪',
      S1: '所有情绪都是正常的',
      S2: '试着给自己的情绪打个分',
      S3: '学习一种情绪调节方法',
      S4: '每天练习情绪觉察',
      S5: '你已经能很好地管理情绪了',
      S6: '帮助身边人处理情绪',
    },
    microActions: {
      S0: '用一个词描述现在的心情',
      S1: '深呼吸3次',
      S2: '记录今天的情绪变化',
      S3: '尝试5分钟冥想',
      S4: '完成今天的情绪日记',
      S5: '尝试新的放松方式',
      S6: '倾听一位朋友的心声',
    },
  },
  stress: {
    title: '压力管理',
    icon: 'warning-o',
    color: '#13c2c2',
    tips: {
      S0: '适度的压力是正常的',
      S1: '了解自己的压力源',
      S2: '试着找到一种减压方式',
      S3: '制定压力应对计划',
      S4: '坚持每天减压练习',
      S5: '你已经掌握了压力管理',
      S6: '帮助他人管理压力',
    },
    microActions: {
      S0: '写下今天最有压力的事',
      S1: '做5分钟放松呼吸',
      S2: '听一首喜欢的歌',
      S3: '练习渐进式肌肉放松',
      S4: '完成今天的减压练习',
      S5: '尝试新的减压技巧',
      S6: '分享你的减压经验',
    },
  },
  cognitive: {
    title: '认知提升',
    icon: 'bulb-o',
    color: '#1890ff',
    tips: {
      S0: '保持好奇心',
      S1: '每天学一点新东西',
      S2: '阅读一篇健康知识',
      S3: '参加一个健康讲座',
      S4: '系统学习健康知识',
      S5: '你已经是健康知识达人了',
      S6: '向他人传播健康知识',
    },
    microActions: {
      S0: '翻看一条健康小知识',
      S1: '阅读一篇健康文章',
      S2: '学习一个健康小技巧',
      S3: '记录一条学到的知识',
      S4: '整理自己的健康知识',
      S5: '写一条健康分享',
      S6: '帮助他人理解健康知识',
    },
  },
  social: {
    title: '社交连接',
    icon: 'friends-o',
    color: '#2f54eb',
    tips: {
      S0: '和身边的人聊聊天',
      S1: '好的社交关系让人更健康',
      S2: '主动联系一位朋友',
      S3: '加入一个健康群组',
      S4: '保持社交活动频率',
      S5: '你的社交生活很丰富',
      S6: '帮助新成员融入社群',
    },
    microActions: {
      S0: '给一位朋友发条问候',
      S1: '和家人聊10分钟',
      S2: '约朋友一起散步',
      S3: '参加一次社群活动',
      S4: '组织一次小聚会',
      S5: '邀请新朋友加入',
      S6: '帮助一位新人融入',
    },
  },
}

const domainCards = computed(() => {
  const domains = profile.value?.primary_domains || ['nutrition', 'exercise', 'sleep']
  const stage = profile.value?.stage?.current || 'S0'

  return domains.map((d: string) => {
    const config = DOMAIN_CONFIG[d]
    if (!config) return { key: d, title: d, icon: 'info-o', color: '#999', tip: '', microAction: '' }
    return {
      key: d,
      title: config.title,
      icon: config.icon,
      color: config.color,
      tip: config.tips[stage] || config.tips['S0'],
      microAction: config.microActions[stage] || config.microActions['S0'],
    }
  })
})

async function loadProfile() {
  loading.value = true
  try {
    const res = await api.get('/api/v1/assessment/profile/me')
    profile.value = res
  } catch {
    // 尝试用自己的用户ID
    try {
      const userStr = localStorage.getItem('h5_auth_user')
      const user = userStr ? JSON.parse(userStr) : null
      if (user?.id) {
        const res = await api.get(`/api/v1/assessment/profile/${user.id}`)
        profile.value = res
      }
    } catch {
      profile.value = null
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadTodayTasks()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading { text-align: center; padding: 40px 0; }

.stage-card {
  text-align: center;
  padding: $spacing-lg;

  .stage-visual {
    margin-bottom: $spacing-lg;
  }

  .stage-circle {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: $spacing-sm;
  }

  .stage-early { background: linear-gradient(135deg, #fff1f0, #ffccc7); }
  .stage-mid { background: linear-gradient(135deg, #fff7e6, #ffe7ba); }
  .stage-late { background: linear-gradient(135deg, #e6fffb, #b5f5ec); }

  .stage-emoji { font-size: 36px; }

  .stage-name {
    font-size: 20px;
    font-weight: 700;
    margin: 0 0 $spacing-xs;
  }

  .stage-desc {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    line-height: 1.6;
    margin: 0;
  }
}

.journey-bar {
  display: flex;
  justify-content: space-between;
  position: relative;
  padding: 0 4px;

  &::before {
    content: '';
    position: absolute;
    top: 6px;
    left: 16px;
    right: 16px;
    height: 2px;
    background: #e8e8e8;
  }

  .journey-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    z-index: 1;
  }

  .step-circle {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #e8e8e8;
  }

  .passed .step-circle { background: #52c41a; }
  .active .step-circle { background: #1989fa; box-shadow: 0 0 0 3px rgba(25, 137, 250, 0.2); }

  .step-name { font-size: 10px; color: #bbb; }
  .passed .step-name { color: #52c41a; }
  .active .step-name { color: #1989fa; font-weight: 600; }
}

.domains-section {
  margin-top: $spacing-md;

  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }
}

.domain-item {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  margin-bottom: $spacing-sm;

  .domain-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: #f5f5f5;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .domain-title {
    font-size: $font-size-md;
    font-weight: 600;
  }

  .domain-tip {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    line-height: 1.5;
  }

  .domain-micro {
    background: #f6ffed;
    padding: 8px 12px;
    border-radius: 8px;
    border-left: 3px solid #52c41a;
    font-size: $font-size-sm;

    .micro-label {
      color: #52c41a;
      font-weight: 600;
      margin-right: 4px;
    }
  }
}

.micro-actions-section {
  margin-top: $spacing-md;
  background: #fff;
  border-radius: $border-radius;
  padding: $spacing-md;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-sm;

    h3 { font-size: $font-size-lg; margin: 0; }
    .view-all { font-size: $font-size-sm; color: #1989fa; text-decoration: none; }
  }

  .today-progress {
    margin-bottom: $spacing-sm;
    font-size: $font-size-sm;
    color: $text-color-secondary;

    :deep(.van-progress) { margin-top: 4px; }
  }
}

.micro-task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;

  &:last-child { border-bottom: none; }
  &.done { opacity: 0.6; }

  .micro-check {
    width: 24px;
    height: 24px;
    border: 2px solid #d9d9d9;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    cursor: pointer;

    &.checked {
      background: #07c160;
      border-color: #07c160;
      color: #fff;
    }
  }

  .micro-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 6px;

    .micro-title { font-size: $font-size-md; }
  }
}

.micro-empty {
  text-align: center;
  padding: $spacing-md;
  color: $text-color-placeholder;
  font-size: $font-size-sm;
}

.reassess-btn {
  margin-top: $spacing-lg;
}

.empty-state {
  text-align: center;
  padding: 40px $spacing-lg;

  h3 {
    margin: $spacing-md 0 $spacing-xs;
    font-size: $font-size-lg;
  }

  p {
    color: $text-color-secondary;
    margin-bottom: $spacing-lg;
  }
}
</style>
