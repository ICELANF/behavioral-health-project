<template>
  <a-drawer
    :open="open"
    :width="640"
    title="用户角色画像"
    @close="$emit('update:open', false)"
    :destroyOnClose="true"
  >
    <a-spin :spinning="loading" tip="加载中...">
      <template v-if="profile">
        <!-- Basic Info -->
        <div class="profile-header">
          <a-avatar :size="48" :style="{ background: roleColor(profile.basic.role) }">
            {{ (profile.basic.full_name || profile.basic.username)[0] }}
          </a-avatar>
          <div class="header-info">
            <div class="header-name">{{ profile.basic.full_name || profile.basic.username }}</div>
            <div class="header-meta">
              <a-tag :color="roleColor(profile.basic.role)">{{ profile.basic.role_label }}</a-tag>
              <span class="meta-text">{{ profile.basic.email }}</span>
              <span v-if="profile.basic.phone" class="meta-text">{{ profile.basic.phone }}</span>
            </div>
            <div class="header-sub">
              <a-badge :status="profile.basic.is_active ? 'success' : 'error'" :text="profile.basic.is_active ? '正常' : '停用'" />
              <span class="meta-text">注册: {{ formatDate(profile.basic.created_at) }}</span>
              <span v-if="profile.basic.last_login_at" class="meta-text">最近登录: {{ formatDate(profile.basic.last_login_at) }}</span>
            </div>
          </div>
        </div>

        <a-divider />

        <!-- 3D Points -->
        <div class="section">
          <div class="section-title">三维积分</div>
          <a-row :gutter="12">
            <a-col :span="8">
              <a-card size="small" class="point-card" :bodyStyle="{ textAlign: 'center', padding: '12px' }">
                <div class="point-icon" style="color: #22c55e">&#x1F331;</div>
                <div class="point-value">{{ profile.points.growth }}</div>
                <div class="point-label">成长</div>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card size="small" class="point-card" :bodyStyle="{ textAlign: 'center', padding: '12px' }">
                <div class="point-icon" style="color: #3b82f6">&#x1F4DD;</div>
                <div class="point-value">{{ profile.points.contribution }}</div>
                <div class="point-label">贡献</div>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card size="small" class="point-card" :bodyStyle="{ textAlign: 'center', padding: '12px' }">
                <div class="point-icon" style="color: #f59e0b">&#x2B50;</div>
                <div class="point-value">{{ profile.points.influence }}</div>
                <div class="point-label">影响力</div>
              </a-card>
            </a-col>
          </a-row>
        </div>

        <!-- Level Progress -->
        <div class="section" v-if="profile.level_progress">
          <div class="section-title">
            等级进度
            <span class="level-badge">
              L{{ profile.level_progress.current_level }} {{ profile.level_progress.current_name }}
              <template v-if="profile.level_progress.next_name">
                &rarr; L{{ profile.level_progress.next_level }} {{ profile.level_progress.next_name }}
              </template>
              <template v-else>
                (最高等级)
              </template>
            </span>
          </div>
          <template v-if="profile.level_progress.requirements">
            <div class="progress-item" v-for="(dim, key) in profile.level_progress.requirements" :key="key">
              <div class="progress-label">
                <span>{{ dimLabel(key) }}</span>
                <span>{{ dim.current }}/{{ dim.required }}</span>
              </div>
              <a-progress
                :percent="dim.required > 0 ? Math.min(100, Math.round(dim.current / dim.required * 100)) : 100"
                :strokeColor="dimColor(key)"
                size="small"
              />
            </div>
          </template>
          <div v-if="profile.level_progress.companions" class="companions-req">
            <span>同道者: </span>
            <span v-for="i in profile.level_progress.companions.required" :key="i" class="companion-dot" :class="{ filled: i <= profile.level_progress.companions.graduated }">
              {{ i <= profile.level_progress.companions.graduated ? '&#x25CF;' : '&#x25CB;' }}
            </span>
            <span class="meta-text" style="margin-left: 8px">
              {{ profile.level_progress.companions.graduated }}/{{ profile.level_progress.companions.required }} 已毕业
              <template v-if="profile.level_progress.companions.target">(需达 {{ profile.level_progress.companions.target }})</template>
            </span>
          </div>
        </div>

        <a-divider v-if="profile.grower_data" dashed />

        <!-- Grower Data -->
        <div class="section" v-if="profile.grower_data">
          <div class="section-title">学习数据</div>
          <a-row :gutter="[12, 12]">
            <a-col :span="6">
              <a-statistic title="连续天数" :value="profile.grower_data.current_streak" suffix="天" :valueStyle="{ fontSize: '20px' }" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="本周完成率" :value="profile.grower_data.weekly_completion_rate" suffix="%" :valueStyle="{ fontSize: '20px' }" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="累计学习" :value="Math.round(profile.grower_data.total_learning_minutes / 60)" suffix="h" :valueStyle="{ fontSize: '20px' }" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="考试通过" :valueStyle="{ fontSize: '20px' }">
                <template #formatter>
                  {{ profile.grower_data.exams.passed }}/{{ profile.grower_data.exams.total }}
                </template>
              </a-statistic>
            </a-col>
          </a-row>
          <div class="daily-tasks-row" v-if="profile.grower_data.daily_tasks_today.total > 0">
            <span>今日任务: </span>
            <a-progress
              :percent="Math.round(profile.grower_data.daily_tasks_today.done / profile.grower_data.daily_tasks_today.total * 100)"
              :format="() => `${profile.grower_data.daily_tasks_today.done}/${profile.grower_data.daily_tasks_today.total}`"
              size="small"
              style="width: 200px; display: inline-flex; margin-left: 8px"
            />
          </div>
          <div class="meta-text" style="margin-top: 4px">
            最长连续: {{ profile.grower_data.longest_streak }} 天
          </div>
        </div>

        <a-divider v-if="profile.sharer_data" dashed />

        <!-- Sharer Data: Contributions -->
        <div class="section" v-if="profile.sharer_data">
          <div class="section-title">内容贡献</div>
          <div class="contrib-summary">
            已投 {{ profile.sharer_data.contributions.total }} 篇
            <a-tag color="green">发布 {{ profile.sharer_data.contributions.published }}</a-tag>
            <a-tag v-if="profile.sharer_data.contributions.pending" color="orange">待审 {{ profile.sharer_data.contributions.pending }}</a-tag>
            <a-tag v-if="profile.sharer_data.contributions.rejected" color="red">拒绝 {{ profile.sharer_data.contributions.rejected }}</a-tag>
          </div>
          <a-list
            v-if="profile.sharer_data.contribution_list.length > 0"
            :dataSource="profile.sharer_data.contribution_list"
            size="small"
            :bordered="true"
            style="margin-top: 8px"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <div style="flex: 1">
                  <span>{{ item.title }}</span>
                  <a-tag v-if="item.evidence_tier" size="small" style="margin-left: 6px">{{ item.evidence_tier }}</a-tag>
                </div>
                <template #actions>
                  <a-tag :color="statusColor(item.status)" size="small">{{ statusLabel(item.status) }}</a-tag>
                  <span class="meta-text">{{ formatDate(item.created_at) }}</span>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </div>

        <!-- Sharer Data: Mentees -->
        <div class="section" v-if="profile.sharer_data && profile.sharer_data.mentees.length > 0">
          <div class="section-title">同道者</div>
          <div class="mentee-grid">
            <div v-for="m in profile.sharer_data.mentees" :key="m.mentee_id" class="mentee-card">
              <a-avatar :size="32" :style="{ background: roleColor(m.mentee_role) }">
                {{ m.mentee_name[0] }}
              </a-avatar>
              <div class="mentee-name">{{ m.mentee_name }}</div>
              <a-badge :status="m.status === 'active' ? 'processing' : m.status === 'graduated' ? 'success' : 'default'"
                       :text="m.status === 'active' ? '进行中' : m.status === 'graduated' ? '已毕业' : m.status" />
            </div>
          </div>
        </div>

        <!-- Sharer Data: Influence -->
        <div class="section" v-if="profile.sharer_data">
          <div class="section-title">影响力明细</div>
          <div class="influence-row">
            <span class="influence-total">{{ profile.sharer_data.influence.total }} 分</span>
            = 赞 {{ profile.sharer_data.influence.likes }}
            + 藏 {{ profile.sharer_data.influence.saves }}
            + 官方 {{ profile.sharer_data.influence.official }}
          </div>
        </div>

        <a-divider v-if="profile.coach_data" dashed />

        <!-- Coach Data -->
        <div class="section" v-if="profile.coach_data">
          <div class="section-title">教练数据</div>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-statistic title="学员数" :value="profile.coach_data.student_count" :valueStyle="{ fontSize: '20px' }" />
            </a-col>
            <a-col :span="12">
              <a-statistic title="案例数" :value="profile.coach_data.case_count" :valueStyle="{ fontSize: '20px' }" />
            </a-col>
          </a-row>
        </div>
      </template>

      <a-empty v-else-if="!loading" description="无法加载用户画像" />
    </a-spin>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import request from '@/api/request'

