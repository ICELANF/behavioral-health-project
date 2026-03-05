<template>
  <div class="app-shell">
    <router-view />
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html { font-size: 16px; -webkit-text-size-adjust: 100%; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif; background: #f5f6fa; color: #2c3e50; }
.app-shell { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #f5f6fa; position: relative; }

/* uni-toast compat */
.uni-toast { position: fixed; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; z-index: 9999; pointer-events: none; }
.uni-toast-inner { background: rgba(0,0,0,0.7); color: #fff; padding: 12px 24px; border-radius: 8px; font-size: 14px; max-width: 80vw; text-align: center; pointer-events: auto; }
.uni-toast-icon { display: block; font-size: 36px; margin-bottom: 6px; color: #67c23a; }

/* scroll-view → div with overflow */
scroll-view { display: block; overflow-y: auto; -webkit-overflow-scrolling: touch; }
</style>
