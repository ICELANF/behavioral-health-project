<template>
  <div class="coach-portal">
    <!-- 顶部导航栏 -->
    <div class="portal-header">
      <div class="header-left">
        <span class="greeting">{{ getGreeting() }}，{{ coachInfo.name }}</span>
        <a-tag :color="getLevelColor(coachInfo.level)">{{ coachInfo.level }} {{ coachInfo.levelName }}</a-tag>
      </div>
      <div class="header-right">
        <a-badge :count="notifications" :offset="[-2, 2]">
          <BellOutlined class="header-icon" />
        </a-badge>
        <a-dropdown>
          <a-avatar :src="coachInfo.avatar" :size="36">
            {{ coachInfo.name?.charAt(0) }}
          </a-avatar>
          <template #overlay>
            <a-menu @click="handleMenuClick">
              <a-menu-item key="profile">个人中心</a-menu-item>
              <a-menu-item key="settings">设置</a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout">退出登录</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" style="text-align:center;padding:60px 0">
      <a-spin size="large" tip="加载工作台数据..." />
    </div>

    <!-- 今日工作概览 -->
    <div v-if="!loading" class="overview-section">
      <div class="section-title">
        <CalendarOutlined /> 今日工作概览
      </div>
      <div class="overview-cards">
        <div class="overview-card" :class="{ clickable: todayStats.pendingFollowups > 0 }" @click="todayStats.pendingFollowups > 0 && router.push('/coach-portal/students')">
          <div class="card-icon todo"><ClockCircleOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.pendingFollowups }}</div>
            <div class="card-label">待跟进</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon done"><CheckCircleOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.completedFollowups }}</div>
            <div class="card-label">已完成</div>
          </div>
        </div>
        <div class="overview-card" :class="{ clickable: todayStats.alertStudents > 0 }" @click="todayStats.alertStudents > 0 && router.push('/coach-portal/students?priority=high')">
          <div class="card-icon alert"><AlertOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.alertStudents }}</div>
            <div class="card-label">需关注</div>
          </div>
        </div>
        <div class="overview-card" :class="{ clickable: todayStats.unreadMessages > 0 }" @click="todayStats.unreadMessages > 0 && router.push('/coach/messages')">
          <div class="card-icon message"><MessageOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.unreadMessages }}</div>
            <div class="card-label">未读消息</div>
          </div>
        </div>
        <div class="overview-card clickable" @click="openPushQueueDrawer">
          <div class="card-icon" style="background:#f9f0ff;color:#722ed1"><a-badge :count="pushQueueStats.pending" :offset="[6,-4]"><AuditOutlined /></a-badge></div>
          <div class="card-content">
            <div class="card-value">{{ pushQueueStats.pending }}</div>
            <div class="card-label">待审批推送</div>
          </div>
        </div>
      </div>
      <!-- 设备预警卡片 -->
      <div v-if="deviceAlerts.length" class="device-alerts-section" style="margin-top:12px">
        <div v-for="alert in deviceAlerts.slice(0, 3)" :key="alert.id"
             style="display:flex;align-items:center;gap:8px;padding:10px 12px;border-radius:8px;margin-bottom:6px"
             :style="{ background: alert.severity === 'danger' ? '#fff2f0' : '#fffbe6', border: '1px solid ' + (alert.severity === 'danger' ? '#ffccc7' : '#ffe58f') }"
        >
          <AlertOutlined :style="{ color: alert.severity === 'danger' ? '#ff4d4f' : '#faad14', fontSize:'18px' }" />
          <div style="flex:1">
            <div style="font-size:13px;font-weight:500">{{ alert.message }}</div>
            <div style="font-size:11px;color:#999">{{ alert.student_name || '' }} · {{ alert.data_type }} · 值: {{ alert.data_value }}</div>
          </div>
          <a-button size="small" type="link" @click="resolveAlert(alert)">处理</a-button>
        </div>
      </div>
    </div>

    <!-- 待跟进学员列表 -->
    <div v-if="!loading" class="students-section">
      <div class="section-header">
        <div class="section-title">
          <TeamOutlined /> 待跟进学员
        </div>
        <a class="view-all" @click="router.push('/coach-portal/students')">查看全部 <RightOutlined /></a>
      </div>

      <div class="student-list">
        <div
          v-for="student in pendingStudents.slice(0, 2)"
          :key="student.id"
          class="student-card"
          @click="openStudentDetail(student)"
        >
          <div class="student-avatar">
            <a-avatar :size="48" :src="student.avatar">
              {{ student.name?.charAt(0) }}
            </a-avatar>
            <span class="stage-badge" :class="student.stage">
              {{ getStageLabel(student.stage) }}
            </span>
          </div>
          <div class="student-info">
            <div class="student-name">{{ student.name }}</div>
            <div class="student-condition">{{ student.condition }}</div>
            <div class="student-meta">
              <span class="meta-item">
                <ClockCircleOutlined /> {{ student.lastContact }}
              </span>
              <a-tag v-if="student.priority === 'high'" color="red" size="small">紧急</a-tag>
              <a-tag v-else-if="student.priority === 'medium'" color="orange" size="small">重要</a-tag>
            </div>
          </div>
          <div class="student-action">
            <a-button type="primary" size="small" @click.stop="startFollowup(student)">
              开始跟进
            </a-button>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 干预建议审核 -->
    <div v-if="!loading" class="ai-section">
      <div class="section-header">
        <div class="section-title">
          <RobotOutlined /> AI 干预建议审核
        </div>
        <a class="view-all" @click="router.push('/coach-portal/ai-review')">
          {{ aiRecommendations.filter(r => r.status === 'pending').length }} 条待审核 <RightOutlined />
        </a>
      </div>

      <div class="ai-recommendations">
        <div
          v-for="rec in aiRecommendations.slice(0, 2)"
          :key="rec.id"
          class="recommendation-card"
          :class="{ 'rec-approved': rec.status === 'approved', 'rec-rejected': rec.status === 'rejected', 'rec-modified': rec.status === 'modified' }"
        >
          <div class="rec-header">
            <span class="rec-type" :class="rec.type">{{ rec.typeLabel }}</span>
            <span class="rec-student">{{ rec.studentName }}</span>
            <span v-if="rec.status !== 'pending'" class="rec-status" :class="'status-' + rec.status">
              {{ { approved: '已批准', rejected: '已驳回', modified: '已修正' }[rec.status] }}
            </span>
          </div>
          <div class="rec-content">
            <div class="rec-ai-label">AI 建议：</div>
            {{ rec.suggestion }}
          </div>

          <!-- 修正输入框 -->
          <div v-if="rec.showModify" class="rec-modify-area">
            <textarea
              v-model="rec.modifiedText"
              class="modify-textarea"
              placeholder="输入修正后的建议内容..."
              rows="3"
            ></textarea>
            <div class="modify-actions">
              <a-button size="small" type="primary" @click="confirmModify(rec)">确认修正并推送</a-button>
              <a-button size="small" @click="rec.showModify = false">取消</a-button>
            </div>
          </div>

          <!-- 审核操作按钮 -->
          <div v-if="rec.status === 'pending'" class="rec-actions">
            <a-button size="small" type="primary" style="background:#52c41a;border-color:#52c41a" @click="approveRecommendation(rec)">
              批准推送
            </a-button>
            <a-button size="small" @click="rec.showModify = true">
              修正后推送
            </a-button>
            <a-button size="small" danger @click="rejectRecommendation(rec)">
              驳回
            </a-button>
            <a-button size="small" type="link" @click="viewDetail(rec)">
              查看学员
            </a-button>
          </div>

          <!-- 已处理状态 -->
          <div v-else class="rec-result">
            <span v-if="rec.status === 'approved'" class="result-text approved">已批准推送给 {{ rec.studentName }}</span>
            <span v-if="rec.status === 'modified'" class="result-text modified">已修正推送：{{ rec.modifiedText }}</span>
            <span v-if="rec.status === 'rejected'" class="result-text rejected">已驳回，不推送</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 干预工具箱 -->
    <div v-if="!loading" class="intervention-section">
      <div class="section-header">
        <div class="section-title">
          <AppstoreOutlined /> 干预工具箱
        </div>
      </div>

      <div class="intervention-grid">
        <div
          v-for="tool in interventionTools"
          :key="tool.id"
          class="tool-card"
          @click="openTool(tool)"
        >
          <div class="tool-icon">{{ tool.icon }}</div>
          <div class="tool-name">{{ tool.name }}</div>
        </div>
      </div>
    </div>

    <!-- 我的学习 -->
    <div v-if="!loading" class="learning-section">
      <div class="section-header">
        <div class="section-title">
          <BookOutlined /> 我的学习
        </div>
        <a class="view-all" @click="goToLearning">查看课程 <RightOutlined /></a>
      </div>

      <div class="learning-progress">
        <div class="progress-item">
          <div class="progress-label">
            <span>{{ coachInfo.level }} 认证进度</span>
            <span class="progress-value">{{ learningProgress.certProgress }}%</span>
          </div>
          <a-progress
            :percent="learningProgress.certProgress"
            :show-info="false"
            stroke-color="#667eea"
          />
        </div>
        <div class="progress-stats">
          <div class="stat-item">
            <div class="stat-value">{{ learningProgress.coursesCompleted }}/{{ learningProgress.coursesTotal }}</div>
            <div class="stat-label">课程完成</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ learningProgress.examsPassed }}/{{ learningProgress.examsTotal }}</div>
            <div class="stat-label">考试通过</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ learningProgress.caseCount }}</div>
            <div class="stat-label">案例积累</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="bottom-nav">
      <div class="nav-item active">
        <HomeOutlined />
        <span>工作台</span>
      </div>
      <div class="nav-item" @click="router.push('/coach-portal/students')">
        <TeamOutlined />
        <span>学员</span>
      </div>
      <div class="nav-item" @click="goToMessages">
        <MessageOutlined />
        <span>消息</span>
      </div>
      <div class="nav-item" @click="goToLearning">
        <BookOutlined />
        <span>学习</span>
      </div>
      <div class="nav-item" @click="handleLogout">
        <LogoutOutlined />
        <span>退出</span>
      </div>
    </div>

    <!-- 推送评估抽屉 -->
    <a-drawer
      v-model:open="assessmentDrawerVisible"
      title="推送评估"
      placement="right"
      :width="720"
      :closable="true"
      destroyOnClose
    >
      <div class="assessment-panel">
        <!-- 推送表单 -->
        <div class="assign-form card" style="padding:16px;margin-bottom:16px;border:1px solid #f0f0f0;border-radius:8px">
          <h4 style="margin-bottom:12px">推送评估给学员</h4>

          <!-- AI推送建议面板 -->
          <div v-if="pushRecommendations.length" style="margin-bottom:16px;padding:12px;background:#f0f9ff;border-radius:8px;border:1px solid #bae7ff">
            <div style="font-size:13px;font-weight:600;color:#1890ff;margin-bottom:8px">AI 推送建议</div>
            <div v-for="rec in pushRecommendations" :key="rec.student_id" style="padding:8px;background:#fff;border-radius:6px;margin-bottom:6px;border-left:3px solid" :style="{ borderLeftColor: rec.priority === 'high' ? '#ff4d4f' : rec.priority === 'medium' ? '#faad14' : '#52c41a' }">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:500">{{ rec.student_name }}</span>
                <a-tag :color="rec.priority === 'high' ? 'red' : rec.priority === 'medium' ? 'orange' : 'green'" size="small">
                  {{ rec.priority === 'high' ? '高优' : rec.priority === 'medium' ? '中优' : '低优' }}
                </a-tag>
              </div>
              <div style="font-size:12px;color:#666;margin-top:4px">{{ rec.reasoning }}</div>
              <a-button type="link" size="small" style="padding:0;margin-top:4px" @click="applyRecommendation(rec)">采用建议</a-button>
            </div>
          </div>

          <div style="margin-bottom:12px">
            <div style="margin-bottom:4px;font-weight:500">选择学员</div>
            <a-select
              v-model:value="assignForm.studentId"
              placeholder="请选择学员"
              style="width:100%"
              show-search
              option-filter-prop="label"
            >
              <a-select-option
                v-for="s in pendingStudents"
                :key="s.id"
                :value="s.id"
                :label="s.name"
              >{{ s.name }} ({{ getStageLabel(s.stage) }})</a-select-option>
            </a-select>
          </div>

          <div style="margin-bottom:12px">
            <div style="margin-bottom:4px;font-weight:500">推送类型</div>
            <a-radio-group v-model:value="assignForm.pushType">
              <a-radio-button value="questions">高频题目</a-radio-button>
              <a-radio-button value="behavior">行为评估</a-radio-button>
              <a-radio-button value="custom">自由命题</a-radio-button>
              <a-radio-button value="scales">整套量表</a-radio-button>
            </a-radio-group>
            <a-tag v-if="assignTotalItems > 0" :color="assignTotalItems > 3 ? 'red' : 'blue'" style="margin-left:8px">
              {{ assignTotalItems }}/3 项
            </a-tag>
          </div>

          <!-- 高频题目模式 -->
          <template v-if="assignForm.pushType === 'questions'">
            <div style="margin-bottom:12px">
              <div style="margin-bottom:4px;font-weight:500">题目预设</div>
              <a-radio-group v-model:value="assignForm.questionPreset">
                <a-radio value="hf20">HF-20（20题快速筛查，约5分钟）</a-radio>
                <a-radio value="hf50">HF-50（50题深度评估，约12分钟）</a-radio>
              </a-radio-group>
            </div>
          </template>

          <!-- 行为评估模式 -->
          <template v-if="assignForm.pushType === 'behavior'">
            <div style="margin-bottom:12px">
              <div style="margin-bottom:4px;font-weight:500">从题库选择题目（最多3道，约1-3分钟）</div>
              <div style="font-size:12px;color:#999;margin-bottom:8px">从内置5套量表171道题中自由选取，降低用户认知负担</div>
              <a-input-search
                v-model:value="behaviorSearchText"
                placeholder="搜索题目关键词..."
                style="margin-bottom:8px"
                allow-clear
              />
              <div v-if="assignForm.selectedQuestionIds.length > 0" style="margin-bottom:8px">
                <a-tag v-for="qid in assignForm.selectedQuestionIds" :key="qid" closable @close="removeBehaviorQuestion(qid)" color="blue">
                  {{ getBehaviorQuestionLabel(qid) }}
                </a-tag>
              </div>
              <div style="max-height:280px;overflow-y:auto;border:1px solid #f0f0f0;border-radius:6px">
                <div v-if="loadingAllQuestions" style="text-align:center;padding:20px"><a-spin size="small" /></div>
                <template v-else>
                  <div v-for="group in filteredBehaviorGroups" :key="group.key" style="margin-bottom:4px">
                    <div style="padding:6px 12px;background:#fafafa;font-size:12px;font-weight:600;color:#666;position:sticky;top:0;z-index:1">
                      {{ group.label }} ({{ group.questions.length }})
                    </div>
                    <div
                      v-for="q in group.questions"
                      :key="q.id"
                      style="padding:8px 12px;cursor:pointer;border-bottom:1px solid #fafafa;display:flex;align-items:center;gap:8px;font-size:13px"
                      :style="{ background: assignForm.selectedQuestionIds.includes(q.id) ? '#e6f7ff' : 'transparent' }"
                      @click="toggleBehaviorQuestion(q.id)"
                    >
                      <a-checkbox :checked="assignForm.selectedQuestionIds.includes(q.id)" :disabled="!assignForm.selectedQuestionIds.includes(q.id) && assignForm.selectedQuestionIds.length >= 3" />
                      <span style="color:#999;font-size:11px;flex-shrink:0">[{{ q.id }}]</span>
                      <span style="flex:1">{{ q.text }}</span>
                      <a-tag size="small" :color="{ ttm7:'blue', bpt6:'purple', spi:'green', capacity:'orange', big_five:'cyan' }[q.questionnaire] || 'default'">
                        {{ q.dimension }}
                      </a-tag>
                    </div>
                  </div>
                </template>
              </div>
              <div style="font-size:12px;color:#999;margin-top:4px;text-align:right">
                已选 {{ assignForm.selectedQuestionIds.length }}/3
              </div>
            </div>
          </template>

          <!-- 自由命题模式 -->
          <template v-if="assignForm.pushType === 'custom'">
            <div style="margin-bottom:12px">
              <div style="margin-bottom:4px;font-weight:500">自由命题（最多3道，约3分钟）</div>
              <div style="font-size:12px;color:#999;margin-bottom:8px">直接编写题目，学员将用1-5分量表作答</div>
              <div v-for="(_, idx) in assignForm.customQuestions" :key="idx" style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <span style="flex-shrink:0;color:#999;font-size:12px">{{ idx + 1 }}.</span>
                <a-input
                  v-model:value="assignForm.customQuestions[idx]"
                  :placeholder="`请输入第${idx + 1}道题目...`"
                  allow-clear
                />
                <a-button v-if="assignForm.customQuestions.length > 1" type="text" danger size="small" @click="assignForm.customQuestions.splice(idx, 1)">
                  <DeleteOutlined />
                </a-button>
              </div>
              <a-button v-if="assignForm.customQuestions.length < 3" type="dashed" block size="small" @click="assignForm.customQuestions.push('')">
                + 添加题目
              </a-button>
            </div>
          </template>

          <!-- 量表模式 -->
          <template v-if="assignForm.pushType === 'scales'">
            <div style="margin-bottom:12px">
              <div style="margin-bottom:4px;font-weight:500">选择量表</div>
              <a-alert v-if="assignForm.scales.length > 3" message="建议每次推送不超过3项" type="warning" show-icon style="margin-bottom:8px" />
              <a-checkbox-group v-model:value="assignForm.scales" :options="scaleOptions" />
            </div>
          </template>

          <div style="margin-bottom:12px">
            <div style="margin-bottom:4px;font-weight:500">教练备注（可选）</div>
            <a-input v-model:value="assignForm.note" placeholder="给学员的备注说明..." />
          </div>
          <a-button type="primary" block :loading="assignSubmitting" :disabled="assignTotalItems > 3 || assignTotalItems === 0" @click="submitAssign">
            推送评估 {{ assignTotalItems > 0 ? `(${assignTotalItems}项)` : '' }}
          </a-button>
        </div>

        <!-- 已推送列表 -->
        <div style="margin-top:16px">
          <h4 style="margin-bottom:12px">已推送的评估任务</h4>
          <a-spin :spinning="loadingAssignments">
            <div v-if="assignmentList.length === 0" style="text-align:center;padding:24px;color:#999">暂无评估任务</div>
            <div v-for="a in assignmentList" :key="a.id" class="assignment-card" style="padding:12px;border:1px solid #f0f0f0;border-radius:8px;margin-bottom:8px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <span style="font-weight:500">{{ a.student_name }}</span>
                <a-tag
                  :color="{ pending:'orange', completed:'blue', reviewed:'cyan', pushed:'green' }[a.status] || 'default'"
                  size="small"
                >{{ { pending:'待完成', completed:'待审核', reviewed:'已审核', pushed:'已推送' }[a.status] || a.status }}</a-tag>
              </div>
              <div style="font-size:12px;color:#999">
                {{ typeof a.scales === 'object' && !Array.isArray(a.scales) ? (a.scales.custom_questions ? '自由命题: ' + a.scales.custom_questions.length + '道题' : a.scales.question_ids?.length ? '行为评估: ' + a.scales.question_ids.length + '道题' : a.scales.question_preset ? '高频题: ' + a.scales.question_preset : '量表: ' + (a.scales.scales || []).join(', ')) : '量表: ' + (a.scales || []).join(', ') }}
                <span style="margin-left:12px">{{ a.completed_at ? '完成于 ' + a.completed_at.replace('T',' ').slice(0,16) : '创建于 ' + (a.created_at||'').replace('T',' ').slice(0,16) }}</span>
              </div>
              <a-button
                v-if="a.status === 'completed'"
                type="link"
                size="small"
                style="padding:0;margin-top:4px"
                @click="openReviewDrawer(a)"
              >去审核</a-button>
            </div>
          </a-spin>
        </div>
      </div>
    </a-drawer>

    <!-- 审核与推送抽屉 -->
    <a-drawer
      v-model:open="goalDrawerVisible"
      :title="'审核与推送' + (reviewingAssignment ? ' - ' + reviewingAssignment.student_name : '')"
      placement="right"
      :width="800"
      :closable="true"
      destroyOnClose
    >
      <div class="review-panel">
        <template v-if="!reviewingAssignment">
          <!-- 待审核列表 -->
          <a-spin :spinning="loadingReviewList">
            <div v-if="reviewList.length === 0" style="text-align:center;padding:40px;color:#999">暂无待审核的评估</div>
            <div
              v-for="a in reviewList"
              :key="a.id"
              style="padding:12px;border:1px solid #f0f0f0;border-radius:8px;margin-bottom:12px;cursor:pointer"
              @click="selectReviewAssignment(a)"
            >
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:600">{{ a.student_name }}</span>
                <a-tag :color="a.status === 'completed' ? 'blue' : 'cyan'" size="small">
                  {{ a.status === 'completed' ? '待审核' : '已审核' }}
                </a-tag>
              </div>
              <div style="font-size:12px;color:#999;margin-top:4px">
                完成于 {{ (a.completed_at||'').replace('T',' ').slice(0,16) }} | {{ (a.review_items||[]).length }} 条内容
              </div>
            </div>
          </a-spin>
        </template>

        <template v-else>
          <!-- 审核详情 -->
          <a-button size="small" @click="reviewingAssignment = null" style="margin-bottom:12px">
            返回列表
          </a-button>

          <div v-for="item in reviewingAssignment.review_items" :key="item.id"
               style="padding:12px;border:1px solid #f0f0f0;border-radius:8px;margin-bottom:12px"
               :style="{ borderLeftColor: { goal:'#1890ff',prescription:'#52c41a',suggestion:'#faad14' }[item.category] || '#d9d9d9', borderLeftWidth:'3px' }"
          >
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <div>
                <a-tag :color="{ goal:'blue',prescription:'green',suggestion:'orange' }[item.category]" size="small">
                  {{ { goal:'管理目标',prescription:'行为处方',suggestion:'指导建议' }[item.category] || item.category }}
                </a-tag>
                <span style="margin-left:8px;font-weight:500">{{ item.original_content?.domain_name || item.domain }}</span>
              </div>
              <a-tag v-if="item.status !== 'pending'" :color="{ approved:'green',modified:'blue',rejected:'red' }[item.status]" size="small">
                {{ { approved:'已采纳',modified:'已修改',rejected:'已拒绝' }[item.status] }}
              </a-tag>
            </div>

            <!-- 原始内容 -->
            <div style="background:#fafafa;padding:8px 12px;border-radius:6px;font-size:13px;margin-bottom:8px">
              <template v-if="item.category === 'goal'">
                <div><strong>目标: </strong>{{ item.original_content?.core_goal }}</div>
                <div v-if="item.original_content?.strategy"><strong>策略: </strong>{{ item.original_content.strategy }}</div>
              </template>
              <template v-else-if="item.category === 'prescription'">
                <div v-if="item.original_content?.recommended_behaviors?.length">
                  <strong>推荐行为: </strong>
                  <span v-for="(b,i) in item.original_content.recommended_behaviors" :key="i">{{ typeof b === 'string' ? b : b.name || b.title || JSON.stringify(b) }}{{ i < item.original_content.recommended_behaviors.length-1 ? '、' : '' }}</span>
                </div>
                <div v-if="item.original_content?.contraindicated_behaviors?.length">
                  <strong>禁忌行为: </strong>
                  <span v-for="(b,i) in item.original_content.contraindicated_behaviors" :key="i">{{ typeof b === 'string' ? b : b.name || b.title || JSON.stringify(b) }}{{ i < item.original_content.contraindicated_behaviors.length-1 ? '、' : '' }}</span>
                </div>
              </template>
              <template v-else-if="item.category === 'suggestion'">
                <div v-for="(adv,i) in (item.original_content?.advice || [])" :key="i" style="margin-bottom:4px">
                  {{ i+1 }}. {{ typeof adv === 'string' ? adv : adv.title || adv.content || JSON.stringify(adv) }}
                </div>
              </template>
            </div>

            <!-- 修改输入 -->
            <div v-if="item._editing" style="margin-bottom:8px">
              <a-textarea v-model:value="item._editText" :rows="3" placeholder="输入修改后的内容..." />
              <a-input v-model:value="item._editNote" placeholder="教练批注（可选）" style="margin-top:4px" />
              <div style="margin-top:8px;display:flex;gap:8px">
                <a-button type="primary" size="small" @click="confirmReviewModify(item)">确认修改</a-button>
                <a-button size="small" @click="item._editing = false">取消</a-button>
              </div>
            </div>

            <!-- 审核操作 -->
            <div v-if="item.status === 'pending' && !item._editing" style="display:flex;gap:8px">
              <a-button size="small" style="background:#52c41a;border-color:#52c41a;color:#fff" @click="reviewItem(item, 'approved')">
                采纳
              </a-button>
              <a-button size="small" @click="item._editing = true; item._editText = ''; item._editNote = ''">
                修改
              </a-button>
              <a-button size="small" danger @click="reviewItem(item, 'rejected')">
                拒绝
              </a-button>
            </div>
          </div>

          <!-- 推送按钮 -->
          <div style="margin-top:16px">
            <a-button
              type="primary"
              block
              :loading="pushSubmitting"
              :disabled="reviewingAssignment.review_items.some((i: any) => i.status === 'pending')"
              @click="pushAssignment"
            >
              确认推送给学员
            </a-button>
            <div v-if="reviewingAssignment.review_items.some((i: any) => i.status === 'pending')" style="text-align:center;font-size:12px;color:#ff4d4f;margin-top:4px">
              还有 {{ reviewingAssignment.review_items.filter((i: any) => i.status === 'pending').length }} 条未审核
            </div>
          </div>
        </template>
      </div>
    </a-drawer>

    <!-- 个人中心抽屉 -->
    <a-drawer
      v-model:open="profileDrawerVisible"
      title="个人中心"
      placement="right"
      :width="480"
      :closable="true"
      destroyOnClose
    >
      <div class="profile-panel">
        <div class="profile-card">
          <a-avatar :size="72">{{ coachInfo.name?.charAt(0) }}</a-avatar>
          <div class="profile-name">{{ coachInfo.name }}</div>
          <a-tag :color="getLevelColor(coachInfo.level)">{{ coachInfo.level }} {{ coachInfo.levelName }}</a-tag>
        </div>
        <div class="profile-stats">
          <div class="pstat"><div class="pstat-val">{{ pendingStudents.length }}</div><div class="pstat-label">管理学员</div></div>
          <div class="pstat"><div class="pstat-val">{{ learningProgress.coursesCompleted }}</div><div class="pstat-label">已学课程</div></div>
          <div class="pstat"><div class="pstat-val">{{ learningProgress.caseCount }}</div><div class="pstat-label">案例积累</div></div>
        </div>
        <div class="profile-section">
          <h4>专长领域</h4>
          <div class="specialty-tags">
            <a-tag v-for="s in coachInfo.specialty" :key="s" color="blue">{{ s }}</a-tag>
          </div>
        </div>
        <div class="profile-section">
          <h4>认证进度</h4>
          <a-progress :percent="learningProgress.certProgress" stroke-color="#667eea" />
        </div>
      </div>
    </a-drawer>

    <!-- 设置抽屉 -->
    <a-drawer
      v-model:open="settingsDrawerVisible"
      title="设置"
      placement="right"
      :width="480"
      :closable="true"
      destroyOnClose
    >
      <div class="settings-panel">
        <div class="setting-item">
          <span>消息通知</span>
          <a-switch v-model:checked="settingsState.notifications" />
        </div>
        <div class="setting-item">
          <span>学员预警提醒</span>
          <a-switch v-model:checked="settingsState.alertReminder" />
        </div>
        <div class="setting-item">
          <span>AI 建议自动推送</span>
          <a-switch v-model:checked="settingsState.autoAIPush" />
        </div>
        <div class="setting-item">
          <span>深色模式</span>
          <a-switch v-model:checked="settingsState.darkMode" />
        </div>
        <a-divider />
        <a-button danger block @click="handleLogout">退出登录</a-button>
      </div>
    </a-drawer>

    <!-- 分配挑战抽屉 -->
    <a-drawer
      v-model:open="challengeAssignDrawerVisible"
      :title="'分配挑战 - ' + (challengeAssignStudent?.name || '')"
      placement="right"
      :width="640"
      :closable="true"
      destroyOnClose
    >
      <div class="challenge-assign-panel">
        <!-- 学员现有挑战进度 -->
        <div style="margin-bottom:16px">
          <h4 style="margin-bottom:8px">当前参与的挑战</h4>
          <a-spin :spinning="loadingStudentChallenges">
            <div v-if="studentChallenges.length === 0" style="text-align:center;padding:16px;color:#999;font-size:13px">暂无参与中的挑战</div>
            <div v-for="ch in studentChallenges" :key="ch.id" style="padding:10px 12px;border:1px solid #f0f0f0;border-radius:8px;margin-bottom:8px">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:500">{{ ch.challenge_title }}</span>
                <a-tag :color="{ enrolled:'blue', active:'green', completed:'default', dropped:'red' }[ch.status] || 'default'" size="small">
                  {{ { enrolled:'待开始', active:'进行中', completed:'已完成', dropped:'已退出' }[ch.status] || ch.status }}
                </a-tag>
              </div>
              <div style="font-size:12px;color:#999;margin-top:4px">
                第 {{ ch.current_day }} / {{ ch.duration_days }} 天 · 连续打卡 {{ ch.streak_days }} 天
              </div>
              <a-progress :percent="ch.day_progress_pct || 0" :show-info="false" size="small" style="margin-top:4px" />
            </div>
          </a-spin>
        </div>

        <a-divider />

        <!-- 已发布挑战列表 -->
        <div>
          <h4 style="margin-bottom:8px">选择挑战分配</h4>
          <a-spin :spinning="loadingPublishedChallenges">
            <div v-if="publishedChallenges.length === 0" style="text-align:center;padding:16px;color:#999;font-size:13px">暂无已发布的挑战</div>
            <div
              v-for="ch in publishedChallenges"
              :key="ch.id"
              style="padding:12px;border:1px solid #f0f0f0;border-radius:8px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center"
            >
              <div style="flex:1">
                <div style="font-weight:500">{{ ch.title }}</div>
                <div style="font-size:12px;color:#999;margin-top:2px">
                  {{ ch.category }} · {{ ch.duration_days }}天 · {{ ch.enrollment_count || 0 }}人参与
                </div>
                <div v-if="ch.description" style="font-size:12px;color:#666;margin-top:4px">{{ ch.description?.slice(0, 60) }}{{ ch.description?.length > 60 ? '...' : '' }}</div>
              </div>
              <a-button
                type="primary"
                size="small"
                :loading="assigningChallengeId === ch.id"
                :disabled="studentChallenges.some((sc: any) => sc.challenge_id === ch.id && ['enrolled','active'].includes(sc.status))"
                @click="assignChallenge(ch.id)"
              >
                {{ studentChallenges.some((sc: any) => sc.challenge_id === ch.id && ['enrolled','active'].includes(sc.status)) ? '已分配' : '分配' }}
              </a-button>
            </div>
          </a-spin>
        </div>
      </div>
    </a-drawer>

    <!-- 推送审批抽屉 -->
    <a-drawer
      v-model:open="pushQueueDrawerVisible"
      title="推送审批队列"
      placement="right"
      :width="720"
      :closable="true"
      destroyOnClose
    >
      <div class="push-queue-panel">
        <!-- 统计栏 -->
        <div style="display:flex;gap:16px;margin-bottom:16px">
          <div style="flex:1;text-align:center;padding:12px;background:#f6ffed;border-radius:8px">
            <div style="font-size:20px;font-weight:700;color:#52c41a">{{ pushQueueStats.sent }}</div>
            <div style="font-size:12px;color:#999">已投递</div>
          </div>
          <div style="flex:1;text-align:center;padding:12px;background:#fff7e6;border-radius:8px">
            <div style="font-size:20px;font-weight:700;color:#faad14">{{ pushQueueStats.pending }}</div>
            <div style="font-size:12px;color:#999">待审批</div>
          </div>
          <div style="flex:1;text-align:center;padding:12px;background:#e6f7ff;border-radius:8px">
            <div style="font-size:20px;font-weight:700;color:#1890ff">{{ pushQueueStats.approved }}</div>
            <div style="font-size:12px;color:#999">已通过</div>
          </div>
          <div style="flex:1;text-align:center;padding:12px;background:#fff1f0;border-radius:8px">
            <div style="font-size:20px;font-weight:700;color:#ff4d4f">{{ pushQueueStats.rejected }}</div>
            <div style="font-size:12px;color:#999">已拒绝</div>
          </div>
        </div>

        <!-- 筛选器 -->
        <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center">
          <a-select v-model:value="pushQueueFilter.source_type" placeholder="来源" style="width:130px" allow-clear>
            <a-select-option value="challenge">挑战打卡</a-select-option>
            <a-select-option value="device_alert">设备预警</a-select-option>
            <a-select-option value="micro_action">微行动</a-select-option>
            <a-select-option value="ai_recommendation">AI建议</a-select-option>
            <a-select-option value="system">系统</a-select-option>
          </a-select>
          <a-select v-model:value="pushQueueFilter.priority" placeholder="优先级" style="width:100px" allow-clear>
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="normal">中</a-select-option>
            <a-select-option value="low">低</a-select-option>
          </a-select>
          <a-select v-model:value="pushQueueFilter.status" placeholder="状态" style="width:100px">
            <a-select-option value="pending">待审批</a-select-option>
            <a-select-option value="approved">已通过</a-select-option>
            <a-select-option value="sent">已投递</a-select-option>
            <a-select-option value="rejected">已拒绝</a-select-option>
          </a-select>
          <a-button type="primary" size="small" @click="loadPushQueueItems">刷新</a-button>
          <div style="flex:1"></div>
          <a-button
            v-if="pushQueueFilter.status === 'pending' && selectedQueueIds.length > 0"
            type="primary"
            size="small"
            :loading="batchApproving"
            @click="batchApproveQueue"
          >
            批量审批 ({{ selectedQueueIds.length }})
          </a-button>
        </div>

        <!-- 列表 -->
        <a-spin :spinning="loadingPushQueue">
          <div v-if="pushQueueItems.length === 0" style="text-align:center;padding:40px;color:#999">暂无推送条目</div>
          <div
            v-for="item in pushQueueItems"
            :key="item.id"
            style="padding:12px;border-radius:8px;margin-bottom:8px;border:1px solid #f0f0f0;display:flex;gap:10px"
            :style="{ borderLeftWidth:'4px', borderLeftColor: item.priority === 'high' ? '#ff4d4f' : item.priority === 'normal' ? '#faad14' : '#d9d9d9' }"
          >
            <!-- checkbox 仅对 pending -->
            <div v-if="item.status === 'pending'" style="display:flex;align-items:flex-start;padding-top:2px">
              <a-checkbox :checked="selectedQueueIds.includes(item.id)" @change="toggleQueueSelect(item.id)" />
            </div>
            <div style="flex:1">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                <div style="display:flex;align-items:center;gap:6px">
                  <a-tag :color="sourceTagColor(item.source_type)" size="small">{{ sourceTagLabel(item.source_type) }}</a-tag>
                  <span style="font-weight:500;font-size:14px">{{ item.title }}</span>
                </div>
                <a-tag :color="{ pending:'orange', approved:'blue', sent:'green', rejected:'red', expired:'default' }[item.status]" size="small">
                  {{ { pending:'待审批', approved:'已通过', sent:'已投递', rejected:'已拒绝', expired:'已过期' }[item.status] }}
                </a-tag>
              </div>
              <div v-if="item.student_name" style="font-size:12px;color:#666;margin-bottom:2px">学员: {{ item.student_name }}</div>
              <div v-if="item.content" style="font-size:13px;color:#333;margin-bottom:6px;white-space:pre-line;max-height:60px;overflow:hidden">{{ item.content }}</div>
              <div style="font-size:11px;color:#999">
                {{ item.created_at?.replace('T',' ').slice(0,16) }}
                <span v-if="item.coach_note" style="margin-left:8px;color:#666">批注: {{ item.coach_note }}</span>
              </div>

              <!-- 审批操作 (仅 pending) -->
              <div v-if="item.status === 'pending'" style="margin-top:8px;display:flex;gap:8px;align-items:center">
                <a-button size="small" style="background:#52c41a;border-color:#52c41a;color:#fff" @click="approveQueueItem(item)">
                  通过
                </a-button>
                <a-button size="small" @click="item._editing = true">
                  修改后通过
                </a-button>
                <a-button size="small" danger @click="rejectQueueItem(item)">
                  拒绝
                </a-button>
              </div>

              <!-- 修改内容区 -->
              <div v-if="item._editing" style="margin-top:8px;padding:8px;background:#fafafa;border-radius:6px">
                <a-textarea v-model:value="item._editContent" :rows="2" placeholder="修改推送内容..." style="margin-bottom:6px" />
                <a-date-picker
                  v-model:value="item._editTime"
                  show-time
                  placeholder="定时发送（可选）"
                  style="width:100%;margin-bottom:6px"
                  format="YYYY-MM-DD HH:mm"
                />
                <div style="display:flex;gap:8px">
                  <a-button size="small" type="primary" @click="approveQueueItemWithEdit(item)">确认通过</a-button>
                  <a-button size="small" @click="item._editing = false">取消</a-button>
                </div>
              </div>
            </div>
          </div>
        </a-spin>

        <!-- 分页 -->
        <div v-if="pushQueueTotal > 20" style="text-align:center;margin-top:12px">
          <a-pagination
            v-model:current="pushQueuePage"
            :total="pushQueueTotal"
            :page-size="20"
            size="small"
            @change="loadPushQueueItems"
          />
        </div>
      </div>
    </a-drawer>

    <!-- 学员详情抽屉 -->
    <a-drawer
      v-model:open="studentDrawerVisible"
      :title="currentStudent?.name"
      placement="right"
      :width="800"
      :closable="true"
      destroyOnClose
    >
      <template v-if="currentStudent">
        <div class="student-detail">
          <div class="detail-header">
            <a-avatar :size="64" :src="currentStudent.avatar">
              {{ currentStudent.name?.charAt(0) }}
            </a-avatar>
            <div class="detail-info">
              <h3>{{ currentStudent.name }}</h3>
              <p>{{ currentStudent.condition }}</p>
              <a-tag :color="getStageColor(currentStudent.stage)">
                {{ getStageLabel(currentStudent.stage) }}
              </a-tag>
            </div>
          </div>

          <a-tabs>
            <a-tab-pane key="health" tab="健康数据">
              <div class="health-metrics">
                <div class="metric-item">
                  <div class="metric-label">空腹血糖</div>
                  <div class="metric-value">{{ currentStudent.healthData?.fastingGlucose ?? '--' }} mmol/L</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">餐后血糖</div>
                  <div class="metric-value">{{ currentStudent.healthData?.postprandialGlucose ?? '--' }} mmol/L</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">体重</div>
                  <div class="metric-value">{{ currentStudent.healthData?.weight ?? '--' }} kg</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">本周运动</div>
                  <div class="metric-value">{{ currentStudent.healthData?.exerciseMinutes || 0 }} 分钟</div>
                </div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="records" tab="跟进记录">
              <div class="followup-records">
                <a-timeline>
                  <a-timeline-item v-for="record in currentStudent.records" :key="record.id" :color="record.type === 'call' ? 'blue' : 'green'">
                    <div class="record-item">
                      <div class="record-time">{{ record.time }}</div>
                      <div class="record-content">{{ record.content }}</div>
                    </div>
                  </a-timeline-item>
                </a-timeline>
              </div>
            </a-tab-pane>
            <a-tab-pane key="intervention" tab="干预方案">
              <div class="intervention-plan">
                <a-empty v-if="!currentStudent.interventionPlan" description="暂无干预方案" />
                <div v-else>
                  <h4>{{ currentStudent.interventionPlan.name }}</h4>
                  <p>{{ currentStudent.interventionPlan.description }}</p>
                </div>
              </div>
            </a-tab-pane>

            <!-- 诊断评估 -->
            <a-tab-pane key="diagnosis" tab="诊断评估">
              <div class="dx-grid">
                <!-- 左：行为诊断 -->
                <div class="dx-card">
                  <h4 class="dx-card-title">行为诊断</h4>

                  <div class="info-box">
                    <div class="info-row">
                      <span class="info-label">问题</span>
                      <span class="info-value">{{ diagnosisData.problem }}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">困难度</span>
                      <span class="info-value">{{ getDifficultyStars(diagnosisData.difficulty) }}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">目的</span>
                      <span class="info-value">{{ diagnosisData.purpose }}</span>
                    </div>
                  </div>

                  <a-divider style="margin: 12px 0" />

                  <div class="dx-subtitle">六类原因分析</div>
                  <div class="bar-container">
                    <div v-for="reason in diagnosisData.sixReasons" :key="reason.name" class="bar-source">
                      <div class="bar-label">
                        <span>{{ reason.name }}</span>
                        <span :style="{ color: reason.isWeak ? '#ff4d4f' : '#52c41a' }">{{ reason.score }}/{{ reason.max }}</span>
                      </div>
                      <a-progress
                        :percent="reason.score"
                        :stroke-color="getBarColor(reason.score, reason.max, reason.isWeak)"
                        :show-info="false"
                        size="small"
                      />
                      <a-tag v-if="reason.isWeak" color="red" size="small" style="margin-top: 2px">薄弱项</a-tag>
                    </div>
                  </div>

                  <a-divider style="margin: 12px 0" />

                  <div class="dx-subtitle">心理层次</div>
                  <div class="level-badges">
                    <a-tag v-for="level in diagnosisData.psychLevels" :key="level.label" :color="level.color">
                      {{ level.label }}
                    </a-tag>
                  </div>

                  <a-divider style="margin: 12px 0" />

                  <div class="dx-subtitle">循证依据</div>
                  <div class="evidence-list">
                    <div v-for="ev in diagnosisData.evidence" :key="ev.label" class="evidence-item">
                      <span class="evidence-label">{{ ev.label }}</span>
                      <span class="evidence-value" :class="'ev-' + ev.status">{{ ev.value }}</span>
                    </div>
                  </div>
                </div>

                <!-- 右：SPI评估 -->
                <div class="dx-card">
                  <h4 class="dx-card-title">SPI 评估</h4>

                  <div class="spi-circle-wrap">
                    <div class="spi-circle" :class="diagnosisData.spiScore >= 80 ? 'spi-good' : diagnosisData.spiScore >= 60 ? 'spi-mid' : 'spi-low'">
                      <div class="spi-number">{{ diagnosisData.spiScore }}</div>
                      <div class="spi-label">SPI</div>
                    </div>
                  </div>

                  <div class="info-box" style="margin-top: 16px">
                    <div class="info-row">
                      <span class="info-label">成功率</span>
                      <span class="info-value">{{ diagnosisData.successRate }}%</span>
                    </div>
                  </div>

                  <a-divider style="margin: 12px 0" />

                  <div class="dx-subtitle">评估公式</div>
                  <div class="formula-box">
                    {{ diagnosisData.interventionFormula }}
                  </div>

                  <a-divider style="margin: 12px 0" />

                  <div class="dx-subtitle">干预提醒</div>
                  <a-alert
                    :message="diagnosisData.interventionAlert"
                    type="warning"
                    show-icon
                    style="margin-top: 8px"
                  />
                </div>
              </div>
            </a-tab-pane>

            <!-- 行为处方 -->
            <a-tab-pane key="prescription" tab="行为处方">
              <div class="dx-grid">
                <!-- 左：当前处方 -->
                <div class="dx-card">
                  <h4 class="dx-card-title">当前处方</h4>

                  <div class="dx-subtitle">干预阶段</div>
                  <div class="phase-tags">
                    <a-tag
                      v-for="p in prescriptionData.phaseTags"
                      :key="p.label"
                      :color="p.active ? 'blue' : p.done ? 'green' : 'default'"
                    >
                      {{ p.done && !p.active ? '✓ ' : '' }}{{ p.label }}
                    </a-tag>
                  </div>
                  <div class="phase-info">
                    {{ prescriptionData.phase.current }} · {{ prescriptionData.phase.week }} / {{ prescriptionData.phase.total }}
                  </div>

                  <a-divider style="margin: 12px 0" />

                  <div class="dx-subtitle">目标行为</div>
                  <div class="task-list">
                    <div v-for="task in prescriptionData.targetBehaviors" :key="task.name" class="task-item">
                      <div class="task-header">
                        <span class="task-name">{{ task.name }}</span>
                        <span class="task-days" :style="{ color: getTaskColor(task.progress) }">{{ task.currentDays }}天</span>
                      </div>
                      <a-progress
                        :percent="task.progress"
                        :stroke-color="getTaskColor(task.progress)"
                        size="small"
                      />
                      <div class="task-target">目标：{{ task.target }}</div>
                    </div>
                  </div>

                  <a-divider style="margin: 12px 0" />

                  <div class="dx-subtitle">干预策略</div>
                  <div class="strategy-tags">
                    <a-tag v-for="s in prescriptionData.strategies" :key="s.label" :color="s.type">
                      {{ s.label }}
                    </a-tag>
                  </div>

                  <div style="margin-top: 16px; display: flex; gap: 8px">
                    <a-button type="primary" size="small">调整处方</a-button>
                    <a-button size="small">查看历史</a-button>
                  </div>
                </div>

                <!-- 右：AI建议 -->
                <div class="dx-card">
                  <h4 class="dx-card-title">AI 诊断建议</h4>

                  <div class="suggestion-list">
                    <div v-for="sug in aiDiagnosisSuggestions" :key="sug.id" class="suggestion-card" :class="'sug-' + sug.priority">
                      <div class="suggestion-header">
                        <span class="suggestion-title">{{ sug.title }}</span>
                        <a-tag :color="sug.priority === 'high' ? 'red' : 'blue'" size="small">
                          {{ sug.priority === 'high' ? '高优' : '中优' }}
                        </a-tag>
                      </div>
                      <div class="suggestion-message">{{ sug.content }}</div>
                      <div class="suggestion-actions">
                        <a-button type="primary" size="small" @click="message.success('已采纳建议：' + sug.title)">采纳</a-button>
                        <a-button size="small" @click="message.info('已标记参考')">参考</a-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>

          <!-- AI 教练共驾台 -->
          <div class="copilot-section" v-if="copilotVisible">
            <div class="copilot-header">
              <span class="copilot-title">AI 教练共驾台</span>
              <a-tag color="blue" size="small">实时分发中</a-tag>
              <a-button size="small" type="text" @click="copilotVisible = false" style="margin-left:auto">收起</a-button>
            </div>

            <!-- 用户阶段徽章 -->
            <div class="copilot-stage">
              <span class="stage-label">用户阶段:</span>
              <span class="user-stage-badge" :class="'stage-' + copilotState.currentStage">
                {{ copilotState.currentStage }}
              </span>
              <a-tag v-if="copilotState.stageChanged" color="green" size="small">刚迁移</a-tag>
            </div>

            <!-- 触发标签 -->
            <div v-if="copilotState.hitTags.length" class="copilot-tags">
              <a-tag v-for="tag in copilotState.hitTags" :key="tag"
                     :color="tag.includes('RESISTANCE') || tag.includes('HOPELESS') ? 'red' : tag.includes('EMO') ? 'orange' : 'green'"
                     size="small">
                {{ tag }}
              </a-tag>
            </div>

            <!-- 教练处方流 -->
            <div class="copilot-prescriptions">
              <div v-for="(item, idx) in copilotState.prescriptions" :key="idx"
                   class="copilot-rx-card">
                <div class="rx-header">
                  <span class="rx-dot" :class="'risk-' + item.risk_level"></span>
                  <span class="rx-risk">{{ item.risk_level }}</span>
                </div>
                <p class="rx-instruction">{{ item.instruction }}</p>
                <div class="rx-tool-area">
                  <p class="rx-tool-label">建议工具: {{ item.suggested_tool }}</p>
                  <!-- 动态工具组件 -->
                  <component
                    :is="toolMapper[item.suggested_tool]"
                    v-if="toolMapper[item.suggested_tool]"
                    v-bind="item.tool_props || {}"
                    class="dynamic-tool-wrapper"
                    @action="handleCopilotToolAction"
                  />
                  <div v-else class="rx-tool-fallback">
                    工具组件未定义: {{ item.suggested_tool }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 阶段迁移通知 -->
            <div v-if="copilotState.transitionEvent" class="copilot-transition">
              <a-alert
                type="success"
                show-icon
                :message="'阶段迁移: ' + copilotState.transitionEvent.from + ' → ' + copilotState.transitionEvent.to"
                :description="copilotState.transitionEvent.reason"
              />
            </div>

            <!-- 模式切换 -->
            <div class="copilot-mode-switch" style="margin-bottom: 10px;">
              <span style="font-size: 12px; color: #888; margin-right: 8px;">模式:</span>
              <a-radio-group v-model:value="copilotMode" size="small" button-style="solid">
                <a-radio-button value="live">生产</a-radio-button>
                <a-radio-button value="sandbox">沙盒</a-radio-button>
              </a-radio-group>
              <a-tag v-if="copilotMode === 'live'" color="green" size="small" style="margin-left: 8px;">8002</a-tag>
              <a-tag v-else color="orange" size="small" style="margin-left: 8px;">8003</a-tag>
            </div>

            <!-- 测试触发按钮 -->
            <div class="copilot-test">
              <a-select v-model:value="testMessage" style="width: 100%; margin-bottom: 8px" placeholder="选择模拟对话">
                <a-select-option value="我昨晚又没忍住吃了两大包薯片，现在好后悔。">情绪化进食</a-select-option>
                <a-select-option value="别跟我提减肥，我活得够累了，吃点东西怎么了？">抵触/防御</a-select-option>
                <a-select-option value="我打算下周一开始跑步，你觉得行吗？">行动意愿</a-select-option>
                <a-select-option value="今天老板开会骂了我，我觉得我这辈子都没希望了。">绝望/压力</a-select-option>
              </a-select>
              <a-button type="primary" block size="small" @click="triggerCopilotTest"
                        :loading="copilotLoading">
                模拟触发
              </a-button>
            </div>

            <!-- 空状态 -->
            <div v-if="!copilotState.hitTags.length && !copilotLoading" class="copilot-empty">
              等待用户对话... 命中触发规则后将实时显示教练处方
            </div>
          </div>
          <div v-else class="copilot-toggle">
            <a-button size="small" type="dashed" @click="copilotVisible = true">展开 AI 共驾台</a-button>
          </div>

          <!-- 跟进对话区域 -->
          <div v-if="followupMode" class="followup-section">
            <a-divider>跟进对话</a-divider>

            <!-- AI 生成的跟进建议 -->
            <div v-if="aiFollowupLoading" class="ai-generating">
              <a-spin size="small" /> AI 正在分析学员数据，生成跟进建议...
            </div>

            <div v-if="aiFollowupSuggestion && !aiFollowupLoading" class="ai-suggestion-box">
              <div class="suggestion-label">AI 生成的跟进内容：</div>
              <div class="suggestion-text">{{ aiFollowupSuggestion }}</div>
              <div class="suggestion-actions">
                <a-button size="small" type="primary" @click="followupText = aiFollowupSuggestion">采用此建议</a-button>
                <a-button size="small" @click="generateFollowup(currentStudent!)">重新生成</a-button>
              </div>
            </div>

            <!-- 快捷模板 -->
            <div class="template-section">
              <div class="template-label">快捷模板：</div>
              <div class="template-tags">
                <a-tag
                  v-for="tpl in followupTemplates"
                  :key="tpl.id"
                  class="template-tag"
                  @click="followupText = tpl.content.replace('{name}', currentStudent?.name || '')"
                >
                  {{ tpl.label }}
                </a-tag>
              </div>
            </div>

            <!-- 编辑发送区 -->
            <div class="followup-compose">
              <textarea
                v-model="followupText"
                class="followup-textarea"
                placeholder="编辑跟进消息..."
                rows="4"
              ></textarea>
              <div class="compose-actions">
                <a-button @click="generateFollowup(currentStudent!)">
                  <RobotOutlined /> AI 生成
                </a-button>
                <a-button type="primary" :disabled="!followupText.trim()" @click="sendFollowup(currentStudent!)">
                  发送跟进消息
                </a-button>
              </div>
            </div>

            <!-- 发送历史 -->
            <div v-if="followupHistory.length > 0" class="followup-history">
              <div class="history-label">本次跟进记录：</div>
              <div v-for="(msg, idx) in followupHistory" :key="idx" class="history-item">
                <div class="history-time">{{ msg.time }}</div>
                <div class="history-content">{{ msg.content }}</div>
                <a-tag :color="msg.source === 'ai' ? 'blue' : 'green'" size="small">{{ msg.source === 'ai' ? 'AI辅助' : '手动' }}</a-tag>
              </div>
            </div>
          </div>

          <div class="detail-actions">
            <a-button v-if="!followupMode" type="primary" block @click="startFollowup(currentStudent!)">
              开始跟进对话
            </a-button>
            <a-button v-else block @click="followupMode = false; followupHistory = []">
              结束跟进
            </a-button>
            <a-button style="margin-top:8px" block @click="openChallengeAssignDrawer(currentStudent!)">
              分配挑战
            </a-button>
          </div>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch, defineAsyncComponent, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  BellOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  AlertOutlined,
  MessageOutlined,
  TeamOutlined,
  RightOutlined,
  RobotOutlined,
  AppstoreOutlined,
  BookOutlined,
  HomeOutlined,
  UserOutlined,
  LogoutOutlined,
  DeleteOutlined,
  AuditOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const token = localStorage.getItem('admin_token')
const authHeaders = { Authorization: `Bearer ${token}` }

const loading = ref(false)

// 教练信息
const coachInfo = reactive({
  id: '',
  name: localStorage.getItem('admin_name') || '教练',
  avatar: '',
  level: 'L0',
  levelName: '见习教练',
  specialty: [] as string[]
})

const notifications = ref(0)

// 今日统计
const todayStats = reactive({
  pendingFollowups: 0,
  completedFollowups: 0,
  alertStudents: 0,
  unreadMessages: 0
})

// 待跟进学员 (从 API 加载)
const PAGE_SIZE = 30
const pendingStudents = ref<any[]>([])

// 四层诊断数据
const diagnosisData = reactive({
  spiScore: 72,
  successRate: 68,
  sixReasons: [
    { name: '知识不足', score: 35, max: 100, isWeak: true },
    { name: '技能欠缺', score: 50, max: 100, isWeak: true },
    { name: '动机不强', score: 65, max: 100, isWeak: false },
    { name: '环境障碍', score: 40, max: 100, isWeak: true },
    { name: '信念偏差', score: 55, max: 100, isWeak: false },
    { name: '习惯惯性', score: 70, max: 100, isWeak: false }
  ],
  psychLevels: [
    { label: '认知层', color: 'blue' },
    { label: '情绪层', color: 'orange' },
    { label: '动机层', color: 'green' },
    { label: '行为层', color: 'purple' }
  ],
  problem: '餐后血糖持续偏高，饮食控制不理想',
  difficulty: 3,
  purpose: '降低餐后血糖至10mmol/L以下，建立健康饮食习惯',
  evidence: [
    { label: '近7天餐后血糖均值', value: '11.2 mmol/L', status: 'danger' },
    { label: '饮食打卡完成率', value: '43%', status: 'warning' },
    { label: '运动执行率', value: '67%', status: 'normal' }
  ],
  interventionFormula: 'SPI = 0.4×行为执行 + 0.3×指标改善 + 0.2×知识掌握 + 0.1×态度转变',
  interventionAlert: '当前SPI低于80分，建议加强干预力度，重点关注饮食行为改变'
})

// 行为处方数据
const prescriptionData = reactive({
  phase: { current: '强化期', week: '第3周', total: '共8周' },
  phaseTags: [
    { label: '评估期', done: true },
    { label: '启动期', done: true },
    { label: '强化期', active: true },
    { label: '巩固期', done: false },
    { label: '维持期', done: false }
  ],
  targetBehaviors: [
    { name: '每餐主食减量1/3', progress: 60, target: '21天连续达标', currentDays: 13 },
    { name: '餐后30分钟散步', progress: 75, target: '21天连续达标', currentDays: 16 },
    { name: '每日血糖监测2次', progress: 85, target: '14天连续达标', currentDays: 12 }
  ],
  strategies: [
    { label: '动机访谈', type: 'blue' },
    { label: '行为契约', type: 'green' },
    { label: '同伴支持', type: 'orange' },
    { label: '奖励机制', type: 'purple' }
  ]
})

// AI诊断建议
const aiDiagnosisSuggestions = ref([
  {
    id: 'ads1',
    title: '调整饮食干预策略',
    content: '学员饮食打卡率低，建议从"减量"策略调整为"替换"策略，用低GI食物替代高GI食物，降低行为改变难度。',
    type: 'strategy',
    priority: 'high'
  },
  {
    id: 'ads2',
    title: '增加知识教育频次',
    content: '知识不足是当前主要薄弱项，建议每周推送2条碳水化合物与血糖关系的科普内容。',
    type: 'education',
    priority: 'medium'
  },
  {
    id: 'ads3',
    title: '引入同伴激励机制',
    content: '学员处于行动期但动力波动，建议匹配1位同阶段学员组成互助小组，提升坚持率。',
    type: 'social',
    priority: 'medium'
  }
])

// ── AI 教练共驾台 (CoachCopilot 双模式) ──
import copilotApi from '../../api/copilot'

const copilotMode = ref<'live' | 'sandbox'>('live')

const toolMapper: Record<string, any> = {
  "STRESS_ASSESSMENT_FORM": markRaw(defineAsyncComponent(() => import('./tools/StressForm.vue'))),
  "EMPATHY_MODULE_01": markRaw(defineAsyncComponent(() => import('./tools/EmpathyGuide.vue'))),
  "HABIT_DESIGNER": markRaw(defineAsyncComponent(() => import('./tools/HabitCard.vue'))),
  "GENERAL_CHAT": null,
}

const copilotVisible = ref(true)
const copilotLoading = ref(false)
const testMessage = ref('')
const copilotState = reactive({
  currentStage: 'S1',
  stageChanged: false,
  hitTags: [] as string[],
  prescriptions: [] as any[],
  transitionEvent: null as any,
  stateHistory: [] as any[],
})

const triggerCopilotAnalysis = async (msg: string, source: 'live' | 'sandbox') => {
  copilotLoading.value = true
  try {
    let data: any
    if (source === 'live') {
      // 生产模式: 通过 copilotApi 调用 8002
      const resp = await copilotApi.analyze({
        uid: currentStudent.value?.name || 'DEMO_USER',
        message: msg,
        context: { stage: copilotState.currentStage, baps: {} }
      })
      data = resp.data
    } else {
      // 沙盒模式: 保留原 fetch 8003 逻辑
      const resp = await fetch('http://localhost:8003/api/v1/test/simulate-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uid: currentStudent.value?.name || 'DEMO_USER',
          message: msg,
          context: { stage: copilotState.currentStage, baps: {} }
        })
      })
      data = await resp.json()
    }
    copilotState.hitTags = data.triggered_tags || []
    const coachData = data.outputs?.to_coach
    copilotState.prescriptions = Array.isArray(coachData) ? coachData : (coachData?.alerts || [])
    copilotState.transitionEvent = data.transition_event || null
    if (data.new_stage) {
      copilotState.stageChanged = data.new_stage !== copilotState.currentStage
      copilotState.currentStage = data.new_stage
    }
    if (data.state_history) copilotState.stateHistory = data.state_history
  } catch (e: any) {
    message.error('共驾台请求失败: ' + e.message)
  } finally {
    copilotLoading.value = false
  }
}

