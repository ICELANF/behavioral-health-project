import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface SPIMapping {
  phq9: { weight: number; threshold: { low: number; medium: number; high: number } }
  cgmVariability: { weight: number; threshold: { low: number; medium: number; high: number } }
  behaviorConsistency: { weight: number; threshold: { low: number; medium: number; high: number } }
}

const DEFAULT_SPI: SPIMapping = {
  phq9: { weight: 0.4, threshold: { low: 5, medium: 10, high: 15 } },
  cgmVariability: { weight: 0.35, threshold: { low: 20, medium: 33, high: 45 } },
  behaviorConsistency: { weight: 0.25, threshold: { low: 0.3, medium: 0.5, high: 0.7 } },
}

export const useBrainStore = defineStore('brain', () => {
  const spiMapping = ref<SPIMapping>(JSON.parse(JSON.stringify(DEFAULT_SPI)))

  const updateWeight = (metric: keyof SPIMapping, weight: number) => {
    spiMapping.value[metric].weight = weight
  }

  const updateThreshold = (metric: keyof SPIMapping, level: 'low' | 'medium' | 'high', value: number) => {
    spiMapping.value[metric].threshold[level] = value
  }

  const resetToDefault = () => {
    spiMapping.value = JSON.parse(JSON.stringify(DEFAULT_SPI))
  }

  const calculateRiskScore = (metrics: { phq9: number; cgmCV: number; consistency: number }) => {
    const m = spiMapping.value
    const phq9Score = metrics.phq9 >= m.phq9.threshold.high ? 3
      : metrics.phq9 >= m.phq9.threshold.medium ? 2
      : metrics.phq9 >= m.phq9.threshold.low ? 1 : 0

    const cgmScore = metrics.cgmCV >= m.cgmVariability.threshold.high ? 3
      : metrics.cgmCV >= m.cgmVariability.threshold.medium ? 2
      : metrics.cgmCV >= m.cgmVariability.threshold.low ? 1 : 0

    const behaviorScore = metrics.consistency <= m.behaviorConsistency.threshold.low ? 3
      : metrics.consistency <= m.behaviorConsistency.threshold.medium ? 2
      : metrics.consistency <= m.behaviorConsistency.threshold.high ? 1 : 0

    const total = phq9Score * m.phq9.weight + cgmScore * m.cgmVariability.weight + behaviorScore * m.behaviorConsistency.weight

    return {
      score: total,
      level: total >= 2.4 ? 'R3' : total >= 1.5 ? 'R2' : total >= 0.6 ? 'R1' : 'R0',
    }
  }

  return { spiMapping, updateWeight, updateThreshold, resetToDefault, calculateRiskScore }
})
