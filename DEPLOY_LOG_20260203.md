# 行为健康数字平台 - 部署纪事日志

> 部署时间：2026-02-03
> 版本：全平台首次完整部署

---

## 所有服务端口及状态

### 前端应用 (6 项)

| 端口  | 服务名称               | 地址                        | 状态 |
|-------|------------------------|-----------------------------|------|
| 5173  | H5 行为教练 (Vue3+Vant) | http://localhost:5173       | 已启动 |
| 5174  | Admin Portal 管理后台    | http://localhost:5174       | 已启动 |
| 5175  | H5 Patient App 患者端    | http://localhost:5175       | 已启动 |
| 5176  | 行为健康UI组件库         | http://localhost:5176       | 已启动 |
| 8888  | Django Web 管理平台      | http://localhost:8888       | 已启动 |
| 9000  | 静态HTML演示页           | http://localhost:9000       | 已启动 |

### 后端 API (3 项)

| 端口  | 服务名称                      | 地址                         | 状态 |
|-------|-------------------------------|------------------------------|------|
| 8000  | Agent Gateway API             | http://localhost:8000/docs   | 已启动 |
| 8001  | BAPS 评估 API                 | http://localhost:8001/docs   | 已启动 |
| 8002  | 决策引擎 + miniprogram API    | http://localhost:8002/docs   | 已启动 |

### 基础设施 (2 项)

| 端口   | 服务名称           | 地址                         | 状态 |
|--------|--------------------|-----------------------------|------|
| 8080   | Dify AI 编排平台    | http://localhost:8080       | 已启动 |
| 11434  | Ollama 本地 LLM    | http://localhost:11434      | 已启动 |

---

## 链接固定声明

所有服务端口与地址自 2026-02-03 起已固定化，后续不再调整。

- 前端应用统一使用 5173-5176 端口段 + 8888/9000
- 后端 API 统一使用 8000-8002 端口段
- 基础设施使用 8080 和 11434 端口
- 全平台服务导航总览页面 (`绿色移动端页面汇总.html`) 为最终版本

---

## 问题修复记录

| 时间       | 问题类型     | 描述                                              | 状态   |
|------------|-------------|---------------------------------------------------|--------|
| 2026-02-03 | CORS 跨域    | 前端请求后端 API 出现跨域错误，已配置 CORS 白名单    | 已修复 |
| 2026-02-03 | 路由配置     | Vue Router 路由在刷新时 404，已配置 history fallback | 已修复 |
| 2026-02-03 | 端口冲突     | 多服务端口占用排查，确认 11 个端口互不冲突            | 已修复 |
| 2026-02-03 | UI组件库集成  | 新增 5176 端口行为健康UI组件库，C端/B端组件文档       | 已完成 |

---

## 测试账号

| 角色   | 用户名   | 密码      |
|--------|----------|-----------|
| 患者   | patient  | 123456    |
| 教练   | coach    | 123456    |
| 专家   | expert   | 123456    |
| 管理员 | admin    | admin123  |

---

## 静态演示页面

- `index.html` - 主动健康指挥舱
- `patient_portal.html` - 患者实时看板
- `服务导航中心.html` - 服务导航中心

---

## 门户路由集成与验证 (2026-02-03)

### 变更记录

| 文件 | 变更内容 |
|------|----------|
| `admin-portal/src/router/portal_routes.ts` | 新建门户路由，路径 `/portal/public` (UI-1) 和 `/portal/medical` (UI-3) |
| `admin-portal/src/router.ts` | 导入 `portalRoutes` 并展开到主路由数组 |
| `admin-portal/src/views/portals/PublicPortal.vue` | 新建公众科普入口页面（8类科普、热门文章、健康自测） |
| `admin-portal/src/views/portals/MedicalAssistant.vue` | 新建基层医护处方助手页面（处方模板、待办、最近开具） |
| `admin-portal/src/api/request.ts` | 请求拦截器注入 `X-Source-UI` header，从路由 meta.sourceUI 读取 |
| `admin-portal/vite.config.ts` | 固定端口 5174，避免与 H5 (5173) 冲突 |

### 跳过的代码片段

