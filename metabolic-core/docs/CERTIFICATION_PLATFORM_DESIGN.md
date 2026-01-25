# 教练认证平台 · 技术架构设计

> 混合方案：自建管理后台 + 云端视频/直播服务

---

## 一、系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户端 (学员/教练)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  H5 网页端   │  │  微信小程序  │  │   PC 网页   │  │  移动APP    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Gateway (Nginx)                            │
└─────────────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐
│  Admin Backend  │  │ Learning Backend│  │   Metabolic Core (现有)      │
│  (管理后台API)   │  │  (学习系统API)  │  │  - 认证服务                  │
│  - 课程管理      │  │  - 学习进度     │  │  - 晋级引擎                  │
│  - 考试管理      │  │  - 视频播放     │  │  - 知识库                    │
│  - 用户管理      │  │  - 直播互动     │  │  - 干预规划                  │
│  - 数据统计      │  │  - 在线考试     │  │                             │
└────────┬────────┘  └────────┬────────┘  └─────────────┬───────────────┘
         │                    │                         │
         └────────────────────┴─────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         数据层 & 第三方服务                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │PostgreSQL│  │  Redis   │  │ 阿里云OSS    │  │  阿里云视频服务      │ │
│  │ (主数据库)│  │ (缓存)   │  │ (文件存储)   │  │  - VOD (点播)       │ │
│  └──────────┘  └──────────┘  └──────────────┘  │  - Live (直播)      │ │
│                                                │  - RTC (实时互动)   │ │
│                                                └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 二、管理后台设计

### 2.1 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | Vue 3 + Vite | 与现有H5项目保持一致 |
| UI组件库 | Ant Design Vue / Element Plus | 企业级后台组件 |
| 后端框架 | FastAPI (Python) | 与现有项目统一 |
| 数据库 | PostgreSQL | 企业级关系数据库 |
| 缓存 | Redis | 会话、热数据缓存 |
| 文件存储 | 阿里云 OSS | 课件、附件存储 |

### 2.2 后台功能模块

```
管理后台
├── 首页仪表盘
│   ├── 学员统计 (注册/活跃/完成)
│   ├── 课程数据 (播放量/完成率)
│   ├── 考试数据 (通过率/平均分)
│   └── 收入统计 (课程收入/认证费)
│
├── 课程管理
│   ├── 课程列表 (CRUD)
│   ├── 章节管理
│   ├── 视频上传 (对接阿里云VOD)
│   ├── 课件上传 (PDF/PPT)
│   ├── 课程定价
│   └── 上架/下架
│
├── 直播管理
│   ├── 直播间创建
│   ├── 直播日程
│   ├── 回放管理
│   ├── 互动数据 (弹幕/问答)
│   └── 直播统计
│
├── 考试管理
│   ├── 题库管理
│   │   ├── 单选题
│   │   ├── 多选题
│   │   ├── 判断题
│   │   ├── 简答题
│   │   └── 实操题 (上传录音/视频/报告)
│   ├── 试卷组卷
│   │   ├── 手动组卷
│   │   └── 随机抽题
│   ├── 考试安排
│   │   ├── 考试时间
│   │   ├── 防作弊设置
│   │   └── 补考规则
│   └── 成绩管理
│       ├── 自动评分
│       ├── 人工评分 (实操题)
│       └── 成绩发布
│
├── 学员管理
│   ├── 学员列表
│   ├── 学习记录
│   ├── 考试记录
│   ├── 认证进度
│   └── 学员分组
│
├── 教练管理
│   ├── 教练列表
│   ├── 等级管理
│   ├── 晋级审核
│   ├── 案例审核
│   └── 权限配置
│
├── 内容管理
│   ├── 资讯文章
│   ├── 知识库
│   └── 常见问题
│
└── 系统设置
    ├── 角色权限
    ├── 操作日志
    ├── 系统参数
    └── 云服务配置
```

---

## 三、视频课程系统

### 3.1 录播课程 (阿里云VOD)

**上传流程:**
```
管理后台 → 获取上传凭证 → 直传阿里云OSS → 自动转码 → 生成播放地址
```

**播放功能:**
- 自适应码率 (360P/480P/720P/1080P)
- 防盗链 (Referer/鉴权)
- 进度记忆
- 倍速播放 (0.5x ~ 2x)
- 播放统计

**费用估算 (阿里云VOD):**
| 项目 | 单价 | 说明 |
|------|------|------|
| 存储 | ¥0.02/GB/天 | 原始视频+转码后 |
| 转码 | ¥0.003~0.01/分钟 | 按清晰度 |
| 流量 | ¥0.24/GB | 外网播放 |
| CDN加速 | ¥0.15/GB | 推荐使用 |

### 3.2 直播课程 (阿里云Live/RTC)

**直播类型:**

