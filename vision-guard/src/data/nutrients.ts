export interface Nutrient {
  key: string
  name: string
  icon: string
  unit: string
  daily: number
  color: string
  colorL: string
  desc: string
}

export const NUTRIENTS: Record<string, Nutrient> = {
  lutein:  { key: 'lutein',  name: '叶黄素',  icon: '🌿', unit: 'mg',    daily: 8,   color: '#2D9E6B', colorL: '#D4F5E7', desc: '黄斑保护' },
  dha:     { key: 'dha',     name: 'DHA',     icon: '🐟', unit: 'mg',    daily: 220, color: '#1976D2', colorL: '#E3F2FD', desc: '视网膜发育' },
  vitA:    { key: 'vitA',    name: '维生素A', icon: '🥕', unit: 'μgRAE', daily: 600, color: '#F4A261', colorL: '#FFF3E0', desc: '暗视力' },
  vitC:    { key: 'vitC',    name: '维生素C', icon: '🍊', unit: 'mg',    daily: 70,  color: '#E64A19', colorL: '#FBE9E7', desc: '晶状体抗氧化' },
  vitD:    { key: 'vitD',    name: '维生素D', icon: '☀️', unit: 'μg',    daily: 12,  color: '#F9C74F', colorL: '#FFFDE7', desc: '眼轴调节' },
  zinc:    { key: 'zinc',    name: '锌',      icon: '💎', unit: 'mg',    daily: 7,   color: '#7B1FA2', colorL: '#F3E5F5', desc: 'VitA代谢辅助' },
}

export const NUTRIENT_KEYS = Object.keys(NUTRIENTS) as (keyof typeof NUTRIENTS)[]
