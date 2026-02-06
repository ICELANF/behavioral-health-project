<template>
  <div class="my-tools">
    <div class="page-header">
      <h2>我的工具箱</h2>
    </div>

    <!-- Tool Grid -->
    <div class="tools-grid">
      <div v-for="tool in tools" :key="tool.key" class="tool-card" :style="{ borderColor: tool.color }" @click="useTool(tool)">
        <div class="tool-icon" :style="{ background: tool.bgColor }">{{ tool.icon }}</div>
        <div class="tool-info">
          <span class="tool-name">{{ tool.name }}</span>
          <span class="tool-desc">{{ tool.description }}</span>
        </div>
        <div class="tool-stats">
          <span class="stat-num">{{ tool.useCount }}</span>
          <span class="stat-label">使用次数</span>
        </div>
      </div>
    </div>

    <!-- Recent Usage -->
    <a-card title="最近使用" style="margin-top: 16px; margin-bottom: 16px">
      <div v-for="item in recentUsage" :key="item.id" class="usage-item">
        <span class="usage-icon">{{ item.icon }}</span>
        <div class="usage-info">
          <span class="usage-name">{{ item.toolName }}</span>
          <span class="usage-context">学员: {{ item.student }} · {{ item.action }}</span>
        </div>
        <span class="usage-time">{{ item.time }}</span>
      </div>
      <p v-if="recentUsage.length === 0" style="text-align: center; color: #ccc">暂无使用记录</p>
    </a-card>

    <!-- Usage Statistics -->
    <a-card title="使用统计">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-statistic title="本月总使用" :value="totalMonthUsage" suffix="次" />
        </a-col>
        <a-col :span="8">
          <a-statistic title="最常用工具" :value="mostUsedTool" />
        </a-col>
        <a-col :span="8">
          <a-statistic title="工具有效率" :value="effectiveRate" suffix="%" value-style="color: #3f8600" />
        </a-col>
      </a-row>
      <div class="usage-chart" style="margin-top: 16px">
        <div v-for="tool in tools" :key="tool.key" class="chart-item">
          <span class="chart-label">{{ tool.name }}</span>
          <div class="chart-bar-bg">
            <div class="chart-bar" :style="{ width: (tool.useCount / maxUseCount * 100) + '%', background: tool.color }"></div>
          </div>
          <span class="chart-count">{{ tool.useCount }}</span>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

const router = useRouter()

const tools = ref([
  { key: 'stress', name: '压力快速测评', description: '引导学员完成压力筛查评估', icon: '📋', color: '#cf1322', bgColor: '#fff1f0', useCount: 45 },
  { key: 'empathy', name: '同理心倾听', description: 'OARS动机访谈引导', icon: '💜', color: '#722ed1', bgColor: '#f9f0ff', useCount: 38 },
  { key: 'habit', name: '习惯处方卡', description: '制定SMART微习惯目标', icon: '🎯', color: '#389e0d', bgColor: '#f6ffed', useCount: 28 },
  { key: 'content', name: '内容分享', description: '发送教育内容给学员', icon: '📤', color: '#1890ff', bgColor: '#e6f7ff', useCount: 22 },
  { key: 'assessment', name: '安排测评', description: '为学员安排问卷评估', icon: '📝', color: '#d46b08', bgColor: '#fff7e6', useCount: 15 },
  { key: 'report', name: '学员报告', description: '生成学员干预报告', icon: '📊', color: '#13c2c2', bgColor: '#e6fffb', useCount: 10 },
])

const recentUsage = ref([
  { id: 1, icon: '📋', toolName: '压力快速测评', student: '张伟', action: '完成评估，得分 32/80', time: '2小时前' },
  { id: 2, icon: '💜', toolName: '同理心倾听', student: '王芳', action: '倾听模式 15分钟', time: '4小时前' },
  { id: 3, icon: '🎯', toolName: '习惯处方卡', student: '赵强', action: '生成"每日散步5分钟"处方', time: '昨天' },
  { id: 4, icon: '📤', toolName: '内容分享', student: '李娜', action: '分享《压力管理入门》', time: '昨天' },
  { id: 5, icon: '📋', toolName: '压力快速测评', student: '陈静', action: '完成评估，得分 18/80', time: '2天前' },
])

const totalMonthUsage = computed(() => tools.value.reduce((s, t) => s + t.useCount, 0))
const mostUsedTool = computed(() => {
  const max = tools.value.reduce((a, b) => a.useCount > b.useCount ? a : b)
  return max.name
})
const effectiveRate = ref(78)
const maxUseCount = computed(() => Math.max(...tools.value.map(t => t.useCount), 1))

const useTool = (tool) => {
  message.info(`正在打开 ${tool.name}...`)
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.tools-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.tool-card { display: flex; align-items: center; gap: 12px; padding: 16px; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; cursor: pointer; border-left: 3px solid; transition: box-shadow 0.2s; }
.tool-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.tool-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.tool-info { flex: 1; }
.tool-name { display: block; font-size: 14px; font-weight: 600; color: #333; }
.tool-desc { font-size: 12px; color: #999; }
.tool-stats { text-align: center; }
.stat-num { display: block; font-size: 18px; font-weight: 700; color: #333; }
.stat-label { font-size: 11px; color: #999; }

.usage-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.usage-icon { font-size: 20px; }
.usage-info { flex: 1; }
.usage-name { display: block; font-size: 13px; font-weight: 500; }
.usage-context { font-size: 12px; color: #999; }
.usage-time { font-size: 12px; color: #bbb; }

.chart-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.chart-label { min-width: 100px; font-size: 13px; color: #333; }
.chart-bar-bg { flex: 1; height: 16px; background: #f5f5f5; border-radius: 4px; overflow: hidden; }
.chart-bar { height: 100%; border-radius: 4px; transition: width 0.3s; }
.chart-count { min-width: 30px; text-align: right; font-size: 13px; color: #999; }
</style>
