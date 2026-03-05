/**
 * uni-app API compatibility layer for H5.
 * Provides uni.* shims so page components work without modification.
 */
import router from '../router'

function showToast(opts: { title: string; icon?: string; duration?: number; image?: string }) {
  const el = document.createElement('div')
  el.className = 'uni-toast'
  el.innerHTML = `<div class="uni-toast-inner">${opts.icon === 'success' ? '<span class="uni-toast-icon">&#10003;</span>' : ''}${opts.title}</div>`
  document.body.appendChild(el)
  setTimeout(() => el.remove(), opts.duration || 2000)
}

function showModal(opts: { title?: string; content: string; showCancel?: boolean; confirmText?: string; cancelText?: string; success?: (res: { confirm: boolean; cancel: boolean }) => void }) {
  const ok = opts.showCancel === false ? true : confirm(`${opts.title ? opts.title + '\n' : ''}${opts.content}`)
  opts.success?.({ confirm: ok, cancel: !ok })
}

function showLoading(opts?: { title?: string }) {
  const el = document.createElement('div')
  el.id = 'uni-loading'
  el.className = 'uni-toast'
  el.innerHTML = `<div class="uni-toast-inner">${opts?.title || '加载中...'}</div>`
  document.body.appendChild(el)
}

function hideLoading() {
  document.getElementById('uni-loading')?.remove()
}

function navigateTo(opts: { url: string }) {
  const { path, query } = parseUrl(opts.url)
  router.push({ path, query })
}

function redirectTo(opts: { url: string }) {
  const { path, query } = parseUrl(opts.url)
  router.replace({ path, query })
}

function navigateBack(opts?: { delta?: number }) {
  if (window.history.length > 1) router.back()
  else router.replace('/')
}

function switchTab(opts: { url: string }) {
  const { path } = parseUrl(opts.url)
  router.replace(path)
}

function reLaunch(opts: { url: string }) {
  const { path, query } = parseUrl(opts.url)
  router.replace({ path, query })
}

function getStorageSync(key: string): any {
  try {
    const v = localStorage.getItem(key)
    if (v === null) return ''
    try { return JSON.parse(v) } catch { return v }
  } catch { return '' }
}

function setStorageSync(key: string, val: any) {
  localStorage.setItem(key, typeof val === 'string' ? val : JSON.stringify(val))
}

function removeStorageSync(key: string) {
  localStorage.removeItem(key)
}

function getSystemInfoSync() {
  return {
    windowWidth: window.innerWidth,
    windowHeight: window.innerHeight,
    screenWidth: screen.width,
    screenHeight: screen.height,
    statusBarHeight: 0,
    pixelRatio: window.devicePixelRatio,
    platform: 'h5',
  }
}

function createSelectorQuery() {
  return {
    select(sel: string) {
      return {
        boundingClientRect(cb?: (rect: DOMRect | null) => void) {
          const el = document.querySelector(sel)
          const rect = el?.getBoundingClientRect() ?? null
          cb?.(rect)
          return { exec(fn?: Function) { fn?.([rect]) } }
        },
      }
    },
    exec(fn?: Function) { fn?.([]) },
  }
}

function chooseImage(opts: { count?: number; success?: (res: { tempFilePaths: string[] }) => void }) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.multiple = (opts.count || 1) > 1
  input.onchange = () => {
    const files = Array.from(input.files || [])
    const paths = files.map(f => URL.createObjectURL(f))
    opts.success?.({ tempFilePaths: paths })
  }
  input.click()
}

function previewImage(opts: { urls: string[]; current?: string }) {
  // Simple preview: open in new tab
  window.open(opts.current || opts.urls[0], '_blank')
}

function makePhoneCall(opts: { phoneNumber: string }) {
  window.location.href = 'tel:' + opts.phoneNumber
}

function setNavigationBarTitle(opts: { title: string }) {
  document.title = opts.title
}

// Helper: parse miniprogram URL format "/pages/foo/bar?id=1" → { path, query }
function parseUrl(url: string): { path: string; query: Record<string, string> } {
  const [pathPart, qs] = url.split('?')
  // Convert /pages/xxx/yyy to /xxx/yyy
  const path = pathPart.replace(/^\/pages/, '')
  const query: Record<string, string> = {}
  if (qs) {
    qs.split('&').forEach(p => {
      const [k, v] = p.split('=')
      if (k) query[k] = decodeURIComponent(v || '')
    })
  }
  return { path, query }
}

// getCurrentPages shim
function getCurrentPages() {
  return [{ route: router.currentRoute.value.path }]
}

// Stub for APIs that need WeChat environment
function login(_opts?: any) { console.warn('[H5] uni.login requires WeChat environment') }
function getLocation(_opts?: any) { console.warn('[H5] uni.getLocation not available in H5') }
function scanCode(_opts?: any) { console.warn('[H5] uni.scanCode not available in H5') }
function requestPayment(_opts?: any) { console.warn('[H5] uni.requestPayment not available in H5') }

export const uni = {
  showToast,
  showModal,
  showLoading,
  hideLoading,
  navigateTo,
  redirectTo,
  navigateBack,
  switchTab,
  reLaunch,
  getStorageSync,
  setStorageSync,
  removeStorageSync,
  getSystemInfoSync,
  createSelectorQuery,
  chooseImage,
  previewImage,
  makePhoneCall,
  setNavigationBarTitle,
  login,
  getLocation,
  scanCode,
  requestPayment,
}

// Install as global
;(window as any).uni = uni

// uni-app lifecycle shims
export function onLoad(fn: (query?: Record<string, string>) => void) {
  // Will be called in component setup with route.query
  const route = router.currentRoute.value
  fn(route.query as Record<string, string>)
}

export function onShow(fn: () => void) {
  fn()
}

export function onHide(_fn: () => void) {
  // no-op in H5
}

export function onPullDownRefresh(_fn: () => void) {
  // no-op in H5
}

export function onReachBottom(_fn: () => void) {
  // no-op in H5
}

export default uni
