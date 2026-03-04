<template>
  <div class="my-companions">
    <van-nav-bar title="我的同道者" left-arrow @click-left="goBack()" />

    <!-- 统计卡片 -->
    <div class="stats-card">
      <div class="stat-item">
        <span class="num">{{ stats.graduated_count || 0 }}</span>
        <span class="lab">已毕业</span>
      </div>
      <div class="stat-item">
        <span class="num">{{ stats.active_count || 0 }}</span>
        <span class="lab">进行中</span>
      </div>
      <div class="stat-item">
        <span class="num">{{ stats.avg_quality ? Number(stats.avg_quality).toFixed(1) : '-' }}</span>
        <span class="lab">质量分</span>
      </div>
    </div>

    <!-- Tab 切换 -->
    <van-tabs v-model:active="activeTab" @change="onTabChange">
      <!-- 寻找同道 Tab（仅 grower 角色，且未有活跃导师时显示） -->
      <van-tab v-if="isGrower && !hasActiveMentor" title="寻找同道" name="peer">
        <div class="peer-section">
          <van-loading v-if="loadingPeers" class="peer-loading" />

          <template v-else-if="peerCandidates.length">
            <div
              v-for="c in peerCandidates"
              :key="c.mentor_id"
              class="peer-card"
            >
              <div class="peer-avatar">
                <van-image round width="48" height="48" :src="c.avatar_url || defaultAvatar" />
              </div>
              <div class="peer-info">
                <div class="peer-name">{{ c.mentor_name || `用户${c.mentor_id}` }}</div>
                <div class="peer-meta">
                  <van-tag type="primary" size="small">{{ c.mentor_role === 'sharer' ? '分享者' : c.mentor_role }}</van-tag>
                  <span class="peer-stage">{{ c.stage_label || c.stage }}</span>
                </div>
                <div class="peer-score">匹配度 {{ Math.round((c.score || 0) * 100) }}%</div>
                <div v-if="c.rationale" class="peer-rationale">{{ c.rationale }}</div>
              </div>
              <van-button
                type="primary"
                size="small"
                round
                :loading="inviting === c.mentor_id"
                @click="invitePeer(c.mentor_id)"
              >
                邀请同道
              </van-button>
            </div>
          </template>

          <van-empty v-else description="暂无合适的同道者，系统会持续为你匹配" />
        </div>
      </van-tab>

      <van-tab title="我带教的" name="mentees">
        <van-pull-refresh v-model="refreshing" @refresh="loadMentees">
          <van-empty v-if="!mentees.length" description="暂无带教关系" />
          <van-cell-group inset v-else>
            <van-cell
              v-for="m in mentees"
              :key="m.id"
              :title="m.mentee_name || `用户${m.mentee_id}`"
              :label="`${m.mentee_role} · ${m.status === 'active' ? '进行中' : m.status === 'graduated' ? '已毕业' : '已退出'}`"
            >
              <template #right-icon>
                <van-tag :type="m.status === 'active' ? 'primary' : m.status === 'graduated' ? 'success' : 'danger'" plain>
                  {{ m.status === 'active' ? '进行中' : m.status === 'graduated' ? '已毕业' : '已退出' }}
                </van-tag>
              </template>
            </van-cell>
          </van-cell-group>
        </van-pull-refresh>
      </van-tab>

      <van-tab title="我的导师" name="mentors">
        <van-pull-refresh v-model="refreshing" @refresh="loadMentors">
          <div v-if="isGrower && hasActiveMentor" class="has-mentor-tip">
            你已有同道者，继续加油！
          </div>
          <van-empty v-if="!mentors.length" description="暂无导师关系" />
          <van-cell-group inset v-else>
            <van-cell
              v-for="m in mentors"
              :key="m.id"
              :title="m.mentor_name || `用户${m.mentor_id}`"
              :label="`${m.mentor_role} · ${m.status === 'active' ? '进行中' : m.status === 'graduated' ? '已毕业' : '已退出'}`"
            >
              <template #right-icon>
                <van-tag :type="m.status === 'active' ? 'primary' : 'success'" plain>
                  {{ m.status === 'active' ? '进行中' : '已毕业' }}
                </van-tag>
              </template>
            </van-cell>
          </van-cell-group>
        </van-pull-refresh>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { useGoBack } from '@/composables/useGoBack'
