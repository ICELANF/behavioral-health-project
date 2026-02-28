/**
 * HTTP 请求封装 — uni-app 版
 * 功能：Token 自动注入 / 401 自动刷新 / 统一错误处理 / 小程序+H5 双端兼容
 */

// ─── 环境配置 ───────────────────────────────────────────────
const BASE_URL = (() => {
  // #ifdef H5
  return '/api'          // H5 走 vite proxy 反代
  // #endif
  // #ifndef H5
  // 小程序生产环境：替换为真实域名
  // 开发期间：微信开发者工具 → 详情 → 本地设置 → 不校验合法域名
  return 'https://your-domain.com/api'
  // #endif
})()

const TOKEN_KEY   = 'bhp_access_token'
const REFRESH_KEY = 'bhp_refresh_token'
const USER_KEY    = 'bhp_user_info'

// ─── Token 工具 ─────────────────────────────────────────────
export const tokenStorage = {
  getAccess:  (): string => uni.getStorageSync(TOKEN_KEY)   || '',
  getRefresh: (): string => uni.getStorageSync(REFRESH_KEY) || '',
  setTokens(access: string, refresh: string) {
    uni.setStorageSync(TOKEN_KEY, access)
    uni.setStorageSync(REFRESH_KEY, refresh)
  },
  clear() {
    uni.removeStorageSync(TOKEN_KEY)
    uni.removeStorageSync(REFRESH_KEY)
    uni.removeStorageSync(USER_KEY)
  }
}

// ─── 刷新 Token 互斥锁（防并发多次刷新）────────────────────
let refreshing = false
let refreshQueue: Array<(token: string) => void> = []

async function refreshAccessToken(): Promise<string> {
  if (refreshing) {
    return new Promise(resolve => { refreshQueue.push(resolve) })
  }
  refreshing = true
  const refreshToken = tokenStorage.getRefresh()
  if (!refreshToken) {
    refreshing = false
    throw new Error('NO_REFRESH_TOKEN')
  }
  try {
    const res = await rawRequest<{ access_token: string }>({
      url: '/auth/refresh',
      method: 'POST',
      data: { refresh_token: refreshToken }
    })
    const newToken = res.access_token
    tokenStorage.setTokens(newToken, refreshToken)
    refreshQueue.forEach(cb => cb(newToken))
    refreshQueue = []
    return newToken
  } finally {
    refreshing = false
  }
}

// ─── 跳转登录 ───────────────────────────────────────────────
function redirectToLogin() {
  tokenStorage.clear()
  uni.reLaunch({ url: '/pages/auth/login' })
}

// ─── 底层请求（不带重试）────────────────────────────────────
function rawRequest<T = any>(options: RequestOptions): Promise<T> {
  const url = options.url.startsWith('http')
    ? options.url
    : `${BASE_URL}${options.url}`

  return new Promise((resolve, reject) => {
    uni.request({
      url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        ...options.header,
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {})
      },
      timeout: options.timeout || 15000,
      success: (res: any) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          reject({ statusCode: res.statusCode, data: res.data })
        }
      },
      fail: (err: any) => reject({ statusCode: 0, message: err.errMsg || '网络请求失败' })
    })
  })
}

// ─── 主请求函数（带 Token + 自动刷新）──────────────────────
export interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  data?: any
  header?: Record<string, string>
  token?: string
  timeout?: number
  noAuth?: boolean    // true = 不带 token（登录/注册接口）
  noToast?: boolean   // true = 不自动弹错误 toast
}

export async function request<T = any>(options: RequestOptions): Promise<T> {
  const token = tokenStorage.getAccess()

  const doRequest = async (tk?: string): Promise<T> => {
    return rawRequest<T>({
      ...options,
      token: options.noAuth ? undefined : (tk || token)
    })
  }

  try {
    return await doRequest()
  } catch (err: any) {
    if (err.statusCode === 401 && !options.noAuth) {
      try {
        const newToken = await refreshAccessToken()
        return await doRequest(newToken)
      } catch {
        redirectToLogin()
        throw err
      }
    }
    // 统一错误提示
    if (!options.noToast) {
      const msg = err.data?.detail || err.data?.message || err.message || '请求失败'
      uni.showToast({ title: typeof msg === 'string' ? msg : '操作失败', icon: 'none', duration: 2000 })
    }
    throw err
  }
}

// ─── 便捷方法 ────────────────────────────────────────────────
export const http = {
  get: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'GET', data, ...opts }),

  post: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'POST', data, ...opts }),

  put: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'PUT', data, ...opts }),

  patch: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'PATCH', data, ...opts }),

  delete: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'DELETE', data, ...opts })
}

export default http
