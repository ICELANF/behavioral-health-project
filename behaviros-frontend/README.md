# BehaviorOS V4.0 — 前端工程

## 快速启动

```bash
npm install
npm run dev
```

开发服务器启动后访问 `http://localhost:5173`，API请求自动代理到 `http://localhost:8000`（后端）。

## 目录结构

```
src/
├── api/                    # HTTP客户端 + API模块
│   ├── http.ts             # axios实例，JWT拦截器，错误处理
│   ├── auth.ts             # 认证API (6端点)
│   └── index.ts            # 业务API集合 (旅程/评估/Agent/微行动/挑战/积分/学习/内容/设备)
├── components/
│   ├── common/             # 全局通用组件
│   └── layout/
│       └── AppLayout.vue   # 主布局 (侧边栏+顶栏+内容区，角色动态菜单)
├── modules/                # 功能模块 (可独立开发)
│   ├── rx/                 # 行为处方模块 (已有完整实现)
│   │   ├── api/rxApi.ts    # 8个Rx端点
│   │   ├── components/     # 7个Vue组件 (BigFiveRadar/TTMProgressBar/...)
│   │   ├── composables/    # 组合逻辑 (轮询/构建器/格式化)
│   │   ├── router/         # 模块路由
│   │   ├── stores/         # Pinia Store
│   │   ├── types/          # TypeScript类型
│   │   └── views/          # RxDashboard.vue
│   ├── behavior/           # 行为行动 (ActionsView实现)
│   ├── assessment/         # 健康评估 (占位)
│   ├── agent/              # AI对话 (AgentChatView实现)
│   ├── coach/              # 教练端 (占位)
│   └── admin/              # 管理端 (占位)
├── router/
│   └── index.ts            # 主路由 (角色守卫+权限检查)
├── stores/
│   ├── auth.ts             # 认证Store (登录/注销/角色/权限)
│   └── app.ts              # 应用Store (侧边栏/主题/通知)
├── styles/
│   └── global.css          # Tailwind + 品牌变量 + AntD覆盖
├── types/
│   └── index.ts            # 全局类型 (镜像后端models)
├── App.vue                 # 根组件
└── main.ts                 # 入口 (Vue+Pinia+Router+AntD)
```

## 已实现页面

| 页面 | 路由 | 状态 | 对接API |
|------|------|------|--------|
| 登录 | /login | ✅ 完整 | POST /auth/login |
| 注册 | /register | ✅ 完整 | POST /auth/register |
| 首页仪表盘 | / | ✅ 完整 | journey/actions/challenges/points |
| AI对话 | /agent | ✅ 完整 | chat sessions + agent/run |
| 今日行动 | /actions | ✅ 完整 | micro-actions |
| 行为处方 | /rx/dashboard | ✅ 完整(已有模块) | 8个Rx端点 |
| 我的旅程 | /journey | 🚧 占位 | journey API |
| 健康评估 | /assessment | 🚧 占位 | assessment API |
| 挑战打卡 | /challenges | 🚧 占位 | challenge API |
| 学习成长 | /learning | 🚧 占位 | learning API |
| 健康数据 | /health-data | 🚧 占位 | device API |
| 我的积分 | /points | 🚧 占位 | credits API |
| 教练工作台 | /coach | 🚧 占位 | coach API |
| 管理后台 | /admin | 🚧 占位 | admin API |

## 角色权限

路由守卫自动根据用户角色控制页面访问：

| 角色 | 级别 | 可访问 |
|------|------|--------|
| observer | 0 | 基础页面 |
| grower | 1 | + 所有用户功能 |
| sharer | 2 | + 内容贡献 |
| coach | 3 | + 教练工作台 + 行为处方 |
| promoter | 4 | + 督导管理 |
| master | 5 | + 高阶功能 |
| admin | 6 | 全部页面 |

## 技术栈

- **Vue 3.4** + Composition API + `<script setup>`
- **TypeScript** 严格模式
- **Pinia** 状态管理
- **Vue Router 4** + 角色守卫
- **Ant Design Vue 4** UI组件库
- **Tailwind CSS 3** 工具类
- **axios** HTTP客户端 + JWT自动注入
- **Vite 5** 构建工具

## 新增模块开发指南

1. 在 `src/modules/` 下创建模块目录
2. 包含 `components/` `views/` `api/` (可选 `stores/` `composables/`)
3. 在 `src/router/index.ts` 中注册路由
4. 在 `AppLayout.vue` 的 `menuItems` 中添加菜单项
