<template>
  <div class="knowledge-page">
    <van-nav-bar title="健康知识库" left-arrow @click-left="$router.back()" />

    <van-search v-model="query" placeholder="搜索健康知识..." @search="onSearch" show-action>
      <template #action>
        <span @click="onSearch">搜索</span>
      </template>
    </van-search>

    <!-- 快捷标签 -->
    <div class="tags">
      <van-tag v-for="t in quickTags" :key="t" size="large" plain type="primary"
        @click="query = t; onSearch()" class="tag">{{ t }}</van-tag>
    </div>

    <!-- AI 回答 -->
    <van-cell-group inset v-if="answer" style="margin-top: 12px;">
      <van-cell>
        <template #title><strong>AI 回答</strong></template>
        <template #label>
          <div class="answer-text">{{ answer }}</div>
          <div class="sources" v-if="sources.length">
            <div class="src-label">参考来源:</div>
            <div v-for="(s, i) in sources" :key="i" class="src-item">
              {{ s.source }} <span v-if="s.section">/ {{ s.section }}</span>
              <van-tag size="small">{{ (s.score * 100).toFixed(0) }}%</van-tag>
            </div>
          </div>
        </template>
      </van-cell>
    </van-cell-group>

    <van-loading v-if="loading" style="text-align:center; margin: 40px;" />

    <van-empty v-if="searched && !answer && !loading" description="未找到相关知识" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { showToast } from 'vant'
import { chatApi } from '../../api/v3/index.js'

const query = ref('')
const answer = ref('')
const sources = ref([])
const loading = ref(false)
const searched = ref(false)

const quickTags = ['SPI评分', '行为阶段', '代谢综合征', '中医体质', '动机式访谈', '打卡规则']

async function onSearch() {
  if (!query.value.trim()) return
  loading.value = true
  searched.value = true
  answer.value = ''
  sources.value = []

  try {
    const res = await chatApi.knowledge(query.value.trim())
    if (res?.data) {
      answer.value = res.data.answer || ''
      sources.value = res.data.sources || []
    } else {
      showToast(res?.message || '查询失败')
    }
  } catch { showToast('网络错误') }
  finally { loading.value = false }
}
</script>

<style scoped>
.knowledge-page { padding-bottom: 70px; }
.tags { padding: 8px 12px; display: flex; flex-wrap: wrap; gap: 8px; }
.tag { cursor: pointer; }
.answer-text { font-size: 15px; line-height: 1.7; white-space: pre-wrap; margin: 8px 0; }
.sources { margin-top: 12px; padding-top: 8px; border-top: 1px solid #eee; }
.src-label { font-size: 12px; color: #999; margin-bottom: 4px; }
.src-item { font-size: 13px; color: #666; margin: 2px 0; }
</style>
