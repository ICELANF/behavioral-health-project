<template>
  <view class="home-page">
    <!-- ═══ COACH / ADMIN 首页 ═══ -->
    <template v-if="userRole === 'coach' || userRole === 'admin'">
      <view class="home-header home-header--coach">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-date">{{ todayStr }}</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <view class="home-stats">
          <view class="home-stat-card home-stat-card--purple" @tap="goPage('/pages/coach/assessment/index')">
            <text class="home-stat-icon">📊</text>
            <text class="home-stat-num">{{ coachStats.pendingAssess }}</text>
            <text class="home-stat-label">待审评估</text>
          </view>
          <view class="home-stat-card home-stat-card--blue" @tap="goPage('/pages/coach/flywheel/index')">
            <text class="home-stat-icon">🤖</text>
            <text class="home-stat-num">{{ coachStats.pendingAiPlan }}</text>
            <text class="home-stat-label">待审AI计划</text>
          </view>
          <view class="home-stat-card home-stat-card--warn" @tap="goPage('/pages/coach/health-review/index')">
            <text class="home-stat-icon">🩺</text>
            <text class="home-stat-num">{{ coachStats.pendingHealthReview }}</text>
            <text class="home-stat-label">待审健康数据</text>
          </view>
          <view class="home-stat-card home-stat-card--green" @tap="goPage('/pages/coach/push-queue/index')">
            <text class="home-stat-icon">📤</text>
            <text class="home-stat-num">{{ coachStats.pendingRx }}</text>
            <text class="home-stat-label">待审处方</text>
          </view>
        </view>

        <!-- 第二行：晋级申请 + 内容投稿 -->
        <view class="home-stats" style="margin-top:0;">
          <view class="home-stat-card" style="border-left:4rpx solid #9B59B6;" @tap="goPage('/pages/coach/promotion/index')">
            <text class="home-stat-icon">🎖</text>
            <text class="home-stat-num">{{ coachStats.pendingPromotion }}</text>
            <text class="home-stat-label">待审晋级</text>
          </view>
          <view class="home-stat-card" style="border-left:4rpx solid #1ABC9C;" @tap="goPage('/pages/coach/contributions/index')">
            <text class="home-stat-icon">✍️</text>
            <text class="home-stat-num">{{ coachStats.pendingContributions }}</text>
            <text class="home-stat-label">待审投稿</text>
          </view>
        </view>

        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">📌 今日待办</text>
          </view>
          <view v-if="todos.length > 0" class="home-todo-list">
            <view v-for="(item, idx) in todos.slice(0,6)" :key="idx" class="home-todo-item" @tap="handleTodo(item)">
              <view class="home-todo-dot" :style="{ background: priorityColor(item.priority) }"></view>
              <view class="home-todo-body">
                <text class="home-todo-title">{{ item.title }}</text>
                <view class="home-todo-meta">
                  <view class="home-todo-tag" :style="{ background: todoTagBg(item.type) }">{{ item.type_label }}</view>
                  <text v-if="item.student_name" class="home-todo-student">{{ item.student_name }}</text>
                </view>
              </view>
              <text class="home-todo-arrow">›</text>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>✅ 今日无待办，继续保持！</text></view>
        </view>
        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">🔔 学员动态</text>
            <text class="home-section-more" @tap="goPage('/pages/coach/messages/index')">更多 ›</text>
          </view>
          <view v-if="activities.length > 0" class="home-activity-list">
            <view v-for="(a, idx) in activities.slice(0,6)" :key="idx" class="home-activity-item">
              <view class="home-activity-avatar" :style="{ background: avatarColor(a.student_name) }">{{ (a.student_name||'?')[0] }}</view>
              <view class="home-activity-body">
                <text class="home-activity-text"><text style="font-weight:600;">{{ a.student_name }}</text> {{ a.action_text || '完成了一项任务' }}</text>
                <text class="home-activity-time">{{ a.time_ago || '' }}</text>
              </view>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>暂无新动态</text></view>
        </view>
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <view class="home-shortcut" @tap="goPage('/pages/coach/flywheel/index')">
              <view class="home-sc-icon" style="background:#E8F4FD;">🤖</view>
              <text class="home-sc-label">AI跟进</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/students/index')">
              <view class="home-sc-icon" style="background:#EEF6FF;">👥</view>
              <text class="home-sc-label">学员管理</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/risk/index')">
              <view class="home-sc-icon" style="background:#FFF2F2;">🛡️</view>
              <text class="home-sc-label">风险管理</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/analytics/index')">
              <view class="home-sc-icon" style="background:#F0FFF8;">📈</view>
              <text class="home-sc-label">数据分析</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/health-review/index')">
              <view class="home-sc-icon" style="background:#FFF0E6;">🩺</view>
              <text class="home-sc-label">健康审核</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/push-queue/index')">
              <view class="home-sc-icon" style="background:#F0FFF0;">📤</view>
              <text class="home-sc-label">推送队列</text>
            </view>
          </view>
        </view>
        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>

    <!-- ═══ GROWER 首页 ═══ -->
    <template v-else-if="userRole === 'grower'">
      <view class="home-header home-header--grower">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-date">{{ todayStr }}</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <!-- 健康数据快览 -->
        <view class="home-health-cards">
          <view class="home-health-card" @tap="goPage('/pages/health/blood-glucose')">
            <text class="home-health-icon">🩸</text>
            <text class="home-health-val">{{ growerHealth.glucose || '—' }}</text>
            <text class="home-health-unit">mmol/L</text>
            <text class="home-health-label">血糖</text>
          </view>
          <view class="home-health-card" @tap="goPage('/pages/health/weight')">
            <text class="home-health-icon">⚖️</text>
            <text class="home-health-val">{{ growerHealth.weight || '—' }}</text>
            <text class="home-health-unit">kg</text>
            <text class="home-health-label">体重</text>
          </view>
          <view class="home-health-card" @tap="goPage('/pages/health/exercise')">
            <text class="home-health-icon">👟</text>
            <text class="home-health-val">{{ growerHealth.steps || '—' }}</text>
            <text class="home-health-unit">步</text>
            <text class="home-health-label">今日步数</text>
          </view>
        </view>

        <!-- 今日任务 -->
        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">📋 今日任务</text>
            <text class="home-section-more" @tap="goPage('/pages/journey/progress')">全部 ›</text>
          </view>
          <view v-if="growerTasks.length > 0">
            <view v-for="(t, i) in growerTasks.slice(0,4)" :key="i" class="home-task-item">
              <view class="home-task-check" :class="{ 'home-task-check--done': t.done }" @tap="toggleTask(t)">{{ t.done ? '✓' : '' }}</view>
              <text class="home-task-text" :class="{ 'home-task-text--done': t.done }">{{ t.title }}</text>
              <text class="home-task-pts">+{{ t.points || 10 }}分</text>
            </view>
            <view class="home-task-progress">
              <view class="home-task-bar">
                <view class="home-task-fill" :style="{ width: growerTaskProgress + '%' }"></view>
              </view>
              <text class="home-task-pct">{{ growerTaskProgress }}% 完成</text>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>📭 今日无任务，教练还未分配</text></view>
        </view>

        <!-- 今日用药提醒 banner -->
        <view class="home-med-banner" v-if="todayMedReminder" @tap="goPage('/pages/medical/index')">
          <text class="home-med-icon">💊</text>
          <view class="home-med-body">
            <text class="home-med-title">今日用药未记录</text>
            <text class="home-med-sub">{{ todayMedReminder }}</text>
          </view>
          <text class="home-med-arrow">›</text>
        </view>

        <!-- 体重记录提醒 banner -->
        <view class="home-weight-banner" v-if="weightDaysSince > 7" @tap="goPage('/pages/health/weight')">
          <text class="home-weight-icon">⚖️</text>
          <view class="home-weight-body">
            <text class="home-weight-title">{{ weightDaysSince >= 999 ? '还未记录过体重' : `已 ${weightDaysSince} 天未记录体重` }}</text>
            <text class="home-weight-sub">定期测量体重有助于追踪健康变化，点击记录</text>
          </view>
          <text class="home-weight-arrow">›</text>
        </view>

        <!-- 待完成评估 -->
        <view class="home-section" v-if="growerPendingAssess > 0">
          <view class="home-assess-banner" @tap="goPage('/pages/assessment/pending')">
            <text class="home-assess-icon">📝</text>
            <view class="home-assess-body">
              <text class="home-assess-title">您有 {{ growerPendingAssess }} 份评估待完成</text>
              <text class="home-assess-sub">教练已为您安排评估，完成后获得积分</text>
            </view>
            <text class="home-assess-arrow">›</text>
          </view>
        </view>

        <!-- 快捷入口 -->
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <view class="home-shortcut" @tap="goPage('/pages/health/blood-glucose')">
              <view class="home-sc-icon" style="background:#FFF0F5;">🩸</view>
              <text class="home-sc-label">记录血糖</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/food/scan')">
              <view class="home-sc-icon" style="background:#F0FFF4;">🥗</view>
              <text class="home-sc-label">记录饮食</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/health/exercise')">
              <view class="home-sc-icon" style="background:#EEF6FF;">🏃</view>
              <text class="home-sc-label">运动记录</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/learning/index')">
              <view class="home-sc-icon" style="background:#FFF8EE;">📚</view>
              <text class="home-sc-label">学习中心</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/reflection/index')">
              <view class="home-sc-icon" style="background:#F5F0FF;">📓</view>
              <text class="home-sc-label">成长感悟</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/medical/index')">
              <view class="home-sc-icon" style="background:#F0FFF8;">💊</view>
              <text class="home-sc-label">理性就医</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/trajectory/index')">
              <view class="home-sc-icon" style="background:#EEF9EE;">📈</view>
              <text class="home-sc-label">行为轨迹</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/companions/index')">
              <view class="home-sc-icon" style="background:#E8F8F0;">💬</view>
              <text class="home-sc-label">联系教练</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/become-sharer/index')">
              <view class="home-sc-icon" style="background:#FFF8EE;">🌟</view>
              <text class="home-sc-label">成为分享者</text>
            </view>
          </view>
        </view>

        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>

    <!-- ═══ SHARER 首页 ═══ -->
    <template v-else-if="userRole === 'sharer'">
      <view class="home-header home-header--sharer">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-role-badge">分享者</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

        <!-- 伙伴概览 -->
        <view class="home-stats">
          <view class="home-stat-card" @tap="goPage('/pages/sharer/mentees')">
            <text class="home-stat-icon">👥</text>
            <text class="home-stat-num">{{ sharerData.menteeCount }}</text>
            <text class="home-stat-label">我的伙伴</text>
          </view>
          <view class="home-stat-card home-stat-card--blue" @tap="goPage('/pages/sharer/mentees')">
            <text class="home-stat-icon">🔥</text>
            <text class="home-stat-num">{{ sharerData.activeToday }}</text>
            <text class="home-stat-label">今日活跃</text>
          </view>
          <view class="home-stat-card home-stat-card--purple" @tap="goPage('/pages/sharer/share-content')">
            <text class="home-stat-icon">📢</text>
            <text class="home-stat-num">{{ sharerData.published }}</text>
            <text class="home-stat-label">已发布</text>
          </view>
          <view class="home-stat-card home-stat-card--warn">
            <text class="home-stat-icon">⭐</text>
            <text class="home-stat-num">{{ sharerData.influence }}</text>
            <text class="home-stat-label">影响力</text>
          </view>
        </view>

        <!-- 伙伴动态 -->
        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">🔔 伙伴动态</text>
            <text class="home-section-more" @tap="goPage('/pages/sharer/mentees')">查看全部 ›</text>
          </view>
          <view v-if="sharerMentees.length > 0">
            <view v-for="m in sharerMentees.slice(0,3)" :key="m.id" class="home-activity-item">
              <view class="home-activity-avatar" :style="{ background: avatarColor(m.name) }">{{ (m.name||'?')[0] }}</view>
              <view class="home-activity-body">
                <text class="home-activity-text" style="font-weight:600;">{{ m.name }}</text>
                <text class="home-activity-time">连续打卡 {{ m.streak || 0 }} 天 · {{ m.status === 'active' ? '今日已打卡' : '未打卡' }}</text>
              </view>
              <text :style="{ color: m.status === 'active' ? '#27AE60' : '#E74C3C', fontSize: '24rpx' }">{{ m.today_pct || 0 }}%</text>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>暂无伙伴动态</text></view>
        </view>

        <!-- 健康数据快览 -->
        <view class="home-health-cards">
          <view class="home-health-card" @tap="goPage('/pages/health/blood-glucose')">
            <text class="home-health-icon">🩸</text>
            <text class="home-health-val">{{ growerHealth.glucose || '—' }}</text>
            <text class="home-health-unit">mmol/L</text>
            <text class="home-health-label">血糖</text>
          </view>
          <view class="home-health-card" @tap="goPage('/pages/health/weight')">
            <text class="home-health-icon">⚖️</text>
            <text class="home-health-val">{{ growerHealth.weight || '—' }}</text>
            <text class="home-health-unit">kg</text>
            <text class="home-health-label">体重</text>
          </view>
          <view class="home-health-card" @tap="goPage('/pages/health/exercise')">
            <text class="home-health-icon">👟</text>
            <text class="home-health-val">{{ growerHealth.steps || '—' }}</text>
            <text class="home-health-unit">步</text>
            <text class="home-health-label">今日步数</text>
          </view>
        </view>

        <!-- 今日任务 -->
        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">📋 今日任务</text>
            <text class="home-section-more" @tap="goPage('/pages/journey/progress')">全部 ›</text>
          </view>
          <view v-if="growerTasks.length > 0">
            <view v-for="(t, i) in growerTasks.slice(0,4)" :key="i" class="home-task-item">
              <view class="home-task-check" :class="{ 'home-task-check--done': t.done }" @tap="toggleTask(t)">{{ t.done ? '✓' : '' }}</view>
              <text class="home-task-text" :class="{ 'home-task-text--done': t.done }">{{ t.title }}</text>
              <text class="home-task-pts">+{{ t.points || 10 }}分</text>
            </view>
            <view class="home-task-progress">
              <view class="home-task-bar">
                <view class="home-task-fill" :style="{ width: growerTaskProgress + '%' }"></view>
              </view>
              <text class="home-task-pct">{{ growerTaskProgress }}% 完成</text>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>📭 今日无任务，教练还未分配</text></view>
        </view>

        <!-- 用药提醒 banner -->
        <view class="home-med-banner" v-if="todayMedReminder" @tap="goPage('/pages/medical/index')">
          <text class="home-med-icon">💊</text>
          <view class="home-med-body">
            <text class="home-med-title">今日用药未记录</text>
            <text class="home-med-sub">{{ todayMedReminder }}</text>
          </view>
          <text class="home-med-arrow">›</text>
        </view>

        <!-- 体重记录提醒 banner -->
        <view class="home-weight-banner" v-if="weightDaysSince > 7" @tap="goPage('/pages/health/weight')">
          <text class="home-weight-icon">⚖️</text>
          <view class="home-weight-body">
            <text class="home-weight-title">{{ weightDaysSince >= 999 ? '还未记录过体重' : `已 ${weightDaysSince} 天未记录体重` }}</text>
            <text class="home-weight-sub">定期测量体重有助于追踪健康变化，点击记录</text>
          </view>
          <text class="home-weight-arrow">›</text>
        </view>

        <!-- 待完成评估 -->
        <view class="home-section" v-if="growerPendingAssess > 0">
          <view class="home-assess-banner" @tap="goPage('/pages/assessment/pending')">
            <text class="home-assess-icon">📝</text>
            <view class="home-assess-body">
              <text class="home-assess-title">您有 {{ growerPendingAssess }} 份评估待完成</text>
              <text class="home-assess-sub">教练已为您安排评估，完成后获得积分</text>
            </view>
            <text class="home-assess-arrow">›</text>
          </view>
        </view>

        <!-- 快捷入口 -->
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <!-- 分享者专属 -->
            <view class="home-shortcut" @tap="goPage('/pages/sharer/mentees')">
              <view class="home-sc-icon" style="background:#EEF6FF;">👥</view>
              <text class="home-sc-label">我的伙伴</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/case-stories/index')">
              <view class="home-sc-icon" style="background:#FFF0E6;">🌿</view>
              <text class="home-sc-label">健康之路</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/sharer/share-content')">
              <view class="home-sc-icon" style="background:#E8F8F0;">✍️</view>
              <text class="home-sc-label">我的投稿</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/companions/invitations')">
              <view class="home-sc-icon" style="background:#F5EEFF;">📩</view>
              <text class="home-sc-label">同道邀请</text>
            </view>
            <!-- 成长者功能全保留 -->
            <view class="home-shortcut" @tap="goPage('/pages/health/blood-glucose')">
              <view class="home-sc-icon" style="background:#FFF0F5;">🩸</view>
              <text class="home-sc-label">记录血糖</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/food/scan')">
              <view class="home-sc-icon" style="background:#F0FFF4;">🥗</view>
              <text class="home-sc-label">记录饮食</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/health/exercise')">
              <view class="home-sc-icon" style="background:#EEF6FF;">🏃</view>
              <text class="home-sc-label">运动记录</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/learning/index')">
              <view class="home-sc-icon" style="background:#FFF8EE;">📚</view>
              <text class="home-sc-label">学习中心</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/reflection/index')">
              <view class="home-sc-icon" style="background:#F5F0FF;">📓</view>
              <text class="home-sc-label">成长感悟</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/medical/index')">
              <view class="home-sc-icon" style="background:#F0FFF8;">💊</view>
              <text class="home-sc-label">理性就医</text>
            </view>
            <!-- 分享者：同路由 /trajectory/index，角色感知内部渲染教练晋级进度 -->
            <view class="home-shortcut" @tap="goPage('/pages/trajectory/index')">
              <view class="home-sc-icon" style="background:#EDE9FE;">🎯</view>
              <text class="home-sc-label">教练之道</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/companions/index')">
              <view class="home-sc-icon" style="background:#E8F8F0;">💬</view>
              <text class="home-sc-label">联系教练</text>
            </view>
          </view>
        </view>
        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>

    <!-- ═══ SUPERVISOR 首页 ═══ -->
    <template v-else-if="userRole === 'supervisor'">
      <view class="home-header home-header--supervisor">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-role-badge">行为健康促进师</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <view class="home-stats">
          <view class="home-stat-card" @tap="goPage('/pages/supervisor/coaches')">
            <text class="home-stat-icon">👨‍🏫</text>
            <text class="home-stat-num">{{ supervisorData.coachCount }}</text>
            <text class="home-stat-label">管理教练</text>
          </view>
          <view class="home-stat-card home-stat-card--warn" @tap="goPage('/pages/supervisor/review-queue')">
            <text class="home-stat-icon">🔍</text>
            <text class="home-stat-num">{{ supervisorData.pendingReview }}</text>
            <text class="home-stat-label">待审健康</text>
          </view>
          <view class="home-stat-card" style="border-left:4rpx solid #8e24aa;" @tap="goPage('/pages/supervisor/promotion/index')">
            <text class="home-stat-icon">🎖</text>
            <text class="home-stat-num">{{ supervisorData.pendingPromotion }}</text>
            <text class="home-stat-label">待复核晋级</text>
          </view>
          <view class="home-stat-card home-stat-card--blue">
            <text class="home-stat-icon">✅</text>
            <text class="home-stat-num">{{ supervisorData.approvedToday }}</text>
            <text class="home-stat-label">今日审批</text>
          </view>
        </view>
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <view class="home-shortcut" @tap="goPage('/pages/supervisor/coaches')">
              <view class="home-sc-icon" style="background:#EEF6FF;">👨‍🏫</view>
              <text class="home-sc-label">教练管理</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/supervisor/review-queue')">
              <view class="home-sc-icon" style="background:#FFF0E6;">🔍</view>
              <text class="home-sc-label">健康审核</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/supervisor/promotion/index')">
              <view class="home-sc-icon" style="background:#F3E5F5;">🎖</view>
              <text class="home-sc-label">晋级复核</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/notifications/index')">
              <view class="home-sc-icon" style="background:#FFF8EE;">🔔</view>
              <text class="home-sc-label">消息中心</text>
            </view>
          </view>
        </view>
        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>

    <!-- ═══ MASTER 首页 ═══ -->
    <template v-else-if="userRole === 'master'">
      <view class="home-header home-header--master">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-role-badge">行为健康大师</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <view class="home-stats">
          <view class="home-stat-card home-stat-card--warn" @tap="goPage('/pages/master/critical-review')">
            <text class="home-stat-icon">🚨</text>
            <text class="home-stat-num">{{ masterData.critical }}</text>
            <text class="home-stat-label">危急病例</text>
          </view>
          <view class="home-stat-card home-stat-card--blue" @tap="goPage('/pages/master/dashboard')">
            <text class="home-stat-icon">🤖</text>
            <text class="home-stat-num">{{ masterData.aiPending }}</text>
            <text class="home-stat-label">AI分析待审</text>
          </view>
          <view class="home-stat-card home-stat-card--purple" @tap="goPage('/pages/master/knowledge')">
            <text class="home-stat-icon">📚</text>
            <text class="home-stat-num">{{ masterData.knowledgePending }}</text>
            <text class="home-stat-label">知识待发布</text>
          </view>
          <view class="home-stat-card" style="border-left:4rpx solid #b8860b;" @tap="goPage('/pages/master/promotion/index')">
            <text class="home-stat-icon">👑</text>
            <text class="home-stat-num">{{ masterData.pendingPromotion }}</text>
            <text class="home-stat-label">待终审晋级</text>
          </view>
          <view class="home-stat-card">
            <text class="home-stat-icon">✅</text>
            <text class="home-stat-num">{{ masterData.reviewedToday }}</text>
            <text class="home-stat-label">今日审核</text>
          </view>
        </view>
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <view class="home-shortcut" @tap="goPage('/pages/master/critical-review')">
              <view class="home-sc-icon" style="background:#FFF2F2;">🚨</view>
              <text class="home-sc-label">危急审核</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/master/promotion/index')">
              <view class="home-sc-icon" style="background:#FFF8DC;">👑</view>
              <text class="home-sc-label">晋级终审</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/master/knowledge')">
              <view class="home-sc-icon" style="background:#F5F0FF;">📚</view>
              <text class="home-sc-label">知识库</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/analytics/index')">
              <view class="home-sc-icon" style="background:#F0FFF4;">📊</view>
              <text class="home-sc-label">数据概览</text>
            </view>
          </view>
        </view>
        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@/compat/uni'
