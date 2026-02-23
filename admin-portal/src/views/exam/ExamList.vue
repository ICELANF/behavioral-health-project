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

    <!-- 考试列表 -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <a-empty v-if="examList.length === 0 && !loading" description="暂无考试" />
        <ListCard v-for="record in examList" :key="record.exam_id" @click="handleEdit(record)">
          <template #title>
            <a-tag :color="levelColors[record.level as CertificationLevel]" size="small">{{ record.level }}</a-tag>
            <span class="exam-name" style="margin-left: 6px">{{ record.exam_name }}</span>
          </template>
          <template #subtitle>
            <a-tag :color="examTypeColors[record.exam_type as ExamType]" size="small">
              {{ examTypeLabels[record.exam_type as ExamType] }}
            </a-tag>
            <a-badge
              :status="statusBadges[record.status] as any"
              :text="statusLabels[record.status]"
              style="margin-left: 8px"
            />
          </template>
          <template #meta>
            <span>{{ record.questions_count || record.question_ids?.length || 0 }} 题</span>
            <span>及格 {{ record.passing_score }} 分</span>
            <span>{{ record.duration_minutes ? `${record.duration_minutes} 分钟` : '不限时' }}</span>
          </template>
          <template #actions>
            <a-button type="link" size="small" @click.stop="handleEdit(record)">编辑</a-button>
            <a-button type="link" size="small" @click.stop="handleViewResults(record)">成绩</a-button>
            <a-dropdown>
              <a-button type="link" size="small" @click.stop>
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
          </template>
        </ListCard>
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination
        v-model:current="filters.page"
        v-model:pageSize="filters.page_size"
        :total="examStore.total || examStore.exams.length"
        show-size-changer
        show-quick-jumper
        :show-total="(total: number) => `共 ${total} 条`"
        @change="onPaginationChange"
      />
    </div>
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
import ListCard from '@/components/core/ListCard.vue';

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

// 考试列表
const examList = computed(() => examStore.exams);

// pagination computed removed — now using direct a-pagination

// columns removed — now using ListCard layout

// 分页变化
const onPaginationChange = (page: number, pageSize: number) => {
  filters.page = page;
  filters.page_size = pageSize;
  examStore.fetchExams(filters);
};

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

.list-card-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.exam-name {
  font-weight: 500;
}
</style>
