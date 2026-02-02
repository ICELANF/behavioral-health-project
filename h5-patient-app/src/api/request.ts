import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { storage } from '@/utils/storage'
import router from '@/router'

// 扩展axios配置类型，添加自定义选项
declare module 'axios' {
  export interface AxiosRequestConfig {
    // 是否静默失败（不显示错误提示）
    silentError?: boolean
  }
}

// 创建axios实例
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
console.log('[API] Base URL:', apiBaseUrl)

const service: AxiosInstance = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    console.log('[API Request]', config.method?.toUpperCase(), config.url)
    // 添加Token
    const token = storage.token.get()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('[API] Using token:', token.substring(0, 20) + '...')
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    closeToast()

    // 检查是否静默失败
    const silentError = error.config?.silentError

    // 处理响应错误
    if (error.response) {
      const { status, data } = error.response

      // 如果配置了静默失败，不显示任何提示
      if (silentError) {
        return Promise.reject(error)
      }

      switch (status) {
        case 401:
          // Token过期或无效
          showToast('登录已过期，请重新登录')
          storage.token.remove()
          storage.user.remove()
          router.push('/login')
          break

        case 403:
          showToast('没有权限访问')
          break

        case 404:
          showToast('请求的资源不存在')
          break

        case 500:
          showToast(data?.detail || '服务器错误，请稍后重试')
          break

        default:
          showToast(data?.detail || data?.message || '请求失败')
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      if (!silentError) {
        showToast('网络连接失败，请检查网络')
      }
    } else {
      // 其他错误
      if (!silentError) {
        showToast(error.message || '请求失败')
      }
    }

    return Promise.reject(error)
  }
)

/**
 * 通用请求方法
 */
class Request {
  /**
   * GET请求
   */
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  }

  /**
   * POST请求
   */
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  }

  /**
   * PUT请求
   */
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  }

  /**
   * DELETE请求
   */
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config)
  }

  /**
   * 带加载提示的请求
   */
  async withLoading<T = any>(
    promise: Promise<T>,
    loadingText: string = '加载中...'
  ): Promise<T> {
    showLoadingToast({
      message: loadingText,
      forbidClick: true,
      duration: 0
    })

    try {
      const result = await promise
      closeToast()
      return result
    } catch (error) {
      closeToast()
      throw error
    }
  }
}

export default new Request()
