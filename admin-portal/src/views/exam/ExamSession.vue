<template>
  <div class="exam-session">
    <!-- 考前人脸验证 -->
    <div v-if="sessionState === 'verification'" class="verification-stage">
      <a-card class="verification-card">
        <template #title>
          <SafetyCertificateOutlined /> 身份验证
        </template>

        <div class="verification-content">
          <div class="verification-camera">
            <video
              ref="verifyVideoRef"
              autoplay
              playsinline
              muted
              class="verify-video"
            />
            <div v-if="!cameraReady" class="camera-loading">
              <LoadingOutlined spin />
              <span>正在初始化摄像头...</span>
            </div>
            <div v-if="verificationError" class="camera-error">
              <ExclamationCircleOutlined />
              <span>{{ verificationError }}</span>
            </div>
          </div>

          <div class="verification-instructions">
            <a-alert type="info" show-icon>
              <template #message>
                请确保您的面部清晰可见，光线充足，然后点击"开始验证"
              </template>
            </a-alert>

            <div class="verification-checklist">
              <div class="check-item" :class="{ checked: cameraReady }">
                <CheckCircleOutlined v-if="cameraReady" />
                <CloseCircleOutlined v-else />
                摄像头已就绪
              </div>
              <div class="check-item" :class="{ checked: faceDetected }">
                <CheckCircleOutlined v-if="faceDetected" />
                <CloseCircleOutlined v-else />
                检测到人脸
              </div>
            </div>
          </div>

          <div class="verification-actions">
            <a-button @click="handleCancel">取消</a-button>
            <a-button
              type="primary"
              :loading="verifying"
              :disabled="!cameraReady"
              @click="handleVerification"
            >
              {{ verifying ? '验证中...' : '开始验证' }}
            </a-button>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 考试进行中 -->
    <div v-else-if="sessionState === 'exam'" class="exam-stage">
      <!-- 考试头部 -->
      <div class="exam-header">
        <div class="exam-info">
          <h2>{{ examData?.exam_name }}</h2>
          <div class="exam-meta">
            <a-tag :color="levelColors[examData?.level || 'L0']">
              {{ levelLabels[examData?.level || 'L0'] }}
            </a-tag>
            <a-tag :color="examTypeColors[examData?.exam_type || 'theory']">
              {{ examTypeLabels[examData?.exam_type || 'theory'] }}
            </a-tag>
          </div>
        </div>

        <div class="exam-timer" :class="{ warning: remainingSeconds < 300 }">
          <ClockCircleOutlined />
          <span>{{ formatTime(remainingSeconds) }}</span>
        </div>

        <div class="exam-actions">
          <a-button type="primary" danger @click="confirmSubmit">
            提交试卷
          </a-button>
        </div>
      </div>

      <!-- 考试主体 -->
      <div class="exam-body">
        <!-- 题目区域 -->
        <div class="question-area">
          <div class="question-header">
            <span class="question-number">
              第 {{ currentQuestionIndex + 1 }} / {{ questions.length }} 题
            </span>
            <span class="question-score">
              ({{ currentQuestion?.default_score || 0 }} 分)
            </span>
            <a-tag :color="questionTypeColors[currentQuestion?.type || 'single']">
              {{ questionTypeLabels[currentQuestion?.type || 'single'] }}
            </a-tag>
          </div>

          <div class="question-content">
            <p class="question-text">{{ currentQuestion?.content }}</p>

            <!-- 单选题 -->
            <div v-if="currentQuestion?.type === 'single'" class="question-options">
              <a-radio-group
                v-model:value="currentAnswer"
                class="options-group"
              >
                <a-radio
                  v-for="(option, index) in currentQuestion.options"
                  :key="index"
                  :value="index"
                  class="option-item"
                >
                  <span class="option-letter">{{ String.fromCharCode(65 + index) }}.</span>
                  {{ option }}
                </a-radio>
              </a-radio-group>
            </div>

            <!-- 多选题 -->
            <div v-else-if="currentQuestion?.type === 'multiple'" class="question-options">
              <a-checkbox-group
                v-model:value="currentAnswer"
                class="options-group"
              >
                <a-checkbox
                  v-for="(option, index) in currentQuestion.options"
                  :key="index"
                  :value="index"
                  class="option-item"
                >
                  <span class="option-letter">{{ String.fromCharCode(65 + index) }}.</span>
                  {{ option }}
                </a-checkbox>
              </a-checkbox-group>
            </div>

            <!-- 判断题 -->
            <div v-else-if="currentQuestion?.type === 'truefalse'" class="question-options">
              <a-radio-group
                v-model:value="currentAnswer"
                class="options-group"
              >
                <a-radio :value="true" class="option-item">
                  <CheckOutlined /> 正确
                </a-radio>
                <a-radio :value="false" class="option-item">
                  <CloseOutlined /> 错误
                </a-radio>
              </a-radio-group>
            </div>

            <!-- 简答题 -->
            <div v-else-if="currentQuestion?.type === 'short_answer'" class="question-options">
              <a-textarea
                v-model:value="currentAnswer"
                :rows="6"
                placeholder="请输入您的答案..."
                :maxlength="2000"
                show-count
              />
            </div>
          </div>

          <!-- 题目导航 -->
          <div class="question-navigation">
            <a-button
              :disabled="currentQuestionIndex === 0"
              @click="goToQuestion(currentQuestionIndex - 1)"
            >
              <LeftOutlined /> 上一题
            </a-button>
            <a-button
              v-if="currentQuestionIndex < questions.length - 1"
              type="primary"
              @click="goToQuestion(currentQuestionIndex + 1)"
            >
              下一题 <RightOutlined />
            </a-button>
            <a-button
              v-else
              type="primary"
              @click="confirmSubmit"
            >
              完成考试
            </a-button>
          </div>
        </div>

        <!-- 答题卡 -->
        <div class="answer-card">
          <div class="card-title">答题卡</div>
          <div class="card-grid">
            <div
              v-for="(_, index) in questions"
              :key="index"
              class="card-item"
              :class="{
                current: index === currentQuestionIndex,
                answered: answers[index] !== undefined && answers[index] !== null,
              }"
              @click="goToQuestion(index)"
            >
              {{ index + 1 }}
            </div>
          </div>
          <div class="card-legend">
            <div class="legend-item">
              <span class="legend-dot current"></span>
              <span>当前</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot answered"></span>
              <span>已答</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot"></span>
              <span>未答</span>
            </div>
          </div>
          <div class="card-stats">
            <div>已答: {{ answeredCount }} / {{ questions.length }}</div>
          </div>
        </div>
      </div>

      <!-- 摄像头预览 -->
      <ProctorCamera
        :is-active="antiCheat.isActive.value"
        :has-permission="antiCheat.proctorCamera.hasPermission.value"
        :error-message="antiCheat.proctorCamera.errorMessage.value"
        :snapshot-count="antiCheat.proctorCamera.snapshotCount.value"
        @init="handleCameraInit"
        @retry="handleCameraRetry"
      />

      <!-- 违规警告 -->
      <ViolationWarning
        :visible="antiCheat.showWarning.value"
        :message="antiCheat.warningMessage.value"
        :violation-count="antiCheat.violationCount.value"
        :max-violations="antiCheatConfig.autoSubmitThreshold"
        :integrity-score="antiCheat.integrityScore.value"
        @acknowledge="handleWarningAcknowledge"
      />
    </div>

    <!-- 考试结束 -->
    <div v-else-if="sessionState === 'submitted'" class="submitted-stage">
      <a-result
        :status="submitResult?.status === 'passed' ? 'success' : 'warning'"
        :title="submitResult?.status === 'passed' ? '恭喜您通过考试!' : '很遗憾，未达到及格分数'"
      >
        <template #subTitle>
          <div class="result-summary">
            <div class="result-item">
              <span class="label">得分:</span>
              <span class="value" :class="submitResult?.status">
                {{ submitResult?.score }} / 100
              </span>
            </div>
            <div class="result-item">
              <span class="label">及格分:</span>
              <span class="value">{{ examData?.passing_score }}</span>
            </div>
            <div class="result-item">
              <span class="label">用时:</span>
              <span class="value">{{ formatDuration(submitResult?.duration_seconds || 0) }}</span>
            </div>
            <div class="result-item">
              <span class="label">诚信分:</span>
              <span class="value">{{ submitResult?.integrity_score }}</span>
            </div>
          </div>
        </template>
        <template #extra>
          <a-button type="primary" @click="backToList">
            返回考试列表
          </a-button>
          <a-button v-if="submitResult?.status === 'failed' && examData?.allow_retry" @click="handleRetry">
            重新考试
          </a-button>
        </template>
      </a-result>
    </div>

    <!-- 提交确认弹窗 -->
    <a-modal
      v-model:open="showSubmitConfirm"
      title="确认提交"
      :closable="false"
      :maskClosable="false"
    >
      <div class="submit-confirm-content">
        <p>您确定要提交试卷吗?</p>
        <div class="submit-stats">
          <div>已答题目: {{ answeredCount }} / {{ questions.length }}</div>
          <div v-if="unansweredCount > 0" class="warning-text">
            <WarningOutlined /> 还有 {{ unansweredCount }} 道题未作答
          </div>
          <div>剩余时间: {{ formatTime(remainingSeconds) }}</div>
        </div>
      </div>
      <template #footer>
        <a-button @click="showSubmitConfirm = false">继续答题</a-button>
        <a-button type="primary" :loading="submitting" @click="handleSubmit">
          确认提交
        </a-button>
      </template>
    </a-modal>

    <!-- 断点续考确认弹窗 -->
    <a-modal
      v-model:open="showRestoreConfirm"
      title="发现未完成的考试"
      :closable="false"
      :maskClosable="false"
    >
      <div class="restore-confirm-content">
        <a-alert type="info" show-icon style="margin-bottom: 16px">
          <template #message>
            检测到您有一场未完成的考试，是否继续?
          </template>
        </a-alert>
        <div class="restore-info" v-if="savedSessionInfo">
          <div class="info-row">
            <span class="label">上次答题时间:</span>
            <span class="value">{{ savedSessionInfo.lastSavedAt }}</span>
          </div>
          <div class="info-row">
            <span class="label">已答题目:</span>
            <span class="value">{{ savedSessionInfo.answeredCount }} 道</span>
          </div>
          <div class="info-row">
            <span class="label">剩余时间:</span>
            <span class="value warning">{{ savedSessionInfo.remainingTime }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <a-button @click="handleStartNew">放弃，重新开始</a-button>
        <a-button type="primary" @click="handleRestoreExam">
          <HistoryOutlined /> 继续考试
        </a-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import {
  SafetyCertificateOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  LeftOutlined,
  RightOutlined,
  CheckOutlined,
  CloseOutlined,
  WarningOutlined,
  HistoryOutlined,
} from '@ant-design/icons-vue';
import ProctorCamera from '@/components/exam/ProctorCamera.vue';
import ViolationWarning from '@/components/exam/ViolationWarning.vue';
import { useAntiCheat, type AntiCheatConfig } from '@/composables/useAntiCheat';
import { useExamPersistence } from '@/composables/useExamPersistence';
import type { ExamDefinition, Question, ExamResult } from '@/types/exam';
import {
  levelLabels,
  levelColors,
  examTypeLabels,
  examTypeColors,
  questionTypeLabels,
  questionTypeColors,
} from '@/types/exam';

const route = useRoute();
const router = useRouter();

// 考试状态
type SessionState = 'verification' | 'exam' | 'submitted';
const sessionState = ref<SessionState>('verification');

// 人脸验证相关
const verifyVideoRef = ref<HTMLVideoElement | null>(null);
const cameraReady = ref(false);
const faceDetected = ref(false);
const verifying = ref(false);
const verificationError = ref('');
let verifyStream: MediaStream | null = null;

// 考试数据
const examData = ref<ExamDefinition | null>(null);
const questions = ref<Question[]>([]);
const currentQuestionIndex = ref(0);
const answers = ref<Record<number, any>>({});

// 计时器
const remainingSeconds = ref(0);
let timerInterval: number | null = null;
const startTime = ref<Date | null>(null);

// 提交相关
const showSubmitConfirm = ref(false);
const submitting = ref(false);
const submitResult = ref<ExamResult | null>(null);

// 断点续考相关
const showRestoreConfirm = ref(false);
const savedSessionInfo = ref<{
  lastSavedAt: string;
  answeredCount: number;
  remainingTime: string;
} | null>(null);

// 初始化持久化 (需要在 loadExamData 后获取真实 coachId)
const examId = route.params.id as string;
const coachId = 'current_user'; // 实际应从用户状态获取
const examPersistence = useExamPersistence(examId, coachId);

// 防作弊配置
const antiCheatConfig: AntiCheatConfig = {
  enableScreenDetection: true,
  enableFullscreen: true,
  enableProctor: true,
  maxViolations: 10,
  warningThreshold: 2,
  autoSubmitThreshold: 5,
  proctorConfig: {
    intervalSeconds: 60,
    randomVarianceSeconds: 15,
    quality: 0.7,
  },
};

const antiCheat = useAntiCheat(antiCheatConfig);

// 计算属性
const currentQuestion = computed(() => questions.value[currentQuestionIndex.value]);

const currentAnswer = computed({
  get: () => answers.value[currentQuestionIndex.value],
  set: (value) => {
    answers.value[currentQuestionIndex.value] = value;
  },
});

const answeredCount = computed(() => {
  return Object.values(answers.value).filter((a) => a !== undefined && a !== null).length;
});

const unansweredCount = computed(() => questions.value.length - answeredCount.value);

// 初始化验证摄像头
const initVerificationCamera = async () => {
  try {
    verifyStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      audio: false,
    });

    if (verifyVideoRef.value) {
      verifyVideoRef.value.srcObject = verifyStream;
      await verifyVideoRef.value.play();
      cameraReady.value = true;
      faceDetected.value = true; // 简化处理，实际需接入人脸检测 API
    }
  } catch (error: any) {
    verificationError.value = error.name === 'NotAllowedError'
      ? '摄像头权限被拒绝，请在浏览器设置中允许访问'
      : '摄像头初始化失败';
    console.error('[ExamSession] Camera init error:', error);
  }
};

