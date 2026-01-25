<template>
  <div class="page-container">
    <van-nav-bar title="行健行为教练" />

    <div class="page-content">
      <!-- 欢迎卡片 -->
      <div class="welcome-card card">
        <div class="welcome-header">
          <van-icon name="user-circle-o" size="48" color="#1989fa" />
          <div class="welcome-text">
            <h2>你好，{{ userStore.name }}</h2>
            <p>今天感觉如何？</p>
          </div>
        </div>
        <div class="efficacy-display" :style="{ backgroundColor: userStore.efficacyColor + '20' }">
          <span class="efficacy-number" :style="{ color: userStore.efficacyColor }">
            {{ userStore.efficacyScore }}
          </span>
          <span class="efficacy-label">效能感</span>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="quick-actions card">
        <h3>快捷服务</h3>
        <van-grid :column-num="4" :border="false">
          <van-grid-item icon="chat-o" text="开始对话" to="/chat" />
          <van-grid-item icon="todo-list-o" text="我的任务" to="/tasks" />
          <van-grid-item icon="chart-trending-o" text="健康看板" to="/dashboard" />
          <van-grid-item icon="records-o" text="健康档案" to="/profile" />
        </van-grid>
      </div>

      <!-- 专家团队 -->
      <div class="experts-card card">
        <h3>专家团队</h3>
        <div class="expert-list">
          <div
            v-for="expert in chatStore.experts"
            :key="expert.id"
            class="expert-item"
            @click="goToChat(expert.id)"
          >
            <div class="expert-avatar" :class="'avatar-' + expert.id">
              <van-icon name="manager" />
            </div>
            <div class="expert-info">
              <div class="expert-name">{{ expert.name }}</div>
              <div class="expert-role">{{ expert.role }}</div>
            </div>
            <van-icon name="arrow" class="expert-arrow" />
          </div>
        </div>
      </div>

      <!-- 今日任务 -->
      <div v-if="chatStore.pendingTasks.length > 0" class="tasks-preview card">
        <div class="tasks-header">
          <h3>今日任务</h3>
          <router-link to="/tasks" class="view-all">查看全部</router-link>
        </div>
        <TaskCard
          v-for="task in chatStore.pendingTasks.slice(0, 3)"
          :key="task.id"
          :task="task"
          @toggle="chatStore.toggleTaskComplete"
        />
      </div>
    </div>

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import TabBar from '@/components/common/TabBar.vue'
import TaskCard from '@/components/chat/TaskCard.vue'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

function goToChat(expertId: string) {
  chatStore.setCurrentExpert(expertId)
  router.push('/chat')
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.welcome-card {
  .welcome-header {
    display: flex;
    align-items: center;
    margin-bottom: $spacing-md;
  }

  .welcome-text {
    margin-left: $spacing-md;

    h2 {
      font-size: $font-size-xl;
      margin-bottom: 4px;
    }

    p {
      color: $text-color-secondary;
      font-size: $font-size-sm;
    }
  }

  .efficacy-display {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: $spacing-md;
    border-radius: $border-radius;
    gap: $spacing-xs;

    .efficacy-number {
      font-size: 32px;
      font-weight: bold;
    }

    .efficacy-label {
      font-size: $font-size-sm;
      color: $text-color-secondary;
    }
  }
}

.quick-actions {
  h3 {
    margin-bottom: $spacing-sm;
    font-size: $font-size-lg;
  }
}

.experts-card {
  h3 {
    margin-bottom: $spacing-sm;
    font-size: $font-size-lg;
  }
}

.expert-list {
  .expert-item {
    display: flex;
    align-items: center;
    padding: $spacing-sm 0;
    border-bottom: 1px solid $border-color;

    &:last-child {
      border-bottom: none;
    }
  }

  .expert-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 20px;

    &.avatar-mental_health { background-color: $expert-mental; }
    &.avatar-nutrition { background-color: $expert-nutrition; }
    &.avatar-sports_rehab { background-color: $expert-sports; }
    &.avatar-tcm_wellness { background-color: $expert-tcm; }
  }

  .expert-info {
    flex: 1;
    margin-left: $spacing-sm;

    .expert-name {
      font-weight: 500;
    }

    .expert-role {
      font-size: $font-size-xs;
      color: $text-color-secondary;
    }
  }

  .expert-arrow {
    color: $text-color-placeholder;
  }
}

.tasks-preview {
  .tasks-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-sm;

    h3 {
      font-size: $font-size-lg;
    }

    .view-all {
      font-size: $font-size-sm;
      color: $primary-color;
      text-decoration: none;
    }
  }
}
</style>
