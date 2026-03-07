<template>
  <div class="prescription-page">
    <template v-if="loading">
      <div class="loading">加载处方中...</div>
    </template>
    <template v-else-if="!profile">
      <div class="empty">
        <p>请先完成评估</p>
        <button class="btn-primary" @click="$router.push('/v3/motivation-quiz')">开始评估</button>
      </div>
    </template>
    <template v-else>
      <!-- 状态提示 -->
      <div class="readiness-banner" :class="readinessClass">
        <span>{{ todayData?.readiness_hint || '欢迎回来' }}</span>
      </div>

      <!-- UI-04: BPT-6 驱动处方排列 -->

      <!-- 行动型 A: 行动优先 -->
      <template v-if="bpt6Type === 'action'">
        <div class="rx-card action-first">
          <h3>今天就做这件事</h3>
          <div class="action-block large">
            <p class="action-main">{{ strategy?.prescription || '完成一次15分钟健走' }}</p>
          </div>
          <details class="principle-fold">
            <summary>为什么这样做？</summary>
            <p>{{ strategy?.entry || '' }}</p>
          </details>
        </div>
      </template>

      <!-- 知识型 B: 原理优先 -->
      <template v-else-if="bpt6Type === 'knowledge'">
        <div class="rx-card knowledge-first">
          <h3>科学依据</h3>
          <div class="principle-block">
            <p>{{ strategy?.entry || '' }}</p>
          </div>
          <h3>推荐行动</h3>
          <div class="action-block">
            <p>{{ strategy?.prescription || '' }}</p>
          </div>
        </div>
      </template>

      <!-- 情绪型 C: 感受优先 -->
      <template v-else-if="bpt6Type === 'emotion'">
        <div class="rx-card emotion-first">
          <h3>今天感受如何？</h3>
          <div class="emotion-check">
            <span
              v-for="emoji in ['😊', '😐', '😔', '😤']"
              :key="emoji"
              class="emoji-btn"
              :class="{ active: selectedMood === emoji }"
              @click="selectedMood = emoji"
            >{{ emoji }}</span>
          </div>
          <div class="action-block" v-if="selectedMood">
            <p>{{ strategy?.prescription || '' }}</p>
          </div>
        </div>
      </template>

      <!-- 关系型 D: 社群入口 -->
      <template v-else-if="bpt6Type === 'relation'">
        <div class="rx-card relation-first">
          <h3>推荐行动</h3>
          <div class="action-block">
            <p>{{ strategy?.prescription || '' }}</p>
          </div>
          <button class="btn-social" @click="$router.push('/my-companions')">
            邀请TA一起
          </button>
        </div>
      </template>

      <!-- 矛盾型 E: 只给一件事 -->
      <template v-else-if="bpt6Type === 'ambivalent'">
        <div class="rx-card minimal">
          <h3>只需要做一件事</h3>
          <div class="action-block large single">
            <p class="action-main">{{ strategy?.prescription || '深呼吸3次，然后站起来走动1分钟' }}</p>
          </div>
        </div>
      </template>

      <!-- 环境型 F / 默认 -->
      <template v-else>
        <div class="rx-card environment-first">
          <h3>推荐行动</h3>
          <div class="action-block">
            <p>{{ strategy?.prescription || '' }}</p>
          </div>
          <div class="env-settings" v-if="bpt6Type === 'environment'">
            <h4>环境设置建议</h4>
            <p>{{ strategy?.format || '在固定时间、固定地点执行，建立环境触发锚' }}</p>
          </div>
        </div>
      </template>

      <!-- 注意事项 -->
      <div class="caution-card" v-if="strategy?.caution">
        <span class="caution-icon">!</span>
        <p>{{ strategy.caution }}</p>
      </div>

      <!-- 底部操作 -->
      <div class="actions">
        <button class="btn-primary" @click="$router.push('/v3/profile-card')">查看我的画像</button>
        <button class="btn-secondary" @click="$router.back()">返回</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const loading = ref(true)
const profile = ref<any>(null)
const todayData = ref<any>(null)
const selectedMood = ref('')

const bpt6Type = computed(() => profile.value?.bpt6_type || 'mixed')
const strategy = computed(() => profile.value?.strategy || null)

const readinessClass = computed(() => {
  const hint = todayData.value?.readiness_hint || ''
  if (hint.includes('很好')) return 'high'
  if (hint.includes('稳步')) return 'medium'
  if (hint.includes('轻量')) return 'low'
  return 'rest'
})

onMounted(async () => {
  try {
    const [profileRes, todayRes] = await Promise.allSettled([
      request.get('/api/v1/guixin/profile-card'),
      request.get('/api/v1/guixin/today-anchor'),
    ])
    if (profileRes.status === 'fulfilled') profile.value = profileRes.value.data
    if (todayRes.status === 'fulfilled') todayData.value = todayRes.value.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.prescription-page {
  max-width: 430px;
  margin: 0 auto;
  padding: 20px 16px;
  min-height: 100vh;
  background: linear-gradient(180deg, #f0f4ff 0%, #fff 30%);
}
.loading, .empty { text-align: center; padding: 60px 20px; color: #666; }

.readiness-banner {
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 15px;
  font-weight: 500;
  text-align: center;
}
.readiness-banner.high { background: #e8f5e9; color: #2e7d32; }
.readiness-banner.medium { background: #e3f2fd; color: #1565c0; }
.readiness-banner.low { background: #fff8e1; color: #f57f17; }
.readiness-banner.rest { background: #fce4ec; color: #c62828; }

.rx-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.rx-card h3 {
  font-size: 18px;
  color: #1a1a2e;
  margin-bottom: 12px;
}

.action-block {
  background: #f0f4ff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}
.action-block.large {
  padding: 24px;
  text-align: center;
}
.action-block.large .action-main {
  font-size: 20px;
  font-weight: 600;
  color: #4f6ef7;
  line-height: 1.5;
}
.action-block.single { background: linear-gradient(135deg, #4f6ef7, #7b61ff); }
.action-block.single .action-main { color: #fff; }

.principle-block {
  background: #f8f9ff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

.principle-fold {
  margin-top: 8px;
}
.principle-fold summary {
  color: #4f6ef7;
  cursor: pointer;
  font-size: 14px;
}
.principle-fold p {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.emotion-check {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 16px;
}
.emoji-btn {
  font-size: 32px;
  cursor: pointer;
  opacity: 0.5;
  transition: all 0.2s;
}
.emoji-btn.active { opacity: 1; transform: scale(1.3); }

.btn-social {
  width: 100%;
  padding: 12px;
  background: #fff;
  border: 2px solid #27ae60;
  color: #27ae60;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

.env-settings {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}
.env-settings h4 { font-size: 14px; color: #666; margin-bottom: 4px; }
.env-settings p { font-size: 13px; color: #888; }

.caution-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #fff8e1;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 20px;
}
.caution-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f57f17;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}
.caution-card p { font-size: 13px; color: #795548; line-height: 1.4; }

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 40px;
}
.btn-primary {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #4f6ef7, #7b61ff);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}
.btn-secondary {
  width: 100%;
  padding: 14px;
  background: #fff;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 12px;
  font-size: 16px;
  cursor: pointer;
}
</style>
