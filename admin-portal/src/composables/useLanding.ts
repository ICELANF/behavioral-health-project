import { ref, computed, onMounted, onUnmounted, type Ref } from 'vue'

// ═══════ Theme System ═══════

export interface Theme {
  primary: string
  accent: string
  warm: string
  heroBg: string
  text: string
  textLight: string
}

export const THEMES: Record<string, Theme> = {
  home:       { primary: '#1a472a', accent: '#22c55e', warm: '#f0fdf4', heroBg: 'radial-gradient(ellipse at 30% 50%,#1a472a 0%,#0f2e1a 60%,#0a1f12 100%)', text: '#1a472a', textLight: '#166534' },
  hospital:   { primary: '#065f46', accent: '#34d399', warm: '#ecfdf5', heroBg: 'radial-gradient(ellipse at 70% 40%,#065f46 0%,#022c22 60%,#011815 100%)', text: '#065f46', textLight: '#047857' },
  insurance:  { primary: '#1e3a5f', accent: '#60a5fa', warm: '#f0f9ff', heroBg: 'radial-gradient(ellipse at 60% 50%,#1e3a5f 0%,#0f1d30 60%,#080e18 100%)', text: '#1e3a5f', textLight: '#1e40af' },
  government: { primary: '#7f1d1d', accent: '#f87171', warm: '#fef2f2', heroBg: 'radial-gradient(ellipse at 40% 50%,#7f1d1d 0%,#3b1010 60%,#1a0808 100%)', text: '#7f1d1d', textLight: '#991b1b' },
  rwe:        { primary: '#0f172a', accent: '#38bdf8', warm: '#f0f9ff', heroBg: 'radial-gradient(ellipse at 50% 30%,#1e293b 0%,#0f172a 60%,#020617 100%)', text: '#0f172a', textLight: '#334155' },
}

// ═══════ SVG Data ═══════

export const SVG_DATA: Record<string, { paths: string[]; nodes: [number, number][] }> = {
  home:       { paths: ['M200 360 Q200 280 160 220 Q120 160 140 100','M200 360 Q200 300 240 240 Q280 180 260 120','M200 360 Q190 320 180 180 Q210 120 200 80'], nodes: [[140,100],[260,120],[200,80],[120,180],[280,200]] },
  hospital:   { paths: ['M200 350 Q180 280 200 200 Q220 140 200 80','M200 260 Q140 240 100 200','M200 260 Q260 240 300 200'], nodes: [[200,80],[100,200],[300,200],[160,140],[240,140]] },
  insurance:  { paths: ['M100 300 Q150 200 200 200 Q250 200 300 100','M100 200 Q200 180 300 200','M200 350 Q200 250 200 150'], nodes: [[100,300],[300,100],[200,150],[150,200],[250,200]] },
  government: { paths: ['M120 320 L120 120 L280 120 L280 320','M120 180 L280 180','M120 240 L280 240'], nodes: [[120,120],[280,120],[200,80],[120,180],[280,240]] },
  rwe:        { paths: ['M80 200 Q140 120 200 200 Q260 280 320 200','M80 200 Q140 280 200 200 Q260 120 320 200','M200 80 L200 320'], nodes: [[80,200],[320,200],[200,80],[200,320],[200,200]] },
}

// ═══════ Page Content Data ═══════

export interface FlowStep { icon: string; title: string; desc: string }
export interface DataCardItem { icon: string; number: number; suffix: string; label: string; description: string }
export interface Quote { quote: string; name: string; role: string }
export interface HeroStat { value: number; suffix: string; label: string }
export interface PageCTA { title: string; subtitle: string; button: string }

export interface PageData {
  heroTag: string
  heroCta: string
  heroTitle: string
  heroSubtitle: string
  heroStats: HeroStat[]
  hasScenes?: boolean
  sectionTag: string
  sectionTitle: string
  sectionSub: string
  flow: FlowStep[]
  cardsTag: string
  cardsTitle: string
  cards: DataCardItem[]
  testimonials: Quote[]
  cta: PageCTA
}

interface PlatformStats {
  api_endpoints: number
  data_models: number
  agent_count: number
  knowledge_tiers: number
  scheduler_jobs: number
  platform_version: string
}

