<template>
  <div class="react-nav-container">
    <div class="nav-header">
      <h1>🎯 React集成页面导航</h1>
      <p>以下是已集成的React功能页面</p>
    </div>

    <div class="nav-grid">
      <router-link
        v-for="route in reactPages"
        :key="route.path"
        :to="route.path"
        class="nav-card"
      >
        <div class="card-icon">{{ route.icon }}</div>
        <div class="card-content">
          <h3>{{ route.title }}</h3>
          <p>{{ route.description }}</p>
          <div class="card-badge" :class="route.role">
            {{ route.role ? route.roleText : '公开访问' }}
          </div>
        </div>
        <div class="card-arrow">→</div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
const reactPages = [
  {
    path: '/react/demo',
    icon: '🔬',
    title: 'React演示页',
    description: '展示React组件集成效果，包含逻辑流、决策规则等演示',
    role: null,
    roleText: ''
  },
  {
    path: '/journey',
    icon: '🌱',
    title: '成长之旅',
    description: '用户行为改变成长历程可视化，展示健康管理进展',
    role: null,
    roleText: ''
  },
  {
    path: '/trace',
    icon: '🔍',
    title: '决策追踪',
    description: '查看AI决策过程、逻辑链路和规则执行详情',
    role: 'protected',
    roleText: '需要登录'
  },
  {
    path: '/expert/workspace',
    icon: '👨‍🔬',
    title: '专家工作区',
    description: '专家专用工作台，包含审核、督导等功能',
    role: 'expert',
    roleText: '专家专用'
  },
  {
    path: '/admin/evolution',
    icon: '📊',
    title: '系统演进',
    description: '查看系统架构演进和技术栈变化历程',
    role: 'admin',
    roleText: '管理员专用'
  }
]
</script>

<style scoped>
.react-nav-container {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 64px);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.nav-header {
  text-align: center;
  color: white;
  margin-bottom: 40px;
}

.nav-header h1 {
  font-size: 36px;
  margin-bottom: 12px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.nav-header p {
  font-size: 16px;
  opacity: 0.9;
}

.nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.nav-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  position: relative;
  overflow: hidden;
}

.nav-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.nav-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.card-icon {
  font-size: 48px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
}

.card-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.card-content p {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 12px;
}

.card-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: #f3f4f6;
  color: #4b5563;
}

.card-badge.protected {
  background: #fef3c7;
  color: #d97706;
}

.card-badge.expert {
  background: #f3e8ff;
  color: #9333ea;
}

.card-badge.admin {
  background: #fee2e2;
  color: #dc2626;
}

.card-arrow {
  font-size: 24px;
  color: #667eea;
  flex-shrink: 0;
  transition: transform 0.3s;
}

.nav-card:hover .card-arrow {
  transform: translateX(4px);
}
</style>
