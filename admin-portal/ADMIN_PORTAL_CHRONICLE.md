# 教练认证管理后台 · 开发纪事

> 最后更新: 2026-01-24
> 此文件用于记录管理后台开发进展，防止 AI 助手记忆遗忘

---

## 项目概述

**项目名称**: 教练认证管理后台 (Admin Portal)
**项目目录**: `D:\behavioral-health-project\admin-portal`
**技术栈**: Vue 3 + Vite + TypeScript + Ant Design Vue 4 + Pinia + Vue Router 4
**状态**: 开发中
**访问地址**: http://localhost:3000
**登录凭据**: admin / admin123

---

## 系统定位

```
┌─────────────────────────────────────────────────────────────┐
│                    教练认证平台架构                          │
├─────────────────────────────────────────────────────────────┤
│  管理后台 (admin-portal)  ←── 本项目                        │
│    ├── 课程管理 (视频+章节测验)                              │
│    ├── 题库管理                                              │
│    ├── 考试管理                                              │
│    ├── 直播管理                                              │
│    ├── 教练管理                                              │
│    └── 学员管理                                              │
├─────────────────────────────────────────────────────────────┤
│  后端服务 (metabolic-core)                                   │
│    ├── 认证体系 API (certification/)                        │
│    ├── 知识库 API (libraries/)                              │
│    └── 编排器 API (orchestrator/)                           │
├─────────────────────────────────────────────────────────────┤
│  第三方服务 (待接入)                                         │
│    ├── 阿里云 VOD (视频点播)                                │
│    ├── 阿里云 Live (直播)                                   │
│    ├── 阿里云 OSS (文件存储)                                │
│    └── 阿里云人脸核身 (考试防作弊)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
admin-portal/
├── src/
│   ├── main.ts                 # 入口文件 (Pinia + Router + Antd)
│   ├── App.vue                 # 根组件 (ConfigProvider 中文)
│   ├── router.ts               # 路由配置 (含权限守卫)
│   ├── style.css               # 全局样式
│   │
│   ├── layouts/
│   │   └── AdminLayout.vue     # 管理后台布局 (侧边栏+顶栏)
│   │
│   ├── views/
│   │   ├── Login.vue           # 登录页
│   │   ├── Settings.vue        # 系统设置 (占位)
│   │   │
│   │   ├── dashboard/
│   │   │   └── Index.vue       # 工作台仪表盘
│   │   │
│   │   ├── course/
│   │   │   ├── List.vue        # 课程列表 ✅
│   │   │   ├── Edit.vue        # 创建/编辑课程 ✅
│   │   │   └── Chapters.vue    # 章节管理 ✅ (核心功能)
│   │   │
│   │   ├── exam/
│   │   │   ├── QuestionBank.vue    # 题库列表 ✅
│   │   │   ├── QuestionEdit.vue    # 题目编辑 (基础)
│   │   │   ├── ExamList.vue        # 考试列表 (占位)
│   │   │   ├── ExamEdit.vue        # 考试编辑 (占位)
│   │   │   └── Results.vue         # 成绩管理 (占位)
│   │   │
│   │   ├── live/
│   │   │   ├── List.vue        # 直播列表 (占位)
│   │   │   └── Edit.vue        # 直播编辑 (占位)
│   │   │
│   │   └── coach/
│   │       ├── List.vue        # 教练列表 (占位)
│   │       ├── Detail.vue      # 教练详情 (占位)
│   │       ├── Review.vue      # 晋级审核 (占位)
│   │       └── StudentList.vue # 学员列表 (占位)
│   │
│   ├── api/                    # API 服务 (待开发)
│   ├── stores/                 # Pinia 状态管理 (待开发)
│   ├── components/             # 公共组件 (待开发)
│   └── utils/                  # 工具函数 (待开发)
│
├── package.json
├── vite.config.ts
├── tsconfig.json
└── ADMIN_PORTAL_CHRONICLE.md   # 本文件
```

---

## 已完成功能

### 1. 基础框架 ✅

- [x] Vue 3 + Vite 项目初始化
- [x] Ant Design Vue 4 集成
- [x] Vue Router 4 路由配置
- [x] Pinia 状态管理集成
- [x] 中文语言包配置

### 2. 布局系统 ✅

- [x] AdminLayout 管理后台布局
  - [x] 可折叠侧边栏菜单
  - [x] 顶部导航栏
  - [x] 面包屑导航
  - [x] 用户下拉菜单
- [x] 登录页面
  - [x] 表单验证
  - [x] Token 存储
  - [x] 路由守卫