// 执行人脸验证
const handleVerification = async () => {
  verifying.value = true;

  try {
    // 模拟人脸验证 API 调用
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // 验证成功，停止验证摄像头
    if (verifyStream) {
      verifyStream.getTracks().forEach((track) => track.stop());
      verifyStream = null;
    }

    // 进入考试
    await startExam();
  } catch (error) {
    message.error('人脸验证失败，请重试');
  } finally {
    verifying.value = false;
  }
};

// 开始考试
const startExam = async (isRestore: boolean = false) => {
  // 加载考试数据
  await loadExamData();

  // 如果是恢复考试，应用保存的进度
  if (isRestore) {
    const restored = examPersistence.restoreProgress();
    if (restored) {
      answers.value = restored.answers;
      currentQuestionIndex.value = restored.currentQuestionIndex;
      remainingSeconds.value = restored.remainingSeconds;
      antiCheat.integrityScore.value = restored.integrityScore;
      message.success('已恢复考试进度');
    }
  }

  // 启动防作弊
  const { success, errors } = await antiCheat.start();
  if (!success) {
    errors.forEach((err) => message.warning(err));
  }

  // 设置自动提交回调
  antiCheat.onAutoSubmit(() => {
    message.error('违规次数过多，试卷已自动提交');
    handleSubmit();
  });

  // 启动自动保存
  examPersistence.startAutoSave(() => ({
    remainingSeconds: remainingSeconds.value,
    answers: answers.value,
    currentQuestionIndex: currentQuestionIndex.value,
    violations: antiCheat.violations.value,
    integrityScore: antiCheat.integrityScore.value,
  }));

  // 启动计时器
  startTimer();

  // 切换状态
  sessionState.value = 'exam';
  startTime.value = new Date();
};

