# BehaviorOS Coach-Miniprogram 稳定化推进方案

> 基线: `9a6b18b` (Sprint 1 · 44页面框架 + 9 API模块 + 5组件 + 双模式首页)
> 目标: 在确保稳定的前提下恢复100%功能 + BOS UI美化
> 日期: 2026-03-01

---

## 零、当前锚点资产盘点

### 9a6b18b 包含的前端资产

| 类别 | 内容 | 数量 |
|------|------|------|
| 页面 | 44个完整页面(home/journey/profile/coach/assessment/exam/learning/companions/notifications/auth/profile-extra) | 44 |
| API模块 | auth.ts, coach.ts, assessment.ts, companion.ts, exam.ts, journey.ts, learning.ts, profile.ts, request.ts | 9 |
| 组件 | BHPCourseCard, BHPLevelBadge, BHPPointsCard, BHPRiskTag, BHPTabBar | 5 |
| 配置 | pages.json(187行), manifest.json, package.json | 3 |
| 视图 | grower首页 + coach首页 双模式 | 2 |

### 后端资产 (Docker内，不受前端回滚影响)

| 服务 | 端口 | 状态 |
|------|------|------|
| bhp_v3_api (FastAPI) | 8000 | ✅ healthy |
| PostgreSQL | 5432 | ✅ healthy |
| Redis | 6379 (容器内) | ✅ running |
| Qdrant | 6333 | ✅ running |
| bhp_v3_worker (Celery) | - | ✅ healthy |
| bhp_v3_beat | - | ⚠️ unhealthy (已知) |

### backup分支保存的待恢复资产

| 资产 | 来源分支 | 说明 |
|------|----------|------|
| 11个BOS美化页面(原始版) | backup-2026-0301-before-rollback | 小程序版UI/ 目录 |
| 11个BOS美化页面(统一配置版) | backup-2026-0301-before-rollback | 小程序版UI更新/ 目录 |
| config/env.ts | backup-2026-0301-before-rollback | 环境配置 |
| utils/request.ts(统一版) | backup-2026-0301-before-rollback | 已合并的HTTP模块 |
| api_test_suite/ | backup-2026-0301-before-rollback | API测试套件 |
| coach页面目录重构 | backup-2026-0301-before-rollback | dashboard/index.vue等子目录结构 |

---

## 一、三个推进方案对比

### 方案A: 保守渐进（推荐）

```
锚点 → 基线验证 → 基础设施加固 → 功能恢复(无UI) → 全面测试 → UI集成 → 上线
```

**核心原则**: 每一步都验证通过后再进下一步，功能恢复和UI美化严格分离。

| 优点 | 缺点 |
|------|------|
| 每步可回退，风险最低 | 总耗时最长(8-10小时) |
| 问题定位精准 | 步骤多，需要耐心 |
| 最终交付最稳定 | |

### 方案B: 选择性合并

```
锚点 → 基线验证 → 从backup分支cherry-pick已验证的修复 → 跳过中间试错 → 直接到稳定状态
```

**核心原则**: 不重复走一遍踩坑路，直接提取backup分支中已验证有效的最终结果。

| 优点 | 缺点 |
|------|------|
| 快(4-6小时) | cherry-pick可能引入隐藏依赖 |
| 利用已有工作成果 | 需要精确判断哪些改动是干净的 |

### 方案C: 双轨并行

```
stabilize分支做基础设施加固
同时在另一个分支准备UI集成包
加固完成后一次性merge UI分支
```

| 优点 | 缺点 |
|------|------|
| 并行提效 | 分支管理复杂 |
| UI准备不阻塞基座工作 | merge可能有冲突 |

### 推荐: 方案A（保守渐进）

理由: 此前的问题正是因为多个改动叠加导致状态不可预测。这次需要的是确定性，不是速度。

---

## 二、方案A 完整执行计划

### Phase 0: 基线验证 (30分钟)

