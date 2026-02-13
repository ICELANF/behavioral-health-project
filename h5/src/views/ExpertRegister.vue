<!--
  专家入驻注册 — 5 步向导 (可点击步骤标签切换)
  路由: /expert-register (public)
-->
<template>
  <div class="expert-register">
    <van-nav-bar title="申请入驻" left-arrow @click-left="$router.back()" />

    <!-- 步骤标签 (可点击切换) -->
    <div class="step-tabs">
      <div
        v-for="(sm, i) in stepLabels"
        :key="i"
        class="step-tab"
        :class="{ active: step === i, done: i < step, locked: i > maxReached }"
        @click="goToStep(i)"
      >
        <span class="tab-num" :class="{ 'tab-done': i < step }">{{ i < step ? '✓' : i + 1 }}</span>
        <span class="tab-label">{{ sm }}</span>
      </div>
    </div>

    <!-- 步骤描述 -->
    <div class="step-desc-bar">
      <span class="step-desc-text">{{ stepDescs[step] }}</span>
      <span class="step-progress">{{ step + 1 }}/5</span>
    </div>

    <div class="step-content">

      <!-- ── Step 1: 个人信息 + 账号 ── -->
      <div v-show="step === 0" class="step-panel">
        <!-- 未登录: 创建账号 -->
        <van-cell-group v-if="!isLoggedIn" inset title="创建账号">
          <van-field v-model="accountForm.username" label="登录名" placeholder="字母+数字, 至少3位" required />
          <van-field v-model="accountForm.password" label="密码" type="password" placeholder="至少6位" required />
          <van-field v-model="accountForm.confirmPwd" label="确认密码" type="password" placeholder="再次输入密码" required />
          <van-field v-model="accountForm.email" label="邮箱" placeholder="用于接收审核通知" required />
        </van-cell-group>

        <van-cell-group inset title="基本信息">
          <van-field v-model="form.full_name" label="真实姓名" placeholder="请输入真实姓名" required />
          <van-field label="性别" required>
            <template #input>
              <van-radio-group v-model="form.gender" direction="horizontal">
                <van-radio name="male">男</van-radio>
                <van-radio name="female">女</van-radio>
                <van-radio name="other">保密</van-radio>
              </van-radio-group>
            </template>
          </van-field>
        </van-cell-group>

        <van-cell-group inset title="出生日期" style="margin-top: 12px">
          <van-field v-model="form.birthday" label="出生日期" placeholder="如: 1985-06-15" />
        </van-cell-group>

        <van-cell-group inset title="联系方式" style="margin-top: 12px">
          <van-field v-model="form.phone" label="手机号" type="tel" placeholder="11位手机号" required />
          <van-field v-if="isLoggedIn" v-model="form.email" label="邮箱" placeholder="用于接收通知" />
        </van-cell-group>

        <van-cell-group inset title="个人照片（选填）" style="margin-top: 12px">
          <div style="padding: 12px">
            <van-uploader
              v-model="avatarFiles"
              :after-read="onAvatarUpload"
              :max-count="1"
              :max-size="5 * 1024 * 1024"
              accept="image/*"
              @oversize="showFailToast('照片不能超过 5MB')"
            />
            <div class="upload-tip">上传个人正面照片，JPG/PNG 格式，不超过 5MB</div>
          </div>
        </van-cell-group>

        <div v-if="!isLoggedIn" class="register-tip">
          <van-icon name="info-o" /> 已有账号？
          <van-button size="small" type="primary" plain @click="$router.push('/login')">直接登录</van-button>
        </div>
      </div>

      <!-- ── Step 2: 专业资质 ── -->
      <div v-show="step === 1" class="step-panel">
        <van-cell-group inset title="专家头衔">
          <van-field v-model="form.expert_title" label="头衔" placeholder="例: 主任医师·内分泌科" required />
        </van-cell-group>

        <van-cell-group inset title="工作单位" style="margin-top: 12px">
          <van-field v-model="form.workplace" label="单位名称" placeholder="例: XX医院内分泌科" />
          <van-field v-model="form.work_position" label="职务/职称" placeholder="例: 科室主任" />
          <van-field v-model="form.work_address" label="单位地址" placeholder="例: 北京市朝阳区XX路XX号" />
        </van-cell-group>

        <van-cell-group inset title="资质与专长" style="margin-top: 12px">
          <van-field label="资质证书">
            <template #input>
              <div class="tag-input-area">
                <van-tag v-for="(c, i) in form.expert_credentials" :key="i" closeable type="primary" size="medium" @close="form.expert_credentials.splice(i, 1)" style="margin: 2px 4px">{{ c }}</van-tag>
                <input v-model="credentialInput" class="mini-input" placeholder="输入后回车添加" @keydown.enter.prevent="addCredential" />
              </div>
            </template>
          </van-field>
          <van-field label="专长领域">
            <template #input>
              <div class="tag-input-area">
                <van-tag v-for="(s, i) in form.expert_specialties" :key="i" closeable type="success" size="medium" @close="form.expert_specialties.splice(i, 1)" style="margin: 2px 4px">{{ s }}</van-tag>
                <input v-model="specialtyInput" class="mini-input" placeholder="输入后回车添加" @keydown.enter.prevent="addSpecialty" />
              </div>
            </template>
          </van-field>
        </van-cell-group>

        <van-cell-group inset title="资质证书图片（选填）" style="margin-top: 12px">
          <div style="padding: 12px">
            <van-uploader
              v-model="credentialFiles"
              :after-read="onCredentialUpload"
              :max-count="5"
              :max-size="10 * 1024 * 1024"
              accept="image/*,.pdf"
              @oversize="showFailToast('文件不能超过 10MB')"
            />
            <div class="upload-tip">支持 JPG/PNG/PDF, 最多 5 张, 单张不超过 10MB</div>
          </div>
        </van-cell-group>

        <van-cell-group inset title="自我介绍（选填）" style="margin-top: 12px">
          <van-field v-model="form.expert_self_intro" type="textarea" rows="3" placeholder="简要介绍您的专业背景、从业经历和擅长方向" autosize show-word-limit maxlength="500" />
        </van-cell-group>
      </div>

      <!-- ── Step 3: 领域选择 ── -->
      <div v-show="step === 2" class="step-panel">
        <div class="domain-grid">
          <div
            v-for="domain in domains"
            :key="domain.id"
            class="domain-card"
            :class="{ selected: form.domain_id === domain.id }"
            :style="form.domain_id === domain.id ? { borderColor: domain.default_colors.primary, background: domain.default_colors.bg } : {}"
            @click="selectDomain(domain)"
          >
            <div class="domain-icon">{{ domain.icon }}</div>
            <div class="domain-label">{{ domain.label }}</div>
            <div class="domain-agents">
              <van-tag v-for="a in domain.recommended_agents.slice(0, 3)" :key="a" size="small" plain>{{ a }}</van-tag>
            </div>
          </div>
        </div>
        <van-loading v-if="domainsLoading" class="loading-center" />
      </div>

      <!-- ── Step 4: 品牌设置 ── -->
      <div v-show="step === 3" class="step-panel">
        <van-cell-group inset title="工作室品牌">
          <van-field v-model="form.brand_name" label="工作室名称" placeholder="例: 张三健康管理工作室" required />
          <van-field v-model="form.brand_tagline" label="品牌标语" placeholder="例: 科学管糖，健康生活" />
          <van-field v-model="form.brand_avatar" label="头像 Emoji" placeholder="选一个代表 Emoji" />
          <van-field v-model="form.welcome_message" label="欢迎语" type="textarea" rows="2" placeholder="客户首次进入工作室时看到的欢迎语" autosize />
        </van-cell-group>

        <div class="agent-list-section" v-if="selectedDomain">
          <div class="section-title">推荐 AI 助手 (可调整)</div>
          <van-checkbox-group v-model="form.selected_agents" direction="horizontal">
            <van-checkbox
              v-for="a in availableAgents"
              :key="a"
              :name="a"
              shape="square"
              style="margin: 4px 8px"
              :disabled="a === 'crisis'"
            >
              {{ a }}{{ a === 'crisis' ? ' (必选)' : '' }}
            </van-checkbox>
          </van-checkbox-group>
        </div>

        <div class="theme-preview" v-if="selectedDomain" :style="{ background: selectedDomain.default_colors.bg, borderColor: selectedDomain.default_colors.primary }">
          <div class="preview-avatar" :style="{ background: selectedDomain.default_colors.primary }">
            {{ form.brand_avatar || selectedDomain.icon }}
          </div>
          <div class="preview-name">{{ form.brand_name || '工作室名称' }}</div>
          <div class="preview-tagline">{{ form.brand_tagline || '品牌标语' }}</div>
        </div>
      </div>

      <!-- ── Step 5: 补充信息 + 确认 ── -->
      <div v-show="step === 4" class="step-panel">
        <van-cell-group inset title="通信地址（选填）">
          <van-field v-model="form.communication_address" type="textarea" rows="2" placeholder="用于接收平台寄送的证书等材料" autosize />
        </van-cell-group>

        <van-cell-group inset title="银行结算信息（选填）" style="margin-top: 12px">
          <div class="bank-hint">用于未来服务费结算，可稍后在工作室设置中补充</div>
          <van-field v-model="form.bank_name" label="开户银行" placeholder="例: 中国工商银行" />
          <van-field v-model="form.bank_branch" label="开户支行" placeholder="例: 北京朝阳支行" />
          <van-field v-model="form.bank_account" label="银行账号" placeholder="请输入银行卡号" />
          <van-field v-model="form.bank_holder" label="开户人" placeholder="与银行卡一致的姓名" />
        </van-cell-group>

        <van-cell-group inset title="信息汇总" style="margin-top: 12px">
          <van-cell title="姓名" :value="form.full_name || '-'" />
          <van-cell title="性别" :value="genderLabel" />
          <van-cell title="出生日期" :value="form.birthday || '-'" />
          <van-cell title="手机" :value="form.phone || '-'" />
          <van-cell title="头衔" :value="form.expert_title || '-'" />
          <van-cell title="工作单位" :value="form.workplace || '-'" />
          <van-cell title="工作室" :value="form.brand_name || '-'" />
          <van-cell title="领域" :value="selectedDomain?.label || '-'" />
          <van-cell title="资质" :value="form.expert_credentials.join(', ') || '-'" />
          <van-cell title="证书图片" :value="form.credential_images.length ? `${form.credential_images.length} 张` : '未上传'" />
          <van-cell title="专长" :value="form.expert_specialties.join(', ') || '-'" />
          <van-cell title="AI 助手" :value="form.selected_agents.join(', ') || '-'" />
          <van-cell title="银行信息" :value="form.bank_account ? '已填写' : '未填写'" />
        </van-cell-group>

        <div class="agreement">
          <van-checkbox v-model="agreed" shape="square">我已阅读并同意《专家入驻服务协议》</van-checkbox>
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="bottom-bar">
      <van-button v-if="step > 0" plain @click="step--" style="flex: 1">上一步</van-button>
      <van-button v-if="step < 4" type="primary" @click="nextStep" :loading="registering" style="flex: 1" :disabled="!canNext">
        下一步
      </van-button>
      <van-button v-if="step === 4" type="primary" @click="submitApplication" :loading="submitting" :disabled="!agreed" style="flex: 1">
        提交申请
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showFailToast } from 'vant'
import storage from '@/utils/storage'
import request from '@/api/request'