// 加载考试数据
const loadExamData = async () => {
  const examId = route.params.id as string;

  // 模拟 API 调用
  examData.value = {
    exam_id: examId,
    exam_name: 'L1 初级教练理论考试',
    level: 'L1',
    exam_type: 'theory',
    passing_score: 70,
    weight_percent: 100,
    duration_minutes: 60,
    questions_count: 10,
    question_ids: [],
    status: 'published',
    max_attempts: 3,
    allow_retry: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    instructions: '请认真阅读每道题目，选择正确答案。',
  };

  // 模拟题目数据
  questions.value = [
    {
      question_id: 'q1',
      content: '教练在与客户建立关系时，最重要的是什么?',
      type: 'single',
      level: 'L1',
      difficulty: 2,
      options: ['严格按照计划执行', '建立信任和共情', '提供专业建议', '设定明确目标'],
      answer: 1,
      use_count: 0,
      default_score: 10,
      status: 'active',
      created_at: '',
      updated_at: '',
    },
    {
      question_id: 'q2',
      content: '以下哪些是有效的倾听技巧?',
      type: 'multiple',
      level: 'L1',
      difficulty: 2,
      options: ['保持眼神接触', '打断对方纠正错误', '适时点头回应', '复述关键内容'],
      answer: [0, 2, 3],
      use_count: 0,
      default_score: 10,
      status: 'active',
      created_at: '',
      updated_at: '',
    },
    {
      question_id: 'q3',
      content: '教练应该直接告诉客户该怎么做，而不是引导客户自己思考。',
      type: 'truefalse',
      level: 'L1',
      difficulty: 1,
      answer: false,
      use_count: 0,
      default_score: 10,
      status: 'active',
      created_at: '',
      updated_at: '',
    },
    {
      question_id: 'q4',
      content: '请简述教练与客户建立信任关系的三个关键要素。',
      type: 'short_answer',
      level: 'L1',
      difficulty: 3,
      use_count: 0,
      default_score: 20,
      status: 'active',
      created_at: '',
      updated_at: '',
    },
    {
      question_id: 'q5',
      content: 'SMART 目标中的 "M" 代表什么?',
      type: 'single',
      level: 'L1',
      difficulty: 1,
      options: ['Motivated (有动力的)', 'Measurable (可衡量的)', 'Meaningful (有意义的)', 'Moderate (适度的)'],
      answer: 1,
      use_count: 0,
      default_score: 10,
      status: 'active',
      created_at: '',
      updated_at: '',
    },
  ];

  remainingSeconds.value = (examData.value.duration_minutes || 60) * 60;
};