const triggerCopilotTest = async () => {
  if (!testMessage.value) { message.warning('请选择模拟对话'); return }
  await triggerCopilotAnalysis(testMessage.value, copilotMode.value)
}

const handleCopilotToolAction = (data: any) => {
  message.success('工具动作: ' + JSON.stringify(data))
}

// AI 推荐（含审核状态，从学员列表同步生成）
const aiRecommendations = ref<any[]>([])

// 干预工具
const interventionTools = ref([
  { id: 't1', icon: '📋', name: '评估量表' },
  { id: 't2', icon: '📚', name: '健康课程' },
  { id: 't3', icon: '🎯', name: '审核推送' },
  { id: 't4', icon: '💬', name: '建议模板' },
  { id: 't5', icon: '📊', name: '数据分析' },
  { id: 't6', icon: '🤖', name: 'AI 助手' },
  { id: 't7', icon: '✅', name: '推送审批' }
])

// 学习进度
const learningProgress = reactive({
  certProgress: 65,
  coursesCompleted: 8,
  coursesTotal: 12,
  examsPassed: 2,
  examsTotal: 3,
  caseCount: 15
})

// 抽屉状态
const studentDrawerVisible = ref(false)
const currentStudent = ref<typeof pendingStudents.value[0] | null>(null)
const assessmentDrawerVisible = ref(false)
const goalDrawerVisible = ref(false)
const profileDrawerVisible = ref(false)
const settingsDrawerVisible = ref(false)

