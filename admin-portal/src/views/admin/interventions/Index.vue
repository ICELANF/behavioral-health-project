<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import {
  Card,
  Table,
  Button,
  Select,
  Space,
  Tag,
  Divider,
  Drawer,
  Descriptions,
  DescriptionsItem,
  Tabs,
  TabPane,
  Timeline,
  TimelineItem,
  Alert,
  Row,
  Col,
  Statistic,
  Modal,
  List,
  ListItem,
  ListItemMeta,
  Tooltip,
  Badge,
  message
} from 'ant-design-vue'
import {
  ExperimentOutlined,
  ThunderboltOutlined,
  BookOutlined,
  UserOutlined,
  BulbOutlined,
  HeartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  StarOutlined
} from '@ant-design/icons-vue'
import BehaviorStageTag from '@/components/BehaviorStageTag.vue'
import RiskLevelTag from '@/components/RiskLevelTag.vue'
import TriggerDomainTag from '@/components/TriggerDomainTag.vue'
import CoachLevelBadge from '@/components/CoachLevelBadge.vue'
import {
  getAllInterventionPacks,
  matchInterventionPack,
  TRIGGER_TAGS,
  TASK_CATEGORY_MAP,
  ACTION_CATEGORY_MAP,
  type MatchResult
} from '@/api/interventions'
import { TTM_STAGES, COACH_LEVELS } from '@/constants'
import type { InterventionPack, TTMStage, CoachLevel } from '@/types'

// 匹配测试条件
const matchTest = reactive({
  trigger_tag: undefined as string | undefined,
  behavior_stage: undefined as TTMStage | undefined,
  coach_level: 'L1' as CoachLevel  // 默认 L1 初级教练
})

// 数据
const dataSource = ref<InterventionPack[]>(getAllInterventionPacks())
const matchResults = ref<MatchResult[]>([])
const matchedPackIds = ref<Set<string>>(new Set())
const executablePackIds = ref<Set<string>>(new Set())
const loading = ref(false)
const isMatchMode = ref(false)

// 详情抽屉
const drawerVisible = ref(false)
const selectedPack = ref<InterventionPack | null>(null)
const activeTabKey = ref('tasks')

// CoachAction 推荐弹窗
const actionModalVisible = ref(false)
const currentMatchResult = ref<MatchResult | null>(null)

// 表格列定义
const columns = [
  {
    title: '编号',
    dataIndex: 'pack_id',
    key: 'pack_id',
    width: 100
  },
  {
    title: '干预包名称',
    dataIndex: 'name',
    key: 'name',
    width: 180
  },
  {
    title: '关联触发标签',
    dataIndex: 'trigger_tags',
    key: 'trigger_tags',
    width: 200
  },
  {
    title: '适用行为阶段',
    dataIndex: 'applicable_stages',
    key: 'applicable_stages',
    width: 280
  },
  {
    title: '最低教练等级',
    dataIndex: 'coach_level_min',
    key: 'coach_level_min',
    width: 130
  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    width: 80,
    sorter: (a: InterventionPack, b: InterventionPack) => a.priority - b.priority
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    key: 'is_active',
    width: 80
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    fixed: 'right' as const
  }
]

// 获取触发标签显示名称
const getTriggerTagLabel = (tag: string) => {
  const found = TRIGGER_TAGS.find(t => t.tag === tag)
  return found?.label || tag
}

// 获取任务类别标签
const getTaskCategoryTag = (category: string) => {
  const config = TASK_CATEGORY_MAP[category as keyof typeof TASK_CATEGORY_MAP]
  return config || { label: category, color: '#666' }
}

// 获取教练动作类别标签
const getActionCategoryTag = (category: string) => {
  const config = ACTION_CATEGORY_MAP[category as keyof typeof ACTION_CATEGORY_MAP]
  return config || { label: category, color: '#666' }
}