const DRAFT_KEY = 'expert_register_draft'

const router = useRouter()
const step = ref(0)
const maxReached = ref(0)
const agreed = ref(false)
const submitting = ref(false)
const registering = ref(false)
const domainsLoading = ref(false)

const isLoggedIn = computed(() => !!storage.getToken())

const stepLabels = ['个人信息', '专业资质', '领域选择', '品牌设置', '确认提交']
const stepDescs = [
  '填写您的基本个人信息，未注册用户需先创建账号',
  '填写工作单位、专业头衔、资质证书，上传证明材料',
  '选择您的主要服务领域，系统将推荐匹配的AI助手',
  '设置工作室品牌形象，调整AI助手组合',
  '填写通信与结算信息（可跳过），确认后提交审核',
]

// ── 表单 ──
const form = reactive({
  full_name: '',
  gender: '',
  birthday: '',
  phone: '',
  email: '',
  avatar_url: '',
  workplace: '',
  work_position: '',
  work_address: '',
  expert_title: '',
  expert_self_intro: '',
  expert_specialties: [] as string[],
  expert_credentials: [] as string[],
  credential_images: [] as string[],
  domain_id: '',
  selected_agents: [] as string[],
  brand_name: '',
  brand_tagline: '',
  brand_avatar: '',
  welcome_message: '',
  communication_address: '',
  bank_name: '',
  bank_branch: '',
  bank_account: '',
  bank_holder: '',
})

