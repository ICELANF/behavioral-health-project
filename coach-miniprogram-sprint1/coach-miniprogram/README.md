# BHP 教练培养体系 · 微信小程序 + H5
## Sprint 1 交付包 — 基础骨架

---

## 快速启动

### 1. 安装依赖

```bash
cd coach-miniprogram
npm install
```

### 2. 开发模式

```bash
# 微信小程序（在 HBuilderX 或命令行均可）
npm run dev:mp-weixin

# H5 浏览器预览
npm run dev:h5
```

### 3. 微信开发者工具配置

打开微信开发者工具 → 导入项目
- 目录：`unpackage/dist/dev/mp-weixin`
- AppID：`wx5755ae9b2491a04b`
- **开发阶段**：详情 → 本地设置 → 勾选「不校验合法域名」

### 4. 后端联调

H5 模式通过 vite proxy 自动转发 `/api` → `localhost:8000`，无跨域问题。

小程序开发阶段不校验域名即可直接访问本地后端。

---

## Sprint 1 已完成内容

```
✅ 项目初始化（uni-app Vue3 + TypeScript）
✅ 微信小程序 + H5 双目标配置
✅ AppID: wx5755ae9b2491a04b 已写入 manifest.json
✅ 分包策略（主包 + 6个分包）
✅ BHP Design System CSS Tokens 完整适配（小程序兼容版）
✅ HTTP 封装（Token 自动注入 + 401 自动刷新 + 统一错误处理）
✅ 三个核心 Store（user / learning / coach）
✅ 微信一键登录工具函数
✅ 4个通用组件（LevelBadge / PointsCard / RiskTag / CourseCard）
✅ 双模式 TabBar 组件（学习者 L0-L2 / 教练 L3+）
✅ 登录页（账号密码 + 微信一键）
✅ 首页（角色自适应：学习者视图 / 教练工作台视图）
✅ App.vue 入口 + 启动时登录态恢复
```

---

## 文件结构

```
src/
├── styles/
│   └── bhp-design-tokens.css   ← BHP Design System（小程序适配版）
├── api/
│   ├── request.ts              ← HTTP 基础封装
│   └── auth.ts                 ← 认证接口
├── stores/
│   ├── user.ts                 ← 用户状态
│   ├── learning.ts             ← 学习状态
│   └── coach.ts                ← 教练工作台状态
├── utils/
│   ├── level.ts                ← 级别/积分工具函数
│   └── wechat.ts               ← 微信小程序工具
├── components/
│   ├── BHPLevelBadge.vue       ← 六级角色徽章
│   ├── BHPPointsCard.vue       ← 三维积分卡
│   ├── BHPRiskTag.vue          ← 风险等级标签
│   ├── BHPCourseCard.vue       ← 课程内容卡片
│   └── BHPTabBar.vue           ← 双模式 TabBar
└── pages/
    ├── auth/login.vue          ← 登录页
    └── home/index.vue          ← 首页（双模式）
```

---

## Sprint 2 计划（下周）

学习中心全流程：
- 课程目录（M1-M4 分类 + 等级门控）
- 视频播放（断点续播 30s 心跳）
- 图文/音频内容详情
- 随堂测验（单选 + 多选）
- 完成学习 → 积分+学分联动

---

## 已知注意事项

1. **后端 BaseURL**：`request.ts` 中小程序生产环境 URL 需替换为真实域名（当前为占位符）
2. **TabBar 图标**：`pages.json` 引用 `static/tabs/*.png`，需提供实际图标文件（或改用 emoji 版 `BHPTabBar.vue`）
3. **Logo**：登录页引用 `/static/logo.png`，需提供实际文件
4. **color-mix()**：Design System 品牌主题的深/浅色变体已改为直接色值，不再依赖 `color-mix()`
5. **暗色模式**：MVP 阶段暂不实现，`html.dark` 相关样式已移除

---

*Sprint 1 | 行健平台 V5.3.1 | 2026-02-28*
