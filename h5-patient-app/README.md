# 行为健康平台 - 患者端H5应用

> Vue 3 + TypeScript + Vant UI + Vite

---

## 项目结构

```
h5-patient-app/
├── public/
│   └── index.html
├── src/
│   ├── main.ts                 # 应用入口
│   ├── App.vue                 # 根组件
│   ├── router/
│   │   └── index.ts            # 路由配置
│   ├── stores/
│   │   ├── user.ts             # 用户状态管理
│   │   └── assessment.ts       # 评估状态管理
│   ├── api/
│   │   ├── auth.ts             # 认证API
│   │   ├── assessment.ts       # 评估API
│   │   └── data.ts             # 数据上传API
│   ├── views/
│   │   ├── LoginPage.vue       # 登录页
│   │   ├── RegisterPage.vue    # 注册页
│   │   ├── HomePage.vue        # 首页/仪表盘
│   │   ├── DataInputPage.vue   # 数据录入页
│   │   └── ResultPage.vue      # 评估结果页
│   ├── components/
│   │   ├── DataInputForm.vue   # 数据输入表单
│   │   ├── RiskCard.vue        # 风险卡片
│   │   └── TriggerList.vue     # Trigger列表
│   └── types/
│       └── index.ts            # TypeScript类型定义
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

---

## 核心页面

### 1. LoginPage.vue - 登录页

**功能：**
- 用户名/邮箱 + 密码登录
- 记住登录状态
- 跳转到注册页

**API调用：**
```typescript
POST /auth/login
{
  "username": "patient_alice",
  "password": "password123"
}
```

### 2. RegisterPage.vue - 注册页

**功能：**
- 注册新用户
- 表单验证（用户名、邮箱、密码）
- 自动登录

**API调用：**
```typescript
POST /auth/register
{
  "username": "new_user",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "张三"
}
```

### 3. HomePage.vue - 首页

**功能：**
- 显示用户基本信息
- 最近评估历史
- 快速数据录入入口
- 今日健康指标卡片

**组件：**
- UserInfoCard
- RecentAssessments
- QuickActions

### 4. DataInputPage.vue - 数据录入

**功能：**
- 文本输入（心情日记）
- 血糖值输入（多个数据点）
- HRV值输入
- 活动/睡眠数据
- 提交评估

**表单结构：**
```typescript
interface AssessmentInput {
  text_content: string;
  glucose_values?: number[];
  hrv_values?: number[];
  activity_data?: {
    steps: number;
    distance?: number;
  };
  sleep_data?: {
    duration: number;
    quality: number;
  };
}
```

**API调用：**
```typescript
POST /api/assessment/submit
{
  "user_id": 1,
  "text_content": "今天感觉压力很大...",
  "glucose_values": [6.5, 11.2, 13.5],
  "hrv_values": [58, 62, 55]
}
```

### 5. ResultPage.vue - 评估结果

**功能：**
- 显示风险等级（R0-R4）
- 识别的Triggers列表
- 路由的Agent建议
- 推荐行动步骤
- 历史趋势图表

**数据结构：**
```typescript
interface AssessmentResult {
  assessment_id: string;
  risk_level: string;
  risk_score: number;
  triggers: Trigger[];
  routing_decision: {
    primary_agent: string;
    secondary_agents: string[];
    recommended_actions: string[];
  };
  timestamp: string;
}
```

---

## 状态管理（Pinia）

### user.ts - 用户Store

```typescript
export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token'),
    isLoggedIn: false
  }),
  actions: {
    async login(username, password) {
      // 调用登录API
      // 保存token
      // 更新状态
    },
    async register(data) {
      // 调用注册API
    },
    logout() {
      // 清除token和用户信息
    }
  }
})
```

### assessment.ts - 评估Store

```typescript
export const useAssessmentStore = defineStore('assessment', {
  state: () => ({
    currentAssessment: null,
    history: [],
    loading: false
  }),
  actions: {
    async submitAssessment(data) {
      // 提交评估数据
      // 获取结果
    },
    async fetchHistory() {
      // 获取历史评估
    }
  }
})
```

---

## API封装

### api/auth.ts

```typescript
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

export const authAPI = {
  login: (data) => axios.post(`${API_BASE}/auth/login`, data),
  register: (data) => axios.post(`${API_BASE}/auth/register`, data),
  getCurrentUser: () => axios.get(`${API_BASE}/auth/me`)
}
```

### api/assessment.ts

```typescript
export const assessmentAPI = {
  submit: (data) => axios.post(`${API_BASE}/api/assessment/submit`, data),
  getResult: (id) => axios.get(`${API_BASE}/api/assessment/${id}`),
  getHistory: (userId) => axios.get(`${API_BASE}/api/assessment/history/${userId}`)
}
```

---

## 路由配置

```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginPage.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterPage.vue')
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomePage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/data-input',
    name: 'DataInput',
    component: () => import('../views/DataInputPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/result/:id',
    name: 'Result',
    component: () => import('../views/ResultPage.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const isLoggedIn = localStorage.getItem('token')

  if (requiresAuth && !isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

---

## 开发步骤

### 1. 安装依赖

```bash
cd h5-patient-app
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

---

## Vant UI组件使用

```vue
<template>
  <van-form @submit="onSubmit">
    <van-cell-group inset>
      <van-field
        v-model="username"
        name="用户名"
        label="用户名"
        placeholder="请输入用户名"
        :rules="[{ required: true, message: '请填写用户名' }]"
      />
      <van-field
        v-model="password"
        type="password"
        name="密码"
        label="密码"
        placeholder="请输入密码"
        :rules="[{ required: true, message: '请填写密码' }]"
      />
    </van-cell-group>
    <div style="margin: 16px;">
      <van-button round block type="primary" native-type="submit">
        登录
      </van-button>
    </div>
  </van-form>
</template>
```

---

## 环境变量

创建 `.env` 文件：

```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=行为健康平台
```

---

## TypeScript类型定义

```typescript
// src/types/index.ts

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  full_name?: string;
}

export interface AssessmentInput {
  text_content?: string;
  glucose_values?: number[];
  hrv_values?: number[];
}

export interface Trigger {
  tag_id: string;
  name: string;
  category: string;
  severity: string;
  confidence: number;
}

export interface AssessmentResult {
  assessment_id: string;
  user_id: number;
  risk_level: string;
  risk_score: number;
  triggers: Trigger[];
  routing_decision: {
    primary_agent: string;
    secondary_agents: string[];
    recommended_actions: string[];
  };
  timestamp: string;
}
```

---

## 下一步开发

1. **完成核心页面组件**
   - LoginPage.vue
   - DataInputPage.vue
   - ResultPage.vue

2. **实现状态管理**
   - user store
   - assessment store

3. **API集成**
   - 认证流程
   - 评估提交
   - 结果展示

4. **UI优化**
   - 响应式设计
   - 加载状态
   - 错误处理

5. **测试**
   - 单元测试
   - E2E测试

---

## 启动命令

```bash
# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev

# 3. 在浏览器访问
http://localhost:5173
```

---

**注意：** 本框架已创建基础结构，具体页面组件需要进一步实现。参考上述API和数据结构进行开发。