### 3. 工作台仪表盘 ✅

- [x] 统计卡片 (学员/教练/课程/今日学习)
- [x] 认证等级分布图 (L0-L4)
- [x] 待处理事项列表
- [x] 最近考试表格
- [x] 晋级申请表格

### 4. 课程管理 ✅ (核心)

**课程列表 (List.vue)**
- [x] 课程表格展示
- [x] 多条件筛选 (等级/类别/状态/关键词)
- [x] 上架/下架操作
- [x] 删除确认
- [x] 跳转章节管理

**课程编辑 (Edit.vue)**
- [x] 基本信息表单
- [x] 认证等级选择 (L0-L3)
- [x] 课程类别选择 (K-M-S-V)
- [x] 学习目标动态添加
- [x] 前置课程选择
- [x] 封面上传
- [x] 考核设置 (通过分/重试/顺序学习)
- [x] 关联考试
- [x] 发布设置

**章节管理 (Chapters.vue)** ⭐ 核心功能
- [x] 章节折叠面板
- [x] 章节增删改
- [x] 视频上传区域 (待接入阿里云VOD)
- [x] **章节测验系统**
  - [x] 单选题创建/编辑
  - [x] 多选题创建/编辑
  - [x] 判断题创建/编辑
  - [x] 选项动态增删
  - [x] 正确答案设置
  - [x] 答案解析填写
- [x] **测验触发设置**
  - [x] 视频结束后触发
  - [x] 视频播放中暂停触发
  - [x] 弹出时间点设置
  - [x] 通过分数设置
  - [x] 允许重试开关

### 5. 题库管理 ✅

**题库列表 (QuestionBank.vue)**
- [x] 题目表格展示
- [x] 多条件筛选 (类型/等级/难度)
- [x] 难度星级显示
- [x] 编辑/删除操作

**题目编辑 (QuestionEdit.vue)**
- [x] 基础表单 (类型/内容/等级)
- [ ] 完整选项编辑 (待完善)
- [ ] 答案解析 (待完善)

### 6. 占位模块

以下模块已创建占位页面，待后续开发：

- [ ] 考试管理 (ExamList/ExamEdit/Results)
- [ ] 直播管理 (List/Edit)
- [ ] 教练管理 (List/Detail/Review)
- [ ] 学员管理 (StudentList)
- [ ] 系统设置 (Settings)

---

## 路由结构

```typescript
/ (AdminLayout)
├── /dashboard          # 工作台
├── /course
│   ├── /list           # 课程列表
│   ├── /create         # 创建课程
│   ├── /edit/:id       # 编辑课程
│   └── /chapters/:courseId  # 章节管理
├── /question
│   ├── /bank           # 题库列表
│   ├── /create         # 创建题目
│   └── /edit/:id       # 编辑题目
├── /exam
│   ├── /list           # 考试列表
│   ├── /create         # 创建考试
│   └── /results/:examId # 成绩管理
├── /live
│   ├── /list           # 直播列表
│   └── /create         # 创建直播
├── /coach
│   ├── /list           # 教练列表
│   ├── /detail/:id     # 教练详情
│   └── /review         # 晋级审核
├── /student            # 学员管理
└── /settings           # 系统设置

/login                  # 登录页 (无布局)
```

---

## 依赖清单

```json
{
  "dependencies": {
    "vue": "^3.x",
    "vue-router": "^4.x",
    "pinia": "^2.x",
    "ant-design-vue": "^4.x",
    "@ant-design/icons-vue": "^7.x",
    "axios": "^1.x",
    "dayjs": "^1.x",
    "uuid": "^9.x"
  },
  "devDependencies": {
    "vite": "^6.x",
    "typescript": "~5.x",
    "@types/uuid": "^9.x",
    "vue-tsc": "^2.x"
  }
}
```

---

## 快速启动

```bash
# 进入项目目录
cd D:\behavioral-health-project\admin-portal

# 安装依赖 (如果未安装)
npm install

# 启动开发服务器
npm run dev -- --port 3000

# 访问
http://localhost:3000
# 登录: admin / admin123
```

---

## 待开发功能 (优先级排序)

### P0 - 核心功能

1. **阿里云VOD视频上传**
   - 获取上传凭证 API
   - 视频直传 OSS
   - 转码回调处理
   - Aliplayer 播放器集成

2. **数据库持久化**
   - PostgreSQL 数据库设计
   - 课程/章节/题目 CRUD API
   - 与 metabolic-core 整合

3. **考试系统完善**
   - 组卷功能 (手动/随机)
   - 考试安排
   - 自动评分
   - 成绩统计

