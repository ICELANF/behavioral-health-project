export interface Scores {
  metabolism: number
  stress: number
  sleep: number
  stability: number
  control: number
}

export interface AssessmentResult {
  label: string
  scores: Scores
}

/**
 * Multi-select scoring: for each question, take the average of selected option indices.
 * Option indices: 0 = best → 3 = worst.
 * Two questions per dimension, sum both averages, divide by max (6), × 100.
 */
function questionScore(selected: number[] | undefined): number {
  if (!selected || selected.length === 0) return 0
  return selected.reduce((s, v) => s + v, 0) / selected.length
}

export function computeResult(answers: Record<number, number | number[]>): AssessmentResult {
  const scores: Scores = { metabolism: 0, stress: 0, sleep: 0, stability: 0, control: 0 }
  const idxMap: [number, number][] = [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]
  const keys = Object.keys(scores) as (keyof Scores)[]

  idxMap.forEach(([a, b], i) => {
    const va = Array.isArray(answers[a]) ? questionScore(answers[a] as number[]) : (answers[a] as number || 0)
    const vb = Array.isArray(answers[b]) ? questionScore(answers[b] as number[]) : (answers[b] as number || 0)
    scores[keys[i]] = Math.round((va + vb) / 6 * 100)
  })

  if (scores.metabolism > 65 && scores.stress > 60) return { label: 'high_pressure', scores }
  if (scores.stress > 70 && scores.sleep < 40 && scores.control < 40) return { label: 'emotion_drain', scores }
  if (scores.sleep > 65 && scores.stress > 55) return { label: 'night_drain', scores }
  if (scores.metabolism > 70 && scores.stability < 35) return { label: 'hidden_fatigue', scores }
  return { label: 'structural', scores }
}
