import { defineStore } from 'pinia'
import { ref, computed, reactive } from 'vue'
import { computeResult, type AssessmentResult } from '@/data/scoring'
import { LABELS } from '@/data/labels'
import { BELIEF_OPTS } from '@/data/questions'
import { submitAssessment } from '@/api/assessment'

export const useAssessmentStore = defineStore('assessment', () => {
  const door = ref<string | null>(null)
  const concerns = ref<{ worry: string; confusion: string; desire: string; aversion: string }>({
    worry: '', confusion: '', desire: '', aversion: '',
  })
  const voiceBlobs = reactive<Record<string, Blob>>({})
  const voiceEmotions = reactive<Record<string, string>>({})
  const scenes = ref<number[]>([])
  const beliefs = ref<number[]>([])
  const answers = ref<Record<number, number[]>>({})
  const result = ref<AssessmentResult | null>(null)
  const expectations = ref<string[]>([])

  const currentLabel = computed(() =>
    result.value ? LABELS[result.value.label] : null
  )
  const currentScores = computed(() =>
    result.value?.scores ?? null
  )
  const beliefTexts = computed(() =>
    beliefs.value.map(i => BELIEF_OPTS[i]?.text).filter(Boolean)
  )
  // backward compat — first belief for factormap
  const beliefText = computed(() => beliefTexts.value[0] || '')

  function setDoor(key: string) { door.value = key }

  function toggleScene(idx: number) {
    const pos = scenes.value.indexOf(idx)
    if (pos >= 0) scenes.value.splice(pos, 1)
    else scenes.value.push(idx)
  }

  function toggleBelief(idx: number) {
    const pos = beliefs.value.indexOf(idx)
    if (pos >= 0) beliefs.value.splice(pos, 1)
    else beliefs.value.push(idx)
  }

  function toggleAnswer(qIdx: number, optIdx: number) {
    const cur = answers.value[qIdx] || []
    const pos = cur.indexOf(optIdx)
    if (pos >= 0) cur.splice(pos, 1)
    else cur.push(optIdx)
    answers.value = { ...answers.value, [qIdx]: [...cur] }
  }

  function toggleExpectation(text: string) {
    const idx = expectations.value.indexOf(text)
    if (idx >= 0) expectations.value.splice(idx, 1)
    else expectations.value.push(text)
  }

  async function doSubmit() {
    const sessionId = localStorage.getItem('session_id') || ''
    const serverResult = await submitAssessment({
      door: door.value || '',
      scene: scenes.value[0] ?? 0,
      belief: beliefs.value[0] ?? 0,
      answers: answers.value,
      concerns: concerns.value,
      voiceEmotions: { ...voiceEmotions },
      sessionId,
    })
    if (serverResult?.label) {
      result.value = serverResult
    } else {
      result.value = computeResult(answers.value)
    }

    // Upload voice blobs in background (non-blocking)
    uploadVoiceBlobs(sessionId)

    return result.value
  }

  async function uploadVoiceBlobs(sessionId: string) {
    const keys = Object.keys(voiceBlobs)
    if (keys.length === 0) return
    try {
      const { default: http } = await import('@/api/request')
      for (const key of keys) {
        const formData = new FormData()
        formData.append('file', voiceBlobs[key], `concern_${key}.webm`)
        formData.append('field', key)
        formData.append('session_id', sessionId)
        await http.post('/v1/audio/upload-concern', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        }).catch(() => {}) // non-critical, don't block
      }
    } catch { /* silent */ }
  }

  function reset() {
    door.value = null
    concerns.value = { worry: '', confusion: '', desire: '', aversion: '' }
    Object.keys(voiceBlobs).forEach(k => delete voiceBlobs[k])
    Object.keys(voiceEmotions).forEach(k => delete voiceEmotions[k])
    scenes.value = []
    beliefs.value = []
    answers.value = {}
    result.value = null
    expectations.value = []
  }

  return {
    door, concerns, voiceBlobs, voiceEmotions, scenes, beliefs, answers, result, expectations,
    currentLabel, currentScores, beliefText, beliefTexts,
    setDoor, toggleScene, toggleBelief, toggleAnswer, toggleExpectation,
    doSubmit, reset,
  }
})
