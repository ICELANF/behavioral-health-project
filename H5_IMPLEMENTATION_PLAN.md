# H5患者应用实施计划

> 规划时间：2026-01-28
> 预计工期：2-3天
> 当前进度：30% → 目标：100%

---

## 📊 当前状态分析

### ✅ 已完成（30%）

**后端基础设施（100%）：**
- ✅ 数据库系统（6表+种子数据）
- ✅ 认证系统（JWT + bcrypt）
- ✅ API后端（FastAPI + 认证端点）
- ✅ L2评估引擎（9.31ms响应）
- ✅ CLI工具（db/status/serve/test）

**H5前端框架（30%）：**
- ✅ `package.json` - 依赖配置
- ✅ `README.md` - 开发文档
- ✅ `src/` 目录结构
  - ✅ api/
  - ✅ components/
  - ✅ views/
  - ✅ types/
  - ✅ utils/

### ⚠️ 待实现（70%）

**核心文件缺失：**
- ❌ `vite.config.ts` - Vite配置
- ❌ `tsconfig.json` - TypeScript配置
- ❌ `index.html` - HTML入口
- ❌ `src/main.ts` - 应用入口
- ❌ `src/App.vue` - 根组件
- ❌ `src/router/` - 路由配置
- ❌ `src/stores/` - Pinia状态管理

**页面组件缺失：**
- ❌ `src/views/LoginPage.vue` - 登录页
- ❌ `src/views/RegisterPage.vue` - 注册页
- ❌ `src/views/HomePage.vue` - 首页
- ❌ `src/views/DataInputPage.vue` - 数据录入
- ❌ `src/views/ResultPage.vue` - 评估结果

**API集成缺失：**
- ❌ `src/api/request.ts` - Axios封装
- ❌ `src/api/auth.ts` - 认证API
- ❌ `src/api/assessment.ts` - 评估API

---

## 🎯 实施目标

### 第一阶段：基础框架搭建（Day 1上午）

**目标：** 让应用能够启动并显示登录页

**任务清单：**
1. ✅ 安装依赖：`npm install`
2. 📝 创建配置文件：
   - `vite.config.ts`
   - `tsconfig.json`
   - `index.html`
   - `.env`
3. 📝 创建应用入口：
   - `src/main.ts`
   - `src/App.vue`
4. 📝 配置路由：
   - `src/router/index.ts`
5. 📝 创建登录页：
   - `src/views/LoginPage.vue`

**验证标准：**
```bash
npm run dev
# 浏览器访问 http://localhost:5173
# 应该能看到登录页面
```

---

### 第二阶段：认证功能实现（Day 1下午）

**目标：** 完成用户登录、注册和状态管理

**任务清单：**
1. 📝 封装HTTP请求：
   - `src/api/request.ts`（Axios配置、拦截器）
2. 📝 实现认证API：
   - `src/api/auth.ts`（login、register、me）
3. 📝 创建用户Store：
   - `src/stores/user.ts`（Pinia）
4. 📝 创建注册页：
   - `src/views/RegisterPage.vue`
5. 📝 完善登录页：
   - 表单验证
   - 错误处理
   - 加载状态
   - Token存储

**验证标准：**
```bash
# 1. 注册新用户
# 2. 登录成功后跳转首页
# 3. 刷新页面仍保持登录状态
# 4. Token自动添加到请求头
```

---

### 第三阶段：首页和数据录入（Day 2）

**目标：** 实现首页仪表盘和数据录入功能

**任务清单：**
1. 📝 创建首页：
   - `src/views/HomePage.vue`
   - 用户信息卡片
   - 最近评估列表
   - 快捷操作按钮
2. 📝 创建数据录入页：
   - `src/views/DataInputPage.vue`
   - 文本输入（心情日记）
   - 血糖值输入（多个数据点）
   - HRV值输入
   - 活动/睡眠数据
3. 📝 实现评估API：
   - `src/api/assessment.ts`（submit、getResult、getHistory）
4. 📝 创建评估Store：
   - `src/stores/assessment.ts`
5. 📝 创建通用组件：
   - `src/components/DataInputForm.vue`

**验证标准：**
```bash
# 1. 登录后进入首页
# 2. 查看历史评估记录
# 3. 点击"数据录入"
# 4. 填写表单并提交
# 5. 提交成功后跳转到结果页
```

---

### 第四阶段：评估结果展示（Day 3上午）

**目标：** 展示评估结果和干预建议

**任务清单：**
1. 📝 创建结果页：
   - `src/views/ResultPage.vue`
   - 风险等级展示（R0-R4）
   - Trigger列表
   - Agent建议
   - 推荐行动
2. 📝 创建结果组件：
   - `src/components/RiskCard.vue`
   - `src/components/TriggerList.vue`