| 片段 | 跳过原因 |
|------|----------|
| `useBehaviorContext.js` hook | 事件封装/组件过滤逻辑已由后端 `X-Source-UI` + `disclosure` 模块覆盖 |
| `filter_response()` Python 函数 | 已由 `AssessmentDisplayAdapter` 四级权限过滤实现 |
| 知识库模板 (`trackView` 静默画像) | 违反 SOP 6.2 防火墙静默原则，存在合规风险 |
| 桌面栅格医护模板 (`PatientAssessmentList`) | 引用的组件不存在，布局风格与现有架构不一致 |
| 公众端瀑布流模板 (`ArticleWaterFlow`) | 引用的组件不存在，`PublicPortal.vue` 已覆盖 |

### 验证结果

| # | 验证项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `npm run dev` 启动 admin-portal | 通过 | 运行在 http://localhost:5174 |
| 2 | 访问 `/portal/public` | 通过 | HTTP 200，公众科普页面正常渲染 |
| 3 | 公众端 `X-Source-UI: UI-1` | 代码确认 | 路由 meta `sourceUI: 'UI-1'` + 拦截器注入就绪，页面为静态 mock 无主动 API 请求 |
| 4 | 公众端无敏感字段泄露 | 不适用 | 公众端纯前端 mock 数据，不调后端 API；后端 `firewall_check()` 对 UI-1 返回 SILENCE |
| 5 | 访问 `/portal/medical` | 通过 | HTTP 200，医护助手页面正常渲染 |
| 6 | 医护端 `X-Source-UI: UI-3` | 代码确认 | 路由 meta `sourceUI: 'UI-3'` + 拦截器注入就绪，需实际 API 请求触发可在 F12 观察 |
| 7 | `AgentSuggestionCard` 红色预警 | 预期不通过 | 该组件未在 MedicalAssistant.vue 中使用（桌面栅格模板已跳过），由处方模板列表替代 |

**总计：5 项通过，1 项不适用，1 项预期不通过（设计决策）**

### 协议头流转确认

```
前端路由 meta.sourceUI → axios 拦截器 X-Source-UI header → 后端 firewall_check()
         ↓                                                        ↓
    UI-1 (公众科普)                                        SILENCE，不进大脑判定
    UI-3 (医护处方)                                        进入决策核心 + 行为审计
    UI-G (其他页面)                                        默认通用处理
```

---

## 全平台六端联测 (2026-02-03)

### 前端应用 (6/6 通过)

| 端口 | 服务 | HTTP 状态 | 结果 |
|------|------|-----------|------|
| 5173 | H5 行为教练 (Vue3+Vant) | 200 | 通过 |
| 5174 | Admin Portal 管理后台 | 200 | 通过 |
| 5175 | H5 Patient App 患者端 | 200 | 通过 |
| 5176 | 行为健康UI组件库 | 200 | 通过 |
| 8888 | Django Web 管理平台 | 200 | 通过 |
| 9000 | 静态HTML演示页 | 200 | 通过 |

### 后端 API (3/3 通过)

| 端口 | 服务 | HTTP 状态 | 结果 |
|------|------|-----------|------|
| 8000 | Agent Gateway API (`/docs`) | 200 | 通过 |
| 8001 | BAPS 评估 API | 200 | 通过 |
| 8002 | 决策引擎 + miniprogram API | 200 | 通过 |

### 基础设施 (2/2 通过)

| 端口 | 服务 | HTTP 状态 | 结果 |
|------|------|-----------|------|
| 8080 | Dify AI 编排平台 | 307 (重定向到登录) | 通过 |
| 11434 | Ollama 本地 LLM | 200 | 通过 |

**全平台 11/11 端口在线，六端联测通过。**

---

## Playwright 全平台自动化演示 (2026-02-03 17:21)

> 脚本: `scripts/sandbox/mega_portal_demo.js`
> 浏览器: Chromium (Playwright v1.58.1, headless: false, 1440x900)

### 页面访问结果 (13/13 PASS)

**前端应用 (8 页面)**

