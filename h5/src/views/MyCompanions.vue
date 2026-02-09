<template>
  <div class="my-companions">
    <van-nav-bar title="我的同道者" left-arrow @click-left="$router.back()" />

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
import { ref, reactive, onMounted } from 'vue'
import { companionApi } from '@/api/credit-promotion'

const activeTab = ref('mentees')
const refreshing = ref(false)
const stats = reactive<Record<string, any>>({})
const mentees = ref<any[]>([])
const mentors = ref<any[]>([])

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

function onTabChange(name: string) {
  if (name === 'mentees' && !mentees.value.length) loadMentees()
  if (name === 'mentors' && !mentors.value.length) loadMentors()
}

onMounted(() => {
  loadStats()
  loadMentees()
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
</style>