3. 📝 创建TypeScript类型：
   - `src/types/index.ts`

**验证标准：**
```bash
# 1. 提交评估后自动跳转结果页
# 2. 显示完整的评估结果
# 3. 风险等级用颜色区分
# 4. Trigger列表展示清晰
# 5. 可以查看历史评估结果
```

---

### 第五阶段：优化和完善（Day 3下午）

**目标：** 优化用户体验和错误处理

**任务清单：**
1. 📝 路由守卫：
   - 未登录重定向到登录页
   - 登录后重定向到首页
2. 📝 错误处理：
   - API错误统一处理
   - Toast提示
   - 网络错误重试
3. 📝 加载状态：
   - Loading组件
   - 骨架屏
4. 📝 响应式优化：
   - 移动端适配
   - 触摸友好
5. 📝 本地存储：
   - Token持久化
   - 用户信息缓存

**验证标准：**
```bash
# 1. 网络错误有友好提示
# 2. 加载时显示loading
# 3. 表单验证完整
# 4. 移动端显示正常
# 5. 刷新页面不丢失状态
```

---

## 📁 文件清单（需创建）

### 配置文件（5个）
```
h5-patient-app/
├── vite.config.ts          # Vite配置
├── tsconfig.json           # TypeScript配置
├── index.html              # HTML入口
├── .env                    # 环境变量
└── .env.development        # 开发环境变量
```

### 核心文件（3个）
```
src/
├── main.ts                 # 应用入口（Vue实例创建）
├── App.vue                 # 根组件（router-view）
└── style.css               # 全局样式
```

### 路由文件（1个）
```
src/router/
└── index.ts                # 路由配置（5个路由）
```

### 状态管理（2个）
```
src/stores/
├── user.ts                 # 用户Store（登录状态、用户信息）
└── assessment.ts           # 评估Store（当前评估、历史记录）
```

### API封装（3个）
```
src/api/
├── request.ts              # Axios配置、拦截器
├── auth.ts                 # 认证API（login、register、me）
└── assessment.ts           # 评估API（submit、getResult、getHistory）
```

### 页面组件（5个）
```
src/views/
├── LoginPage.vue           # 登录页（表单+验证）
├── RegisterPage.vue        # 注册页（表单+验证）
├── HomePage.vue            # 首页（仪表盘+快捷操作）
├── DataInputPage.vue       # 数据录入（文本+血糖+HRV）
└── ResultPage.vue          # 评估结果（风险+Trigger+建议）
```

### 通用组件（3个）
```
src/components/
├── DataInputForm.vue       # 数据输入表单
├── RiskCard.vue            # 风险卡片
└── TriggerList.vue         # Trigger列表
```

### 类型定义（1个）
```
src/types/
└── index.ts                # TypeScript类型定义
```

### 工具函数（1个）
```
src/utils/
└── storage.ts              # 本地存储封装
```

**总计：24个文件**

---

## 🛠️ 技术栈详情

### 核心框架
- **Vue 3.5** - Composition API + `<script setup>`
- **TypeScript 5.6** - 类型安全
- **Vite 6.0** - 快速开发服务器

### UI组件库
- **Vant UI 4.9** - 移动端组件
  - Form（表单）
  - Field（输入框）
  - Button（按钮）
  - Cell（单元格）
  - Card（卡片）
  - Toast（轻提示）
  - Loading（加载）
  - NavBar（导航栏）

### 状态管理
- **Pinia 3.0** - Vue官方推荐
  - 简单直观
  - TypeScript支持良好
  - DevTools集成

### 路由
- **Vue Router 4.4** - SPA路由
  - 路由守卫
  - 懒加载
  - 动态路由

### HTTP客户端
- **Axios 1.7** - Promise based
  - 请求拦截器（添加Token）
  - 响应拦截器（错误处理）
  - 请求取消

---

## 🔗 API集成设计

### 后端API基础URL
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
```

### 认证流程
```typescript
// 1. 用户登录
POST /auth/login
Request: { username, password }
Response: { access_token, refresh_token, user }

// 2. 保存Token
localStorage.setItem('access_token', token)

// 3. 请求拦截器自动添加Token
config.headers.Authorization = `Bearer ${token}`

// 4. 访问受保护端点
GET /auth/me
Headers: { Authorization: Bearer <token> }
Response: { id, username, email, role, ... }
```

### 评估流程
```typescript
// 1. 提交评估数据
POST /api/assessment/submit
Request: {
  user_id: number,
  text_content: string,
  glucose_values?: number[],
  hrv_values?: number[]
}
Response: {
  assessment_id: string,
  risk_level: string,
  risk_score: number,
  triggers: Trigger[],
  routing_decision: {...}
}

