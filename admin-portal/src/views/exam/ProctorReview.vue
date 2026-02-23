<template>
  <div class="proctor-review">
    <a-page-header title="监考审核" sub-title="审核异常考试记录">
      <template #extra>
        <a-radio-group v-model:value="filterStatus" button-style="solid" @change="handleFilterChange">
          <a-radio-button value="all">全部</a-radio-button>
          <a-radio-button value="flagged">
            待审核 <a-badge :count="flaggedCount" :number-style="{ backgroundColor: '#fa8c16' }" />
          </a-radio-button>
          <a-radio-button value="valid">已通过</a-radio-button>
          <a-radio-button value="invalidated">已作废</a-radio-button>
        </a-radio-group>
      </template>
    </a-page-header>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card>
          <a-statistic title="待审核" :value="flaggedCount">
            <template #prefix>
              <ExclamationCircleOutlined style="color: #fa8c16" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日审核" :value="todayReviewedCount">
            <template #prefix>
              <CheckCircleOutlined style="color: #52c41a" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="平均违规次数" :value="avgViolationCount" :precision="1">
            <template #prefix>
              <WarningOutlined style="color: #ff4d4f" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="作废率" :value="invalidationRate" suffix="%">
            <template #prefix>
              <StopOutlined style="color: #999" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 审核列表 -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <a-empty v-if="sessions.length === 0 && !loading" description="暂无监考记录" />
        <ListCard v-for="record in sessions" :key="record.id" @click="showDetail(record)">
          <template #avatar>
            <a-avatar :size="40">{{ record.coach_name?.charAt(0) }}</a-avatar>
          </template>
          <template #title>
            <span>{{ record.coach_name }}</span>
            <a-tag :color="reviewStatusColors[record.review_status]" size="small" style="margin-left: 8px">{{ reviewStatusLabels[record.review_status] }}</a-tag>
          </template>
          <template #subtitle>
            <span>{{ record.exam_name }}</span>
            <a-tag :color="levelColors[record.level]" size="small" style="margin-left: 6px">{{ levelLabels[record.level] }}</a-tag>
          </template>
          <template #meta>
            <span :class="{ 'score-passed': record.status === 'passed', 'score-failed': record.status === 'failed' }">{{ record.score }} 分</span>
            <a-badge :count="record.violation_count" :number-style="{ backgroundColor: record.violation_count > 3 ? '#ff4d4f' : '#fa8c16' }" />
            <span style="color: #999; font-size: 12px">诚信 {{ record.integrity_score }}%</span>
            <span style="color: #999; font-size: 12px">{{ record.submitted_at }}</span>
          </template>
          <template #actions>
            <a-button size="small" type="link" @click.stop="showDetail(record)">详情</a-button>
            <template v-if="record.review_status === 'flagged'">
              <a-button size="small" type="link" style="color: #52c41a" @click.stop="approveSession(record)">通过</a-button>
              <a-button size="small" type="link" danger @click.stop="invalidateSession(record)">作废</a-button>
            </template>
          </template>
        </ListCard>
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination v-model:current="pagination.current" v-model:pageSize="pagination.pageSize" :total="pagination.total" :show-total="(t: any) => `共 ${t} 条`" @change="onPaginationChange" />
    </div>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="showDetailModal"
      :title="currentSession?.coach_name + ' - ' + currentSession?.exam_name"
      width="900px"
      :footer="null"
    >
      <div v-if="currentSession" class="session-detail">
        <!-- 基本信息 -->
        <a-descriptions :column="3" bordered size="small">
          <a-descriptions-item label="考生">{{ currentSession.coach_name }}</a-descriptions-item>
          <a-descriptions-item label="考试">{{ currentSession.exam_name }}</a-descriptions-item>
          <a-descriptions-item label="等级">
            <a-tag :color="levelColors[currentSession.level]">{{ levelLabels[currentSession.level] }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="得分">{{ currentSession.score }}</a-descriptions-item>
          <a-descriptions-item label="及格分">{{ currentSession.passing_score }}</a-descriptions-item>
          <a-descriptions-item label="结果">
            <a-tag :color="currentSession.status === 'passed' ? 'success' : 'error'">
              {{ currentSession.status === 'passed' ? '通过' : '未通过' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="开始时间">{{ formatDateTime(currentSession.started_at) }}</a-descriptions-item>
          <a-descriptions-item label="提交时间">{{ formatDateTime(currentSession.submitted_at) }}</a-descriptions-item>
          <a-descriptions-item label="用时">{{ formatDuration(currentSession.duration_seconds) }}</a-descriptions-item>
        </a-descriptions>

        <!-- 违规记录 -->
        <div class="section-title">
          <WarningOutlined /> 违规记录 ({{ currentSession.violations?.length || 0 }})
        </div>
        <a-table
          :columns="violationColumns"
          :data-source="currentSession.violations || []"
          :pagination="false"
          size="small"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'type'">
              <a-tag :color="violationTypeColors[record.type]">
                {{ violationTypeLabels[record.type] }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'severity'">
              <a-tag :color="severityColors[record.severity]">
                {{ severityLabels[record.severity] }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'timestamp'">
              {{ formatDateTime(record.timestamp) }}
            </template>
          </template>
        </a-table>

        <!-- 抓拍记录 -->
        <div class="section-title">
          <CameraOutlined /> 抓拍记录 ({{ currentSession.snapshots?.length || 0 }})
        </div>
        <div class="snapshots-grid">
          <div
            v-for="snapshot in currentSession.snapshots"
            :key="snapshot.id"
            class="snapshot-item"
          >
            <img :src="snapshot.dataUrl || '/placeholder-snapshot.jpg'" alt="抓拍" />
            <div class="snapshot-info">
              <a-tag size="small" :color="snapshot.trigger === 'violation' ? 'error' : 'default'">
                {{ snapshotTriggerLabels[snapshot.trigger] }}
              </a-tag>
              <span class="snapshot-time">{{ formatDateTime(snapshot.timestamp) }}</span>
            </div>
          </div>
          <a-empty v-if="!currentSession.snapshots?.length" description="暂无抓拍记录" />
        </div>

        <!-- 审核操作 -->
        <div v-if="currentSession.review_status === 'flagged'" class="review-actions">
          <a-input
            v-model:value="reviewRemark"
            placeholder="审核备注（可选）"
            style="width: 300px; margin-right: 16px"
          />
          <a-button type="primary" @click="approveSession(currentSession)">
            <CheckOutlined /> 审核通过
          </a-button>
          <a-button danger @click="invalidateSession(currentSession)">
            <CloseOutlined /> 作废成绩
          </a-button>
        </div>
        <div v-else class="review-result">
          <a-tag :color="reviewStatusColors[currentSession.review_status]" size="large">
            {{ reviewStatusLabels[currentSession.review_status] }}
          </a-tag>
          <span v-if="currentSession.review_remark" class="review-remark">
            备注: {{ currentSession.review_remark }}
          </span>
        </div>
      </div>
    </a-modal>

    <!-- 作废确认 -->
    <a-modal
      v-model:open="showInvalidateConfirm"
      title="确认作废"
      @ok="confirmInvalidate"
      :confirm-loading="invalidating"
    >
      <p>确定要作废 <strong>{{ sessionToInvalidate?.coach_name }}</strong> 的考试成绩吗?</p>
      <p class="warning-text">此操作不可撤销，该成绩将被标记为无效。</p>
      <a-input
        v-model:value="invalidateReason"
        placeholder="请输入作废原因"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import type { TableColumnsType, TablePaginationConfig } from 'ant-design-vue';
import {
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  StopOutlined,
  EyeOutlined,
  CheckOutlined,
  CloseOutlined,
  CameraOutlined,
} from '@ant-design/icons-vue';
import type { CertificationLevel, ExamResult } from '@/types/exam';
import { levelLabels, levelColors } from '@/types/exam';
import request from '@/api/request';
import ListCard from '@/components/core/ListCard.vue';

interface ProctorSession extends ExamResult {
  coach_name: string;
  level: CertificationLevel;
  violations: Violation[];
  snapshots: Snapshot[];
  review_remark?: string;
}

interface Violation {
  id: string;
  type: string;
  severity: string;
  timestamp: string;
  duration_ms?: number;
}

interface Snapshot {
  id: string;
  dataUrl?: string;
  timestamp: string;
  trigger: 'interval' | 'violation' | 'manual';
}

// 状态
const loading = ref(false);
const sessions = ref<ProctorSession[]>([]);
const filterStatus = ref<'all' | 'flagged' | 'valid' | 'invalidated'>('all');
const showDetailModal = ref(false);
const currentSession = ref<ProctorSession | null>(null);
const reviewRemark = ref('');
const showInvalidateConfirm = ref(false);
const sessionToInvalidate = ref<ProctorSession | null>(null);
const invalidateReason = ref('');
const invalidating = ref(false);

const pagination = ref<TablePaginationConfig>({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: (total) => `共 ${total} 条`,
});

// 统计
const flaggedCount = computed(() => sessions.value.filter((s) => s.review_status === 'flagged').length);
const todayReviewedCount = ref(0);
const avgViolationCount = computed(() => {
  if (sessions.value.length === 0) return 0;
  const total = sessions.value.reduce((sum, s) => sum + s.violation_count, 0);
  return total / sessions.value.length;
});
const invalidationRate = ref(0);

// 常量
const reviewStatusLabels: Record<string, string> = {
  valid: '已通过',
  flagged: '待审核',
  invalidated: '已作废',
};

const reviewStatusColors: Record<string, string> = {
  valid: 'success',
  flagged: 'warning',
  invalidated: 'error',
};

const violationTypeLabels: Record<string, string> = {
  screen_switch: '切屏',
  tab_change: '切换标签',
  window_blur: '窗口失焦',
  fullscreen_exit: '退出全屏',
  face_not_detected: '人脸未检测',
  multiple_faces: '检测到多人',
};

const violationTypeColors: Record<string, string> = {
  screen_switch: 'orange',
  tab_change: 'orange',
  window_blur: 'blue',
  fullscreen_exit: 'orange',
  face_not_detected: 'red',
  multiple_faces: 'red',
};

const severityLabels: Record<string, string> = {
  low: '轻微',
  medium: '一般',
  high: '严重',
  critical: '重大',
};

const severityColors: Record<string, string> = {
  low: 'default',
  medium: 'warning',
  high: 'error',
  critical: 'error',
};

const snapshotTriggerLabels: Record<string, string> = {
  interval: '定时',
  violation: '违规',
  manual: '手动',
};

// main columns removed — using ListCard layout

const violationColumns: TableColumnsType = [
  { title: '类型', key: 'type', dataIndex: 'type', width: 120 },
  { title: '严重程度', key: 'severity', dataIndex: 'severity', width: 100 },
  { title: '时间', key: 'timestamp', dataIndex: 'timestamp', width: 180 },
  { title: '持续时间', key: 'duration', dataIndex: 'duration_ms', width: 100 },
];

// 方法
const fetchSessions = async () => {
  loading.value = true;

  try {
    const params: any = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    if (filterStatus.value !== 'all') {
      params.review_status = filterStatus.value;
    }
    const res = await request.get('/certification/sessions/proctor', { params });
    sessions.value = res.data?.items || res.data?.data || res.data || [];
    pagination.value.total = res.data?.total || sessions.value.length;
  } catch (e) {
    console.error('加载监考记录失败:', e);
  } finally {
    loading.value = false;
  }
};

const handleFilterChange = () => {
  // 根据筛选条件过滤
  fetchSessions();
};

const onPaginationChange = (page: number, pageSize: number) => {
  pagination.value.current = page;
  pagination.value.pageSize = pageSize;
  fetchSessions();
};

const showDetail = (record: ProctorSession) => {
  currentSession.value = record;
  reviewRemark.value = '';
  showDetailModal.value = true;
};

const approveSession = async (session: ProctorSession) => {
  try {
    await request.post(`/certification/sessions/${session.id}/approve`, {
      remark: reviewRemark.value || undefined,
    });

    session.review_status = 'valid';
    session.review_remark = reviewRemark.value || undefined;

    message.success('审核通过');
    showDetailModal.value = false;
  } catch (error) {
    console.error('审核失败:', error);
    message.error('操作失败');
  }
};

const invalidateSession = (session: ProctorSession) => {
  sessionToInvalidate.value = session;
  invalidateReason.value = '';
  showInvalidateConfirm.value = true;
};

const confirmInvalidate = async () => {
  if (!invalidateReason.value) {
    message.warning('请输入作废原因');
    return;
  }

  invalidating.value = true;

  try {
    await request.post(`/certification/sessions/${sessionToInvalidate.value?.id}/invalidate`, {
      reason: invalidateReason.value,
    });

    if (sessionToInvalidate.value) {
      sessionToInvalidate.value.review_status = 'invalidated';
      sessionToInvalidate.value.review_remark = invalidateReason.value;
    }

    message.success('成绩已作废');
    showInvalidateConfirm.value = false;
    showDetailModal.value = false;
  } catch (error) {
    message.error('操作失败');
  } finally {
    invalidating.value = false;
  }
};

const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
};

const formatDuration = (seconds: number): string => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m} 分 ${s} 秒`;
};

// 生命周期
onMounted(() => {
  fetchSessions();
});
</script>

<style scoped>
.proctor-review {
  padding: 24px;
}

.list-card-container { display: flex; flex-direction: column; gap: 10px; }

.stats-row {
  margin-bottom: 24px;
}

.review-table-card {
  margin-top: 24px;
}

.coach-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-passed {
  color: #52c41a;
  font-weight: bold;
}

.score-failed {
  color: #ff4d4f;
  font-weight: bold;
}

.session-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.section-title {
  margin: 24px 0 12px;
  font-weight: bold;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.snapshots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.snapshot-item {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.snapshot-item img {
  width: 100%;
  height: 100px;
  object-fit: cover;
  background: #f5f5f5;
}

.snapshot-info {
  padding: 8px;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.snapshot-time {
  color: #999;
}

.review-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.review-result {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 16px;
}

.review-remark {
  color: #666;
}

.warning-text {
  color: #ff4d4f;
  font-size: 12px;
}
</style>
