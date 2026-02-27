<template>
  <van-action-sheet
    v-model:show="visible"
    title="自选任务"
    :close-on-click-overlay="true"
    :style="{ maxHeight: '75vh' }"
  >
    <div class="catalog-content">
      <!-- 搜索框 -->
      <div class="search-bar">
        <van-search
          v-model="keyword"
          placeholder="搜索任务..."
          shape="round"
          :show-action="false"
        />
      </div>

      <!-- 难度筛选 -->
      <div class="difficulty-tabs">
        <span
          v-for="d in difficultyOptions" :key="d.value"
          class="diff-chip" :class="{ active: activeDifficulty === d.value }"
          @click="activeDifficulty = d.value"
        >
          {{ d.label }}
        </span>
      </div>

      <!-- 分类筛选 (横向滚动 tabs) -->
      <div class="category-tabs">
        <span
          v-for="cat in categories" :key="cat"
          class="cat-chip" :class="{ active: activeCategory === cat }"
          @click="activeCategory = cat"
        >
          {{ cat }}
        </span>
      </div>

      <!-- 目录列表 -->
      <div class="catalog-list" v-if="!catalogLoading">
        <div
          v-for="item in filteredItems" :key="item.id"
          class="catalog-item"
        >
          <div class="item-icon">{{ item.icon || '📋' }}</div>
          <div class="item-info">
            <div class="item-header">
              <span class="item-title">{{ item.default_title }}</span>
              <span class="diff-tag" :class="item.difficulty || 'easy'">
                {{ difficultyLabel(item.difficulty) }}
              </span>
            </div>
            <div class="item-desc" v-if="item.description">{{ item.description }}</div>
            <div class="item-meta">
              <span class="item-mins" v-if="item.estimated_minutes">
                {{ item.estimated_minutes }}分钟
              </span>
              <span class="item-pts" v-if="item.points_reward">
                +{{ item.points_reward.growth }} 成长分
              </span>
              <span class="item-freq">
                {{ freqLabel(item.frequency_suggestion) }}
              </span>
            </div>
          </div>
          <button
            class="add-btn"
            :disabled="addingId === item.id"
            @click="handleAdd(item)"
          >
            {{ addingId === item.id ? '...' : '+ 添加' }}
          </button>
        </div>
        <div v-if="filteredItems.length === 0" class="empty-hint">
          暂无匹配任务
        </div>
      </div>
      <div class="catalog-list" v-else>
        <div class="loading-hint">加载中...</div>
      </div>

      <!-- 自定义输入 -->
      <div class="custom-input-row">
        <input
          v-model="customTitle"
          class="custom-input"
          placeholder="自定义任务名..."
          maxlength="50"
          @keyup.enter="handleCustomAdd"
        />
        <button
          class="custom-add-btn"
          :disabled="!customTitle.trim() || customAdding"
          @click="handleCustomAdd"
        >
          {{ customAdding ? '...' : '添加' }}
        </button>
      </div>
    </div>
  </van-action-sheet>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { showToast } from 'vant'
import type { CatalogItem } from '@/composables/useTaskGroups'

const props = defineProps<{
  show: boolean
  catalog: CatalogItem[]
  catalogLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', val: boolean): void
  (e: 'added'): void
  (e: 'add-from-catalog', catalogId: string, customTitle?: string): void
}>()

const visible = computed({
  get: () => props.show,
  set: (v) => emit('update:show', v),
})

const keyword = ref('')
const activeCategory = ref('全部')
const activeDifficulty = ref('all')
const addingId = ref('')
const customTitle = ref('')
const customAdding = ref(false)

const difficultyOptions = [
  { value: 'all', label: '全部' },
  { value: 'easy', label: '简单' },
  { value: 'moderate', label: '中等' },
  { value: 'challenging', label: '挑战' },
]

function difficultyLabel(d?: string) {
  const map: Record<string, string> = { easy: '简单', moderate: '中等', challenging: '挑战' }
  return map[d || 'easy'] || '简单'
}

function freqLabel(f?: string) {
  const map: Record<string, string> = { daily: '每日', weekly: '每周', as_needed: '按需' }
  return map[f || 'daily'] || ''
}

// 提取唯一分类
const categories = computed(() => {
  const cats = new Set(props.catalog.map(c => c.category))
  return ['全部', ...Array.from(cats).filter(Boolean)]
})

// 筛选
const filteredItems = computed(() => {
  let items = props.catalog
  if (activeCategory.value !== '全部') {
    items = items.filter(i => i.category === activeCategory.value)
  }
  if (activeDifficulty.value !== 'all') {
    items = items.filter(i => (i.difficulty || 'easy') === activeDifficulty.value)
  }
  if (keyword.value.trim()) {
    const kw = keyword.value.trim().toLowerCase()
    items = items.filter(i =>
      i.default_title.toLowerCase().includes(kw) ||
      (i.description || '').toLowerCase().includes(kw)
    )
  }
  return items
})

