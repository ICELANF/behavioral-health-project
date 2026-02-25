import { ref, watch } from 'vue';

/**
 * 考试会话持久化数据
 */
export interface ExamSessionData {
  examId: string;
  coachId: string;
  startTime: string;
  remainingSeconds: number;
  answers: Record<number, any>;
  currentQuestionIndex: number;
  violations: any[];
  snapshots: any[];
  integrityScore: number;
  lastSavedAt: string;
}

const STORAGE_KEY = 'exam_session_data';
const AUTO_SAVE_INTERVAL = 10000; // 10秒自动保存

/**
 * 考试断点续考 Hook
 * 自动保存考试进度到 localStorage，支持断点恢复
 */
export function useExamPersistence(examId: string, coachId: string) {
  const hasUnfinishedExam = ref(false);
  const savedSession = ref<ExamSessionData | null>(null);
  let autoSaveTimer: number | null = null;

  /**
   * 生成存储 key
   */
  const getStorageKey = () => `${STORAGE_KEY}_${coachId}_${examId}`;

  /**
   * 检查是否有未完成的考试
   */
  const checkUnfinishedExam = (): ExamSessionData | null => {
    try {
      const key = getStorageKey();
      const data = localStorage.getItem(key);

      if (!data) return null;

      const session: ExamSessionData = JSON.parse(data);

      // 检查是否过期（超过24小时视为过期）
      const savedTime = new Date(session.lastSavedAt).getTime();
      const now = Date.now();
      const hoursDiff = (now - savedTime) / (1000 * 60 * 60);

      if (hoursDiff > 24) {
        clearSavedSession();
        return null;
      }

      // 检查剩余时间
      if (session.remainingSeconds <= 0) {
        clearSavedSession();
        return null;
      }

      hasUnfinishedExam.value = true;
      savedSession.value = session;

      return session;
    } catch (error) {
      console.error('[ExamPersistence] Check error:', error);
      return null;
    }
  };

  /**
   * 保存考试进度
   */
  const saveProgress = (data: Partial<ExamSessionData>) => {
    try {
      const key = getStorageKey();
      const existing = localStorage.getItem(key);
      const current: ExamSessionData = existing
        ? JSON.parse(existing)
        : {
            examId,
            coachId,
            startTime: new Date().toISOString(),
            remainingSeconds: 0,
            answers: {},
            currentQuestionIndex: 0,
            violations: [],
            snapshots: [],
            integrityScore: 100,
            lastSavedAt: '',
          };

      const updated: ExamSessionData = {
        ...current,
        ...data,
        lastSavedAt: new Date().toISOString(),
      };

      localStorage.setItem(key, JSON.stringify(updated));
    } catch (error) {
      console.error('[ExamPersistence] Save error:', error);
    }
  };

  /**
   * 开始自动保存
   */
  const startAutoSave = (getDataFn: () => Partial<ExamSessionData>) => {
    stopAutoSave();

    autoSaveTimer = window.setInterval(() => {
      const data = getDataFn();
      saveProgress(data);
    }, AUTO_SAVE_INTERVAL);

  };

  /**
   * 停止自动保存
   */
  const stopAutoSave = () => {
    if (autoSaveTimer) {
      clearInterval(autoSaveTimer);
      autoSaveTimer = null;
    }
  };

  /**
   * 清除保存的会话
   */
  const clearSavedSession = () => {
    try {
      const key = getStorageKey();
      localStorage.removeItem(key);
      hasUnfinishedExam.value = false;
      savedSession.value = null;
    } catch (error) {
      console.error('[ExamPersistence] Clear error:', error);
    }
  };

  /**
   * 恢复考试进度
   */
  const restoreProgress = (): ExamSessionData | null => {
    if (!savedSession.value) return null;

    // 重新计算剩余时间（扣除离线时间）
    const savedTime = new Date(savedSession.value.lastSavedAt).getTime();
    const now = Date.now();
    const elapsedSeconds = Math.floor((now - savedTime) / 1000);

    const adjustedRemainingSeconds = Math.max(
      0,
      savedSession.value.remainingSeconds - elapsedSeconds
    );

    const restored: ExamSessionData = {
      ...savedSession.value,
      remainingSeconds: adjustedRemainingSeconds,
    };

    return restored;
  };

  /**
   * 获取所有未完成的考试（跨考试查询）
   */
  const getAllUnfinishedExams = (): ExamSessionData[] => {
    const results: ExamSessionData[] = [];

    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(STORAGE_KEY)) {
          const data = localStorage.getItem(key);
          if (data) {
            const session: ExamSessionData = JSON.parse(data);

            // 检查是否过期
            const savedTime = new Date(session.lastSavedAt).getTime();
            const hoursDiff = (Date.now() - savedTime) / (1000 * 60 * 60);

            if (hoursDiff <= 24 && session.remainingSeconds > 0) {
              results.push(session);
            }
          }
        }
      }
    } catch (error) {
      console.error('[ExamPersistence] Get all error:', error);
    }

    return results;
  };

  return {
    hasUnfinishedExam,
    savedSession,
    checkUnfinishedExam,
    saveProgress,
    startAutoSave,
    stopAutoSave,
    clearSavedSession,
    restoreProgress,
    getAllUnfinishedExams,
  };
}
