<template>
  <div class="card-list">
    <!-- 筛选区 -->
    <a-card class="filter-card">
      <a-form layout="inline">
        <a-form-item label="关键词">
          <a-input v-model:value="filters.keyword" placeholder="搜索标题" allow-clear style="width: 180px" />
        </a-form-item>
        <a-form-item label="领域">
          <a-select v-model:value="filters.domain" placeholder="全部领域" allow-clear style="width: 120px">
            <a-select-option v-for="domain in TRIGGER_DOMAINS" :key="domain.value" :value="domain.value">
              {{ domain.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="练习类型">
          <a-select v-model:value="filters.practiceType" placeholder="全部类型" allow-clear style="width: 120px">
            <a-select-option value="daily">每日练习</a-select-option>
            <a-select-option value="situational">情境练习</a-select-option>
            <a-select-option value="weekly">周度练习</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="filters.status" placeholder="全部状态" allow-clear style="width: 100px">
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="offline">已下架</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSearch">搜索</a-button>
          <a-button style="margin-left: 8px" @click="handleReset">重置</a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 操作栏 -->
    <div class="action-bar">
      <a-button type="primary" @click="handleCreate">
        <template #icon><PlusOutlined /></template>
        创建练习卡片
      </a-button>
    </div>

    <!-- 卡片网格展示 -->
    <a-spin :spinning="loading">
      <div class="cards-grid">
        <div
          v-for="card in cards"
          :key="card.card_id"
          class="practice-card"
          :style="{ background: card.cover_color || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }"
        >
          <div class="card-header">
            <span class="card-icon">{{ card.icon }}</span>
            <div class="card-badges">
              <a-tag :color="getStatusColor(card.status)" size="small">{{ getStatusLabel(card.status) }}</a-tag>
              <a-tag color="blue" size="small">{{ getPracticeTypeLabel(card.practice_type) }}</a-tag>
            </div>
          </div>
          <div class="card-body">
            <h3 class="card-title">{{ card.title }}</h3>
            <p class="card-desc">{{ truncate(card.description, 50) }}</p>
            <div class="card-meta">
              <span><ClockCircleOutlined /> {{ card.estimated_minutes }}分钟</span>
              <span><StarOutlined /> {{ getDifficultyLabel(card.difficulty) }}</span>
              <span>{{ getDomainLabel(card.domain) }}</span>
            </div>
          </div>
          <div class="card-stats">
            <span><PlayCircleOutlined /> {{ formatNumber(card.use_count) }}次使用</span>
            <span><CheckCircleOutlined /> {{ formatNumber(card.complete_count) }}次完成</span>
          </div>
          <div class="card-actions">
            <a-button type="text" size="small" @click="handleView(card)">
              <EyeOutlined /> 查看
            </a-button>
            <a-button type="text" size="small" @click="handleEdit(card)">
              <EditOutlined /> 编辑
            </a-button>
            <a-dropdown>
              <a-button type="text" size="small">
                <MoreOutlined />
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item @click="handleDuplicate(card)">复制</a-menu-item>
                  <a-menu-item v-if="card.status === 'published'" @click="handleOffline(card)">下架</a-menu-item>
                  <a-menu-item v-if="card.status === 'draft'" @click="handlePublish(card)">发布</a-menu-item>
                  <a-menu-divider />
                  <a-menu-item danger @click="handleDelete(card)">删除</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>

        <!-- 空状态 -->
        <a-empty v-if="cards.length === 0 && !loading" description="暂无练习卡片" />
      </div>
    </a-spin>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <a-pagination
        v-model:current="pagination.current"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        show-size-changer
        :show-total="(total: number) => `共 ${total} 个卡片`"
        @change="handlePageChange"
      />
    </div>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:open="editModalVisible"
      :title="editingCard ? '编辑练习卡片' : '创建练习卡片'"
      width="700px"
      :footer="null"
    >
      <a-form :model="editForm" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="标题" required>
          <a-input v-model:value="editForm.title" placeholder="如：3分钟呼吸放松" />
        </a-form-item>
        <a-form-item label="描述" required>
          <a-textarea v-model:value="editForm.description" :rows="2" placeholder="简短描述练习内容和效果" />
        </a-form-item>
        <a-form-item label="图标">
          <a-input v-model:value="editForm.icon" placeholder="使用 emoji 作为图标，如 🧘" style="width: 100px" />
          <span class="icon-preview" v-if="editForm.icon">预览：{{ editForm.icon }}</span>
        </a-form-item>
        <a-form-item label="背景色">
          <a-input v-model:value="editForm.cover_color" placeholder="如：linear-gradient(135deg, #667eea 0%, #764ba2 100%)" />
        </a-form-item>
        <a-form-item label="领域" required>
          <a-select v-model:value="editForm.domain" placeholder="选择所属领域">
            <a-select-option v-for="domain in TRIGGER_DOMAINS" :key="domain.value" :value="domain.value">
              {{ domain.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="练习类型" required>
          <a-radio-group v-model:value="editForm.practice_type">
            <a-radio-button value="daily">每日练习</a-radio-button>
            <a-radio-button value="situational">情境练习</a-radio-button>
            <a-radio-button value="weekly">周度练习</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="预计时长">
          <a-input-number v-model:value="editForm.estimated_minutes" :min="1" :max="60" /> 分钟
        </a-form-item>
        <a-form-item label="难度">
          <a-rate v-model:value="editForm.difficulty" :count="3" />
        </a-form-item>

        <a-divider>练习步骤</a-divider>

        <div class="steps-editor">
          <div v-for="(step, index) in editForm.steps" :key="index" class="step-item">
            <div class="step-header">
              <span class="step-number">步骤 {{ index + 1 }}</span>
              <a-button type="text" size="small" danger @click="removeStep(index)">
                <DeleteOutlined />
              </a-button>
            </div>
            <a-form-item label="指导语">
              <a-textarea v-model:value="step.instruction" :rows="2" placeholder="描述这一步需要做什么" />
            </a-form-item>
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="时长(秒)">
                  <a-input-number v-model:value="step.duration_seconds" :min="0" style="width: 100%" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="交互类型">
                  <a-select v-model:value="step.interaction" placeholder="选择交互方式">
                    <a-select-option value="read">阅读</a-select-option>
                    <a-select-option value="timer">计时</a-select-option>
                    <a-select-option value="input">输入</a-select-option>
                    <a-select-option value="breathe">呼吸引导</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
          </div>
          <a-button type="dashed" block @click="addStep">
            <PlusOutlined /> 添加步骤
          </a-button>
        </div>

        <a-divider>小贴士</a-divider>
        <a-form-item label="练习贴士">
          <a-select v-model:value="editForm.tips" mode="tags" placeholder="输入后按回车添加" />
        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 4 }">
          <a-space>
            <a-button type="primary" @click="handleSave">保存并发布</a-button>
            <a-button @click="handleSaveAsDraft">存为草稿</a-button>
            <a-button @click="editModalVisible = false">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 查看弹窗 -->
    <a-modal
      v-model:open="viewModalVisible"
      :title="currentCard?.title"
      width="500px"
      :footer="null"
    >
      <template v-if="currentCard">
        <div
          class="preview-card"
          :style="{ background: currentCard.cover_color || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }"
        >
          <div class="preview-icon">{{ currentCard.icon }}</div>
          <h2>{{ currentCard.title }}</h2>
          <p>{{ currentCard.description }}</p>
          <div class="preview-meta">
            <span>{{ currentCard.estimated_minutes }}分钟</span>
            <span>{{ getDifficultyLabel(currentCard.difficulty) }}</span>
          </div>
        </div>

        <a-divider>练习步骤</a-divider>
        <a-timeline>
          <a-timeline-item v-for="(step, index) in currentCard.steps" :key="index">
            <div class="step-preview">
              <div class="step-instruction">{{ step.instruction }}</div>
              <div class="step-info">
                <span v-if="step.duration_seconds">{{ step.duration_seconds }}秒</span>
                <span v-if="step.interaction">{{ getInteractionLabel(step.interaction) }}</span>
              </div>
            </div>
          </a-timeline-item>
        </a-timeline>

        <template v-if="currentCard.tips?.length">
          <a-divider>小贴士</a-divider>
          <ul class="tips-list">
            <li v-for="(tip, index) in currentCard.tips" :key="index">{{ tip }}</li>
          </ul>
        </template>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  PlusOutlined,
  ClockCircleOutlined,
  StarOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  EditOutlined,
  MoreOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { PracticeCard, PracticeStep, ContentStatus } from '@/types/content'
import { TRIGGER_DOMAINS } from '@/constants'

// 筛选
const filters = reactive({
  keyword: '',
  domain: undefined as string | undefined,
  practiceType: undefined as string | undefined,
  status: undefined as ContentStatus | undefined
})

// 列表
const loading = ref(false)
const cards = ref<PracticeCard[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0
})

// 编辑弹窗
const editModalVisible = ref(false)
const editingCard = ref<PracticeCard | null>(null)
const editForm = reactive({
  title: '',
  description: '',
  icon: '🧘',
  cover_color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  domain: '',
  practice_type: 'daily' as 'daily' | 'situational' | 'weekly',
  estimated_minutes: 5,
  difficulty: 1 as 1 | 2 | 3,
  steps: [] as PracticeStep[],
  tips: [] as string[]
})

// 查看弹窗
const viewModalVisible = ref(false)
const currentCard = ref<PracticeCard | null>(null)

// 辅助函数
const getDomainLabel = (domain: string) => TRIGGER_DOMAINS.find(d => d.value === domain)?.label || domain
const getStatusLabel = (status: ContentStatus) => {
  const map: Record<string, string> = { draft: '草稿', published: '已发布', offline: '已下架' }
  return map[status] || status
}
const getStatusColor = (status: ContentStatus) => {
  const map: Record<string, string> = { draft: 'default', published: 'green', offline: 'red' }
  return map[status] || 'default'
}
const getPracticeTypeLabel = (type: string) => {
  const map: Record<string, string> = { daily: '每日', situational: '情境', weekly: '周度' }
  return map[type] || type
}
const getDifficultyLabel = (level: number) => ['简单', '中等', '困难'][level - 1] || ''
const getInteractionLabel = (type: string) => {
  const map: Record<string, string> = { read: '阅读', timer: '计时', input: '输入', breathe: '呼吸引导' }
  return map[type] || type
}
const truncate = (str: string, len: number) => str.length > len ? str.slice(0, len) + '...' : str
const formatNumber = (num: number) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

// 事件处理
const handleSearch = () => {
  pagination.current = 1
  fetchCards()
}

const handleReset = () => {
  filters.keyword = ''
  filters.domain = undefined
  filters.practiceType = undefined
  filters.status = undefined
  handleSearch()
}

const handlePageChange = () => {
  fetchCards()
}

const handleCreate = () => {
  editingCard.value = null
  Object.assign(editForm, {
    title: '',
    description: '',
    icon: '🧘',
    cover_color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    domain: '',
    practice_type: 'daily',
    estimated_minutes: 5,
    difficulty: 1,
    steps: [{ order: 1, instruction: '', duration_seconds: 0, interaction: 'read' }],
    tips: []
  })
  editModalVisible.value = true
}

const handleEdit = (card: PracticeCard) => {
  editingCard.value = card
  Object.assign(editForm, {
    title: card.title,
    description: card.description,
    icon: card.icon,
    cover_color: card.cover_color,
    domain: card.domain,
    practice_type: card.practice_type,
    estimated_minutes: card.estimated_minutes,
    difficulty: card.difficulty,
    steps: [...card.steps],
    tips: card.tips ? [...card.tips] : []
  })
  editModalVisible.value = true
}

const handleView = (card: PracticeCard) => {
  currentCard.value = card
  viewModalVisible.value = true
}

const addStep = () => {
  editForm.steps.push({
    order: editForm.steps.length + 1,
    instruction: '',
    duration_seconds: 0,
    interaction: 'read'
  })
}

const removeStep = (index: number) => {
  editForm.steps.splice(index, 1)
  editForm.steps.forEach((step, i) => { step.order = i + 1 })
}

const handleSave = () => {
  message.success('保存成功')
  editModalVisible.value = false
  fetchCards()
}

const handleSaveAsDraft = () => {
  message.success('已存为草稿')
  editModalVisible.value = false
  fetchCards()
}

const handleDuplicate = (card: PracticeCard) => {
  message.success('已复制')
}

const handlePublish = (card: PracticeCard) => {
  message.success('已发布')
  fetchCards()
}

const handleOffline = (card: PracticeCard) => {
  message.success('已下架')
  fetchCards()
}

const handleDelete = (card: PracticeCard) => {
  message.success('已删除')
  fetchCards()
}

// 获取数据
const fetchCards = async () => {
  loading.value = true
  try {
    // 模拟数据
    cards.value = [
      {
        card_id: 'card1',
        type: 'card',
        source: 'platform',
        status: 'published',
        title: '3分钟呼吸放松',
        description: '通过简单的深呼吸练习，快速缓解紧张和焦虑，恢复内心平静。',
        icon: '🧘',
        cover_color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        domain: 'stress',
        practice_type: 'situational',
        estimated_minutes: 3,
        difficulty: 1,
        steps: [
          { order: 1, instruction: '找一个舒适的坐姿，闭上眼睛', duration_seconds: 10, interaction: 'read' },
          { order: 2, instruction: '深吸气4秒，感受腹部缓缓隆起', duration_seconds: 4, interaction: 'breathe' },
          { order: 3, instruction: '屏住呼吸4秒', duration_seconds: 4, interaction: 'timer' },
          { order: 4, instruction: '缓慢呼气6秒，感受身体放松', duration_seconds: 6, interaction: 'breathe' },
          { order: 5, instruction: '重复以上呼吸5次', duration_seconds: 70, interaction: 'timer' },
          { order: 6, instruction: '慢慢睁开眼睛，感受此刻的平静', duration_seconds: 10, interaction: 'read' }
        ],
        tips: ['可以在工作间隙随时练习', '配合轻柔的音乐效果更好'],
        author_id: 'platform',
        author_name: '平台',
        visibility: 'public',
        use_count: 15680,
        complete_count: 12340,
        like_count: 2890,
        created_at: '2025-01-01T10:00:00Z',
        updated_at: '2025-01-01T10:00:00Z'
      },
      {
        card_id: 'card2',
        type: 'card',
        source: 'platform',
        status: 'published',
        title: '睡前身体扫描',
        description: '通过逐步放松身体各部位，帮助你进入深度睡眠状态。',
        icon: '😴',
        cover_color: 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)',
        domain: 'sleep',
        practice_type: 'daily',
        estimated_minutes: 10,
        difficulty: 2,
        steps: [
          { order: 1, instruction: '躺下，闭上眼睛，做3次深呼吸', duration_seconds: 30, interaction: 'breathe' },
          { order: 2, instruction: '将注意力集中在脚趾，感受它们的状态，然后放松', duration_seconds: 60, interaction: 'timer' },
          { order: 3, instruction: '注意力移到小腿和膝盖，感受并放松', duration_seconds: 60, interaction: 'timer' },
          { order: 4, instruction: '继续向上，放松大腿和臀部', duration_seconds: 60, interaction: 'timer' },
          { order: 5, instruction: '放松腹部和胸部，感受呼吸的起伏', duration_seconds: 60, interaction: 'timer' },
          { order: 6, instruction: '放松双臂、双手和手指', duration_seconds: 60, interaction: 'timer' },
          { order: 7, instruction: '最后放松颈部、面部和头部', duration_seconds: 60, interaction: 'timer' },
          { order: 8, instruction: '感受整个身体的放松状态，自然入睡', duration_seconds: 30, interaction: 'read' }
        ],
        tips: ['建议在关灯后进行', '可以配合助眠音频'],
        author_id: 'platform',
        author_name: '平台',
        visibility: 'public',
        use_count: 8920,
        complete_count: 7650,
        like_count: 1890,
        created_at: '2025-01-05T10:00:00Z',
        updated_at: '2025-01-05T10:00:00Z'
      },
      {
        card_id: 'card3',
        type: 'card',
        source: 'expert',
        status: 'published',
        title: '感恩日记',
        description: '每天记录3件感恩的事，培养积极心态，提升幸福感。',
        icon: '🙏',
        cover_color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        domain: 'emotion',
        practice_type: 'daily',
        estimated_minutes: 5,
        difficulty: 1,
        steps: [
          { order: 1, instruction: '找一个安静的时刻，准备好笔和本子（或使用下方输入）', duration_seconds: 10, interaction: 'read' },
          { order: 2, instruction: '回想今天发生的事情', duration_seconds: 30, interaction: 'timer' },
          { order: 3, instruction: '写下第一件让你感恩的事', interaction: 'input' },
          { order: 4, instruction: '写下第二件让你感恩的事', interaction: 'input' },
          { order: 5, instruction: '写下第三件让你感恩的事', interaction: 'input' },
          { order: 6, instruction: '感受内心的温暖和满足', duration_seconds: 20, interaction: 'read' }
        ],
        tips: ['可以是很小的事情，比如一杯好喝的咖啡', '坚持21天会形成习惯'],
        author_id: 'expert1',
        author_name: '李明远老师',
        visibility: 'public',
        use_count: 6780,
        complete_count: 5890,
        like_count: 1560,
        created_at: '2025-01-10T10:00:00Z',
        updated_at: '2025-01-10T10:00:00Z'
      },
      {
        card_id: 'card4',
        type: 'card',
        source: 'coach',
        status: 'draft',
        title: '情绪急救包',
        description: '当负面情绪来袭时，用这5分钟快速恢复平静。',
        icon: '🆘',
        cover_color: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
        domain: 'emotion',
        practice_type: 'situational',
        estimated_minutes: 5,
        difficulty: 1,
        steps: [
          { order: 1, instruction: '停下手中的事，给自己一个暂停', duration_seconds: 10, interaction: 'read' },
          { order: 2, instruction: '给当前的情绪命名：我现在感到______', interaction: 'input' },
          { order: 3, instruction: '深呼吸3次，吸4秒呼6秒', duration_seconds: 30, interaction: 'breathe' },
          { order: 4, instruction: '感受双脚踩在地面的感觉，让自己接地', duration_seconds: 30, interaction: 'timer' },
          { order: 5, instruction: '问自己：这个情绪在告诉我什么？', interaction: 'input' }
        ],
        tips: ['情绪没有对错，只是信号', '练习越多，恢复越快'],
        author_id: 'coach1',
        author_name: '张教练',
        visibility: 'registered',
        use_count: 0,
        complete_count: 0,
        like_count: 0,
        review_status: 'pending',
        created_at: '2026-02-03T10:00:00Z',
        updated_at: '2026-02-03T10:00:00Z'
      }
    ] as PracticeCard[]
    pagination.total = cards.value.length
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCards()
})
</script>

<style scoped>
.card-list {
  padding: 24px;
}

.filter-card {
  margin-bottom: 16px;
}

.action-bar {
  margin-bottom: 16px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  min-height: 200px;
}

.practice-card {
  border-radius: 16px;
  padding: 20px;
  color: white;
  display: flex;
  flex-direction: column;
  min-height: 280px;
  position: relative;
  overflow: hidden;
}

.practice-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.1);
  pointer-events: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  position: relative;
  z-index: 1;
}