// 启动计时器
const startTimer = () => {
  timerInterval = window.setInterval(() => {
    remainingSeconds.value--;

    if (remainingSeconds.value <= 0) {
      clearInterval(timerInterval!);
      message.warning('考试时间已到，试卷将自动提交');
      handleSubmit();
    }
  }, 1000);
};

// 格式化时间
const formatTime = (seconds: number): string => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${m}:${String(s).padStart(2, '0')}`;
};

// 格式化时长
const formatDuration = (seconds: number): string => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m} 分 ${s} 秒`;
};

// 切换题目
const goToQuestion = (index: number) => {
  if (index >= 0 && index < questions.value.length) {
    currentQuestionIndex.value = index;
  }
};

// 摄像头初始化回调
const handleCameraInit = (video: HTMLVideoElement) => {
  antiCheat.proctorCamera.initVideoElement(video);
};

// 摄像头重试
const handleCameraRetry = async () => {
  await antiCheat.proctorCamera.requestPermission();
  if (antiCheat.proctorCamera.hasPermission.value) {
    await antiCheat.proctorCamera.start();
  }
};

// 警告确认
const handleWarningAcknowledge = () => {
  antiCheat.dismissWarning();
};

// 确认提交
const confirmSubmit = () => {
  showSubmitConfirm.value = true;
};

