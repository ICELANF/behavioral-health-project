<template>
  <div class="learning-progress">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>学习进度</h2>
    </div>

    <!-- Overall Stats -->
    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-icon">📚</span>
        <span class="stat-val">{{ overallStats.coursesCompleted }}</span>
        <span class="stat-label">已完成课程</span>
      </div>
      <div class="stat-card">
        <span class="stat-icon">⏱</span>
        <span class="stat-val">{{ overallStats.totalHours }}h</span>
        <span class="stat-label">学习时长</span>
      </div>
      <div class="stat-card">
        <span class="stat-icon">🏆</span>
        <span class="stat-val">{{ overallStats.badges }}</span>
        <span class="stat-label">获得徽章</span>
      </div>
      <div class="stat-card">
        <span class="stat-icon">🔥</span>
        <span class="stat-val">{{ overallStats.streak }}</span>
        <span class="stat-label">连续学习天</span>
      </div>
    </div>

    <!-- Skill Tree / Roadmap -->
    <div class="section">
      <h3 class="section-title">技能路线图</h3>
      <div class="roadmap">
        <div v-for="(phase, i) in roadmap" :key="i" class="roadmap-phase">
          <div class="phase-header" :class="{ completed: phase.completed, current: phase.current }">
            <span class="phase-dot" :style="{ background: phase.completed ? '#52c41a' : phase.current ? '#1890ff' : '#d9d9d9' }"></span>
            <span class="phase-name">{{ phase.name }}</span>
            <span class="phase-pct">{{ phase.progress }}%</span>
          </div>
          <div class="phase-skills">
            <div v-for="skill in phase.skills" :key="skill.name" class="skill-item" :class="{ unlocked: skill.unlocked }">
              <span class="skill-icon">{{ skill.icon }}</span>
              <span class="skill-name">{{ skill.name }}</span>
              <a-progress :percent="skill.progress" size="small" :stroke-color="skill.progress === 100 ? '#52c41a' : '#1890ff'" style="width: 80px" />
            </div>
          </div>
          <div v-if="i < roadmap.length - 1" class="phase-connector"></div>
        </div>
      </div>
    </div>

    <!-- Course Completion -->
    <div class="section">
      <h3 class="section-title">课程完成率</h3>
      <div v-for="course in courseProgress" :key="course.id" class="course-card">
        <div class="course-header">
          <span class="course-name">{{ course.name }}</span>
          <span class="course-pct">{{ course.progress }}%</span>
        </div>
        <a-progress :percent="course.progress" :stroke-color="course.progress === 100 ? '#52c41a' : '#1890ff'" :show-info="false" />
        <div class="course-meta">
          <span>{{ course.completedChapters }}/{{ course.totalChapters }} 章节</span>
          <span>{{ course.lastStudied }}</span>
        </div>
      </div>
    </div>

    <!-- Badges & Achievements -->
    <div class="section">
      <h3 class="section-title">徽章成就</h3>
      <div class="badges-grid">
        <div v-for="badge in badges" :key="badge.id" class="badge-item" :class="{ earned: badge.earned }">
          <span class="badge-icon">{{ badge.icon }}</span>
          <span class="badge-name">{{ badge.name }}</span>
          <span v-if="badge.earned" class="badge-date">{{ badge.earnedDate }}</span>
          <span v-else class="badge-condition">{{ badge.condition }}</span>
        </div>
      </div>
    </div>

    <!-- Certificates -->
    <div class="section">
      <h3 class="section-title">证书展示</h3>
      <div v-for="cert in certificates" :key="cert.id" class="cert-card">
        <span class="cert-icon">📜</span>
        <div class="cert-info">
          <span class="cert-name">{{ cert.name }}</span>
          <span class="cert-date">颁发于 {{ cert.date }}</span>
        </div>
        <button class="cert-btn">查看</button>
      </div>
      <p v-if="certificates.length === 0" class="empty-text">完成课程后将获得证书</p>
    </div>

    <!-- Recommended Next -->
    <div class="section">
      <h3 class="section-title">推荐下一步</h3>
      <div v-for="rec in recommendations" :key="rec.id" class="rec-card" @click="$router.push(rec.link || '')">
        <span class="rec-icon">{{ rec.icon }}</span>
        <div class="rec-info">
          <span class="rec-name">{{ rec.name }}</span>
          <span class="rec-desc">{{ rec.description }}</span>
        </div>
        <span class="rec-arrow">→</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { learningApi } from '@/api/index'
import request from '@/api/request'

const overallStats = ref({ coursesCompleted: 0, totalHours: 0, badges: 0, streak: 0 })
const loading = ref(true)
const roadmap = ref([])
const courseProgress = ref([])
const badges = ref([])
const certificates = ref([])
const recommendations = ref([])