// 分配挑战
const challengeAssignDrawerVisible = ref(false)
const challengeAssignStudent = ref<any>(null)
const loadingStudentChallenges = ref(false)
const studentChallenges = ref<any[]>([])
const loadingPublishedChallenges = ref(false)
const publishedChallenges = ref<any[]>([])
const assigningChallengeId = ref<number | null>(null)

// 推送审批队列
const pushQueueDrawerVisible = ref(false)
const pushQueueStats = reactive({ pending: 0, approved: 0, rejected: 0, sent: 0, expired: 0 })
const pushQueueFilter = reactive({ source_type: null as string | null, priority: null as string | null, status: 'pending' })
const loadingPushQueue = ref(false)
const pushQueueItems = ref<any[]>([])
const pushQueueTotal = ref(0)
const pushQueuePage = ref(1)
const selectedQueueIds = ref<number[]>([])
const batchApproving = ref(false)

// 推送评估表单
const assignForm = reactive({
  studentId: null as number | null,
  pushType: 'questions' as 'questions' | 'scales' | 'custom' | 'behavior',
  questionPreset: 'hf20' as string,
  questionIds: [] as string[],
  selectedQuestionIds: [] as string[],
  customQuestions: [''] as string[],
  scales: [] as string[],
  note: '',
})
// 行为评估题库
const allBuiltinQuestions = ref<any[]>([])
const loadingAllQuestions = ref(false)
const behaviorSearchText = ref('')
const scaleOptions = [
  { label: 'TTM7 行为阶段', value: 'ttm7' },
  { label: 'BIG5 大五人格', value: 'big5' },
  { label: 'BPT-6 行为类型', value: 'bpt6' },
  { label: 'CAPACITY 改变潜力', value: 'capacity' },
  { label: 'SPI 成功可能性', value: 'spi' },
]
const assignTotalItems = computed(() => {
  if (assignForm.pushType === 'questions') {
    return assignForm.questionPreset ? 1 : assignForm.questionIds.length
  }
  if (assignForm.pushType === 'behavior') {
    return assignForm.selectedQuestionIds.length > 0 ? 1 : 0
  }
  if (assignForm.pushType === 'custom') {
    return assignForm.customQuestions.filter(q => q.trim()).length > 0 ? 1 : 0
  }
  return assignForm.scales.length
})
const filteredBehaviorGroups = computed(() => {
  const groupMap: Record<string, { key: string; label: string; questions: any[] }> = {
    ttm7: { key: 'ttm7', label: 'TTM7 行为阶段', questions: [] },
    bpt6: { key: 'bpt6', label: 'BPT-6 行为类型', questions: [] },
    spi: { key: 'spi', label: 'SPI 成功可能性', questions: [] },
    capacity: { key: 'capacity', label: 'CAPACITY 改变潜力', questions: [] },
    big_five: { key: 'big_five', label: 'BIG5 大五人格', questions: [] },
  }
  const keyword = behaviorSearchText.value.trim().toLowerCase()
  for (const q of allBuiltinQuestions.value) {
    if (keyword && !q.text.toLowerCase().includes(keyword) && !q.id.toLowerCase().includes(keyword) && !q.dimension.toLowerCase().includes(keyword)) continue
    const g = groupMap[q.questionnaire]
    if (g) g.questions.push(q)
  }
  return Object.values(groupMap).filter(g => g.questions.length > 0)
})
const assignSubmitting = ref(false)
const loadingAssignments = ref(false)
const assignmentList = ref<any[]>([])
// 设备预警
const deviceAlerts = ref<any[]>([])
// AI推送建议
const pushRecommendations = ref<any[]>([])