import { httpReq as http } from '@/api/request'
import { avatarColor, parseRisk } from '@/utils/studentUtils'

// ── 通用 ──────────────────────────────────────────────
const userRole = ref('coach')
const userName = ref('用户')
const refreshing = ref(false)

const greetText = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了,'
  if (h < 12) return '早上好,'
  if (h < 14) return '中午好,'
  if (h < 18) return '下午好,'
  return '晚上好,'
})

const todayStr = computed(() => {
  const d = new Date()
  const wds = ['日','一','二','三','四','五','六']
  return `${d.getMonth()+1}月${d.getDate()}日 周${wds[d.getDay()]}`
})

function detectRole() {
  try {
    const raw = uni.getStorageSync('user_info')
    if (raw) {
      const u = typeof raw === 'string' ? JSON.parse(raw) : raw
      userRole.value = (u.role || 'coach').toLowerCase()
      userName.value = u.full_name || u.display_name || u.username || '用户'
    }
  } catch (e) { console.warn('[home/index] detectRole:', e) }
}

function goPage(url: string) { uni.navigateTo({ url }) }
function priorityColor(p: string): string {
  const m: Record<string,string> = { urgent:'#E74C3C', high:'#E67E22', normal:'#3498DB', low:'#27AE60' }
  return m[p] || '#8E99A4'
}