> 目标: 确认9a6b18b本身是健康的

#### 0.1 编译验证

```powershell
cd D:\behavioral-health-project\coach-miniprogram

# 确认package.json在位
cat package.json | Select-Object -First 10

# 清理+重装
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
npm install

# 编译
npm run dev:mp-weixin
```

**通过标准**: dist/dev/mp-weixin 正常生成，编译零错误。

#### 0.2 微信开发者工具验证

- [ ] 工具项目路径指向: `D:\behavioral-health-project\coach-miniprogram\dist\dev\mp-weixin`
- [ ] 登录页正常渲染
- [ ] grower (`grower`/`Grower@2026`) 登录→首页显示
- [ ] coach (`coach`/`Coach@2026`) 登录→教练首页显示

#### 0.3 后端API验证

```powershell
# coach登录
$body = '{"username":"coach","password":"Coach@2026"}'
$r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json"
Write-Host "Token: $($r.access_token.Substring(0,20))..."

# 测试coach端点
$h = @{ Authorization = "Bearer $($r.access_token)" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/coach/dashboard" -Headers $h
```

**Phase 0 判定**:
- ✅ 全部通过 → 进入Phase 1
- ❌ 编译失败 → 检查package.json的scripts字段是否包含dev:mp-weixin
- ❌ 登录失败 → 检查API端口和认证配置

---

### Phase 1: 基础设施加固 (1-2小时)

> 目标: 消除所有配置漂移和环境污染

#### 1.1 确立端口真相源

**铁律: 后端只有一个端口 8000，全项目统一。**

```powershell
# 审计当前代码中的端口引用
cd D:\behavioral-health-project\coach-miniprogram
Select-String -Path "src\**\*" -Pattern "8001|8002|localhost:\d{4}" -Recurse | ForEach-Object {
    "$($_.Filename):$($_.LineNumber) → $($_.Line.Trim())"
}
```

如果发现8001或8002引用，逐个修正为8000。

#### 1.2 确认request.ts是唯一HTTP模块

```powershell
# 查看当前锚点中的request模块
Get-ChildItem -Path src -Recurse -Filter "request.ts" | Select-Object FullName

# 期望只有一个: src/api/request.ts
```

**检查request.ts中的BASE_URL配置**:

```powershell
Select-String -Path "src\api\request.ts" -Pattern "BASE_URL|baseURL|localhost"
```

如果BASE_URL硬编码为8002或其他错误端口，修正：

```powershell
# 查看当前值
cat src\api\request.ts | Select-String "BASE|base|8000|8002"
```

#### 1.3 确认package.json编译命令

```powershell
cat package.json | Select-String "dev:mp-weixin"
```

**必须包含 `-p mp-weixin` 参数**。如果缺失:

```powershell
# 查看完整scripts段
cat package.json | Select-String -Pattern '"scripts"' -Context 0,10
```

修复方法（如需要）:

```powershell
# 用node修改package.json
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json','utf8'));
pkg.scripts['dev:mp-weixin'] = 'uni -p mp-weixin';
pkg.scripts['build:mp-weixin'] = 'uni build -p mp-weixin';
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
console.log('Fixed. Scripts:', JSON.stringify(pkg.scripts, null, 2));
"
```

#### 1.4 创建环境配置文件

9a6b18b锚点没有.env文件，需要新建：

```powershell
# 开发环境
Set-Content -Path ".env" -Value "VITE_API_URL=http://localhost:8000/api/v1"

# 生产环境
Set-Content -Path ".env.production" -Value "VITE_API_URL=https://your-production-domain.com/api/v1"
```

然后确认request.ts能读取该变量。如果request.ts中是硬编码URL，先不动——到Phase 3统一处理。

#### 1.5 Docker环境治理

