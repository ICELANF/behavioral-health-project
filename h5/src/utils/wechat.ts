/**
 * WeChat JSSDK utilities.
 * All methods are no-ops when not in WeChat browser.
 */
import api from '@/api/index'

/** Detect if running inside WeChat browser */
export function isWechat(): boolean {
  return /MicroMessenger/i.test(navigator.userAgent)
}

/** Initialize WeChat JSSDK — call once on app mount */
export async function initWechatSDK(): Promise<boolean> {
  if (!isWechat()) return false

  try {
    // Dynamic import to avoid bundling when not needed
    const wx = (await import('weixin-js-sdk')).default
    const res: any = await api.get('/api/v1/wechat/jsapi-ticket', {
      params: { url: window.location.href.split('#')[0] }
    })
    if (!res.configured) return false

    wx.config({
      debug: false,
      appId: res.appId,
      timestamp: res.timestamp,
      nonceStr: res.nonceStr,
      signature: res.signature,
      jsApiList: [
        'updateAppMessageShareData',
        'updateTimelineShareData',
        'scanQRCode',
      ],
    })

    return new Promise((resolve) => {
      wx.ready(() => resolve(true))
      wx.error(() => resolve(false))
    })
  } catch {
    return false
  }
}

/** Configure WeChat share card */
export async function shareToWechat(
  title: string,
  desc: string,
  link: string,
  imgUrl: string,
): Promise<void> {
  if (!isWechat()) return

  try {
    const wx = (await import('weixin-js-sdk')).default
    const shareData = { title, desc, link, imgUrl }
    wx.updateAppMessageShareData(shareData)
    wx.updateTimelineShareData({ title, link, imgUrl })
  } catch {
    // Silently fail when not in WeChat
  }
}
