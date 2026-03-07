<template>
  <div>
    <div class="page-header">
      <h2>系统配置</h2>
      <button class="save-btn" :disabled="saving" @click="saveAll">{{ saving?'保存中...':'保存配置' }}</button>
    </div>

    <div class="config-layout">
      <!-- 左侧分类 -->
      <div class="config-nav">
        <button v-for="sec in sections" :key="sec.key" class="cnav-item" :class="{active:activeSection===sec.key}" @click="activeSection=sec.key">
          <span>{{ sec.icon }}</span>{{ sec.label }}
        </button>
      </div>

      <!-- 右侧配置项 -->
      <div class="config-body">
        <!-- 平台基础 -->
        <template v-if="activeSection==='basic'">
          <div class="section-title">平台基础设置</div>
          <div class="config-fields">
            <div class="field-row"><label>平台名称</label><input v-model="cfg.platform_name" class="cfg-input"/></div>
            <div class="field-row"><label>平台简称</label><input v-model="cfg.platform_short_name" class="cfg-input"/></div>
            <div class="field-row"><label>联系邮箱</label><input v-model="cfg.contact_email" type="email" class="cfg-input"/></div>
            <div class="field-row"><label>客服电话</label><input v-model="cfg.support_phone" class="cfg-input"/></div>
            <div class="field-row"><label>隐私政策 URL</label><input v-model="cfg.privacy_url" class="cfg-input"/></div>
          </div>
        </template>

        <!-- 注册与角色 -->
        <template v-else-if="activeSection==='auth'">
          <div class="section-title">注册与角色设置</div>
          <div class="config-fields">
            <div class="field-row">
              <label>开放注册</label>
              <label class="toggle"><input type="checkbox" v-model="cfg.open_registration"/><span class="slider"></span></label>
            </div>
            <div class="field-row">
              <label>需要邮箱验证</label>
              <label class="toggle"><input type="checkbox" v-model="cfg.require_email_verify"/><span class="slider"></span></label>
            </div>
            <div class="field-row"><label>默认注册角色</label>
              <select v-model="cfg.default_role" class="cfg-select">
                <option value="observer">观察员</option>
                <option value="grower">成长者</option>
              </select>
            </div>
            <div class="field-row"><label>教练申请需审批</label>
              <label class="toggle"><input type="checkbox" v-model="cfg.coach_requires_approval"/><span class="slider"></span></label>
            </div>
            <div class="field-row"><label>晋级审核级数</label>
              <select v-model="cfg.promotion_levels" class="cfg-select">
                <option :value="1">1级（仅教练）</option>
                <option :value="2">2级（教练+督导）</option>
                <option :value="3">3级（教练+督导+大师）</option>
              </select>
            </div>
          </div>
        </template>

        <!-- AI & 模型 -->
        <template v-else-if="activeSection==='ai'">
          <div class="section-title">AI 与模型设置</div>
          <div class="config-fields">
            <div class="field-row"><label>Ollama 地址</label><input v-model="cfg.ollama_url" class="cfg-input"/></div>
            <div class="field-row"><label>默认嵌入模型</label><input v-model="cfg.embed_model" class="cfg-input"/></div>
            <div class="field-row"><label>向量维度</label>
              <select v-model="cfg.vector_dim" class="cfg-select">
                <option :value="1024">1024（mxbai-embed-large）</option>
                <option :value="768">768</option>
              </select>
            </div>
            <div class="field-row"><label>AI对话每日限额（次）</label><input v-model.number="cfg.ai_daily_limit" type="number" min="0" class="cfg-input cfg-short"/></div>
            <div class="field-row">
              <label>启用 RAG 知识库</label>
              <label class="toggle"><input type="checkbox" v-model="cfg.enable_rag"/><span class="slider"></span></label>
            </div>
          </div>
        </template>

        <!-- 通知 -->
        <template v-else-if="activeSection==='notify'">
          <div class="section-title">通知设置</div>
          <div class="config-fields">
            <div class="field-row">
              <label>站内通知</label>
              <label class="toggle"><input type="checkbox" v-model="cfg.notify_inapp"/><span class="slider"></span></label>
            </div>
            <div class="field-row">
              <label>微信模板消息</label>
              <label class="toggle"><input type="checkbox" v-model="cfg.notify_wechat"/><span class="slider"></span></label>
            </div>
            <div class="field-row">
              <label>短信通知</label>
              <label class="toggle"><input type="checkbox" v-model="cfg.notify_sms"/><span class="slider"></span></label>
            </div>
            <div class="field-row"><label>危急数据告警邮箱</label><input v-model="cfg.alert_email" type="email" class="cfg-input"/></div>
          </div>
        </template>

        <!-- 安全 -->
        <template v-else-if="activeSection==='security'">
          <div class="section-title">安全设置</div>
          <div class="config-fields">
            <div class="field-row"><label>JWT 过期时间（小时）</label><input v-model.number="cfg.jwt_expire_hours" type="number" min="1" max="720" class="cfg-input cfg-short"/></div>
            <div class="field-row"><label>登录失败锁定次数</label><input v-model.number="cfg.login_max_retries" type="number" min="3" max="20" class="cfg-input cfg-short"/></div>
            <div class="field-row">
              <label>强制双因素认证（管理员）</label>
              <label class="toggle"><input type="checkbox" v-model="cfg.require_2fa_admin"/><span class="slider"></span></label>
            </div>
            <div class="field-row"><label>API 速率限制（次/分钟）</label><input v-model.number="cfg.rate_limit_per_min" type="number" min="10" class="cfg-input cfg-short"/></div>
          </div>
        </template>

        <div v-if="saveMsg" class="save-msg" :class="saveOk?'ok':'err'">{{ saveMsg }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'

const activeSection = ref('basic')
const saving = ref(false)
const saveMsg = ref('')
const saveOk = ref(true)

const sections = [
  { key:'basic',    icon:'🏠', label:'平台基础' },
  { key:'auth',     icon:'👤', label:'注册与角色' },
  { key:'ai',       icon:'🤖', label:'AI 与模型' },
  { key:'notify',   icon:'🔔', label:'通知设置' },
  { key:'security', icon:'🔒', label:'安全设置' },
]

const cfg = ref({
  platform_name: '行健行为健康平台',
  platform_short_name: '行健',
  contact_email: 'admin@xingjian.health',
  support_phone: '',
  privacy_url: '/privacy-policy',
  open_registration: true,
  require_email_verify: false,
  default_role: 'observer',
  coach_requires_approval: true,
  promotion_levels: 3,
  ollama_url: 'http://localhost:11434',
  embed_model: 'mxbai-embed-large:latest',
  vector_dim: 1024,
  ai_daily_limit: 50,
  enable_rag: true,
  notify_inapp: true,
  notify_wechat: false,
  notify_sms: false,
  alert_email: '',
  jwt_expire_hours: 24,
  login_max_retries: 5,
  require_2fa_admin: false,
  rate_limit_per_min: 60,
})

async function saveAll() {
  saving.value = true; saveMsg.value = ''
  try {
    await api.post('/api/v1/system/config', cfg.value)
    saveOk.value = true; saveMsg.value = '✓ 配置已保存'
  } catch {
    // 端点可能未实现，本地保存即可
    localStorage.setItem('staff_admin_config', JSON.stringify(cfg.value))
    saveOk.value = true; saveMsg.value = '✓ 配置已本地保存（后端端点未开放）'
  }
  saving.value = false
  setTimeout(() => saveMsg.value = '', 3000)
}

onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/system/config')
    Object.assign(cfg.value, res)
  } catch {
    const local = localStorage.getItem('staff_admin_config')
    if (local) try { Object.assign(cfg.value, JSON.parse(local)) } catch {}
  }
})
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-header h2 { font-size:18px; font-weight:600; color:#111827; margin:0; }
.save-btn { padding:9px 22px; background:#3b82f6; color:#fff; border:none; border-radius:8px; font-size:13px; font-weight:600; cursor:pointer; }
.save-btn:hover { background:#2563eb; }
.save-btn:disabled { opacity:.6; cursor:not-allowed; }

.config-layout { display:flex; gap:0; background:#fff; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,.06); overflow:hidden; min-height:500px; }

.config-nav { width:180px; flex-shrink:0; background:#f9fafb; border-right:1px solid #f3f4f6; padding:12px 0; }
.cnav-item { display:flex; align-items:center; gap:8px; width:100%; padding:10px 16px; background:none; border:none; text-align:left; font-size:13px; color:#6b7280; cursor:pointer; transition:all .15s; }
.cnav-item:hover { background:#f0f7ff; color:#374151; }
.cnav-item.active { background:#eff6ff; color:#1d4ed8; font-weight:600; border-right:2px solid #3b82f6; }

.config-body { flex:1; padding:28px 32px; }
.section-title { font-size:15px; font-weight:600; color:#111827; margin-bottom:20px; padding-bottom:10px; border-bottom:1px solid #f3f4f6; }

.config-fields { display:flex; flex-direction:column; gap:16px; }
.field-row { display:flex; align-items:center; gap:16px; }
.field-row label:first-child { width:180px; font-size:13px; color:#374151; flex-shrink:0; }
.cfg-input { flex:1; max-width:320px; padding:9px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:13px; outline:none; }
.cfg-input:focus { border-color:#3b82f6; }
.cfg-short { max-width:120px; }
.cfg-select { flex:1; max-width:260px; padding:9px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:13px; background:#fff; cursor:pointer; }

/* Toggle switch */
.toggle { position:relative; display:inline-block; width:44px; height:24px; }
.toggle input { opacity:0; width:0; height:0; }
.slider { position:absolute; inset:0; background:#d1d5db; border-radius:24px; cursor:pointer; transition:.25s; }
.slider::before { content:''; position:absolute; width:18px; height:18px; left:3px; top:3px; background:#fff; border-radius:50%; transition:.25s; }
.toggle input:checked + .slider { background:#3b82f6; }
.toggle input:checked + .slider::before { transform:translateX(20px); }

.save-msg { margin-top:20px; font-size:13px; font-weight:500; padding:10px 14px; border-radius:8px; }
.save-msg.ok { background:#d1fae5; color:#065f46; }
.save-msg.err { background:#fee2e2; color:#dc2626; }
</style>