// 执行匹配测试
const handleMatchTest = () => {
  if (!matchTest.trigger_tag) {
    message.warning('请选择触发标签')
    return
  }
  if (!matchTest.behavior_stage) {
    message.warning('请选择行为阶段')
    return
  }

  // 调用匹配函数
  const results = matchInterventionPack(
    matchTest.trigger_tag,
    matchTest.behavior_stage,
    matchTest.coach_level
  )

  matchResults.value = results
  matchedPackIds.value = new Set(results.map(r => r.pack.pack_id))
  executablePackIds.value = new Set(results.filter(r => r.canExecute).map(r => r.pack.pack_id))
  isMatchMode.value = true

  if (results.length > 0) {
    const execCount = results.filter(r => r.canExecute).length
    message.success('匹配到 ' + results.length + ' 个干预包，其中 ' + execCount + ' 个可执行')

    // 自动弹出第一个可执行干预包的推荐动作
    const firstExecutable = results.find(r => r.canExecute)
    if (firstExecutable && firstExecutable.matchedActions.length > 0) {
      currentMatchResult.value = firstExecutable
      actionModalVisible.value = true
    }
  } else {
    message.warning('未找到匹配的干预包')
  }
}

// 重置匹配测试
const handleResetMatch = () => {
  matchTest.trigger_tag = undefined
  matchTest.behavior_stage = undefined
  matchResults.value = []
  matchedPackIds.value.clear()
  executablePackIds.value.clear()
  isMatchMode.value = false
}

// 判断行样式
const getRowClassName = (record: InterventionPack) => {
  if (!isMatchMode.value) return ''

  if (executablePackIds.value.has(record.pack_id)) {
    return 'matched-row executable-row'
  }
  if (matchedPackIds.value.has(record.pack_id)) {
    return 'matched-row not-executable-row'
  }
  return ''
}

// 查看推荐动作
const handleViewActions = (record: InterventionPack) => {
  const result = matchResults.value.find(r => r.pack.pack_id === record.pack_id)
  if (result) {
    currentMatchResult.value = result
    actionModalVisible.value = true
  }
}

// 查看详情
const handleViewDetail = (record: InterventionPack) => {
  selectedPack.value = record
  activeTabKey.value = 'tasks'
  drawerVisible.value = true
}

// 统计信息
const stats = computed(() => {
  const total = dataSource.value.length
  const active = dataSource.value.filter(p => p.is_active).length
  const matched = matchedPackIds.value.size
  const executable = executablePackIds.value.size
  return { total, active, matched, executable }
})

// 获取匹配结果
const getMatchResult = (packId: string) => {
  return matchResults.value.find(r => r.pack.pack_id === packId)
}
</script>

