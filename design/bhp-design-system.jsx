import { useState, useEffect } from "react";

// ══════════════════════════════════════════════════════════════════════
// 行健平台 V5.3.0 完整设计系统
// ① 5套封面主题  ② 3套角色首页主题  ③ 教练队伍建设（依据体系全景文档）
// 权威来源：平台教练体系全景-20260225.md
// ══════════════════════════════════════════════════════════════════════

// ─── 权威常量（直接对应 admin-portal/src/constants/index.ts） ────────
const COACH_LEVELS = {
  L0: { label: "观察员",        emoji: "👀", color: "#8c8c8c", role: "OBSERVER",  bg: "#F5F5F5",
        desc: "行为入口·认知-行为信号的原始数据源" },
  L1: { label: "成长者",        emoji: "🌱", color: "#1890ff", role: "GROWER",    bg: "#E6F7FF",
        desc: "行为养成践行者·效果的唯一承载体" },
  L2: { label: "分享者",        emoji: "💬", color: "#52c41a", role: "SHARER",    bg: "#F6FFED",
        desc: "同伴支持者·经验传递与陪伴者" },
  L3: { label: "行为健康教练",   emoji: "🎯", color: "#faad14", role: "COACH",    bg: "#FFFBE6",
        desc: "系统翻译者·行为改变实施者" },
  L4: { label: "行为健康促进师", emoji: "⭐", color: "#722ed1", role: "PROMOTER", bg: "#F9F0FF",
        desc: "系统放大器·组织/区域推动者" },
  L5: { label: "大师",          emoji: "🏆", color: "#eb2f96", role: "MASTER",   bg: "#FFF0F6",
        desc: "学科文明层·理论范式与传承者" },
};

// 晋级阈值（权威源: api/paths_api.py _LEVEL_THRESHOLDS）
const LEVEL_THRESHOLDS = {
  "L0→L1": { G: 100,  C: 0,    I: 0,   exam: false, peers: null },
  "L1→L2": { G: 500,  C: 50,   I: 0,   exam: false, peers: null },
  "L2→L3": { G: 800,  C: 200,  I: 50,  exam: true,  peers: "4个L1同道者" },
  "L3→L4": { G: 1500, C: 600,  I: 200, exam: true,  peers: "4个L2同道者" },
  "L4→L5": { G: 3000, C: 1500, I: 600, exam: true,  peers: "4个L3同道者" },
};

// 教练认证升级条件（权威源: api/coach_api.py _UPGRADE_REQ）
const COACH_UPGRADE_REQ = {
  "L0→L1": { students: 5,   messages: 20,   assessments: null, improved: null },
  "L1→L2": { students: 15,  messages: 100,  assessments: 30,   improved: null },
  "L2→L3": { students: 30,  messages: 300,  assessments: 100,  improved: 10   },
  "L3→L4": { students: 50,  messages: 500,  assessments: null, improved: 25   },
  "L4→L5": { students: 100, messages: 1000, assessments: null, improved: 50   },
};

// ─── 5套封面主题 ──────────────────────────────────────────────────────
const COVER_THEMES = {
  chenxi: {
    name: "晨曦", nameEn: "DAWN", desc: "暖橙·活力·新的开始",
    bg: "linear-gradient(145deg,#FFF8F0,#FFE0CC,#FFCBA0)",
    card: "rgba(255,255,255,0.8)", border: "rgba(232,101,10,0.15)",
    primary: "#E8650A", accent: "#FF9A3C", text: "#2D1A0A", textSub: "#8B5E3C",
    glow: "rgba(232,101,10,0.28)", hero: "linear-gradient(135deg,#FF8C42,#FFB347,#FFC96B)",
    pattern: "circles",
  },
  zhulin: {
    name: "竹林", nameEn: "BAMBOO", desc: "清绿·自然·生机盎然",
    bg: "linear-gradient(145deg,#F0FBF4,#E0F5E9,#C8EDD6)",
    card: "rgba(255,255,255,0.82)", border: "rgba(56,142,60,0.13)",
    primary: "#2E7D32", accent: "#66BB6A", text: "#0D2B0F", textSub: "#4A7A4E",
    glow: "rgba(46,125,50,0.22)", hero: "linear-gradient(135deg,#43A047,#66BB6A,#A5D6A7)",
    pattern: "dots",
  },
  shuimo: {
    name: "水墨", nameEn: "INK WASH", desc: "米白·朱砂·东方意蕴",
    bg: "linear-gradient(145deg,#FAFAF8,#F5F3EE,#EDE9E0)",
    card: "rgba(255,255,255,0.92)", border: "rgba(100,80,60,0.1)",
    primary: "#C62828", accent: "#8D6E63", text: "#1A1208", textSub: "#6B5B4E",
    glow: "rgba(198,40,40,0.18)", hero: "linear-gradient(135deg,#37474F,#546E7A,#78909C)",
    pattern: "ink",
  },
  shanhu: {
    name: "珊瑚", nameEn: "CORAL", desc: "暖红·健康·充满希望",
    bg: "linear-gradient(145deg,#FFF5F5,#FFE8E8,#FFCACA)",
    card: "rgba(255,255,255,0.84)", border: "rgba(233,79,79,0.13)",
    primary: "#D32F2F", accent: "#EF5350", text: "#2B0A0A", textSub: "#8B4444",
    glow: "rgba(211,47,47,0.22)", hero: "linear-gradient(135deg,#FF7043,#EF5350,#EC407A)",
    pattern: "hearts",
  },
  muyun: {
    name: "暮云", nameEn: "DUSK", desc: "薰紫·柔和·疗愈感",
    bg: "linear-gradient(145deg,#F8F0FF,#EDE0FF,#D5CCFF)",
    card: "rgba(255,255,255,0.8)", border: "rgba(103,58,183,0.13)",
    primary: "#5E35B1", accent: "#9575CD", text: "#1A0A2B", textSub: "#6B4A8B",
    glow: "rgba(94,53,177,0.26)", hero: "linear-gradient(135deg,#7B1FA2,#9C27B0,#CE93D8)",
    pattern: "stars",
  },
};

// ─── 3套首页主题 ──────────────────────────────────────────────────────
const HOME_THEMES = {
  natural:  { name: "清新自然", icon: "🌿", desc: "绿白为主，清爽通透" },
  elegant:  { name: "典雅东方", icon: "🏮", desc: "水墨风格，简约有力" },
  vibrant:  { name: "活力现代", icon: "⚡", desc: "渐变深色，充满能量" },
};

const ROLE_HOME_PALETTES = {
  observer: {
    natural:  { bg:"#F0FBF4", hero:"linear-gradient(135deg,#2E7D32,#43A047)", card:"#fff", primary:"#2E7D32", text:"#0D2B0F", sub:"#4A7A4E", border:"rgba(46,125,50,0.12)" },
    elegant:  { bg:"#FAFAF8", hero:"linear-gradient(135deg,#37474F,#546E7A)", card:"#fff", primary:"#C62828", text:"#1A1208", sub:"#6B5B4E", border:"rgba(100,80,60,0.1)"  },
    vibrant:  { bg:"#0D2137", hero:"linear-gradient(135deg,#1565C0,#1976D2)", card:"rgba(255,255,255,0.07)", primary:"#42A5F5", text:"#fff", sub:"rgba(255,255,255,0.55)", border:"rgba(255,255,255,0.1)" },
  },
  grower: {
    natural:  { bg:"#FFFDE7", hero:"linear-gradient(135deg,#F57F17,#FFA000)", card:"#fff", primary:"#E65100", text:"#2B1700", sub:"#8B5E20", border:"rgba(230,81,0,0.1)"  },
    elegant:  { bg:"#FAFAF8", hero:"linear-gradient(135deg,#263238,#37474F)", card:"#fff", primary:"#1A237E", text:"#0A0F1A", sub:"#546E7A", border:"rgba(26,35,126,0.1)" },
    vibrant:  { bg:"#1B0A2B", hero:"linear-gradient(135deg,#7B1FA2,#AB47BC)", card:"rgba(255,255,255,0.07)", primary:"#CE93D8", text:"#fff", sub:"rgba(255,255,255,0.55)", border:"rgba(255,255,255,0.1)" },
  },
  coach: {
    natural:  { bg:"#FFF8F0", hero:"linear-gradient(135deg,#BF360C,#E64A19)", card:"#fff", primary:"#BF360C", text:"#2B0A00", sub:"#8B4A30", border:"rgba(191,54,12,0.1)" },
    elegant:  { bg:"#F5F0FF", hero:"linear-gradient(135deg,#4A148C,#6A1B9A)", card:"#fff", primary:"#4A148C", text:"#150A20", sub:"#6A4A7A", border:"rgba(74,20,140,0.1)" },
    vibrant:  { bg:"#0A1F2B", hero:"linear-gradient(135deg,#00695C,#00897B)", card:"rgba(255,255,255,0.07)", primary:"#4DB6AC", text:"#fff", sub:"rgba(255,255,255,0.55)", border:"rgba(255,255,255,0.1)" },
  },
};

