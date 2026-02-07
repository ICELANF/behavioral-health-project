<!--
引用展示组件 (v2 — 知识库优先 + 来源区分)

区分「知识库引用」和「模型补充」:
- 知识库引用按 scope 分层: 专家私有 > 领域知识 > 平台公共
- 模型补充段有明确的视觉提示 (黄色条)
- 来源统计摘要: "引用了3条知识库来源 + 1处模型补充"
-->

<template>
  <div v-if="hasCitations || hasModelSupplement" class="citation-block">

    <!-- 折叠头: 来源摘要 -->
    <button class="citation-toggle" @click="expanded = !expanded">
      <span class="citation-icon">📚</span>
      <span class="citation-summary">
        {{ summaryText }}
      </span>
      <span class="citation-arrow" :class="{ open: expanded }">▾</span>
    </button>

    <!-- 展开内容 -->
    <transition name="slide">
      <div v-if="expanded" class="citation-body">

        <!-- ── 知识库引用 ── -->
        <div v-if="hasCitations" class="citation-section">
          <div class="section-header knowledge-header">
            <span class="section-icon">📖</span>
            <span>知识库引用</span>
            <span class="section-badge knowledge-badge">
              {{ knowledgeCitations.length }} 条
            </span>
          </div>

          <!-- 按 scope 分组 -->
          <template v-for="group in scopeGroups" :key="group.scope">
            <div v-if="group.items.length > 0" class="scope-group">
              <div class="scope-label">{{ group.label }}</div>

              <div
                v-for="cite in group.items"
                :key="cite.index"
                class="citation-card"
              >
                <!-- 序号 -->
                <div class="cite-badge" :style="badgeStyle">
                  {{ cite.index }}
                </div>

                <!-- 内容 -->
                <div class="cite-body">
                  <div class="cite-title">
                    <span class="cite-doc-title">《{{ cite.docTitle }}》</span>
                    <span v-if="cite.heading" class="cite-heading">
                      &gt; {{ cite.heading }}
                    </span>
                  </div>

                  <div class="cite-meta">
                    <span v-if="cite.author" class="meta-item">
                      ✍️ {{ cite.author }}
                    </span>
                    <span v-if="cite.source" class="meta-item">
                      📖 {{ cite.source }}
                    </span>
                    <span v-if="cite.pageNumber" class="meta-item">
                      📄 第{{ cite.pageNumber }}页
                    </span>
                    <span class="meta-item scope-tag" :class="'scope-' + cite.scope">
                      {{ cite.scopeLabel }}
                    </span>
                    <span
                      class="meta-item cite-score"
                      :title="'相关度: ' + (cite.relevanceScore * 100).toFixed(0) + '%'"
                    >
                      {{ scoreIcon(cite.relevanceScore) }}
                      {{ (cite.relevanceScore * 100).toFixed(0) }}%
                    </span>
                  </div>

                  <!-- 预览 -->
                  <div
                    v-if="cite.contentPreview"
                    class="cite-preview"
                    :class="{ 'cite-preview-full': expandedPreviews.has(cite.index) }"
                    @click="togglePreview(cite.index)"
                  >
                    {{ cite.contentPreview }}
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- ── 模型补充 ── -->
        <div v-if="hasModelSupplement" class="citation-section supplement-section">
          <div class="section-header supplement-header">
            <span class="section-icon">🤖</span>
            <span>模型补充</span>
            <span class="section-badge supplement-badge">
              {{ modelSupplementSections.length }} 处
            </span>
          </div>

          <div class="supplement-notice">
            以下内容基于AI通用知识生成，非来自本平台知识库
          </div>

          <div
            v-for="(section, i) in modelSupplementSections"
            :key="'supp-' + i"
            class="supplement-card"
          >
            <div class="supplement-bar"></div>
            <div class="supplement-text">{{ section }}</div>
          </div>
        </div>

      </div>
    </transition>
  </div>
</template>


<script setup>
import { ref, reactive, computed } from 'vue'

const props = defineProps({
  citations: {
    type: Array,
    default: () => [],
  },
  hasModelSupplement: {
    type: Boolean,
    default: false,
  },
  modelSupplementSections: {
    type: Array,
    default: () => [],
  },
  sourceStats: {
    type: Object,
    default: () => ({}),
  },
  accentColor: {
    type: String,
    default: '#3B82F6',
  },
})

const expanded = ref(false)
const expandedPreviews = reactive(new Set())

// 知识库引用 (排除 model 类型)
const knowledgeCitations = computed(() =>
  props.citations.filter(c => c.sourceType !== 'model')
)

const hasCitations = computed(() => knowledgeCitations.value.length > 0)

// 按 scope 分组 (保持层级顺序)
const scopeGroups = computed(() => {
  const groups = [
    { scope: 'tenant',   label: '🔒 专家私有资料', items: [] },
    { scope: 'domain',   label: '📂 领域专业知识', items: [] },
    { scope: 'platform', label: '🌐 平台通用知识', items: [] },
  ]
  for (const cite of knowledgeCitations.value) {
    const g = groups.find(g => g.scope === cite.scope) || groups[2]
    g.items.push(cite)
  }
  return groups.filter(g => g.items.length > 0)
})

