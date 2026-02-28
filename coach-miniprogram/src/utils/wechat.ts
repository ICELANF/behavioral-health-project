/**
 * 微信小程序工具函数
 * - isMiniprogram: 运行环境检测
 * - wechatLogin: 微信一键登录流程
 */
import authApi from '@/api/auth'
import { useUserStore } from '@/stores/user'

/** 是否在微信小程序环境 */
export const isMiniprogram = (() => {
  // #ifdef MP-WEIXIN
  return true
  // #endif
  // #ifndef MP-WEIXIN
  return false
  // #endif
})()

/**
 * 微信登录
 * 1. wx.login() 获取 code
 * 2. POST /v1/auth/wechat/miniprogram { code }
 * 3. 写入 userStore
 * @returns 登录是否成功
 */
export async function wechatLogin(): Promise<boolean> {
  try {
    const code = await getWxCode()
    if (!code) return false
    const res = await authApi.wechatLogin({ code })
    const userStore = useUserStore()
    userStore.setAuth(
      { access_token: res.access_token, refresh_token: res.refresh_token },
      res.user
    )
    return true
  } catch (err) {
    console.error('[wechat] login error:', err)
    return false
  }
}

/** 获取微信登录 code */
function getWxCode(): Promise<string> {
  return new Promise((resolve) => {
    // #ifdef MP-WEIXIN
    wx.login({
      success: (res) => resolve(res.code || ''),
      fail:    ()    => resolve(''),
    })
    // #endif
    // #ifndef MP-WEIXIN
    resolve('')
    // #endif
  })
}

/**
 * 获取用户头像（小程序 wx.getUserProfile）
 * 返回 avatarUrl 或空字符串
 */
export function getWxAvatar(): Promise<string> {
  return new Promise((resolve) => {
    // #ifdef MP-WEIXIN
    wx.getUserProfile({
      desc: '用于完善您的个人资料',
      success: (res) => resolve(res.userInfo?.avatarUrl || ''),
      fail:    ()    => resolve(''),
    })
    // #endif
    // #ifndef MP-WEIXIN
    resolve('')
    // #endif
  })
}

/**
 * 复制文本到剪贴板
 */
export function copyToClipboard(text: string, tip = '已复制') {
  uni.setClipboardData({
    data: text,
    success: () => uni.showToast({ title: tip, icon: 'success', duration: 1500 }),
  })
}
