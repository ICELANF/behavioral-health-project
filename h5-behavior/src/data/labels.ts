import { D } from '@/design/tokens'

export interface ActionItem {
  ico: string
  name: string
  why: string
  color: string
}

export interface LabelDef {
  name: string
  tcm: string
  color: string
  icon: string
  insight: string
  taboo: string
  actions: ActionItem[]
}

export const LABELS: Record<string, LabelDef> = {
  high_pressure: {
    name: '燃尽模式', tcm: '阴虚质·湿热质倾向', color: D.rose, icon: '🔥',
    insight: '你不是太累了——你是把身体当发动机开，从来没有真正熄过火。皮质醇把你的代谢调成了"战时状态"，睡觉都在救火。',
    taboo: '不催快速减重，不给高强度运动，优先修复睡眠节律',
    actions: [
      { ico: '🚶', name: '餐后10分钟散步', why: '激活GLUT4，把血糖峰值压下来20-30%', color: D.teal },
      { ico: '🌬️', name: '睡前3分钟腹式呼吸', why: '告诉神经系统"战争结束了"，重置皮质醇', color: D.indigo },
      { ico: '📵', name: '22:30手机静音', why: '蓝光让大脑以为是白天，入睡推迟1-2小时', color: D.amber },
    ]
  },
  emotion_drain: {
    name: '内耗主导型', tcm: '气郁质·血瘀质倾向', color: '#F472B6', icon: '💜',
    insight: '你的压力不是来自一件大事，而是每天100件小事在磨你。情绪压着走，身体在替你扛着，久了就变成了说不清楚的"不舒服"。',
    taboo: '不强迫立刻行动，不给孤立任务，优先建立安全感',
    actions: [
      { ico: '📝', name: '晚间3行情绪记录', why: '把感受从身体里拿出来，放到纸上，大脑才能松开', color: D.teal },
      { ico: '🌳', name: '每日30分钟户外步行', why: '不是为了运动，是为了重建多巴胺和血清素的平衡', color: D.amber },
      { ico: '✅', name: '记录今天3件好事', why: '不是正能量鸡汤，是改变大脑对现实的取样方式', color: D.indigo },
    ]
  },
  night_drain: {
    name: '夜间透支型', tcm: '阴虚质·气虚质倾向', color: D.indigo, icon: '🌙',
    insight: '你在用睡眠换时间——每一个"再刷一会儿"，都是在透支明天的状态。问题不是你几点睡，而是你的身体从来没有真正充过满格的电。',
    taboo: '不给夜间运动，不催早起，优先固定起床时间',
    actions: [
      { ico: '⏰', name: '固定起床时间', why: '起床时间是生物钟的主锚点，比几点睡更重要', color: D.teal },
      { ico: '🌡️', name: '睡前90分钟停屏幕', why: '身体要降温0.5°C才能进入深睡，屏幕在阻止这件事', color: D.amber },
      { ico: '🌅', name: '起床后10分钟晒太阳', why: '校准生物钟，全天的精力都会因此更稳', color: D.gold },
    ]
  },
  hidden_fatigue: {
    name: '代谢迟滞型', tcm: '痰湿质·阳虚质倾向', color: D.amber, icon: '⚠️',
    insight: '你可能觉得自己只是"懒"或者"没毅力"——但真实情况是，代谢机制在拖住你，意志力在跟生理规律硬扛，赢不了。',
    taboo: '不用"胖"字，不给复杂计划，说"代谢负担"替代"体重问题"',
    actions: [
      { ico: '🥗', name: '进食顺序：蔬菜→蛋白质→主食', why: '同样的食物，换顺序，血糖峰值降30%', color: D.teal },
      { ico: '⏱️', name: '5分钟启动规则', why: '先做5分钟再决定要不要继续，打破静止惯性', color: D.amber },
      { ico: '🚰', name: '饭后别立刻坐下', why: '餐后肌肉轻微收缩，胰岛素敏感性明显改善', color: D.gold },
    ]
  },
  structural: {
    name: '底层修复型', tcm: '气虚质·阳虚质·特禀质倾向', color: D.sage, icon: '🌱',
    insight: '你想改变，意愿是真的——但身体的底层资源还不够支撑行动。不是你不行，是地基还没打好。先补，再建。',
    taboo: '不催剧烈运动，先查TSH排除甲减，优先上午9-11点活动',
    actions: [
      { ico: '☕', name: '黄芪红枣茶代茶饮', why: '温和补气，降低每天行动的启动成本', color: D.amber },
      { ico: '☀️', name: '上午9-11点户外晒太阳', why: '维生素D合成+皮质醇觉醒，同时激活', color: D.gold },
      { ico: '🎯', name: '每天只定1个5分钟目标', why: '每天一次成功体验，重建"我可以"的感觉', color: D.teal },
    ]
  },
}