```powershell
cd D:\behavioral-health-project

# 检查是否有多个compose文件在运行
docker-compose -f docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}" 2>$null
docker-compose -f docker-compose.app.yaml ps --format "table {{.Name}}\t{{.Status}}" 2>$null
```

**决策规则**:

| 情况 | 行动 |
|------|------|
| 只有docker-compose.yml在跑 | ✅ 保持，这是正确状态 |
| docker-compose.app.yaml也在跑 | 执行 `docker-compose -f docker-compose.app.yaml down` |
| 两个都在跑且共享网络 | 先down app.yaml，确认主Stack正常后再决定是否需要app.yaml |

**小程序开发阶段不需要app.yaml**：前端由`npm run dev:mp-weixin`本地编译，不需要Docker中的前端容器。

#### 1.6 验证网络隔离

```powershell
# 确认bhp_v3_api只在默认网络
docker inspect bhp_v3_api --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'

# 从宿主机直接测试API
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST `
    -Body '{"username":"coach","password":"Coach@2026"}' -ContentType "application/json"
```

#### Phase 1 验收

- [ ] 全项目无8001/8002端口引用
- [ ] request.ts唯一且指向正确端口
- [ ] package.json编译命令正确
- [ ] .env文件就位
- [ ] Docker仅主Stack运行，无冲突
- [ ] 编译通过，登录成功

```powershell
# Phase 1 完成后提交
git add -A
git commit -m "phase1: 基础设施加固 — 端口统一/环境配置/Docker治理"
```

---

### Phase 2: 子包依赖根治 (1-2小时)

> 目标: 解决flywheel等coach子包页面无法require主包模块的问题
> 这是锚点前已存在的根本问题，也是后续所有"零依赖内联"方案的起因

#### 2.1 诊断当前子包结构

```powershell
# 查看pages.json中的子包配置
cat src\pages.json | Select-String -Pattern "subPackages|subpackages|root" -Context 0,5

# 查看coach页面的import依赖
Select-String -Path "src\pages\coach\**\*.vue" -Pattern "import.*from.*@/" -Recurse
```

#### 2.2 三种解决方案

**方案2A: subPackages共享配置 (首选)**

在pages.json中为子包声明可访问主包资源：

```json
{
  "subPackages": [{
    "root": "pages/coach",
    "pages": [
      {"path": "dashboard/index"},
      {"path": "flywheel/index"},
      {"path": "students/index"},
      {"path": "students/detail"}
    ]
  }],
  "preloadRule": {
    "pages/coach/dashboard/index": {
      "packages": ["__APP__"],
      "network": "all"
    }
  }
}
```

验证：编译后在微信开发者工具中打开coach页面，查看console是否还有`module not defined`错误。

**方案2B: 子包本地模块 (备选)**

如果方案2A不行，在coach子包内创建本地request模块：

```powershell
# 创建子包本地工具
mkdir -p src\pages\coach\utils

# 从主包复制request模块到子包
Copy-Item src\api\request.ts src\pages\coach\utils\request.ts
```

然后修改coach页面的import路径：
```typescript
// 从
import request from '@/api/request'
// 改为
import request from '../utils/request'  // 相对路径，子包内部解析
```

**方案2C: 取消子包，全部放主包 (兜底)**

如果A和B都不行，将coach页面从subPackages移到主包：

```json
{
  "pages": [
    {"path": "pages/home/index"},
    {"path": "pages/coach/dashboard/index"},
    {"path": "pages/coach/flywheel/index"}
  ]
}
```

代价是主包体积增大，但能保证稳定运行。

#### 2.3 验证

```powershell
# 重编译
npm run dev:mp-weixin