// 提交试卷
const handleSubmit = async () => {
  submitting.value = true;
  showSubmitConfirm.value = false;

  try {
    // 停止计时器
    if (timerInterval) {
      clearInterval(timerInterval);
    }

    // 停止防作弊
    await antiCheat.stop();

    // 计算用时
    const durationSeconds = startTime.value
      ? Math.floor((Date.now() - startTime.value.getTime()) / 1000)
      : 0;

    // 获取防作弊数据
    const sessionData = antiCheat.getSessionData();

    // 模拟提交 API
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // 模拟计算分数
    let score = 0;
    const examAnswers = questions.value.map((q, index) => {
      const userAnswer = answers.value[index];
      const correctAnswer = q.answer;
      let isCorrect = false;

      if (q.type === 'single' || q.type === 'truefalse') {
        isCorrect = userAnswer === correctAnswer;
      } else if (q.type === 'multiple') {
        isCorrect = JSON.stringify(userAnswer?.sort()) === JSON.stringify((correctAnswer as number[])?.sort());
      } else if (q.type === 'short_answer') {
        isCorrect = !!userAnswer; // 简答题需人工评分
      }

      const scoreEarned = isCorrect ? q.default_score : 0;
      score += scoreEarned;

      return {
        question_id: q.question_id,
        user_answer: userAnswer,
        correct_answer: correctAnswer,
        is_correct: isCorrect,
        score_earned: scoreEarned,
        max_score: q.default_score,
      };
    });

    // 构建结果
    submitResult.value = {
      id: `result_${Date.now()}`,
      coach_id: 'current_user',
      exam_id: examData.value?.exam_id || '',
      exam_name: examData.value?.exam_name || '',
      attempt_number: 1,
      score,
      passing_score: examData.value?.passing_score || 70,
      status: score >= (examData.value?.passing_score || 70) ? 'passed' : 'failed',
      answers: examAnswers,
      duration_seconds: durationSeconds,
      started_at: startTime.value?.toISOString() || '',
      submitted_at: new Date().toISOString(),
      violation_count: sessionData.violationCount,
      integrity_score: sessionData.integrityScore,
      review_status: sessionData.violationCount > 0 ? 'flagged' : 'valid',
    };

    // 清除保存的会话
    examPersistence.stopAutoSave();
    examPersistence.clearSavedSession();

    sessionState.value = 'submitted';
    message.success('试卷提交成功');
  } catch (error) {
    message.error('提交失败，请重试');
  } finally {
    submitting.value = false;
  }
};