// ── COACH 数据 ─────────────────────────────────────────
const coachStats = ref({ pendingAssess:0, pendingAiPlan:0, pendingHealthReview:0, pendingRx:0, pendingPromotion:0, pendingContributions:0 })
const todos = ref<any[]>([])
const activities = ref<any[]>([])

async function loadCoach() {
  // ─── 并行加载全部数据源 ──────────────────────────────────────
  const [dashRes, assessRes, aiRes, healthRes, rxRes, learningRes, examRes, promoRes, contribRes] =
    await Promise.allSettled([
      http<any>('/api/v1/coach/dashboard'),
      http<any>('/api/v1/assessment-assignments/coach-list?status=completed'),
      http<any>('/api/v1/coach/review-queue?status=pending'),
      http<any>('/api/v1/health-review/queue?reviewer_role=coach'),
      http<any>('/api/v1/coach/push-queue?status=pending&page_size=20'),
      http<any>('/api/v1/learning/my?status=in_progress&limit=3'),
      http<any>('/api/v1/certification/exams'),
      http<any>('/api/v1/promotion/applications?status=pending'),
      http<any>('/api/v1/contributions/review/pending'),
    ])

  const ok = <T>(r: PromiseSettledResult<T>, fallback: T): T =>
    r.status === 'fulfilled' ? r.value : fallback

  const dash      = ok(dashRes,     {} as any)
  const assessD   = ok(assessRes,   {} as any)
  const aiD       = ok(aiRes,       {} as any)
  const healthD   = ok(healthRes,   {} as any)
  const rxD       = ok(rxRes,       {} as any)
  const learningD = ok(learningRes, {} as any)
  const examD     = ok(examRes,     {} as any)
  const promoD    = ok(promoRes,    {} as any)
  const contribD  = ok(contribRes,  {} as any)

  // ─── 学员动态 ─────────────────────────────────────────────────
  const students: any[] = dash.students || []
  activities.value = students.slice(0, 10).map((s: any) => ({
    student_name: s.name || s.full_name || s.username || '未知',
    action_text: s.micro_action_count
      ? `完成了${s.micro_action_count}个微行动`
      : (s.days_since_last_contact === 0 ? '今天活跃' : `${s.days_since_last_contact ?? '?'}天未活跃`),
    time_ago: s.last_active_time || '',
  }))

  // ─── 4张卡数量 ────────────────────────────────────────────────
  const assessItems: any[] = assessD.items || assessD.assignments || (Array.isArray(assessD) ? assessD : [])
  const aiItems:     any[] = aiD.items || []
  const healthItems: any[] = healthD.items || healthD.queue || (Array.isArray(healthD) ? healthD : [])
  const rxItems:     any[] = rxD.items || []

  coachStats.value.pendingAssess        = assessItems.length
  coachStats.value.pendingAiPlan        = aiD.total_pending ?? aiItems.length
  coachStats.value.pendingHealthReview  = healthD.total ?? healthItems.length
  coachStats.value.pendingRx            = rxD.total ?? rxItems.length
  coachStats.value.pendingPromotion     = promoD.total ?? (promoD.applications || []).length
  coachStats.value.pendingContributions = contribD.total ?? (contribD.data || []).length

  // ─── 今日待办（三方案合并） ────────────────────────────────────
  const todoList: any[] = []

  // 【方案2】紧急审核 — 任意队列中 priority=urgent 的条目优先浮出
  aiItems.filter((i: any) => i.priority === 'urgent').slice(0, 2).forEach((i: any) => {
    todoList.push({
      id: 'urg_' + i.id,
      title: `${i.student_name || '学员'} 的AI跟进计划急需审核`,
      student_name: i.student_name || '',
      type: 'urgent', type_label: '紧急审核', priority: 'urgent',
      url: '/coach/flywheel/index',
    })
  })

  // 【方案1】重点学员 — R3高危 或 连续3天以上未联系
  students
    .map((s: any) => ({
      ...s,
      _rl: parseRisk(s.risk_level),
    }))
    .filter(s => s._rl >= 3 || (s.days_since_last_contact ?? 0) >= 3)
    .sort((a, b) => b._rl - a._rl)
    .slice(0, 3)
    .forEach(s => {
      const days = s.days_since_last_contact ?? 0
      todoList.push({
        id: 'stu_' + s.id,
        title: s._rl >= 3
          ? `${s.name} — R${s._rl} 高危，建议立即跟进`
          : `${s.name} — 已 ${days} 天未联系`,
        student_name: s.name || '',
        type: s._rl >= 3 ? 'high_risk' : 'inactive',
        type_label: s._rl >= 3 ? '高危学员' : '长期未联系',
        priority: s._rl >= 3 ? 'urgent' : 'high',
        url: '/coach/students/detail?id=' + s.id,
      })
    })

  // 【方案4】我的成长 — 在途学习课程（最多1条）
  const learningItems: any[] = learningD.items || []
  if (learningItems.length) {
    const l = learningItems[0]
    todoList.push({
      id: 'learn_' + l.id,
      title: `继续学习：${l.title || '培训课程'}`,
      student_name: '',
      type: 'learning', type_label: '我的学习', priority: 'normal',
      url: '/learning/index',
    })
  }

  // 【方案4】我的成长 — 近期考试提醒（最多1条）
  const examItems: any[] = examD.items || []
  if (examItems.length) {
    const e = examItems[0]
    todoList.push({
      id: 'exam_' + e.exam_id,
      title: `备考提醒：${e.exam_name || '教练认证考试'}`,
      student_name: '',
      type: 'exam', type_label: '考试备考', priority: 'normal',
      url: '/exam/list',
    })
  }

  todos.value = todoList.slice(0, 6)
}

