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

    <!-- 今日工作概览 -->
    <div class="overview-section">
      <div class="section-title">
        <CalendarOutlined /> 今日工作概览
      </div>
      <div class="overview-cards">
        <div class="overview-card">
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
        <div class="overview-card">
          <div class="card-icon alert"><AlertOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.alertStudents }}</div>
            <div class="card-label">需关注</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon message"><MessageOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.unreadMessages }}</div>
            <div class="card-label">未读消息</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 待跟进学员列表 -->
    <div class="students-section">
      <div class="section-header">
        <div class="section-title">
          <TeamOutlined /> 待跟进学员
        </div>
        <a class="view-all" @click="goToStudentList">查看全部 <RightOutlined /></a>
      </div>

      <div class="student-list">
        <div
          v-for="student in pendingStudents"
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
    <div class="ai-section">
      <div class="section-header">
        <div class="section-title">
          <RobotOutlined /> AI 干预建议审核
        </div>
        <span class="view-all">{{ aiRecommendations.filter(r => r.status === 'pending').length }} 条待审核</span>
      </div>

      <div class="ai-recommendations">
        <div
          v-for="rec in aiRecommendations"
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

    <!-- 干预包快捷入口 -->
    <div class="intervention-section">
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

    <!-- 学习进度 -->
    <div class="learning-section">
      <div class="section-header">
        <div class="section-title">
          <BookOutlined /> 我的学习
        </div>
        <a class="view-all">查看课程 <RightOutlined /></a>
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
      <div class="nav-item" @click="goToStudentList">
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

    <!-- 评估量表抽屉 -->
    <a-drawer
      v-model:open="assessmentDrawerVisible"
      title="学员评估量表"
      placement="right"
      width="100%"
      :closable="true"
    >
      <div class="assessment-panel">
        <div v-for="student in pendingStudents" :key="student.id" class="assessment-student-card">
          <div class="assess-header">
            <a-avatar :size="40">{{ student.name?.charAt(0) }}</a-avatar>
            <div class="assess-info">
              <div class="assess-name">{{ student.name }}</div>
              <div class="assess-condition">{{ student.condition }}</div>
            </div>
            <a-tag :color="getStageColor(student.stage)" size="small">{{ getStageLabel(student.stage) }}</a-tag>
          </div>
          <div class="assess-metrics">
            <div class="assess-metric">
              <span class="assess-label">空腹血糖</span>
              <span class="assess-value" :class="student.healthData.fastingGlucose > 7 ? 'text-danger' : 'text-normal'">{{ student.healthData.fastingGlucose }} mmol/L</span>
            </div>
            <div class="assess-metric">
              <span class="assess-label">餐后血糖</span>
              <span class="assess-value" :class="student.healthData.postprandialGlucose > 10 ? 'text-danger' : 'text-normal'">{{ student.healthData.postprandialGlucose }} mmol/L</span>
            </div>
            <div class="assess-metric">
              <span class="assess-label">体重</span>
              <span class="assess-value">{{ student.healthData.weight }} kg</span>
            </div>
            <div class="assess-metric">
              <span class="assess-label">运动量</span>
              <span class="assess-value">{{ student.healthData.exerciseMinutes }} 分/周</span>
            </div>
          </div>
          <div class="assess-evaluation">
            <div class="eval-title">综合评估</div>
            <a-rate v-model:value="student.assessScore" allow-half />
            <div class="eval-note">
              <a-input placeholder="评估备注..." size="small" v-model:value="student.assessNote" />
            </div>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 目标设定抽屉 -->
    <a-drawer
      v-model:open="goalDrawerVisible"
      title="学员目标设定"
      placement="right"
      width="100%"
      :closable="true"
    >
      <div class="goal-panel">
        <div v-for="student in pendingStudents" :key="student.id" class="goal-student-card">
          <div class="goal-header">
            <a-avatar :size="36">{{ student.name?.charAt(0) }}</a-avatar>
            <span class="goal-name">{{ student.name }}</span>
            <a-tag :color="getStageColor(student.stage)" size="small">{{ getStageLabel(student.stage) }}</a-tag>
          </div>
          <div class="goal-items">
            <div class="goal-item">
              <span class="goal-label">血糖目标</span>
              <span class="goal-value">空腹 &lt; 7.0 · 餐后 &lt; 10.0</span>
            </div>
            <div class="goal-item">
              <span class="goal-label">运动目标</span>
              <span class="goal-value">每周 150 分钟中等强度</span>
            </div>
            <div class="goal-item">
              <span class="goal-label">体重目标</span>
              <span class="goal-value">{{ Math.round(student.healthData.weight * 0.95) }} kg（减重5%）</span>
            </div>
            <div class="goal-item">
              <span class="goal-label">阶段目标</span>
              <span class="goal-value">{{ getNextStageGoal(student.stage) }}</span>
            </div>
          </div>
          <a-button type="primary" size="small" block @click="message.success(`已更新 ${student.name} 的目标`)">保存目标</a-button>
        </div>
      </div>
    </a-drawer>

    <!-- 个人中心抽屉 -->
    <a-drawer
      v-model:open="profileDrawerVisible"
      title="个人中心"
      placement="right"
      width="100%"
      :closable="true"
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
      width="100%"
      :closable="true"
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

    <!-- 学员详情抽屉 -->
    <a-drawer
      v-model:open="studentDrawerVisible"
      :title="currentStudent?.name"
      placement="right"
      width="100%"
      :closable="true"
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
                  <div class="metric-value">{{ currentStudent.healthData?.fastingGlucose || '--' }} mmol/L</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">餐后血糖</div>
                  <div class="metric-value">{{ currentStudent.healthData?.postprandialGlucose || '--' }} mmol/L</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">体重</div>
                  <div class="metric-value">{{ currentStudent.healthData?.weight || '--' }} kg</div>
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
          </div>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, defineAsyncComponent, markRaw } from 'vue'
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
  LogoutOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 教练信息