async function loadLearningData() {
  if (!localStorage.getItem('admin_token')) return
  loading.value = true
  const userId = parseInt(localStorage.getItem('admin_user_id') || '0')

  const [statsR, timeR, streakR, rewardsR, contentR] = await Promise.allSettled([
    learningApi.getStats(userId),
    learningApi.getTime(userId),
    learningApi.getStreak(userId),
    learningApi.getRewards(userId),
    request.get('/v1/content/recommended', { params: { limit: 5 } }).then(r => r.data),
  ])

  // ── 顶部统计 ──
  let totalMin = 0, totalPts = 0, quizPassed = 0, currentStreak = 0
  if (statsR.status === 'fulfilled' && statsR.value) {
    const s = statsR.value
    totalMin = s.learning_time?.total_minutes ?? 0
    totalPts = s.learning_points?.total_points ?? 0
    quizPassed = s.learning_points?.quiz_stats?.passed_quizzes ?? 0
    currentStreak = s.streak?.current_streak ?? 0
    overallStats.value.coursesCompleted = quizPassed
    overallStats.value.badges = s.learning_time?.rewards_earned + (s.learning_points?.rewards_earned || 0)
  }
  if (timeR.status === 'fulfilled' && timeR.value) {
    overallStats.value.totalHours = timeR.value.total_hours ?? 0
  }
  if (streakR.status === 'fulfilled' && streakR.value) {
    overallStats.value.streak = streakR.value.current_streak ?? 0
  }

  // ── 技能路线图 (基于六级体系) ──
  const levels = [
    { name: '观察者 → 成长者', pointsReq: 100, skills: [
      { icon: '📖', name: '基础健康知识', progFn: () => Math.min(100, totalPts) },
      { icon: '✅', name: '首次打卡', progFn: () => currentStreak > 0 ? 100 : 0 },
    ]},
    { name: '成长者 → 分享者', pointsReq: 500, skills: [
      { icon: '📚', name: '课程学习 (500积分)', progFn: () => Math.min(100, Math.round(totalPts / 500 * 100)) },
      { icon: '🏅', name: '完成测验 (50次)', progFn: () => Math.min(100, Math.round(quizPassed / 50 * 100)) },
    ]},
    { name: '分享者 → 教练', pointsReq: 800, skills: [
      { icon: '🎯', name: '深度学习 (800积分)', progFn: () => Math.min(100, Math.round(totalPts / 800 * 100)) },
      { icon: '💡', name: '知识贡献 (200积分)', progFn: () => Math.min(100, Math.round(totalPts / 200 * 100)) },
      { icon: '🤝', name: '同道者互助', progFn: () => 0 },
    ]},
  ]
  roadmap.value = levels.map((lv, i) => {
    const skills = lv.skills.map(sk => ({
      icon: sk.icon, name: sk.name, progress: sk.progFn(), unlocked: totalPts >= (levels[i - 1]?.pointsReq ?? 0),
    }))
    const avgProg = Math.round(skills.reduce((s, sk) => s + sk.progress, 0) / skills.length)
    return {
      name: lv.name,
      progress: avgProg,
      completed: avgProg >= 100,
      current: i === 0 ? avgProg < 100 : (levels[i - 1] && totalPts >= levels[i - 1].pointsReq && avgProg < 100),
      skills,
    }
  })

  // ── 课程完成 (从学习时间推导) ──
  const domains = ['nutrition', 'exercise', 'emotion', 'sleep']
  const domainNames = { nutrition: '营养与饮食管理', exercise: '科学运动指导', emotion: '情绪智力提升', sleep: '睡眠质量改善' }
  courseProgress.value = domains.map((d, i) => {
    const prog = Math.min(100, Math.round((totalMin / 4 / (60 + i * 20)) * 100))
    return {
      id: d, name: domainNames[d] || d,
      progress: Math.min(prog, 100 - i * 8),
      completedChapters: Math.floor(prog / 20), totalChapters: 5,
      lastStudied: currentStreak > 0 ? '今天' : '暂无记录',
    }
  })

  // ── 徽章成就 (来自 rewards API) ──
  if (rewardsR.status === 'fulfilled' && rewardsR.value) {
    const rw = rewardsR.value
    const allBadges = []
    for (const tr of (rw.time_rewards || [])) {
      allBadges.push({
        id: `time-${tr.milestone.minutes}`,
        icon: tr.milestone.icon, name: tr.milestone.reward,
        earned: tr.earned, earnedDate: tr.earned ? '已获得' : '',
        condition: `学习 ${tr.milestone.minutes} 分钟`,
      })
    }
    for (const sr of (rw.streak_rewards || [])) {
      allBadges.push({
        id: `streak-${sr.milestone.days}`,
        icon: sr.milestone.icon, name: sr.milestone.reward,
        earned: sr.earned, earnedDate: sr.earned ? '已获得' : '',
        condition: `连续学习 ${sr.milestone.days} 天`,
      })
    }
    badges.value = allBadges
    overallStats.value.badges = allBadges.filter(b => b.earned).length
  }

  // ── 推荐下一步 (来自 content API) ──
  if (contentR.status === 'fulfilled' && contentR.value) {
    const items = Array.isArray(contentR.value) ? contentR.value : (contentR.value.items || [])
    recommendations.value = items.slice(0, 4).map((c) => ({
      id: c.id,
      icon: c.type === 'course' ? '📚' : c.type === 'video' ? '🎬' : '📝',
      name: c.title,
      description: c.subtitle || c.domain || '',
      link: `/client/content/${c.id}`,
    }))
  }
  // 如果没有推荐内容，添加默认推荐
  if (recommendations.value.length === 0) {
    recommendations.value = [
      { id: 'learn', icon: '📚', name: '继续学习课程', description: '每日学习15分钟，积累健康知识', link: '/client/learning-center' },
      { id: 'assess', icon: '📋', name: '完成健康测评', description: '了解自己的行为改变阶段', link: '/client/my/assessments' },
      { id: 'chat', icon: '💬', name: '咨询AI教练', description: '获取个性化健康建议', link: '/client/chat-v2' },
    ]
  }

  loading.value = false
}