# 在微信开发者工具中:
# 1. 打开coach/dashboard页面 → 无报错
# 2. 打开coach/flywheel页面 → 无报错
# 3. 检查console无 "module xxx is not defined"
```

#### Phase 2 验收

- [ ] coach子包页面全部可渲染
- [ ] 无`module not defined`错误
- [ ] request模块在子包中可正常工作
- [ ] API请求从子包页面发出后返回正确数据

```powershell
git add -A
git commit -m "phase2: 子包依赖根治 — coach页面可正常引用请求模块"
```

---

### Phase 3: HTTP请求模块统一 (1小时)

> 目标: 建立唯一的、支持环境切换的请求模块

#### 3.1 检查当前request.ts

```powershell
cat src\api\request.ts
```

审查要点:
- BASE_URL是硬编码还是从环境变量读取？
- 是否有token自动注入？
- 是否有401拦截和token刷新？
- 是否有请求超时配置？

#### 3.2 升级request.ts

如果当前版本缺少上述功能，升级为完整版：

```typescript
// src/api/request.ts — 唯一HTTP模块

// 环境变量读取（uni-app方式）
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

function getToken(): string {
  return uni.getStorageSync('access_token') || ''
}

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  header?: Record<string, string>
}

// 请求队列（token刷新时暂存后续请求）
let isRefreshing = false
let pendingRequests: Array<() => void> = []

function request<T = any>(options: RequestOptions): Promise<T> {
  const { url, method = 'GET', data, header = {} } = options
  const token = getToken()

  return new Promise((resolve, reject) => {
    uni.request({
      url: url.startsWith('http') ? url : `${BASE_URL}${url}`,
      method,
      data,
      timeout: 15000,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...header,
      },
      success: (res: any) => {
        if (res.statusCode === 401) {
          // Token过期处理
          handleUnauthorized().then(() => {
            // 重试原请求
            request<T>(options).then(resolve).catch(reject)
          }).catch(reject)
        } else if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          reject({ statusCode: res.statusCode, data: res.data })
        }
      },
      fail: (err: any) => {
        reject(err)
      }
    })
  })
}

async function handleUnauthorized(): Promise<void> {
  if (isRefreshing) {
    return new Promise(resolve => { pendingRequests.push(resolve) })
  }
  isRefreshing = true
  try {
    const refreshToken = uni.getStorageSync('refresh_token')
    if (!refreshToken) throw new Error('No refresh token')

    const res: any = await new Promise((resolve, reject) => {
      uni.request({
        url: `${BASE_URL}/auth/refresh`,
        method: 'POST',
        data: { refresh_token: refreshToken },
        header: { 'Content-Type': 'application/json' },
        success: (r: any) => r.statusCode === 200 ? resolve(r.data) : reject(r),
        fail: reject,
      })
    })

    uni.setStorageSync('access_token', res.access_token)
    if (res.refresh_token) uni.setStorageSync('refresh_token', res.refresh_token)

    // 释放队列
    pendingRequests.forEach(cb => cb())
    pendingRequests = []
  } catch {
    // 刷新失败，清除token，跳转登录
    uni.removeStorageSync('access_token')
    uni.removeStorageSync('refresh_token')
    uni.reLaunch({ url: '/pages/auth/login' })
    throw new Error('Session expired')
  } finally {
    isRefreshing = false
  }
}

// 便捷方法
export const http = {
  get: <T = any>(url: string, data?: any) => request<T>({ url, method: 'GET', data }),
  post: <T = any>(url: string, data?: any) => request<T>({ url, method: 'POST', data }),
  put: <T = any>(url: string, data?: any) => request<T>({ url, method: 'PUT', data }),
  del: <T = any>(url: string, data?: any) => request<T>({ url, method: 'DELETE', data }),
}

