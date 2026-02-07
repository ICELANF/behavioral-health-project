<template>
  <div class="exam-edit">
    <!-- 面包屑导航 -->
    <a-breadcrumb style="margin-bottom: 16px">
      <a-breadcrumb-item><router-link to="/exam/list">考试管理</router-link></a-breadcrumb-item>
      <a-breadcrumb-item>{{ isEdit ? '编辑考试' : '创建考试' }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-spin :spinning="loading">
      <a-row :gutter="16">
        <!-- 左侧：基本信息 + 题目管理 -->
        <a-col :span="16">
          <!-- 基本信息 -->
          <a-card title="基本信息" :bordered="false" style="margin-bottom: 16px">
            <a-form
              :model="formState"
              :rules="formRules"
              ref="formRef"
              layout="vertical"
            >
              <a-form-item label="考试名称" name="exam_name">
                <a-input v-model:value="formState.exam_name" placeholder="请输入考试名称" />
              </a-form-item>

              <a-form-item label="考试描述" name="description">
                <a-textarea
                  v-model:value="formState.description"
                  placeholder="请输入考试描述和说明"
                  :rows="3"
                />
              </a-form-item>

              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="认证等级" name="level">
                    <a-select v-model:value="formState.level" placeholder="选择等级">
                      <a-select-option value="L0">L0 观察员</a-select-option>
                      <a-select-option value="L1">L1 成长者</a-select-option>
                      <a-select-option value="L2">L2 分享者</a-select-option>
                      <a-select-option value="L3">L3 教练</a-select-option>
                      <a-select-option value="L4">L4 促进师</a-select-option>
                      <a-select-option value="L5">L5 大师</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="考试类型" name="exam_type">
                    <a-select v-model:value="formState.exam_type" placeholder="选择类型">
                      <a-select-option value="theory">理论考试</a-select-option>
                      <a-select-option value="case_simulation">案例模拟</a-select-option>
                      <a-select-option value="dialogue_assessment">对话评估</a-select-option>
                      <a-select-option value="specialty">专项考试</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item
                    v-if="formState.exam_type === 'specialty'"
                    label="专项方向"
                    name="specialty"
                  >
                    <a-select v-model:value="formState.specialty" placeholder="选择专项">
                      <a-select-option value="diabetes_reversal">糖尿病逆转</a-select-option>
                      <a-select-option value="hypertension">高血压</a-select-option>
                      <a-select-option value="weight_management">体重管理</a-select-option>
                      <a-select-option value="stress_psychology">心理压力</a-select-option>
                      <a-select-option value="metabolic_syndrome">代谢综合征</a-select-option>
                      <a-select-option value="sleep_optimization">睡眠优化</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>

              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="考试时长(分钟)" name="duration_minutes">
                    <a-input-number
                      v-model:value="formState.duration_minutes"
                      :min="0"
                      :max="300"
                      style="width: 100%"
                      placeholder="0表示不限时"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="及格分数" name="passing_score">
                    <a-input-number
                      v-model:value="formState.passing_score"
                      :min="0"
                      :max="100"
                      style="width: 100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="总分权重(%)" name="weight_percent">
                    <a-input-number
                      v-model:value="formState.weight_percent"
                      :min="0"
                      :max="100"
                      style="width: 100%"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
            </a-form>
          </a-card>

          <!-- 题目管理 -->
          <a-card :bordered="false">
            <template #title>
              <div class="question-header">
                <span>已选题目 ({{ selectedQuestions.length }} 题)</span>
                <a-button type="primary" @click="openQuestionPicker">
                  <template #icon><PlusOutlined /></template>
                  从题库选择
                </a-button>
              </div>
            </template>

            <a-table
              v-if="selectedQuestions.length > 0"
              :dataSource="selectedQuestions"
              :columns="questionColumns"
              :pagination="false"
              rowKey="question_id"
              size="small"
            >
              <template #bodyCell="{ column, record, index }">
                <template v-if="column.key === 'index'">
                  {{ index + 1 }}
                </template>
                <template v-else-if="column.key === 'content'">
                  <span class="question-content">{{ truncate(record.content, 50) }}</span>
                </template>
                <template v-else-if="column.key === 'type'">
                  <a-tag :color="questionTypeColors[record.type as QuestionType]">
                    {{ questionTypeLabels[record.type as QuestionType] }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'difficulty'">
                  <a-rate :value="record.difficulty" disabled :count="5" />
                </template>
                <template v-else-if="column.key === 'score'">
                  <a-input-number
                    v-model:value="record.score"
                    :min="0"
                    :max="100"
                    size="small"
                    style="width: 70px"
                  />
                </template>
                <template v-else-if="column.key === 'action'">
                  <a-button type="link" danger size="small" @click="removeQuestion(index)">
                    移除
                  </a-button>
                </template>
              </template>
            </a-table>

            <a-empty v-else description="暂无题目，请从题库选择">
              <a-button type="primary" @click="openQuestionPicker">从题库选择</a-button>
            </a-empty>
          </a-card>
        </a-col>

        <!-- 右侧：设置 -->
        <a-col :span="8">
          <a-card title="考试设置" :bordered="false" style="margin-bottom: 16px">
            <a-form layout="vertical">
              <a-form-item label="考试状态">
                <a-radio-group v-model:value="formState.status">
                  <a-radio value="draft">草稿</a-radio>
                  <a-radio value="published">发布</a-radio>
                </a-radio-group>
              </a-form-item>

              <a-form-item label="允许重考">
                <a-switch v-model:checked="formState.allow_retry" />
              </a-form-item>

              <a-form-item v-if="formState.allow_retry" label="最大尝试次数">
                <a-input-number
                  v-model:value="formState.max_attempts"
                  :min="1"
                  :max="10"
                  style="width: 100%"
                />
              </a-form-item>

              <a-form-item label="考试说明">
                <a-textarea
                  v-model:value="formState.instructions"
                  placeholder="考试前显示的说明文字"
                  :rows="4"
                />
              </a-form-item>
            </a-form>
          </a-card>

          <!-- 操作按钮 -->
          <a-card :bordered="false">
            <a-space direction="vertical" style="width: 100%">
              <a-button type="primary" block @click="handleSave" :loading="saving">
                保存
              </a-button>
              <a-button block @click="handleCancel">取消</a-button>
            </a-space>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>

    <!-- 题目选择器弹窗 -->
    <a-modal
      v-model:open="questionPickerVisible"
      title="从题库选择题目"
      width="900px"
      :footer="null"
      @cancel="closeQuestionPicker"
    >
      <!-- 筛选 -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="6">
          <a-select
            v-model:value="pickerFilters.type"
            placeholder="题目类型"
            allowClear
            style="width: 100%"
            @change="loadQuestions"
          >
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multiple">多选题</a-select-option>
            <a-select-option value="truefalse">判断题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="pickerFilters.level"
            placeholder="认证等级"
            allowClear
            style="width: 100%"
            @change="loadQuestions"
          >
            <a-select-option value="L0">L0</a-select-option>
            <a-select-option value="L1">L1</a-select-option>
            <a-select-option value="L2">L2</a-select-option>
            <a-select-option value="L3">L3</a-select-option>
            <a-select-option value="L4">L4</a-select-option>
            <a-select-option value="L5">L5</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="pickerFilters.difficulty"
            placeholder="难度"
            allowClear
            style="width: 100%"
            @change="loadQuestions"
          >
            <a-select-option :value="1">1星</a-select-option>
            <a-select-option :value="2">2星</a-select-option>
            <a-select-option :value="3">3星</a-select-option>
            <a-select-option :value="4">4星</a-select-option>
            <a-select-option :value="5">5星</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search
            v-model:value="pickerFilters.keyword"
            placeholder="搜索题目"
            @search="loadQuestions"
          />
        </a-col>
      </a-row>

      <!-- 题目列表 -->
      <a-table
        :dataSource="availableQuestions"
        :columns="pickerColumns"
        :loading="questionStore.loading"
        :row-selection="rowSelection"
        rowKey="question_id"
        size="small"
        :scroll="{ y: 400 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'content'">
            <span class="question-content">{{ truncate(record.content, 60) }}</span>
          </template>
          <template v-else-if="column.key === 'type'">
            <a-tag :color="questionTypeColors[record.type as QuestionType]" size="small">
              {{ questionTypeLabels[record.type as QuestionType] }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'level'">
            <a-tag :color="levelColors[record.level as CertificationLevel]" size="small">
              {{ record.level }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'difficulty'">
            <a-rate :value="record.difficulty" disabled :count="5" style="font-size: 12px" />
          </template>
          <template v-else-if="column.key === 'selected'">
            <a-tag v-if="isQuestionSelected(record.question_id)" color="green">已选</a-tag>
          </template>
        </template>
      </a-table>

      <!-- 底部操作 -->
      <div style="margin-top: 16px; text-align: right">
        <span style="margin-right: 16px">已选择 {{ tempSelectedKeys.length }} 题</span>
        <a-space>
          <a-button @click="closeQuestionPicker">取消</a-button>
          <a-button type="primary" @click="confirmQuestionSelection">确认添加</a-button>
        </a-space>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';
import { useExamStore } from '../../stores/exam';
import { useQuestionStore } from '../../stores/question';
import type {
  ExamDefinition,
  Question,
  CertificationLevel,
  QuestionType,
  QuestionListParams,
} from '../../types/exam';
import {
  levelColors,
  questionTypeLabels,
  questionTypeColors,
} from '../../types/exam';

const router = useRouter();
const route = useRoute();
const examStore = useExamStore();
const questionStore = useQuestionStore();

// 是否编辑模式
const isEdit = computed(() => !!route.params.id);
const examId = computed(() => route.params.id as string);

// 加载状态
const loading = ref(false);
const saving = ref(false);

// 表单引用
const formRef = ref();

// 表单数据
const formState = reactive<Partial<ExamDefinition>>({
  exam_name: '',
  description: '',
  level: 'L1',
  exam_type: 'theory',
  specialty: undefined,
  passing_score: 60,
  weight_percent: 100,
  duration_minutes: 60,
  status: 'draft',
  max_attempts: 2,
  allow_retry: true,
  instructions: '',
  question_ids: [],
});

// 表单验证规则
const formRules = {
  exam_name: [{ required: true, message: '请输入考试名称' }],
  level: [{ required: true, message: '请选择认证等级' }],
  exam_type: [{ required: true, message: '请选择考试类型' }],
  passing_score: [{ required: true, message: '请输入及格分数' }],
};

// 已选题目 (带分数)
interface SelectedQuestion extends Question {
  score: number;
}
const selectedQuestions = ref<SelectedQuestion[]>([]);

// 题目表格列
const questionColumns = [
  { title: '序号', key: 'index', width: 60, align: 'center' as const },
  { title: '题目内容', key: 'content', ellipsis: true },
  { title: '类型', key: 'type', width: 80 },
  { title: '难度', key: 'difficulty', width: 120 },
  { title: '分值', key: 'score', width: 80 },
  { title: '操作', key: 'action', width: 80 },
];

// 题目选择器
const questionPickerVisible = ref(false);
const pickerFilters = reactive<QuestionListParams>({
  type: undefined,
  level: undefined,
  difficulty: undefined,
  keyword: '',
});
const tempSelectedKeys = ref<string[]>([]);

// 可用题目列表
const availableQuestions = computed(() => {
  if (questionStore.questions.length > 0) {
    return questionStore.questions;
  }
  // 模拟数据
  return mockQuestions;
});

// 模拟题目数据
const mockQuestions: Question[] = [
  {
    question_id: 'q1',
    content: '行为改变的五阶段模型（跨理论模型）中，"准备阶段"的主要特征是什么？',
    type: 'single',
    level: 'L1',
    difficulty: 3,
    options: ['完全没有改变意愿', '开始考虑改变', '已制定行动计划', '已开始行动'],
    answer: 2,
    explanation: '准备阶段的特征是个体已经打算在近期采取行动...',
    tags: ['行为科学', 'TTM模型'],
    use_count: 45,
    default_score: 2,
    status: 'active',
    created_at: '2026-01-20T10:00:00Z',
    updated_at: '2026-01-20T10:00:00Z',
  },
  {
    question_id: 'q2',
    content: '关于动机访谈（MI）技术，以下哪些是其核心原则？（多选）',
    type: 'multiple',
    level: 'L1',
    difficulty: 4,
    options: ['表达共情', '发展矛盾', '支持自我效能', '直接指导'],
    answer: [0, 1, 2],
    explanation: '动机访谈的核心原则包括表达共情、发展矛盾、支持自我效能...',
    tags: ['动机访谈', 'MI'],
    use_count: 38,
    default_score: 4,
    status: 'active',
    created_at: '2026-01-19T10:00:00Z',
    updated_at: '2026-01-19T10:00:00Z',
  },
  {
    question_id: 'q3',
    content: '糖尿病前期的空腹血糖标准是 6.1-7.0 mmol/L',
    type: 'truefalse',
    level: 'L2',
    difficulty: 2,
    answer: true,
    explanation: '根据WHO标准，空腹血糖6.1-7.0mmol/L为糖耐量受损...',
    tags: ['糖尿病', '诊断标准'],
    use_count: 52,
    default_score: 1,
    status: 'active',
    created_at: '2026-01-18T10:00:00Z',
    updated_at: '2026-01-18T10:00:00Z',
  },
  {
    question_id: 'q4',
    content: 'COM-B行为改变模型中的"M"代表什么？',
    type: 'single',
    level: 'L1',
    difficulty: 2,
    options: ['能力(Capability)', '动机(Motivation)', '管理(Management)', '方法(Method)'],
    answer: 1,
    explanation: 'COM-B模型中M代表Motivation（动机）...',
    tags: ['行为科学', 'COM-B'],
    use_count: 67,
    default_score: 2,
    status: 'active',
    created_at: '2026-01-17T10:00:00Z',
    updated_at: '2026-01-17T10:00:00Z',
  },
  {
    question_id: 'q5',
    content: '在教练对话中遇到用户表达抗拒时，最佳的处理方式是？',
    type: 'single',
    level: 'L2',
    difficulty: 4,
    options: ['直接指出问题', '给出具体建议', '倾听并共情', '转换话题'],
    answer: 2,
    explanation: '面对抗拒，首先应该倾听并表达共情...',
    tags: ['教练技能', '阻抗处理'],
    use_count: 29,
    default_score: 3,
    status: 'active',
    created_at: '2026-01-16T10:00:00Z',
    updated_at: '2026-01-16T10:00:00Z',
  },
];

// 选择器表格列
const pickerColumns = [
  { title: '题目内容', key: 'content', ellipsis: true },
  { title: '类型', key: 'type', width: 80 },
  { title: '等级', key: 'level', width: 60 },
  { title: '难度', key: 'difficulty', width: 100 },
  { title: '', key: 'selected', width: 60 },
];

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: tempSelectedKeys.value,
  onChange: (keys: string[]) => {
    tempSelectedKeys.value = keys;
  },
  getCheckboxProps: (record: Question) => ({
    disabled: isQuestionSelected(record.question_id),
  }),
}));

// 判断题目是否已选
const isQuestionSelected = (questionId: string) => {
  return selectedQuestions.value.some((q) => q.question_id === questionId);
};

// 截断文本
const truncate = (text: string, length: number) => {
  if (!text) return '';
  return text.length > length ? text.slice(0, length) + '...' : text;
};

// 打开题目选择器
const openQuestionPicker = () => {
  tempSelectedKeys.value = [];
  questionPickerVisible.value = true;
  loadQuestions();
};

// 关闭题目选择器
const closeQuestionPicker = () => {
  questionPickerVisible.value = false;
  tempSelectedKeys.value = [];
};

// 加载题库
const loadQuestions = () => {
  questionStore.fetchQuestions(pickerFilters);
};

// 确认选择题目
const confirmQuestionSelection = () => {
  const newQuestions = availableQuestions.value
    .filter((q) => tempSelectedKeys.value.includes(q.question_id))
    .map((q) => ({
      ...q,
      score: q.default_score || 1,
    }));

  selectedQuestions.value = [...selectedQuestions.value, ...newQuestions];
  closeQuestionPicker();
  message.success(`已添加 ${newQuestions.length} 道题目`);
};

// 移除题目
const removeQuestion = (index: number) => {
  selectedQuestions.value.splice(index, 1);
};

// 保存考试
const handleSave = async () => {
  try {
    await formRef.value?.validate();

    if (selectedQuestions.value.length === 0) {
      message.warning('请至少选择一道题目');
      return;
    }

    saving.value = true;

    const examData: Partial<ExamDefinition> = {
      ...formState,
      question_ids: selectedQuestions.value.map((q) => q.question_id),
      questions_count: selectedQuestions.value.length,
    };

    if (isEdit.value) {
      await examStore.updateExam(examId.value, examData);
      message.success('考试已更新');
    } else {
      await examStore.createExam(examData);
      message.success('考试已创建');
    }

    router.push('/exam/list');
  } catch (error) {
    console.error('Save failed:', error);
  } finally {
    saving.value = false;
  }
};

// 取消
const handleCancel = () => {
  router.push('/exam/list');
};

// 加载考试数据
const loadExam = async () => {
  if (!isEdit.value) return;

  loading.value = true;
  try {
    const exam = await examStore.fetchExam(examId.value);
    if (exam) {
      Object.assign(formState, exam);
      // 加载已选题目
      if (exam.question_ids && exam.question_ids.length > 0) {
        // TODO: 从API加载题目详情
        selectedQuestions.value = mockQuestions
          .filter((q) => exam.question_ids.includes(q.question_id))
          .map((q) => ({ ...q, score: q.default_score || 1 }));
      }
    }
  } finally {
    loading.value = false;
  }
};

// 页面加载
onMounted(() => {
  loadExam();
});
</script>

<style scoped>
.exam-edit {
  padding: 0;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-content {
  color: #333;
}
</style>