// 重置筛选
watch(() => props.show, (v) => {
  if (v) {
    keyword.value = ''
    activeCategory.value = '全部'
    activeDifficulty.value = 'all'
  }
})

async function handleAdd(item: CatalogItem) {
  addingId.value = item.id
  emit('add-from-catalog', item.id)
  // 父组件处理实际 API 调用并 emit 'added'
  // 这里延迟重置按钮状态
  setTimeout(() => { addingId.value = '' }, 1500)
}

async function handleCustomAdd() {
  const title = customTitle.value.trim()
  if (!title) return
  customAdding.value = true
  emit('add-from-catalog', '', title)
  customTitle.value = ''
  setTimeout(() => { customAdding.value = false }, 1500)
}
</script>

<style scoped>
.catalog-content { padding: 0 16px 20px; }

/* ── 搜索 ── */
.search-bar { margin-bottom: 8px; }
.search-bar :deep(.van-search) { padding: 0; }
.search-bar :deep(.van-search__content) { background: #f3f4f6; }

/* ── 难度筛选 ── */
.difficulty-tabs {
  display: flex; gap: 6px; margin-bottom: 8px;
}
.diff-chip {
  font-size: 12px; padding: 4px 12px;
  border-radius: 12px; background: #f3f4f6; color: #6b7280;
  cursor: pointer; font-weight: 500; transition: all 0.2s;
  border: 1px solid transparent;
}
.diff-chip.active {
  background: #eff6ff; color: #2563eb; border-color: #93c5fd; font-weight: 600;
}

/* ── 分类 tabs ── */
.category-tabs {
  display: flex; gap: 8px; overflow-x: auto; padding: 4px 0 12px;
  -webkit-overflow-scrolling: touch;
}
.category-tabs::-webkit-scrollbar { display: none; }
.cat-chip {
  flex-shrink: 0; font-size: 13px; padding: 5px 14px;
  border-radius: 16px; background: #f3f4f6; color: #6b7280;
  cursor: pointer; font-weight: 500; transition: all 0.2s;
}
.cat-chip.active {
  background: var(--bhp-brand-primary, #10b981); color: #fff; font-weight: 600;
}

/* ── 列表 ── */
.catalog-list {
  max-height: 35vh; overflow-y: auto; margin-bottom: 12px;
}
.catalog-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 12px 0; border-bottom: 1px solid #f3f4f6;
}
.catalog-item:last-child { border-bottom: none; }
.item-icon { font-size: 24px; flex-shrink: 0; line-height: 1; padding-top: 2px; }
.item-info { flex: 1; min-width: 0; }
.item-header { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }
.item-title { font-size: 14px; font-weight: 500; color: #111827; }
.diff-tag {
  flex-shrink: 0; font-size: 10px; padding: 1px 6px;
  border-radius: 4px; font-weight: 600;
}
.diff-tag.easy { background: #ecfdf5; color: #059669; }
.diff-tag.moderate { background: #eff6ff; color: #2563eb; }
.diff-tag.challenging { background: #fef3c7; color: #d97706; }
.item-desc {
  font-size: 12px; color: #9ca3af; line-height: 1.4;
  margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical;
}
.item-meta {
  display: flex; gap: 8px; font-size: 11px; color: #9ca3af;
}
.item-pts { color: #d97706; font-weight: 600; }
.item-freq { color: #6b7280; }
.add-btn {
  flex-shrink: 0; background: #f0fdf4; color: #15803d;
  border: 1px solid #bbf7d0; border-radius: 8px;
  padding: 5px 12px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.2s; margin-top: 4px;
}
.add-btn:active { transform: scale(0.95); }
.add-btn:disabled { opacity: 0.5; cursor: default; }
.empty-hint, .loading-hint {
  text-align: center; padding: 24px 0; color: #9ca3af; font-size: 14px;
}

/* ── 自定义输入 ── */
.custom-input-row {
  display: flex; gap: 8px; padding-top: 12px; border-top: 1px solid #e5e7eb;
}
.custom-input {
  flex: 1; border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 10px 14px; font-size: 14px; outline: none;
  transition: border-color 0.2s;
}
.custom-input:focus { border-color: var(--bhp-brand-primary, #10b981); }
.custom-input::placeholder { color: #d1d5db; }
.custom-add-btn {
  flex-shrink: 0; background: var(--bhp-brand-primary, #10b981); color: #fff;
  border: none; border-radius: 10px; padding: 10px 18px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 0.2s;
}
.custom-add-btn:active { transform: scale(0.95); }
.custom-add-btn:disabled { opacity: 0.5; cursor: default; }
</style>