// 2. 查看评估结果
GET /api/assessment/{id}
Response: { ...完整评估结果 }

// 3. 查看历史记录
GET /api/assessment/history/{user_id}
Response: Assessment[]
```

---

## 📱 页面设计规范

### 登录页（LoginPage.vue）
```vue
<template>
  <div class="login-page">
    <van-nav-bar title="用户登录" />

    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="username"
          name="username"
          label="用户名"
          placeholder="请输入用户名或邮箱"
          :rules="[{ required: true, message: '请填写用户名' }]"
        />
        <van-field
          v-model="password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请填写密码' }]"
        />
      </van-cell-group>

      <div class="button-group">
        <van-button round block type="primary" native-type="submit">
          登录
        </van-button>
        <van-button round block plain type="primary" @click="goToRegister">
          注册账号
        </van-button>
      </div>
    </van-form>
  </div>
</template>
```

### 首页（HomePage.vue）
```vue
<template>
  <div class="home-page">
    <van-nav-bar title="行为健康" right-text="退出" @click-right="logout" />

    <!-- 用户信息卡片 -->
    <van-card
      :title="userStore.user?.full_name"
      :desc="`用户ID: ${userStore.user?.id}`"
      :thumb="avatarUrl"
    />

    <!-- 快捷操作 -->
    <van-grid :column-num="2">
      <van-grid-item icon="edit" text="数据录入" @click="goToDataInput" />
      <van-grid-item icon="bar-chart-o" text="历史记录" @click="goToHistory" />
    </van-grid>

    <!-- 最近评估 -->
    <van-cell-group title="最近评估">
      <van-cell v-for="item in recentAssessments" :key="item.id"
        :title="item.timestamp"
        :label="`风险等级: ${item.risk_level}`"
        is-link
        @click="goToResult(item.id)"
      />
    </van-cell-group>
  </div>
</template>
```

### 数据录入页（DataInputPage.vue）
```vue
<template>
  <div class="data-input-page">
    <van-nav-bar title="数据录入" left-arrow @click-left="goBack" />

    <van-form @submit="onSubmit">
      <!-- 心情日记 -->
      <van-cell-group title="心情日记">
        <van-field
          v-model="formData.text_content"
          rows="4"
          type="textarea"
          placeholder="记录今天的心情..."
        />
      </van-cell-group>

      <!-- 血糖值 -->
      <van-cell-group title="血糖值 (mmol/L)">
        <van-field
          v-for="(value, index) in formData.glucose_values"
          :key="index"
          v-model.number="formData.glucose_values[index]"
          type="number"
          :label="`测量${index + 1}`"
        />
        <van-button size="small" @click="addGlucose">添加测量</van-button>
      </van-cell-group>

      <!-- 提交按钮 -->
      <van-button round block type="primary" native-type="submit" :loading="loading">
        提交评估
      </van-button>
    </van-form>
  </div>
</template>
```

---

## 🧪 测试计划

### 手动测试清单

**认证流程：**
- [ ] 注册新用户成功
- [ ] 用户名重复提示错误
- [ ] 登录成功并跳转首页
- [ ] 用户名或密码错误提示
- [ ] 登出成功并清除Token
- [ ] 刷新页面保持登录状态

**数据录入：**
- [ ] 文本输入正常
- [ ] 血糖值输入验证
- [ ] HRV值输入验证
- [ ] 提交成功跳转结果页
- [ ] 网络错误友好提示

**结果展示：**
- [ ] 风险等级显示正确
- [ ] Trigger列表完整
- [ ] 建议内容清晰
- [ ] 历史记录可查看

**异常处理：**
- [ ] Token过期自动跳转登录
- [ ] 网络错误提示
- [ ] 表单验证提示
- [ ] 加载状态显示

---

## 📦 依赖安装

### 需要安装的包（已在package.json中）

```bash
cd h5-patient-app
npm install
```

**主要依赖：**
```json
{
  "vue": "^3.5.0",
  "vue-router": "^4.4.0",
  "pinia": "^3.0.0",
  "axios": "^1.7.0",
  "vant": "^4.9.0"
}
```

**开发依赖：**
```json
{
  "@vitejs/plugin-vue": "^5.0.0",
  "typescript": "^5.6.0",
  "vite": "^6.0.0",
  "vue-tsc": "^2.1.0",
  "unplugin-vue-components": "^0.27.0"
}
```

---

## 🚀 启动流程

### 开发环境启动

```bash
# 1. 进入H5目录
cd h5-patient-app

# 2. 安装依赖（首次）
npm install

# 3. 启动开发服务器
npm run dev

# 4. 浏览器访问
http://localhost:5173
```

### 后端API启动

```bash
# 在另一个终端