// 返回列表
const backToList = () => {
  router.push('/exam/list');
};

// 重新考试
const handleRetry = () => {
  // 重置状态
  answers.value = {};
  currentQuestionIndex.value = 0;
  submitResult.value = null;
  sessionState.value = 'verification';

  // 重新初始化摄像头
  initVerificationCamera();
};

// 取消考试
const handleCancel = () => {
  Modal.confirm({
    title: '确认取消',
    content: '确定要取消本次考试吗?',
    onOk: () => {
      if (verifyStream) {
        verifyStream.getTracks().forEach((track) => track.stop());
      }
      router.push('/exam/list');
    },
  });
};

// 恢复考试
const handleRestoreExam = async () => {
  showRestoreConfirm.value = false;

  // 停止验证摄像头
  if (verifyStream) {
    verifyStream.getTracks().forEach((track) => track.stop());
    verifyStream = null;
  }

  // 恢复考试（跳过人脸验证，因为之前已验证过）
  await startExam(true);
};

// 放弃恢复，重新开始
const handleStartNew = () => {
  showRestoreConfirm.value = false;
  examPersistence.clearSavedSession();
  // 继续正常的验证流程
};

// 检查未完成的考试
const checkAndPromptRestore = () => {
  const saved = examPersistence.checkUnfinishedExam();
  if (saved) {
    // 计算剩余时间
    const savedTime = new Date(saved.lastSavedAt).getTime();
    const elapsedSeconds = Math.floor((Date.now() - savedTime) / 1000);
    const adjustedRemaining = Math.max(0, saved.remainingSeconds - elapsedSeconds);

    savedSessionInfo.value = {
      lastSavedAt: new Date(saved.lastSavedAt).toLocaleString('zh-CN'),
      answeredCount: Object.keys(saved.answers).filter(
        (k) => saved.answers[parseInt(k)] !== undefined
      ).length,
      remainingTime: formatTime(adjustedRemaining),
    };

    showRestoreConfirm.value = true;
  }
};

