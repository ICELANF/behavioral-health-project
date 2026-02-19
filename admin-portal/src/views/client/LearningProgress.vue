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

const overallStats = ref({ coursesCompleted: 3, totalHours: 12, badges: 5, streak: 7 })
const loading = ref(true)

async function loadLearningData() {
  loading.value = true
  // Use userId=0 as a self-reference (backend may use current user from token)
  const userId = parseInt(localStorage.getItem('admin_user_id') || '0')
  const [statsR, timeR, streakR] = await Promise.allSettled([
    learningApi.getStats(userId),
    learningApi.getTime(userId),
    learningApi.getStreak(userId),
  ])

  if (statsR.status === 'fulfilled' && statsR.value) {
    const s = statsR.value
    overallStats.value.coursesCompleted = s.courses_completed ?? s.coursesCompleted ?? overallStats.value.coursesCompleted
    overallStats.value.badges = s.badges ?? s.badges_earned ?? overallStats.value.badges
  } else {
    console.warn('Failed to load learning stats, using mock', statsR.status === 'rejected' ? statsR.reason : '')
  }

  if (timeR.status === 'fulfilled' && timeR.value) {
    overallStats.value.totalHours = timeR.value.total_hours ?? timeR.value.totalHours ?? overallStats.value.totalHours
  }

  if (streakR.status === 'fulfilled' && streakR.value) {
    overallStats.value.streak = streakR.value.current_streak ?? streakR.value.streak ?? overallStats.value.streak
  }

  loading.value = false
}

onMounted(loadLearningData)

const roadmap = ref([
  {
    name: '基础认知', completed: true, current: false, progress: 100,
    skills: [
      { name: '健康基础知识', icon: '📖', progress: 100, unlocked: true },
      { name: '行为改变原理', icon: '🧠', progress: 100, unlocked: true },
    ]
  },
  {
    name: '技能学习', completed: false, current: true, progress: 65,
    skills: [
      { name: '压力管理技术', icon: '🧘', progress: 80, unlocked: true },
      { name: '健康饮食规划', icon: '🥗', progress: 60, unlocked: true },
      { name: '运动计划制定', icon: '🏃', progress: 40, unlocked: true },
      { name: '情绪调节方法', icon: '😌', progress: 30, unlocked: true },
    ]
  },
  {
    name: '实践应用', completed: false, current: false, progress: 15,
    skills: [
      { name: '自我监测', icon: '📊', progress: 30, unlocked: true },
      { name: '习惯养成', icon: '🎯', progress: 20, unlocked: true },
      { name: '社会支持', icon: '👥', progress: 0, unlocked: false },
    ]
  },
  {
    name: '持续维持', completed: false, current: false, progress: 0,
    skills: [
      { name: '复发预防', icon: '🛡️', progress: 0, unlocked: false },
      { name: '长期目标管理', icon: '🏔️', progress: 0, unlocked: false },
    ]
  },
])

const courseProgress = ref([
  { id: '1', name: '压力管理入门', progress: 100, completedChapters: 8, totalChapters: 8, lastStudied: '3天前' },
  { id: '2', name: '健康饮食指南', progress: 75, completedChapters: 5, totalChapters: 6, lastStudied: '今天' },
  { id: '3', name: '运动与情绪管理', progress: 40, completedChapters: 2, totalChapters: 5, lastStudied: '昨天' },
  { id: '4', name: '睡眠改善课程', progress: 0, completedChapters: 0, totalChapters: 4, lastStudied: '未开始' },
])

const badges = ref([
  { id: '1', icon: '🌱', name: '学习新手', earned: true, earnedDate: '2024-11-01', condition: '' },
  { id: '2', icon: '📚', name: '好学勤练', earned: true, earnedDate: '2024-11-15', condition: '' },
  { id: '3', icon: '🔥', name: '连续7天', earned: true, earnedDate: '2025-01-15', condition: '' },
  { id: '4', icon: '🏅', name: '首课完成', earned: true, earnedDate: '2024-12-20', condition: '' },
  { id: '5', icon: '⭐', name: '满分测评', earned: true, earnedDate: '2025-01-10', condition: '' },
  { id: '6', icon: '💪', name: '运动达人', earned: false, condition: '完成运动课程' },
  { id: '7', icon: '🧘', name: '正念大师', earned: false, condition: '连续冥想30天' },
  { id: '8', icon: '👑', name: '全课通关', earned: false, condition: '完成所有课程' },
])

const certificates = ref([
  { id: '1', name: '压力管理入门结业证书', date: '2024-12-20' },
])

const recommendations = ref([
  { id: '1', icon: '📖', name: '继续学习《健康饮食指南》', description: '还剩1章即可完成', link: '' },
  { id: '2', icon: '📝', name: '完成本周PSS-10测评', description: '定期评估有助于跟踪进度', link: '/client/assessment/list' },
  { id: '3', icon: '🏃', name: '开始《运动与情绪管理》第3章', description: '学习运动对情绪的积极影响', link: '' },
])
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
