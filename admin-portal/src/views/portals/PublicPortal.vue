<template>
  <div class="public-portal">
    <!-- 顶部区域 -->
    <div class="header-section">
      <div class="header-content">
        <div class="header-title">行为健康科普入口</div>
        <div class="header-subtitle">了解行为健康知识，开启健康生活方式</div>
      </div>
    </div>

    <div class="main-content">
      <!-- 搜索栏 -->
      <div class="section-card search-card">
        <a-input-search
          v-model:value="searchQuery"
          placeholder="搜索健康知识、常见问题..."
          size="large"
          @search="onSearch"
        />
      </div>

      <!-- 健康科普分类 -->
      <div class="section-card">
        <div class="card-header">
          <span class="card-title">科普分类</span>
        </div>
        <div class="category-grid">
          <div
            v-for="cat in categories"
            :key="cat.key"
            class="category-item"
            @click="selectCategory(cat.key)"
          >
            <div class="category-icon" :style="{ background: cat.bg }">{{ cat.icon }}</div>
            <div class="category-name">{{ cat.label }}</div>
          </div>
        </div>
      </div>

      <!-- 热门文章 -->
      <div class="section-card">
        <div class="card-header">
          <span class="card-title">热门科普</span>
          <a class="more-link">更多 ></a>
        </div>
        <div class="article-list">
          <div v-for="article in hotArticles" :key="article.id" class="article-item" @click="openArticle(article)">
            <div class="article-info">
              <div class="article-title">{{ article.title }}</div>
              <div class="article-meta">
                <span class="article-tag" :style="{ background: article.tagBg, color: article.tagColor }">{{ article.tag }}</span>
                <span class="article-views">{{ article.views }} 阅读</span>
              </div>
            </div>
            <div class="article-thumb" v-if="article.thumb">
              <img :src="article.thumb" :alt="article.title" />
            </div>
          </div>
        </div>
      </div>

      <!-- 自测工具 -->
      <div class="section-card">
        <div class="card-header">
          <span class="card-title">健康自测</span>
        </div>
        <div class="tool-grid">
          <div v-for="tool in selfTestTools" :key="tool.id" class="tool-card" @click="openTool(tool)">
            <div class="tool-icon">{{ tool.icon }}</div>
            <div class="tool-name">{{ tool.name }}</div>
            <div class="tool-desc">{{ tool.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 快速入口 -->
      <div class="section-card entry-card">
        <div class="entry-row" @click="router.push('/portal/medical')">
          <div class="entry-icon">🩺</div>
          <div class="entry-info">
            <div class="entry-title">基层医护处方助手</div>
            <div class="entry-desc">面向医护人员的行为处方开具工具</div>
          </div>
          <RightOutlined class="entry-arrow" />
        </div>
        <div class="entry-row" @click="router.push('/client')">
          <div class="entry-icon">📱</div>
          <div class="entry-info">
            <div class="entry-title">患者健康管理</div>
            <div class="entry-desc">登录后查看个人健康数据与任务</div>
          </div>
          <RightOutlined class="entry-arrow" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { RightOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const router = useRouter()
const searchQuery = ref('')

const categories = [
  { key: 'glucose', icon: '🩸', label: '血糖管理', bg: '#fef2f2' },
  { key: 'diet', icon: '🥗', label: '饮食营养', bg: '#f0fdf4' },
  { key: 'exercise', icon: '🏃', label: '运动康复', bg: '#eff6ff' },
  { key: 'mental', icon: '🧘', label: '心理健康', bg: '#fdf4ff' },
  { key: 'medication', icon: '💊', label: '用药指导', bg: '#faf5ff' },
  { key: 'sleep', icon: '😴', label: '睡眠管理', bg: '#ecfeff' },
  { key: 'weight', icon: '⚖️', label: '体重控制', bg: '#fffbeb' },
  { key: 'prevention', icon: '🛡️', label: '并发症预防', bg: '#f0f5ff' },
]

const hotArticles = ref([
  { id: 1, title: '2型糖尿病患者的每日运动指南：30分钟改变健康轨迹', tag: '运动', tagBg: '#dcfce7', tagColor: '#16a34a', views: '3.2万', thumb: '' },
  { id: 2, title: '低GI饮食全攻略：哪些食物可以放心吃？', tag: '饮食', tagBg: '#fef3c7', tagColor: '#d97706', views: '2.8万', thumb: '' },
  { id: 3, title: '行为改变五阶段模型：从犹豫到坚持的科学路径', tag: '心理', tagBg: '#e0e7ff', tagColor: '#4f46e5', views: '1.5万', thumb: '' },
  { id: 4, title: '血糖监测时间点解读：餐前餐后到底差多少？', tag: '血糖', tagBg: '#fee2e2', tagColor: '#dc2626', views: '4.1万', thumb: '' },
])

const selfTestTools = ref([
  { id: 1, icon: '📋', name: 'PHQ-9 抑郁筛查', desc: '9题快速评估' },
  { id: 2, icon: '📊', name: 'GAD-7 焦虑评估', desc: '7题焦虑自测' },
  { id: 3, icon: '🩸', name: '糖尿病风险评估', desc: '多维度风险筛查' },
  { id: 4, icon: '🏃', name: '运动能力测评', desc: '运动处方参考' },
])

const onSearch = (value: string) => {
  message.info(`搜索: ${value}`)
}

const selectCategory = (key: string) => {
  message.info(`进入分类: ${key}`)
}

const openArticle = (article: { title: string }) => {
  message.info(`打开文章: ${article.title}`)
}

const openTool = (tool: { name: string }) => {
  message.info(`打开工具: ${tool.name}`)
}
</script>

<style scoped>
.public-portal {
  min-height: 100vh;
  background: #f5f7fa;
}

.header-section {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  padding: 40px 16px 50px;
  border-radius: 0 0 24px 24px;
}

.header-content {
  max-width: 500px;
  margin: 0 auto;
  text-align: center;
}

.header-title {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
}

.header-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
}

.main-content {
  max-width: 500px;
  margin: -30px auto 0;
  padding: 0 16px 32px;
  position: relative;
  z-index: 10;
}

.section-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.more-link {
  color: #10b981;
  font-size: 13px;
  cursor: pointer;
}

/* 分类 */
.category-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: transform 0.2s;
}

.category-item:hover {
  transform: translateY(-2px);
}

.category-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.category-name {
  font-size: 12px;
  color: #4b5563;
  font-weight: 500;
}

/* 文章列表 */
.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.article-item:hover {
  background: #f3f4f6;
}

.article-info {
  flex: 1;
  min-width: 0;
}

.article-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.5;
  margin-bottom: 8px;
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.article-tag {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}

.article-views {
  font-size: 11px;
  color: #9ca3af;
}

.article-thumb {
  flex-shrink: 0;
  width: 80px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  background: #e5e7eb;
}

.article-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 自测工具 */
.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.tool-card {
  padding: 14px;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-card:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
}

.tool-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.tool-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 12px;
  color: #6b7280;
}

/* 入口 */
.entry-card {
  padding: 0;
  overflow: hidden;
}

.entry-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.entry-row:hover {
  background: #f9fafb;
}

.entry-row + .entry-row {
  border-top: 1px solid #f3f4f6;
}

.entry-icon {
  font-size: 28px;
}

.entry-info {
  flex: 1;
}

.entry-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.entry-desc {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.entry-arrow {
  color: #d1d5db;
  font-size: 12px;
}
</style>
