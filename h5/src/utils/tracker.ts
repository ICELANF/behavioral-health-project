/**
 * H5 Event Tracker — queued batch event ingestion.
 * Flushes every 10s or at 20 events.
 */
import type { Router } from 'vue-router'
import api from '@/api/index'

interface TrackEvent {
  event_type: string
  properties?: Record<string, any>
  client_timestamp: string
}

const queue: TrackEvent[] = []
let flushTimer: ReturnType<typeof setInterval> | null = null

/** Track a single event */
export function track(event: string, properties?: Record<string, any>): void {
  queue.push({
    event_type: event,
    properties,
    client_timestamp: new Date().toISOString(),
  })
  if (queue.length >= 20) flush()
}

/** Flush queued events to backend */
async function flush(): Promise<void> {
  if (queue.length === 0) return
  // 无 token 时丢弃事件，避免 401 循环
  const token = localStorage.getItem('h5_token')
  if (!token) { queue.length = 0; return }
  const batch = queue.splice(0, 100)
  try {
    await api.post('/api/v1/events/track', { events: batch })
  } catch {
    // Put events back on failure (best-effort, 最多保留50条)
    queue.unshift(...batch.slice(0, 50))
  }
}

/** Initialize tracker — call once from main.ts */
export function initTracker(router: Router): void {
  // Auto-track page views
  router.afterEach((to) => {
    track('page_view', {
      page: to.path,
      name: (to.name as string) || '',
      title: (to.meta?.title as string) || '',
    })
  })

  // Session start
  track('session_start', { referrer: document.referrer })

  // Session end on unload
  window.addEventListener('beforeunload', () => {
    track('session_end', { duration_ms: performance.now() })
    // Sync flush via sendBeacon
    if (queue.length > 0 && navigator.sendBeacon) {
      const payload = JSON.stringify({ events: queue.splice(0, 100) })
      navigator.sendBeacon('/api/v1/events/track', new Blob([payload], { type: 'application/json' }))
    }
  })

  // Periodic flush every 10 seconds
  flushTimer = setInterval(flush, 10_000)
}
