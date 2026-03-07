import { D } from '@/design/tokens'

export interface SceneItem {
  ico: string
  text: string
  sub: string
}

export interface Door {
  key: string
  label: string
  icon: string
  title: string
  desc: string
  color: string
  rgb: string
  gradient: string
  scenes: SceneItem[]
}

export const DOORS: Door[] = [
  {
    key: 'symptom', label: '身体信号', icon: '🌡️',
    title: '你的身体，是否正在求助……',
    desc: '选一个最近常有的感受——3分钟，找到真正的原因',
    color: D.amber, rgb: '245,166,35',
    gradient: 'linear-gradient(135deg,rgba(245,166,35,.2),rgba(245,166,35,.05))',
    scenes: [
      { ico: '⚡', text: '下午三点，脑子突然空了，什么都不想干', sub: '精力断崖·不是懒，是血糖在作怪' },
      { ico: '😴', text: '睡了七八个小时，醒来还是累', sub: '睡眠无效·身体在睡，但没有修复' },
      { ico: '👖', text: '腰悄悄大了一圈，明明没怎么多吃', sub: '代谢减速·不是吃多了，是代谢变了' },
      { ico: '📋', text: '体检有个数字飘红，医生说"注意一下"', sub: '慢病早期·现在改还来得及' },
      { ico: '💢', text: '情绪说来就来，自己都觉得莫名其妙', sub: '压力代谢·不是脾气差，是身体在超载' },
      { ico: '🩺', text: '血压偏高了一点，但还没到吃药的程度', sub: '心血管早期·行为改变比药物更有效' },
    ]
  },
  {
    key: 'risk', label: '风险距离', icon: '📊',
    title: '你离自己担心的慢性病，还有多远？……',
    desc: '不是吓你——是让你看清楚，自己真正站在哪里',
    color: D.teal, rgb: '0,184,160',
    gradient: 'linear-gradient(135deg,rgba(0,184,160,.2),rgba(0,184,160,.05))',
    scenes: [
      { ico: '🍬', text: '糖尿病，离你到底有多远？', sub: '血糖调节·很多人不知道自己已经在路上了' },
      { ico: '⚖️', text: '减重为什么总是反弹？', sub: '代谢适应·不是意志力不够，是方法错了' },
      { ico: '🧬', text: '父母有的那个病，会轮到你吗？', sub: '家族风险·遗传只是底牌，行为才是变量' },
      { ico: '❤️', text: '你的心脏，能撑多少年？', sub: '心血管风险·血压血脂现在的轨迹指向哪里' },
      { ico: '🧠', text: '你的大脑，正在以多快的速度老去？', sub: '认知健康·记性变差不是气，是可以干预的' },
      { ico: '😶', text: '身体总觉得哪里不对，但检查又没问题？', sub: '亚健康灰色地带·功能下降早于指标异常' },
    ]
  },
  {
    key: 'growth', label: '为什么这么累', icon: '🚀',
    title: '我如此努力，为什么活着还是这么累？……',
    desc: '不只是身体的问题——关于关系、意义，和你真正想要的生活',
    color: D.indigo, rgb: '76,110,245',
    gradient: 'linear-gradient(135deg,rgba(76,110,245,.2),rgba(76,110,245,.05))',
    scenes: [
      { ico: '🌀', text: '每天都很忙，但不知道在忙什么', sub: '意义感缺失·身体在转，内心在空转' },
      { ico: '🤖', text: 'AI要替代很多工作了，我的价值在哪？', sub: '认知韧性·人机时代，适应力才是核心竞争力' },
      { ico: '👦', text: '跟孩子说不了两句就起冲突', sub: '亲子关系·不是沟通技巧问题，是状态问题' },
      { ico: '💼', text: '在公司越来越撑不住，但又不知道怎么办', sub: '职场适应·不是能力不够，是压力超载了' },
      { ico: '🛋️', text: '全世界都在躺平，我为什么还要努力？', sub: '内驱力重建·不是懒，是找不到真正值得的理由' },
      { ico: '💔', text: '付出了很多，好像没有人真的在乎你', sub: '关系消耗·不是你不够好，是能量已经见底了' },
    ]
  },
]
