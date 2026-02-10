import axios from 'axios'
import { message } from 'ant-design-vue'

// 创建 axios 实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  async (config) => {
    const token = localStorage.getItem('admin_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // FormData: let axios auto-set Content-Type with correct multipart boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    // 注入 X-Source-UI 协议头，与后端 SOP 6.2 防火墙对齐
    try {
      const { default: router } = await import('../router')
      const sourceUI = router.currentRoute.value.meta.sourceUI as string || 'UI-G'
      config.headers['X-Source-UI'] = sourceUI
    } catch {
      config.headers['X-Source-UI'] = 'UI-G'
    }

    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { data } = response
    // 后端返回 success: false 的情况
    if (data && data.success === false) {
      message.error(data.error || data.message || '操作失败')
      return Promise.reject(new Error(data.error || data.message))
    }
    return response
  },
  (error) => {
    // 处理 HTTP 错误
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          message.error('登录已过期，请重新登录')
          localStorage.removeItem('admin_token')
          import('../router').then(m => m.default.push('/login'))
          break
        case 403:
          message.error('没有权限执行此操作')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 500:
          message.error('服务器内部错误')
          break
        default:
          message.error(data?.message || data?.error || `请求失败 (${status})`)
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络')
    } else {
      message.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

export default request