export default request
```

#### 3.3 确保所有API模块引用统一

```powershell
# 查找所有import request的地方
Select-String -Path "src\**\*.ts","src\**\*.vue" -Pattern "from.*request" -Recurse
```

所有引用应指向 `@/api/request` 或子包方案2B中的相对路径。

#### Phase 3 验收

- [ ] 全项目只有一个request模块
- [ ] BASE_URL从环境变量读取，回退到localhost:8000
- [ ] 包含token注入、401拦截、刷新队列
- [ ] 所有API模块import路径一致

```powershell
git add -A
git commit -m "phase3: HTTP请求模块统一 — 环境切换/401拦截/token刷新"
```

---

### Phase 4: 功能完整性验证 (1小时)

> 目标: 确认44个页面 + 双角色视图 全部正常工作

#### 4.1 Grower视图验证

```
账号: grower / Grower@2026
```

| 页面 | 路径 | 检查项 |
|------|------|--------|
| 首页 | home/index | 数据卡片显示，底部TabBar正常 |
| 旅程 | journey/index | 页面渲染，阶段展示 |
| 学习 | learning/index | 课程列表加载 |
| 评估 | assessment/index | 评估问卷可打开 |
| 同伴 | companions/index | 页面渲染 |
| 通知 | notifications/index | 消息列表 |
| 个人 | profile/index | 头像、昵称显示 |

#### 4.2 Coach视图验证

```
账号: coach / Coach@2026
```

| 页面 | 路径 | 检查项 |
|------|------|--------|
| 教练首页 | coach/index | 工作台统计 |
| 学员列表 | coach/students | 学员数据加载 |
| 学员详情 | coach/students/detail | 大五人格、BPT6标签 |
| 飞轮 | coach/flywheel | **重点**: 页面渲染、审核队列 |
| 消息 | coach/messages | 会话列表 |
| 分析 | coach/analytics | 统计图表 |

#### 4.3 API端点烟测

```powershell
# 自动化烟测脚本
$coach = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST -Body '{"username":"coach","password":"Coach@2026"}' `
    -ContentType "application/json"
$token = $coach.access_token
$h = @{ Authorization = "Bearer $token" }

$endpoints = @(
    @{name="dashboard"; path="/api/v1/coach/dashboard"},
    @{name="students"; path="/api/v1/coach/students"},
    @{name="conversations"; path="/api/v1/coach/conversations"},
    @{name="live-sessions"; path="/api/v1/coach/live-sessions"},
    @{name="risk-alerts"; path="/api/v1/coach/risk-alerts"},
    @{name="review-queue"; path="/api/v1/coach/review-queue"},
    @{name="push-pending"; path="/api/v1/coach-push/pending"},
    @{name="analytics"; path="/api/v1/coach/analytics/week-trend"},
    @{name="assessment"; path="/api/v1/assessment-assignments"},
    @{name="stats-today"; path="/api/v1/coach/stats/today"}
)

foreach ($ep in $endpoints) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000$($ep.path)" -Headers $h -UseBasicParsing
        Write-Host "✅ $($ep.name) → $($r.StatusCode)"
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        Write-Host "❌ $($ep.name) → $code"
    }
}
```

**对比说明**: 上面的端点列表来自SESSION-SUMMARY中记录的11个页面的API依赖表。如果某个端点返回404，说明后端可能未实现该路由——记录下来，在Phase 5中决定是用mock数据还是跳过该功能。

#### 4.4 /v1/professional/ 幽灵路径排查

```powershell
# 在源码中搜索
Select-String -Path "src\**\*" -Pattern "professional" -Recurse

# 在编译产物中搜索
Select-String -Path "dist\**\*.js" -Pattern "professional" -Recurse

# 如果源码中没有但编译产物中有:
# → 说明是缓存污染，清理dist后重编译即可
# 如果两者都没有:
# → 说明该问题已随回滚消除
```

#### Phase 4 验收

- [ ] grower视图7个核心页面全部可渲染
- [ ] coach视图6个核心页面全部可渲染
- [ ] API烟测端点 ≥80% 返回200
- [ ] 无/v1/professional/幽灵请求
- [ ] 编译零错误

```powershell
git add -A
git commit -m "phase4: 功能完整性验证通过 — 44页面双视图全部正常"
```

---

