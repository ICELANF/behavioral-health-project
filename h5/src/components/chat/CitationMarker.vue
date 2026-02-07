<!--
内联引用标记 (v2 — 知识库/模型补充 双标记)

- [1] [2] 等知识库引用标记 → 蓝色可点击标签
- 【补充】标记 → 黄色提示标签
- 【以下为通用专业知识...】 → 全段黄色底纹提示
-->

<template>
  <span class="citation-text" v-html="renderedHtml"></span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  citations: { type: Array, default: () => [] },
  hasModelSupplement: { type: Boolean, default: false },
  accentColor: { type: String, default: '#3B82F6' },
})

const emit = defineEmits(['cite-click'])

const citationIndexes = computed(() =>
  new Set(props.citations.map(c => c.index))
)

const renderedHtml = computed(() => {
  if (!props.text) return ''
  let html = escapeHtml(props.text)

  // 1. 替换 [1] [2] 为可点击知识库引用标签
  html = html.replace(/\[(\d+)\]/g, (match, num) => {
    const idx = parseInt(num)
    if (citationIndexes.value.has(idx)) {
      const cite = props.citations.find(c => c.index === idx)
      const title = cite
        ? `${cite.docTitle}${cite.heading ? ' > ' + cite.heading : ''}`
        : ''
      const scopeClass = cite ? `cite-scope-${cite.scope || 'platform'}` : ''
      return `<span
        class="cite-ref ${scopeClass}"
        data-cite-index="${idx}"
        title="${title}"
        style="--accent: ${props.accentColor}"
      >[${idx}]</span>`
    }
    return match
  })

  // 2. 替换 【补充】/【模型补充】/【补充说明】 为黄色标签
  html = html.replace(
    /【(补充|模型补充|补充说明)】/g,
    '<span class="model-tag" title="以下内容基于AI通用知识，非来自知识库">🤖 $1</span>'
  )

  // 3. 替换 【以下为通用专业知识...】 为提示块
  html = html.replace(
    /【以下为通用专业知识[^】]*】/g,
    '<span class="model-notice">🤖 以下为通用专业知识，非本平台专属资料</span>'
  )

  // 4. 替换 **补充说明**: 格式
  html = html.replace(
    /\*{0,2}补充说明\*{0,2}[:：]/g,
    '<span class="model-tag" title="以下内容基于AI通用知识，非来自知识库">🤖 补充说明：</span>'
  )

  // 5. 换行处理
  html = html.replace(/\n/g, '<br>')

  return html
})

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
</script>

<style scoped>
.citation-text {
  line-height: 1.7;
}

/* 知识库引用标签 [1] [2] */
.citation-text :deep(.cite-ref) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 4px;
  margin: 0 1px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--accent, #3B82F6);
  background: color-mix(in srgb, var(--accent, #3B82F6) 10%, transparent);
  cursor: pointer;
  vertical-align: super;
  transition: all 0.15s;
}
.citation-text :deep(.cite-ref:hover) {
  background: color-mix(in srgb, var(--accent, #3B82F6) 20%, transparent);
  transform: scale(1.1);
}

/* scope 区分色 */
.citation-text :deep(.cite-scope-tenant) {
  color: #DC2626;
  background: #FEE2E220;
}
.citation-text :deep(.cite-scope-domain) {
  color: var(--accent, #3B82F6);
}
.citation-text :deep(.cite-scope-platform) {
  color: #6B7280;
  background: #F3F4F610;
}

/* 模型补充标签 【补充】 */
.citation-text :deep(.model-tag) {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  margin: 0 2px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #92400E;
  background: #FEF3C7;
  border: 1px solid #FDE68A;
  vertical-align: baseline;
}

/* 无知识库时的整体通知 */
.citation-text :deep(.model-notice) {
  display: block;
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #92400E;
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  border-left: 3px solid #F59E0B;
}
</style>