// 生命周期
onMounted(() => {
  // 先检查是否有未完成的考试
  checkAndPromptRestore();

  // 初始化验证摄像头
  initVerificationCamera();
});

onUnmounted(() => {
  // 清理验证摄像头
  if (verifyStream) {
    verifyStream.getTracks().forEach((track) => track.stop());
  }

  // 清理计时器
  if (timerInterval) {
    clearInterval(timerInterval);
  }

  // 停止自动保存
  examPersistence.stopAutoSave();

  // 停止防作弊
  antiCheat.stop();
});
</script>

<style scoped>
.exam-session {
  min-height: 100vh;
  background: #f0f2f5;
}

/* 验证阶段 */
.verification-stage {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 24px;
}

.verification-card {
  width: 100%;
  max-width: 600px;
}

.verification-content {
  text-align: center;
}

.verification-camera {
  width: 320px;
  height: 240px;
  margin: 0 auto 24px;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.verify-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.camera-loading,
.camera-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
}

.camera-error {
  color: #ff4d4f;
}

.verification-instructions {
  margin-bottom: 24px;
}

.verification-checklist {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #999;
}

.check-item.checked {
  color: #52c41a;
}

.verification-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

/* 考试阶段 */
.exam-stage {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.exam-info h2 {
  margin: 0 0 8px;
  font-size: 18px;
}

.exam-meta {
  display: flex;
  gap: 8px;
}

.exam-timer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.exam-timer.warning {
  color: #ff4d4f;
  animation: blink 1s infinite;
}

@keyframes blink {
  50% {
    opacity: 0.5;
  }
}

.exam-body {
  flex: 1;
  display: flex;
  padding: 24px;
  gap: 24px;
  overflow: hidden;
}

.question-area {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.question-number {
  font-size: 16px;
  font-weight: bold;
}

.question-score {
  color: #999;
}

.question-content {
  flex: 1;
}

.question-text {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 24px;
}

.question-options {
  padding-left: 8px;
}

.options-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.option-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.option-item:hover {
  background: #f0f0f0;
}

.option-letter {
  font-weight: bold;
  margin-right: 8px;
  color: #1890ff;
}

.question-navigation {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 答题卡 */
.answer-card {
  width: 240px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  flex-shrink: 0;
}

.card-title {
  font-weight: bold;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}

.card-item {
  width: 36px;
  height: 36px;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.card-item:hover {
  border-color: #1890ff;
}

.card-item.current {
  background: #1890ff;
  border-color: #1890ff;
  color: #fff;
}

.card-item.answered {
  background: #52c41a;
  border-color: #52c41a;
  color: #fff;
}

.card-item.current.answered {
  background: #1890ff;
}

.card-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: #d9d9d9;
}

.legend-dot.current {
  background: #1890ff;
}

.legend-dot.answered {
  background: #52c41a;
}

.card-stats {
  margin-top: 16px;
  font-size: 14px;
  color: #666;
}

/* 提交确认 */
.submit-confirm-content {
  text-align: center;
}

.submit-stats {
  margin-top: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.submit-stats > div {
  margin-bottom: 8px;
}

.warning-text {
  color: #fa8c16;
}

/* 提交结果 */
.submitted-stage {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 24px;
}

.result-summary {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
}

.result-item {
  text-align: center;
}

.result-item .label {
  display: block;
  font-size: 14px;
  color: #999;
  margin-bottom: 4px;
}

.result-item .value {
  font-size: 24px;
  font-weight: bold;
}

.result-item .value.passed {
  color: #52c41a;
}

.result-item .value.failed {
  color: #ff4d4f;
}

/* 断点续考确认 */
.restore-confirm-content {
  padding: 8px 0;
}

.restore-info {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.restore-info .info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.restore-info .info-row:last-child {
  margin-bottom: 0;
}

.restore-info .label {
  color: #666;
}

.restore-info .value {
  font-weight: 500;
}

.restore-info .value.warning {
  color: #fa8c16;
}
</style>
