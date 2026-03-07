<template>
  <div>
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-right">
        <input v-model="searchQ" type="text" placeholder="搜索用户名/姓名..." class="search-input" @keyup.enter="search" />
        <button class="search-btn" @click="search">搜索</button>
        <select v-model="roleFilter" class="filter-select" @change="search">
          <option value="">全部角色</option>
          <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
        </select>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="users.length === 0" class="empty">{{ searchQ ? '未找到匹配用户' : '暂无用户数据' }}</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>用户名</th><th>姓名</th><th>角色</th><th>手机</th><th>注册时间</th><th>状态</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>
              <div class="user-cell">
                <div class="u-avatar">{{ (u.full_name || u.username || '?')[0] }}</div>
                <div>
                  <div class="u-name">{{ u.username }}</div>
                  <div class="u-id">ID: {{ u.id }}</div>
                </div>
              </div>
            </td>
            <td>{{ u.full_name || '—' }}</td>
            <td><span class="role-tag" :class="'role-' + u.role">{{ roleLabel(u.role) }}</span></td>
            <td>{{ u.phone || '—' }}</td>
            <td>{{ u.created_at?.slice(0, 10) || '—' }}</td>
            <td>
              <span class="status-dot" :class="u.is_active !== false ? 'dot-active' : 'dot-inactive'"></span>
              {{ u.is_active !== false ? '正常' : '禁用' }}
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div v-if="total > pageSize" class="pagination">
        <button class="page-btn" :disabled="page <= 1" @click="gotoPage(page - 1)">‹</button>
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <button class="page-btn" :disabled="page >= totalPages" @click="gotoPage(page + 1)">›</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/index'

const loading = ref(false)
const users = ref<any[]>([])
const searchQ = ref('')
const roleFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const roles = [
  { value: 'observer', label: '观察员' },
  { value: 'grower', label: '成长者' },
  { value: 'sharer', label: '分享者' },
  { value: 'coach', label: '教练' },
  { value: 'supervisor', label: '督导' },
  { value: 'master', label: '大师' },
  { value: 'admin', label: '管理员' },
]

const ROLE_LABELS: Record<string, string> = {
  observer: '观察员', grower: '成长者', sharer: '分享者',
  coach: '教练', promoter: '促进师', supervisor: '督导',
  master: '大师', admin: '管理员',
}

function roleLabel(r: string) { return ROLE_LABELS[r?.toLowerCase()] || r || '—' }

async function search() {
  page.value = 1
  await load()
}

async function gotoPage(p: number) {
  page.value = p
  await load()
}

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchQ.value) params.append('q', searchQ.value)
    if (roleFilter.value) params.append('role', roleFilter.value)
    params.append('page', String(page.value))
    params.append('page_size', String(pageSize))
    const res: any = await api.get(`/api/v1/users/search?${params}`)
    users.value = res.items || res.users || (Array.isArray(res) ? res : [])
    total.value = res.total ?? users.value.length
  } catch { users.value = [] }
  loading.value = false
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }
.header-right { display: flex; gap: 8px; align-items: center; }

.search-input {
  padding: 9px 14px; border: 1px solid #e5e7eb; border-radius: 8px;
  font-size: 13px; width: 220px; outline: none;
}
.search-input:focus { border-color: #3b82f6; }

.search-btn {
  padding: 9px 16px; background: #3b82f6; color: #fff; border: none;
  border-radius: 8px; font-size: 13px; cursor: pointer;
}
.search-btn:hover { background: #2563eb; }

.filter-select { padding: 9px 12px; border: 1px solid #e5e7eb; border-radius: 8px; font-size: 13px; background: #fff; cursor: pointer; }

.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; color: #6b7280; font-weight: 500; border-bottom: 2px solid #f3f4f6; }
.data-table td { padding: 12px; color: #374151; border-bottom: 1px solid #f9fafb; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }

.user-cell { display: flex; align-items: center; gap: 10px; }
.u-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #3b82f6);
  color: #fff; font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.u-name { font-size: 13px; font-weight: 500; color: #111827; }
.u-id { font-size: 11px; color: #9ca3af; }

.role-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; background: #f3f4f6; color: #374151; }
.role-coach { background: #ede9fe; color: #5b21b6; }
.role-supervisor { background: #f3e8ff; color: #7e22ce; }
.role-master { background: #fef9c3; color: #92400e; }
.role-admin { background: #fee2e2; color: #dc2626; }
.role-grower { background: #dbeafe; color: #1d4ed8; }
.role-sharer { background: #ffedd5; color: #c2410c; }

.status-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }
.dot-active { background: #10b981; }
.dot-inactive { background: #ef4444; }

.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f3f4f6; }
.page-btn { padding: 6px 14px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; font-size: 16px; cursor: pointer; }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 13px; color: #6b7280; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