onMounted(loadLearningData)
</script>

<style scoped>
.learning-progress { max-width: 600px; margin: 0 auto; padding: 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 16px; }
.stat-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 10px; padding: 12px; text-align: center; }
.stat-icon { font-size: 20px; display: block; }
.stat-val { display: block; font-size: 20px; font-weight: 700; color: #333; }
.stat-label { font-size: 11px; color: #999; }

.section { margin-bottom: 20px; }
.section-title { font-size: 15px; font-weight: 600; color: #333; margin: 0 0 12px; }

.roadmap { position: relative; }
.roadmap-phase { margin-bottom: 4px; }
.phase-header { display: flex; align-items: center; gap: 8px; padding: 8px; border-radius: 6px; background: #fafafa; }
.phase-header.completed { background: #f6ffed; }
.phase-header.current { background: #e6f7ff; }
.phase-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.phase-name { flex: 1; font-size: 14px; font-weight: 500; }
.phase-pct { font-size: 12px; color: #999; }
.phase-skills { padding-left: 20px; }
.skill-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.skill-item:not(.unlocked) { opacity: 0.4; }
.skill-icon { font-size: 16px; }
.skill-name { min-width: 100px; font-size: 12px; color: #333; }
.phase-connector { width: 2px; height: 8px; background: #e8e8e8; margin-left: 13px; }

.course-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
.course-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.course-name { font-size: 14px; font-weight: 500; }
.course-pct { font-size: 14px; font-weight: 600; color: #1890ff; }
.course-meta { display: flex; justify-content: space-between; font-size: 11px; color: #999; margin-top: 4px; }

.badges-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.badge-item { background: #fff; border: 1px solid #f0f0f0; border-radius: 10px; padding: 12px; text-align: center; }
.badge-item:not(.earned) { opacity: 0.4; }
.badge-icon { font-size: 28px; display: block; margin-bottom: 4px; }
.badge-name { font-size: 12px; font-weight: 500; color: #333; display: block; }
.badge-date { font-size: 10px; color: #999; }
.badge-condition { font-size: 10px; color: #bbb; }

.cert-card { display: flex; align-items: center; gap: 12px; padding: 12px; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px; margin-bottom: 8px; }
.cert-icon { font-size: 28px; }
.cert-info { flex: 1; }
.cert-name { display: block; font-size: 14px; font-weight: 500; }
.cert-date { font-size: 12px; color: #999; }
.cert-btn { padding: 4px 12px; border: 1px solid #d4b106; border-radius: 4px; background: #fff; color: #d4b106; cursor: pointer; }

.rec-card { display: flex; align-items: center; gap: 12px; padding: 12px; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; margin-bottom: 8px; cursor: pointer; }
.rec-card:hover { background: #fafafa; }
.rec-icon { font-size: 24px; }
.rec-info { flex: 1; }
.rec-name { display: block; font-size: 14px; font-weight: 500; }
.rec-desc { font-size: 12px; color: #999; }
.rec-arrow { font-size: 18px; color: #ccc; }
.empty-text { text-align: center; color: #ccc; padding: 16px; }
</style>