### Phase 5: Coach页面目录重构 (30分钟)

> 目标: 为BOS UI集成准备正确的目录结构
> 当前9a6b18b中coach页面可能是平铺结构，UI美化需要子目录结构

#### 5.1 检查当前结构

```powershell
Get-ChildItem -Path src\pages\coach -Recurse | Select-Object FullName
```

**9a6b18b中的结构** (预期):
```
src/pages/coach/
├── index.vue          # 教练首页
├── students.vue       # 学员列表
├── students-detail.vue # 学员详情
├── flywheel.vue       # AI飞轮
├── messages.vue       # 消息
└── analytics.vue      # 分析
```

**UI美化需要的结构**:
```
src/pages/coach/
├── dashboard/index.vue    # 工作台 (新页面)
├── flywheel/index.vue     # AI飞轮
├── students/index.vue     # 学员列表
├── students/detail.vue    # 学员详情
├── risk/index.vue         # 风险管理 (新页面)
├── assessment/index.vue   # 评估分配
├── assessment/review.vue  # 评估审核
├── push-queue/index.vue   # 推送审批
├── analytics/index.vue    # 分析
├── messages/index.vue     # 消息
└── live/index.vue         # 直播
```

#### 5.2 执行重构

```powershell
cd D:\behavioral-health-project\coach-miniprogram\src\pages\coach

# 创建子目录
$dirs = @("dashboard","flywheel","students","risk","assessment","push-queue","analytics","messages","live")
foreach ($d in $dirs) { New-Item -ItemType Directory -Path $d -Force }

# 移动现有文件到子目录
# (具体移动命令根据5.1查看的实际结构调整)
```

#### 5.3 同步更新pages.json

每个移动的文件都需要同步更新pages.json中的路径。

#### Phase 5 验收

- [ ] 目录结构与UI美化目标一致
- [ ] pages.json路由全部更新
- [ ] 编译通过
- [ ] 所有coach页面在新路径下正常渲染

```powershell
git add -A
git commit -m "phase5: coach目录重构 — 子目录结构准备就绪"
```

---

### Phase 6: BOS UI集成 (1-2小时)

> 目标: 一次性集成11个美化页面
> 前提: Phase 1-5 全部通过

#### 6.1 从backup分支提取UI文件

```powershell
cd D:\behavioral-health-project

# 提取11个美化页面的最终版本（统一配置版）
git checkout backup-2026-0301-before-rollback -- "小程序版UI更新/src/pages/coach/"

# 逐个复制到正确位置
$source = "小程序版UI更新\src\pages\coach"
$target = "coach-miniprogram\src\pages\coach"

$files = @(
    "dashboard\index.vue",
    "flywheel\index.vue",
    "students\index.vue",
    "students\detail.vue",
    "risk\index.vue",
    "assessment\index.vue",
    "assessment\review.vue",
    "push-queue\index.vue",
    "analytics\index.vue",
    "messages\index.vue",
    "live\index.vue"
)

foreach ($f in $files) {
    $s = Join-Path $source $f
    $t = Join-Path $target $f
    if (Test-Path $s) {
        Copy-Item $s $t -Force
        Write-Host "✅ $f"
    } else {
        Write-Host "❌ 未找到: $f"
    }
}
```

#### 6.2 关键修改: 替换内联代码为统一模块

每个美化页面中如果还有内联的`_request()`和`_BASE`，替换为Phase 3建立的统一模块：

```powershell
# 检查是否有内联代码残留
Select-String -Path "src\pages\coach\**\*.vue" -Pattern "_request|_BASE|_getToken|localhost:800" -Recurse
```

如果有，需要批量替换。替换规则：

| 删除 | 替换为 |
|------|--------|
| `const _BASE = 'http://localhost:8002/api'` | (删除) |
| `function _getToken() { ... }` | (删除) |
| `function _request(url, method, data) { ... }` | (删除) |
| `_request('/v1/coach/xxx', 'GET')` | `http.get('/coach/xxx')` |
| 文件顶部添加 | `import { http } from '@/api/request'` 或子包相对路径 |