const props = defineProps<{
  open: boolean
  userId: number | null
}>()

defineEmits(['update:open'])

const loading = ref(false)
const profile = ref<any>(null)

watch(() => [props.open, props.userId], async ([isOpen, uid]) => {
  if (isOpen && uid) {
    loading.value = true
    profile.value = null
    try {
      const { data } = await request.get(`/v1/admin/users/${uid}/role-profile`)
      profile.value = data
    } catch (e) {
      console.error('加载用户画像失败:', e)
    } finally {
      loading.value = false
    }
  }
}, { immediate: true })

const roleColor = (role: string) => {
  const map: Record<string, string> = {
    admin: '#cf1322', supervisor: '#722ed1', promoter: '#eb2f96',
    master: '#faad14', coach: '#1890ff', sharer: '#52c41a',
    grower: '#fa8c16', observer: '#8c8c8c',
  }
  return map[role] || '#999'
}

const dimLabel = (key: string) => ({ growth: '成长', contribution: '贡献', influence: '影响力' }[key] || key)
const dimColor = (key: string) => ({ growth: '#22c55e', contribution: '#3b82f6', influence: '#f59e0b' }[key] || '#1890ff')

const statusColor = (s: string) => ({ approved: 'green', pending: 'orange', rejected: 'red' }[s] || 'default')
const statusLabel = (s: string) => ({ approved: '已发布', pending: '待审核', rejected: '已拒绝' }[s] || s)