const { goBack } = useGoBack()
import { ref, reactive, computed, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { companionApi, peerMatchingApi } from '@/api/credit-promotion'
import storage from '@/utils/storage'

const defaultAvatar = 'https://cdn.jsdelivr.net/gh/vant-ui/vant@main/src/assets/default-avatar.png'

const activeTab = ref('mentees')
const refreshing = ref(false)
const stats = reactive<Record<string, any>>({})
const mentees = ref<any[]>([])
const mentors = ref<any[]>([])
const peerCandidates = ref<any[]>([])
const loadingPeers = ref(false)
const inviting = ref<number | null>(null)

const isGrower = computed(() => {
  const u = storage.getAuthUser()
  return (u?.role || '').toLowerCase() === 'grower'
})

const hasActiveMentor = computed(() => mentors.value.some(m => m.status === 'active'))

async function loadStats() {
  try {
    const res = await companionApi.getStats()
    Object.assign(stats, res)
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

async function loadMentees() {
  try {
    const res = await companionApi.getMyMentees()
    mentees.value = Array.isArray(res) ? res : []
  } catch (e) {
    console.error('加载带教列表失败', e)
  } finally {
    refreshing.value = false
  }
}

async function loadMentors() {
  try {
    const res = await companionApi.getMyMentors()
    mentors.value = Array.isArray(res) ? res : []
  } catch (e) {
    console.error('加载导师列表失败', e)
  } finally {
    refreshing.value = false
  }
}

async function loadPeerCandidates() {
  loadingPeers.value = true
  try {
    const res: any = await peerMatchingApi.recommend({ top_n: 3, mentor_role: 'sharer' })
    peerCandidates.value = Array.isArray(res) ? res : (res?.candidates || res?.items || [])
  } catch (e) {
    console.error('加载同道推荐失败', e)
    peerCandidates.value = []
  } finally {
    loadingPeers.value = false
  }
}

async function invitePeer(mentorId: number) {
  inviting.value = mentorId
  try {
    await peerMatchingApi.accept({ mentor_id: mentorId })
    showSuccessToast('已发送邀请')
    await loadMentors()
    activeTab.value = 'mentors'
  } catch (e) {
    showFailToast('发送失败，请重试')
  } finally {
    inviting.value = null
  }
}

function onTabChange(name: string) {
  if (name === 'mentees' && !mentees.value.length) loadMentees()
  if (name === 'mentors' && !mentors.value.length) loadMentors()
  if (name === 'peer' && !peerCandidates.value.length) loadPeerCandidates()
}

onMounted(async () => {
  loadStats()
  await Promise.allSettled([loadMentees(), loadMentors()])
  if (isGrower.value && !hasActiveMentor.value) {
    activeTab.value = 'peer'
    loadPeerCandidates()
  }
})
</script>

<style scoped>
.my-companions {
  min-height: 100vh;
  background: #f7f8fa;
}
.stats-card {
  display: flex;
  justify-content: space-around;
  margin: 12px 16px;
  padding: 16px;
  background: linear-gradient(135deg, #722ed1, #eb2f96);
  border-radius: 12px;
  color: #fff;
  text-align: center;
}
.stat-item .num {
  font-size: 28px;
  font-weight: bold;
  display: block;
}
.stat-item .lab {
  font-size: 12px;
  opacity: 0.8;
}

/* 寻找同道 */
.peer-section {
  padding: 12px 16px;
}
.peer-loading {
  text-align: center;
  padding: 40px 0;
}
.peer-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.peer-info {
  flex: 1;
  min-width: 0;
}
.peer-name {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}
.peer-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.peer-stage {
  font-size: 12px;
  color: #888;
}
.peer-score {
  font-size: 12px;
  color: #722ed1;
  margin-bottom: 4px;
}
.peer-rationale {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}
.has-mentor-tip {
  margin: 10px 16px;
  padding: 10px 14px;
  background: #f0f9ff;
  border-radius: 8px;
  font-size: 13px;
  color: #1989fa;
  border-left: 3px solid #1989fa;
}
</style>