// 摘要文字
const summaryText = computed(() => {
  const parts = []
  const kCount = knowledgeCitations.value.length
  if (kCount > 0) {
    const breakdown = props.sourceStats?.scopeBreakdown || {}
    const details = []
    if (breakdown.tenant) details.push(`${breakdown.tenant}条专家资料`)
    if (breakdown.domain) details.push(`${breakdown.domain}条领域知识`)
    if (breakdown.platform) details.push(`${breakdown.platform}条平台知识`)
    parts.push(`引用了 ${details.join(' + ') || kCount + '条知识库来源'}`)
  }
  if (props.hasModelSupplement) {
    parts.push(`${props.modelSupplementSections?.length || 1}处模型补充`)
  }
  return parts.join(' + ') || '查看来源信息'
})

const badgeStyle = computed(() => ({
  backgroundColor: props.accentColor + '20',
  color: props.accentColor,
  borderColor: props.accentColor + '40',
}))

function togglePreview(index) {
  if (expandedPreviews.has(index)) {
    expandedPreviews.delete(index)
  } else {
    expandedPreviews.add(index)
  }
}

function scoreIcon(score) {
  if (score >= 0.8) return '🟢'
  if (score >= 0.6) return '🟡'
  return '🟠'
}
</script>


<style scoped>
.citation-block {
  margin-top: 12px;
  border-radius: 10px;
  border: 1px solid #E5E7EB;
  background: #FAFAFA;
  overflow: hidden;
}

/* 折叠头 */
.citation-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: #6B7280;
  transition: background 0.15s;
}
.citation-toggle:hover { background: #F3F4F6; }
.citation-icon { font-size: 14px; }
.citation-summary { flex: 1; text-align: left; font-weight: 500; }
.citation-arrow { transition: transform 0.2s; font-size: 12px; }
.citation-arrow.open { transform: rotate(180deg); }

/* 内容区 */
.citation-body {
  padding: 4px 12px 12px;
}

/* 知识 / 补充 分区头 */
.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}
.section-icon { font-size: 14px; }
.section-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.knowledge-badge { background: #DBEAFE; color: #1E40AF; }
.supplement-badge { background: #FEF3C7; color: #92400E; }

/* scope 分组 */
.scope-group { margin-bottom: 8px; }
.scope-label {
  font-size: 11px;
  color: #9CA3AF;
  font-weight: 500;
  padding: 4px 0 4px 4px;
  letter-spacing: 0.5px;
}

/* 引用卡片 */
.citation-card {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  background: white;
  border: 1px solid #E5E7EB;
  margin-bottom: 6px;
  transition: box-shadow 0.15s;
}
.citation-card:hover { box-shadow: 0 1px 4px rgba(0,0,0,0.06); }

.cite-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px; height: 24px; min-width: 24px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid;
}

.cite-body { flex: 1; min-width: 0; }

.cite-title { font-size: 13px; font-weight: 500; color: #1F2937; line-height: 1.4; }
.cite-doc-title { color: #1E40AF; }
.cite-heading { color: #6B7280; font-weight: 400; }

.cite-meta {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-top: 4px; font-size: 11px; color: #9CA3AF;
}
.meta-item { display: flex; align-items: center; gap: 2px; }
.cite-score { margin-left: auto; }

/* scope 标签 */
.scope-tag {
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 500;
}
.scope-tenant { background: #FEE2E2; color: #991B1B; }
.scope-domain { background: #DBEAFE; color: #1E40AF; }
.scope-platform { background: #F3F4F6; color: #6B7280; }

/* 预览 */
.cite-preview {
  margin-top: 6px; font-size: 12px; color: #6B7280;
  line-height: 1.5; max-height: 40px; overflow: hidden;
  cursor: pointer; position: relative;
}
.cite-preview::after {
  content: '... 点击展开';
  position: absolute; right: 0; bottom: 0;
  background: linear-gradient(to right, transparent, white 30%);
  padding-left: 20px; font-size: 11px; color: #3B82F6;
}
.cite-preview-full { max-height: none; }
.cite-preview-full::after { display: none; }

/* ── 模型补充区 ── */
.supplement-section {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #E5E7EB;
}

.supplement-notice {
  font-size: 11px;
  color: #D97706;
  background: #FFFBEB;
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.supplement-card {
  display: flex;
  gap: 8px;
  padding: 8px 10px;
  background: #FFFBEB;
  border-radius: 8px;
  margin-bottom: 6px;
  border: 1px solid #FDE68A;
}

.supplement-bar {
  width: 3px;
  min-height: 100%;
  border-radius: 2px;
  background: #F59E0B;
  flex-shrink: 0;
}

.supplement-text {
  font-size: 12px;
  line-height: 1.6;
  color: #78350F;
}

/* 动画 */
.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; max-height: 0; }
</style>
