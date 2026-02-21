/**
 * Feature flag composable — loads flags once per session, caches in refs.
 */
import { ref, type Ref } from 'vue'
import api from '@/api/index'

interface FlagState {
  enabled: boolean
  variant: string
}

// Session-level cache
let flagCache: Record<string, FlagState> | null = null
let loading = false
const waiters: Array<(cache: Record<string, FlagState>) => void> = []

async function loadFlags(): Promise<Record<string, FlagState>> {
  if (flagCache) return flagCache

  if (loading) {
    return new Promise((resolve) => waiters.push(resolve))
  }

  loading = true
  try {
    const res: any = await api.get('/api/v1/flags')
    flagCache = res.flags || {}
  } catch {
    flagCache = {}
  }
  loading = false
  waiters.forEach((fn) => fn(flagCache!))
  waiters.length = 0
  return flagCache!
}

export function useFeatureFlag(flagKey: string): {
  enabled: Ref<boolean>
  variant: Ref<string>
} {
  const enabled = ref(false)
  const variant = ref('control')

  loadFlags().then((flags) => {
    const flag = flags[flagKey]
    if (flag) {
      enabled.value = flag.enabled
      variant.value = flag.variant || 'control'
    }
  })

  return { enabled, variant }
}