// 审核与推送
const loadingReviewList = ref(false)
const reviewList = ref<any[]>([])
const reviewingAssignment = ref<any>(null)
const pushSubmitting = ref(false)

// 设置状态
const settingsState = reactive({
  notifications: true,
  alertReminder: true,
  autoAIPush: false,
  darkMode: false
})

// 方法
const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

const getLevelColor = (level: string) => {
  const colors: Record<string, string> = {
    'L0': 'default',
    'L1': 'blue',
    'L2': 'green',
    'L3': 'purple',
    'L4': 'gold'
  }
  return colors[level] || 'default'
}

const getStageLabel = (stage: string) => {
  const labels: Record<string, string> = {
    S0: '觉醒期', S1: '松动期', S2: '探索期', S3: '准备期',
    S4: '行动期', S5: '坚持期', S6: '融入期',
    precontemplation: '前意向期', contemplation: '意向期',
    preparation: '准备期', action: '行动期', maintenance: '维持期',
    unknown: '未评估',
  }
  return labels[stage] || stage
}

const getStageColor = (stage: string) => {
  const colors: Record<string, string> = {
    S0: 'default', S1: 'default', S2: 'blue', S3: 'cyan',
    S4: 'green', S5: 'purple', S6: 'gold',
    precontemplation: 'default', contemplation: 'blue',
    preparation: 'cyan', action: 'green', maintenance: 'purple',
    unknown: 'default',
  }
  return colors[stage] || 'default'
}

