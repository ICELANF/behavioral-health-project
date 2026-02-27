<template>
  <div class="global-search">
    <van-search
      v-model="searchQuery"
      :placeholder="searchScope.placeholder.value"
      shape="round"
      @search="doSearch"
      @clear="clearResults"
    >
      <template #right-icon>
        <div class="search-right-icons">
          <van-icon
            v-if="voiceInput.isSupported"
            name="audio"
            :class="{ recording: voiceInput.isRecording.value }"
            @click.stop="toggleVoice"
          />
          <van-icon name="photograph" @click.stop="triggerImage" />
        </div>
      </template>
    </van-search>

    <!-- 搜索结果弹出层 -->
    <van-popup v-model:show="showResults" position="top" :style="{ paddingTop: '56px', maxHeight: '70vh', overflowY: 'auto' }">
      <div v-if="searchLoading" style="text-align: center; padding: 32px 0">
        <van-loading type="spinner" />
      </div>
      <div v-else-if="searchTotal === 0 && searchQuery" style="text-align: center; padding: 32px 0; color: #999; font-size: 14px">
        未找到相关内容
      </div>
      <template v-else>
        <van-cell-group
          v-for="(items, category) in searchResults"
          :key="category"
          :title="categoryLabel(category as string)"
        >
          <van-cell
            v-for="item in items"
            :key="item.id"
            :title="item.title || item.full_name || item.username || item.content"
            :label="item.role || item.category || item.status || ''"
            is-link
            @click="goToResult(category as string, item)"
          />
        </van-cell-group>
      </template>

      <!-- 图片分析结果 -->
      <van-cell-group v-if="imageAnalysis" title="图片识别结果">
        <van-cell :title="imageAnalysis" />
      </van-cell-group>
    </van-popup>

    <input ref="imgInput" type="file" accept="image/*" capture="environment" style="display:none" @change="onImage" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'
import { useSearchScope } from '@/composables/useSearchScope'
import { useVoiceInput } from '@/composables/useVoiceInput'

const router = useRouter()
const searchScope = useSearchScope()
const voiceInput = useVoiceInput()

const searchQuery = ref('')
const searchResults = ref<Record<string, any[]>>({})
const searchTotal = ref(0)
const searchLoading = ref(false)
const showResults = ref(false)
const imageAnalysis = ref('')
const imgInput = ref<HTMLInputElement | null>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null

watch(searchQuery, (val) => {
  if (searchTimer) clearTimeout(searchTimer)
  if (!val || !val.trim()) {
    clearResults()
    return
  }
  searchTimer = setTimeout(() => doSearch(), 300)
})

// Watch voice transcript → auto-search
watch(() => voiceInput.transcript.value, (text) => {
  if (text) {
    searchQuery.value = text
  }
})

const CATEGORY_LABELS: Record<string, string> = {
  users: '用户',
  prescriptions: '行为处方',
  tasks: '每日任务',
  checkins: '打卡记录',
  content: '学习内容',
}

function categoryLabel(key: string) {
  return CATEGORY_LABELS[key] || key
}

async function doSearch() {
  const q = searchQuery.value?.trim()
  if (!q) return
  searchLoading.value = true
  showResults.value = true
  try {
    const res: any = await api.get('/api/v1/search', {
      params: { q, modules: searchScope.modules.value.join(','), limit: 20 }
    })
    const data = res.data || res
    searchResults.value = data.results || {}
    searchTotal.value = data.total || 0
  } catch {
    searchResults.value = {}
    searchTotal.value = 0
  } finally {
    searchLoading.value = false
  }
}

function clearResults() {
  searchResults.value = {}
  searchTotal.value = 0
  showResults.value = false
  imageAnalysis.value = ''
}

function toggleVoice() {
  voiceInput.toggleRecording()
  if (voiceInput.isRecording.value) {
    showToast({ message: '正在录音...', type: 'loading', duration: 0 })
  }
}

function triggerImage() {
  imgInput.value?.click()
}

async function onImage(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  target.value = ''

  const formData = new FormData()
  formData.append('file', file)

  showResults.value = true
  searchLoading.value = true
  try {
    const res: any = await api.post('/api/v1/food/recognize', formData)
    const data = res.data || res
    // 格式化食物识别结果
    if (data.food_name) {
      const parts = [data.food_name]
      if (data.calories) parts.push(`热量: ${data.calories} kcal`)
      if (data.protein) parts.push(`蛋白质: ${data.protein}g`)
      if (data.fat) parts.push(`脂肪: ${data.fat}g`)
      if (data.carbs) parts.push(`碳水: ${data.carbs}g`)
      imageAnalysis.value = parts.join(' | ')
    } else if (data.description || data.result) {
      imageAnalysis.value = data.description || data.result
    } else if (data.image_url) {
      imageAnalysis.value = '图片已保存，AI 分析暂不可用'
    } else {
      imageAnalysis.value = '未识别到食物信息'
    }
  } catch {
    showToast({ message: '图片识别失败', type: 'fail' })
  } finally {
    searchLoading.value = false
  }
}

function goToResult(category: string, item: any) {
  showResults.value = false
  searchQuery.value = ''
  switch (category) {
    case 'content':
      router.push(`/content/${item.type || 'article'}/${item.id}`)
      break
    case 'tasks':
      router.push('/tasks')
      break
    case 'users':
      router.push({ path: '/profile', query: { uid: item.id } })
      break
    default:
      router.push('/tasks')
  }
}
</script>

<style scoped>
.global-search {
  padding: 0 12px;
}

.search-right-icons {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  color: #969799;
}

.search-right-icons .van-icon {
  cursor: pointer;
  transition: color 0.2s;
}

.search-right-icons .van-icon:active {
  color: var(--bhp-brand-primary, #10b981);
}

.recording {
  color: #ee0a24 !important;
  animation: pulse-voice 1s infinite;
}

@keyframes pulse-voice {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