#### 6.3 pages.json路由注册

确保11个页面全部在pages.json中注册：

```json
{
  "subPackages": [{
    "root": "pages/coach",
    "pages": [
      {"path": "dashboard/index", "style": {"navigationBarTitleText": "工作台"}},
      {"path": "flywheel/index", "style": {"navigationBarTitleText": "AI飞轮"}},
      {"path": "students/index", "style": {"navigationBarTitleText": "学员管理"}},
      {"path": "students/detail", "style": {"navigationBarTitleText": "学员详情"}},
      {"path": "risk/index", "style": {"navigationBarTitleText": "风险管理"}},
      {"path": "assessment/index", "style": {"navigationBarTitleText": "评估管理"}},
      {"path": "assessment/review", "style": {"navigationBarTitleText": "评估审核"}},
      {"path": "push-queue/index", "style": {"navigationBarTitleText": "推送审批"}},
      {"path": "analytics/index", "style": {"navigationBarTitleText": "数据分析"}},
      {"path": "messages/index", "style": {"navigationBarTitleText": "消息"}},
      {"path": "live/index", "style": {"navigationBarTitleText": "直播"}}
    ]
  }]
}
```

#### 6.4 清理旧文件

```powershell
# 删除旧的平铺coach页面（如果还在）
$oldFiles = @("coach/dashboard.vue", "coach/push-queue.vue")
foreach ($f in $oldFiles) {
    $path = "src\pages\$f"
    if (Test-Path $path) {
        Remove-Item $path
        Write-Host "已清理: $f"
    }
}

# 清理提取的临时文件
Remove-Item -Recurse -Force "小程序版UI更新" -ErrorAction SilentlyContinue
```

#### 6.5 返回箭头修复

之前发现的返回箭头不可见问题，在集成时一并修复：

```powershell
# 将所有coach页面中的细Unicode箭头替换为uni.navigateBack
Select-String -Path "src\pages\coach\**\*.vue" -Pattern "←|‹|❮|navigateBack" -Recurse
```

建议统一使用`uni.navigateBack()`而非Unicode字符：

```vue
<view class="nav-back" @tap="uni.navigateBack()">
  <text style="font-size:36rpx;font-weight:bold;">＜</text>
  <text>返回</text>
</view>
```

#### Phase 6 验收

- [ ] 11个美化页面全部到位
- [ ] 无内联_request代码残留
- [ ] pages.json路由全部注册
- [ ] 编译零错误
- [ ] 每个页面在微信开发者工具中正常渲染
- [ ] 返回箭头可见
- [ ] 无/v1/professional/幽灵请求
- [ ] BOS设计体系正确呈现 (毛玻璃/渐变/呼吸灯)

```powershell
git add -A
git commit -m "phase6: BOS UI集成完成 — 11个美化页面一次性到位"
git tag bos-ui-integrated-v1
```

---

### Phase 7: 最终回归测试 (1小时)

> 目标: 全面确认功能100% + 稳定性

#### 7.1 编译+全页面浏览

```powershell
Remove-Item -Recurse -Force dist
npm run dev:mp-weixin
```

在微信开发者工具中逐一打开所有页面，检查console无错误。

#### 7.2 端到端场景测试

| 场景 | 步骤 | 期望结果 |
|------|------|----------|
| Grower登录→首页 | 输入grower/Grower@2026 → 登录 | 显示成长者首页+数据 |
| Coach登录→工作台 | 输入coach/Coach@2026 → 登录 | 显示BOS美化工作台 |
| Coach→学员列表 | 点击学员管理 | 学员列表加载+风险标签 |
| Coach→学员详情 | 点击某学员 | 大五人格条+BPT6标签+聊天气泡 |
| Coach→飞轮 | 点击AI飞轮 | 审核队列展示(不测AI生成按钮) |
| Coach→风险 | 点击风险管理 | R0-R4色级+呼吸灯 |
| Coach→分析 | 点击数据分析 | 统计卡+CSS饼图 |
| 返回导航 | 每个页面点返回 | 正确返回上一页 |
| Token过期 | (可选)手动清除token后操作 | 自动跳转登录页 |

