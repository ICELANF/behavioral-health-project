/**
 * 行健平台 �?环境配置
 * 统一管理 API 地址，替代各页面内联 _BASE
 *
 * 使用方式�? *   import { BASE_URL } from '@/config/env'
 */

// 生产环境 �?上线前改为实际域�?const PROD_URL = 'https://api.xingjian.health/api'

// 开发环�?const DEV_URL = 'http://localhost:8000/api'

export const BASE_URL: string =
  process.env.NODE_ENV === 'production' ? PROD_URL : DEV_URL

export default { BASE_URL }
