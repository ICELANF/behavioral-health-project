import { ref, computed, watch, onUnmounted } from 'vue';
import { useScreenDetection, type ScreenViolation } from './useScreenDetection';
import { useFullscreen } from './useFullscreen';
import { useProctorCamera, type Snapshot, type SnapshotConfig } from './useProctorCamera';

/**
 * 违规记录（统一格式）
 */
export interface Violation {
  id: string;
  type: 'screen_switch' | 'tab_change' | 'window_blur' | 'fullscreen_exit' | 'face_not_detected' | 'multiple_faces';
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  duration_ms?: number;
  snapshotId?: string;
  details?: Record<string, any>;
}

/**
 * 防作弊配置
 */
export interface AntiCheatConfig {
  enableScreenDetection: boolean;
  enableFullscreen: boolean;
  enableProctor: boolean;
  maxViolations: number;           // 最大违规次数（超过自动提交）
  warningThreshold: number;        // 警告阈值
  autoSubmitThreshold: number;     // 自动提交阈值
  proctorConfig?: Partial<SnapshotConfig>;
}

const defaultConfig: AntiCheatConfig = {
  enableScreenDetection: true,
  enableFullscreen: true,
  enableProctor: true,
  maxViolations: 10,
  warningThreshold: 2,
  autoSubmitThreshold: 5,
};

/**
 * 防作弊系统主 Hook
 * 整合切屏检测、全屏模式、抓拍功能
 */