### P1 - 重要功能

4. **防作弊机制**
   - 人脸识别验证
   - 切屏检测
   - 考中抓拍
   - 全屏模式

5. **直播系统**
   - 阿里云 Live 集成
   - 推流/播放配置
   - 直播回放

6. **教练管理完善**
   - 教练列表/详情
   - 晋级审核流程
   - 案例审核

### P2 - 增强功能

7. **实操评估**
   - 录音/录像上传
   - 人工评分工作台
   - 评分维度配置

8. **数据统计**
   - 学习数据分析
   - 考试数据分析
   - 导出报表

---

## 阿里云服务配置 (待填写)

```yaml
# 视频点播 VOD
aliyun_vod:
  access_key_id: ""
  access_key_secret: ""
  region: "cn-shanghai"

# 对象存储 OSS
aliyun_oss:
  bucket: ""
  endpoint: ""

# 视频直播 Live
aliyun_live:
  push_domain: ""
  play_domain: ""

# 人脸核身
aliyun_face:
  scene_id: ""
```

---

## 与 metabolic-core 集成

管理后台需要调用 metabolic-core 的认证体系 API：

```typescript
// 认证相关 API 端点 (metabolic-core 端口 8002)
const API_BASE = 'http://localhost:8002/api'

// 认证等级
GET  /certification/levels              // 获取等级要求
GET  /certification/courses             // 获取课程列表
GET  /certification/exams               // 获取考试列表

// 教练管理
GET  /certification/coaches             // 教练列表
POST /certification/coaches             // 创建教练
GET  /certification/coaches/:id/evaluate // 晋级评估
POST /certification/coaches/:id/promote  // 执行晋级
```

---

## 开发里程碑

### 2026-01-24
- [x] 项目初始化 (Vue3 + Vite + TypeScript)
- [x] Ant Design Vue 4 集成
- [x] 路由系统配置
- [x] 管理后台布局 (AdminLayout)
- [x] 登录页面
- [x] 工作台仪表盘
- [x] 课程列表页
- [x] 课程编辑页
- [x] **章节管理页 (核心功能)**
  - 视频上传区域
  - 章节测验题目管理
  - 触发时机配置
- [x] 题库管理页
- [x] 占位页面创建
- [x] 开发服务器启动 (端口3000)

### 2026-01-24 (续) - P0/P1 功能实施
- [x] **后端数据库层 (metabolic-core)**
  - Docker Compose PostgreSQL 配置
  - TypeORM 配置和 DataSource
  - 13 个数据库实体 (Entity) 文件
  - Repository 层 (CoachRepository, ExamRepository)
  - 环境变量配置 (.env)

- [x] **前端 API 层**
  - Axios 实例 + 拦截器 (src/api/request.ts)
  - 考试 API (src/api/exam.ts)
  - 题库 API (src/api/question.ts)
  - 成绩 API (src/api/result.ts)

- [x] **前端状态管理 (Pinia)**
  - 考试 Store (src/stores/exam.ts)
  - 题库 Store (src/stores/question.ts)

- [x] **TypeScript 类型定义**
  - 考试系统类型 (src/types/exam.ts)
  - UI 常量和标签映射

- [x] **考试管理完整功能**
  - ExamList.vue - 考试列表 (筛选/CRUD/发布)
  - ExamEdit.vue - 考试编辑 (表单/题目选择器)
  - Results.vue - 成绩管理 (统计卡片/详情弹窗)

### 待开发
- [ ] 防作弊机制 (P1)
  - 切屏检测
  - 全屏模式
  - 人脸核身
  - 考中抓拍

---

## 注意事项

1. **登录凭据**: 当前为硬编码演示 (admin/admin123)，生产环境需接入真实认证
2. **数据存储**: 当前为内存模拟数据，需接入数据库
3. **视频上传**: 已预留上传区域，需接入阿里云VOD
4. **API调用**: 需启动 metabolic-core (端口8002) 才能使用认证API

---

## 相关文档

- 项目总纪事: `D:\behavioral-health-project\PROJECT_CHRONICLE.md`
- 认证体系设计: `D:\behavioral-health-project\metabolic-core\docs\CERTIFICATION_PLATFORM_DESIGN.md`
- 今日开发纪事: `D:\behavioral-health-project\metabolic-core\docs\CHANGELOG_2026-01-24.md`
- 认证体系规范: `D:\行为健康教练认证体系 · 工程级系统规范.txt`

---

*此文件应在每次重大更新后维护，以确保开发历史的完整性。*
