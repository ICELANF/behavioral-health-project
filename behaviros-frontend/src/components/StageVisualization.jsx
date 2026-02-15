import { useState, useEffect, useRef } from "react";

const STAGES = [
  { id: "S0", name: "授权进入", icon: "🌱", color: "#8B9F82", weeks: "第1天", language: "准备开始你的成长之旅" },
  { id: "S1", name: "觉察与稳定期", icon: "👁️", color: "#7B9EA8", weeks: "1-2周", language: "正在培养觉察习惯" },
  { id: "S2", name: "尝试与波动期", icon: "🌊", color: "#C4956A", weeks: "2-4周", language: "正在尝试新行为 — 波动是正常的" },
  { id: "S3", name: "形成路径期", icon: "🛤️", color: "#9B8EC4", weeks: "4-8周", language: "正在形成自己的习惯路径" },
  { id: "S4", name: "内化期", icon: "💎", color: "#6BA89C", weeks: "8-16周", language: "行为已开始内化为习惯" },
  { id: "S5", name: "转出期", icon: "🎓", color: "#D4A057", weeks: "16-24周", language: "即将毕业 — 这是新的开始" },
];

const FORBIDDEN_DISPLAY = ["风险等级", "群体排名", "预测结论", "R0-R4风险标签", "BPT类型判断"];

// Demo data
const DEMO_STATE = {
  user_id: 1001,
  current_stage: "S3",
  stage_entered_at: new Date(Date.now() - 35 * 86400000).toISOString(),
  is_graduated: false,
  stability_counter_days: 0,
  behavior_attempts: 23,
  indicators_improved: 2,
  feedback_frequency: 4.2,
  pathway_score: 0.55,
  stage_history: [
    { stage: "S0", entered_at: "2025-09-01T00:00:00Z", exited_at: "2025-09-01T12:00:00Z", duration_days: 1 },
    { stage: "S1", entered_at: "2025-09-01T12:00:00Z", exited_at: "2025-09-15T00:00:00Z", duration_days: 14 },
    { stage: "S2", entered_at: "2025-09-15T00:00:00Z", exited_at: "2025-10-12T00:00:00Z", duration_days: 27 },
  ],
  journey_timeline: [
    { stage: "S0", name: "授权进入", status: "completed", duration_days: 1 },
    { stage: "S1", name: "觉察与稳定期", status: "completed", duration_days: 14 },
    { stage: "S2", name: "尝试与波动期", status: "completed", duration_days: 27 },
    { stage: "S3", name: "形成路径期", status: "current", duration_days: 35 },
    { stage: "S4", name: "内化期", status: "upcoming", duration_days: 0 },
    { stage: "S5", name: "转出期", status: "upcoming", duration_days: 0 },
  ],
};

const DEMO_S4_STATE = {
  ...DEMO_STATE,
  current_stage: "S4",
  stability_counter_days: 52,
  stage_history: [
    ...DEMO_STATE.stage_history,
    { stage: "S3", entered_at: "2025-10-12T00:00:00Z", exited_at: "2025-11-20T00:00:00Z", duration_days: 39 },
  ],
  journey_timeline: [
    { stage: "S0", name: "授权进入", status: "completed", duration_days: 1 },
    { stage: "S1", name: "觉察与稳定期", status: "completed", duration_days: 14 },
    { stage: "S2", name: "尝试与波动期", status: "completed", duration_days: 27 },
    { stage: "S3", name: "形成路径期", status: "completed", duration_days: 39 },
    { stage: "S4", name: "内化期", status: "current", duration_days: 52 },
    { stage: "S5", name: "转出期", status: "upcoming", duration_days: 0 },
  ],
};