function handleTodo(item: any) {
  uni.navigateTo({ url: item.url || '/pages/coach/flywheel/index' })
}

function todoTagBg(type: string): string {
  const m: Record<string, string> = {
    urgent:        '#FDEDEC',
    high_risk:     '#FDEDEC',
    inactive:      '#FFF3E0',
    learning:      '#EBF5FB',
    exam:          '#F5EEF8',
    assessment:    '#EAF4FB',
    ai_plan:       '#E8F8F5',
    health:        '#FEF9E7',
    rx_push:       '#EAFAF1',
  }
  return m[type] || '#F5F5F5'
}

// ── GROWER 数据 ────────────────────────────────────────
const growerHealth = ref<any>({ glucose: null, weight: null, steps: null })
const growerTasks = ref<any[]>([])
const growerPendingAssess = ref(0)
const todayMedReminder = ref('')   // 今日未打卡用药提醒文字
const weightDaysSince = ref(-1)    // -1=未知; 0=今日; 8+=超7天未记录

const growerTaskProgress = computed(() => {
  if (!growerTasks.value.length) return 0
  const done = growerTasks.value.filter(t => t.done).length
  return Math.round((done / growerTasks.value.length) * 100)
})

async function loadGrower() {
  try {
    const res = await http<any>('/api/v1/health-data/summary')
    growerHealth.value = {
      glucose: res.latest_glucose?.value?.toFixed(1) ?? null,
      weight:  res.latest_weight_kg?.toFixed(1) ?? null,
      steps:   res.steps_today ?? null,
    }
  } catch (e) { console.warn('[home/index] summary:', e) }
  try {
    const res = await http<any>('/api/v1/daily-tasks/today')
    growerTasks.value = (res.tasks || []).map((t: any) => ({
      id: t.id, title: t.title || t.description || '任务',
      done: t.status === 'completed' || t.completed === true,
      points: t.points || 10,
    }))
  } catch (e) { console.warn('[home/index] today:', e) }
  try {
    const res = await http<any>('/api/v1/assessment-assignments/my-pending')
    growerPendingAssess.value = (res.items || res.assignments || []).length
  } catch (e) { console.warn('[home/index] my-pending:', e) }

  // 今日用药提醒：reminder_time 已过且今日未打卡
  try {
    const medRes = await http<any>('/api/v1/medical/medications?active_only=true')
    const meds: any[] = medRes.items || medRes.medications || []
    const now = new Date()
    const nowMin = now.getHours() * 60 + now.getMinutes()
    const due = meds.filter((m: any) => {
      if (!m.reminder_time) return false
      const parts = (m.reminder_time as string).slice(0, 5).split(':').map(Number)
      return parts[0] * 60 + parts[1] <= nowMin && !m.taken_today
    })
    todayMedReminder.value = due.length
      ? due.map((m: any) => m.name).join('、') + ' 今日未记录'
      : ''
  } catch { todayMedReminder.value = '' }
  // 体重记录提醒：距上次记录天数
  try {
    const vRes = await http<any>('/api/v1/health-data/vitals?data_type=weight&limit=1&days=365')
    const items: any[] = vRes.items || vRes || []
    if (items.length) {
      const lastAt = new Date(items[0].recorded_at)
      const diffMs = Date.now() - lastAt.getTime()
      weightDaysSince.value = Math.floor(diffMs / 86400000)
    } else {
      weightDaysSince.value = 999  // 从未记录
    }
  } catch { weightDaysSince.value = -1 }
}