export function useAntiCheat(config: Partial<AntiCheatConfig> = {}) {
  const mergedConfig = { ...defaultConfig, ...config };

  // 子模块
  const screenDetection = useScreenDetection();
  const fullscreen = useFullscreen();
  const proctorCamera = useProctorCamera(mergedConfig.proctorConfig);

  // 状态
  const isActive = ref(false);
  const violations = ref<Violation[]>([]);
  const integrityScore = ref(100);
  const showWarning = ref(false);
  const warningMessage = ref('');

  // 计算属性
  const violationCount = computed(() => violations.value.length);

  const shouldAutoSubmit = computed(() => {
    return violationCount.value >= mergedConfig.autoSubmitThreshold;
  });

  const shouldShowWarning = computed(() => {
    return violationCount.value >= mergedConfig.warningThreshold &&
           violationCount.value < mergedConfig.autoSubmitThreshold;
  });

  // 回调函数
  let onViolationCallback: ((violation: Violation) => void) | null = null;
  let onAutoSubmitCallback: (() => void) | null = null;
  let onWarningCallback: ((count: number, message: string) => void) | null = null;

  /**
   * 设置违规回调
   */
  const onViolation = (callback: (violation: Violation) => void) => {
    onViolationCallback = callback;
  };

  /**
   * 设置自动提交回调
   */
  const onAutoSubmit = (callback: () => void) => {
    onAutoSubmitCallback = callback;
  };

  /**
   * 设置警告回调
   */
  const onWarning = (callback: (count: number, message: string) => void) => {
    onWarningCallback = callback;
  };

  /**
   * 根据违规类型确定严重程度
   */
  const getSeverity = (type: Violation['type']): Violation['severity'] => {
    switch (type) {
      case 'screen_switch':
      case 'tab_change':
        return 'medium';
      case 'window_blur':
        return 'low';
      case 'fullscreen_exit':
        return 'medium';
      case 'face_not_detected':
        return 'high';
      case 'multiple_faces':
        return 'critical';
      default:
        return 'low';
    }
  };

  /**
   * 根据严重程度计算扣分
   */
  const getScoreDeduction = (severity: Violation['severity']): number => {
    switch (severity) {
      case 'low': return 2;
      case 'medium': return 5;
      case 'high': return 15;
      case 'critical': return 30;
      default: return 2;
    }
  };

  /**
   * 记录违规
   */
  const recordViolation = (
    type: Violation['type'],
    details?: Record<string, any>,
    durationMs?: number
  ): Violation => {
    const severity = getSeverity(type);

    // 抓拍（如果启用）
    let snapshotId: string | undefined;
    if (mergedConfig.enableProctor && proctorCamera.isActive.value) {
      const snapshot = proctorCamera.captureOnViolation(`v_${Date.now()}`);
      if (snapshot) {
        snapshotId = snapshot.id;
      }
    }

    const violation: Violation = {
      id: `v_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      severity,
      timestamp: new Date().toISOString(),
      duration_ms: durationMs,
      snapshotId,
      details,
    };

    violations.value.push(violation);

    // 更新诚信分
    const deduction = getScoreDeduction(severity);
    integrityScore.value = Math.max(0, integrityScore.value - deduction);

    // 触发回调
    if (onViolationCallback) {
      onViolationCallback(violation);
    }

    // 检查是否需要警告或自动提交
    checkThresholds();


    return violation;
  };

  /**
   * 检查阈值
   */
  const checkThresholds = () => {
    if (shouldAutoSubmit.value) {
      showWarning.value = false;
      warningMessage.value = '';

      if (onAutoSubmitCallback) {
        onAutoSubmitCallback();
      }
    } else if (shouldShowWarning.value) {
      showWarning.value = true;
      warningMessage.value = `您已有 ${violationCount.value} 次违规行为。再违规 ${mergedConfig.autoSubmitThreshold - violationCount.value} 次将自动提交试卷。`;

      if (onWarningCallback) {
        onWarningCallback(violationCount.value, warningMessage.value);
      }
    }
  };

  /**
   * 关闭警告
   */
  const dismissWarning = () => {
    showWarning.value = false;
    warningMessage.value = '';
  };

  /**
   * 启动防作弊
   */
  const start = async (): Promise<{ success: boolean; errors: string[] }> => {
    const errors: string[] = [];

    if (isActive.value) {
      return { success: true, errors };
    }

    isActive.value = true;
    violations.value = [];
    integrityScore.value = 100;

    // 启动切屏检测
    if (mergedConfig.enableScreenDetection) {
      screenDetection.startMonitoring();

      // 监听切屏违规
      watch(
        () => screenDetection.violationCount.value,
        (newCount, oldCount) => {
          if (newCount > oldCount) {
            const lastViolation = screenDetection.violations.value[screenDetection.violations.value.length - 1];
            if (lastViolation) {
              const type = lastViolation.type === 'visibility_change' ? 'tab_change' : 'window_blur';
              recordViolation(type, { original: lastViolation }, lastViolation.duration_ms);
            }
          }
        }
      );
    }

    // 启动全屏模式
    if (mergedConfig.enableFullscreen) {
      const fullscreenSuccess = await fullscreen.startEnforcing();
      if (!fullscreenSuccess) {
        errors.push('全屏模式启动失败，请确保浏览器支持全屏功能');
      }

      // 监听全屏退出
      fullscreen.onExit(() => {
        recordViolation('fullscreen_exit', { exitCount: fullscreen.exitCount.value });

        // 尝试恢复全屏
        setTimeout(() => {
          fullscreen.tryRestore();
        }, 500);
      });
    }

    // 启动抓拍
    if (mergedConfig.enableProctor) {
      const proctorSuccess = await proctorCamera.start();
      if (!proctorSuccess) {
        errors.push(proctorCamera.errorMessage.value || '摄像头启动失败');
      }
    }


    return { success: errors.length === 0, errors };
  };

  /**
   * 停止防作弊
   */
  const stop = async () => {
    if (!isActive.value) return;

    isActive.value = false;

    // 停止各模块
    if (mergedConfig.enableScreenDetection) {
      screenDetection.stopMonitoring();
    }

    if (mergedConfig.enableFullscreen) {
      await fullscreen.stopEnforcing();
    }

    if (mergedConfig.enableProctor) {
      proctorCamera.stop();
    }

  };

  /**
   * 获取会话数据（用于提交）
   */
  const getSessionData = () => {
    return {
      violations: violations.value,
      violationCount: violationCount.value,
      integrityScore: integrityScore.value,
      snapshots: proctorCamera.snapshots.value.map((s) => ({
        id: s.id,
        timestamp: s.timestamp,
        trigger: s.trigger,
        violationId: s.violationId,
        uploaded: s.uploaded,
        uploadUrl: s.uploadUrl,
      })),
      fullscreenExitCount: fullscreen.exitCount.value,
    };
  };

  /**
   * 重置状态
   */
  const reset = () => {
    violations.value = [];
    integrityScore.value = 100;
    showWarning.value = false;
    warningMessage.value = '';
    screenDetection.clearViolations();
    fullscreen.resetExitCount();
    proctorCamera.clearSnapshots();
  };

  // 组件卸载时清理
  onUnmounted(() => {
    stop();
  });

  return {
    // 状态
    isActive,
    violations,
    violationCount,
    integrityScore,
    showWarning,
    warningMessage,
    shouldAutoSubmit,

    // 子模块暴露
    screenDetection,
    fullscreen,
    proctorCamera,

    // 方法
    start,
    stop,
    recordViolation,
    dismissWarning,
    getSessionData,
    reset,

    // 回调设置
    onViolation,
    onAutoSubmit,
    onWarning,
  };
}