function StabilityRing({ days, required = 90 }) {
  const pct = Math.min(100, (days / required) * 100);
  const r = 54, c = 2 * Math.PI * r;
  const offset = c - (pct / 100) * c;
  return (
    <div style={{ position: "relative", width: 140, height: 140 }}>
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#e8ece6" strokeWidth="8" />
        <circle cx="70" cy="70" r={r} fill="none" stroke="#6BA89C" strokeWidth="8"
          strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
          transform="rotate(-90 70 70)" style={{ transition: "stroke-dashoffset 1.2s ease" }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: 28, fontWeight: 700, color: "#2d3a2e", fontFamily: "'Noto Serif SC', serif" }}>{days}</span>
        <span style={{ fontSize: 11, color: "#7a8a7c", letterSpacing: 1 }}>/ {required} 天</span>
      </div>
    </div>
  );
}

function JourneyTimeline({ timeline, currentStage }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 0, width: "100%", overflowX: "auto", padding: "12px 0" }}>
      {timeline.map((item, i) => {
        const stageInfo = STAGES.find(s => s.id === item.stage) || STAGES[0];
        const isCurrent = item.status === "current";
        const isCompleted = item.status === "completed";
        const isUpcoming = item.status === "upcoming";
        return (
          <div key={item.stage} style={{ display: "flex", alignItems: "flex-start", flex: isCurrent ? "1.5" : "1" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 72, position: "relative" }}>
              <div style={{
                width: isCurrent ? 48 : 36, height: isCurrent ? 48 : 36,
                borderRadius: "50%",
                background: isUpcoming ? "#eef0ec" : stageInfo.color,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: isCurrent ? 22 : 16,
                boxShadow: isCurrent ? `0 0 0 4px ${stageInfo.color}33, 0 4px 16px ${stageInfo.color}44` : "none",
                transition: "all 0.5s ease",
                opacity: isUpcoming ? 0.5 : 1,
              }}>
                {isCompleted ? "✓" : stageInfo.icon}
              </div>
              <div style={{ marginTop: 8, textAlign: "center" }}>
                <div style={{
                  fontSize: 10, fontWeight: 600, color: isUpcoming ? "#bbb" : stageInfo.color,
                  letterSpacing: 1, textTransform: "uppercase",
                }}>{item.stage}</div>
                <div style={{
                  fontSize: 11, color: isCurrent ? "#2d3a2e" : isUpcoming ? "#ccc" : "#7a8a7c",
                  fontWeight: isCurrent ? 600 : 400, marginTop: 2, maxWidth: 80,
                }}>{stageInfo.name}</div>
                {item.duration_days > 0 && (
                  <div style={{ fontSize: 10, color: "#aab5ac", marginTop: 2 }}>{item.duration_days}天</div>
                )}
              </div>
            </div>
            {i < timeline.length - 1 && (
              <div style={{
                flex: 1, height: 2, minWidth: 16, marginTop: isCurrent ? 23 : 17,
                background: isCompleted ? stageInfo.color : "#e0e4dd",
                borderRadius: 1,
                opacity: isUpcoming ? 0.3 : 0.7,
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function StageCard({ stageInfo, state, isActive }) {
  const daysInStage = isActive ? Math.floor((Date.now() - new Date(state.stage_entered_at).getTime()) / 86400000) : 0;
  return (
    <div style={{
      background: isActive ? `linear-gradient(135deg, ${stageInfo.color}11, ${stageInfo.color}08)` : "#fafbf9",
      border: isActive ? `2px solid ${stageInfo.color}55` : "1px solid #e8ece6",
      borderRadius: 16, padding: "24px 20px",
      transition: "all 0.4s ease",
      position: "relative", overflow: "hidden",
    }}>
      {isActive && <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 3,
        background: `linear-gradient(90deg, ${stageInfo.color}, ${stageInfo.color}88)`,
      }} />}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <span style={{ fontSize: 28 }}>{stageInfo.icon}</span>
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: stageInfo.color, letterSpacing: 1 }}>{stageInfo.id} · {stageInfo.weeks}</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#2d3a2e", fontFamily: "'Noto Serif SC', serif" }}>{stageInfo.name}</div>
        </div>
      </div>
      <p style={{ fontSize: 13, color: "#5a6b5c", lineHeight: 1.6, margin: "0 0 12px 0" }}>{stageInfo.language}</p>
      {isActive && (
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <div style={{ background: "#fff", borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
            <span style={{ color: "#999" }}>已在本阶段</span>
            <span style={{ fontWeight: 700, color: "#2d3a2e", marginLeft: 6 }}>{daysInStage} 天</span>
          </div>
          <div style={{ background: "#fff", borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
            <span style={{ color: "#999" }}>行为尝试</span>
            <span style={{ fontWeight: 700, color: "#2d3a2e", marginLeft: 6 }}>{state.behavior_attempts} 次</span>
          </div>
        </div>
      )}
    </div>
  );
}

function DisplayGuard({ stage }) {
  const stageInfo = STAGES.find(s => s.id === stage);
  const config = {
    S1: { allowed: ["行为趋势", "稳定性变化"], forbidden: ["风险等级", "群体排名", "预测结论"] },
    S2: { allowed: ["行为趋势", "阶段语言"], forbidden: ["风险等级", "群体排名"] },
    S3: { allowed: ["阶段语言", "行为趋势"], forbidden: ["风险等级", "预测结论"] },
    S4: { allowed: ["阶段语言", "稳定性数据"], forbidden: ["风险等级"] },
    S5: { allowed: ["毕业证明", "成长轨迹回顾"], forbidden: [] },
  }[stage] || { allowed: [], forbidden: [] };

  return (
    <div style={{ background: "#f8f9f7", borderRadius: 12, padding: 16, border: "1px solid #e8ece6" }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: "#7a8a7c", marginBottom: 10, letterSpacing: 1 }}>数据展示权限 · {stageInfo?.name}</div>
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 140 }}>
          <div style={{ fontSize: 11, color: "#6BA89C", fontWeight: 600, marginBottom: 6 }}>✅ 可展示</div>
          {config.allowed.map(item => (
            <div key={item} style={{ fontSize: 12, color: "#5a6b5c", padding: "3px 0" }}>· {item}</div>
          ))}
          {config.allowed.length === 0 && <div style={{ fontSize: 12, color: "#bbb" }}>—</div>}
        </div>
        <div style={{ flex: 1, minWidth: 140 }}>
          <div style={{ fontSize: 11, color: "#c75a5a", fontWeight: 600, marginBottom: 6 }}>❌ 禁止展示</div>
          {[...config.forbidden, ...FORBIDDEN_DISPLAY.slice(0, 2)].map(item => (
            <div key={item} style={{ fontSize: 12, color: "#c75a5a88", padding: "3px 0" }}>· {item}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CoachOverview() {
  const dist = { S0: 2, S1: 5, S2: 8, S3: 6, S4: 3, S5: 1 };
  const total = Object.values(dist).reduce((a, b) => a + b, 0);
  const maxVal = Math.max(...Object.values(dist));
  return (
    <div style={{ background: "#fff", borderRadius: 16, padding: 20, border: "1px solid #e8ece6" }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: "#2d3a2e", marginBottom: 16, fontFamily: "'Noto Serif SC', serif" }}>学员阶段分布 · {total} 人</div>
      <div style={{ display: "flex", gap: 6, alignItems: "flex-end", height: 100 }}>
        {STAGES.map(s => {
          const val = dist[s.id] || 0;
          const h = maxVal > 0 ? (val / maxVal) * 80 : 0;
          return (
            <div key={s.id} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: "#2d3a2e" }}>{val}</span>
              <div style={{
                width: "100%", height: h, borderRadius: "6px 6px 0 0",
                background: `linear-gradient(180deg, ${s.color}, ${s.color}88)`,
                transition: "height 0.6s ease", minHeight: val > 0 ? 8 : 0,
              }} />
              <span style={{ fontSize: 10, color: "#999" }}>{s.id}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function StageVisualization() {
  const [viewMode, setViewMode] = useState("journey");
  const [demoMode, setDemoMode] = useState("S3");
  const state = demoMode === "S4" ? DEMO_S4_STATE : DEMO_STATE;
  const currentStageInfo = STAGES.find(s => s.id === state.current_stage);

  return (
    <div style={{
      minHeight: "100vh", background: "linear-gradient(180deg, #f4f6f2 0%, #eef1eb 100%)",
      fontFamily: "'Noto Sans SC', 'Helvetica Neue', sans-serif", padding: "24px 16px",
    }}>
      <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Noto+Sans+SC:wght@300;400;600;700&display=swap" rel="stylesheet" />

      <div style={{ maxWidth: 680, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#2d3a2e", margin: 0, fontFamily: "'Noto Serif SC', serif", letterSpacing: 2 }}>
            成长旅程
          </h1>
          <p style={{ fontSize: 12, color: "#7a8a7c", marginTop: 4, letterSpacing: 1 }}>S0-S5 六阶段行为改变可视化</p>
        </div>

        {/* Demo Controls */}
        <div style={{ display: "flex", gap: 8, justifyContent: "center", marginBottom: 20 }}>
          {["S3", "S4"].map(mode => (
            <button key={mode} onClick={() => setDemoMode(mode)} style={{
              padding: "6px 16px", borderRadius: 20, border: "1px solid #ddd", fontSize: 12,
              background: demoMode === mode ? "#2d3a2e" : "#fff",
              color: demoMode === mode ? "#fff" : "#666", cursor: "pointer", fontWeight: 500,
            }}>
              {mode === "S3" ? "路径形成期" : "内化期(90天)"}
            </button>
          ))}
        </div>

        {/* Current Stage Hero */}
        <div style={{
          background: `linear-gradient(135deg, ${currentStageInfo.color}22 0%, ${currentStageInfo.color}0a 100%)`,
          borderRadius: 20, padding: 24, marginBottom: 20,
          border: `1px solid ${currentStageInfo.color}33`,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{
              width: 60, height: 60, borderRadius: "50%",
              background: `linear-gradient(135deg, ${currentStageInfo.color}, ${currentStageInfo.color}cc)`,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 30,
              boxShadow: `0 4px 20px ${currentStageInfo.color}44`,
            }}>{currentStageInfo.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: currentStageInfo.color, fontWeight: 600, letterSpacing: 2 }}>{currentStageInfo.id} · 当前阶段</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: "#2d3a2e", fontFamily: "'Noto Serif SC', serif" }}>{currentStageInfo.name}</div>
              <div style={{ fontSize: 13, color: "#5a6b5c", marginTop: 4, lineHeight: 1.5 }}>{currentStageInfo.language}</div>
            </div>
          </div>

          {/* S4 Stability Ring */}
          {state.current_stage === "S4" && (
            <div style={{ display: "flex", alignItems: "center", gap: 20, marginTop: 20, padding: "16px 0", borderTop: `1px solid ${currentStageInfo.color}22` }}>
              <StabilityRing days={state.stability_counter_days} />
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#2d3a2e", fontFamily: "'Noto Serif SC', serif" }}>90天稳定验证</div>
                <div style={{ fontSize: 12, color: "#7a8a7c", marginTop: 4, lineHeight: 1.6 }}>
                  行为习惯需连续保持90天方可毕业。<br />
                  中断不降级，重新开始计数。
                </div>
                <div style={{ fontSize: 11, color: currentStageInfo.color, marginTop: 8, fontWeight: 600 }}>
                  还需 {90 - state.stability_counter_days} 天 · 预计 {new Date(Date.now() + (90 - state.stability_counter_days) * 86400000).toLocaleDateString("zh-CN")} 完成
                </div>
              </div>
            </div>
          )}
        </div>

        {/* View Tabs */}
        <div style={{ display: "flex", gap: 4, marginBottom: 16, background: "#e8ece6", borderRadius: 10, padding: 3 }}>
          {[
            { id: "journey", label: "成长旅程" },
            { id: "stages", label: "阶段详情" },
            { id: "permissions", label: "数据权限" },
            { id: "coach", label: "教练视角" },
          ].map(tab => (
            <button key={tab.id} onClick={() => setViewMode(tab.id)} style={{
              flex: 1, padding: "8px 0", borderRadius: 8, border: "none", fontSize: 12, fontWeight: 600,
              background: viewMode === tab.id ? "#fff" : "transparent",
              color: viewMode === tab.id ? "#2d3a2e" : "#999",
              cursor: "pointer", boxShadow: viewMode === tab.id ? "0 1px 4px #0001" : "none",
            }}>{tab.label}</button>
          ))}
        </div>

        {/* Journey Timeline View */}
        {viewMode === "journey" && (
          <div style={{ background: "#fff", borderRadius: 16, padding: 20, border: "1px solid #e8ece6" }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#2d3a2e", marginBottom: 16, fontFamily: "'Noto Serif SC', serif" }}>成长轨迹</div>
            <JourneyTimeline timeline={state.journey_timeline} currentStage={state.current_stage} />
            <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
              {[
                { label: "总天数", value: state.stage_history.reduce((a, h) => a + h.duration_days, 0) + Math.floor((Date.now() - new Date(state.stage_entered_at).getTime()) / 86400000), unit: "天" },
                { label: "行为尝试", value: state.behavior_attempts, unit: "次" },
                { label: "指标好转", value: state.indicators_improved, unit: "项" },
              ].map(stat => (
                <div key={stat.label} style={{ background: "#f8f9f7", borderRadius: 10, padding: "10px 12px", textAlign: "center" }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: "#2d3a2e", fontFamily: "'Noto Serif SC', serif" }}>{stat.value}</div>
                  <div style={{ fontSize: 11, color: "#999" }}>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stages Detail View */}
        {viewMode === "stages" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {STAGES.map(s => (
              <StageCard key={s.id} stageInfo={s} state={state} isActive={s.id === state.current_stage} />
            ))}
          </div>
        )}

        {/* Display Permissions View */}
        {viewMode === "permissions" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ background: "#c75a5a11", borderRadius: 12, padding: 14, border: "1px solid #c75a5a22" }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#c75a5a", marginBottom: 6 }}>⚠️ 全局红线 (Sheet⑪ RED-01~06)</div>
              <div style={{ fontSize: 12, color: "#7a5555", lineHeight: 1.8 }}>
                {FORBIDDEN_DISPLAY.map(item => <div key={item}>· {item} — 任何阶段均禁止展示</div>)}
              </div>
            </div>
            {STAGES.filter(s => s.id !== "S0").map(s => (
              <DisplayGuard key={s.id} stage={s.id} />
            ))}
          </div>
        )}

        {/* Coach Overview */}
        {viewMode === "coach" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <CoachOverview />
            <div style={{ background: "#fff", borderRadius: 16, padding: 20, border: "1px solid #e8ece6" }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#2d3a2e", marginBottom: 12, fontFamily: "'Noto Serif SC', serif" }}>需关注学员</div>
              {[
                { name: "学员A", stage: "S2", days: 35, alert: "S2停留超预期 (28天)" },
                { name: "学员B", stage: "S4", days: 45, alert: "稳定计数器中断, 已重置" },
              ].map((item, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "10px 12px",
                  background: "#fdf8f0", borderRadius: 10, marginBottom: 8, border: "1px solid #f0e6d4",
                }}>
                  <span style={{ fontSize: 18 }}>{STAGES.find(s => s.id === item.stage)?.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#2d3a2e" }}>{item.name}</div>
                    <div style={{ fontSize: 11, color: "#C4956A" }}>{item.alert}</div>
                  </div>
                  <span style={{ fontSize: 11, color: "#999", background: "#f0ece6", padding: "4px 8px", borderRadius: 6 }}>{item.stage} · {item.days}天</span>
                </div>
              ))}
            </div>
            <div style={{
              background: "#f0f5f3", borderRadius: 12, padding: 14, border: "1px solid #d4e4de",
              fontSize: 12, color: "#5a7a6c", lineHeight: 1.7,
            }}>
              <strong>教练提醒:</strong> S2阶段波动不降级。当学员出现反复时, 留在S2继续支持, 不批评不加压。S3是唯一允许回退的阶段(回S2), 但回退时需给予正面鼓励。
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
