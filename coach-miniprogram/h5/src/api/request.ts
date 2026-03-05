/**
 * H5 HTTP request module — drop-in replacement for miniprogram request.ts.
 * Uses fetch instead of uni.request. Keeps the same httpReq<T>() API.
 */

const API_HOST = import.meta.env.VITE_API_HOST || ''
const BASE_URL = `${API_HOST}/api/v1`

interface RequestOptions {
  noAuth?: boolean
  noToast?: boolean
}

function getToken(): string {
  return localStorage.getItem('access_token') || ''
}
function getRefreshToken(): string {
  return localStorage.getItem('refresh_token') || ''
}
function saveToken(access: string) {
  localStorage.setItem('access_token', access)
}
function clearAuth() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_info')
}

let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

async function refreshAccessToken(): Promise<string> {
  const rt = getRefreshToken()
  if (!rt) throw new Error('no refresh token')
  const res = await fetch(`${API_HOST}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: rt }),
  })
  if (!res.ok) throw new Error('refresh failed')
  const data = await res.json()
  saveToken(data.access_token)
  return data.access_token
}

function goLogin() {
  clearAuth()
  window.location.href = '/auth/login'
}

function showToast(msg: string) {
  // Reuse the uni compat toast if loaded, else alert
  if ((window as any).uni?.showToast) {
    (window as any).uni.showToast({ title: msg, icon: 'none' })
  }
}

async function request<T = any>(
  method: string,
  path: string,
  data?: any,
  options: RequestOptions = {}
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (!options.noAuth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const url = path.startsWith('http') ? path
    : path.startsWith('/api/') ? `${API_HOST}${path}`
    : `${BASE_URL}/${path.replace(/^\//, '')}`

  const fetchOpts: RequestInit = { method, headers }
  if (data && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    fetchOpts.body = JSON.stringify(data)
  }

  let res: Response
  try {
    res = await fetch(url, fetchOpts)
  } catch {
    if (!options.noToast) showToast('网络异常，请检查连接')
    throw new Error('network error')
  }

  if (res.ok) return res.json()

  // 401 — try refresh
  if (res.status === 401 && !options.noAuth) {
    if (isRefreshing) {
      return new Promise<T>((resolve, reject) => {
        refreshQueue.push(async (newToken) => {
          headers['Authorization'] = `Bearer ${newToken}`
          try {
            const r2 = await fetch(url, { ...fetchOpts, headers })
            if (r2.ok) resolve(await r2.json())
            else reject(await r2.json().catch(() => ({})))
          } catch (e) { reject(e) }
        })
      })
    }
    isRefreshing = true
    try {
      const newToken = await refreshAccessToken()
      isRefreshing = false
      refreshQueue.forEach(fn => fn(newToken))
      refreshQueue = []
      headers['Authorization'] = `Bearer ${newToken}`
      const r2 = await fetch(url, { ...fetchOpts, headers })
      if (r2.ok) return r2.json()
      throw await r2.json().catch(() => ({}))
    } catch {
      isRefreshing = false
      refreshQueue = []
      goLogin()
      throw new Error('Session expired')
    }
  }

  const errData = await res.json().catch(() => ({}))
  if (!options.noToast) {
    if (res.status === 403) {
      console.warn('[403]', path, errData?.detail)
    } else {
      const msg = errData?.detail || errData?.message || `请求失败 (${res.status})`
      showToast(String(msg).slice(0, 30))
    }
  }
  throw { statusCode: res.status, data: errData }
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
  post<T = any>(path: string, data?: any, opts?: RequestOptions) { return request<T>('POST', path, data, opts) },
  put<T = any>(path: string, data?: any, opts?: RequestOptions) { return request<T>('PUT', path, data, opts) },
  patch<T = any>(path: string, data?: any, opts?: RequestOptions) { return request<T>('PATCH', path, data, opts) },
  delete<T = any>(path: string, opts?: RequestOptions) { return request<T>('DELETE', path, undefined, opts) },
}

export function httpReq<T = any>(url: string, opts: { method?: string; data?: any } = {}): Promise<T> {
  const method = (opts.method || 'GET').toUpperCase()
  return request<T>(method, url, opts.data)
}

export { getToken }
export const apiHost = API_HOST

export default http
