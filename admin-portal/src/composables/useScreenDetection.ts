import { ref, onMounted, onUnmounted } from 'vue';

/**
 * 切屏检测违规记录
 */
export interface ScreenViolation {
  id: string;
  type: 'visibility_change' | 'blur' | 'focus_loss';
  timestamp: string;
  duration_ms: number;
  reported: boolean;
}

/**
 * 切屏检测 Hook
 * 使用 Visibility API 和 blur/focus 事件检测用户是否离开考试页面
 */
export function useScreenDetection() {
  const violations = ref<ScreenViolation[]>([]);
  const violationCount = ref(0);
  const isPageVisible = ref(true);
  const isMonitoring = ref(false);

  let hiddenStartTime: number | null = null;
  let currentViolationId: string | null = null;

  /**
   * 生成违规ID
   */
  const generateViolationId = () => {
    return `v_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  /**
   * 记录违规
   */
  const recordViolation = (type: ScreenViolation['type']) => {
    const violation: ScreenViolation = {
      id: generateViolationId(),
      type,
      timestamp: new Date().toISOString(),
      duration_ms: 0,
      reported: false,
    };

    violations.value.push(violation);
    violationCount.value++;
    currentViolationId = violation.id;

    return violation;
  };

  /**
   * 更新违规时长
   */
  const updateViolationDuration = (durationMs: number) => {
    if (currentViolationId) {
      const violation = violations.value.find((v) => v.id === currentViolationId);
      if (violation) {
        violation.duration_ms = durationMs;
      }
      currentViolationId = null;
    }
  };

  /**
   * 处理页面可见性变化
   */
  const handleVisibilityChange = () => {
    if (!isMonitoring.value) return;

    if (document.visibilityState === 'hidden') {
      isPageVisible.value = false;
      hiddenStartTime = Date.now();
      recordViolation('visibility_change');
    } else {
      isPageVisible.value = true;
      if (hiddenStartTime) {
        const duration = Date.now() - hiddenStartTime;
        updateViolationDuration(duration);
        hiddenStartTime = null;
      }
    }
  };

  /**
   * 处理窗口失焦
   */
  const handleWindowBlur = () => {
    if (!isMonitoring.value) return;

    isPageVisible.value = false;
    hiddenStartTime = Date.now();
    recordViolation('blur');
  };

  /**
   * 处理窗口获焦
   */
  const handleWindowFocus = () => {
    if (!isMonitoring.value) return;

    isPageVisible.value = true;
    if (hiddenStartTime) {
      const duration = Date.now() - hiddenStartTime;
      updateViolationDuration(duration);
      hiddenStartTime = null;
    }
  };

  /**
   * 处理页面关闭/刷新
   */
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (!isMonitoring.value) return;

    e.preventDefault();
    e.returnValue = '考试进行中，确定要离开吗？您的答案可能不会被保存。';
    return e.returnValue;
  };

  /**
   * 开始监控
   */
  const startMonitoring = () => {
    if (isMonitoring.value) return;

    isMonitoring.value = true;
    violations.value = [];
    violationCount.value = 0;

    // 添加事件监听
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);
    window.addEventListener('focus', handleWindowFocus);
    window.addEventListener('beforeunload', handleBeforeUnload);

  };

  /**
   * 停止监控
   */
  const stopMonitoring = () => {
    if (!isMonitoring.value) return;

    isMonitoring.value = false;

    // 移除事件监听
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    window.removeEventListener('blur', handleWindowBlur);
    window.removeEventListener('focus', handleWindowFocus);
    window.removeEventListener('beforeunload', handleBeforeUnload);

  };

  /**
   * 获取未上报的违规
   */
  const getUnreportedViolations = () => {
    return violations.value.filter((v) => !v.reported);
  };

  /**
   * 标记违规为已上报
   */
  const markAsReported = (violationIds: string[]) => {
    violations.value.forEach((v) => {
      if (violationIds.includes(v.id)) {
        v.reported = true;
      }
    });
  };

  /**
   * 清空违规记录
   */
  const clearViolations = () => {
    violations.value = [];
    violationCount.value = 0;
  };

  // 组件卸载时清理
  onUnmounted(() => {
    stopMonitoring();
  });

  return {
    violations,
    violationCount,
    isPageVisible,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    getUnreportedViolations,
    markAsReported,
    clearViolations,
  };
}