// ══════════════════════════════════════════════════════════════════════
// 组件 1：封面
// ══════════════════════════════════════════════════════════════════════
function PlatformCover({ themeKey }) {
  const t = COVER_THEMES[themeKey];
  const [nums, setNums] = useState({ agents: 0, apis: 0, models: 0 });

  useEffect(() => {
    const targets = { agents: 49, apis: 667, models: 147 };
    let frame = 0;
    const id = setInterval(() => {
      frame++;
      setNums({
        agents: Math.min(Math.floor(targets.agents * frame / 50), targets.agents),
        apis:   Math.min(Math.floor(targets.apis   * frame / 50), targets.apis),
        models: Math.min(Math.floor(targets.models * frame / 50), targets.models),
      });
      if (frame >= 50) clearInterval(id);
    }, 20);
    return () => clearInterval(id);
  }, [themeKey]);

  const PatternBg = () => {
    if (t.pattern === "circles") return (
      <svg style={{position:"absolute",inset:0,width:"100%",height:"100%",opacity:0.06}} aria-hidden>
        {[80,130,180,230].map((r,i)=><circle key={i} cx="85%" cy="20%" r={r} fill="none" stroke={t.primary} strokeWidth="1.5"/>)}
      </svg>
    );
    if (t.pattern === "dots") return (
      <svg style={{position:"absolute",inset:0,width:"100%",height:"100%",opacity:0.08}} aria-hidden>
        {[...Array(40)].map((_,i)=><circle key={i} cx={`${(i*137.5)%100}%`} cy={`${(i*83.7)%100}%`} r={2+(i%3)} fill={t.accent}/>)}
      </svg>
    );
    if (t.pattern === "ink") return (
      <svg style={{position:"absolute",inset:0,width:"100%",height:"100%",opacity:0.04}} aria-hidden>
        <text x="78%" y="55%" textAnchor="middle" fontSize="260" fill={t.textSub} fontFamily="'Noto Serif SC',serif" dominantBaseline="middle">健</text>
      </svg>
    );
    if (t.pattern === "hearts") return (
      <div style={{position:"absolute",inset:0,overflow:"hidden",opacity:0.05,display:"flex",flexWrap:"wrap",alignContent:"flex-start",pointerEvents:"none"}}>
        {[...Array(16)].map((_,i)=><div key={i} style={{fontSize:70,transform:`rotate(${i*23%50-25}deg)`,margin:8}}>❤️</div>)}
      </div>
    );
    if (t.pattern === "stars") return (
      <svg style={{position:"absolute",inset:0,width:"100%",height:"100%",opacity:0.1}} aria-hidden>
        {[...Array(35)].map((_,i)=><circle key={i} cx={`${(i*137.5)%100}%`} cy={`${(i*83.7)%100}%`} r={1+(i%3)} fill={t.accent} opacity={0.4+(i%3)*0.2}/>)}
      </svg>
    );
    return null;
  };

  const roles = [
    { emoji:"👀", label:"Observer", badge:"L0" },
    { emoji:"🌱", label:"Grower",   badge:"L1" },
    { emoji:"💬", label:"Sharer",   badge:"L2" },
    { emoji:"🎯", label:"Coach",    badge:"L3" },
    { emoji:"⭐", label:"Promoter", badge:"L4" },
    { emoji:"⚕️", label:"Expert",   badge:"XZB", isNew:true },
    { emoji:"🏛️", label:"Institution", badge:"ORG", isNew:true },
  ];

  return (
    <div style={{background:t.bg,borderRadius:20,overflow:"hidden",position:"relative",
      fontFamily:"'Noto Serif SC',serif",border:`1px solid ${t.border}`,
      boxShadow:`0 16px 48px ${t.glow}`}}>
      <PatternBg/>
      {/* Topbar */}
      <div style={{position:"relative",zIndex:1,display:"flex",justifyContent:"space-between",
        alignItems:"center",padding:"18px 28px",borderBottom:`1px solid ${t.border}`,backdropFilter:"blur(8px)"}}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={{width:38,height:38,borderRadius:10,background:t.hero,display:"flex",
            alignItems:"center",justifyContent:"center",fontSize:18,fontWeight:900,color:"#fff",
            boxShadow:`0 4px 12px ${t.glow}`}}>行</div>
          <div>
            <div style={{fontSize:15,fontWeight:700,color:t.text,letterSpacing:2}}>行健平台</div>
            <div style={{fontSize:9,color:t.textSub,letterSpacing:1}}>BehaviorOS · {t.nameEn}</div>
          </div>
        </div>
        <div style={{display:"flex",gap:10,alignItems:"center"}}>
          <span style={{fontSize:10,color:t.textSub}}>HEAD = 054</span>
          <span style={{background:`${t.glow}`,color:t.primary,border:`1px solid ${t.glow}`,
            fontSize:10,padding:"3px 10px",borderRadius:20,fontWeight:700}}>V5.3.0</span>
        </div>
      </div>

      {/* Body */}
      <div style={{position:"relative",zIndex:1,display:"flex",padding:"28px 28px 24px"}}>
        {/* Left */}
        <div style={{flex:1,paddingRight:28}}>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:14}}>
            <div style={{width:20,height:2,background:t.accent}}/>
            <span style={{fontSize:10,color:t.textSub,letterSpacing:3,fontFamily:"sans-serif",textTransform:"uppercase"}}>
              Behavioral Health OS
            </span>
          </div>
          <h1 style={{fontSize:48,fontWeight:900,lineHeight:1.1,color:t.text,margin:"0 0 4px",letterSpacing:-1}}>
            <span style={{color:t.primary}}>行</span>为健康<br/>操作系统
          </h1>
          <p style={{fontSize:12,color:t.textSub,letterSpacing:4,margin:"0 0 20px",fontFamily:"sans-serif"}}>
            BehaviorOS · {t.name}
          </p>
          <div style={{borderLeft:`3px solid ${t.accent}`,paddingLeft:14,marginBottom:24,maxWidth:360}}>
            <p style={{fontSize:16,fontWeight:700,color:t.text,lineHeight:1.6,margin:0}}>
              让<span style={{color:t.primary}}>每个角色</span>在首次交互中<br/>
              感受到这是<span style={{color:t.primary}}>为我设计的</span>
            </p>
          </div>
          {/* Stats */}
          <div style={{display:"flex",gap:24,marginBottom:24}}>
            {[{n:nums.agents,u:"类",l:"AI AGENTS"},{n:nums.apis+"+",u:"",l:"ENDPOINTS"},{n:nums.models,u:"个",l:"ORM MODELS"}].map((s,i)=>(
              <div key={i}>
                <div style={{fontFamily:"sans-serif",fontSize:28,fontWeight:800,color:t.text,lineHeight:1}}>
                  {s.n}<span style={{fontSize:13,color:t.accent}}>{s.u}</span>
                </div>
                <div style={{fontSize:9,color:t.textSub,marginTop:3,letterSpacing:1,fontFamily:"sans-serif"}}>{s.l}</div>
              </div>
            ))}
          </div>
          <button style={{background:t.hero,color:"#fff",border:"none",borderRadius:50,
            padding:"12px 28px",fontSize:14,fontWeight:700,cursor:"pointer",letterSpacing:2,
            fontFamily:"'Noto Serif SC',serif",boxShadow:`0 6px 20px ${t.glow}`}}>
            立即开始
          </button>
          {/* Architecture chain */}
          <div style={{display:"flex",alignItems:"center",gap:4,marginTop:16,flexWrap:"wrap"}}>
            {["Observer","Grower","Sharer","Coach","Expert","Institution"].map((n,i,arr)=>(
              <span key={n} style={{display:"flex",alignItems:"center",gap:4}}>
                <span style={{fontSize:10,color:i>=4?t.primary:t.textSub,fontFamily:"sans-serif",
                  fontWeight:i>=4?700:400}}>{n}{i>=4?" ★":""}</span>
                {i<arr.length-1&&<span style={{color:t.border,fontSize:10}}>→</span>}
              </span>
            ))}
          </div>
        </div>
        {/* Right – roles */}
        <div style={{width:240}}>
          <p style={{fontSize:10,color:t.textSub,letterSpacing:2,marginBottom:8,fontFamily:"sans-serif"}}>ROLE ECOSYSTEM</p>
          <div style={{display:"flex",flexDirection:"column",gap:6}}>
            {roles.map((r,i)=>(
              <div key={i} style={{background:t.card,border:`1px solid ${t.border}`,borderRadius:10,
                padding:"9px 12px",display:"flex",alignItems:"center",gap:10,backdropFilter:"blur(8px)"}}>
                <span style={{fontSize:16,width:22,textAlign:"center"}}>{r.emoji}</span>
                <span style={{flex:1,fontSize:12,fontWeight:600,color:t.text}}>
                  {r.label}{r.isNew&&<span style={{fontSize:9,color:t.primary,marginLeft:4}}>★新</span>}
                </span>
                <span style={{fontSize:9,padding:"2px 7px",borderRadius:8,background:`${t.glow}`,
                  color:t.primary,fontFamily:"sans-serif",fontWeight:700}}>{r.badge}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      {/* Footer */}
      <div style={{position:"relative",zIndex:1,borderTop:`1px solid ${t.border}`,padding:"10px 28px",
        display:"flex",justifyContent:"space-between",alignItems:"center"}}>
        <div style={{display:"flex",gap:8}}>
          {["FastAPI","Vue 3","PostgreSQL+pgvector","Redis","Docker"].map(tech=>(
            <span key={tech} style={{fontSize:9,color:t.textSub,padding:"2px 8px",
              border:`1px solid ${t.border}`,borderRadius:3,fontFamily:"sans-serif"}}>{tech}</span>
          ))}
        </div>
        <span style={{fontSize:9,color:t.textSub,fontFamily:"sans-serif"}}>2026-02-25 · 49 AGENTS · 34+ COACH ENDPOINTS</span>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// 组件 2：角色首页卡片预览
// ══════════════════════════════════════════════════════════════════════
function RoleHomeCard({ role, themeKey }) {
  const p = ROLE_HOME_PALETTES[role][themeKey];
  const isDark = themeKey === "vibrant";

  const content = {
    observer: {
      title: "开始了解自己", sub: "体验者 · L0",
      body: () => (
        <>
          <div style={{background:isDark?"rgba(255,255,255,0.08)":p.card,borderRadius:12,padding:12,marginBottom:8,border:`1px solid ${p.border}`}}>
            <div style={{fontSize:12,fontWeight:700,color:p.text,marginBottom:8}}>最近有没有这些困扰？</div>
            <div style={{display:"flex",flexWrap:"wrap",gap:6}}>
              {["😴 睡不好","📊 血糖波动","⚖️ 体重","🌧️ 情绪"].map((tag,i)=>(
                <span key={tag} style={{padding:"5px 10px",borderRadius:20,fontSize:11,cursor:"pointer",
                  background:i===1?p.primary:"transparent",color:i===1?"#fff":p.sub,
                  border:`1px solid ${i===1?p.primary:p.border}`}}>{tag}</span>
              ))}
            </div>
          </div>
          <div style={{background:p.primary,borderRadius:10,padding:"11px 14px",color:"#fff",textAlign:"center",fontSize:13,fontWeight:700,cursor:"pointer"}}>
            3分钟了解你现在的行为阶段 →
          </div>
          <div style={{marginTop:8,background:isDark?"rgba(255,255,255,0.06)":"rgba(0,0,0,0.04)",borderRadius:10,padding:"10px 12px",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <div>
              <div style={{fontSize:12,fontWeight:600,color:p.text}}>AI 健康向导</div>
              <div style={{fontSize:10,color:p.sub}}>有什么想聊的？我在</div>
            </div>
            <div style={{textAlign:"center"}}>
              <div style={{fontSize:20,fontWeight:800,color:p.primary}}>3</div>
              <div style={{fontSize:9,color:p.sub}}>次/今日</div>
            </div>
          </div>
        </>
      ),
    },
    grower: {
      title: "第14天 · 保持节奏", sub: "成长者 · L1",
      body: () => (
        <>
          <div style={{display:"flex",gap:10,marginBottom:10}}>
            <div style={{background:isDark?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.04)",borderRadius:10,padding:10,textAlign:"center",flex:1,border:`1px solid ${p.border}`}}>
              <div style={{fontSize:22}}>🔥</div>
              <div style={{fontSize:18,fontWeight:800,color:p.primary}}>14</div>
              <div style={{fontSize:10,color:p.sub}}>连续天数</div>
            </div>
            <div style={{background:isDark?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.04)",borderRadius:10,padding:10,textAlign:"center",flex:1,border:`1px solid ${p.border}`}}>
              <div style={{fontSize:22}}>📊</div>
              <div style={{fontSize:18,fontWeight:800,color:p.primary}}>78</div>
              <div style={{fontSize:10,color:p.sub}}>行为稳定度</div>
            </div>
          </div>
          {["晨间冥想 15min","蔬菜摄入打卡","饭后散步 20min"].map((task,i)=>(
            <div key={i} style={{display:"flex",alignItems:"center",gap:10,padding:"9px 12px",
              background:isDark?"rgba(255,255,255,0.06)":p.card,borderRadius:10,marginBottom:6,
              border:`1px solid ${p.border}`}}>
              <div style={{width:16,height:16,borderRadius:"50%",background:i===0?p.primary:"transparent",
                border:`2px solid ${i===0?p.primary:p.border}`,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
                {i===0&&<span style={{fontSize:9,color:"#fff"}}>✓</span>}
              </div>
              <span style={{fontSize:12,color:i===0?p.sub:p.text,textDecoration:i===0?"line-through":"none"}}>{task}</span>
            </div>
          ))}
        </>
      ),
    },
    coach: {
      title: "今日工作台", sub: "行为健康教练 · L3",
      body: () => (
        <>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:8,marginBottom:10}}>
            {[{n:"3",l:"待审核",c:"#F44336"},{n:"12",l:"活跃学员",c:p.primary},{n:"2",l:"高风险",c:"#FF9800"}].map(m=>(
              <div key={m.l} style={{background:isDark?"rgba(255,255,255,0.08)":p.card,borderRadius:10,padding:"10px 8px",textAlign:"center",border:`1px solid ${p.border}`}}>
                <div style={{fontSize:20,fontWeight:800,color:m.c}}>{m.n}</div>
                <div style={{fontSize:10,color:p.sub}}>{m.l}</div>
              </div>
            ))}
          </div>
          <div style={{fontSize:11,fontWeight:700,color:p.sub,marginBottom:6}}>AI副驾驶 待审核推送</div>
          {[{name:"李同学",risk:"高风险",score:28,rc:"#F44336"},{name:"王同学",risk:"需关注",score:45,rc:"#FF9800"}].map(s=>(
            <div key={s.name} style={{display:"flex",alignItems:"center",gap:10,padding:"9px 12px",
              background:isDark?"rgba(255,255,255,0.06)":p.card,borderRadius:10,marginBottom:6,border:`1px solid ${p.border}`}}>
              <div style={{width:28,height:28,borderRadius:"50%",background:p.primary,color:"#fff",
                display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:700,flexShrink:0}}>{s.name[0]}</div>
              <div style={{flex:1}}>
                <div style={{fontSize:12,fontWeight:600,color:p.text}}>{s.name}</div>
                <div style={{height:3,background:isDark?"rgba(255,255,255,0.1)":"#eee",borderRadius:2,marginTop:3}}>
                  <div style={{width:`${s.score}%`,height:"100%",background:s.rc,borderRadius:2}}/>
                </div>
              </div>
              <span style={{fontSize:10,padding:"2px 8px",borderRadius:8,background:`${s.rc}15`,color:s.rc,fontWeight:700}}>{s.risk}</span>
            </div>
          ))}
        </>
      ),
    },
  };

  const cfg = content[role];

  return (
    <div style={{background:p.bg,borderRadius:18,overflow:"hidden",border:`1px solid ${p.border}`,fontFamily:"'Noto Serif SC',serif"}}>
      <div style={{background:p.hero,padding:"18px 16px 20px",color:"#fff"}}>
        <div style={{fontSize:10,opacity:0.75,letterSpacing:1,marginBottom:3}}>{cfg.sub}</div>
        <div style={{fontSize:20,fontWeight:800}}>{cfg.title}</div>
      </div>
      <div style={{padding:14}}>{cfg.body()}</div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// 组件 3：教练队伍建设（完全对齐体系全景文档）
// ══════════════════════════════════════════════════════════════════════
function CoachBuildPage() {
  const [tab, setTab] = useState("journey");
  const [expanded, setExpanded] = useState(null);

  // 成长路径 — 对应平台真实晋级体系 L0→L5
  const journey = [
    {
      key: "L0→L1",
      from: "L0", to: "L1",
      fromLabel: "观察员", toLabel: "成长者",
      emoji: "👀→🌱",
      title: "从观察到行动",
      desc: "完成首次行为评估，开始打卡养成",
      stageColor: COACH_LEVELS.L1.color,
      points: { G: 100 },
      coach_req: COACH_UPGRADE_REQ["L0→L1"],
      trust: "信任分需达到 building 阶段（≥30%）",
      highlight: null,
    },
    {
      key: "L1→L2",
      from: "L1", to: "L2",
      fromLabel: "成长者", toLabel: "分享者",
      emoji: "🌱→💬",
      title: "从个人到社区",
      desc: "行为稳定后开始影响他人，贡献内容",
      stageColor: COACH_LEVELS.L2.color,
      points: { G: 500, C: 50 },
      coach_req: COACH_UPGRADE_REQ["L1→L2"],
      trust: "信任分需达到 established（≥50%）",
      highlight: null,
    },
    {
      key: "L2→L3",
      from: "L2", to: "L3",
      fromLabel: "分享者", toLabel: "行为健康教练",
      emoji: "💬→🎯",
      title: "★ 成为专业教练",
      desc: "通过认证考试，开始正式带教学员",
      stageColor: COACH_LEVELS.L3.color,
      points: { G: 800, C: 200, I: 50 },
      coach_req: COACH_UPGRADE_REQ["L2→L3"],
      trust: "需要 4个L1同道者 + 通过认证考试",
      highlight: "EXAM",
      examNote: "需通过「行为健康教练」认证考试（理论+技能+综合三维评分）",
      ironLaw: "成为教练后，所有AI建议必须经你审核才能推送给学员（铁律）",
    },
    {
      key: "L3→L4",
      from: "L3", to: "L4",
      fromLabel: "行为健康教练", toLabel: "行为健康促进师",
      emoji: "🎯→⭐",
      title: "从教练到促进师",
      desc: "系统放大器，管理更大范围的组织与区域",
      stageColor: COACH_LEVELS.L4.color,
      points: { G: 1500, C: 600, I: 200 },
      coach_req: COACH_UPGRADE_REQ["L3→L4"],
      trust: "需要 4个L2同道者 + 通过促进师认证",
      highlight: "EXAM",
    },
    {
      key: "L4→L5",
      from: "L4", to: "L5",
      fromLabel: "行为健康促进师", toLabel: "大师",
      emoji: "⭐→🏆",
      title: "学科文明层",
      desc: "理论范式与传承者，平台最高专业级别",
      stageColor: COACH_LEVELS.L5.color,
      points: { G: 3000, C: 1500, I: 600 },
      coach_req: COACH_UPGRADE_REQ["L4→L5"],
      trust: "需要 4个L3同道者 + 通过大师认证",
      highlight: "EXAM",
    },
  ];

  // 核心铁律说明
  const ironLaws = [
    {
      icon: "🤖",
      title: "AI→审核→推送（铁律）",
      desc: "所有 AI 生成的建议、处方、推送，必须先经教练在「CoachPushQueue」中审核修改后才可推送给用户。绝不允许 AI 内容直接触达用户。",
      color: "#F44336",
    },
    {
      icon: "⚡",
      title: "CrisisAgent 优先级 0",
      desc: "危机信号由 CrisisAgent 最先拦截（优先级0），教练随后跟进。教练不能关闭 Crisis 通道。",
      color: "#FF9800",
    },
    {
      icon: "📋",
      title: "推送审批 72 小时超时",
      desc: "教练审批队列中的 pending 项目超过 72 小时自动变为 expired，避免过期内容推送给学员。",
      color: "#1890ff",
    },
    {
      icon: "🔒",
      title: "教练只管辖三类学员",
      desc: "教练只能管理 Observer(L0) / Grower(L1) / Sharer(L2)，不能越级干预其他教练或管理员的工作范围。",
      color: "#52c41a",
    },
  ];

  // AI 工具体系
  const aiTools = [
    { icon: "🤖", name: "CoachCopilotAgent",     desc: "教练副驾驶·预警检查 + 学员状态 + 依从率干预 + 周报生成",      priority: "P2·权重0.85" },
    { icon: "💊", name: "AI行为处方生成",          desc: "copilot_prescription_service·SPI诊断+六因分析+处方生成",     priority: "云优先·25s超时" },
    { icon: "💡", name: "AI消息建议",              desc: "coach_ai_suggestion_service·鼓励/提醒/建议/微行动 四类型",   priority: "规则+LLM双轨" },
    { icon: "📊", name: "AI推送推荐引擎",          desc: "push_recommendation_service·设备信号+行为事实+评估间隔",     priority: "实时分析" },
  ];

  // 推送来源类型（11种，来自体系文档 §3.4）
  const pushSources = [
    "challenge","device_alert","micro_action","ai_recommendation","system",
    "coach_message","coach_reminder","assessment_push","micro_action_assign","vision_rx","xzb_expert",
  ];
  const pushLabels: Record<string,string> = {
    challenge:"挑战活动", device_alert:"设备预警", micro_action:"微行动",
    ai_recommendation:"AI推荐", system:"系统通知", coach_message:"教练消息",
    coach_reminder:"教练提醒", assessment_push:"评估推送", micro_action_assign:"微行动分配",
    vision_rx:"视力处方", xzb_expert:"行诊智伴",
  };

  // 绩效看板（KPI 维度，来自 CoachKpiMetric ORM）
  const kpiDimensions = [
    { label: "活跃学员数",   key: "active_client_count",        unit: "人" },
    { label: "课程完成率",   key: "session_completion_rate",    unit: "%" },
    { label: "学员留存率",   key: "client_retention_rate",      unit: "%" },
    { label: "阶段晋级率",   key: "stage_advancement_rate",     unit: "%" },
    { label: "评估覆盖率",   key: "assessment_coverage",        unit: "%" },
    { label: "干预依从率",   key: "intervention_adherence",     unit: "%" },
    { label: "学员满意度",   key: "client_satisfaction",        unit: "分" },
    { label: "安全事故数",   key: "safety_incident_count",      unit: "次" },
    { label: "督导合规率",   key: "supervision_compliance",     unit: "%" },
    { label: "知识贡献",     key: "knowledge_contribution",     unit: "篇" },
  ];

  const tabs = [
    { key: "journey",  label: "📈 成长路径" },
    { key: "ironlaw",  label: "🔒 工作铁律" },
    { key: "aitools",  label: "🤖 AI工具" },
    { key: "kpi",      label: "📊 绩效体系" },
    { key: "apply",    label: "🚀 立即申请" },
  ];

  const fmtReq = (req) => {
    const parts = [];
    if (req.students)    parts.push(`带教学员 ≥ ${req.students}人`);
    if (req.messages)    parts.push(`发送消息 ≥ ${req.messages}条`);
    if (req.assessments) parts.push(`完成评估 ≥ ${req.assessments}次`);
    if (req.improved)    parts.push(`改善学员 ≥ ${req.improved}人`);
    return parts;
  };

  return (
    <div style={{fontFamily:"'Noto Serif SC',serif",background:"#F4F6FB",minHeight:"100%"}}>
      {/* Hero */}
      <div style={{background:"linear-gradient(135deg,#1B2A3B,#0D3B6B,#1565C0)",padding:"36px 28px 44px",color:"#fff",position:"relative",overflow:"hidden"}}>
        <div style={{position:"absolute",top:-60,right:-60,width:280,height:280,borderRadius:"50%",background:"rgba(255,255,255,0.04)"}}/>
        <div style={{position:"relative",zIndex:1}}>
          <div style={{display:"inline-block",background:"rgba(255,255,255,0.13)",borderRadius:20,
            padding:"3px 14px",fontSize:10,letterSpacing:2,marginBottom:14}}>🎯 COACH SYSTEM · 教练体系</div>
          <h1 style={{fontSize:32,fontWeight:900,margin:"0 0 10px",lineHeight:1.2}}>
            行健教练队伍建设<br/>
            <span style={{color:"#90CAF9",fontSize:22}}>L0 → L5 · 六级晋级 · AI辅助</span>
          </h1>
          <p style={{fontSize:13,opacity:0.8,margin:"0 0 22px",maxWidth:480,lineHeight:1.7}}>
            教练体系是 AI 与用户之间的<strong>人机协同桥梁</strong>。<br/>
            34+ API 端点 · 7 ORM 模型 · 4 核心服务 · 20+ 前端组件
          </p>
          {/* Stats */}
          <div style={{display:"flex",gap:20,flexWrap:"wrap"}}>
            {[
              {n:"34+", l:"API端点"}, {n:"7",   l:"ORM模型"},
              {n:"4",   l:"核心服务"},{n:"20+", l:"前端组件"},
              {n:"3",   l:"定时任务"},{n:"11",  l:"推送来源类型"},
            ].map(s=>(
              <div key={s.l} style={{textAlign:"center"}}>
                <div style={{fontSize:24,fontWeight:900,fontFamily:"sans-serif"}}>{s.n}</div>
                <div style={{fontSize:10,opacity:0.6}}>{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Role level overview strip */}
      <div style={{background:"#fff",borderBottom:"1px solid #eee",padding:"12px 28px",
        display:"flex",gap:0,overflowX:"auto"}}>
        {Object.entries(COACH_LEVELS).map(([lv,cfg])=>(
          <div key={lv} style={{display:"flex",alignItems:"center",gap:0,flex:"0 0 auto"}}>
            <div style={{display:"flex",flexDirection:"column",alignItems:"center",padding:"0 14px"}}>
              <div style={{width:32,height:32,borderRadius:"50%",background:`${cfg.color}20`,
                border:`2px solid ${cfg.color}`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,marginBottom:3}}>
                {cfg.emoji}
              </div>
              <div style={{fontSize:10,fontWeight:700,color:cfg.color}}>{lv}</div>
              <div style={{fontSize:9,color:"#888",maxWidth:56,textAlign:"center",lineHeight:1.3}}>{cfg.label}</div>
            </div>
            {lv!=="L5"&&<div style={{color:"#DDD",fontSize:14,flexShrink:0}}>→</div>}
          </div>
        ))}
      </div>

      {/* Tab nav */}
      <div style={{background:"#fff",borderBottom:"1px solid #eee",display:"flex",padding:"0 20px",
        position:"sticky",top:0,zIndex:10,overflowX:"auto"}}>
        {tabs.map(tb=>(
          <button key={tb.key} onClick={()=>setTab(tb.key)} style={{
            padding:"14px 18px",border:"none",background:"transparent",fontSize:13,cursor:"pointer",
            fontWeight:tab===tb.key?700:400,color:tab===tb.key?"#1565C0":"#888",
            borderBottom:tab===tb.key?"2px solid #1565C0":"2px solid transparent",
            transition:"all 0.2s",fontFamily:"'Noto Serif SC',serif",whiteSpace:"nowrap",
          }}>{tb.label}</button>
        ))}
      </div>

      <div style={{padding:"20px 20px 40px"}}>

        {/* ── Tab: Journey ── */}
        {tab==="journey"&&(
          <div>
            <div style={{background:"#E3F2FD",borderRadius:12,padding:"12px 16px",marginBottom:16,
              border:"1px solid rgba(21,101,192,0.15)"}}>
              <div style={{fontSize:12,fontWeight:700,color:"#1565C0",marginBottom:4}}>
                📌 成为教练的核心路径
              </div>
              <div style={{fontSize:12,color:"#444",lineHeight:1.7}}>
                任何用户均从 L0 观察员起步。到达 L2 分享者后，即可申请「教练候选」。
                通过认证考试（理论+技能+综合）并满足带教数量要求后，正式晋升为 L3 行为健康教练。
              </div>
            </div>

            {journey.map((step,i)=>(
              <div key={step.key}>
                <div onClick={()=>setExpanded(expanded===i?null:i)}
                  style={{background:"#fff",borderRadius:16,padding:16,marginBottom:0,
                    border:`2px solid ${expanded===i?step.stageColor:"#F0F0F0"}`,
                    cursor:"pointer",transition:"all 0.2s",
                    boxShadow:expanded===i?`0 4px 16px ${step.stageColor}25`:"0 1px 6px rgba(0,0,0,0.05)"}}>
                  <div style={{display:"flex",alignItems:"center",gap:12}}>
                    {/* Level icons */}
                    <div style={{display:"flex",alignItems:"center",gap:6,flexShrink:0}}>
                      <div style={{width:36,height:36,borderRadius:10,background:`${COACH_LEVELS[step.from].color}15`,
                        border:`2px solid ${COACH_LEVELS[step.from].color}40`,display:"flex",flexDirection:"column",
                        alignItems:"center",justifyContent:"center"}}>
                        <div style={{fontSize:14}}>{COACH_LEVELS[step.from].emoji}</div>
                        <div style={{fontSize:8,color:COACH_LEVELS[step.from].color,fontWeight:700}}>{step.from}</div>
                      </div>
                      <div style={{color:"#CCC",fontSize:14}}>→</div>
                      <div style={{width:36,height:36,borderRadius:10,background:`${step.stageColor}15`,
                        border:`2px solid ${step.stageColor}40`,display:"flex",flexDirection:"column",
                        alignItems:"center",justifyContent:"center"}}>
                        <div style={{fontSize:14}}>{COACH_LEVELS[step.to].emoji}</div>
                        <div style={{fontSize:8,color:step.stageColor,fontWeight:700}}>{step.to}</div>
                      </div>
                    </div>
                    <div style={{flex:1}}>
                      <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:2}}>
                        <span style={{fontSize:14,fontWeight:700,color:"#222"}}>{step.title}</span>
                        {step.highlight==="EXAM"&&(
                          <span style={{fontSize:9,background:"rgba(250,173,20,0.15)",color:"#faad14",
                            padding:"2px 8px",borderRadius:8,fontWeight:700,border:"1px solid rgba(250,173,20,0.3)"}}>
                            需考试
                          </span>
                        )}
                      </div>
                      <div style={{fontSize:11,color:"#888"}}>{step.desc}</div>
                    </div>
                    <span style={{color:"#CCC",fontSize:12,transform:expanded===i?"rotate(90deg)":"none",transition:"0.2s"}}>▶</span>
                  </div>

                  {expanded===i&&(
                    <div style={{marginTop:14,paddingTop:14,borderTop:`1px solid ${step.stageColor}20`}}>
                      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
                        {/* Points */}
                        <div style={{background:step.stageColor+"10",borderRadius:10,padding:12}}>
                          <div style={{fontSize:11,fontWeight:700,color:step.stageColor,marginBottom:6}}>📊 积分要求</div>
                          {Object.entries(step.points).map(([k,v])=>(
                            <div key={k} style={{display:"flex",justifyContent:"space-between",
                              fontSize:12,color:"#444",marginBottom:4}}>
                              <span>{{G:"成长点(G)",C:"贡献点(C)",I:"影响力(I)"}[k]}</span>
                              <span style={{fontWeight:700,color:step.stageColor}}>≥ {v}</span>
                            </div>
                          ))}
                        </div>
                        {/* Coach specific */}
                        <div style={{background:"rgba(0,0,0,0.03)",borderRadius:10,padding:12}}>
                          <div style={{fontSize:11,fontWeight:700,color:"#1565C0",marginBottom:6}}>🎯 教练要求</div>
                          {fmtReq(step.coach_req).map(r=>(
                            <div key={r} style={{fontSize:11,color:"#555",marginBottom:3}}>• {r}</div>
                          ))}
                        </div>
                      </div>
                      {/* Trust / exam / iron law notes */}
                      <div style={{marginTop:10,padding:10,background:"rgba(0,0,0,0.02)",
                        borderRadius:8,borderLeft:`3px solid ${step.stageColor}`}}>
                        <div style={{fontSize:11,color:"#666"}}>{step.trust}</div>
                        {step.examNote&&<div style={{fontSize:11,color:"#faad14",marginTop:4}}>⚠ {step.examNote}</div>}
                        {step.ironLaw&&<div style={{fontSize:11,color:"#F44336",marginTop:4,fontWeight:700}}>🔒 {step.ironLaw}</div>}
                      </div>
                    </div>
                  )}
                </div>
                {i<journey.length-1&&<div style={{height:8,display:"flex",justifyContent:"center",alignItems:"center",color:"#DDD",fontSize:12}}>↕</div>}
              </div>
            ))}
          </div>
        )}

        {/* ── Tab: Iron Laws ── */}
        {tab==="ironlaw"&&(
          <div>
            <div style={{background:"#FFF3E0",borderRadius:12,padding:"14px 16px",marginBottom:16,
              border:"1px solid rgba(230,81,0,0.2)"}}>
              <div style={{fontSize:13,fontWeight:700,color:"#E65100",marginBottom:6}}>
                ⚠ 核心铁律：AI → 教练审核 → 推送
              </div>
              <div style={{fontSize:13,color:"#555",lineHeight:1.8}}>
                <strong>所有 AI 生成的建议、处方、推送</strong>，必须先进入 CoachPushQueue（coach_schema），
                经教练在工作台审核修改后才可推送给用户。<br/>
                绝不允许 AI 内容直接触达用户。<br/>
                <span style={{color:"#E65100",fontWeight:700}}>违反此铁律将触发平台安全告警。</span>
              </div>
            </div>

            {/* Push workflow */}
            <div style={{background:"#fff",borderRadius:14,padding:18,marginBottom:14,boxShadow:"0 1px 8px rgba(0,0,0,0.05)"}}>
              <div style={{fontSize:14,fontWeight:700,color:"#222",marginBottom:14}}>推送审批完整流程</div>
              <div style={{display:"flex",flexDirection:"column",gap:0}}>
                {[
                  {step:"1",text:"AI推荐引擎生成建议（push_recommendation_service）",color:"#1890ff"},
                  {step:"2",text:"进入 CoachPushQueue → status = \"pending\"",color:"#faad14"},
                  {step:"3",text:"教练在工作台查看 · 修改内容 · 设定投递时间",color:"#722ed1"},
                  {step:"4a",text:"审批通过 → 激活处方 → 生成每日任务 → WebSocket 推送通知",color:"#52c41a"},
                  {step:"4b",text:"审批拒绝 → 记录退回原因（coach_review_logs 审计）",color:"#F44336"},
                  {step:"⏱",text:"72小时未处理 → 自动 expired（定时任务清理）",color:"#8c8c8c"},
                ].map(item=>(
                  <div key={item.step} style={{display:"flex",alignItems:"flex-start",gap:12,marginBottom:8}}>
                    <div style={{width:28,height:28,borderRadius:"50%",background:`${item.color}15`,
                      border:`2px solid ${item.color}30`,display:"flex",alignItems:"center",justifyContent:"center",
                      fontSize:10,fontWeight:700,color:item.color,flexShrink:0}}>{item.step}</div>
                    <div style={{flex:1,fontSize:13,color:"#444",paddingTop:4,lineHeight:1.6}}>{item.text}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Push source types */}
            <div style={{background:"#fff",borderRadius:14,padding:18,marginBottom:14,boxShadow:"0 1px 8px rgba(0,0,0,0.05)"}}>
              <div style={{fontSize:14,fontWeight:700,color:"#222",marginBottom:12}}>
                推送来源类型（11种）
              </div>
              <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
                {pushSources.map(s=>(
                  <span key={s} style={{padding:"5px 12px",borderRadius:20,fontSize:11,
                    background:s==="xzb_expert"?"rgba(250,173,20,0.1)":s==="vision_rx"?"rgba(82,196,26,0.1)":"rgba(24,144,255,0.08)",
                    color:s==="xzb_expert"?"#faad14":s==="vision_rx"?"#52c41a":"#1890ff",
                    border:`1px solid ${s==="xzb_expert"?"rgba(250,173,20,0.3)":s==="vision_rx"?"rgba(82,196,26,0.3)":"rgba(24,144,255,0.2)"}`,
                    fontFamily:"sans-serif"}}>
                    {pushLabels[s]}
                  </span>
                ))}
              </div>
            </div>

            {/* 4 iron laws */}
            <div style={{display:"flex",flexDirection:"column",gap:10}}>
              {ironLaws.map(law=>(
                <div key={law.title} style={{background:"#fff",borderRadius:12,padding:16,
                  borderLeft:`3px solid ${law.color}`,boxShadow:"0 1px 6px rgba(0,0,0,0.04)"}}>
                  <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:6}}>
                    <span style={{fontSize:20}}>{law.icon}</span>
                    <div style={{fontSize:13,fontWeight:700,color:law.color}}>{law.title}</div>
                  </div>
                  <div style={{fontSize:12,color:"#555",lineHeight:1.7}}>{law.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Tab: AI Tools ── */}
        {tab==="aitools"&&(
          <div>
            <div style={{background:"#F0F4FF",borderRadius:12,padding:"12px 16px",marginBottom:16,
              border:"1px solid rgba(24,144,255,0.15)"}}>
              <div style={{fontSize:12,fontWeight:700,color:"#1565C0",marginBottom:4}}>
                🤖 双轨 AI 策略（规则引擎 + LLM 增强）
              </div>
              <div style={{fontSize:12,color:"#444",lineHeight:1.6}}>
                规则引擎始终运行（baseline），LLM 增强在可用时激活，5分钟冷却，<strong>永不阻塞主流程</strong>。
                云优先（DeepSeek/Qwen）→ Ollama fallback。
              </div>
            </div>

            {aiTools.map(tool=>(
              <div key={tool.name} style={{background:"#fff",borderRadius:14,padding:16,marginBottom:10,
                boxShadow:"0 1px 8px rgba(0,0,0,0.05)"}}>
                <div style={{display:"flex",gap:12,alignItems:"flex-start"}}>
                  <span style={{fontSize:28,flexShrink:0}}>{tool.icon}</span>
                  <div style={{flex:1}}>
                    <div style={{fontSize:14,fontWeight:700,color:"#222",marginBottom:4}}>{tool.name}</div>
                    <div style={{fontSize:12,color:"#555",lineHeight:1.6,marginBottom:6}}>{tool.desc}</div>
                    <span style={{fontSize:10,background:"rgba(24,144,255,0.08)",color:"#1890ff",
                      padding:"2px 10px",borderRadius:10,border:"1px solid rgba(24,144,255,0.2)",
                      fontFamily:"sans-serif"}}>{tool.priority}</span>
                  </div>
                </div>
              </div>
            ))}

            {/* Agent details */}
            <div style={{background:"#fff",borderRadius:14,padding:18,boxShadow:"0 1px 8px rgba(0,0,0,0.05)"}}>
              <div style={{fontSize:14,fontWeight:700,color:"#222",marginBottom:12}}>CoachCopilotAgent 触发逻辑</div>
              <div style={{fontFamily:"monospace",background:"#F8F9FA",borderRadius:8,padding:14,fontSize:11,color:"#333",lineHeight:1.8}}>
                {`关键词: 教练/学员/报告/周报/预警/异常\n       处方/干预/微行动/建议/指导/BFR\n\n触发场景:\n  血糖 >11.1 或 <3.9  → 高风险预警\n  睡眠 <5h            → 睡眠告警\n  HRV <20ms           → 生理预警\n  依从率 <30%         → 超高强度干预建议\n  依从率 <60%         → 处方复查建议\n\n优先级: 2  |  权重: 0.85  |  置信度: 0.9(预警) / 0.7(正常)`}
              </div>
            </div>
          </div>
        )}

        {/* ── Tab: KPI ── */}
        {tab==="kpi"&&(
          <div>
            <div style={{background:"#fff",borderRadius:14,padding:18,marginBottom:14,boxShadow:"0 1px 8px rgba(0,0,0,0.05)"}}>
              <div style={{fontSize:14,fontWeight:700,color:"#222",marginBottom:4}}>绩效周期</div>
              <div style={{fontSize:12,color:"#888",marginBottom:14}}>
                日/周/月 三个周期独立计算（CoachKpiMetric ORM，period_type: day/week/month）
              </div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
                {kpiDimensions.map((d,i)=>(
                  <div key={d.key} style={{display:"flex",alignItems:"center",gap:10,
                    padding:"10px 12px",background:"#FAFAFA",borderRadius:10,
                    border:"1px solid #F0F0F0"}}>
                    <div style={{width:32,height:32,borderRadius:8,background:`hsl(${i*36},70%,92%)`,
                      display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,flexShrink:0}}>
                      {["👥","📅","🔄","📈","📋","💊","😊","⚠","🎓","📝"][i]}
                    </div>
                    <div>
                      <div style={{fontSize:12,fontWeight:600,color:"#333"}}>{d.label}</div>
                      <div style={{fontSize:10,color:"#aaa",fontFamily:"sans-serif"}}>{d.unit}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Auto escalation */}
            <div style={{background:"#FFF8E1",borderRadius:14,padding:16,marginBottom:14,
              border:"1px solid rgba(255,193,7,0.3)"}}>
              <div style={{fontSize:13,fontWeight:700,color:"#F57F17",marginBottom:8}}>⚡ 自动升级机制（08:00 定时任务）</div>
              <div style={{fontSize:12,color:"#555",lineHeight:1.8}}>
                每日 08:00，系统检测<strong>无教练学员</strong>，自动创建 CoachPushQueue 条目，
                通知上级督导或促进师介入，确保每位学员都有教练跟进。<br/>
                KPI 状态：green / yellow / red，红色自动推送给督导（auto_escalated = true）。
              </div>
            </div>

            {/* Trust score */}
            <div style={{background:"#fff",borderRadius:14,padding:18,boxShadow:"0 1px 8px rgba(0,0,0,0.05)"}}>
              <div style={{fontSize:14,fontWeight:700,color:"#222",marginBottom:14}}>
                信任分六信号模型（trust_score_service）
              </div>
              {[
                {signal:"对话深度",    weight:"25%", note:"avg(note_length) / 50"},
                {signal:"主动回归",    weight:"20%", note:"consecutive_days / total_task_days"},
                {signal:"话题开放度",  weight:"15%", note:"distinct_tags / 6"},
                {signal:"情绪表达",    weight:"15%", note:"emotion_notes / total_notes"},
                {signal:"信息分享",    weight:"15%", note:"rich_checkins / total_checkins"},
                {signal:"好奇心",      weight:"10%", note:"notes_present / total"},
              ].map(s=>(
                <div key={s.signal} style={{display:"flex",alignItems:"center",gap:12,marginBottom:8}}>
                  <div style={{width:36,fontSize:12,fontWeight:700,color:"#1565C0",flexShrink:0}}>{s.weight}</div>
                  <div style={{flex:1}}>
                    <div style={{height:5,background:"#eee",borderRadius:3,overflow:"hidden"}}>
                      <div style={{height:"100%",background:"linear-gradient(90deg,#1565C0,#42A5F5)",
                        width:s.weight,borderRadius:3}}/>
                    </div>
                  </div>
                  <div style={{width:80,fontSize:11,fontWeight:600,color:"#333"}}>{s.signal}</div>
                  <div style={{flex:1,fontSize:10,color:"#aaa",fontFamily:"sans-serif"}}>{s.note}</div>
                </div>
              ))}
              <div style={{marginTop:12,display:"flex",gap:8,flexWrap:"wrap"}}>
                {[
                  {level:"not_established",range:"<30%",  desc:"禁止行为建议",color:"#F44336"},
                  {level:"building",       range:"30-50%", desc:"温和引入评估", color:"#FF9800"},
                  {level:"established",    range:">50%",   desc:"全面干预允许", color:"#52c41a"},
                ].map(t=>(
                  <div key={t.level} style={{padding:"8px 12px",borderRadius:10,
                    background:`${t.color}10`,border:`1px solid ${t.color}30`}}>
                    <div style={{fontSize:11,fontWeight:700,color:t.color}}>{t.range} · {t.level}</div>
                    <div style={{fontSize:10,color:"#666",marginTop:2}}>{t.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Tab: Apply ── */}
        {tab==="apply"&&(
          <div>
            <div style={{background:"#fff",borderRadius:16,padding:20,marginBottom:14,boxShadow:"0 2px 12px rgba(0,0,0,0.06)"}}>
              <div style={{fontSize:15,fontWeight:700,color:"#222",marginBottom:16}}>
                🚀 申请成为教练候选人（需达到 L2 分享者）
              </div>
              {[
                {label:"当前阶段",type:"select",options:["L0 观察员","L1 成长者","L2 分享者"]},
                {label:"你的健康改变经历",type:"textarea",placeholder:"描述你经历的健康挑战和改变（100字以上），这将作为教练资质审核依据..."},
                {label:"期望专科方向",type:"select",options:["青少年视力保护","代谢综合征管理","职场压力与睡眠","慢病逆转","情绪与行为管理"]},
                {label:"推荐人（Coach/Supervisor用户名）",type:"input",placeholder:"可选，有推荐人将加速审核"},
              ].map(f=>(
                <div key={f.label} style={{marginBottom:14}}>
                  <div style={{fontSize:13,fontWeight:600,color:"#444",marginBottom:6}}>{f.label}</div>
                  {f.type==="textarea"?
                    <textarea placeholder={f.placeholder} style={{width:"100%",borderRadius:10,border:"1px solid #E0E0E0",
                      padding:"10px 12px",fontSize:12,minHeight:80,resize:"vertical",
                      fontFamily:"'Noto Serif SC',serif",boxSizing:"border-box"}}/>
                  :f.type==="select"?
                    <select style={{width:"100%",borderRadius:10,border:"1px solid #E0E0E0",
                      padding:"10px 12px",fontSize:12,background:"#fff",fontFamily:"'Noto Serif SC',serif"}}>
                      {f.options.map(o=><option key={o}>{o}</option>)}
                    </select>
                  :
                    <input placeholder={f.placeholder} style={{width:"100%",borderRadius:10,border:"1px solid #E0E0E0",
                      padding:"10px 12px",fontSize:12,fontFamily:"'Noto Serif SC',serif",boxSizing:"border-box"}}/>
                  }
                </div>
              ))}
              <button style={{width:"100%",padding:"14px",background:"linear-gradient(135deg,#1565C0,#1976D2)",
                color:"#fff",border:"none",borderRadius:12,fontSize:14,fontWeight:700,cursor:"pointer",
                fontFamily:"'Noto Serif SC',serif",boxShadow:"0 4px 16px rgba(21,101,192,0.35)"}}>
                提交申请 → 进入 L2→L3 审核流程
              </button>
              <p style={{fontSize:11,color:"#aaa",textAlign:"center",marginTop:8}}>
                API: POST /api/v1/coach/promotion-applications
              </p>
            </div>

            {/* Current openings */}
            <div style={{background:"#fff",borderRadius:16,padding:18,boxShadow:"0 1px 8px rgba(0,0,0,0.05)"}}>
              <div style={{fontSize:14,fontWeight:700,color:"#222",marginBottom:14}}>📢 当前急需专向</div>
              {[
                {domain:"青少年视力保护",count:8,urgent:true, desc:"VisionGuard 专项，与眼科Expert协作，行智诊疗接入"},
                {domain:"代谢综合征管理",count:5,urgent:true, desc:"慢病逆转领域，AI处方生成辅助，需基础健康知识"},
                {domain:"职场压力与睡眠",count:3,urgent:false,desc:"企业健康管理场景，数据驱动干预"},
              ].map(item=>(
                <div key={item.domain} style={{display:"flex",alignItems:"center",gap:12,padding:"12px 0",
                  borderBottom:"1px solid #F5F5F5"}}>
                  <div style={{flex:1}}>
                    <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:4}}>
                      <span style={{fontSize:13,fontWeight:700,color:"#222"}}>{item.domain}</span>
                      {item.urgent&&<span style={{fontSize:10,background:"#FFF3E0",color:"#E65100",
                        padding:"1px 8px",borderRadius:10,fontWeight:700}}>急需</span>}
                    </div>
                    <div style={{fontSize:11,color:"#888"}}>{item.desc}</div>
                  </div>
                  <div style={{textAlign:"center",flexShrink:0}}>
                    <div style={{fontSize:22,fontWeight:800,color:"#1565C0"}}>{item.count}</div>
                    <div style={{fontSize:10,color:"#aaa"}}>名额</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// 主 App
// ══════════════════════════════════════════════════════════════════════
export default function App() {
  const [page, setPage]         = useState("covers");
  const [coverTheme, setCover]  = useState("chenxi");
  const [role, setRole]         = useState("observer");
  const [homeTheme, setHome]    = useState("natural");

  return (
    <div style={{fontFamily:"'Noto Serif SC',serif",background:"#EDEEF2",minHeight:"100vh"}}>
      {/* Nav */}
      <div style={{background:"rgba(255,255,255,0.96)",backdropFilter:"blur(12px)",
        borderBottom:"1px solid rgba(0,0,0,0.07)",display:"flex",alignItems:"center",
        padding:"0 20px",position:"sticky",top:0,zIndex:200}}>
        <div style={{fontWeight:800,fontSize:17,color:"#1565C0",padding:"16px 16px 16px 0",marginRight:12,whiteSpace:"nowrap"}}>
          行健 设计系统
        </div>
        {[
          {key:"covers",   label:"🎨 5套封面"},
          {key:"homepages",label:"🏠 角色首页"},
          {key:"coach",    label:"🎯 教练队伍"},
        ].map(n=>(
          <button key={n.key} onClick={()=>setPage(n.key)} style={{
            padding:"18px 16px",border:"none",background:"transparent",fontSize:13,cursor:"pointer",
            fontWeight:page===n.key?700:400,color:page===n.key?"#1565C0":"#888",
            borderBottom:page===n.key?"2px solid #1565C0":"2px solid transparent",
            transition:"all 0.2s",fontFamily:"'Noto Serif SC',serif",whiteSpace:"nowrap",
          }}>{n.label}</button>
        ))}
        <div style={{marginLeft:"auto",fontSize:10,color:"#bbb",paddingRight:4}}>V5.3.0 · Migration 054</div>
      </div>

      {/* ── 封面 ── */}
      {page==="covers"&&(
        <div style={{padding:20}}>
          <h2 style={{fontSize:20,fontWeight:800,color:"#1A1A2E",margin:"0 0 4px"}}>5套封面风格</h2>
          <p style={{fontSize:12,color:"#888",margin:"0 0 16px"}}>点击切换 · 告别深蓝压抑 · 每套各有美学逻辑</p>
          {/* Switcher */}
          <div style={{display:"flex",gap:8,marginBottom:20,flexWrap:"wrap"}}>
            {Object.entries(COVER_THEMES).map(([k,t])=>(
              <button key={k} onClick={()=>setCover(k)} style={{
                padding:"10px 16px",borderRadius:50,border:`2px solid ${coverTheme===k?t.primary:"#DDD"}`,
                background:coverTheme===k?t.bg:"#fff",cursor:"pointer",transition:"all 0.2s",
                display:"flex",alignItems:"center",gap:8,
              }}>
                <div style={{width:14,height:14,borderRadius:"50%",background:t.hero}}/>
                <span style={{fontSize:13,fontWeight:coverTheme===k?700:400,color:coverTheme===k?t.primary:"#555"}}>
                  {t.name}
                </span>
                <span style={{fontSize:10,color:"#aaa"}}>{t.desc}</span>
              </button>
            ))}
          </div>
          <PlatformCover themeKey={coverTheme}/>
          {/* Thumbnails */}
          <h3 style={{fontSize:13,fontWeight:700,color:"#555",margin:"20px 0 12px"}}>全部5套缩略对比</h3>
          <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:12}}>
            {Object.entries(COVER_THEMES).map(([k,t])=>(
              <div key={k} onClick={()=>setCover(k)} style={{borderRadius:12,overflow:"hidden",cursor:"pointer",
                border:`2px solid ${coverTheme===k?t.primary:"#E0E0E0"}`,
                boxShadow:coverTheme===k?`0 4px 14px ${t.glow}`:"none",transition:"all 0.2s"}}>
                <div style={{height:72,background:t.bg,padding:10,display:"flex",alignItems:"center",gap:8}}>
                  <div style={{width:26,height:26,borderRadius:7,background:t.hero,
                    display:"flex",alignItems:"center",justifyContent:"center",fontSize:13,fontWeight:900,color:"#fff"}}>行</div>
                  <div>
                    <div style={{fontSize:11,fontWeight:700,color:t.text}}>{t.name}</div>
                    <div style={{fontSize:9,color:t.textSub}}>{t.nameEn}</div>
                  </div>
                </div>
                <div style={{background:t.card,padding:"6px 10px",borderTop:`1px solid ${t.border}`}}>
                  <div style={{fontSize:9,color:t.primary,fontWeight:600}}>{t.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 角色首页 ── */}
      {page==="homepages"&&(
        <div style={{padding:20}}>
          <h2 style={{fontSize:20,fontWeight:800,color:"#1A1A2E",margin:"0 0 4px"}}>角色首页 × 3套主题</h2>
          <p style={{fontSize:12,color:"#888",margin:"0 0 16px"}}>
            每位用户可在「个人设置」中切换主题 · 存入 user_preferences.home_theme
          </p>
          {/* Selectors */}
          <div style={{display:"flex",gap:16,flexWrap:"wrap",marginBottom:20}}>
            <div>
              <div style={{fontSize:11,color:"#888",marginBottom:6,fontWeight:600}}>选择角色</div>
              <div style={{display:"flex",gap:8}}>
                {[{k:"observer",l:"👀 Observer"},{k:"grower",l:"🌱 Grower"},{k:"coach",l:"🎯 Coach"}].map(r=>(
                  <button key={r.k} onClick={()=>setRole(r.k)} style={{
                    padding:"9px 14px",borderRadius:10,border:`2px solid ${role===r.k?"#1565C0":"#DDD"}`,
                    background:role===r.k?"#E3F0FF":"#fff",cursor:"pointer",fontSize:12,
                    fontWeight:role===r.k?700:400,color:role===r.k?"#1565C0":"#555",
                    fontFamily:"'Noto Serif SC',serif",
                  }}>{r.l}</button>
                ))}
              </div>
            </div>
            <div>
              <div style={{fontSize:11,color:"#888",marginBottom:6,fontWeight:600}}>选择主题</div>
              <div style={{display:"flex",gap:8}}>
                {Object.entries(HOME_THEMES).map(([k,t])=>(
                  <button key={k} onClick={()=>setHome(k)} style={{
                    padding:"9px 14px",borderRadius:10,border:`2px solid ${homeTheme===k?"#1565C0":"#DDD"}`,
                    background:homeTheme===k?"#E3F0FF":"#fff",cursor:"pointer",fontSize:12,
                    fontWeight:homeTheme===k?700:400,color:homeTheme===k?"#1565C0":"#555",
                    fontFamily:"'Noto Serif SC',serif",
                  }}>{t.icon} {t.name}</button>
                ))}
              </div>
            </div>
          </div>
          {/* Single preview */}
          <div style={{maxWidth:360,margin:"0 auto 24px"}}>
            <RoleHomeCard role={role} themeKey={homeTheme}/>
          </div>
          {/* 3-column compare */}
          <h3 style={{fontSize:13,fontWeight:700,color:"#555",marginBottom:12}}>
            三套主题对比（{COACH_LEVELS[role==="observer"?"L0":role==="grower"?"L1":"L3"].label}）
          </h3>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:14}}>
            {Object.entries(HOME_THEMES).map(([k,t])=>(
              <div key={k}>
                <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:8}}>
                  <span style={{fontSize:18}}>{t.icon}</span>
                  <div>
                    <div style={{fontSize:12,fontWeight:700,color:"#222"}}>{t.name}</div>
                    <div style={{fontSize:10,color:"#888"}}>{t.desc}</div>
                  </div>
                </div>
                <RoleHomeCard role={role} themeKey={k}/>
              </div>
            ))}
          </div>
          {/* Code hint */}
          <div style={{marginTop:20,background:"#1A1A2E",borderRadius:12,padding:16,fontFamily:"monospace"}}>
            <div style={{fontSize:10,color:"#64B5F6",marginBottom:8}}>// user_preferences 表存储结构</div>
            <pre style={{fontSize:11,color:"#E0E0E0",margin:0}}>{`{\n  "home_theme": "${homeTheme}",\n  "cover_style": "chenxi",\n  "font_size": "normal"\n}`}</pre>
          </div>
        </div>
      )}

      {/* ── 教练队伍 ── */}
      {page==="coach"&&<CoachBuildPage/>}
    </div>
  );
}