/** Merge dynamic platform stats into home page data */
function applyDynamicStats(base: PageData, stats: PlatformStats): PageData {
  const heroStats = [...base.heroStats]
  // heroStats[1] = AI Agent count
  heroStats[1] = { value: stats.agent_count, suffix: '+', label: 'AI Agent' }

  const sectionSub = `${stats.api_endpoints}+ API · ${stats.data_models}张数据表 · ${stats.agent_count}个AI Agent · 双轨状态机`

  const cards: DataCardItem[] = [
    { icon: '🔌', number: stats.api_endpoints, suffix: '+', label: 'API 端点', description: '覆盖评估、干预、学习、设备全链路' },
    { icon: '🧬', number: stats.data_models, suffix: '+', label: '数据模型', description: '从用户画像到行为轨迹全维度建模' },
    { icon: '🤖', number: stats.agent_count, suffix: '+', label: 'AI Agent', description: 'Master协调、领域专家、主动干预' },
    { icon: '📚', number: stats.knowledge_tiers, suffix: '层', label: '知识引擎', description: 'RAG检索+证据分层+引用标注' },
  ]

  // flow step 3: update agent count in desc
  const flow = base.flow.map((f, i) =>
    i === 2 ? { ...f, desc: `${stats.agent_count} Agent协同` } : f
  )

  return { ...base, heroStats, sectionSub, cards, flow }
}

