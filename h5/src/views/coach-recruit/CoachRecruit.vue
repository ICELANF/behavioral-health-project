<template>
  <!--
    coach-recruit/index.vue
    路由: /coach-recruit  （新增到 h5/src/router/index.ts）
    对应文档: 平台教练体系全景-20260225.md
    权威数据:
      角色层级 → api/coach_api.py _ROLE_LEVEL_MAP
      晋级阈值 → api/paths_api.py _LEVEL_THRESHOLDS
      教练认证升级条件 → api/coach_api.py _UPGRADE_REQ
      申请接口 → POST /api/v1/coach/promotion-applications
  -->
  <div class="coach-recruit">

    <!-- ── Hero ───────────────────────────────────────── -->
    <div class="hero">
      <div class="hero-eyebrow">🎯 COACH SYSTEM · 教练体系</div>
      <h1 class="hero-title">
        行健教练队伍建设<br />
        <span class="hero-sub">L0 → L5 · 六级晋级 · AI 人机协同</span>
      </h1>
      <p class="hero-desc">
        教练体系是 AI 与用户之间的 <strong>人机协同桥梁</strong>。<br />
        34+ API · 7 ORM 模型 · 4 核心服务 · 20+ 前端组件
      </p>
      <div class="hero-stats">
        <div v-for="s in stats" :key="s.label" class="stat-item">
          <span class="stat-val">{{ s.val }}</span>
          <span class="stat-label">{{ s.label }}</span>
        </div>
      </div>
    </div>

    <!-- ── 角色层级横条 ────────────────────────────────── -->
    <div class="level-strip">
      <div v-for="(lv, idx) in levels" :key="lv.key" class="level-node">
        <div class="level-circle" :style="{ borderColor: lv.color, background: lv.color+'18' }">
          <span class="level-emoji">{{ lv.emoji }}</span>
        </div>
        <div class="level-key" :style="{ color: lv.color }">{{ lv.key }}</div>
        <div class="level-name">{{ lv.label }}</div>
        <div v-if="idx < levels.length - 1" class="level-arrow">→</div>
      </div>
    </div>

    <!-- ── Tab Nav ────────────────────────────────────── -->
    <div class="tab-nav">
      <button
        v-for="tb in tabs"
        :key="tb.key"
        :class="['tab-btn', { active: activeTab === tb.key }]"
        @click="activeTab = tb.key"
      >{{ tb.label }}</button>
    </div>

    <!-- ──────────── Tab: 成长路径 ──────────────────────── -->
    <div v-show="activeTab === 'journey'" class="tab-body">
      <div class="info-box blue">
        <b>成为教练的核心路径</b><br />
        任何用户均从 L0 观察员起步。到达 <b>L2 分享者</b>后，即可申请教练候选。
        通过认证考试（理论 + 技能 + 综合）并满足带教数量要求后，
        正式晋升为 <b>L3 行为健康教练</b>。
      </div>

      <div v-for="(step, i) in journey" :key="step.key" class="journey-wrap">
        <div
          class="journey-card"
          :class="{ expanded: openStep === i }"
          :style="{ '--sc': step.color }"
          @click="openStep = openStep === i ? -1 : i"
        >
          <!-- Header row -->
          <div class="journey-header">
            <div class="journey-icons">
              <div class="j-icon" :style="{ borderColor: step.fromColor+'50', background: step.fromColor+'15' }">
                <span>{{ step.fromEmoji }}</span>
                <span class="j-lv" :style="{ color: step.fromColor }">{{ step.from }}</span>
              </div>
              <span class="j-arrow">→</span>
              <div class="j-icon" :style="{ borderColor: step.color+'50', background: step.color+'15' }">
                <span>{{ step.toEmoji }}</span>
                <span class="j-lv" :style="{ color: step.color }">{{ step.to }}</span>
              </div>
            </div>
            <div class="journey-meta">
              <div class="journey-title">
                {{ step.title }}
                <span v-if="step.needExam" class="badge-exam">需考试</span>
              </div>
              <div class="journey-desc">{{ step.desc }}</div>
            </div>
            <span class="j-toggle">{{ openStep === i ? '▼' : '▶' }}</span>
          </div>

          <!-- Detail -->
          <transition name="expand">
            <div v-if="openStep === i" class="journey-detail">
              <div class="detail-grid">
                <!-- Points -->
                <div class="detail-box" :style="{ background: step.color+'12' }">
                  <div class="detail-box-title" :style="{ color: step.color }">📊 积分要求</div>
                  <div v-for="(v, k) in step.points" :key="k" class="detail-row">
                    <span>{{ { G: '成长点(G)', C: '贡献点(C)', I: '影响力(I)' }[k] }}</span>
                    <b :style="{ color: step.color }">≥ {{ v }}</b>
                  </div>
                  <div v-if="step.peers" class="detail-row">
                    <span>同道者</span>
                    <b :style="{ color: step.color }">{{ step.peers }}</b>
                  </div>
                </div>
                <!-- Coach reqs -->
                <div class="detail-box gray">
                  <div class="detail-box-title blue">🎯 教练要求</div>
                  <div v-for="r in step.coachReqs" :key="r" class="detail-row-dot">• {{ r }}</div>
                </div>
              </div>
              <!-- Notes -->
              <div class="detail-note" :style="{ borderColor: step.color }">
                <div v-if="step.trustNote">{{ step.trustNote }}</div>
                <div v-if="step.examNote" class="note-warn">⚠ {{ step.examNote }}</div>
                <div v-if="step.ironLaw" class="note-iron">🔒 {{ step.ironLaw }}</div>
              </div>
            </div>
          </transition>
        </div>
        <div v-if="i < journey.length - 1" class="step-connector">↕</div>
      </div>
    </div>

    <!-- ──────────── Tab: 工作铁律 ──────────────────────── -->
    <div v-show="activeTab === 'ironlaw'" class="tab-body">
      <div class="info-box orange">
        <b>核心铁律：AI → 教练审核 → 推送</b><br />
        所有 AI 生成的建议、处方、推送，必须先进入 <code>CoachPushQueue</code>，
        经教练在工作台审核修改后才可推送给用户。
        <b style="color:#E65100">绝不允许 AI 内容直接触达用户。</b>
      </div>

      <!-- Push workflow -->
      <div class="section-card">
        <div class="section-title">推送审批完整流程</div>
        <div v-for="fl in flow" :key="fl.step" class="flow-item">
          <div class="flow-dot" :style="{ background: fl.color+'20', borderColor: fl.color+'40', color: fl.color }">
            {{ fl.step }}
          </div>
          <div class="flow-text">{{ fl.text }}</div>
        </div>
      </div>

      <!-- Status machine -->
      <div class="section-card">
        <div class="section-title">推送状态机</div>
        <div class="status-chain">
          <span v-for="(s, i) in statusMachine" :key="s.label" class="status-node-wrap">
            <span class="status-node" :style="{ background: s.color+'15', color: s.color, borderColor: s.color+'30' }">
              {{ s.label }}
            </span>
            <span v-if="i < statusMachine.length - 1" class="status-arrow">→</span>
          </span>
        </div>
        <div class="status-note">超时72小时 → pending 自动变 expired（定时任务清理）</div>
      </div>

      <!-- Push source types (11) -->
      <div class="section-card">
        <div class="section-title">推送来源类型（11种）</div>
        <div class="push-tags">
          <span v-for="s in pushSources" :key="s.key" class="push-tag" :class="s.cls">
            {{ s.label }}
          </span>
        </div>
      </div>

      <!-- 4 iron laws -->
      <div v-for="law in ironLaws" :key="law.title" class="iron-card" :style="{ borderColor: law.color }">
        <div class="iron-header">
          <span class="iron-icon">{{ law.icon }}</span>
          <span class="iron-title" :style="{ color: law.color }">{{ law.title }}</span>
        </div>
        <div class="iron-desc">{{ law.desc }}</div>
      </div>
    </div>

    <!-- ──────────── Tab: AI 工具 ──────────────────────── -->
    <div v-show="activeTab === 'aitools'" class="tab-body">
      <div class="info-box blue">
        <b>双轨 AI 策略</b>：规则引擎（始终运行）+ LLM 增强（可用时激活，5分钟冷却，永不阻塞主流程）。<br />
        云优先（DeepSeek/Qwen）→ Ollama fallback，超时 25s。
      </div>
      <div v-for="tool in aiTools" :key="tool.name" class="ai-card">
        <span class="ai-icon">{{ tool.icon }}</span>
        <div class="ai-body">
          <div class="ai-name">{{ tool.name }}</div>
          <div class="ai-desc">{{ tool.desc }}</div>
          <span class="ai-badge">{{ tool.priority }}</span>
        </div>
      </div>
      <!-- Copilot logic -->
      <div class="section-card" style="margin-top:12px">
        <div class="section-title">CoachCopilotAgent 触发逻辑</div>
        <pre class="code-block">