<template>
  <div class="interventions-page">
    <!-- 模拟匹配区域 -->
    <Card class="match-test-card" :bordered="false">
      <template #title>
        <Space>
          <ExperimentOutlined style="color: #1890ff" />
          <span>匹配测试</span>
          <Tooltip title="根据触发标签、行为阶段和教练等级匹配适合的干预包">
            <InfoCircleOutlined style="color: #999" />
          </Tooltip>
        </Space>
      </template>
      <template #extra>
        <Space v-if="isMatchMode">
          <Badge :count="stats.executable" :number-style="{ backgroundColor: '#52c41a' }">
            <Tag color="success">可执行</Tag>
          </Badge>
          <Badge :count="stats.matched - stats.executable" :number-style="{ backgroundColor: '#faad14' }">
            <Tag color="warning">等级不足</Tag>
          </Badge>
        </Space>
      </template>

      <Row :gutter="16" align="middle">
        <Col :span="6">
          <div class="match-field">
            <label class="field-label">
              <span class="required">*</span> 触发标签
            </label>
            <Select
              v-model:value="matchTest.trigger_tag"
              placeholder="选择触发标签"
              style="width: 100%"
              allow-clear
              show-search
              :filter-option="(input: string, option: any) => option.label?.toLowerCase().includes(input.toLowerCase())"
            >
              <a-select-option
                v-for="tag in TRIGGER_TAGS"
                :key="tag.tag"
                :value="tag.tag"
                :label="tag.label"
              >
                <Space>
                  <TriggerDomainTag :domain="tag.domain" />
                  {{ tag.label }}
                </Space>
              </a-select-option>
            </Select>
          </div>
        </Col>

        <Col :span="5">
          <div class="match-field">
            <label class="field-label">
              <span class="required">*</span> 行为阶段
            </label>
            <Select
              v-model:value="matchTest.behavior_stage"
              placeholder="选择行为阶段"
              style="width: 100%"
              allow-clear
            >
              <a-select-option
                v-for="(config, key) in TTM_STAGES"
                :key="key"
                :value="key"
              >
                <Space>
                  <span :style="{ color: config.color, fontWeight: 'bold' }">{{ config.order }}</span>
                  {{ config.label }}
                </Space>
              </a-select-option>
            </Select>
          </div>
        </Col>

        <Col :span="5">
          <div class="match-field">
            <label class="field-label">当前教练等级</label>
            <Select
              v-model:value="matchTest.coach_level"
              placeholder="选择教练等级"
              style="width: 100%"
            >
              <a-select-option
                v-for="(config, key) in COACH_LEVELS"
                :key="key"
                :value="key"
              >
                <Space>
                  <Tag :color="config.color">{{ key }}</Tag>
                  {{ config.label }}
                </Space>
              </a-select-option>
            </Select>
          </div>
        </Col>

        <Col :span="5">
          <Space style="margin-top: 22px">
            <Button
              type="primary"
              size="large"
              @click="handleMatchTest"
              :disabled="!matchTest.trigger_tag || !matchTest.behavior_stage"
            >
              <template #icon><ThunderboltOutlined /></template>
              执行匹配
            </Button>
            <Button @click="handleResetMatch" :disabled="!isMatchMode">
              清除
            </Button>
          </Space>
        </Col>

        <Col :span="3">
          <Statistic
            title="匹配结果"
            :value="isMatchMode ? stats.matched : '-'"
            :value-style="{ color: isMatchMode && stats.matched > 0 ? '#1890ff' : '#999' }"
            suffix="个"
          />
        </Col>
      </Row>

      <!-- 匹配提示 -->
      <Alert
        v-if="isMatchMode && stats.matched > 0"
        style="margin-top: 16px"
        type="info"
        show-icon
      >
        <template #message>
          <Space>
            <span>匹配到 <strong>{{ stats.matched }}</strong> 个干预包</span>
            <Divider type="vertical" />
            <span>
              <CheckCircleOutlined style="color: #52c41a" />
              <strong>{{ stats.executable }}</strong> 个可执行（{{ matchTest.coach_level }} 等级）
            </span>
            <span v-if="stats.matched > stats.executable">
              <CloseCircleOutlined style="color: #faad14" />
              <strong>{{ stats.matched - stats.executable }}</strong> 个需更高等级
            </span>
          </Space>
        </template>
        <template #description>
          点击表格中的「查看推荐」按钮，可查看该干预包推荐的教练动作
        </template>
      </Alert>
    </Card>

    <!-- 干预包列表 -->
    <Card title="干预包列表" :bordered="false" style="margin-top: 16px">
      <template #extra>
        <Space>
          <span style="color: #666">共 {{ stats.total }} 个干预包</span>
        </Space>
      </template>

      <!-- 图例说明 -->
      <div v-if="isMatchMode" class="legend-bar">
        <Space>
          <span class="legend-item">
            <span class="legend-color executable"></span>
            可执行（绿色高亮）
          </span>
          <span class="legend-item">
            <span class="legend-color not-executable"></span>
            等级不足（黄色高亮）
          </span>
          <span class="legend-item">
            <span class="legend-color normal"></span>
            未匹配
          </span>
        </Space>
      </div>

      <!-- 数据表格 -->
      <Table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :pagination="{ pageSize: 10, showSizeChanger: true, showTotal: (total: number) => '共 ' + total + ' 条' }"
        :scroll="{ x: 1200 }"
        :row-class-name="(record: InterventionPack) => getRowClassName(record)"
        row-key="pack_id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'pack_id'">
            <Space>
              <Tag :color="executablePackIds.has(record.pack_id) ? 'green' : matchedPackIds.has(record.pack_id) ? 'orange' : 'default'">
                {{ record.pack_id }}
              </Tag>
              <StarOutlined v-if="executablePackIds.has(record.pack_id)" style="color: #52c41a" />
            </Space>
          </template>

          <template v-else-if="column.key === 'name'">
            <div class="pack-name-cell">
              <span class="pack-name">{{ record.name }}</span>
              <TriggerDomainTag :domain="record.trigger_domain" style="margin-left: 8px" />
            </div>
          </template>

          <template v-else-if="column.key === 'trigger_tags'">
            <Space wrap>
              <Tag
                v-for="tag in record.trigger_tags"
                :key="tag"
                :color="matchTest.trigger_tag === tag ? 'green' : 'purple'"
              >
                {{ getTriggerTagLabel(tag) }}
              </Tag>
            </Space>
          </template>

          <template v-else-if="column.key === 'applicable_stages'">
            <Space wrap>
              <BehaviorStageTag
                v-for="stage in record.applicable_stages"
                :key="stage"
                :stage="stage"
              />
            </Space>
          </template>

          <template v-else-if="column.key === 'coach_level_min'">
            <CoachLevelBadge :level="record.coach_level_min" :show-description="true" />
          </template>

          <template v-else-if="column.key === 'is_active'">
            <Tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? '启用' : '停用' }}
            </Tag>
          </template>

          <template v-else-if="column.key === 'action'">
            <Space>
              <Button
                v-if="matchedPackIds.has(record.pack_id)"
                type="primary"
                size="small"
                ghost
                @click="handleViewActions(record as InterventionPack)"
              >
                <template #icon><BulbOutlined /></template>
                查看推荐
              </Button>
              <Button type="link" size="small" @click="handleViewDetail(record as InterventionPack)">
                详情
              </Button>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- CoachAction 推荐弹窗 -->
    <Modal
      v-model:open="actionModalVisible"
      :title="currentMatchResult?.pack.name + ' - 推荐教练动作'"
      width="700px"
      :footer="null"
    >
      <template v-if="currentMatchResult">
        <!-- 状态提示 -->
        <Alert
          :type="currentMatchResult.canExecute ? 'success' : 'warning'"
          show-icon
          style="margin-bottom: 16px"
        >
          <template #message>
            <span v-if="currentMatchResult.canExecute">
              <CheckCircleOutlined /> 当前等级（{{ matchTest.coach_level }}）可执行此干预包
            </span>
            <span v-else>
              <CloseCircleOutlined /> {{ currentMatchResult.reason }}
            </span>
          </template>
        </Alert>

        <!-- 匹配信息 -->
        <Descriptions :column="2" size="small" bordered style="margin-bottom: 16px">
          <DescriptionsItem label="触发标签">
            <Tag color="purple">{{ getTriggerTagLabel(matchTest.trigger_tag || '') }}</Tag>
          </DescriptionsItem>
          <DescriptionsItem label="行为阶段">
            <BehaviorStageTag :stage="matchTest.behavior_stage!" />
          </DescriptionsItem>
          <DescriptionsItem label="最低要求等级">
            <CoachLevelBadge :level="currentMatchResult.pack.coach_level_min" />
          </DescriptionsItem>
          <DescriptionsItem label="干预包优先级">
            <Tag color="blue">P{{ currentMatchResult.pack.priority }}</Tag>
          </DescriptionsItem>
        </Descriptions>

        <Divider>
          <Space>
            <UserOutlined />
            推荐教练动作（{{ currentMatchResult.matchedActions.length }}）
          </Space>
        </Divider>

        <!-- 推荐动作列表 -->
        <List
          :data-source="currentMatchResult.matchedActions"
          :bordered="false"
        >
          <template #renderItem="{ item: action }">
            <Card size="small" class="action-recommend-card">
              <template #title>
                <Space>
                  <Tag :color="getActionCategoryTag(action.category).color">
                    {{ getActionCategoryTag(action.category).label }}
                  </Tag>
                  <span style="font-weight: 500">{{ action.title }}</span>
                </Space>
              </template>
              <template #extra>
                <CoachLevelBadge :level="action.required_level" />
              </template>

              <p style="color: #666; margin-bottom: 12px">{{ action.description }}</p>

              <!-- 参考话术 -->
              <div v-if="action.script" class="script-box">
                <div class="script-header">
                  <BookOutlined /> 参考话术
                </div>
                <div class="script-text">"{{ action.script }}"</div>
              </div>

              <!-- 教练提示 -->
              <div v-if="action.tips?.length" class="tips-box">
                <div class="tips-header">
                  <HeartOutlined /> 教练提示
                </div>
                <ul class="tips-list">
                  <li v-for="(tip, idx) in action.tips" :key="idx">{{ tip }}</li>
                </ul>
              </div>
            </Card>
          </template>
        </List>

        <div v-if="currentMatchResult.matchedActions.length === 0" style="text-align: center; padding: 40px; color: #999">
          该行为阶段暂无专属推荐动作
        </div>
      </template>
    </Modal>

    <!-- 详情抽屉 -->
    <Drawer
      v-model:open="drawerVisible"
      :title="selectedPack?.name"
      width="700"
      placement="right"
    >
      <template v-if="selectedPack">
        <!-- 基本信息 -->
        <Descriptions :column="2" bordered size="small">
          <DescriptionsItem label="编号">
            <Tag color="blue">{{ selectedPack.pack_id }}</Tag>
          </DescriptionsItem>
          <DescriptionsItem label="优先级">
            <Tag color="orange">P{{ selectedPack.priority }}</Tag>
          </DescriptionsItem>
          <DescriptionsItem label="触发域" :span="2">
            <TriggerDomainTag :domain="selectedPack.trigger_domain" :show-icon="true" />
          </DescriptionsItem>
          <DescriptionsItem label="描述" :span="2">
            {{ selectedPack.description }}
          </DescriptionsItem>
          <DescriptionsItem label="触发标签" :span="2">
            <Space wrap>
              <Tag v-for="tag in selectedPack.trigger_tags" :key="tag" color="purple">
                {{ getTriggerTagLabel(tag) }}
              </Tag>
            </Space>
          </DescriptionsItem>
          <DescriptionsItem label="适用阶段" :span="2">
            <Space wrap>
              <BehaviorStageTag
                v-for="stage in selectedPack.applicable_stages"
                :key="stage"
                :stage="stage"
                :show-tooltip="true"
              />
            </Space>
          </DescriptionsItem>
          <DescriptionsItem label="风险等级">
            <Space wrap>
              <RiskLevelTag
                v-for="level in selectedPack.risk_levels"
                :key="level"
                :level="level"
              />
            </Space>
          </DescriptionsItem>
          <DescriptionsItem label="最低教练等级">
            <CoachLevelBadge :level="selectedPack.coach_level_min" :show-description="true" />
          </DescriptionsItem>
        </Descriptions>

        <Divider />

        <!-- 任务与教练动作 -->
        <Tabs v-model:activeKey="activeTabKey">
          <TabPane key="tasks">
            <template #tab>
              <Space>
                <BulbOutlined />
                干预任务 ({{ selectedPack.tasks.length }})
              </Space>
            </template>

            <div class="task-list">
              <Card
                v-for="task in selectedPack.tasks"
                :key="task.task_id"
                size="small"
                class="task-card"
              >
                <template #title>
                  <Space>
                    <Tag :color="getTaskCategoryTag(task.category).color">
                      {{ getTaskCategoryTag(task.category).label }}
                    </Tag>
                    <span>{{ task.title }}</span>
                  </Space>
                </template>
                <template #extra>
                  <Tag>优先级 {{ task.priority }}</Tag>
                </template>

                <p class="task-desc">{{ task.description }}</p>

                <div class="task-meta">
                  <Space wrap>
                    <span v-if="task.duration_minutes">
                      <Tag color="cyan">{{ task.duration_minutes }} 分钟</Tag>
                    </span>
                    <span v-if="task.behavior_stage?.length">
                      适用阶段:
                      <BehaviorStageTag
                        v-for="stage in task.behavior_stage"
                        :key="stage"
                        :stage="stage"
                      />
                    </span>
                  </Space>
                </div>

                <div v-if="task.resources?.length" class="task-resources">
                  <Divider style="margin: 12px 0" />
                  <span style="color: #666">相关资源: </span>
                  <Tag v-for="res in task.resources" :key="res" color="geekblue">
                    {{ res }}
                  </Tag>
                </div>
              </Card>
            </div>
          </TabPane>

          <TabPane key="actions">
            <template #tab>
              <Space>
                <UserOutlined />
                教练动作 ({{ selectedPack.coach_actions.length }})
              </Space>
            </template>

            <Timeline class="action-timeline">
              <TimelineItem
                v-for="action in selectedPack.coach_actions"
                :key="action.action_id"
                :color="getActionCategoryTag(action.category).color"
              >
                <Card size="small" class="action-card">
                  <template #title>
                    <Space>
                      <Tag :color="getActionCategoryTag(action.category).color">
                        {{ getActionCategoryTag(action.category).label }}
                      </Tag>
                      <span>{{ action.title }}</span>
                    </Space>
                  </template>
                  <template #extra>
                    <CoachLevelBadge :level="action.required_level" />
                  </template>

                  <p class="action-desc">{{ action.description }}</p>

                  <div v-if="action.script" class="action-script">
                    <div class="script-label">
                      <BookOutlined /> 参考话术
                    </div>
                    <div class="script-content">{{ action.script }}</div>
                  </div>

                  <div v-if="action.tips?.length" class="action-tips">
                    <div class="tips-label">
                      <HeartOutlined /> 教练提示
                    </div>
                    <ul class="tips-list">
                      <li v-for="(tip, index) in action.tips" :key="index">{{ tip }}</li>
                    </ul>
                  </div>

                  <div v-if="action.behavior_stage?.length" class="action-stages">
                    <span style="color: #666">适用阶段: </span>
                    <BehaviorStageTag
                      v-for="stage in action.behavior_stage"
                      :key="stage"
                      :stage="stage"
                    />
                  </div>
                </Card>
              </TimelineItem>
            </Timeline>
          </TabPane>
        </Tabs>
      </template>
    </Drawer>
  </div>
