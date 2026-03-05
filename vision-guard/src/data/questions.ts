export interface SurveyQuestion {
  id: string
  emoji: string
  text: string
  sub: string
  opts: string[]
  scores: number[]
  nutrient: string
}

/** Weekly behavioral survey (5 questions) */
export const BEHAVIOR_QUESTIONS = [
  { q: '今天孩子的户外活动时间是？', opts: ['不到30分钟', '30-60分钟', '1-2小时', '超过2小时'] },
  { q: '今天使用电子产品总时长？', opts: ['不到30分钟', '30-60分钟', '1-2小时', '超过2小时'] },
  { q: '孩子做眼保健操了吗？', opts: ['做了两次', '只做了一次', '没做', '不确定'] },
  { q: '孩子近距离用眼时注意距离了吗？', opts: ['一直注意', '大部分时候', '偶尔注意', '没有注意'] },
  { q: '今天孩子的睡眠/休息情况？', opts: ['非常好', '还不错', '一般', '较差'] },
]

/** Weekly nutrition survey (7 questions) */
export const NUTRITION_QUESTIONS: SurveyQuestion[] = [
  { id: 'q1', emoji: '🥬', text: '本周吃了几次深绿色蔬菜？', sub: '菠菜、西兰花、油麦菜、羽衣甘蓝等',
    opts: ['没吃', '1-2次', '3-4次', '5次及以上'], scores: [0, 1, 2, 3], nutrient: 'lutein' },
  { id: 'q2', emoji: '🐟', text: '本周吃了几次深海鱼？', sub: '三文鱼、金枪鱼、鲭鱼、沙丁鱼等',
    opts: ['没吃', '1次', '2次', '3次及以上'], scores: [0, 1, 2, 3], nutrient: 'dha' },
  { id: 'q3', emoji: '🥚', text: '本周平均每天吃几个鸡蛋？', sub: '包含各种烹饪方式',
    opts: ['不吃', '每周3-4个', '每天1个', '每天2个'], scores: [0, 1, 2, 3], nutrient: 'lutein' },
  { id: 'q4', emoji: '🥕', text: '本周吃了几次橙黄色蔬果？', sub: '胡萝卜、南瓜、橙子、芒果等',
    opts: ['没吃', '1-2次', '3-4次', '每天都有'], scores: [0, 1, 2, 3], nutrient: 'vitA' },
  { id: 'q5', emoji: '🍊', text: '本周每天吃了几种新鲜水果？', sub: '关注维生素C摄入',
    opts: ['几乎不吃', '偶尔1种', '1-2种', '2种以上'], scores: [0, 1, 2, 3], nutrient: 'vitC' },
  { id: 'q6', emoji: '☀️', text: '本周喝牛奶/酸奶的频率？', sub: '强化维生素D的乳制品',
    opts: ['不喝', '2-3次', '每天1次', '每天2次'], scores: [0, 1, 2, 3], nutrient: 'vitD' },
  { id: 'q7', emoji: '🦪', text: '本周吃了贝壳类海鲜吗？', sub: '牡蛎、蛤蜊、扇贝等，富含锌',
    opts: ['没吃', '吃了1次', '吃了2次', '3次及以上'], scores: [0, 1, 2, 3], nutrient: 'zinc' },
]