const accountForm = reactive({
  username: '',
  password: '',
  confirmPwd: '',
  email: '',
})

const credentialFiles = ref<any[]>([])
const avatarFiles = ref<any[]>([])
const pendingAvatarFile = ref<File | null>(null)
const pendingCredentialFiles = ref<{ file: File; fileObj: any }[]>([])
const credentialInput = ref('')
const specialtyInput = ref('')
const domains = ref<any[]>([])

const selectedDomain = computed(() => domains.value.find((d: any) => d.id === form.domain_id))

const availableAgents = computed(() => {
  if (!selectedDomain.value) return ['crisis']
  const agents = [...selectedDomain.value.recommended_agents]
  if (!agents.includes('crisis')) agents.push('crisis')
  return agents
})

const genderLabel = computed(() => {
  const map: Record<string, string> = { male: '男', female: '女', other: '保密' }
  return map[form.gender] || '-'
})

const canNext = computed(() => {
  if (step.value === 0) {
    if (!form.full_name.trim() || !form.gender) return false
    if (!isLoggedIn.value) {
      if (!accountForm.username.trim() || !accountForm.password || !accountForm.email) return false
    }
    return true
  }
  if (step.value === 1) return !!form.expert_title.trim()
  if (step.value === 2) return !!form.domain_id
  if (step.value === 3) return !!form.brand_name.trim()
  return true
})