| 类型 | 技术方案 | 延迟 | 互动能力 | 适用场景 |
|------|----------|------|----------|----------|
| 标准直播 | RTMP推流 | 3-5秒 | 弹幕/打赏 | 大班公开课 |
| 低延迟直播 | RTS | <1秒 | 实时问答 | 小班互动课 |
| 实时互动 | WebRTC(RTC) | <400ms | 连麦/白板 | 1对1辅导/答辩 |

**直播功能矩阵:**
```
基础功能
├── 讲师推流 (OBS/手机/网页)
├── 学员观看 (H5/小程序/APP)
├── 实时弹幕
├── 在线人数统计
└── 直播回放

互动功能
├── 举手连麦
├── 屏幕共享
├── 互动白板
├── 在线问答
└── 随堂测验

管理功能
├── 禁言/踢人
├── 公告推送
├── 直播录制
└── 数据统计
```

---

## 四、在线考试系统

### 4.1 题库系统

**题型支持:**

```typescript
// 题目类型定义
type QuestionType =
  | 'single_choice'     // 单选题
  | 'multi_choice'      // 多选题
  | 'true_false'        // 判断题
  | 'fill_blank'        // 填空题
  | 'short_answer'      // 简答题
  | 'essay'             // 论述题
  | 'case_analysis'     // 案例分析
  | 'audio_response'    // 录音回答 (MI话术)
  | 'video_response'    // 录像回答 (教练对话)
  | 'file_upload';      // 文件上传 (案例报告)

interface Question {
  question_id: string;
  type: QuestionType;
  content: string;           // 题目内容 (支持富文本)
  options?: Option[];        // 选项 (选择题)
  answer?: string | string[]; // 标准答案
  explanation?: string;      // 解析
  points: number;            // 分值
  difficulty: 1 | 2 | 3 | 4 | 5;  // 难度
  tags: string[];            // 标签 (知识点)
  rubric?: ScoringRubric;    // 评分规则 (主观题)
}
```

### 4.2 防作弊机制

**技术方案:**

| 功能 | 实现方式 | 说明 |
|------|----------|------|
| 人脸识别 | 阿里云人脸核身 | 考前身份验证 |
| 活体检测 | 阿里云金融级活体 | 防照片/视频攻击 |
| 考中抓拍 | 定时截屏 | 随机间隔抓拍保存 |
| 切屏检测 | Page Visibility API | 检测离开考试页面 |
| 复制禁用 | JS事件拦截 | 禁止复制/粘贴 |
| 全屏模式 | Fullscreen API | 强制全屏作答 |
| IP限制 | 后端校验 | 同一IP多次登录告警 |
| 时间限制 | 前后端双重校验 | 超时自动提交 |

**违规处理:**
```
警告级别:
- 切屏1次 → 提示警告
- 切屏3次 → 强制提交

严重级别:
- 人脸不匹配 → 暂停考试 + 人工审核
- 多设备登录 → 强制下线 + 标记异常
```

### 4.3 实操评估

**录音评估 (MI动机访谈):**
```
1. 系统播放模拟客户音频
2. 学员录制回应 (限时30-60秒)
3. 上传至OSS
4. 督导人工评分 (维度: 共情/反映/开放提问/总结)
```

**录像评估 (教练对话):**
```
1. 给定案例背景
2. 学员录制角色扮演视频 (3-5分钟)
3. 督导按评分表打分
4. 系统辅助: 语音转文字 + 关键词检测
```

**案例报告评估:**
```
1. 提交完整干预报告 (Word/PDF)
2. 结构检查 (自动): 章节完整性
3. 查重检测: 接入论文查重API
4. 人工评审: 多维度评分表
```

---

## 五、数据库设计 (核心表)