const openStudentDetail = (student: typeof pendingStudents.value[0]) => {
  currentStudent.value = student
  studentDrawerVisible.value = true
}

// 跟进对话
const followupMode = ref(false)
const followupText = ref('')
const aiFollowupSuggestion = ref('')
const aiFollowupLoading = ref(false)
const followupHistory = ref<Array<{ time: string; content: string; source: 'ai' | 'manual' }>>([])

const followupTemplates = [
  { id: 'care', label: '日常关怀', content: '{name}您好，最近身体感觉怎么样？血糖控制情况如何？有什么需要帮助的吗？' },
  { id: 'remind', label: '打卡提醒', content: '{name}您好，注意到您最近几天没有打卡记录，是遇到什么困难了吗？我们可以一起调整方案。' },
  { id: 'glucose', label: '血糖异常', content: '{name}您好，您近期的血糖数据有些波动，建议您注意饮食控制，特别是主食的摄入量。需要我为您调整饮食方案吗？' },
  { id: 'exercise', label: '运动鼓励', content: '{name}您好，本周运动量还不够目标哦。建议每天饭后散步15-30分钟，循序渐进，您看怎么样？' },
  { id: 'progress', label: '阶段进展', content: '{name}您好，您目前的各项指标都在改善中，继续保持！接下来我们的目标是进一步稳定血糖水平。' }
]