const formatDate = (iso: string | null) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.profile-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.header-info { flex: 1; }
.header-name { font-size: 18px; font-weight: 600; margin-bottom: 4px; }
.header-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.header-sub { display: flex; align-items: center; gap: 12px; }
.meta-text { font-size: 12px; color: #999; }

.section { margin-bottom: 20px; }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 10px; color: #333; }
.level-badge { font-weight: 400; font-size: 13px; color: #666; margin-left: 8px; }

.point-card { border-radius: 8px; }
.point-icon { font-size: 20px; margin-bottom: 4px; }
.point-value { font-size: 22px; font-weight: 700; color: #333; }
.point-label { font-size: 12px; color: #999; }

.progress-item { margin-bottom: 8px; }
.progress-label { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 2px; }

.companions-req { margin-top: 8px; font-size: 13px; }
.companion-dot { font-size: 18px; margin: 0 2px; }
.companion-dot.filled { color: #52c41a; }

.contrib-summary { font-size: 13px; display: flex; align-items: center; gap: 6px; }

.daily-tasks-row { margin-top: 8px; font-size: 13px; display: flex; align-items: center; }

.mentee-grid { display: flex; gap: 12px; flex-wrap: wrap; }
.mentee-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 10px 14px; border: 1px solid #f0f0f0; border-radius: 8px; min-width: 90px;
}
.mentee-name { font-size: 12px; font-weight: 500; }

.influence-row { font-size: 13px; }
.influence-total { font-size: 16px; font-weight: 600; margin-right: 6px; }
</style>
