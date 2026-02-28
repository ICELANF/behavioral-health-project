/**
 * 微信小程序工具函数
 * 包含: 一键登录 / 获取用户信息 / 分享配置
 */

import authApi from '@/api/auth'
import { useUserStore } from '@/stores/user'

// ─── 微信一键登录 ────────────────────────────────────────────
export async function wechatLogin(): Promise<boolean> {
  return new Promise((resolve) => {
    // #ifdef MP-WEIXIN
    uni.login({
      provider: 'weixin',
      success: async (loginRes) => {
        if (!loginRes.code) { resolve(false); return }
        try {
          const res = await authApi.wechatLogin({ code: loginRes.code })
          const userStore = useUserStore()
          userStore.setAuth(
            { access_token: res.access_token, refresh_token: res.refresh_token },
            res.user
          )
          resolve(true)
        } catch {
          resolve(false)
        }
      },
      fail: () => resolve(false)
    })
    // #endif
    // #ifndef MP-WEIXIN
    resolve(false)
    // #endif
  })
}

// ─── 获取微信用户头像昵称（需用户主动授权，微信新规）────────
export async function getWxUserProfile(): Promise<{ nickName: string; avatarUrl: string } | null> {
  return new Promise((resolve) => {
    // #ifdef MP-WEIXIN
    uni.getUserProfile({
      desc: '用于完善个人信息',
      success: (res) => resolve({ nickName: res.userInfo.nickName, avatarUrl: res.userInfo.avatarUrl }),
      fail: () => resolve(null)
    })
    // #endif
    // #ifndef MP-WEIXIN
    resolve(null)
    // #endif
  })
}

// ─── 配置分享（页面级调用）──────────────────────────────────
export function setupShare(options: {
  title?: string
  path?: string
  imageUrl?: string
}) {
  // #ifdef MP-WEIXIN
  return {
    title:    options.title    || '行健平台 · 行为健康管理',
    path:     options.path     || '/pages/auth/login',
    imageUrl: options.imageUrl || '/static/share-cover.png'
  }
  // #endif
}

// ─── 检测环境 ────────────────────────────────────────────────
export const isMiniprogram = (() => {
  // #ifdef MP-WEIXIN
  return true
  // #endif
  // #ifndef MP-WEIXIN
  return false
  // #endif
})()

// ─── 安全区域高度 ────────────────────────────────────────────
let _safeAreaBottom = 0
export function getSafeAreaBottom(): number {
  if (_safeAreaBottom > 0) return _safeAreaBottom
  try {
    const { safeArea, screenHeight } = uni.getSystemInfoSync()
    _safeAreaBottom = safeArea ? screenHeight - safeArea.bottom : 0
  } catch { _safeAreaBottom = 0 }
  return _safeAreaBottom
}

// ─── 状态栏高度 ─────────────────────────────────────────────
let _statusBarHeight = 0
export function getStatusBarHeight(): number {
  if (_statusBarHeight > 0) return _statusBarHeight
  try {
    _statusBarHeight = uni.getSystemInfoSync().statusBarHeight || 0
  } catch { _statusBarHeight = 0 }
  return _statusBarHeight
}