```sql
-- 课程表
CREATE TABLE courses (
    course_id UUID PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    level VARCHAR(10),  -- L0/L1/L2/L3
    category VARCHAR(50),  -- knowledge/method/skill/value
    cover_url VARCHAR(500),
    duration_minutes INT,
    price DECIMAL(10,2),
    status VARCHAR(20),  -- draft/published/offline
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- 章节表
CREATE TABLE chapters (
    chapter_id UUID PRIMARY KEY,
    course_id UUID REFERENCES courses(course_id),
    title VARCHAR(200),
    sequence INT,
    video_id VARCHAR(100),  -- 阿里云VOD视频ID
    video_url VARCHAR(500),
    duration_seconds INT,
    attachments JSONB  -- [{name, url, type}]
);

-- 学习进度表
CREATE TABLE learning_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    chapter_id UUID REFERENCES chapters(chapter_id),
    progress_percent INT,  -- 0-100
    last_position INT,  -- 秒
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 直播表
CREATE TABLE live_sessions (
    live_id UUID PRIMARY KEY,
    title VARCHAR(200),
    host_id UUID,  -- 讲师ID
    scheduled_at TIMESTAMP,
    duration_minutes INT,
    stream_url VARCHAR(500),
    playback_url VARCHAR(500),
    status VARCHAR(20),  -- scheduled/live/ended
    max_viewers INT,
    actual_viewers INT
);

-- 题库表
CREATE TABLE questions (
    question_id UUID PRIMARY KEY,
    type VARCHAR(30),
    content TEXT,
    options JSONB,
    answer JSONB,
    explanation TEXT,
    points INT,
    difficulty INT,
    tags VARCHAR[],
    rubric JSONB,  -- 评分规则
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 试卷表
CREATE TABLE exams (
    exam_id UUID PRIMARY KEY,
    title VARCHAR(200),
    level VARCHAR(10),
    exam_type VARCHAR(30),  -- theory/case_simulation/dialogue
    questions JSONB,  -- [{question_id, points}]
    total_points INT,
    pass_score INT,
    duration_minutes INT,
    anti_cheat_config JSONB,
    status VARCHAR(20)
);

-- 考试记录表
CREATE TABLE exam_attempts (
    attempt_id UUID PRIMARY KEY,
    exam_id UUID REFERENCES exams(exam_id),
    user_id UUID,
    started_at TIMESTAMP,
    submitted_at TIMESTAMP,
    answers JSONB,  -- [{question_id, answer, auto_score}]
    auto_score INT,
    manual_score INT,
    final_score INT,
    passed BOOLEAN,
    violations JSONB,  -- 违规记录
    screenshots JSONB,  -- 抓拍记录
    reviewed_by UUID,
    reviewed_at TIMESTAMP
);

-- 实操提交表
CREATE TABLE practical_submissions (
    submission_id UUID PRIMARY KEY,
    exam_id UUID,
    user_id UUID,
    question_id UUID,
    file_type VARCHAR(20),  -- audio/video/document
    file_url VARCHAR(500),
    duration_seconds INT,
    transcript TEXT,  -- 语音转文字
    scores JSONB,  -- [{dimension, score, feedback}]
    total_score INT,
    reviewer_id UUID,
    reviewed_at TIMESTAMP
);
```

---

## 六、阿里云服务配置

### 6.1 视频点播 (VOD)

**开通步骤:**
1. 阿里云控制台 → 视频点播
2. 开通服务 → 选择计费方式 (按量/包年)
3. 配置转码模板 (推荐: 标清+高清+超清)
4. 配置域名 + CDN加速
5. 获取AccessKey

**SDK集成:**
```bash
npm install @alicloud/pop-core
npm install ali-oss
```

### 6.2 直播服务 (Live)

**开通步骤:**
1. 阿里云控制台 → 视频直播
2. 添加推流域名 + 播放域名
3. 配置鉴权 (防盗链)
4. 开启录制 (自动保存回放)

### 6.3 实时音视频 (RTC)

**适用场景:** 连麦互动、1对1辅导、在线答辩

**开通步骤:**
1. 阿里云控制台 → 音视频通信RTC
2. 创建应用 → 获取AppID
3. 集成Web SDK

---

## 七、实施路线图

### Phase 1: 基础搭建 (2周)

- [ ] PostgreSQL数据库部署
- [ ] 管理后台框架搭建 (Vue3 + Ant Design)
- [ ] 用户认证系统 (JWT)
- [ ] 课程CRUD接口

### Phase 2: 视频系统 (2周)

- [ ] 阿里云VOD集成
- [ ] 视频上传组件
- [ ] 播放器集成 (Aliplayer)
- [ ] 学习进度追踪

### Phase 3: 考试系统 (3周)

- [ ] 题库管理模块
- [ ] 组卷系统
- [ ] 考试引擎 (防作弊)
- [ ] 自动评分 + 人工评分

### Phase 4: 直播系统 (2周)

- [ ] 直播管理模块
- [ ] 推流/播放集成
- [ ] 互动功能 (弹幕/问答)
- [ ] 回放管理

### Phase 5: 实操评估 (2周)

- [ ] 录音/录像组件
- [ ] 文件上传
- [ ] 评分工作台
- [ ] 语音转文字集成

### Phase 6: 上线优化 (1周)

- [ ] 性能优化
- [ ] 安全审计
- [ ] 数据备份
- [ ] 监控告警

---

## 八、成本估算 (月)

| 项目 | 费用估算 | 说明 |
|------|----------|------|
| 云服务器 | ¥500-1000 | 2-4核8G |
| 数据库RDS | ¥300-500 | PostgreSQL |
| Redis | ¥100-200 | 缓存 |
| OSS存储 | ¥50-200 | 按用量 |
| VOD视频 | ¥500-2000 | 按播放量 |
| 直播服务 | ¥200-1000 | 按使用时长 |
| CDN | ¥200-500 | 按流量 |
| **合计** | **¥1850-5400** | |

---

## 九、下一步行动

1. **确认云服务账号** - 是否已有阿里云账号？
2. **确认技术栈** - 后端用Python(FastAPI)还是Node.js(Express)？
3. **确认优先级** - 先实现哪个模块？(建议: 管理后台 → 录播 → 考试 → 直播)
4. **确认团队** - 是否有前端/后端开发人员协助？

---

*文档版本: v1.0*
*更新时间: 2026-01-24*