async function toggleTask(task: any) {
  if (task.done) return
  try {
    await http(`/api/v1/daily-tasks/${task.id}/checkin`, { method: 'POST', data: {} })
    task.done = true
    uni.showToast({ title: `+${task.points}分`, icon: 'success' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

// ── SHARER 数据 ────────────────────────────────────────
const sharerData = ref({ menteeCount:0, activeToday:0, published:0, influence:0 })
const sharerMentees = ref<any[]>([])

async function loadSharer() {
  try {
    const res = await http<any>('/api/v1/sharer/mentee-progress')
    sharerMentees.value = res.mentees || []
    sharerData.value.menteeCount = sharerMentees.value.length
    sharerData.value.activeToday = sharerMentees.value.filter((m: any) => m.status === 'active').length
  } catch (e) { console.warn('[home/index] mentee-progress:', e) }
  try {
    const res = await http<any>('/api/v1/sharer/contribution-stats')
    sharerData.value.published = res.published ?? 0
  } catch (e) { console.warn('[home/index] contribution-stats:', e) }
  try {
    const res = await http<any>('/api/v1/sharer/influence-score')
    sharerData.value.influence = res.total ?? 0
  } catch (e) { console.warn('[home/index] influence-score:', e) }
}

// ── SUPERVISOR 数据 ────────────────────────────────────
const supervisorData = ref({ coachCount:0, pendingReview:0, highRisk:0, approvedToday:0, pendingPromotion:0 })

async function loadSupervisor() {
  const [dashRes, promoRes] = await Promise.allSettled([
    http<any>('/api/v1/supervisor/dashboard'),
    http<any>('/api/v1/promotion/applications?status=pending'),
  ])
  if (dashRes.status === 'fulfilled') {
    const res = dashRes.value
    supervisorData.value = {
      coachCount:       res.coach_count ?? 0,
      pendingReview:    res.pending_review ?? 0,
      highRisk:         res.high_risk_count ?? 0,
      approvedToday:    res.approved_today ?? 0,
      pendingPromotion: 0,
    }
  }
  if (promoRes.status === 'fulfilled') {
    const apps = (promoRes.value as any).applications || []
    supervisorData.value.pendingPromotion = apps.filter((a: any) => a.review_stage === 'L2').length
  }
}

// ── MASTER 数据 ────────────────────────────────────────
const masterData = ref({ critical:0, aiPending:0, knowledgePending:0, reviewedToday:0, pendingPromotion:0 })

async function loadMaster() {
  const [dashRes, promoRes] = await Promise.allSettled([
    http<any>('/api/v1/master/dashboard'),
    http<any>('/api/v1/promotion/applications?status=pending'),
  ])
  if (dashRes.status === 'fulfilled') {
    const res = dashRes.value
    masterData.value = {
      critical:         res.critical_count ?? 0,
      aiPending:        res.ai_pending ?? 0,
      knowledgePending: res.knowledge_pending ?? 0,
      reviewedToday:    res.reviewed_today ?? 0,
      pendingPromotion: 0,
    }
  }
  if (promoRes.status === 'fulfilled') {
    const apps = (promoRes.value as any).applications || []
    masterData.value.pendingPromotion = apps.filter((a: any) => a.review_stage === 'L3').length
  }
}

// ── 主加载 ─────────────────────────────────────────────
async function loadData() {
  detectRole()
  if (userRole.value === 'coach' || userRole.value === 'admin') await loadCoach()
  else if (userRole.value === 'grower')     await loadGrower()
  else if (userRole.value === 'sharer')     { await loadSharer(); await loadGrower() }
  else if (userRole.value === 'supervisor') await loadSupervisor()
  else if (userRole.value === 'master')     await loadMaster()
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

onShow(() => { loadData() })
</script>

<style scoped>
.home-page { min-height: 100vh; background: #F5F6FA; }

/* 顶部 Header - 角色色 */
.home-header {
  padding: 24rpx 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  color: #fff; display: flex; justify-content: space-between; align-items: flex-end;
}
.home-header--coach      { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); }
.home-header--grower     { background: linear-gradient(135deg, #27AE60 0%, #2ECC71 100%); }
.home-header--sharer     { background: linear-gradient(135deg, #2980B9 0%, #3498DB 100%); }
.home-header--supervisor { background: linear-gradient(135deg, #D35400 0%, #E67E22 100%); }
.home-header--master     { background: linear-gradient(135deg, #7D3C98 0%, #9B59B6 100%); }

.home-greeting { display: flex; flex-direction: column; }
.home-hello { font-size: 26rpx; opacity: 0.85; }
.home-name  { font-size: 38rpx; font-weight: 700; margin-top: 4rpx; }
.home-date  { font-size: 24rpx; opacity: 0.8; }
.home-role-badge { font-size: 22rpx; padding: 6rpx 18rpx; background: rgba(255,255,255,0.2); border-radius: 20rpx; }

.home-scroll { height: calc(100vh - 200rpx); }

/* 统计卡片 */
.home-stats { display: flex; flex-wrap: wrap; gap: 16rpx; padding: 24rpx; }
.home-stat-card {
  flex: 1; min-width: 42%; background: #fff; border-radius: 20rpx; padding: 24rpx;
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04); position: relative; overflow: hidden;
}
.home-stat-card::after { content:''; position:absolute; top:0; left:0; right:0; height:6rpx; background:#2D8E69; }
.home-stat-card--warn::after   { background: #E74C3C; }
.home-stat-card--blue::after   { background: #3498DB; }
.home-stat-card--purple::after { background: #9B59B6; }
.home-stat-card--green::after  { background: #27AE60; }
.home-stat-icon  { font-size: 40rpx; margin-bottom: 8rpx; }
.home-stat-num   { font-size: 48rpx; font-weight: 800; color: #2C3E50; }
.home-stat-label { font-size: 24rpx; color: #8E99A4; margin-top: 4rpx; }

/* Section */
.home-section { margin: 0 24rpx 24rpx; background: #fff; border-radius: 20rpx; padding: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.03); }
.home-section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.home-section-title { font-size: 30rpx; font-weight: 700; color: #2C3E50; }
.home-section-more  { font-size: 24rpx; color: #3498DB; }

/* 待办 */
.home-todo-list { }
.home-todo-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.home-todo-item:last-child { border-bottom: none; }
.home-todo-dot  { width: 12rpx; height: 12rpx; border-radius: 50%; flex-shrink: 0; }
.home-todo-body { flex: 1; }
.home-todo-title   { display: block; font-size: 28rpx; color: #2C3E50; font-weight: 500; }
.home-todo-meta    { display: flex; align-items: center; gap: 8rpx; margin-top: 6rpx; }
.home-todo-tag     { font-size: 20rpx; color: #5B6B7F; padding: 2rpx 10rpx; border-radius: 6rpx; font-weight: 500; }
.home-todo-student { font-size: 22rpx; color: #8E99A4; }
.home-todo-arrow   { font-size: 28rpx; color: #CCC; }

/* 动态 */
.home-activity-item { display: flex; align-items: center; gap: 16rpx; padding: 14rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.home-activity-item:last-child { border-bottom: none; }
.home-activity-avatar { width: 56rpx; height: 56rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 600; flex-shrink: 0; }
.home-activity-body { flex: 1; }
.home-activity-text { display: block; font-size: 26rpx; color: #2C3E50; line-height: 1.5; }
.home-activity-time { display: block; font-size: 22rpx; color: #BDC3C7; margin-top: 4rpx; }

/* 快捷入口 — 每行3个，自动换行 */
.home-shortcuts { display: flex; flex-wrap: wrap; gap: 20rpx; margin-top: 16rpx; }
.home-shortcut  { width: calc(33.33% - 14rpx); display: flex; flex-direction: column; align-items: center; }
.home-sc-icon   { width: 88rpx; height: 88rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: center; font-size: 40rpx; }
.home-sc-label  { font-size: 22rpx; color: #5B6B7F; margin-top: 8rpx; }

/* GROWER 健康卡片 */
.home-health-cards { display: flex; gap: 16rpx; padding: 24rpx; }
.home-health-card {
  flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx 12rpx;
  display: flex; flex-direction: column; align-items: center; text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
.home-health-icon { font-size: 36rpx; margin-bottom: 8rpx; }
.home-health-val  { font-size: 36rpx; font-weight: 700; color: #2C3E50; line-height: 1; }
.home-health-unit { font-size: 18rpx; color: #8E99A4; margin-top: 2rpx; }
.home-health-label { font-size: 20rpx; color: #8E99A4; margin-top: 6rpx; }

/* GROWER 任务 */
.home-task-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.home-task-item:last-child { border-bottom: none; }
.home-task-check {
  width: 44rpx; height: 44rpx; border-radius: 50%; border: 3rpx solid #27AE60;
  display: flex; align-items: center; justify-content: center;
  color: #27AE60; font-size: 24rpx; font-weight: 700; flex-shrink: 0;
}
.home-task-check--done { background: #27AE60; color: #fff; }
.home-task-text { flex: 1; font-size: 28rpx; color: #2C3E50; }
.home-task-text--done { color: #BDC3C7; text-decoration: line-through; }
.home-task-pts  { font-size: 22rpx; color: #27AE60; font-weight: 600; }
.home-task-progress { margin-top: 16rpx; display: flex; align-items: center; gap: 16rpx; }
.home-task-bar  { flex: 1; height: 8rpx; background: #F0F0F0; border-radius: 4rpx; overflow: hidden; }
.home-task-fill { height: 100%; background: #27AE60; border-radius: 4rpx; }
.home-task-pct  { font-size: 22rpx; color: #8E99A4; white-space: nowrap; }

/* GROWER 用药提醒 Banner */
.home-med-banner { display: flex; align-items: center; gap: 16rpx; background: #F0FFF8; border-radius: 12rpx; padding: 20rpx; border-left: 6rpx solid #16a34a; margin: 12rpx 0; }
.home-med-icon   { font-size: 40rpx; }
.home-med-body   { flex: 1; }
.home-med-title  { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.home-med-sub    { display: block; font-size: 22rpx; color: #6b7280; margin-top: 4rpx; }
.home-med-arrow  { font-size: 36rpx; color: #9ca3af; }

/* GROWER 体重提醒 Banner */
.home-weight-banner { display: flex; align-items: center; gap: 16rpx; background: #FFF8E1; border-radius: 12rpx; padding: 20rpx; border-left: 6rpx solid #F59E0B; margin: 12rpx 0; }
.home-weight-icon   { font-size: 40rpx; }
.home-weight-body   { flex: 1; }
.home-weight-title  { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.home-weight-sub    { display: block; font-size: 22rpx; color: #6b7280; margin-top: 4rpx; }
.home-weight-arrow  { font-size: 36rpx; color: #9ca3af; }

/* GROWER 评估 Banner */
.home-assess-banner { display: flex; align-items: center; gap: 16rpx; background: #FFF8E6; border-radius: 12rpx; padding: 20rpx; border-left: 6rpx solid #E67E22; }
.home-assess-icon   { font-size: 40rpx; }
.home-assess-body   { flex: 1; }
.home-assess-title  { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.home-assess-sub    { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.home-assess-arrow  { font-size: 32rpx; color: #E67E22; }

.home-empty-hint { text-align: center; padding: 32rpx 0; font-size: 26rpx; color: #8E99A4; }
</style>
