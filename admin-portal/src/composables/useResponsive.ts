/**
 * useResponsive — reactive breakpoint detection composable.
 *
 * Breakpoints:
 *   mobile  < 640px
 *   tablet  640–1023px
 *   desktop >= 1024px
 *   compact < 768px  (mobile + small-tablet, triggers sidebar drawer)
 */
import { ref, onMounted, onUnmounted, computed } from 'vue'

export const BREAKPOINTS = {
  mobile: 640,
  tablet: 768,
  laptop: 1024,
  desktop: 1280,
} as const

export function useResponsive() {
  const screenWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)

  const isMobile = computed(() => screenWidth.value < BREAKPOINTS.mobile)
  const isCompact = computed(() => screenWidth.value < BREAKPOINTS.tablet)
  const isTablet = computed(() => screenWidth.value >= BREAKPOINTS.mobile && screenWidth.value < BREAKPOINTS.laptop)
  const isDesktop = computed(() => screenWidth.value >= BREAKPOINTS.laptop)

  let raf: number | null = null

  function onResize() {
    if (raf) return
    raf = requestAnimationFrame(() => {
      screenWidth.value = window.innerWidth
      raf = null
    })
  }

  onMounted(() => {
    screenWidth.value = window.innerWidth
    window.addEventListener('resize', onResize, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('resize', onResize)
    if (raf) cancelAnimationFrame(raf)
  })

  /**
   * Responsive modal width helper.
   * @param desktopPx - desired width on desktop (number or string)
   * @returns responsive width value for :width prop
   */
  function modalWidth(desktopPx: number): number | string {
    if (isMobile.value) return '100%'
    if (isCompact.value) return Math.min(desktopPx, screenWidth.value - 48)
    return desktopPx
  }

  return { isMobile, isTablet, isDesktop, isCompact, screenWidth, modalWidth }
}
