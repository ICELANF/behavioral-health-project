<template>
  <div class="exam-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>考试管理</h2>
      <a-button type="primary" @click="handleCreate">
        <template #icon><PlusOutlined /></template>
        创建考试
      </a-button>
    </div>

    <!-- 筛选区域 -->
    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="16">
        <a-col :span="5">
          <a-select
            v-model:value="filters.level"
            placeholder="认证等级"
            allowClear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="L0">L0 观察员</a-select-option>
            <a-select-option value="L1">L1 成长者</a-select-option>
            <a-select-option value="L2">L2 分享者</a-select-option>
            <a-select-option value="L3">L3 教练</a-select-option>
            <a-select-option value="L4">L4 促进师</a-select-option>
            <a-select-option value="L5">L5 大师</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select
            v-model:value="filters.exam_type"
            placeholder="考试类型"
            allowClear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="theory">理论考试</a-select-option>
            <a-select-option value="case_simulation">案例模拟</a-select-option>
            <a-select-option value="dialogue_assessment">对话评估</a-select-option>
            <a-select-option value="specialty">专项考试</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select
            v-model:value="filters.status"
            placeholder="状态"
            allowClear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="archived">已归档</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search
            v-model:value="filters.keyword"
            placeholder="搜索考试名称"
            allowClear
            @search="handleSearch"
          />
        </a-col>
        <a-col :span="3">
          <a-button @click="handleReset">重置</a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 考试表格 -->
    <a-card :bordered="false">
      <a-table
        :dataSource="examList"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        rowKey="exam_id"
        @change="handleTableChange"
      >
        <!-- 考试名称 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'exam_name'">
            <div class="exam-name-cell">
              <a-tag :color="levelColors[record.level as CertificationLevel]">{{ record.level }}</a-tag>
              <span class="exam-name">{{ record.exam_name }}</span>
            </div>
          </template>

          <!-- 考试类型 -->
          <template v-else-if="column.key === 'exam_type'">
            <a-tag :color="examTypeColors[record.exam_type as ExamType]">
              {{ examTypeLabels[record.exam_type as ExamType] }}
            </a-tag>
          </template>

          <!-- 题目数量 -->
          <template v-else-if="column.key === 'questions_count'">
            {{ record.questions_count || record.question_ids?.length || 0 }} 题
          </template>

          <!-- 及格分数 -->
          <template v-else-if="column.key === 'passing_score'">
            {{ record.passing_score }} 分
          </template>

          <!-- 时长 -->
          <template v-else-if="column.key === 'duration_minutes'">
            {{ record.duration_minutes ? `${record.duration_minutes} 分钟` : '不限时' }}
          </template>

          <!-- 状态 -->
          <template v-else-if="column.key === 'status'">
            <a-badge
              :status="statusBadges[record.status] as any"
              :text="statusLabels[record.status]"
            />
          </template>

          <!-- 操作 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
              <a-button type="link" size="small" @click="handleViewResults(record)">成绩</a-button>
              <a-dropdown>
                <a-button type="link" size="small">
                  更多 <DownOutlined />
                </a-button>
                <template #overlay>
                  <a-menu @click="({ key }) => handleMenuClick(key, record)">
                    <a-menu-item v-if="record.status === 'draft'" key="publish">
                      <CheckCircleOutlined /> 发布
                    </a-menu-item>
                    <a-menu-item v-if="record.status === 'published'" key="archive">
                      <StopOutlined /> 下架
                    </a-menu-item>
                    <a-menu-item key="copy">
                      <CopyOutlined /> 复制
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="delete" danger>
                      <DeleteOutlined /> 删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import {
  PlusOutlined,
  DownOutlined,
  CheckCircleOutlined,
  StopOutlined,
  CopyOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';
import { useExamStore } from '../../stores/exam';
import type {
  ExamDefinition,
  CertificationLevel,
  ExamType,
  ExamListParams,
} from '../../types/exam';
import {
  levelColors,
  examTypeLabels,
  examTypeColors,
  statusLabels,
  statusBadges,
} from '../../types/exam';

const router = useRouter();
const examStore = useExamStore();

// 筛选条件
const filters = reactive<ExamListParams>({
  level: undefined,
  exam_type: undefined,
  status: undefined,
  keyword: '',
  page: 1,
  page_size: 10,
});

// 加载状态
const loading = computed(() => examStore.loading);

// 考试列表 (使用模拟数据，后续接入 API)
const examList = computed(() => {
  if (examStore.exams.length > 0) {
    return examStore.exams;
  }
  // 模拟数据
  return mockExams;
});

// 模拟数据
const mockExams: ExamDefinition[] = [
  {
    exam_id: 'exam_l0_theory',
    exam_name: 'L0 行为健康基础理论考试',
    level: 'L0',
    exam_type: 'theory',
    passing_score: 60,
    weight_percent: 100,
    duration_minutes: 60,
    questions_count: 50,
    question_ids: [],
    status: 'published',
    max_attempts: 3,
    allow_retry: true,
    created_at: '2026-01-20T10:00:00Z',
    updated_at: '2026-01-20T10:00:00Z',
  },
  {
    exam_id: 'exam_l1_theory',
    exam_name: 'L1 成长者基础测评',
    level: 'L1',
    exam_type: 'theory',
    passing_score: 70,
    weight_percent: 40,
    duration_minutes: 90,
    questions_count: 80,
    question_ids: [],
    status: 'published',
    max_attempts: 2,
    allow_retry: true,
    created_at: '2026-01-18T10:00:00Z',
    updated_at: '2026-01-18T10:00:00Z',
  },
  {
    exam_id: 'exam_l1_case',
    exam_name: 'L1 案例分析模拟',
    level: 'L1',
    exam_type: 'case_simulation',
    passing_score: 70,
    weight_percent: 30,
    duration_minutes: 45,
    questions_count: 5,
    question_ids: [],
    status: 'draft',
    max_attempts: 2,
    allow_retry: true,
    created_at: '2026-01-22T10:00:00Z',
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    exam_id: 'exam_l2_dialogue',
    exam_name: 'L2 教练对话能力评估',
    level: 'L2',
    exam_type: 'dialogue_assessment',
    passing_score: 75,
    weight_percent: 40,
    duration_minutes: 60,
    questions_count: 10,
    question_ids: [],
    status: 'published',
    max_attempts: 2,
    allow_retry: true,
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-01-15T10:00:00Z',
  },
  {
    exam_id: 'exam_l3_diabetes',
    exam_name: 'L3 糖尿病逆转专项考核',
    level: 'L3',
    exam_type: 'specialty',
    passing_score: 80,
    weight_percent: 50,
    duration_minutes: 120,
    questions_count: 60,
    specialty: 'diabetes_reversal',
    question_ids: [],
    status: 'draft',
    max_attempts: 2,
    allow_retry: true,
    created_at: '2026-01-24T10:00:00Z',
    updated_at: '2026-01-24T10:00:00Z',
  },
];

// 分页配置
const pagination = computed(() => ({
  current: filters.page,
  pageSize: filters.page_size,
  total: examStore.total || mockExams.length,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`,
}));

// 表格列定义
const columns = [
  {
    title: '考试名称',
    key: 'exam_name',
    width: 280,
  },
  {
    title: '类型',
    key: 'exam_type',
    width: 120,
  },
  {
    title: '题目数',
    key: 'questions_count',
    width: 80,
    align: 'center' as const,
  },
  {
    title: '及格分',
    key: 'passing_score',
    width: 80,
    align: 'center' as const,
  },
  {
    title: '时长',
    key: 'duration_minutes',
    width: 100,
    align: 'center' as const,
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
  },
  {
    title: '操作',
    key: 'action',
    width: 180,
    fixed: 'right' as const,
  },
];

// 搜索
const handleSearch = () => {
  filters.page = 1;
  examStore.fetchExams(filters);
};

// 重置
const handleReset = () => {
  filters.level = undefined;
  filters.exam_type = undefined;
  filters.status = undefined;
  filters.keyword = '';
  filters.page = 1;
  examStore.fetchExams(filters);
};

// 表格变化
const handleTableChange = (pag: any) => {
  filters.page = pag.current;
  filters.page_size = pag.pageSize;
  examStore.fetchExams(filters);
};

// 创建考试
const handleCreate = () => {
  router.push('/exam/create');
};

// 编辑考试
const handleEdit = (record: ExamDefinition) => {
  router.push(`/exam/edit/${record.exam_id}`);
};

// 查看成绩
const handleViewResults = (record: ExamDefinition) => {
  router.push(`/exam/results/${record.exam_id}`);
};

// 菜单点击
const handleMenuClick = async (key: string, record: ExamDefinition) => {
  switch (key) {
    case 'publish':
      await handlePublish(record);
      break;
    case 'archive':
      await handleArchive(record);
      break;
    case 'copy':
      handleCopy(record);
      break;
    case 'delete':
      handleDelete(record);
      break;
  }
};

// 发布考试
const handlePublish = async (record: ExamDefinition) => {
  try {
    await examStore.publishExam(record.exam_id);
    message.success('考试已发布');
  } catch (error) {
    message.error('发布失败');
  }
};

// 下架考试
const handleArchive = async (record: ExamDefinition) => {
  Modal.confirm({
    title: '确认下架',
    content: `确定要下架考试"${record.exam_name}"吗？下架后学员将无法参加此考试。`,
    okText: '确认下架',
    cancelText: '取消',
    onOk: async () => {
      try {
        await examStore.archiveExam(record.exam_id);
        message.success('考试已下架');
      } catch (error) {
        message.error('下架失败');
      }
    },
  });
};

// 复制考试 → 跳转创建页并带源 ID
const handleCopy = (record: ExamDefinition) => {
  router.push({ path: '/exam/create', query: { copyFrom: String(record.id) } })
};

// 删除考试
const handleDelete = (record: ExamDefinition) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除考试"${record.exam_name}"吗？此操作不可恢复。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await examStore.deleteExam(record.exam_id);
        message.success('删除成功');
      } catch (error) {
        message.error('删除失败');
      }
    },
  });
};

// 页面加载
onMounted(() => {
  examStore.fetchExams(filters);
});
</script>

<style scoped>
.exam-list {
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

.filter-card {
  margin-bottom: 16px;
}

.exam-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.exam-name {
  font-weight: 500;
}
</style>
