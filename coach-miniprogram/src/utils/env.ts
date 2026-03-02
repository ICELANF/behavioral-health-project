/**
 * H5 模式 API 请求适配
 * 
 * H5 模式下:
 * - 开发环境: 通过 devServer proxy 转发到 localhost:8000
 * - 生产环境: 需要配置 nginx 反向代理或修改 BASE_URL
 * 
 * 小程序模式下:
 * - 直接请求 localhost:8000（开发）或正式域名（生产）
 */

// 自动检测运行环境
export function getBaseUrl(): string {
  // #ifdef H5
  // H5 模式: 开发环境用代理，生产环境用完整URL
  if (import.meta.env.DEV) {
    return ''  // 通过 devServer proxy 转发
  }
  return import.meta.env.VITE_API_BASE || 'https://your-domain.com'
  // #endif

  // #ifdef MP-WEIXIN
  // 小程序模式
  return 'http://localhost:8000'
  // #endif

  // 默认
  return 'http://localhost:8000'
}