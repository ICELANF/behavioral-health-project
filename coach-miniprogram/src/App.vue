<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'

onLaunch(() => {
  // 恢复登录态
  const userStore = useUserStore()
  userStore.restoreFromStorage()
})

onShow(() => {})
onHide(() => {})
</script>

<style lang="css">
/* ─── BHP Design System ─── */
@import '@/styles/bhp-design-tokens.css';

/* ─── 全局重置 ─── */
page {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
  background-color: var(--surface-secondary);
  color: var(--text-primary);
  font-size: 28rpx;
  line-height: 1.6;
  box-sizing: border-box;
}

/* 通用卡片 */
.bhp-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
.bhp-card--flat {
  box-shadow: none;
  border: 1px solid var(--border-light);
}

/* 骨架屏 */
.bhp-skeleton {
  background: linear-gradient(90deg, var(--bhp-gray-100) 25%, var(--bhp-gray-50) 50%, var(--bhp-gray-100) 75%);
  background-size: 400% 100%;
  animation: bhp-shimmer 1.5s ease infinite;
  border-radius: var(--radius-md);
}
@keyframes bhp-shimmer {
  0%   { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* 输入框 */
.bhp-input-wrap {
  display: flex;
  align-items: center;
  gap: 12rpx;
  background: var(--surface-secondary);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0 20rpx;
  height: 88rpx;
  transition: border-color 0.2s;
}
.bhp-input-wrap:focus-within { border-color: var(--bhp-primary-500); }
.bhp-input-wrap--error       { border-color: var(--bhp-danger); }
.bhp-input {
  flex: 1;
  height: 88rpx;
  font-size: 28rpx;
  color: var(--text-primary);
  background: transparent;
}

/* 按钮 */
.bhp-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 28rpx;
  font-weight: 600;
  padding: 0 40rpx;
  height: 80rpx;
  border: none;
  cursor: pointer;
  transition: opacity 0.15s;
}
.bhp-btn::after { border: none; }
.bhp-btn:active { opacity: 0.82; }
.bhp-btn--primary  { background: var(--bhp-primary-500); color: #fff; }
.bhp-btn--outline  { background: transparent; color: var(--bhp-primary-500); border: 1.5px solid var(--bhp-primary-500); }
.bhp-btn--ghost    { background: transparent; color: var(--text-secondary); }
.bhp-btn--danger   { background: var(--bhp-danger); color: #fff; }
.bhp-btn--full     { width: 100%; }
.bhp-btn--lg       { height: 96rpx; font-size: 32rpx; }
.bhp-btn--sm       { height: 60rpx; font-size: 24rpx; padding: 0 20rpx; border-radius: var(--radius-sm); }
.bhp-btn--disabled { opacity: 0.5; pointer-events: none; }

/* 工具类 */
.px-4   { padding-left: 32rpx; padding-right: 32rpx; }
.py-3   { padding-top: 24rpx; padding-bottom: 24rpx; }
.mt-1   { margin-top: 8rpx; }
.mt-2   { margin-top: 16rpx; }
.mt-3   { margin-top: 24rpx; }
.mb-2   { margin-bottom: 16rpx; }
.flex-center { display: flex; align-items: center; justify-content: center; }
.text-xs  { font-size: 22rpx; }
.text-sm  { font-size: 24rpx; }
.text-lg  { font-size: 32rpx; }
.text-xl  { font-size: 36rpx; }
.text-2xl { font-size: 44rpx; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.text-primary-color   { color: var(--bhp-primary-500); }
.text-secondary-color { color: var(--text-secondary); }
.text-tertiary-color  { color: var(--text-tertiary); }
.text-error-color     { color: var(--bhp-danger); }
.safe-area-top    { padding-top: env(safe-area-inset-top); }
.safe-area-bottom { padding-bottom: env(safe-area-inset-bottom); }
</style>