#### 7.3 后端API完整烟测

重新运行Phase 4的烟测脚本，确认与UI集成后没有引入新的API问题。

#### 7.4 生成最终状态报告

```powershell
# 统计
Write-Host "=== 最终状态 ==="
Write-Host "分支: $(git branch --show-current)"
Write-Host "HEAD: $(git log --oneline -1)"
Write-Host "页面总数: $((Get-ChildItem -Path src\pages -Recurse -Filter '*.vue').Count)"
Write-Host "Coach美化页面: $((Get-ChildItem -Path src\pages\coach -Recurse -Filter '*.vue').Count)"
Write-Host "API模块: $((Get-ChildItem -Path src\api -Filter '*.ts').Count)"
Write-Host "编译产物: $(if(Test-Path dist\dev\mp-weixin){'✅ 存在'}else{'❌ 缺失'})"
```

```powershell
git add -A
git commit -m "phase7: 最终回归测试通过 — 功能100%+BOS UI+稳定"
git tag stable-bos-v1.0
```

---

## 三、上线前收尾清单

Phase 7通过后，上线前还需:

| # | 事项 | 说明 |
|---|------|------|
| 1 | API Base切换生产地址 | 修改.env.production中的VITE_API_URL |
| 2 | 生产构建 | `npm run build:mp-weixin` |
| 3 | 微信小程序体验版上传 | 通过微信开发者工具上传 |
| 4 | 后端11个API端点可用性 | 参考SESSION-SUMMARY中的API依赖表 |
| 5 | merge回master | `git checkout master && git merge stable-bos-v1.0` |
| 6 | push | `git push origin master --tags` |

---

## 四、执行时间线总览

| Phase | 内容 | 预计时间 | 累计 |
|-------|------|----------|------|
| 0 | 基线验证 | 30分钟 | 0.5h |
| 1 | 基础设施加固 | 1-2小时 | 2.5h |
| 2 | 子包依赖根治 | 1-2小时 | 4.5h |
| 3 | HTTP模块统一 | 1小时 | 5.5h |
| 4 | 功能完整性验证 | 1小时 | 6.5h |
| 5 | 目录重构 | 30分钟 | 7h |
| 6 | BOS UI集成 | 1-2小时 | 9h |
| 7 | 最终回归 | 1小时 | 10h |

**总计: 约8-10小时，可分2-3个工作session完成。**

建议断点:
- Session 1: Phase 0-3 (基座稳定化)
- Session 2: Phase 4-6 (功能恢复+UI集成)
- Session 3: Phase 7 (最终验收)

---

## 五、与之前加工过程的关键差异

| 维度 | 之前(发现问题的过程) | 这次(稳定化推进) |
|------|----------------------|------------------|
| **端口** | 8000/8002混用，边发现边改 | Phase 1一次性统一为8000 |
| **request模块** | 先内联→再统一→变双份 | Phase 3一步到位，唯一模块 |
| **子包依赖** | 用内联绕过，未真正解决 | Phase 2从根本上解决 |
| **UI集成** | 边部署边修bug，11次× | Phase 6一次性集成，零修补 |
| **Docker** | 双Stack同时跑，发现冲突才处理 | Phase 1提前治理 |
| **编译缓存** | 幽灵路径反复出现 | 每个Phase开始时清理dist |
| **pages.json** | 分3次修改路由 | Phase 5+6一次性完成 |
| **验证** | 改完才测 | 每个Phase结束都验证+提交 |