// ── 步骤导航 (点击标签切换) ──
function goToStep(i: number) {
  if (i <= maxReached.value) {
    step.value = i
  }
}

// ── 草稿 ──
function restoreDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const draft = JSON.parse(raw)
    if (draft.form) {
      Object.keys(form).forEach(k => {
        if (draft.form[k] !== undefined) {
          ;(form as any)[k] = draft.form[k]
        }
      })
    }
    if (typeof draft.step === 'number' && draft.step >= 0 && draft.step <= 4) {
      step.value = draft.step
      maxReached.value = Math.max(draft.step, draft.maxReached || 0)
    }
  } catch { /* ignore */ }
}

function saveDraft() {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify({
      form: { ...form },
      step: step.value,
      maxReached: maxReached.value,
      savedAt: Date.now(),
    }))
  } catch { /* quota */ }
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY)
}

watch(() => ({ ...form }), saveDraft, { deep: true })
watch(step, saveDraft)

// ── 上传 (未登录时本地预览, 登录后自动上传) ──
async function uploadFileToServer(file: File): Promise<string | null> {
  const fd = new FormData()
  fd.append('file', file)
  try {
    const res = await request.post('/v1/expert-registration/upload-credential', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data?.data?.url || null
  } catch {
    return null
  }
}

async function onAvatarUpload(fileObj: any) {
  if (!isLoggedIn.value) {
    // 未登录: 仅本地预览, 暂存文件, 注册后自动上传
    pendingAvatarFile.value = fileObj.file
    fileObj.status = 'done'
    fileObj.message = '待上传'
    return
  }
  const url = await uploadFileToServer(fileObj.file)
  if (url) {
    form.avatar_url = url
    fileObj.status = 'done'
    fileObj.message = '上传成功'
  } else {
    fileObj.status = 'failed'
    fileObj.message = '上传失败'
    showFailToast('照片上传失败')
  }
}

async function onCredentialUpload(fileObj: any) {
  if (!isLoggedIn.value) {
    // 未登录: 暂存文件
    pendingCredentialFiles.value.push({ file: fileObj.file, fileObj })
    fileObj.status = 'done'
    fileObj.message = '待上传'
    return
  }
  const url = await uploadFileToServer(fileObj.file)
  if (url) {
    form.credential_images.push(url)
    fileObj.status = 'done'
    fileObj.message = '上传成功'
  } else {
    fileObj.status = 'failed'
    fileObj.message = '上传失败'
    showFailToast('图片上传失败')
  }
}

// 注册成功后: 上传所有暂存文件
async function uploadPendingFiles() {
  if (pendingAvatarFile.value) {
    const url = await uploadFileToServer(pendingAvatarFile.value)
    if (url) form.avatar_url = url
    pendingAvatarFile.value = null
  }
  for (const item of pendingCredentialFiles.value) {
    const url = await uploadFileToServer(item.file)
    if (url) {
      form.credential_images.push(url)
      item.fileObj.message = '上传成功'
    } else {
      item.fileObj.status = 'failed'
      item.fileObj.message = '上传失败'
    }
  }
  pendingCredentialFiles.value = []
}

// ── 账号注册 ──
async function registerAccount(): Promise<boolean> {
  if (accountForm.password !== accountForm.confirmPwd) {
    showFailToast('两次密码不一致')
    return false
  }
  if (accountForm.password.length < 6) {
    showFailToast('密码至少 6 位')
    return false
  }
  registering.value = true
  try {
    const res = await request.post('/v1/auth/register', {
      username: accountForm.username.trim(),
      password: accountForm.password,
      email: accountForm.email.trim(),
      full_name: form.full_name.trim(),
      phone: form.phone.trim(),
    })
    const token = res.data?.access_token
    if (token) {
      storage.setToken(token)
      storage.setAuthUser(res.data?.user || { username: accountForm.username })
      showToast('账号创建成功')
      return true
    }
    showFailToast('注册返回异常')
    return false
  } catch (e: any) {
    showFailToast(e.response?.data?.detail || '注册失败')
    return false
  } finally {
    registering.value = false
  }
}

// ── Tag ──
function addCredential() {
  const val = credentialInput.value.trim()
  if (val && !form.expert_credentials.includes(val)) {
    form.expert_credentials.push(val)
  }
  credentialInput.value = ''
}

function addSpecialty() {
  const val = specialtyInput.value.trim()
  if (val && !form.expert_specialties.includes(val)) {
    form.expert_specialties.push(val)
  }
  specialtyInput.value = ''
}

function selectDomain(domain: any) {
  form.domain_id = domain.id
  form.selected_agents = [...domain.recommended_agents, 'crisis'].filter((v: string, i: number, a: string[]) => a.indexOf(v) === i)
  if (!form.brand_avatar) form.brand_avatar = domain.icon
}

// ── 步骤 ──
async function nextStep() {
  if (step.value === 0) {
    if (!form.full_name.trim()) { showFailToast('请填写真实姓名'); return }
    if (!form.gender) { showFailToast('请选择性别'); return }
    if (!isLoggedIn.value) {
      const ok = await registerAccount()
      if (!ok) return
      // 注册成功后上传暂存的照片/证书
      await uploadPendingFiles()
    }
  }
  if (step.value === 1 && !form.expert_title.trim()) {
    showFailToast('请填写专家头衔')
    return
  }
  if (step.value === 2 && !form.domain_id) {
    showFailToast('请选择专业领域')
    return
  }
  if (step.value === 3 && !form.brand_name.trim()) {
    showFailToast('请填写工作室名称')
    return
  }
  step.value++
  maxReached.value = Math.max(maxReached.value, step.value)
}

// ── 提交 ──
async function submitApplication() {
  if (!isLoggedIn.value) {
    showFailToast('请先登录')
    router.push('/login')
    return
  }
  submitting.value = true
  try {
    const res = await request.post('/v1/expert-registration/apply', form)
    clearDraft()
    showToast(res.data?.data?.message || '申请已提交')
    router.push('/expert-application-status')
  } catch (e: any) {
    showFailToast(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

// ── 加载领域 ──
async function loadDomains() {
  domainsLoading.value = true
  try {
    const res = await request.get('/v1/expert-registration/domains')
    domains.value = res.data?.data || []
  } catch {
    domains.value = []
  } finally {
    domainsLoading.value = false
  }
}

onMounted(() => {
  restoreDraft()
  loadDomains()
})
</script>

<style scoped>
.expert-register {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 80px;
}

/* ── Step Tabs (可点击) ── */
.step-tabs {
  display: flex;
  background: #fff;
  padding: 12px 8px 8px;
  gap: 2px;
  border-bottom: 1px solid #f0f0f0;
  overflow-x: auto;
}
.step-tab {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px 2px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.step-tab.active {
  background: #E8F0FE;
}
.step-tab.locked {
  opacity: 0.4;
  cursor: not-allowed;
}
.tab-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ddd;
  color: #666;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-tab.active .tab-num {
  background: #1E40AF;
  color: #fff;
}
.tab-num.tab-done {
  background: #52c41a;
  color: #fff;
  font-size: 11px;
}
.tab-label {
  font-size: 11px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.step-tab.active .tab-label {
  color: #1E40AF;
  font-weight: 600;
}

/* ── Step Description Bar ── */
.step-desc-bar {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: #FAFBFC;
  border-bottom: 1px solid #f0f0f0;
}
.step-desc-text {
  flex: 1;
  font-size: 13px;
  color: #666;
  line-height: 1.4;
}
.step-progress {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
  flex-shrink: 0;
}

/* ── Form ── */
.step-content {
  padding: 0 0 16px;
}
.step-panel {
  padding: 8px 16px 0;
}
.register-tip {
  text-align: center;
  padding: 16px;
  color: #969799;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.upload-tip {
  font-size: 12px;
  color: #969799;
  margin-top: 8px;
}
.bank-hint {
  font-size: 12px;
  color: #999;
  padding: 8px 16px 0;
}

/* tag input */
.tag-input-area {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  min-height: 32px;
}
.mini-input {
  border: none;
  outline: none;
  font-size: 14px;
  padding: 4px 0;
  width: 140px;
  background: transparent;
}

/* domain grid */
.domain-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 8px 0;
}
.domain-card {
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.domain-card.selected {
  border-width: 2px;
}
.domain-icon {
  font-size: 28px;
  margin-bottom: 6px;
}
.domain-label {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 6px;
}
.domain-agents {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
}

/* agent / brand */
.agent-list-section {
  padding: 12px 0;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 8px;
  padding-left: 4px;
}
.theme-preview {
  margin-top: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.preview-avatar {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto 10px;
  color: #fff;
}
.preview-name {
  font-size: 17px;
  font-weight: 600;
  color: #323233;
}
.preview-tagline {
  font-size: 13px;
  color: #969799;
  margin-top: 4px;
}

/* summary / agreement */
.agreement {
  padding: 16px;
  text-align: center;
}

/* loading */
.loading-center {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

/* bottom bar */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.06);
  z-index: 10;
}
</style>