const coachInfo = reactive({
  id: 'coach001',
  name: localStorage.getItem('admin_name') || '李教练',
  avatar: '',
  level: 'L2',
  levelName: '中级教练',
  specialty: ['糖尿病逆转', '体重管理']
})

const notifications = ref(3)

// 今日统计
const todayStats = reactive({
  pendingFollowups: 8,
  completedFollowups: 5,
  alertStudents: 2,
  unreadMessages: 12
})

// 待跟进学员
const pendingStudents = ref([
  {
    id: 's001',
    name: '张明华',
    avatar: '',
    condition: '2型糖尿病 · 高血压',
    stage: 'action',
    lastContact: '2天前',
    priority: 'high',
    healthData: {
      fastingGlucose: 7.2,
      postprandialGlucose: 10.5,
      weight: 78,
      exerciseMinutes: 90
    },
    records: [
      { id: 'r1', type: 'call', time: '2024-01-23 14:30', content: '电话跟进，患者反馈血糖控制有所改善' },
      { id: 'r2', type: 'message', time: '2024-01-21 09:15', content: '发送饮食指导资料' }
    ],
    interventionPlan: {
      name: '血糖管理强化方案',
      description: '针对餐后血糖控制的个性化干预'
    },
    assessScore: 3.5,
    assessNote: ''
  },
  {
    id: 's002',
    name: '王小红',
    avatar: '',
    condition: '糖尿病前期 · 肥胖',
    stage: 'preparation',
    lastContact: '1天前',
    priority: 'medium',
    healthData: {
      fastingGlucose: 6.5,
      postprandialGlucose: 8.8,
      weight: 85,
      exerciseMinutes: 45
    },
    records: [
      { id: 'r3', type: 'message', time: '2024-01-24 10:00', content: '提醒完成今日运动任务' }
    ],
    interventionPlan: null,
    assessScore: 3,
    assessNote: ''
  },
  {
    id: 's003',
    name: '李建国',
    avatar: '',
    condition: '2型糖尿病',
    stage: 'contemplation',
    lastContact: '3天前',
    priority: 'low',
    healthData: {
      fastingGlucose: 8.1,
      postprandialGlucose: 12.3,
      weight: 72,
      exerciseMinutes: 30
    },
    records: [],
    interventionPlan: null,
    assessScore: 2,
    assessNote: ''
  }
])

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

// AI 推荐（含审核状态）
const aiRecommendations = ref([
  {
    id: 'ai001',
    type: 'alert',
    typeLabel: '风险提醒',
    studentName: '张明华',
    suggestion: '该学员近3天血糖波动较大，建议进行电话跟进，了解饮食和用药情况',
    status: 'pending' as 'pending' | 'approved' | 'modified' | 'rejected',
    showModify: false,
    modifiedText: ''
  },
  {
    id: 'ai002',
    type: 'intervention',
    typeLabel: '干预建议',
    studentName: '王小红',
    suggestion: '学员处于准备期，建议推送"运动入门指南"课程，强化行为改变动机',
    status: 'pending' as 'pending' | 'approved' | 'modified' | 'rejected',
    showModify: false,
    modifiedText: ''
  },
  {
    id: 'ai003',
    type: 'followup',
    typeLabel: '跟进提醒',
    studentName: '李建国',
    suggestion: '该学员已3天未打卡，建议发送关怀消息，了解近况',
    status: 'pending' as 'pending' | 'approved' | 'modified' | 'rejected',
    showModify: false,
    modifiedText: ''
  }
])

// 干预工具
const interventionTools = ref([
  { id: 't1', icon: '📋', name: '评估量表' },
  { id: 't2', icon: '📚', name: '健康课程' },
  { id: 't3', icon: '🎯', name: '目标设定' },
  { id: 't4', icon: '💬', name: '话术模板' },
  { id: 't5', icon: '📊', name: '数据分析' },
  { id: 't6', icon: '🤖', name: 'AI 助手' }
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
    precontemplation: '前意向期',
    contemplation: '意向期',
    preparation: '准备期',
    action: '行动期',
    maintenance: '维持期'
  }
  return labels[stage] || stage
}

const getStageColor = (stage: string) => {
  const colors: Record<string, string> = {
    precontemplation: 'default',
    contemplation: 'blue',
    preparation: 'cyan',
    action: 'green',
    maintenance: 'purple'
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

const sendFollowup = (student: typeof pendingStudents.value[0]) => {
  if (!followupText.value.trim()) return

  const now = new Date()
  const timeStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`

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
  todayStats.pendingFollowups--
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
      break
    case 't2': // 健康课程
      router.push('/course/list')
      break
    case 't3': // 目标设定
      goalDrawerVisible.value = true
      break
    case 't4': // 话术模板
      router.push('/prompts/list')
      break
    case 't5': // 数据分析
      router.push('/dashboard')
      break
    case 't6': // AI 助手
      router.push('/client/chat')
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
    precontemplation: '进入意向期：建立健康意识',
    contemplation: '进入准备期：制定行动计划',
    preparation: '进入行动期：开始执行方案',
    action: '进入维持期：稳定健康习惯',
    maintenance: '保持维持期：长期坚持'
  }
  return goals[stage] || '持续改善'
}

// 导航
const goToStudentList = () => {
  router.push('/student')
}

const goToMessages = () => {
  router.push('/student')
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

onMounted(() => {
  // 加载数据
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
  grid-template-columns: repeat(4, 1fr);
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
