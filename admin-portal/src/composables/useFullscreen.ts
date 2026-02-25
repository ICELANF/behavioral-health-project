import { ref, onMounted, onUnmounted } from 'vue';

/**
 * 全屏模式管理 Hook
 * 使用 Fullscreen API 强制全屏并检测退出
 */
export function useFullscreen() {
  const isFullscreen = ref(false);
  const isSupported = ref(false);
  const exitCount = ref(0);
  const isEnforcing = ref(false);

  /**
   * 检查浏览器是否支持全屏
   */
  const checkSupport = () => {
    isSupported.value = !!(
      document.fullscreenEnabled ||
      (document as any).webkitFullscreenEnabled ||
      (document as any).mozFullScreenEnabled ||
      (document as any).msFullscreenEnabled
    );
    return isSupported.value;
  };

  /**
   * 请求全屏
   */
  const requestFullscreen = async (element?: HTMLElement): Promise<boolean> => {
    const el = element || document.documentElement;

    try {
      if (el.requestFullscreen) {
        await el.requestFullscreen();
      } else if ((el as any).webkitRequestFullscreen) {
        await (el as any).webkitRequestFullscreen();
      } else if ((el as any).mozRequestFullScreen) {
        await (el as any).mozRequestFullScreen();
      } else if ((el as any).msRequestFullscreen) {
        await (el as any).msRequestFullscreen();
      }

      isFullscreen.value = true;
      return true;
    } catch (error) {
      console.error('[Fullscreen] Request failed:', error);
      return false;
    }
  };

  /**
   * 退出全屏
   */
  const exitFullscreen = async (): Promise<void> => {
    try {
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      } else if ((document as any).webkitExitFullscreen) {
        await (document as any).webkitExitFullscreen();
      } else if ((document as any).mozCancelFullScreen) {
        await (document as any).mozCancelFullScreen();
      } else if ((document as any).msExitFullscreen) {
        await (document as any).msExitFullscreen();
      }

      isFullscreen.value = false;
    } catch (error) {
      console.error('[Fullscreen] Exit failed:', error);
    }
  };

  /**
   * 检查当前是否全屏
   */
  const checkFullscreen = (): boolean => {
    const fullscreenElement =
      document.fullscreenElement ||
      (document as any).webkitFullscreenElement ||
      (document as any).mozFullScreenElement ||
      (document as any).msFullscreenElement;

    isFullscreen.value = !!fullscreenElement;
    return isFullscreen.value;
  };

  /**
   * 全屏变化回调
   */
  let onFullscreenChangeCallback: ((isFullscreen: boolean) => void) | null = null;
  let onExitCallback: (() => void) | null = null;

  /**
   * 设置全屏变化回调
   */
  const onFullscreenChange = (callback: (isFullscreen: boolean) => void) => {
    onFullscreenChangeCallback = callback;
  };

  /**
   * 设置退出全屏回调
   */
  const onExit = (callback: () => void) => {
    onExitCallback = callback;
  };

  /**
   * 处理全屏变化事件
   */
  const handleFullscreenChange = () => {
    const wasFullscreen = isFullscreen.value;
    checkFullscreen();

    // 触发回调
    if (onFullscreenChangeCallback) {
      onFullscreenChangeCallback(isFullscreen.value);
    }

    // 检测退出全屏
    if (wasFullscreen && !isFullscreen.value && isEnforcing.value) {
      exitCount.value++;

      if (onExitCallback) {
        onExitCallback();
      }

    }
  };

  /**
   * 开始强制全屏模式
   */
  const startEnforcing = async (): Promise<boolean> => {
    if (!checkSupport()) {
      console.warn('[Fullscreen] Not supported by browser');
      return false;
    }

    isEnforcing.value = true;
    exitCount.value = 0;

    // 添加事件监听
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    // 请求全屏
    const success = await requestFullscreen();

    if (success) {
    }

    return success;
  };

  /**
   * 停止强制全屏模式
   */
  const stopEnforcing = async () => {
    isEnforcing.value = false;

    // 移除事件监听
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
    document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
    document.removeEventListener('MSFullscreenChange', handleFullscreenChange);

    // 退出全屏
    await exitFullscreen();

  };

  /**
   * 尝试恢复全屏
   */
  const tryRestore = async (): Promise<boolean> => {
    if (!isEnforcing.value) return false;

    return await requestFullscreen();
  };

  /**
   * 重置退出计数
   */
  const resetExitCount = () => {
    exitCount.value = 0;
  };

  // 初始化检查
  onMounted(() => {
    checkSupport();
    checkFullscreen();
  });

  // 组件卸载时清理
  onUnmounted(() => {
    if (isEnforcing.value) {
      stopEnforcing();
    }
  });

  return {
    isFullscreen,
    isSupported,
    exitCount,
    isEnforcing,
    requestFullscreen,
    exitFullscreen,
    checkFullscreen,
    startEnforcing,
    stopEnforcing,
    tryRestore,
    resetExitCount,
    onFullscreenChange,
    onExit,
  };
}
