<template>
  <div class="dashboard">
    <!-- 用户欢迎卡片 -->
    <a-card style="margin-bottom: 16px">
      <a-row align="middle">
        <a-col :span="18">
          <h2 style="margin: 0">欢迎回来，{{ userInfo.userId }}</h2>
          <p style="color: #666; margin: 8px 0 0">
            角色: {{ userInfo.roleLabel }} | 等级: L{{ userInfo.level }}
          </p>
        </a-col>
        <a-col :span="6" style="text-align: right">
          <a-tag :color="userInfo.roleColor">{{ userInfo.role }}</a-tag>
        </a-col>
      </a-row>
    </a-card>

    <a-row :gutter="16">
      <a-col :span="6">
        <a-card>
          <a-statistic title="注册学员" :value="1256" suffix="人">
            <template #prefix><UserOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="认证教练" :value="89" suffix="人">
            <template #prefix><TeamOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="课程数量" :value="18" suffix="门">
            <template #prefix><VideoCameraOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日学习" :value="342" suffix="人次">
            <template #prefix><ReadOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="16">
        <a-card title="认证等级分布">
          <div style="display: flex; align-items: flex-end; height: 280px; gap: 40px; padding: 20px; justify-content: center;">
            <div style="text-align: center;">
              <div style="height: 180px; width: 60px; background: linear-gradient(to top, #1890ff, #69c0ff); border-radius: 4px;"></div>
              <div style="margin-top: 8px; color: #666;">L0<br/>856人</div>
            </div>
            <div style="text-align: center;">
              <div style="height: 120px; width: 60px; background: linear-gradient(to top, #52c41a, #95de64); border-radius: 4px;"></div>
              <div style="margin-top: 8px; color: #666;">L1<br/>52人</div>
            </div>
            <div style="text-align: center;">
              <div style="height: 80px; width: 60px; background: linear-gradient(to top, #faad14, #ffc53d); border-radius: 4px;"></div>
              <div style="margin-top: 8px; color: #666;">L2<br/>28人</div>
            </div>
            <div style="text-align: center;">
              <div style="height: 40px; width: 60px; background: linear-gradient(to top, #f5222d, #ff7875); border-radius: 4px;"></div>
              <div style="margin-top: 8px; color: #666;">L3<br/>7人</div>
            </div>
            <div style="text-align: center;">
              <div style="height: 20px; width: 60px; background: linear-gradient(to top, #722ed1, #b37feb); border-radius: 4px;"></div>
              <div style="margin-top: 8px; color: #666;">L4<br/>2人</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="待处理事项">
          <div style="padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
            <a-badge status="warning" text="3个晋级申请待审核" />
          </div>
          <div style="padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
            <a-badge status="processing" text="5份实操考试待评分" />
          </div>
          <div style="padding: 8px 0;">
            <a-badge status="default" text="2个课程待上架" />
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="12">
        <a-card title="最近考试">
          <table style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr style="border-bottom: 1px solid #f0f0f0;">
                <th style="text-align: left; padding: 8px;">考试名称</th>
                <th style="text-align: left; padding: 8px;">参考人数</th>
                <th style="text-align: left; padding: 8px;">平均分</th>
                <th style="text-align: left; padding: 8px;">通过率</th>
              </tr>
            </thead>
            <tbody>
              <tr style="border-bottom: 1px solid #f0f0f0;">
                <td style="padding: 8px;">L1理论考试</td>
                <td style="padding: 8px;">45</td>
                <td style="padding: 8px;">78</td>
                <td style="padding: 8px;">82%</td>
              </tr>
              <tr style="border-bottom: 1px solid #f0f0f0;">
                <td style="padding: 8px;">L2案例模拟</td>
                <td style="padding: 8px;">23</td>
                <td style="padding: 8px;">72</td>
                <td style="padding: 8px;">65%</td>
              </tr>
              <tr>
                <td style="padding: 8px;">L1对话评估</td>
                <td style="padding: 8px;">38</td>
                <td style="padding: 8px;">75</td>
                <td style="padding: 8px;">74%</td>
              </tr>
            </tbody>
          </table>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="晋级申请">
          <table style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr style="border-bottom: 1px solid #f0f0f0;">
                <th style="text-align: left; padding: 8px;">教练</th>
                <th style="text-align: left; padding: 8px;">当前等级</th>
                <th style="text-align: left; padding: 8px;">申请等级</th>
                <th style="text-align: left; padding: 8px;">申请日期</th>
              </tr>
            </thead>
            <tbody>
              <tr style="border-bottom: 1px solid #f0f0f0;">
                <td style="padding: 8px;">张三</td>
                <td style="padding: 8px;">L1</td>
                <td style="padding: 8px;">L2</td>
                <td style="padding: 8px;">2026-01-24</td>
              </tr>
              <tr style="border-bottom: 1px solid #f0f0f0;">
                <td style="padding: 8px;">李四</td>
                <td style="padding: 8px;">L0</td>
                <td style="padding: 8px;">L1</td>
                <td style="padding: 8px;">2026-01-23</td>
              </tr>
              <tr>
                <td style="padding: 8px;">王五</td>
                <td style="padding: 8px;">L2</td>
                <td style="padding: 8px;">L3</td>
                <td style="padding: 8px;">2026-01-22</td>
              </tr>
            </tbody>
          </table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  UserOutlined,
  TeamOutlined,
  VideoCameraOutlined,
  ReadOutlined
} from '@ant-design/icons-vue'

// 角色映射
const roleLabels: Record<string, string> = {
  ADMIN: '系统管理员',
  EXPERT: '专家',
  COACH_SENIOR: '高级教练',
  COACH_INTERMEDIATE: '中级教练',
  COACH_JUNIOR: '初级教练',
  USER: '学员'
}

const roleColors: Record<string, string> = {
  ADMIN: 'red',
  EXPERT: 'purple',
  COACH_SENIOR: 'gold',
  COACH_INTERMEDIATE: 'blue',
  COACH_JUNIOR: 'green',
  USER: 'default'
}

// 从 localStorage 读取用户信息
const storedUsername = localStorage.getItem('admin_username') || '管理员'
const storedRole = localStorage.getItem('admin_role') || 'USER'
const storedLevel = parseInt(localStorage.getItem('admin_level') || '0')

const userInfo = ref({
  userId: storedUsername,
  role: storedRole,
  roleLabel: roleLabels[storedRole] || '学员',
  roleColor: roleColors[storedRole] || 'default',
  level: storedLevel
})
</script>

<style scoped>
.dashboard :deep(.ant-card) {
  border-radius: 8px;
}
</style>