const startFollowup = (student: typeof pendingStudents.value[0]) => {
  if (!studentDrawerVisible.value) {
    currentStudent.value = student
    studentDrawerVisible.value = true
  }
  followupMode.value = true
  followupText.value = ''
  aiFollowupSuggestion.value = ''
  followupHistory.value = []
  // 自动生成AI建议
  generateFollowup(student)
}

const generateFollowup = async (student: typeof pendingStudents.value[0]) => {
  aiFollowupLoading.value = true
  aiFollowupSuggestion.value = ''

  const prompt = `你是一位专业的行为健康教练，请根据以下学员数据生成一条简短的跟进消息（100字以内），语气温暖专业：
学员：${student.name}
病情：${student.condition}
行为阶段：${getStageLabel(student.stage)}
空腹血糖：${student.healthData.fastingGlucose} mmol/L
餐后血糖：${student.healthData.postprandialGlucose} mmol/L
体重：${student.healthData.weight} kg
本周运动：${student.healthData.exerciseMinutes} 分钟
最近联系：${student.lastContact}
请直接输出跟进消息内容，不要加任何前缀。`

  try {
    const res = await fetch('http://127.0.0.1:8002/chat_sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: prompt, user_id: 'coach001' })
    })
    const data = await res.json()
    aiFollowupSuggestion.value = data.reply || '无法生成建议，请手动输入'
  } catch (e) {
    aiFollowupSuggestion.value = `${student.name}您好，注意到您最近的健康数据有些变化，想了解一下您的近况。有什么需要帮助的吗？`
  }
  aiFollowupLoading.value = false
}

const sendFollowup = async (student: typeof pendingStudents.value[0]) => {
  if (!followupText.value.trim()) return

  const now = new Date()
  const timeStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`

  // 调用真实 API 发送教练消息
  try {
    await fetch(`${API_BASE}/v1/coach/messages`, {
      method: 'POST',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: student.id,
        content: followupText.value,
        message_type: followupText.value === aiFollowupSuggestion.value ? 'advice' : 'text',
      }),
    })
  } catch { /* fallback: 即使 API 失败也更新本地状态 */ }

  // 添加到跟进历史
  followupHistory.value.push({
    time: timeStr,
    content: followupText.value,
    source: followupText.value === aiFollowupSuggestion.value ? 'ai' : 'manual'
  })

  // 添加到学员记录
  student.records.unshift({
    id: 'r-' + Date.now(),
    type: 'message',
    time: timeStr,
    content: followupText.value
  })

  message.success(`已发送跟进消息给 ${student.name}`)
  followupText.value = ''

  // 更新统计
  todayStats.completedFollowups++
  todayStats.pendingFollowups = Math.max(0, todayStats.pendingFollowups - 1)
}

// AI 建议审核操作
const approveRecommendation = (rec: typeof aiRecommendations.value[0]) => {
  rec.status = 'approved'
  message.success(`已批准推送给 ${rec.studentName}`)
}

const rejectRecommendation = (rec: typeof aiRecommendations.value[0]) => {
  rec.status = 'rejected'
  message.warning(`已驳回对 ${rec.studentName} 的建议`)
}

const confirmModify = (rec: typeof aiRecommendations.value[0]) => {
  if (!rec.modifiedText.trim()) {
    message.warning('请输入修正后的建议内容')
    return
  }
  rec.status = 'modified'
  rec.showModify = false
  message.success(`已修正并推送给 ${rec.studentName}`)
}

const viewDetail = (rec: typeof aiRecommendations.value[0]) => {
  const student = pendingStudents.value.find(s => s.name === rec.studentName)
  if (student) {
    openStudentDetail(student)
  }
}

// 干预工具
const openTool = (tool: typeof interventionTools.value[0]) => {
  switch (tool.id) {
    case 't1': // 评估量表
      assessmentDrawerVisible.value = true
      loadAssignmentList()
      break
    case 't2': // 健康课程
      router.push('/course/list')
      break
    case 't3': // 审核与推送
      goalDrawerVisible.value = true
      reviewingAssignment.value = null
      loadReviewList()
      break
    case 't4': // 建议模板
      router.push('/prompts/list')
      break
    case 't5': // 数据分析
      router.push('/dashboard')
      break
    case 't6': // AI 助手
      router.push('/client/chat')
      break
    case 't7': // 推送审批
      openPushQueueDrawer()
      break
  }
}

// 诊断UI辅助函数
const getBarColor = (score: number, max: number, isWeak: boolean) => {
  if (isWeak) return '#ff4d4f'
  const ratio = score / max
  if (ratio >= 0.7) return '#52c41a'
  if (ratio >= 0.4) return '#faad14'
  return '#ff4d4f'
}

const getDifficultyStars = (level: number) => {
  return '★'.repeat(level) + '☆'.repeat(5 - level)
}

const getTaskColor = (rate: number) => {
  if (rate >= 80) return '#52c41a'
  if (rate >= 50) return '#faad14'
  return '#ff4d4f'
}

const getNextStageGoal = (stage: string) => {
  const goals: Record<string, string> = {
    S0: '进入松动期：开始认识到改变的必要',
    S1: '进入探索期：了解改变的可能性',
    S2: '进入准备期：制定行动计划',
    S3: '进入行动期：开始执行方案',
    S4: '进入坚持期：稳定健康习惯',
    S5: '进入融入期：让健康成为生活方式',
    S6: '保持融入期：帮助他人成长',
    precontemplation: '进入意向期：建立健康意识',
    contemplation: '进入准备期：制定行动计划',
    preparation: '进入行动期：开始执行方案',
    action: '进入维持期：稳定健康习惯',
    maintenance: '保持维持期：长期坚持',
  }
  return goals[stage] || '持续改善'
}

// ============ 评估推送与审核 API ============

async function submitAssign() {
  if (!assignForm.studentId) { message.warning('请选择学员'); return }
  if (assignTotalItems.value === 0) { message.warning('请选择推送内容'); return }
  if (assignTotalItems.value > 3) { message.warning('推送项不能超过3项'); return }
  assignSubmitting.value = true
  try {
    const body: any = {
      student_id: assignForm.studentId,
      note: assignForm.note || undefined,
    }
    if (assignForm.pushType === 'questions') {
      body.question_preset = assignForm.questionPreset
    } else if (assignForm.pushType === 'behavior') {
      if (assignForm.selectedQuestionIds.length === 0) { message.warning('请至少选择一道题目'); assignSubmitting.value = false; return }
      body.question_ids = assignForm.selectedQuestionIds
    } else if (assignForm.pushType === 'custom') {
      const validQs = assignForm.customQuestions.filter(q => q.trim())
      if (validQs.length === 0) { message.warning('请至少输入一道题目'); assignSubmitting.value = false; return }
      body.custom_questions = validQs.map(q => ({ text: q.trim(), scale_type: 'likert5' }))
    } else {
      body.scales = assignForm.scales
    }
    const res = await fetch(`${API_BASE}/v1/assessment-assignments/assign`, {
      method: 'POST',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '推送失败')
    message.success(data.message || '评估已推送')
    assignForm.studentId = null
    assignForm.pushType = 'questions'
    assignForm.questionPreset = 'hf20'
    assignForm.questionIds = []
    assignForm.selectedQuestionIds = []
    assignForm.customQuestions = ['']
    assignForm.scales = []
    assignForm.note = ''
    loadAssignmentList()
  } catch (e: any) {
    message.error(e.message || '推送失败')
  } finally {
    assignSubmitting.value = false
  }
}

async function loadAssignmentList() {
  loadingAssignments.value = true
  try {
    // 加载教练的所有 assignment（复用 review-list 端点，显示所有状态）
    const res = await fetch(`${API_BASE}/v1/assessment-assignments/review-list`, {
      headers: authHeaders,
    })
    if (res.ok) {
      const data = await res.json()
      assignmentList.value = data.assignments || []
    }
  } catch { /* ignore */ }
  finally { loadingAssignments.value = false }
}

function openReviewDrawer(assignment: any) {
  reviewingAssignment.value = {
    ...assignment,
    review_items: (assignment.review_items || []).map((item: any) => ({
      ...item,
      _editing: false,
      _editText: '',
      _editNote: '',
    })),
  }
  assessmentDrawerVisible.value = false
  goalDrawerVisible.value = true
}

async function loadReviewList() {
  loadingReviewList.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/assessment-assignments/review-list`, {
      headers: authHeaders,
    })
    if (res.ok) {
      const data = await res.json()
      reviewList.value = data.assignments || []
    }
  } catch { /* ignore */ }
  finally { loadingReviewList.value = false }
}

function selectReviewAssignment(assignment: any) {
  reviewingAssignment.value = {
    ...assignment,
    review_items: (assignment.review_items || []).map((item: any) => ({
      ...item,
      _editing: false,
      _editText: '',
      _editNote: '',
    })),
  }
}

async function reviewItem(item: any, newStatus: string) {
  try {
    const res = await fetch(`${API_BASE}/v1/assessment-assignments/review-items/${item.id}`, {
      method: 'PUT',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    })
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '操作失败')
    }
    item.status = newStatus
    message.success(newStatus === 'approved' ? '已采纳' : '已拒绝')
  } catch (e: any) {
    message.error(e.message || '操作失败')
  }
}

async function confirmReviewModify(item: any) {
  if (!item._editText.trim()) { message.warning('请输入修改内容'); return }
  try {
    const coachContent = { ...item.original_content, modified_text: item._editText }
    const res = await fetch(`${API_BASE}/v1/assessment-assignments/review-items/${item.id}`, {
      method: 'PUT',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: 'modified',
        coach_content: coachContent,
        coach_note: item._editNote || undefined,
      }),
    })
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '操作失败')
    }
    item.status = 'modified'
    item.coach_content = coachContent
    item.coach_note = item._editNote
    item._editing = false
    message.success('已修改')
  } catch (e: any) {
    message.error(e.message || '操作失败')
  }
}