export const PAGES: Record<string, PageData> = {
  home: {
    heroTag: '行为健康数字基建', heroCta: '预约演示',
    heroTitle: '让健康管理<br><em>自然生长</em>',
    heroSubtitle: '不是冰冷的数据看板，是有温度的行为改变系统。从评估到干预、从个体到群体，用数字化基建重塑健康管理的底层逻辑。',
    heroStats: [{ value: 180, suffix: '天', label: '代谢逆转周期' }, { value: 20, suffix: '+', label: 'AI Agent' }, { value: 97, suffix: '%', label: '行为改善率' }],
    hasScenes: true,
    sectionTag: '技术架构', sectionTitle: '不是又一个「健康管理App」', sectionSub: '698+ API · 169张数据表 · 20个AI Agent · 双轨状态机',
    flow: [{ icon: '📋', title: 'BAPS评估', desc: '150题四维量表' }, { icon: '🧠', title: 'AI画像', desc: 'TTM阶段推演' }, { icon: '💊', title: '精准干预', desc: '20 Agent协同' }, { icon: '🔄', title: '行为追踪', desc: '微行动引擎' }, { icon: '📊', title: '效果闭环', desc: '持续优化' }],
    cardsTag: '核心能力', cardsTitle: '平台技术全景',
    cards: [{ icon: '🔌', number: 698, suffix: '+', label: 'API 端点', description: '覆盖评估、干预、学习、设备全链路' }, { icon: '🧬', number: 169, suffix: '+', label: '数据模型', description: '从用户画像到行为轨迹全维度建模' }, { icon: '🤖', number: 20, suffix: '+', label: 'AI Agent', description: 'Master协调、领域专家、主动干预' }, { icon: '📚', number: 4, suffix: '层', label: '知识引擎', description: 'RAG检索+证据分层+引用标注' }],
    testimonials: [{ quote: '终于不是让患者填完问卷就完事了。系统能自动生成行为处方，还能追踪执行。', name: '张主任', role: '某三甲医院 内分泌科' }, { quote: '我们的会员续保率提升了23%，不是靠降价，是靠真正在管健康。', name: '李总', role: '某寿险公司 健康管理部' }, { quote: '基层慢病筛查终于能跟干预打通了，不再是两张皮。', name: '王科长', role: '某区卫健委' }],
    cta: { title: '准备好让改变生长了吗？', subtitle: '15分钟了解一套完整的行为健康数字基建', button: '预约产品演示' },
  },
  hospital: {
    heroTag: '医院解决方案', heroCta: '申请试用',
    heroTitle: '从「治好病」<br>到<em>「管好人」</em>',
    heroSubtitle: '让行为处方像药物处方一样标准化。基于TTM行为改变模型，AI驱动的个性化干预方案，让慢病管理真正闭环。',
    heroStats: [{ value: 42, suffix: '%', label: 'HbA1c达标提升' }, { value: 3, suffix: '倍', label: '随访效率' }, { value: 89, suffix: '%', label: '患者满意度' }],
    sectionTag: '解决方案', sectionTitle: '五步行为处方闭环', sectionSub: '从入院评估到出院随访，每个环节都有AI伴随',
    flow: [{ icon: '📋', title: '智能评估', desc: 'BAPS四维量表' }, { icon: '🎯', title: '阶段识别', desc: 'TTM精准定位' }, { icon: '💊', title: '行为处方', desc: 'AI个性化方案' }, { icon: '📱', title: '每日微行动', desc: '可执行小步骤' }, { icon: '🔄', title: '动态调整', desc: '数据驱动迭代' }],
    cardsTag: '临床效果', cardsTitle: '用数据说话',
    cards: [{ icon: '📉', number: 42, suffix: '%', label: 'HbA1c达标提升', description: '180天代谢逆转，糖化血红蛋白显著改善' }, { icon: '⏱', number: 3, suffix: 'x', label: '随访效率', description: 'AI Agent自动分层随访，释放护士产能' }, { icon: '😊', number: 89, suffix: '%', label: '患者满意度', description: '有温度的数字化管理，不是冰冷推送' }, { icon: '💰', number: 35, suffix: '%', label: '管理成本下降', description: '标准化流程降低人力依赖' }],
    testimonials: [{ quote: '行为处方引擎让我们的慢病管理从「被动随访」变成了「主动干预」，患者依从性大幅提升。', name: '张主任', role: '某三甲医院 内分泌科' }, { quote: '以前护士一天只能随访30个患者，现在AI自动分层，效率提升了3倍。', name: '李护士长', role: '某三甲医院 慢病管理中心' }, { quote: '出院后患者失联一直是痛点。现在微行动推送让患者每天都有事做，复诊率明显提高。', name: '王主任', role: '某二甲医院 康复科' }],
    cta: { title: '让行为处方落地', subtitle: '为您的科室定制一套完整的慢病行为管理方案', button: '预约科室演示' },
  },
  insurance: {
    heroTag: '商保解决方案', heroCta: '商务咨询',
    heroTitle: '健康管理<br>不该是<em>成本中心</em>',
    heroSubtitle: '用行为数据证明价值。从「买了不用」到「天天在用」，让健康管理真正成为会员粘性引擎和赔付控制杠杆。',
    heroStats: [{ value: 23, suffix: '%', label: '续保率提升' }, { value: 18, suffix: '%', label: '赔付率下降' }, { value: 67, suffix: '%', label: '会员活跃度' }],
    sectionTag: '价值闭环', sectionTitle: '从投入到回报的完整链路', sectionSub: '不只是做健康管理，而是让健康管理创造商业价值',
    flow: [{ icon: '👤', title: '会员画像', desc: 'BAPS健康评估' }, { icon: '🏷', title: '风险分层', desc: '精算级别标签' }, { icon: '💊', title: '精准干预', desc: '按风险投入资源' }, { icon: '📱', title: '持续参与', desc: '行为积分体系' }, { icon: '📈', title: '效果验证', desc: '赔付率对照' }],
    cardsTag: '商业价值', cardsTitle: '用数据说话',
    cards: [{ icon: '📈', number: 23, suffix: '%', label: '续保率提升', description: '会员感受到价值，主动续保不再靠降价' }, { icon: '📉', number: 18, suffix: '%', label: '赔付率下降', description: '行为干预降低慢病风险，减少理赔支出' }, { icon: '🔥', number: 67, suffix: '%', label: '会员活跃度', description: '每日微行动+积分体系，远超行业平均' }, { icon: '💎', number: 4, suffix: 'x', label: '投入产出比', description: '每1元健管投入产生4元赔付节省' }],
    testimonials: [{ quote: '我们的会员续保率提升了23%，不是靠降价，是靠真正在管健康。', name: '李总', role: '某寿险公司 健康管理部' }, { quote: '以前健康管理就是送体检，会员做完就忘了。现在每天都有微行动提醒，活跃度完全不一样。', name: '陈经理', role: '某健康险 产品部' }, { quote: '精算部门终于有数据证明健康管理确实在降赔付了。这是我们要的ROI。', name: '赵总监', role: '某财险公司 精算部' }],
    cta: { title: '让健康管理成为利润中心', subtitle: '用数据证明价值，用行为改变创造商业回报', button: '预约商务咨询' },
  },
  government: {
    heroTag: '政府公卫方案', heroCta: '了解方案',
    heroTitle: '基层慢病管理<br>不再是<em>「填表运动」</em>',
    heroSubtitle: '筛查-评估-干预-追踪一体化数字底座。让社区医生从「信息搬运工」变成「健康守门人」，用AI赋能基层。',
    heroStats: [{ value: 85, suffix: '%', label: '筛查覆盖率' }, { value: 60, suffix: '%', label: '干预执行率' }, { value: 40, suffix: '%', label: '管理效率提升' }],
    sectionTag: '一体化流程', sectionTitle: '筛查-评估-干预-追踪四位一体', sectionSub: '不是四个独立系统，是一条完整的数据链路',
    flow: [{ icon: '🔍', title: '社区筛查', desc: '问卷+设备采集' }, { icon: '📋', title: 'BAPS评估', desc: '四维精准画像' }, { icon: '📊', title: '风险分级', desc: '自动分层建档' }, { icon: '💊', title: '精准干预', desc: 'AI行为处方' }, { icon: '📱', title: '追踪随访', desc: '效果闭环' }],
    cardsTag: '实施效果', cardsTitle: '用数据说话',
    cards: [{ icon: '🏘', number: 85, suffix: '%', label: '筛查覆盖率', description: '线上问卷+线下设备，降低筛查门槛' }, { icon: '📋', number: 60, suffix: '%', label: '干预执行率', description: '从「建档了事」到真正跟踪执行' }, { icon: '⏱', number: 40, suffix: '%', label: '管理效率提升', description: 'AI辅助释放基层医生产能' }, { icon: '📊', number: 100, suffix: '%', label: '数据可追溯', description: '每一步操作都有记录，合规无忧' }],
    testimonials: [{ quote: '基层慢病筛查终于能跟干预打通了，不再是两张皮。社区医生有了真正的抓手。', name: '王科长', role: '某区卫健委' }, { quote: '以前慢病管理就是录数据，现在系统自动出干预方案，医生只需要确认执行。', name: '刘主任', role: '某社区卫生服务中心' }, { quote: '数据报表自动生成，年终考核不再通宵加班了。数据是真实的，不是补录的。', name: '孙站长', role: '某乡镇卫生院' }],
    cta: { title: '构建公卫数字底座', subtitle: '让每一分公卫投入都看得见效果', button: '申请试点' },
  },
  rwe: {
    heroTag: '真实世界证据', heroCta: '合作咨询',
    heroTitle: '行为数据<br><em>资产化</em>',
    heroSubtitle: '从海量行为轨迹中挖掘真实世界证据，支撑临床研究、产品迭代和政策决策。让数据不再沉睡在数据库里。',
    heroStats: [{ value: 50, suffix: '万+', label: '行为数据点/日' }, { value: 12, suffix: '维', label: '行为特征' }, { value: 98, suffix: '%', label: '数据完整率' }],
    sectionTag: '数据管线', sectionTitle: '从行为采集到证据产出', sectionSub: '完整的数据资产化链路，每一步都有质量控制',
    flow: [{ icon: '📱', title: '多源采集', desc: '设备+问卷+记录' }, { icon: '🧹', title: '清洗标注', desc: '自动质控管线' }, { icon: '🧬', title: '特征工程', desc: '12维行为建模' }, { icon: '📊', title: '分析洞察', desc: 'AI辅助分析' }, { icon: '📄', title: '证据产出', desc: '论文/报告/专利' }],
    cardsTag: '数据能力', cardsTitle: '用数据说话',
    cards: [{ icon: '📊', number: 50, suffix: '万+', label: '日行为数据点', description: '设备、问卷、微行动多源汇聚' }, { icon: '🧬', number: 12, suffix: '维', label: '行为特征', description: '从睡眠到情绪，全维度量化建模' }, { icon: '✅', number: 98, suffix: '%', label: '数据完整率', description: '自动质控管线保障数据质量' }, { icon: '📄', number: 6, suffix: '篇', label: '已发表论文', description: '真实世界证据支撑学术产出' }],
    testimonials: [{ quote: '行为数据的价值远超预期。通过分析行为轨迹，我们发现了好几个新的干预靶点。', name: '陈教授', role: '某医学院 流行病学系' }, { quote: '数据质量是做RWE最头疼的问题，这套系统的自动质控管线帮了大忙。', name: '周博士', role: '某药企 医学部' }, { quote: '产品迭代终于有了数据支撑，不再是拍脑袋决定功能优先级了。', name: '林总', role: '某数字疗法公司' }],
    cta: { title: '让数据产生价值', subtitle: '从行为轨迹到真实世界证据，每一步都可追溯', button: '预约合作洽谈' },
  },
}