# 1. 确保数据库已初始化
python __main__.py db init --sample-data

# 2. 启动API服务器
python __main__.py serve --reload
```

### 完整测试流程

```bash
# Terminal 1: 启动后端API
python __main__.py serve

# Terminal 2: 启动前端开发服务器
cd h5-patient-app && npm run dev

# Browser:
# 1. 访问 http://localhost:5173
# 2. 注册新用户或使用测试账号登录
# 3. 提交评估数据
# 4. 查看评估结果
```

---

## 📝 开发规范

### Vue组件规范

```vue
<script setup lang="ts">
// 1. 导入（按顺序：Vue API → 第三方库 → 本地模块）
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 2. Props和Emits
interface Props {
  title: string
}
const props = defineProps<Props>()
const emit = defineEmits<{
  submit: [data: FormData]
}>()

// 3. Composables（Pinia stores, router, etc.）
const router = useRouter()
const userStore = useUserStore()

// 4. 响应式数据
const loading = ref(false)
const formData = ref<FormData>({})

// 5. 计算属性
const isValid = computed(() => !!formData.value.username)

// 6. 方法
const onSubmit = async () => {
  loading.value = true
  // ...
}

// 7. 生命周期
onMounted(() => {
  // ...
})
</script>

<template>
  <!-- 模板内容 -->
</template>

<style scoped>
/* 组件样式 */
</style>
```

### API调用规范

```typescript
// src/api/auth.ts
import request from './request'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user: User
}

export const authAPI = {
  // 登录
  login(data: LoginRequest) {
    return request.post<LoginResponse>('/auth/login', data)
  },

  // 注册
  register(data: RegisterRequest) {
    return request.post<TokenResponse>('/auth/register', data)
  },

  // 获取当前用户
  getCurrentUser() {
    return request.get<User>('/auth/me')
  }
}
```

### Pinia Store规范

```typescript
// src/stores/user.ts
import { defineStore } from 'pinia'
import { authAPI } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))

  // Getters
  const isLoggedIn = computed(() => !!token.value)

  // Actions
  const login = async (username: string, password: string) => {
    const res = await authAPI.login({ username, password })
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('access_token', res.access_token)
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
  }

  return { user, token, isLoggedIn, login, logout }
})
```

---

## 🎯 成功标准

### 功能完整性
- [x] 用户可以注册新账号
- [x] 用户可以登录系统
- [x] 登录后可以查看首页
- [x] 可以提交评估数据（文本+血糖+HRV）
- [x] 提交后可以查看评估结果
- [x] 可以查看历史评估记录
- [x] 可以安全登出

### 用户体验
- [x] 页面加载速度快（<1秒）
- [x] 表单验证友好
- [x] 错误提示清晰
- [x] 加载状态明确
- [x] 移动端显示正常

### 代码质量
- [x] TypeScript类型完整
- [x] 组件结构清晰
- [x] API调用统一封装
- [x] 错误处理完善
- [x] 代码注释充分

---

## 📅 时间估算

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|----------|--------|
| **Day 1上午** | 基础框架搭建 | 2-3小时 | P0 |
| **Day 1下午** | 认证功能实现 | 3-4小时 | P0 |
| **Day 2上午** | 首页和数据录入 | 3-4小时 | P0 |
| **Day 2下午** | 评估结果展示 | 2-3小时 | P0 |
| **Day 3上午** | 优化和完善 | 2-3小时 | P1 |
| **Day 3下午** | 测试和修复 | 2-3小时 | P1 |
| **总计** | | **14-20小时** | |

---

## 🎬 执行建议

### 分步执行（推荐）

**如果选择分步实施，建议按以下顺序：**

1. **先完成第一阶段**（基础框架）
   - 确保应用能够启动
   - 看到登录页面
   - 验证后再继续

2. **再完成第二阶段**（认证功能）
   - 完成登录注册流程
   - 测试Token管理
   - 验证后再继续

3. **然后完成第三阶段**（数据录入）
   - 实现首页和录入页
   - 测试数据提交
   - 验证后再继续

4. **最后完成剩余阶段**（结果展示+优化）

### 一次性执行（快速）

**如果选择一次性完成所有代码：**
- 我可以连续创建所有24个文件
- 预计30-40分钟完成所有代码编写
- 然后你进行测试和调试

---

## ❓ 准备开始？

**请选择实施方式：**

1. **🚀 立即开始** - 我现在就开始创建H5应用的所有文件
2. **📋 分步实施** - 先完成第一阶段（基础框架），验证后再继续
3. **🔍 详细讨论** - 先讨论某些技术细节或设计方案
4. **⏸️ 暂时不做** - 先完成其他工作

请告诉我你的选择，我会立即开始执行！💪