</template>

<style scoped>
.interventions-page {
  padding: 24px;
}

.match-test-card {
  background: linear-gradient(135deg, #f0f5ff 0%, #e6f7ff 100%);
}

.match-field {
  display: flex;
  flex-direction: column;
}

.field-label {
  color: #666;
  margin-bottom: 8px;
  font-size: 13px;
}

.field-label .required {
  color: #ff4d4f;
  margin-right: 4px;
}

.pack-name-cell {
  display: flex;
  align-items: center;
}

.pack-name {
  font-weight: 500;
}

/* 图例 */
.legend-bar {
  margin-bottom: 16px;
  padding: 8px 16px;
  background: #fafafa;
  border-radius: 4px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  margin-right: 24px;
  font-size: 13px;
  color: #666;
}

.legend-color {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 2px;
  margin-right: 6px;
}

.legend-color.executable {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
}

.legend-color.not-executable {
  background: #fffbe6;
  border: 1px solid #ffe58f;
}

.legend-color.normal {
  background: #fff;
  border: 1px solid #d9d9d9;
}

/* 匹配高亮行 - 可执行 */
:deep(.executable-row) {
  background-color: #f6ffed !important;
}

:deep(.executable-row:hover > td) {
  background-color: #d9f7be !important;
}

:deep(.executable-row td) {
  border-color: #b7eb8f !important;
}

/* 匹配高亮行 - 不可执行 */
:deep(.not-executable-row) {
  background-color: #fffbe6 !important;
}

:deep(.not-executable-row:hover > td) {
  background-color: #fff1b8 !important;
}

:deep(.not-executable-row td) {
  border-color: #ffe58f !important;
}

/* 推荐动作弹窗 */
.action-recommend-card {
  margin-bottom: 12px;
  border-left: 3px solid #1890ff;
}

.script-box {
  background: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.script-header {
  color: #1890ff;
  font-weight: 500;
  margin-bottom: 8px;
}

.script-text {
  color: #333;
  font-style: italic;
  line-height: 1.6;
}

.tips-box {
  background: #fff7e6;
  border-radius: 6px;
  padding: 12px;
}

.tips-header {
  color: #fa8c16;
  font-weight: 500;
  margin-bottom: 8px;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  color: #666;
}

.tips-list li {
  margin-bottom: 4px;
}

/* 任务卡片 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  border-left: 3px solid #1890ff;
}

.task-desc {
  color: #666;
  margin-bottom: 12px;
}

.task-meta {
  margin-top: 8px;
}

.task-resources {
  margin-top: 8px;
}

/* 教练动作 */
.action-timeline {
  padding-top: 8px;
}

.action-card {
  margin-bottom: 8px;
}

.action-desc {
  color: #666;
  margin-bottom: 12px;
}

.action-script {
  background: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.script-label {
  color: #1890ff;
  font-weight: 500;
  margin-bottom: 8px;
}

.script-content {
  color: #333;
  font-style: italic;
  line-height: 1.6;
}

.action-tips {
  background: #fff7e6;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.tips-label {
  color: #fa8c16;
  font-weight: 500;
  margin-bottom: 8px;
}

.action-stages {
  margin-top: 8px;
}
</style>
