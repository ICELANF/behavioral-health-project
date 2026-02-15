<!--
  ChallengesView.vue — 挑战打卡
  可报名挑战列表 + 我的挑战 + 打卡 + 进度
  对接: challengeApi.list() / getMy() / enroll() / checkin()
-->

<template>
  <div class="challenges-view">
    <div class="page-header">
      <h2 class="page-title">挑战打卡</h2>
      <p class="page-desc">加入挑战，用行动兑换积分</p>
    </div>

    <a-tabs v-model:activeKey="tab" class="main-tabs">
      <!-- 我的挑战 -->
      <a-tab-pane key="my" tab="我的挑战">
        <a-spin :spinning="loading">
          <div v-if="myChallenges.length" class="challenge-list">
            <div v-for="c in myChallenges" :key="c.id" class="ch-card">
              <div class="ch-top">
                <div>
                  <div class="ch-title">{{ c.title }}</div>
                  <div class="ch-meta">{{ c.duration_days }}天挑战 · {{ c.enrolled_count }}人参与</div>
                </div>
                <a-tag :color="c.my_progress?.completed ? 'success' : 'processing'">
                  {{ c.my_progress?.completed ? '已完成' : '进行中' }}
                </a-tag>
              </div>
              <div class="ch-progress" v-if="c.my_progress">
                <a-progress
                  :percent="Math.round((c.my_progress.checkin_count / c.duration_days) * 100)"
                  :stroke-color="{ from: '#4aa883', to: '#2d8e69' }"
                  :format="() => `${c.my_progress!.checkin_count}/${c.duration_days}天`"
                />
                <div class="ch-day">第 {{ c.my_progress.current_day }} 天</div>
              </div>
              <a-button
                v-if="!c.my_progress?.completed"
                type="primary"
                block
                class="ch-btn"
                :loading="c._loading"
                @click="doCheckin(c)"
              >
                今日打卡 +3积分
              </a-button>
              <div v-else class="ch-done-msg">恭喜完成挑战！+10积分</div>
            </div>
          </div>
          <a-empty v-else description="还没有加入任何挑战">
            <a-button type="primary" @click="tab = 'all'">浏览挑战</a-button>
          </a-empty>
        </a-spin>
      </a-tab-pane>

      <!-- 所有挑战 -->
      <a-tab-pane key="all" tab="浏览挑战">
        <a-spin :spinning="loading">
          <div v-if="allChallenges.length" class="challenge-list">
            <div v-for="c in allChallenges" :key="c.id" class="ch-card">
              <div class="ch-top">
                <div>
                  <div class="ch-title">{{ c.title }}</div>
                  <div class="ch-desc" v-if="c.description">{{ c.description }}</div>
                  <div class="ch-meta">{{ c.duration_days }}天 · {{ c.enrolled_count }}人参与</div>
                </div>
                <a-tag :color="c.status === 'active' ? 'green' : 'default'">
                  {{ c.status === 'active' ? '进行中' : c.status }}
                </a-tag>
              </div>
              <a-button
                v-if="c.status === 'active' && !isEnrolled(c.id)"
                type="primary"
                ghost
                block
                class="ch-btn"
                :loading="c._loading"
                @click="doEnroll(c)"
              >
                报名参加
              </a-button>
              <div v-else-if="isEnrolled(c.id)" class="ch-enrolled">已报名</div>
            </div>
          </div>
          <a-empty v-else description="暂无可用挑战" />
        </a-spin>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { challengeApi } from '@/api'
import { message } from 'ant-design-vue'
import type { Challenge } from '@/types'

type ChallengeEx = Challenge & { _loading?: boolean; enrollment_id?: number; challenge_id?: number }

const tab = ref('my')
const loading = ref(true)
const myChallenges = ref<ChallengeEx[]>([])
const allChallenges = ref<ChallengeEx[]>([])

function isEnrolled(challengeId: number) {
  // myChallenges 来自 /my-enrollments, 每项有 challenge_id 字段
  return myChallenges.value.some(c => (c.challenge_id || c.id) === challengeId)
}

async function doCheckin(c: ChallengeEx) {
  c._loading = true
  try {
    // c 来自 my-enrollments, c.id 是 enrollment_id
    // 如果是刚报名临时插入的, 用 enrollment_id 字段
    const enrollmentId = c.enrollment_id || c.id
    await challengeApi.checkin(enrollmentId)
    if (c.my_progress) c.my_progress.checkin_count++
    message.success('打卡成功！+3 成长积分')
  } catch (e: any) {
    message.error(e.message || '打卡失败')
  }
  c._loading = false
}

async function doEnroll(c: ChallengeEx) {
  c._loading = true
  try {
    const enrollment = await challengeApi.enroll(c.id)
    message.success('报名成功！')
    // 用服务端返回的 enrollment 数据 (含 enrollment_id)
    myChallenges.value.push({
      ...c,
      enrollment_id: enrollment?.id || enrollment?.enrollment_id,
      challenge_id: c.id,
      my_progress: enrollment?.my_progress || { current_day: 1, checkin_count: 0, completed: false },
    })
  } catch (e: any) {
    message.error(e.message || '报名失败')
  }
  c._loading = false
}

onMounted(async () => {
  try {
    const [my, all] = await Promise.allSettled([challengeApi.getMy(), challengeApi.list()])
    if (my.status === 'fulfilled') myChallenges.value = my.value
    if (all.status === 'fulfilled') allChallenges.value = all.value
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.challenges-view { max-width: 720px; margin: 0 auto; }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 22px; font-weight: 700; margin: 0 0 4px; }
.page-desc { font-size: 14px; color: #999; margin: 0; }
.main-tabs :deep(.ant-tabs-nav) { margin-bottom: 20px; }

.challenge-list { display: flex; flex-direction: column; gap: 12px; }
.ch-card { background: #fff; border-radius: 14px; padding: 20px; border: 1px solid #f0f0f0; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.ch-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.ch-title { font-size: 16px; font-weight: 600; color: #1a1a1a; }
.ch-desc { font-size: 13px; color: #666; margin-top: 4px; }
.ch-meta { font-size: 12px; color: #bbb; margin-top: 4px; }
.ch-progress { margin-bottom: 14px; }
.ch-day { font-size: 12px; color: #999; margin-top: 4px; text-align: right; }
.ch-btn { border-radius: 10px; height: 42px; font-weight: 600; }
.ch-done-msg { text-align: center; color: #2d8e69; font-weight: 600; font-size: 14px; padding: 8px 0; }
.ch-enrolled { text-align: center; color: #999; font-size: 13px; padding: 8px 0; }
</style>