关键词: 教练/学员/报告/周报/预警/异常/处方/干预/微行动/建议/指导

触发场景:
  血糖 >11.1 或 <3.9  → 高风险预警（HIGH, 置信度0.9）
  睡眠 <5h            → 睡眠告警
  HRV <20ms           → 生理预警
  依从率 <30%         → 超高强度干预建议
  依从率 <60%         → 处方复查建议

优先级: P2  |  权重: 0.85  |  Domain: COACHING
        </pre>
      </div>
    </div>

    <!-- ──────────── Tab: 绩效体系 ──────────────────────── -->
    <div v-show="activeTab === 'kpi'" class="tab-body">
      <div class="section-card">
        <div class="section-title">KPI 维度（CoachKpiMetric，日/周/月）</div>
        <div class="kpi-grid">
          <div v-for="k in kpiDims" :key="k.key" class="kpi-item">
            <span class="kpi-icon">{{ k.icon }}</span>
            <div class="kpi-label">{{ k.label }}</div>
            <div class="kpi-unit">{{ k.unit }}</div>
          </div>
        </div>
      </div>

      <div class="info-box yellow">
        <b>⚡ 自动升级（08:00定时任务）</b><br />
        每日检测无教练学员，自动创建 CoachPushQueue 条目通知督导介入。
        KPI 状态 red → auto_escalated = true，自动推送给督导。
      </div>

      <!-- Trust score -->
      <div class="section-card">
        <div class="section-title">信任分六信号模型</div>
        <div v-for="s in trustSignals" :key="s.signal" class="trust-row">
          <div class="trust-weight" :style="{ color: '#1565C0' }">{{ s.weight }}</div>
          <div class="trust-bar-wrap">
            <div class="trust-bar" :style="{ width: s.weight, background: 'linear-gradient(90deg,#1565C0,#42A5F5)' }"/>
          </div>
          <div class="trust-signal">{{ s.signal }}</div>
          <div class="trust-note">{{ s.note }}</div>
        </div>
        <div class="trust-levels">
          <div v-for="t in trustLevels" :key="t.level" class="trust-level-tag"
            :style="{ background: t.color+'12', borderColor: t.color+'30', color: t.color }">
            <b>{{ t.range }}</b> · {{ t.level }}<br/>
            <span style="font-size:10px;opacity:0.8">{{ t.action }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ──────────── Tab: 立即申请 ──────────────────────── -->
    <div v-show="activeTab === 'apply'" class="tab-body">
      <div class="section-card">
        <div class="section-title">🚀 申请教练候选（需达到 L2 分享者）</div>
        <div class="form-group">
          <label>当前阶段</label>
          <select v-model="form.stage">
            <option>L0 观察员</option>
            <option>L1 成长者</option>
            <option>L2 分享者</option>
          </select>
        </div>
        <div class="form-group">
          <label>健康改变经历</label>
          <textarea v-model="form.story" placeholder="描述你经历的健康挑战和改变（100字以上），作为教练资质审核依据..." />
        </div>
        <div class="form-group">
          <label>期望专科方向</label>
          <select v-model="form.domain">
            <option v-for="d in domains" :key="d">{{ d }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>推荐人用户名（可选）</label>
          <input v-model="form.referrer" placeholder="Coach/Supervisor 用户名，有推荐可加速审核" />
        </div>
        <van-button type="primary" block round @click="submitApply" :loading="submitting">
          提交申请 → POST /api/v1/coach/promotion-applications
        </van-button>
        <p class="form-hint">提交前请确认已达到 L2 分享者（信任分 established ≥50%）</p>
      </div>

      <!-- Openings -->
      <div class="section-card">
        <div class="section-title">📢 当前急需专向</div>
        <div v-for="item in openings" :key="item.domain" class="opening-row">
          <div class="opening-body">
            <div class="opening-header">
              <span class="opening-name">{{ item.domain }}</span>
              <span v-if="item.urgent" class="urgent-tag">急需</span>
            </div>
            <div class="opening-desc">{{ item.desc }}</div>
          </div>
          <div class="opening-slots">
            <div class="slots-num">{{ item.count }}</div>
            <div class="slots-label">名额</div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { showToast } from 'vant'
import { coachApi } from '@/api/coach-api'

// ── 权威数据（对应 api/paths_api.py + api/coach_api.py） ─────────────
const levels = [
  { key: 'L0', label: '观察员',        emoji: '👀', color: '#8c8c8c' },
  { key: 'L1', label: '成长者',        emoji: '🌱', color: '#1890ff' },
  { key: 'L2', label: '分享者',        emoji: '💬', color: '#52c41a' },
  { key: 'L3', label: '行为健康教练',   emoji: '🎯', color: '#faad14' },
  { key: 'L4', label: '行为健康促进师', emoji: '⭐', color: '#722ed1' },
  { key: 'L5', label: '大师',          emoji: '🏆', color: '#eb2f96' },
]

const stats = [
  { val: '34+', label: 'API端点' }, { val: '7',   label: 'ORM模型' },
  { val: '4',   label: '核心服务' }, { val: '20+', label: '前端组件' },
  { val: '11',  label: '推送来源类型' },{ val: '3',  label: '定时任务' },
]

const journey = [
  {
    key: 'L0→L1', from: 'L0', to: 'L1',
    fromEmoji: '👀', toEmoji: '🌱',
    fromColor: '#8c8c8c', color: '#1890ff',
    title: '从观察到行动',
    desc: '完成首次行为评估，开始打卡养成',
    points: { G: 100 },
    peers: null, needExam: false,
    coachReqs: ['带教学员 ≥ 5人', '发送消息 ≥ 20条'],
    trustNote: '信任分需达到 building 阶段（≥30%）',
  },
  {
    key: 'L1→L2', from: 'L1', to: 'L2',
    fromEmoji: '🌱', toEmoji: '💬',
    fromColor: '#1890ff', color: '#52c41a',
    title: '从个人到社区',
    desc: '行为稳定后开始影响他人，贡献内容',
    points: { G: 500, C: 50 },
    peers: null, needExam: false,
    coachReqs: ['带教学员 ≥ 15人', '发送消息 ≥ 100条', '完成评估 ≥ 30次'],
    trustNote: '信任分需达到 established（≥50%）',
  },
  {
    key: 'L2→L3', from: 'L2', to: 'L3',
    fromEmoji: '💬', toEmoji: '🎯',
    fromColor: '#52c41a', color: '#faad14',
    title: '★ 成为行为健康教练',
    desc: '通过认证考试，开始正式带教学员，进入 AI 审核工作流',
    points: { G: 800, C: 200, I: 50 },
    peers: '4个L1同道者', needExam: true,
    coachReqs: ['带教学员 ≥ 30人', '发送消息 ≥ 300条', '完成评估 ≥ 100次', '改善学员 ≥ 10人'],
    trustNote: '需要 4个L1同道者推荐 + 通过认证考试（理论+技能+综合三维评分）',
    examNote: '考试由 Supervisor 出题，coach_exam_records 表记录每次考试结果',
    ironLaw: '成为教练后，所有AI建议必须经你在 CoachPushQueue 中审核才能推送（铁律不可绕过）',
  },
  {
    key: 'L3→L4', from: 'L3', to: 'L4',
    fromEmoji: '🎯', toEmoji: '⭐',
    fromColor: '#faad14', color: '#722ed1',
    title: '从教练到行为健康促进师',
    desc: '系统放大器，管理更大范围的组织与区域推动',
    points: { G: 1500, C: 600, I: 200 },
    peers: '4个L2同道者', needExam: true,
    coachReqs: ['带教学员 ≥ 50人', '发送消息 ≥ 500条', '改善学员 ≥ 25人'],
    trustNote: '需要 4个L2同道者 + 通过促进师认证考试',
  },
  {
    key: 'L4→L5', from: 'L4', to: 'L5',
    fromEmoji: '⭐', toEmoji: '🏆',
    fromColor: '#722ed1', color: '#eb2f96',
    title: '大师 · 学科文明层',
    desc: '理论范式与传承者，平台最高专业级别',
    points: { G: 3000, C: 1500, I: 600 },
    peers: '4个L3同道者', needExam: true,
    coachReqs: ['带教学员 ≥ 100人', '发送消息 ≥ 1000条', '改善学员 ≥ 50人'],
    trustNote: '需要 4个L3同道者 + 通过大师认证考试',
  },
]

const flow = [
  { step: '1', text: 'AI推荐引擎生成建议（push_recommendation_service）',                                  color: '#1890ff' },
  { step: '2', text: '进入 CoachPushQueue（coach_schema）→ status = "pending"',                          color: '#faad14' },
  { step: '3', text: '教练在工作台查看 · 修改内容 · 设定投递时间（CoachWorkbench）',                       color: '#722ed1' },
  { step: '4a',text: '审批通过 → 激活处方 → 生成每日任务 → WebSocket 推送通知',                           color: '#52c41a' },
  { step: '4b',text: '审批拒绝 → 记录退回原因（coach_review_logs 审计表）',                               color: '#F44336' },
  { step: '⏱', text: '72小时未处理 → 自动 expired（expire_stale_items 定时任务）',                       color: '#8c8c8c' },
]

const statusMachine = [
  { label: 'pending',  color: '#faad14' },
  { label: 'approved', color: '#52c41a' },
  { label: 'sent',     color: '#1890ff' },
]

const pushSources = [
  { key: 'challenge',          label: '挑战活动',    cls: '' },
  { key: 'device_alert',       label: '设备预警',    cls: 'warn' },
  { key: 'micro_action',       label: '微行动',      cls: '' },
  { key: 'ai_recommendation',  label: 'AI推荐',      cls: '' },
  { key: 'system',             label: '系统通知',    cls: '' },
  { key: 'coach_message',      label: '教练消息',    cls: '' },
  { key: 'coach_reminder',     label: '教练提醒',    cls: '' },
  { key: 'assessment_push',    label: '评估推送',    cls: '' },
  { key: 'micro_action_assign',label: '微行动分配',  cls: '' },
  { key: 'vision_rx',          label: '视力处方',    cls: 'green' },
  { key: 'xzb_expert',         label: '行诊智伴',    cls: 'gold' },
]

const ironLaws = [
  { icon: '🤖', color: '#F44336', title: 'AI→审核→推送（铁律）',
    desc: '所有 AI 生成的建议必须先经教练在 CoachPushQueue 中审核修改后才可推送给用户。绝不允许 AI 内容直接触达用户。' },
  { icon: '⚡', color: '#FF9800', title: 'CrisisAgent 优先级 0',
    desc: '危机信号由 CrisisAgent 最先拦截（优先级0），教练随后跟进。教练不能关闭 Crisis 通道。' },
  { icon: '📋', color: '#1890ff', title: '审批 72小时超时',
    desc: 'pending 项超过 72 小时自动变为 expired，避免过期内容推送给学员。' },
  { icon: '🔒', color: '#52c41a', title: '教练只管辖三类学员',
    desc: '教练只能管理 Observer(L0) / Grower(L1) / Sharer(L2)。_STUDENT_ROLES 权威定义。' },
]

const aiTools = [
  { icon: '🤖', name: 'CoachCopilotAgent',
    desc: '教练副驾驶 · 预警检查 + 学员状态 + 依从率干预 + 周报生成', priority: 'P2 · 权重0.85 · Domain: COACHING' },
  { icon: '💊', name: 'AI行为处方生成（copilot_prescription_service）',
    desc: 'SPI诊断 + 六因分析 + 处方生成，输出 diagnosis + prescription + ai_suggestions', priority: '云优先 · 超时25s · Ollama fallback' },
  { icon: '💡', name: 'AI消息建议（coach_ai_suggestion_service）',
    desc: '鼓励 / 提醒 / 建议 / 微行动 四类型，STAGE模板 + RISK模板 + 规则+LLM双轨', priority: '5分钟冷却 · 永不阻塞' },
  { icon: '📊', name: 'AI推送推荐引擎（push_recommendation_service）',
    desc: '设备信号 + 行为事实 + 画像 + 评估间隔，输出 PushRecommendation 列表', priority: '实时分析 · 自动入队' },
]

const kpiDims = [
  { key: 'active_client_count',       icon: '👥', label: '活跃学员数',   unit: '人' },
  { key: 'session_completion_rate',   icon: '📅', label: '课程完成率',   unit: '%' },
  { key: 'client_retention_rate',     icon: '🔄', label: '学员留存率',   unit: '%' },
  { key: 'stage_advancement_rate',    icon: '📈', label: '阶段晋级率',   unit: '%' },
  { key: 'assessment_coverage',       icon: '📋', label: '评估覆盖率',   unit: '%' },
  { key: 'intervention_adherence',    icon: '💊', label: '干预依从率',   unit: '%' },
  { key: 'client_satisfaction',       icon: '😊', label: '学员满意度',   unit: '分' },
  { key: 'safety_incident_count',     icon: '⚠', label: '安全事故数',   unit: '次' },
  { key: 'supervision_compliance',    icon: '🎓', label: '督导合规率',   unit: '%' },
  { key: 'knowledge_contribution',    icon: '📝', label: '知识贡献',     unit: '篇' },
]

const trustSignals = [
  { signal: '对话深度',    weight: '25%', note: 'avg(note_length) / 50' },
  { signal: '主动回归',    weight: '20%', note: 'consecutive_days / total_task_days' },
  { signal: '话题开放度',  weight: '15%', note: 'distinct_tags / 6' },
  { signal: '情绪表达',    weight: '15%', note: 'emotion_notes / total_notes' },
  { signal: '信息分享',    weight: '15%', note: 'rich_checkins / total_checkins' },
  { signal: '好奇心',      weight: '10%', note: 'notes_present / total' },
]

const trustLevels = [
  { level: 'not_established', range: '<30%',   color: '#F44336', action: '禁止行为建议' },
  { level: 'building',        range: '30-50%', color: '#FF9800', action: '温和引入评估' },
  { level: 'established',     range: '>50%',   color: '#52c41a', action: '全面干预允许' },
]

const domains = ['青少年视力保护','代谢综合征管理','职场压力与睡眠','慢病逆转','情绪与行为管理']

const openings = [
  { domain: '青少年视力保护', count: 8, urgent: true,  desc: 'VisionGuard 专项，与眼科Expert协作，行诊智伴接入' },
  { domain: '代谢综合征管理', count: 5, urgent: true,  desc: '慢病逆转领域，AI处方生成辅助，需基础健康知识' },
  { domain: '职场压力与睡眠', count: 3, urgent: false, desc: '企业健康管理场景，数据驱动行为干预' },
]

const tabs = [
  { key: 'journey', label: '📈 成长路径' },
  { key: 'ironlaw', label: '🔒 工作铁律' },
  { key: 'aitools', label: '🤖 AI工具' },
  { key: 'kpi',     label: '📊 绩效体系' },
  { key: 'apply',   label: '🚀 立即申请' },
]

const activeTab = ref('journey')
const openStep  = ref(-1)
const submitting = ref(false)
const form = reactive({ stage: 'L2 分享者', story: '', domain: '', referrer: '' })

async function submitApply() {
  if (!form.story || form.story.length < 100) {
    showToast('请填写100字以上的健康改变经历')
    return
  }
  submitting.value = true
  try {
    await coachApi.applyPromotion({
      current_level: form.stage,
      story: form.story,
      target_domain: form.domain,
      referrer: form.referrer || undefined,
    })
    showToast({ type: 'success', message: '申请已提交，审核通常3-7个工作日' })
  } catch {
    showToast('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.coach-recruit { font-family: 'Noto Serif SC', serif; background: #F4F6FB; min-height: 100vh; }

/* Hero */
.hero { background: linear-gradient(135deg,#1B2A3B,#0D3B6B,#1565C0); padding: 36px 24px 44px; color: #fff; }
.hero-eyebrow { display: inline-block; background: rgba(255,255,255,0.13); border-radius: 20px; padding: 3px 14px; font-size: 10px; letter-spacing: 2px; margin-bottom: 14px; }
.hero-title { font-size: 28px; font-weight: 900; margin: 0 0 10px; line-height: 1.3; }
.hero-sub { color: #90CAF9; font-size: 18px; }
.hero-desc { font-size: 13px; opacity: 0.8; margin: 0 0 20px; line-height: 1.7; }
.hero-stats { display: flex; gap: 18px; flex-wrap: wrap; }
.stat-item { text-align: center; }
.stat-val { display: block; font-size: 22px; font-weight: 900; }
.stat-label { font-size: 10px; opacity: 0.65; }

/* Level strip */
.level-strip { background: #fff; border-bottom: 1px solid #eee; padding: 12px 16px; display: flex; overflow-x: auto; gap: 0; }
.level-node { display: flex; flex-direction: column; align-items: center; position: relative; padding: 0 10px; flex-shrink: 0; }
.level-circle { width: 34px; height: 34px; border-radius: 50%; border: 2px solid; display: flex; align-items: center; justify-content: center; margin-bottom: 3px; }
.level-emoji { font-size: 16px; }
.level-key { font-size: 10px; font-weight: 700; }
.level-name { font-size: 9px; color: #888; max-width: 54px; text-align: center; line-height: 1.3; }
.level-arrow { position: absolute; right: -8px; top: 12px; color: #DDD; font-size: 12px; }

/* Tabs */
.tab-nav { background: #fff; border-bottom: 1px solid #eee; display: flex; overflow-x: auto; padding: 0 16px; position: sticky; top: 0; z-index: 10; }
.tab-btn { padding: 14px 16px; border: none; background: transparent; font-size: 12px; cursor: pointer; font-family: inherit; white-space: nowrap; color: #888; border-bottom: 2px solid transparent; transition: all 0.2s; }
.tab-btn.active { font-weight: 700; color: #1565C0; border-bottom-color: #1565C0; }
.tab-body { padding: 16px 16px 40px; }

/* Info boxes */
.info-box { border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; font-size: 12px; line-height: 1.7; }
.info-box.blue   { background: #E3F2FD; border: 1px solid rgba(21,101,192,0.15); color: #1A237E; }
.info-box.orange { background: #FFF3E0; border: 1px solid rgba(230,81,0,0.2);   color: #BF360C; }
.info-box.yellow { background: #FFF8E1; border: 1px solid rgba(255,193,7,0.3);  color: #E65100; }

/* Journey */
.journey-wrap { margin-bottom: 0; }
.step-connector { text-align: center; color: #DDD; font-size: 12px; padding: 3px 0; }
.journey-card { background: #fff; border-radius: 14px; padding: 14px; border: 2px solid #F0F0F0; cursor: pointer; transition: all 0.25s; margin-bottom: 0; }
.journey-card.expanded { border-color: var(--sc); box-shadow: 0 4px 14px color-mix(in srgb, var(--sc) 20%, transparent); }
.journey-header { display: flex; align-items: center; gap: 10px; }
.journey-icons { display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
.j-icon { width: 34px; height: 34px; border-radius: 9px; border: 2px solid; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 14px; }
.j-lv { font-size: 8px; font-weight: 700; }
.j-arrow { color: #CCC; font-size: 12px; }
.journey-meta { flex: 1; }
.journey-title { font-size: 13px; font-weight: 700; color: #222; display: flex; align-items: center; gap: 6px; }
.badge-exam { font-size: 9px; background: rgba(250,173,20,0.15); color: #faad14; padding: 2px 7px; border-radius: 8px; font-weight: 700; border: 1px solid rgba(250,173,20,0.3); }
.journey-desc { font-size: 11px; color: #888; margin-top: 2px; }
.j-toggle { color: #CCC; font-size: 11px; transition: 0.2s; }

.journey-detail { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(0,0,0,0.06); }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.detail-box { border-radius: 10px; padding: 10px; }
.detail-box.gray { background: rgba(0,0,0,0.03); }
.detail-box-title { font-size: 11px; font-weight: 700; margin-bottom: 6px; }
.detail-box-title.blue { color: #1565C0; }
.detail-row { display: flex; justify-content: space-between; font-size: 11px; color: #555; margin-bottom: 3px; }
.detail-row-dot { font-size: 11px; color: #555; margin-bottom: 3px; }
.detail-note { padding: 8px 10px; background: rgba(0,0,0,0.02); border-radius: 8px; border-left: 3px solid var(--sc); font-size: 11px; color: #666; }
.note-warn { color: #faad14; margin-top: 3px; }
.note-iron { color: #F44336; margin-top: 3px; font-weight: 700; }

/* Flow */
.section-card { background: #fff; border-radius: 14px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.05); }
.section-title { font-size: 13px; font-weight: 700; color: #222; margin-bottom: 12px; }
.flow-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; }
.flow-dot { width: 26px; height: 26px; border-radius: 50%; border: 2px solid; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 700; flex-shrink: 0; }
.flow-text { flex: 1; font-size: 12px; color: #444; padding-top: 3px; line-height: 1.5; }

/* Status */
.status-chain { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 8px; }
.status-node-wrap { display: flex; align-items: center; gap: 6px; }
.status-node { padding: 4px 12px; border-radius: 20px; font-size: 11px; border: 1px solid; font-family: monospace; font-weight: 600; }
.status-arrow { color: #DDD; font-size: 12px; }
.status-note { font-size: 11px; color: #aaa; }

/* Push tags */
.push-tags { display: flex; flex-wrap: wrap; gap: 7px; }
.push-tag { padding: 4px 11px; border-radius: 20px; font-size: 11px; background: rgba(24,144,255,0.08); color: #1890ff; border: 1px solid rgba(24,144,255,0.2); }
.push-tag.warn { background: rgba(244,67,54,0.08); color: #F44336; border-color: rgba(244,67,54,0.2); }
.push-tag.green { background: rgba(82,196,26,0.08); color: #52c41a; border-color: rgba(82,196,26,0.2); }
.push-tag.gold  { background: rgba(250,173,20,0.1); color: #faad14; border-color: rgba(250,173,20,0.3); }

/* Iron laws */
.iron-card { background: #fff; border-radius: 12px; padding: 14px; margin-bottom: 10px; border-left: 3px solid; box-shadow: 0 1px 6px rgba(0,0,0,0.04); }
.iron-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.iron-icon { font-size: 18px; }
.iron-title { font-size: 13px; font-weight: 700; }
.iron-desc { font-size: 12px; color: #555; line-height: 1.6; }

/* AI tools */
.ai-card { background: #fff; border-radius: 12px; padding: 14px; margin-bottom: 10px; display: flex; gap: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.04); }
.ai-icon { font-size: 26px; flex-shrink: 0; }
.ai-body { flex: 1; }
.ai-name { font-size: 13px; font-weight: 700; color: #222; margin-bottom: 3px; }
.ai-desc { font-size: 11px; color: #555; line-height: 1.6; margin-bottom: 6px; }
.ai-badge { font-size: 10px; background: rgba(24,144,255,0.08); color: #1890ff; padding: 2px 9px; border-radius: 10px; border: 1px solid rgba(24,144,255,0.2); }
.code-block { background: #F8F9FA; border-radius: 8px; padding: 12px; font-size: 11px; color: #333; line-height: 1.7; white-space: pre-wrap; margin: 0; }

/* KPI */
.kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.kpi-item { display: flex; align-items: center; gap: 8px; padding: 9px 10px; background: #FAFAFA; border-radius: 9px; border: 1px solid #F0F0F0; }
.kpi-icon { font-size: 18px; flex-shrink: 0; }
.kpi-label { font-size: 12px; font-weight: 600; color: #333; flex: 1; }
.kpi-unit { font-size: 10px; color: #aaa; }

/* Trust */
.trust-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.trust-weight { width: 30px; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.trust-bar-wrap { width: 60px; height: 5px; background: #eee; border-radius: 3px; overflow: hidden; flex-shrink: 0; }
.trust-bar { height: 100%; border-radius: 3px; }
.trust-signal { width: 66px; font-size: 11px; font-weight: 600; color: #333; flex-shrink: 0; }
.trust-note { flex: 1; font-size: 10px; color: #aaa; }
.trust-levels { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 12px; }
.trust-level-tag { padding: 7px 10px; border-radius: 10px; border: 1px solid; font-size: 11px; }

/* Form */
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; color: #444; margin-bottom: 6px; }
.form-group input,
.form-group select,
.form-group textarea { width: 100%; border-radius: 10px; border: 1px solid #E0E0E0; padding: 10px 12px; font-size: 12px; font-family: inherit; box-sizing: border-box; }
.form-group textarea { min-height: 80px; resize: vertical; }
.form-hint { font-size: 11px; color: #aaa; text-align: center; margin-top: 8px; }

/* Openings */
.opening-row { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid #F5F5F5; }
.opening-body { flex: 1; }
.opening-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.opening-name { font-size: 13px; font-weight: 700; color: #222; }
.urgent-tag { font-size: 10px; background: #FFF3E0; color: #E65100; padding: 1px 8px; border-radius: 10px; font-weight: 700; }
.opening-desc { font-size: 11px; color: #888; }
.opening-slots { text-align: center; flex-shrink: 0; }
.slots-num { font-size: 22px; font-weight: 800; color: #1565C0; }
.slots-label { font-size: 10px; color: #aaa; }

/* Transitions */
.expand-enter-active, .expand-leave-active { transition: all 0.25s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }
.expand-enter-to, .expand-leave-from { opacity: 1; max-height: 600px; }
</style>
