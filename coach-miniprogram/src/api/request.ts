/**
 * HTTP 请求封装
 * - 自动附加 JWT Authorization 头
 * - 401 时自动刷新 Token，刷新失败则跳登录
 * - 统一错误 Toast（可通过 noToast 选项关闭）
 */

const BASE_URL = 'http://localhost:8000/api'

interface RequestOptions {
  noAuth?:  boolean   // 跳过 Authorization 头（登录/注册接口）
  noToast?: boolean   // 不弹错误提示
}

let isRefreshing  = false
let refreshQueue: Array<(token: string) => void> = []

function getToken(): string {
  return uni.getStorageSync('access_token') || ''
}
function getRefreshToken(): string {
  return uni.getStorageSync('refresh_token') || ''
}
function saveToken(access: string) {
  uni.setStorageSync('access_token', access)
}
function clearAuth() {
  uni.removeStorageSync('access_token')
  uni.removeStorageSync('refresh_token')
  uni.removeStorageSync('user_info')
}

async function refreshAccessToken(): Promise<string> {
  const rt = getRefreshToken()
  if (!rt) throw new Error('no refresh token')
  const res: any = await new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}/v1/auth/refresh`,
      method: 'POST',
      data: { refresh_token: rt },
      success: (r) => resolve(r),
      fail:    (e) => reject(e),
    })
  })
  if (res.statusCode !== 200) throw new Error('refresh failed')
  const newToken = (res.data as any).access_token
  saveToken(newToken)
  return newToken
}

function goLogin() {
  clearAuth()
  uni.reLaunch({ url: '/pages/auth/login' })
}

function request<T = any>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  path: string,
  data?: any,
  options: RequestOptions = {}
): Promise<T> {
  return new Promise((resolve, reject) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (!options.noAuth) {
      const token = getToken()
      if (token) headers['Authorization'] = `Bearer ${token}`
    }

    const url = path.startsWith('http') ? path : `${BASE_URL}/${path.replace(/^\//, '')}`

    uni.request({
      url,
      method,
      data,
      header: headers,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
          return
        }

        // 401 — 尝试刷新 Token
        if (res.statusCode === 401 && !options.noAuth) {
          if (isRefreshing) {
            refreshQueue.push((newToken) => {
              headers['Authorization'] = `Bearer ${newToken}`
              uni.request({
                url, method, data, header: headers,
                success: (r2) => resolve(r2.data as T),
                fail:    (e2) => reject(e2),
              })
            })
            return
          }
          isRefreshing = true
          refreshAccessToken()
            .then((newToken) => {
              isRefreshing = false
              refreshQueue.forEach(fn => fn(newToken))
              refreshQueue = []
              headers['Authorization'] = `Bearer ${newToken}`
              uni.request({
                url, method, data, header: headers,
                success: (r2) => {
                  if (r2.statusCode >= 200 && r2.statusCode < 300) resolve(r2.data as T)
                  else reject(r2.data)
                },
                fail: (e2) => reject(e2),
              })
            })
            .catch(() => {
              isRefreshing = false
              refreshQueue = []
              goLogin()
              reject(new Error('Session expired'))
            })
          return
        }

        const errData = res.data as any
        if (!options.noToast) {
          const msg = errData?.detail || errData?.message || `请求失败 (${res.statusCode})`
          uni.showToast({ title: String(msg).slice(0, 30), icon: 'none' })
        }
        reject({ statusCode: res.statusCode, data: errData })
      },
      fail(err) {
        if (!options.noToast) {
          uni.showToast({ title: '网络异常，请检查连接', icon: 'none' })
        }
        reject(err)
      },
    })
  })
}

const http = {
  get<T = any>(path: string, params?: Record<string, any>, opts?: RequestOptions): Promise<T> {
    if (params && Object.keys(params).length) {
      const qs = Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join('&')
      path = `${path}?${qs}`
    }
    return request<T>('GET', path, undefined, opts)
  },
  post<T = any>(path: string, data?: any, opts?: RequestOptions): Promise<T> {
    return request<T>('POST', path, data, opts)
  },
  put<T = any>(path: string, data?: any, opts?: RequestOptions): Promise<T> {
    return request<T>('PUT', path, data, opts)
  },
  patch<T = any>(path: string, data?: any, opts?: RequestOptions): Promise<T> {
    return request<T>('PATCH', path, data, opts)
  },
  delete<T = any>(path: string, opts?: RequestOptions): Promise<T> {
    return request<T>('DELETE', path, undefined, opts)
  },
}

export default http
