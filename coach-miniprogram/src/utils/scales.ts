/**
 * 量表注册表 — 全平台唯一真相源
 * 新增量表只需在此追加，所有入口自动生效
 */
export interface ScaleDef {
  key: string
  label: string        // 完整名
  shortLabel: string   // 列表/徽标用简称
  desc: string         // 用途说明（教练可见）
  time: number         // 预估完成分钟
  tags: string[]       // 过滤标签
}

export const SCALES_REGISTRY: ScaleDef[] = [
  { key: 'ttm7',     label: 'TTM行为阶段',   shortLabel: 'TTM7',  desc: '识别行为改变阶段 S0-S6',      time: 5,  tags: ['basic','behavior'] },
  { key: 'big5',     label: '大五人格 BIG5', shortLabel: 'BIG5',  desc: '人格特征基线，个性化干预依据', time: 8,  tags: ['basic','psych'] },
  { key: 'bpt6',     label: 'BPT行为类型',   shortLabel: 'BPT6',  desc: '行为偏好分型（6个维度）',      time: 6,  tags: ['behavior'] },
  { key: 'capacity', label: '饮食能力 CAP',  shortLabel: 'CAP',   desc: '饮食习惯与执行能力评估',       time: 10, tags: ['nutrition'] },
  { key: 'spi',      label: '运动偏好 SPI',  shortLabel: 'SPI',   desc: '运动习惯与偏好基线',           time: 7,  tags: ['exercise'] },
  // ── 未来可在此追加：phq9、gad7、ess、dass21 等 ──
]

/** 预设量表包（快速选择入口） */
export const SCALE_PACKS: Record<string, { label: string; scales: string[] }> = {
  comprehensive: { label: '综合',   scales: ['ttm7', 'big5', 'bpt6'] },
  behavior:      { label: '行为',   scales: ['bpt6'] },
  nutrition:     { label: '饮食',   scales: ['capacity'] },
  exercise:      { label: '运动',   scales: ['spi'] },
}

/** 根据已选 key 列表计算预估总时长 */
export function estimateTime(selectedKeys: string[]): number {
  return SCALES_REGISTRY
    .filter(s => selectedKeys.includes(s.key))
    .reduce((sum, s) => sum + s.time, 0)
}

/** 量表 key → 显示名 映射（用于列表格式化） */
export const SCALE_NAME_MAP: Record<string, string> = Object.fromEntries(
  SCALES_REGISTRY.map(s => [s.key, s.shortLabel])
)