// ═══════ Scene Cards (homepage) ═══════

export const SCENES = [
  { icon: '🏥', title: '医院', desc: '行为处方引擎', sub: '从「治好病」到「管好人」', key: 'hospital', color: '#065f46', bg: '#ecfdf5' },
  { icon: '🏢', title: '商保', desc: '健康管理闭环', sub: '降赔付、提续保、增粘性', key: 'insurance', color: '#1e3a5f', bg: '#f0f9ff' },
  { icon: '🏛', title: '政府', desc: '公卫数字底座', sub: '筛查-评估-干预-追踪一体化', key: 'government', color: '#7f1d1d', bg: '#fef2f2' },
  { icon: '🔬', title: 'RWE', desc: '真实世界证据', sub: '行为数据资产化', key: 'rwe', color: '#0f172a', bg: '#f1f5f9' },
]

// ═══════ Composables ═══════

/** 使用当前页面主题 + 动态平台统计 */
export function useLandingTheme() {
  const currentPage = ref('home')
  const platformStats = ref<PlatformStats | null>(null)

  const theme = computed(() => THEMES[currentPage.value] || THEMES.home)
  const svgData = computed(() => SVG_DATA[currentPage.value] || SVG_DATA.home)

  const pageData = computed(() => {
    const base = PAGES[currentPage.value] || PAGES.home
    if (currentPage.value === 'home' && platformStats.value) {
      return applyDynamicStats(base, platformStats.value)
    }
    return base
  })

  function switchPage(page: string) {
    currentPage.value = page
    applyTheme(THEMES[page] || THEMES.home)
    window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior })
  }

  function applyTheme(t: Theme) {
    const root = document.documentElement
    root.style.setProperty('--l-primary', t.primary)
    root.style.setProperty('--l-accent', t.accent)
    root.style.setProperty('--l-warm', t.warm)
    root.style.setProperty('--l-hero-bg', t.heroBg)
    root.style.setProperty('--l-text', t.text)
    root.style.setProperty('--l-text-light', t.textLight)
  }

  onMounted(async () => {
    applyTheme(THEMES.home)
    try {
      const res = await fetch('/api/v1/landing/platform-stats')
      if (res.ok) platformStats.value = await res.json()
    } catch { /* keep static defaults */ }
  })

  return { currentPage, theme, pageData, svgData, switchPage }
}

/** 滚动进入视口时添加 .visible 类 */
export function useScrollReveal(rootRef: Ref<HTMLElement | null>) {
  let observer: IntersectionObserver | null = null

  function init() {
    if (observer) observer.disconnect()
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) e.target.classList.add('visible')
        })
      },
      { threshold: 0.12 }
    )
    if (rootRef.value) {
      rootRef.value.querySelectorAll('.l-fade-in, .l-fade-left').forEach((el) => {
        el.classList.remove('visible')
        observer!.observe(el)
      })
    }
  }

  onMounted(() => setTimeout(init, 50))
  onUnmounted(() => observer?.disconnect())

  return { reinit: () => setTimeout(init, 80) }
}