async function pushAssignment() {
  if (!reviewingAssignment.value) return
  pushSubmitting.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/assessment-assignments/${reviewingAssignment.value.id}/push`, {
      method: 'POST',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '推送失败')
    message.success(data.message || '已推送')
    reviewingAssignment.value = null
    loadReviewList()
    loadAssignmentList()
  } catch (e: any) {
    message.error(e.message || '推送失败')
  } finally {
    pushSubmitting.value = false
  }
}



const goToMessages = () => {
  router.push('/coach/messages')
}

const goToLearning = () => {
  router.push('/course/list')
}

const goToProfile = () => {
  profileDrawerVisible.value = true
}

// 下拉菜单
const handleMenuClick = ({ key }: { key: string }) => {
  switch (key) {
    case 'profile':
      profileDrawerVisible.value = true
      break
    case 'settings':
      settingsDrawerVisible.value = true
      break
    case 'logout':
      handleLogout()
      break
  }
}

const handleLogout = () => {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_username')
  localStorage.removeItem('admin_role')
  localStorage.removeItem('admin_level')
  localStorage.removeItem('admin_name')
  router.push('/login')
}

// ── 示例数据生成器 ──
function generateSampleStudents() {
  const names = [
    '张明华', '王小红', '李建国', '赵芳芳', '刘大伟', '陈晓丽', '杨志强', '黄丽萍',
    '周文博', '吴雅琴', '孙海涛', '马晓东', '朱秀英', '胡建华', '林美玲', '郭志远',
    '何晓燕', '高建平', '罗雪梅', '梁伟明', '谢丽娟', '宋志刚', '唐小芳', '韩大勇',
    '冯雅静', '曹明辉', '彭晓霞', '潘建文', '蒋美华', '邓志豪',
  ]
  const stages = ['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6']
  const conditions = [
    '2型糖尿病·饮食管理', '高血压·运动干预', '肥胖·综合管理', '失眠·睡眠行为调整',
    '焦虑·情绪管理', '慢性疼痛·行为康复', '代谢综合征·生活方式干预', '行为健康管理',
  ]
  const contactDays = ['今天', '1天前', '2天前', '3天前', '5天前', '7天前', '10天前']

  return names.map((name, i) => {
    const stage = stages[i % stages.length]
    const dayIdx = Math.min(i % 7, contactDays.length - 1)
    const daysNum = [0, 1, 2, 3, 5, 7, 10][dayIdx]
    let priority = 'low'
    if (daysNum >= 5 || stage === 'S0') priority = 'high'
    else if (daysNum >= 3 || stage === 'S1') priority = 'medium'

    return {
      id: 1000 + i,
      name,
      avatar: '',
      condition: conditions[i % conditions.length],
      stage,
      stageLabel: getStageLabel(stage),
      lastContact: contactDays[dayIdx],
      priority,
      healthData: {
        fastingGlucose: +(5.0 + Math.random() * 8).toFixed(1),
        postprandialGlucose: +(7.0 + Math.random() * 9).toFixed(1),
        weight: +(55 + Math.random() * 40).toFixed(1),
        exerciseMinutes: Math.floor(Math.random() * 90),
      },
      microAction7d: { completed: Math.floor(Math.random() * 7), total: 7 },
      riskFlags: daysNum >= 5 ? ['dropout_risk'] : [],
      records: [],
      interventionPlan: null,
      assessScore: 0,
      assessNote: '',
    }
  })
}

function generateAiRecommendations(students: any[]) {
  const templates = [
    { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}近3天血糖波动较大，建议进行电话跟进，了解饮食和用药情况` },
    { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}处于准备期，建议推送"运动入门指南"课程，强化行为改变动机` },
    { type: 'followup', typeLabel: '跟进提醒', tpl: (n: string) => `${n}已3天未打卡，建议发送关怀消息，了解近况` },
    { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}睡眠质量持续下降，建议关注情绪状态并调整睡眠干预方案` },
    { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}行为执行率较低，建议降低任务难度，采用渐进式目标设定` },
    { type: 'followup', typeLabel: '跟进提醒', tpl: (n: string) => `${n}上次评估已超过30天，建议推送高频快速评估` },
    { type: 'alert', typeLabel: '风险提醒', tpl: (n: string) => `${n}餐后血糖多次超过13.9mmol/L，建议立即电话了解饮食情况` },
    { type: 'intervention', typeLabel: '干预建议', tpl: (n: string) => `${n}已进入行动期但动力不足，建议引入同伴激励机制` },
  ]
  // 从高优先级学员中生成审核条目
  const candidates = students
    .filter(s => s.priority === 'high' || s.priority === 'medium')
    .slice(0, PAGE_SIZE)
  return candidates.map((s, i) => {
    const t = templates[i % templates.length]
    return {
      id: `ai${String(i + 1).padStart(3, '0')}`,
      type: t.type,
      typeLabel: t.typeLabel,
      studentName: s.name,
      suggestion: t.tpl(s.name),
      status: 'pending' as 'pending' | 'approved' | 'modified' | 'rejected',
      showModify: false,
      modifiedText: '',
    }
  })
}

async function loadDashboard() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/coach/dashboard`, { headers: authHeaders })
    if (!res.ok) throw new Error('Dashboard API failed')
    const data = await res.json()

    // 教练信息
    const c = data.coach || {}
    coachInfo.id = c.id || ''
    coachInfo.name = c.name || coachInfo.name
    coachInfo.level = c.level || 'L0'
    coachInfo.levelName = c.level_name || '见习教练'
    coachInfo.specialty = c.specialty || []

    // 今日统计
    const s = data.today_stats || {}
    todayStats.pendingFollowups = s.pending_followups || 0
    todayStats.completedFollowups = s.completed_followups || 0
    todayStats.alertStudents = s.alert_students || 0
    todayStats.unreadMessages = s.unread_messages || 0
    notifications.value = s.unread_messages || 0

    // 学员列表 → 适配前端字段名（限制 PAGE_SIZE）
    const rawStudents = (data.students || []).map((st: any) => ({
      id: st.id,
      name: st.name,
      avatar: st.avatar || '',
      condition: st.condition || '行为健康管理',
      stage: st.stage || 'unknown',
      stageLabel: st.stage_label || '未评估',
      lastContact: st.last_contact || '未知',
      priority: st.priority || 'low',
      healthData: {
        fastingGlucose: st.health_data?.fasting_glucose ?? null,
        postprandialGlucose: st.health_data?.postprandial_glucose ?? null,
        weight: st.health_data?.weight ?? null,
        exerciseMinutes: st.health_data?.exercise_minutes ?? 0,
      },
      microAction7d: st.micro_action_7d || { completed: 0, total: 0 },
      riskFlags: st.risk_flags || [],
      records: [],
      interventionPlan: null,
      assessScore: 0,
      assessNote: '',
    }))

    // API 有数据则使用，无数据则用示例
    if (rawStudents.length > 0) {
      pendingStudents.value = rawStudents.slice(0, PAGE_SIZE)
    } else {
      pendingStudents.value = generateSampleStudents().slice(0, PAGE_SIZE)
    }
  } catch (e) {
    console.warn('[CoachHome] Dashboard API 不可用，使用示例数据:', e)
    pendingStudents.value = generateSampleStudents().slice(0, PAGE_SIZE)
    todayStats.pendingFollowups = pendingStudents.value.filter(s => s.priority !== 'low').length
    todayStats.alertStudents = pendingStudents.value.filter(s => s.priority === 'high').length
    todayStats.unreadMessages = 5
  } finally {
    // 同步生成 AI 审核列表
    if (aiRecommendations.value.length === 0) {
      aiRecommendations.value = generateAiRecommendations(pendingStudents.value)
    }
    loading.value = false
  }
}

// 行为评估题库
async function loadAllBuiltinQuestions() {
  if (allBuiltinQuestions.value.length > 0) return
  loadingAllQuestions.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/high-freq-questions/all`, { headers: authHeaders })
    if (res.ok) {
      const data = await res.json()
      allBuiltinQuestions.value = data.questions || []
    }
  } catch { /* ignore */ }
  finally { loadingAllQuestions.value = false }
}

function toggleBehaviorQuestion(qid: string) {
  const idx = assignForm.selectedQuestionIds.indexOf(qid)
  if (idx >= 0) {
    assignForm.selectedQuestionIds.splice(idx, 1)
  } else if (assignForm.selectedQuestionIds.length < 3) {
    assignForm.selectedQuestionIds.push(qid)
  } else {
    message.warning('最多选择3道题目')
  }
}

function removeBehaviorQuestion(qid: string) {
  assignForm.selectedQuestionIds = assignForm.selectedQuestionIds.filter(id => id !== qid)
}

function getBehaviorQuestionLabel(qid: string) {
  const q = allBuiltinQuestions.value.find(q => q.id === qid)
  return q ? `[${qid}] ${q.text.slice(0, 15)}...` : qid
}

// AI推送建议
async function loadPushRecommendations() {
  try {
    const res = await fetch(`${API_BASE}/v1/push-recommendations`, { headers: authHeaders })
    if (res.ok) {
      const data = await res.json()
      pushRecommendations.value = data.recommendations || []
    }
  } catch { /* ignore */ }
}

function applyRecommendation(rec: any) {
  assignForm.studentId = rec.student_id
  if (rec.items?.length === 1 && rec.items[0].startsWith('hf')) {
    assignForm.pushType = 'questions'
    assignForm.questionPreset = rec.items[0]
  } else {
    assignForm.pushType = 'questions'
    assignForm.questionPreset = 'hf20'
  }
  message.info(`已预填 ${rec.student_name} 的推送建议`)
}

// 设备预警
async function loadDeviceAlerts() {
  try {
    const res = await fetch(`${API_BASE}/v1/alerts/coach?unread_only=true&limit=5`, { headers: authHeaders })
    if (res.ok) {
      const data = await res.json()
      deviceAlerts.value = data.alerts || []
    }
  } catch { /* ignore */ }
}

async function resolveAlert(alert: any) {
  try {
    await fetch(`${API_BASE}/v1/alerts/${alert.id}/resolve`, {
      method: 'POST',
      headers: authHeaders,
    })
    deviceAlerts.value = deviceAlerts.value.filter((a: any) => a.id !== alert.id)
    message.success('已处理预警')
  } catch { /* ignore */ }
}

// ============ 分配挑战 ============

function openChallengeAssignDrawer(student: any) {
  challengeAssignStudent.value = student
  challengeAssignDrawerVisible.value = true
  loadStudentChallenges(student.id)
  loadPublishedChallenges()
}

async function loadStudentChallenges(studentId: number) {
  loadingStudentChallenges.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/coach/challenges/students/${studentId}`, { headers: authHeaders })
    if (res.ok) {
      const data = await res.json()
      studentChallenges.value = data.enrollments || []
    } else {
      studentChallenges.value = []
    }
  } catch {
    studentChallenges.value = []
  } finally {
    loadingStudentChallenges.value = false
  }
}

async function loadPublishedChallenges() {
  if (publishedChallenges.value.length > 0) return
  loadingPublishedChallenges.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/challenges?status=published`, { headers: authHeaders })
    if (res.ok) {
      const data = await res.json()
      publishedChallenges.value = data.challenges || data || []
    }
  } catch { /* ignore */ }
  finally { loadingPublishedChallenges.value = false }
}

async function assignChallenge(challengeId: number) {
  if (!challengeAssignStudent.value) return
  assigningChallengeId.value = challengeId
  try {
    const res = await fetch(`${API_BASE}/v1/coach/challenges/assign`, {
      method: 'POST',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: challengeAssignStudent.value.id,
        challenge_id: challengeId,
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '分配失败')
    message.success(data.message || '已分配挑战')
    loadStudentChallenges(challengeAssignStudent.value.id)
  } catch (e: any) {
    message.error(e.message || '分配失败')
  } finally {
    assigningChallengeId.value = null
  }
}

// ============ 推送审批队列 ============

function openPushQueueDrawer() {
  pushQueueDrawerVisible.value = true
  loadPushQueueStats()
  loadPushQueueItems()
}

async function loadPushQueueStats() {
  try {
    const res = await fetch(`${API_BASE}/v1/coach/push-queue/stats`, { headers: authHeaders })
    if (res.ok) {
      const data = await res.json()
      Object.assign(pushQueueStats, data)
    }
  } catch { /* ignore */ }
}

async function loadPushQueueItems() {
  loadingPushQueue.value = true
  selectedQueueIds.value = []
  try {
    const params = new URLSearchParams()
    params.set('status', pushQueueFilter.status || 'pending')
    params.set('page', String(pushQueuePage.value))
    params.set('page_size', '20')
    if (pushQueueFilter.source_type) params.set('source_type', pushQueueFilter.source_type)
    if (pushQueueFilter.priority) params.set('priority', pushQueueFilter.priority)

    const res = await fetch(`${API_BASE}/v1/coach/push-queue?${params}`, { headers: authHeaders })
    if (res.ok) {
      const data = await res.json()
      pushQueueItems.value = (data.items || []).map((i: any) => ({
        ...i,
        _editing: false,
        _editContent: i.content || '',
        _editTime: null,
        student_name: getStudentName(i.student_id),
      }))
      pushQueueTotal.value = data.total || 0
    }
  } catch { /* ignore */ }
  finally { loadingPushQueue.value = false }
}

function getStudentName(studentId: number): string {
  const s = pendingStudents.value.find(st => st.id === studentId)
  return s ? s.name : `#${studentId}`
}

function sourceTagColor(t: string) {
  const m: Record<string, string> = { challenge: 'blue', device_alert: 'red', micro_action: 'green', ai_recommendation: 'purple', system: 'default' }
  return m[t] || 'default'
}

function sourceTagLabel(t: string) {
  const m: Record<string, string> = { challenge: '挑战', device_alert: '预警', micro_action: '微行动', ai_recommendation: 'AI', system: '系统' }
  return m[t] || t
}

function toggleQueueSelect(id: number) {
  const idx = selectedQueueIds.value.indexOf(id)
  if (idx >= 0) selectedQueueIds.value.splice(idx, 1)
  else selectedQueueIds.value.push(id)
}

