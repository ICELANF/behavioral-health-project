<template>
  <div class="onboarding">
    <div class="content" v-if="!done">
      <div class="card fu">
        <div style="font-size:12px;color:var(--sub);margin-bottom:8px">
          MVEP 初始化 &middot; 第 {{ step }}/{{ totalSteps }} 步
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (step / totalSteps * 100) + '%' }" />
        </div>

        <!-- Step 1: 品牌命名 -->
        <template v-if="step === 1">
          <div class="step-title">为您的 AI 智伴命名</div>
          <div class="step-desc">给您的 AI 智伴取一个体现诊疗风格的名字，这是患者认识智伴的第一印象。</div>
          <van-field v-model="form.companion_name" label="智伴名称" placeholder="例如：健康小助手" />
          <van-field v-model="form.display_name" label="您的姓名" placeholder="您的显示名称" style="margin-top:8px" />
        </template>

        <!-- Step 2: 专科方向（多选） -->
        <template v-if="step === 2">
          <div class="step-title">您的专科方向</div>
          <div class="step-desc">选择您擅长的领域（可多选），AI 将据此优化知识检索策略。</div>
          <div class="tag-grid">
            <div v-for="s in specialties" :key="s"
              class="tag-chip" :class="{ sel: form.specialties.includes(s) }"
              @click="toggleSpecialty(s)">{{ s }}</div>
          </div>
          <div v-if="form.specialties.length > 0" style="font-size:12px;color:var(--xzb-primary);margin-top:8px;font-weight:600">
            已选 {{ form.specialties.length }} 个领域：{{ form.specialties.join('、') }}
          </div>
        </template>

        <!-- Step 3: 中医权重 -->
        <template v-if="step === 3">
          <div class="step-title">中医融合度</div>
          <div class="step-desc">您的智伴在回答中融入多少中医思维？（0 = 纯现代医学，1 = 重度中医）</div>
          <div style="display:flex;align-items:center;gap:12px;margin-top:16px">
            <span style="font-size:12px;color:var(--sub)">现代</span>
            <input type="range" min="0" max="100" v-model.number="tcmPct" style="flex:1" />
            <span style="font-size:12px;color:var(--sub)">中医</span>
          </div>
          <div style="text-align:center;margin-top:8px;font-size:24px;font-weight:900;color:var(--xzb-primary)">
            {{ (tcmPct / 100).toFixed(2) }}
          </div>
        </template>

        <!-- Step 4: 问候语 -->
        <template v-if="step === 4">
          <div class="step-title">智伴问候语</div>
          <div class="step-desc">这是求助者开始对话时看到的第一条消息。</div>
          <textarea class="text-input" rows="3" v-model="form.greeting"
            :placeholder="`您好，我是${form.companion_name || '您的AI健康助手'}，有什么可以帮您的？`" />
        </template>

        <!-- Step 5: 安全边界声明 -->
        <template v-if="step === 5">
          <div class="step-title">安全边界声明</div>
          <div class="step-desc">此免责声明会在求助者首次交互时展示，设定 AI 辅助诊疗的预期。</div>
          <textarea class="text-input" rows="4" v-model="form.boundary_stmt"
            placeholder="我是AI健康助手，不替代专科就诊，如有紧急情况请立即就医。" />
        </template>

        <!-- Step 6: 领域标签 -->
        <template v-if="step === 6">
          <div class="step-title">领域标签</div>
          <div class="step-desc">选择您擅长的病种和领域，AI 将在这些领域优先调用知识。</div>
          <div class="tag-grid">
            <div v-for="t in domainOptions" :key="t"
              class="tag-chip" :class="{ sel: form.domain_tags.includes(t) }"
              @click="toggleTag(t)">{{ t }}</div>
          </div>
        </template>

        <div class="step-nav">
          <button v-if="step > 1" class="btn-outline" @click="step--">上一步</button>
          <button class="btn-main" style="flex:1" @click="nextStep"
            :disabled="!canProceed">
            {{ step < totalSteps ? '下一步' : '完成初始化' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 完成 -->
    <div class="content" v-else>
      <div class="card fu" style="text-align:center;padding:32px 20px">
        <div class="logo-ring" style="margin:0 auto 16px">XZB</div>
        <div style="font-size:20px;font-weight:900;color:var(--xzb-primary);margin-bottom:8px">
          {{ form.companion_name }} 已就绪！
        </div>
        <div style="font-size:13px;color:var(--sub);line-height:1.6;margin-bottom:20px">
          您的 AI 智伴已完成专业画像初始化。现在可以开始上传知识和配置规则了。
        </div>
        <button class="btn-main" @click="router.push('/')">进入工作站</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { registerExpert } from '@/api/xzb'
import { useExpertStore } from '@/stores/expert'

const router = useRouter()
const store = useExpertStore()
const step = ref(1)
const totalSteps = 6
const done = ref(false)
const tcmPct = ref(30)

const form = reactive({
  display_name: '',
  companion_name: '',
  specialties: [] as string[],
  greeting: '',
  boundary_stmt: '',
  domain_tags: [] as string[],
  license_no: '',
})

const specialties = [
  '糖尿病', '心血管', '心理健康', '中医',
  '营养', '运动', '睡眠', '体重管理',
]

const domainOptions = [
  '2型糖尿病', '高血压', '肥胖', '失眠', '焦虑',
  '抑郁', '慢性疼痛', '肠道健康', '中医体质',
  '运动处方', '营养', '压力管理',
]

function toggleSpecialty(s: string) {
  const idx = form.specialties.indexOf(s)
  if (idx >= 0) form.specialties.splice(idx, 1)
  else form.specialties.push(s)
}

function toggleTag(t: string) {
  const idx = form.domain_tags.indexOf(t)
  if (idx >= 0) form.domain_tags.splice(idx, 1)
  else form.domain_tags.push(t)
}

const canProceed = computed(() => {
  if (step.value === 1) return form.companion_name.trim() && form.display_name.trim()
  if (step.value === 2) return form.specialties.length > 0
  if (step.value === 6) return form.domain_tags.length > 0
  return true
})

async function nextStep() {
  if (step.value < totalSteps) {
    step.value++
    return
  }
  try {
    await registerExpert({
      display_name: form.display_name,
      companion_name: form.companion_name,
      specialty: form.specialties.join(','),
      tcm_weight: tcmPct.value / 100,
      domain_tags: form.domain_tags,
      license_no: form.license_no,
      greeting: form.greeting,
      boundary_stmt: form.boundary_stmt,
    })
    await store.loadAll()
    done.value = true
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '注册失败'
    alert(msg)
  }
}
</script>

<style scoped>
.onboarding { min-height: 100vh; background: var(--bg); }
.content { padding: 14px; }
.progress-bar { height: 5px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 20px; }
.progress-fill { height: 100%; background: var(--grad-header); border-radius: 3px; transition: width .4s; }
.step-title { font-size: 18px; font-weight: 800; color: var(--ink); margin-bottom: 6px; }
.step-desc { font-size: 13px; color: var(--sub); line-height: 1.6; margin-bottom: 16px; }
.tag-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-chip {
  padding: 8px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
  border: 1.5px solid var(--border); color: var(--sub); cursor: pointer; transition: all .2s;
}
.tag-chip.sel { border-color: var(--xzb-primary); background: var(--xzb-primary-l); color: var(--xzb-primary); }
.step-nav { display: flex; gap: 8px; margin-top: 20px; }
.text-input {
  width: 100%; border: 1.5px solid var(--border); border-radius: 12px;
  padding: 12px; font-size: 13px; resize: none; outline: none;
  color: var(--ink); background: white; transition: border-color .2s; line-height: 1.6;
}
.text-input:focus { border-color: var(--xzb-primary); }
.logo-ring {
  width: 64px; height: 64px; border-radius: 50%;
  background: var(--grad-header); color: white;
  font-size: 20px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
}
</style>
