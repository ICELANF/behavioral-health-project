/**
 * 行健平台 - 环境配置
 * 统一管理 API 地址，替代各页面内联 _BASE
 *
 * 使用方式:
 *   import { BASE_URL } from '@/config/env'
 *
 * 生产部署时在 .env.production 中设置:
 *   VITE_API_URL=https://api.xingjian.health/api
 */

const DEV_URL = 'http://localhost:8000/api'

export const BASE_URL: string =
  (import.meta as any).env?.VITE_API_URL || DEV_URL

export default { BASE_URL }