.card-icon {
  font-size: 36px;
}

.card-badges {
  display: flex;
  gap: 4px;
}

.card-body {
  flex: 1;
  position: relative;
  z-index: 1;
  margin: 12px 0;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: white;
}

.card-desc {
  font-size: 13px;
  opacity: 0.9;
  line-height: 1.4;
  margin: 0;
}

.card-meta {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  font-size: 12px;
  opacity: 0.8;
}

.card-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
}

.card-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-actions {
  display: flex;
  gap: 4px;
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 4px;
}

.card-actions .ant-btn {
  color: white;
  flex: 1;
}

.card-actions .ant-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* 编辑弹窗 */
.icon-preview {
  margin-left: 12px;
  font-size: 24px;
}

.steps-editor {
  margin-bottom: 16px;
}

.step-item {
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.step-number {
  font-weight: 500;
  color: #1890ff;
}

/* 查看弹窗 */
.preview-card {
  border-radius: 16px;
  padding: 24px;
  color: white;
  text-align: center;
  margin-bottom: 16px;
}

.preview-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.preview-card h2 {
  color: white;
  margin: 0 0 8px 0;
}

.preview-card p {
  opacity: 0.9;
  margin: 0 0 12px 0;
}

.preview-meta {
  display: flex;
  justify-content: center;
  gap: 16px;
  font-size: 14px;
  opacity: 0.8;
}

.step-preview {
  padding: 4px 0;
}

.step-instruction {
  font-size: 14px;
  color: #333;
}

.step-info {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.step-info span {
  margin-right: 12px;
}

.tips-list {
  padding-left: 20px;
  color: #666;
}

.tips-list li {
  margin-bottom: 8px;
}
</style>