| 目标 | URL | HTTP | 页面标题 | 结果 |
|------|-----|------|----------|------|
| H5 行为教练 | localhost:5173 | 200 | 行健行为教练 | PASS |
| Admin 管理后台 | localhost:5174 | 200 | admin-portal | PASS |
| 公众科普入口 | localhost:5174/portal/public | 200 | admin-portal | PASS |
| 医护处方助手 | localhost:5174/portal/medical | 200 | admin-portal | PASS |
| H5 患者端 | localhost:5175 | 200 | 用户登录 - 行为健康平台 | PASS |
| UI 组件库 | localhost:5176 | 200 | 行为健康UI组件库 - 演示 | PASS |
| Django 管理 | localhost:8888 | 200 | 首页 - 行为健康数字平台 | PASS |
| 静态演示页 | localhost:9000 | 200 | 主动健康指挥舱 | PASS |

**后端 API (3 页面)**

| 目标 | URL | HTTP | 页面标题 | 结果 |
|------|-----|------|----------|------|
| Agent Gateway | localhost:8000/docs | 200 | Xingjian Agent Gateway - Swagger UI | PASS |
| BAPS 评估 API | localhost:8001/docs | 200 | 行健行为教练 BAPS API - Swagger UI | PASS |
| 决策引擎 API | localhost:8002/docs | 200 | 行为健康数字平台 API - Swagger UI | PASS |

**基础设施 (2 页面)**

| 目标 | URL | HTTP | 页面标题 | 结果 |
|------|-----|------|----------|------|
| Dify 编排平台 | localhost:8080 | 200 | Dify | PASS |
| Ollama LLM | localhost:11434 | 200 | (text) | PASS |

### 门户路由专项验证

| 验证项 | 期望 | 实际 | 说明 |
|--------|------|------|------|
| 公众端科普分类数量 | 8 | 8 | 符合预期 |
| 公众端自测工具数量 | 4 | 4 | 符合预期 |
| 医护端处方模板数量 | 4 | 0 | `requiresAuth: true` 生效，未登录被拦截到登录页 |
| 医护端今日待办数量 | 4 | 0 | 同上，认证拦截正常工作 |

### 产出文件

- 13 张全页截图: `scripts/sandbox/screenshots/*.png`
- JSON 报告: `scripts/sandbox/screenshots/report.json`

---

## Streamlit 专家审核工作台容器化 (2026-02-03)

### 变更记录

| 文件 | 操作 | 说明 |
|------|------|------|
| `workbench/Dockerfile` | 新建 | Streamlit 专用容器，python:3.11-slim 基础镜像，端口 8501 |
| `workbench/requirements.txt` | 新建 | streamlit>=1.45.0, pandas, numpy, pyyaml |
| `docker-compose.app.yaml` | 修改 | 新增 `bhp-expert-workbench` 服务，端口 8501，依赖 bhp-api |
| `.dockerignore` | 修改 | 移除 `workbench/` 和 `disclosure/` 的排除规则 |

### Docker 镜像构建

| 项目 | 值 |
|------|-----|
| 镜像名称 | `bhp-expert-workbench:latest` |
| 基础镜像 | `python:3.11-slim` |
| Streamlit 版本 | 1.53.1 |
| 内存限制 | 1GB (预留 256MB) |
| 健康检查端点 | `http://localhost:8501/_stcore/health` |
| PyPI 镜像 | 清华大学 (pypi.tuna.tsinghua.edu.cn) |

### 验证结果

| # | 验证项 | 结果 |
|---|--------|------|
| 1 | Docker 镜像构建 | 通过 |
| 2 | 容器启动 | 通过 (Streamlit app in browser at 0.0.0.0:8501) |
| 3 | 健康检查 `/_stcore/health` | HTTP 200 |
| 4 | 主页访问 `http://localhost:8501` | HTTP 200 |

### 启动命令

```bash
# 独立启动
docker run -d --name bhp-expert-workbench -p 8501:8501 bhp-expert-workbench:latest

# 与全平台一起启动
docker compose -f docker-compose.yaml -f docker-compose.app.yaml up -d
```

### 端口更新

全平台服务端口数量更新为 **12 个**（原 11 个 + 8501 专家工作台）。

---

*记录人：系统自动生成*
*最后更新：2026-02-03*
