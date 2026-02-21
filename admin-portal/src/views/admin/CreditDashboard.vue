<template>
  <div class="credit-dashboard">
    <a-page-header title="学分体系概览" />

    <!-- KPI 卡片 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card>
          <a-statistic title="课程模块总数" :value="stats.total_modules" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card>
          <a-statistic title="学分记录总数" :value="stats.total_credit_records" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card>
          <a-statistic title="有学分用户数" :value="stats.users_with_credits" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card>
          <a-statistic title="待审核晋级申请" :value="pendingApplications" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 模块类型分布 -->
    <a-row :gutter="16">
      <a-col :xs="24" :md="12">
        <a-card title="课程模块按类型分布">
          <a-table
            :columns="typeColumns"
            :data-source="stats.by_type"
            :pagination="false"
            size="small"
            row-key="module_type"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :md="12">
        <a-card title="晋级规则概览">
          <a-table
            :columns="ruleColumns"
            :data-source="rules"
            :pagination="false"
            size="small"
            row-key="from_role"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 快捷入口 -->
    <a-card title="快捷操作" class="mt-4">
      <a-space>
        <a-button type="primary" @click="$router.push('/admin/credit-system/modules')">
          课程模块管理
        </a-button>
        <a-button @click="$router.push('/admin/credit-system/companions')">
          同道者关系管理
        </a-button>
        <a-button @click="$router.push('/admin/credit-system/promotion-review')">
          晋级审核
        </a-button>
      </a-space>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { creditApi, promotionApi } from '@/api/credit-promotion'

const stats = ref<Record<string, any>>({
  total_modules: 0,
  total_credit_records: 0,
  users_with_credits: 0,
  by_type: [],
})
const rules = ref<any[]>([])
const pendingApplications = ref(0)

const typeColumns = [
  { title: '模块类型', dataIndex: 'module_type', key: 'module_type' },
  { title: '数量', dataIndex: 'cnt', key: 'cnt' },
  { title: '总学分', dataIndex: 'total_credits', key: 'total_credits' },
]

const ruleColumns = [
  { title: '晋级路径', dataIndex: 'display', key: 'display' },
  { title: '总学分要求', customRender: ({ record }: any) => record.credits?.total_min, key: 'credits' },
  { title: '成长积分', customRender: ({ record }: any) => record.points?.growth_min, key: 'growth' },
  { title: '同道者毕业数', customRender: ({ record }: any) => record.companions?.graduated_min, key: 'companions' },
]

onMounted(async () => {
  try {
    const [statsRes, rulesRes, appsRes] = await Promise.all([
      creditApi.adminStats(),
      promotionApi.getRules(),
      promotionApi.listApplications({ status: 'pending' }),
    ])
    stats.value = statsRes.data
    rules.value = rulesRes.data
    pendingApplications.value = Array.isArray(appsRes.data) ? appsRes.data.length : 0
  } catch (e) {
    console.error('加载统计失败', e)
  }
})
</script>

<style scoped>
.credit-dashboard { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
.mt-4 { margin-top: 16px; }
</style>
