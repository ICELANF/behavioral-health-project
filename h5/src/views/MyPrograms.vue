<template>
  <div class="page-container">
    <van-nav-bar title="智能监测方案" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <template v-else>
        <!-- 我的方案 -->
        <template v-if="myPrograms.length">
          <div class="section-title">我的方案</div>
          <div
            v-for="p in myPrograms"
            :key="p.enrollment_id"
            class="program-card"
            @click="goToToday(p)"
          >
            <div class="program-header">
              <div class="program-icon" :class="'cat-' + p.category">
                {{ categoryIcon(p.category) }}
              </div>
              <div class="program-info">
                <div class="program-title">{{ p.template_title }}</div>
                <div class="program-meta">
                  <van-tag :type="statusType(p.status)" size="small" round>{{ statusLabel(p.status) }}</van-tag>
                  <span>Day {{ p.current_day }}/{{ p.total_days }}</span>
                </div>
              </div>
              <van-icon name="arrow" color="#c8c9cc" />
            </div>
            <van-progress
              :percentage="p.progress_pct"
              stroke-width="6"
              :color="p.status === 'completed' ? '#07c160' : '#1989fa'"
              track-color="#ebedf0"
              :show-pivot="false"
              style="margin-top: 10px"
            />
            <div class="program-stats">
              <span>{{ p.answered_count || 0 }} 次回答</span>
              <span>{{ p.photo_count || 0 }} 张照片</span>
              <span v-if="p.last_interaction_at">最近: {{ timeAgo(p.last_interaction_at) }}</span>
            </div>
          </div>
        </template>

        <!-- 可报名的方案 -->
        <div class="section-title">{{ myPrograms.length ? '更多方案' : '可报名方案' }}</div>
        <van-empty v-if="!availableTemplates.length && !myPrograms.length" description="暂无方案" />
        <div
          v-for="t in availableTemplates"
          :key="t.id"
          class="template-card"
        >
          <div class="template-header">
            <div class="program-icon" :class="'cat-' + t.category">
              {{ categoryIcon(t.category) }}
            </div>
            <div class="template-info">
              <div class="template-title">{{ t.title }}</div>
              <div class="template-meta">
                {{ t.total_days }}天 &middot; 每日{{ t.pushes_per_day }}次推送
              </div>
              <div v-if="t.description" class="template-desc">{{ t.description }}</div>
            </div>
          </div>
          <div class="template-tags" v-if="t.tags && t.tags.length">
            <van-tag v-for="tag in t.tags" :key="tag" plain round size="small" type="primary" style="margin-right:4px">{{ tag }}</van-tag>
          </div>
          <van-button
            type="primary"
            round
            block
            size="small"
            :loading="enrollingId === t.id"
            style="margin-top: 10px"
            @click="doEnroll(t)"
          >
            立即报名
          </van-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import { programApi } from '@/api/program'

const router = useRouter()
const loading = ref(true)
const myPrograms = ref<any[]>([])
const templates = ref<any[]>([])
const enrollingId = ref('')

const enrolledSlugs = computed(() => new Set(myPrograms.value.map((p: any) => p.template_slug)))
const availableTemplates = computed(() => templates.value.filter((t: any) => !enrolledSlugs.value.has(t.slug)))

const categoryIcon = (cat: string) => {
  const icons: Record<string, string> = {
    glucose: '\u{1F4C9}', weight: '\u{2696}', sleep: '\u{1F634}',
    metabolic: '\u{1F525}', exercise: '\u{1F3C3}', custom: '\u{2B50}',
  }
  return icons[cat] || '\u{1F4CB}'
}

const statusType = (s: string) => {
  const m: Record<string, string> = { active: 'primary', paused: 'warning', completed: 'success', dropped: 'default' }
  return (m[s] || 'default') as any
}

const statusLabel = (s: string) => {
  const m: Record<string, string> = { active: '进行中', paused: '已暂停', completed: '已完成', dropped: '已退出' }
  return m[s] || s
}

const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}分钟前`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}小时前`
  return `${Math.floor(hrs / 24)}天前`
}

const loadData = async () => {
  loading.value = true
  try {
    const [my, tpl] = await Promise.all([
      programApi.getMyPrograms(),
      programApi.listTemplates(),
    ])
    myPrograms.value = my as any
    templates.value = tpl as any
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const doEnroll = async (t: any) => {
  enrollingId.value = t.id
  try {
    const res: any = await programApi.enroll({ template_id: t.id })
    if (res.success) {
      showSuccessToast('报名成功')
      await loadData()
    }
  } catch (e: any) {
    showFailToast(e?.response?.data?.detail || '报名失败')
  } finally {
    enrollingId.value = ''
  }
}

const goToToday = (p: any) => {
  if (p.status === 'active') {
    router.push(`/program/${p.enrollment_id}/today`)
  } else {
    router.push(`/program/${p.enrollment_id}/timeline`)
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-container { min-height: 100vh; background: #f5f5f5; }
.page-content { padding: 12px; }
.loading { text-align: center; padding: 60px 0; }

.section-title { font-size: 15px; font-weight: 600; color: #333; margin: 16px 0 8px 4px; }
.section-title:first-child { margin-top: 0; }

.program-card, .template-card {
  background: #fff; border-radius: 12px; padding: 14px; margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.program-header, .template-header { display: flex; align-items: center; gap: 12px; }
.program-icon {
  width: 44px; height: 44px; border-radius: 12px; display: flex;
  align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0;
}
.cat-glucose { background: #e6f7ff; }
.cat-weight { background: #fff7e6; }
.cat-sleep { background: #f6ffed; }
.cat-metabolic { background: #fff1f0; }
.cat-exercise { background: #f9f0ff; }
.cat-custom { background: #f5f5f5; }
.program-info, .template-info { flex: 1; min-width: 0; }
.program-title, .template-title { font-size: 15px; font-weight: 600; color: #333; }
.program-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; font-size: 12px; color: #999; }
.template-meta { font-size: 12px; color: #999; margin-top: 2px; }
.template-desc { font-size: 12px; color: #666; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.template-tags { margin-top: 8px; }
.program-stats { display: flex; gap: 12px; margin-top: 8px; font-size: 12px; color: #999; }
</style>
