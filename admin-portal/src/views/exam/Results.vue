<template>
  <div class="exam-results">
    <!-- 面包屑导航 -->
    <a-breadcrumb style="margin-bottom: 16px">
      <a-breadcrumb-item><router-link to="/exam/list">考试管理</router-link></a-breadcrumb-item>
      <a-breadcrumb-item>成绩管理</a-breadcrumb-item>
    </a-breadcrumb>

    <!-- 页面标题 -->
    <div class="page-header">
      <h2>{{ examInfo.exam_name || '考试成绩' }}</h2>
      <a-button @click="handleExport">
        <template #icon><DownloadOutlined /></template>
        导出成绩
      </a-button>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="考试人次"
            :value="statistics.totalAttempts"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix><TeamOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="及格率"
            :value="statistics.passRate"
            suffix="%"
            :value-style="{ color: statistics.passRate >= 60 ? '#52c41a' : '#ff4d4f' }"
          >
            <template #prefix><CheckCircleOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="平均分"
            :value="statistics.averageScore"
            :precision="1"
            suffix="分"
            :value-style="{ color: '#722ed1' }"
          >
            <template #prefix><LineChartOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="最高分/最低分"
            :value="`${statistics.highestScore}/${statistics.lowestScore}`"
            :value-style="{ color: '#fa8c16' }"
          >
            <template #prefix><TrophyOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选和表格 -->
    <a-card :bordered="false">
      <!-- 筛选区域 -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="5">
          <a-select
            v-model:value="filters.passed"
            placeholder="通过状态"
            allowClear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option :value="true">已通过</a-select-option>
            <a-select-option :value="false">未通过</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="8">
          <a-range-picker
            v-model:value="dateRange"
            style="width: 100%"
            @change="handleDateChange"
          />
        </a-col>
        <a-col :span="6">
          <a-input-search
            v-model:value="filters.keyword"
            placeholder="搜索考生姓名"
            allowClear
            @search="handleSearch"
          />
        </a-col>
        <a-col :span="5">
          <a-button @click="handleReset">重置</a-button>
        </a-col>
      </a-row>

      <!-- 成绩表格 -->
      <a-table
        :dataSource="resultList"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        rowKey="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <!-- 考生姓名 -->
          <template v-if="column.key === 'user_name'">
            <span>{{ record.user_name || record.coach_id }}</span>
          </template>

          <!-- 得分 -->
          <template v-else-if="column.key === 'score'">
            <span :style="{ color: record.status === 'passed' ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }">
              {{ record.score }} 分
            </span>
          </template>

          <!-- 状态 -->
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.status === 'passed' ? 'success' : 'error'">
              {{ record.status === 'passed' ? '通过' : '未通过' }}
            </a-tag>
          </template>

          <!-- 用时 -->
          <template v-else-if="column.key === 'duration'">
            {{ formatDuration(record.duration_seconds) }}
          </template>

          <!-- 提交时间 -->
          <template v-else-if="column.key === 'submitted_at'">
            {{ formatDate(record.submitted_at) }}
          </template>

          <!-- 诚信分 -->
          <template v-else-if="column.key === 'integrity_score'">
            <a-progress
              :percent="record.integrity_score"
              :size="50"
              type="circle"
              :status="record.integrity_score >= 80 ? 'success' : record.integrity_score >= 60 ? 'normal' : 'exception'"
            />
          </template>

          <!-- 操作 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleViewDetail(record)">
                查看详情
              </a-button>
              <a-button
                v-if="record.review_status === 'flagged'"
                type="link"
                size="small"
                danger
                @click="handleInvalidate(record)"
              >
                作废
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 成绩详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      title="成绩详情"
      width="800px"
      :footer="null"
    >
      <template v-if="currentResult">
        <!-- 基本信息 -->
        <a-descriptions :column="3" bordered size="small" style="margin-bottom: 16px">
          <a-descriptions-item label="考生">{{ currentResult.user_name || currentResult.coach_id }}</a-descriptions-item>
          <a-descriptions-item label="得分">
            <span :style="{ color: currentResult.status === 'passed' ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }">
              {{ currentResult.score }} / {{ currentResult.passing_score }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="currentResult.status === 'passed' ? 'success' : 'error'">
              {{ currentResult.status === 'passed' ? '通过' : '未通过' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="用时">{{ formatDuration(currentResult.duration_seconds) }}</a-descriptions-item>
          <a-descriptions-item label="尝试次数">第 {{ currentResult.attempt_number }} 次</a-descriptions-item>
          <a-descriptions-item label="提交时间">{{ formatDate(currentResult.submitted_at) }}</a-descriptions-item>
          <a-descriptions-item label="诚信分" :span="3">
            <a-progress
              :percent="currentResult.integrity_score"
              :status="currentResult.integrity_score >= 80 ? 'success' : currentResult.integrity_score >= 60 ? 'normal' : 'exception'"
            />
            <span v-if="currentResult.violation_count > 0" style="color: #ff4d4f; margin-left: 8px">
              (违规 {{ currentResult.violation_count }} 次)
            </span>
          </a-descriptions-item>
        </a-descriptions>

        <!-- 答题详情 -->
        <h4 style="margin-bottom: 12px">答题详情</h4>
        <a-table
          :dataSource="currentResult.answers"
          :columns="answerColumns"
          :pagination="false"
          size="small"
          rowKey="question_id"
        >
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.key === 'index'">
              {{ index + 1 }}
            </template>
            <template v-else-if="column.key === 'user_answer'">
              {{ formatAnswer(record.user_answer) }}
            </template>
            <template v-else-if="column.key === 'correct_answer'">
              {{ formatAnswer(record.correct_answer) }}
            </template>
            <template v-else-if="column.key === 'is_correct'">
              <CheckCircleOutlined v-if="record.is_correct" style="color: #52c41a; font-size: 16px" />
              <CloseCircleOutlined v-else style="color: #ff4d4f; font-size: 16px" />
            </template>
            <template v-else-if="column.key === 'score'">
              {{ record.score_earned }} / {{ record.max_score }}
            </template>
          </template>
        </a-table>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import {
  DownloadOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LineChartOutlined,
  TrophyOutlined,
} from '@ant-design/icons-vue';
import { useExamStore } from '../../stores/exam';
import { resultApi } from '../../api/result';
import type { ExamResult, ExamStatistics, ResultListParams } from '../../types/exam';
import dayjs from 'dayjs';

const route = useRoute();
const examStore = useExamStore();

// 考试ID
const examId = computed(() => route.params.examId as string);

// 加载状态
const loading = ref(false);

// 考试信息
const examInfo = ref<{ exam_name: string }>({ exam_name: '' });

// 统计数据
const statistics = ref<ExamStatistics>({
  exam_id: '',
  totalAttempts: 0,
  passCount: 0,
  failCount: 0,
  passRate: 0,
  averageScore: 0,
  highestScore: 0,
  lowestScore: 0,
});

// 筛选条件
const filters = reactive<ResultListParams>({
  exam_id: '',
  passed: undefined,
  date_from: undefined,
  date_to: undefined,
  keyword: '',
  page: 1,
  page_size: 10,
});

// 日期范围
const dateRange = ref<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

// 成绩列表 (使用模拟数据)
const resultList = ref<ExamResult[]>([]);

// 模拟成绩数据
const mockResults: ExamResult[] = [
  {
    id: 'r1',
    coach_id: 'coach_001',
    exam_id: 'exam_l1_theory',
    exam_name: 'L1 初级教练理论考核',
    attempt_number: 1,
    score: 85,
    passing_score: 70,
    status: 'passed',
    answers: [
      { question_id: 'q1', user_answer: 2, correct_answer: 2, is_correct: true, score_earned: 2, max_score: 2 },
      { question_id: 'q2', user_answer: [0, 1, 2], correct_answer: [0, 1, 2], is_correct: true, score_earned: 4, max_score: 4 },
      { question_id: 'q3', user_answer: true, correct_answer: true, is_correct: true, score_earned: 1, max_score: 1 },
      { question_id: 'q4', user_answer: 0, correct_answer: 1, is_correct: false, score_earned: 0, max_score: 2 },
    ],
    duration_seconds: 2850,
    started_at: '2026-01-24T09:00:00Z',
    submitted_at: '2026-01-24T09:47:30Z',
    violation_count: 0,
    integrity_score: 100,
    review_status: 'valid',
  },
  {
    id: 'r2',
    coach_id: 'coach_002',
    exam_id: 'exam_l1_theory',
    exam_name: 'L1 初级教练理论考核',
    attempt_number: 1,
    score: 62,
    passing_score: 70,
    status: 'failed',
    answers: [
      { question_id: 'q1', user_answer: 1, correct_answer: 2, is_correct: false, score_earned: 0, max_score: 2 },
      { question_id: 'q2', user_answer: [0, 1], correct_answer: [0, 1, 2], is_correct: false, score_earned: 2, max_score: 4 },
      { question_id: 'q3', user_answer: false, correct_answer: true, is_correct: false, score_earned: 0, max_score: 1 },
      { question_id: 'q4', user_answer: 1, correct_answer: 1, is_correct: true, score_earned: 2, max_score: 2 },
    ],
    duration_seconds: 3600,
    started_at: '2026-01-24T10:00:00Z',
    submitted_at: '2026-01-24T11:00:00Z',
    violation_count: 2,
    integrity_score: 85,
    review_status: 'flagged',
  },
  {
    id: 'r3',
    coach_id: 'coach_003',
    exam_id: 'exam_l1_theory',
    exam_name: 'L1 初级教练理论考核',
    attempt_number: 2,
    score: 78,
    passing_score: 70,
    status: 'passed',
    answers: [
      { question_id: 'q1', user_answer: 2, correct_answer: 2, is_correct: true, score_earned: 2, max_score: 2 },
      { question_id: 'q2', user_answer: [0, 1, 2], correct_answer: [0, 1, 2], is_correct: true, score_earned: 4, max_score: 4 },
      { question_id: 'q3', user_answer: true, correct_answer: true, is_correct: true, score_earned: 1, max_score: 1 },
      { question_id: 'q4', user_answer: 1, correct_answer: 1, is_correct: true, score_earned: 2, max_score: 2 },
    ],
    duration_seconds: 2400,
    started_at: '2026-01-23T14:00:00Z',
    submitted_at: '2026-01-23T14:40:00Z',
    violation_count: 0,
    integrity_score: 100,
    review_status: 'valid',
  },
];

// 分页配置
const pagination = computed(() => ({
  current: filters.page,
  pageSize: filters.page_size,
  total: resultList.value.length,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`,
}));

// 表格列定义
const columns = [
  { title: '考生', key: 'user_name', width: 150 },
  { title: '得分', key: 'score', width: 100, align: 'center' as const },
  { title: '状态', key: 'status', width: 100, align: 'center' as const },
  { title: '用时', key: 'duration', width: 100, align: 'center' as const },
  { title: '提交时间', key: 'submitted_at', width: 180 },
  { title: '诚信分', key: 'integrity_score', width: 100, align: 'center' as const },
  { title: '操作', key: 'action', width: 150 },
];

// 答题详情列定义
const answerColumns = [
  { title: '题号', key: 'index', width: 60, align: 'center' as const },
  { title: '用户答案', key: 'user_answer', width: 150 },
  { title: '正确答案', key: 'correct_answer', width: 150 },
  { title: '正误', key: 'is_correct', width: 60, align: 'center' as const },
  { title: '得分', key: 'score', width: 80, align: 'center' as const },
];

// 详情弹窗
const detailVisible = ref(false);
const currentResult = ref<ExamResult | null>(null);

// 格式化时长
const formatDuration = (seconds: number) => {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}分${secs}秒`;
};

// 格式化日期
const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss');
};

// 格式化答案
const formatAnswer = (answer: any) => {
  if (Array.isArray(answer)) {
    return answer.map((a) => String.fromCharCode(65 + a)).join(', ');
  }
  if (typeof answer === 'boolean') {
    return answer ? '正确' : '错误';
  }
  if (typeof answer === 'number') {
    return String.fromCharCode(65 + answer);
  }
  return String(answer);
};

// 搜索
const handleSearch = () => {
  filters.page = 1;
  loadResults();
};

// 日期变化
const handleDateChange = (dates: [dayjs.Dayjs, dayjs.Dayjs] | null) => {
  if (dates) {
    filters.date_from = dates[0].format('YYYY-MM-DD');
    filters.date_to = dates[1].format('YYYY-MM-DD');
  } else {
    filters.date_from = undefined;
    filters.date_to = undefined;
  }
  handleSearch();
};

// 重置
const handleReset = () => {
  filters.passed = undefined;
  filters.date_from = undefined;
  filters.date_to = undefined;
  filters.keyword = '';
  filters.page = 1;
  dateRange.value = null;
  loadResults();
};

// 表格变化
const handleTableChange = (pag: any) => {
  filters.page = pag.current;
  filters.page_size = pag.pageSize;
  loadResults();
};

// 查看详情
const handleViewDetail = (record: ExamResult) => {
  currentResult.value = record;
  detailVisible.value = true;
};

// 作废成绩
const handleInvalidate = (record: ExamResult) => {
  Modal.confirm({
    title: '确认作废',
    content: '确定要作废该成绩吗？此操作不可恢复。',
    okText: '确认作废',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await resultApi.invalidate(record.id, '管理员手动作废');
        message.success('成绩已作废');
        loadResults();
      } catch (error) {
        message.error('操作失败');
      }
    },
  });
};

// 导出成绩
const handleExport = async () => {
  try {
    message.loading({ content: '正在导出...', key: 'export' });
    await resultApi.export(examId.value, 'csv');
    message.success({ content: '导出成功', key: 'export' });
  } catch (error) {
    message.error({ content: '导出失败', key: 'export' });
  }
};

// 加载成绩列表
const loadResults = async () => {
  loading.value = true;
  try {
    filters.exam_id = examId.value;
    // 使用模拟数据
    resultList.value = mockResults;

    // 计算统计数据
    const total = mockResults.length;
    const passCount = mockResults.filter((r) => r.status === 'passed').length;
    const scores = mockResults.map((r) => r.score);

    statistics.value = {
      exam_id: examId.value,
      totalAttempts: total,
      passCount,
      failCount: total - passCount,
      passRate: total > 0 ? Math.round((passCount / total) * 100) : 0,
      averageScore: total > 0 ? Math.round((scores.reduce((a, b) => a + b, 0) / total) * 10) / 10 : 0,
      highestScore: total > 0 ? Math.max(...scores) : 0,
      lowestScore: total > 0 ? Math.min(...scores) : 0,
    };

    // 尝试从API加载
    // const response = await resultApi.list(filters);
    // resultList.value = response.data.data || [];
  } finally {
    loading.value = false;
  }
};

// 加载考试信息
const loadExamInfo = async () => {
  const exam = await examStore.fetchExam(examId.value);
  if (exam) {
    examInfo.value = { exam_name: exam.exam_name };
  }
};

// 页面加载
onMounted(() => {
  loadExamInfo();
  loadResults();
});
</script>

<style scoped>
.exam-results {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
}
</style>