async function approveQueueItem(item: any) {
  try {
    const res = await fetch(`${API_BASE}/v1/coach/push-queue/${item.id}/approve`, {
      method: 'POST',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '操作失败')
    message.success('已审批通过')
    loadPushQueueStats()
    loadPushQueueItems()
  } catch (e: any) {
    message.error(e.message || '操作失败')
  }
}

async function approveQueueItemWithEdit(item: any) {
  try {
    const body: any = {}
    if (item._editContent && item._editContent !== item.content) {
      body.content_override = item._editContent
    }
    if (item._editTime) {
      body.scheduled_time = typeof item._editTime === 'string' ? item._editTime : item._editTime.toISOString()
    }
    const res = await fetch(`${API_BASE}/v1/coach/push-queue/${item.id}/approve`, {
      method: 'POST',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '操作失败')
    message.success('已修改并审批通过')
    loadPushQueueStats()
    loadPushQueueItems()
  } catch (e: any) {
    message.error(e.message || '操作失败')
  }
}

async function rejectQueueItem(item: any) {
  try {
    const res = await fetch(`${API_BASE}/v1/coach/push-queue/${item.id}/reject`, {
      method: 'POST',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '操作失败')
    message.success('已拒绝')
    loadPushQueueStats()
    loadPushQueueItems()
  } catch (e: any) {
    message.error(e.message || '操作失败')
  }
}

async function batchApproveQueue() {
  if (selectedQueueIds.value.length === 0) return
  batchApproving.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/coach/push-queue/batch-approve`, {
      method: 'POST',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_ids: selectedQueueIds.value }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '操作失败')
    message.success(data.message || `已批量审批 ${data.approved_count} 条`)
    selectedQueueIds.value = []
    loadPushQueueStats()
    loadPushQueueItems()
  } catch (e: any) {
    message.error(e.message || '操作失败')
  } finally {
    batchApproving.value = false
  }
}

watch(() => assignForm.pushType, (val) => {
  if (val === 'behavior') loadAllBuiltinQuestions()
})

onMounted(() => {
  loadDashboard()
  loadPushRecommendations()
  loadDeviceAlerts()
  loadPushQueueStats()
})
</script>

<style scoped>
.coach-portal {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 70px;
}

/* 顶部导航 */
.portal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.greeting {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  color: #fff;
  font-size: 20px;
  cursor: pointer;
}

/* 概览区域 */
.overview-section {
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.overview-card {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s, transform 0.2s;
}

.overview-card.clickable {
  cursor: pointer;
}

.overview-card.clickable:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.card-icon.todo {
  background: #fff7e6;
  color: #fa8c16;
}

.card-icon.done {
  background: #f6ffed;
  color: #52c41a;
}

.card-icon.alert {
  background: #fff1f0;
  color: #f5222d;
}

.card-icon.message {
  background: #e6f7ff;
  color: #1890ff;
}

.card-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.card-label {
  font-size: 12px;
  color: #6b7280;
}

/* 学员列表 */
.students-section {
  padding: 0 16px 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.view-all {
  font-size: 13px;
  color: #667eea;
  display: flex;
  align-items: center;
  gap: 4px;
}

.student-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.student-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: transform 0.2s;
}

.student-card:active {
  transform: scale(0.98);
}

.student-avatar {
  position: relative;
}

.stage-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  white-space: nowrap;
  background: #e8e8e8;
  color: #666;
}

.stage-badge.action {
  background: #f6ffed;
  color: #52c41a;
}

.stage-badge.preparation {
  background: #e6fffb;
  color: #13c2c2;
}

.stage-badge.contemplation {
  background: #e6f7ff;
  color: #1890ff;
}

.student-info {
  flex: 1;
  min-width: 0;
}

.student-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.student-condition {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.student-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #9ca3af;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* AI 推荐 */
.ai-section {
  padding: 0 16px 16px;
}

.ai-recommendations {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.rec-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rec-type {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.rec-type.alert {
  background: #fff1f0;
  color: #f5222d;
}

.rec-type.intervention {
  background: #e6f7ff;
  color: #1890ff;
}

.rec-type.followup {
  background: #fff7e6;
  color: #fa8c16;
}

.rec-student {
  font-size: 13px;
  color: #6b7280;
}

.rec-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
}

.rec-actions {
  margin-top: 8px;
  display: flex;
  gap: 12px;
}

/* 干预工具 */
.intervention-section {
  padding: 0 16px 16px;
}

.intervention-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.tool-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: transform 0.2s;
}

.tool-card:active {
  transform: scale(0.95);
}

.tool-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.tool-name {
  font-size: 13px;
  color: #374151;
}

/* 学习进度 */
.learning-section {
  padding: 0 16px 16px;
}

.learning-progress {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.progress-item {
  margin-bottom: 12px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  color: #374151;
}

.progress-value {
  color: #667eea;
  font-weight: 600;
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 11px;
  color: #9ca3af;
}

/* 底部导航 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  display: flex;
  justify-content: space-around;
  padding: 8px 0;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 10px;
  color: #9ca3af;
  cursor: pointer;
  padding: 4px 12px;
}

.nav-item.active {
  color: #667eea;
}

.nav-item :deep(.anticon) {
  font-size: 20px;
}

/* 学员详情 */
.student-detail {
  padding: 16px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.detail-info h3 {
  margin: 0 0 4px;
  font-size: 18px;
}

.detail-info p {
  margin: 0 0 8px;
  color: #6b7280;
  font-size: 14px;
}

.health-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.metric-item {
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.followup-records {
  padding: 16px 0;
}

.record-item {
  padding: 4px 0;
}

.record-time {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.record-content {
  font-size: 14px;
  color: #374151;
}

.detail-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: #fff;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
}

/* AI 审核状态 */
.rec-approved { border-left: 3px solid #52c41a; }
.rec-rejected { border-left: 3px solid #ff4d4f; opacity: 0.6; }
.rec-modified { border-left: 3px solid #1890ff; }

.rec-ai-label { font-size: 11px; color: #9ca3af; margin-bottom: 4px; }

.rec-status { margin-left: auto; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.status-approved { background: #f6ffed; color: #52c41a; }
.status-rejected { background: #fff1f0; color: #ff4d4f; }
.status-modified { background: #e6f7ff; color: #1890ff; }

.rec-modify-area { margin-top: 10px; }
.modify-textarea {
  width: 100%; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 8px;
  font-size: 13px; resize: vertical; outline: none;
}
.modify-textarea:focus { border-color: #667eea; }
.modify-actions { margin-top: 8px; display: flex; gap: 8px; }

.rec-result { margin-top: 8px; padding: 8px 12px; border-radius: 8px; background: #fafafa; }
.result-text { font-size: 12px; }
.result-text.approved { color: #52c41a; }
.result-text.modified { color: #1890ff; }
.result-text.rejected { color: #ff4d4f; }

/* 评估量表 */
.assessment-panel { padding: 0 4px; }
.assessment-student-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.assess-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.assess-info { flex: 1; }
.assess-name { font-weight: 600; font-size: 15px; }
.assess-condition { font-size: 12px; color: #6b7280; }
.assess-metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 12px; }
.assess-metric { background: #f9fafb; padding: 8px 12px; border-radius: 8px; display: flex; justify-content: space-between; }
.assess-label { font-size: 12px; color: #6b7280; }
.assess-value { font-size: 13px; font-weight: 600; }
.text-danger { color: #ff4d4f; }
.text-normal { color: #52c41a; }
.assess-evaluation { border-top: 1px solid #f0f0f0; padding-top: 12px; }
.eval-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.eval-note { margin-top: 8px; }

/* 目标设定 */
.goal-panel { padding: 0 4px; }
.goal-student-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.goal-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.goal-name { font-weight: 600; flex: 1; }
.goal-items { margin-bottom: 12px; }
.goal-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.goal-label { font-size: 13px; color: #6b7280; }
.goal-value { font-size: 13px; font-weight: 500; color: #1f2937; }

/* 个人中心 */
.profile-panel { padding: 0 4px; }
.profile-card { text-align: center; padding: 24px 0; }
.profile-name { font-size: 20px; font-weight: 700; margin: 12px 0 8px; }
.profile-stats { display: flex; justify-content: space-around; padding: 16px 0; border-top: 1px solid #f0f0f0; border-bottom: 1px solid #f0f0f0; margin-bottom: 16px; }
.pstat { text-align: center; }
.pstat-val { font-size: 22px; font-weight: 700; color: #667eea; }
.pstat-label { font-size: 12px; color: #6b7280; }
.profile-section { margin-bottom: 20px; }
.profile-section h4 { font-size: 14px; font-weight: 600; margin-bottom: 10px; }
.specialty-tags { display: flex; gap: 8px; flex-wrap: wrap; }

/* 设置 */
.settings-panel { padding: 0 4px; }
.setting-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid #f5f5f5; font-size: 14px; }

/* 跟进对话 */
.followup-section { margin-top: 16px; }

.ai-generating {
  display: flex; align-items: center; gap: 8px;
  padding: 16px; background: #f0f5ff; border-radius: 8px;
  font-size: 13px; color: #667eea; margin-bottom: 12px;
}

.ai-suggestion-box {
  background: linear-gradient(135deg, #f0f5ff, #e6f7ff);
  border: 1px solid #bae7ff; border-radius: 12px;
  padding: 14px; margin-bottom: 12px;
}
.suggestion-label { font-size: 11px; color: #667eea; font-weight: 600; margin-bottom: 6px; }
.suggestion-text { font-size: 14px; color: #374151; line-height: 1.6; margin-bottom: 10px; }
.suggestion-actions { display: flex; gap: 8px; }

.template-section { margin-bottom: 12px; }
.template-label { font-size: 12px; color: #6b7280; margin-bottom: 8px; }
.template-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.template-tag { cursor: pointer; transition: all 0.2s; }
.template-tag:hover { color: #667eea; border-color: #667eea; }

.followup-compose { margin-bottom: 16px; }
.followup-textarea {
  width: 100%; padding: 10px 14px; border: 2px solid #e5e7eb; border-radius: 12px;
  font-size: 14px; resize: vertical; outline: none; line-height: 1.6;
  transition: border-color 0.2s;
}
.followup-textarea:focus { border-color: #667eea; }
.compose-actions { margin-top: 8px; display: flex; justify-content: flex-end; gap: 8px; }

.followup-history { margin-bottom: 80px; }
.history-label { font-size: 12px; color: #6b7280; margin-bottom: 8px; }
.history-item {
  background: #f9fafb; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
  display: flex; flex-direction: column; gap: 4px;
}
.history-time { font-size: 11px; color: #9ca3af; }
.history-content { font-size: 13px; color: #374151; line-height: 1.5; }

/* 诊断评估 & 行为处方 */
.dx-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 640px) {
  .dx-grid {
    grid-template-columns: 1fr;
  }
}

.dx-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f0;
}

.dx-card-title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  padding-bottom: 8px;
  border-bottom: 2px solid #667eea;
}

.dx-subtitle {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

/* SPI 圆圈 */
.spi-circle-wrap {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.spi-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 6px solid #d9d9d9;
  transition: border-color 0.3s;
}

.spi-circle.spi-good {
  border-color: #52c41a;
  background: #f6ffed;
}

.spi-circle.spi-mid {
  border-color: #faad14;
  background: #fffbe6;
}

.spi-circle.spi-low {
  border-color: #ff4d4f;
  background: #fff1f0;
}

.spi-number {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.spi-circle.spi-good .spi-number { color: #52c41a; }
.spi-circle.spi-mid .spi-number { color: #faad14; }
.spi-circle.spi-low .spi-number { color: #ff4d4f; }

.spi-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

/* 柱状条 */
.bar-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bar-source {
  margin-bottom: 2px;
}

.bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #374151;
  margin-bottom: 2px;
}

/* 信息框 */
.info-box {
  background: #f9fafb;
  border-radius: 8px;
  padding: 10px 12px;
}

.info-row {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.6;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  color: #6b7280;
  white-space: nowrap;
  min-width: 48px;
  font-weight: 500;
}

.info-value {
  color: #1f2937;
  flex: 1;
}

.formula-box {
  background: #f0f5ff;
  border: 1px solid #d6e4ff;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 12px;
  color: #1d39c4;
  line-height: 1.6;
  font-family: 'Courier New', monospace;
}

/* 循证依据 */
.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.evidence-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9fafb;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.evidence-label {
  color: #6b7280;
}

.evidence-value {
  font-weight: 600;
}

.ev-danger { color: #ff4d4f; }
.ev-warning { color: #faad14; }
.ev-normal { color: #52c41a; }

/* 心理层次 */
.level-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 处方阶段 */
.phase-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.phase-info {
  font-size: 13px;
  color: #667eea;
  font-weight: 500;
}

/* 任务列表 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  background: #f9fafb;
  border-radius: 8px;
  padding: 10px 12px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.task-name {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.task-days {
  font-size: 13px;
  font-weight: 600;
}

.task-target {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
}

/* 策略标签 */
.strategy-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* AI 建议卡片 */
.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-card {
  background: #f9fafb;
  border-radius: 10px;
  padding: 12px 14px;
  border-left: 3px solid #d9d9d9;
}

.suggestion-card.sug-high {
  border-left-color: #ff4d4f;
  background: #fff1f0;
}

.suggestion-card.sug-medium {
  border-left-color: #1890ff;
  background: #e6f7ff;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.suggestion-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.suggestion-message {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  margin-bottom: 10px;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
}

/* AI 教练共驾台 */
.copilot-section {
  margin-top: 16px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  padding: 16px;
  background: #fafbfc;
}
.copilot-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.copilot-title {
  font-weight: 700;
  font-size: 15px;
}
.copilot-stage {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
}
.stage-label { color: #888; }
.user-stage-badge {
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 13px;
}
.stage-S1 { background: #fff1f0; color: #cf1322; }
.stage-S2 { background: #fff7e6; color: #d46b08; }
.stage-S3 { background: #f6ffed; color: #389e0d; }
.copilot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}
.copilot-prescriptions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}
.copilot-rx-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}
.rx-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.rx-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.risk-L1 { background: #faad14; }
.risk-L2 { background: #ff4d4f; }
.risk-L3 { background: #cf1322; }
.rx-risk { font-size: 12px; font-weight: 600; }
.rx-instruction { font-size: 13px; color: #333; margin: 4px 0 8px; }
.rx-tool-area { border-top: 1px dashed #e8e8e8; padding-top: 8px; }
.rx-tool-label { font-size: 11px; color: #999; margin-bottom: 6px; }
.rx-tool-fallback { font-size: 11px; color: #fa8c16; background: #fff7e6; padding: 6px; border-radius: 4px; }
.copilot-transition { margin-bottom: 12px; }
.copilot-test {
  border-top: 1px solid #e8e8e8;
  padding-top: 12px;
  margin-top: 8px;
}
.copilot-empty {
  text-align: center;
  color: #bbb;
  font-size: 13px;
  padding: 20px 0;
}
.copilot-toggle { margin-top: 12px; text-align: center; }
</style>
