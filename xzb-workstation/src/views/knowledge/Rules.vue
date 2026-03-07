<template>
  <div class="rules-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      规则编辑器
    </div>
    <div class="content">
      <button class="btn-main fu" style="width:100%" @click="showAdd = true">+ 新建规则</button>

      <div v-for="rule in rules" :key="rule.id" class="card fu fu-1">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
          <div class="rule-badge" :class="rule.overrides_llm ? 'override' : ''">
            {{ rule.overrides_llm ? '覆盖LLM' : '建议' }}
          </div>
          <div style="font-size:13px;font-weight:700;flex:1">{{ rule.rule_name }}</div>
          <div class="chip" :class="rule.is_active ? 'chip--teal' : 'chip--red'">
            {{ rule.is_active ? '启用' : '停用' }}
          </div>
        </div>
        <div style="font-size:12px;color:var(--sub)">
          动作: {{ rule.action_type }} &middot; 优先级: {{ rule.priority }}
        </div>
      </div>

      <div v-if="rules.length === 0" class="card fu fu-1" style="text-align:center;padding:32px">
        <div style="font-size:14px;font-weight:700">暂无规则</div>
        <div style="font-size:13px;color:var(--sub)">创建规则来引导 AI 智伴的行为。</div>
      </div>

      <div v-if="showAdd" class="modal-mask" @click.self="showAdd = false">
        <div class="modal-body">
          <div style="font-size:16px;font-weight:800;margin-bottom:16px">新建规则</div>
          <van-field v-model="newRule.rule_name" label="规则名称" placeholder="例如：糖尿病胰岛素规则" />
          <div style="margin-top:8px">
            <div style="font-size:12px;font-weight:600;color:var(--sub);margin-bottom:4px">动作类型</div>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <div v-for="a in actionTypes" :key="a.key"
                class="filter-chip" :class="{ sel: newRule.action_type === a.key }"
                @click="newRule.action_type = a.key">{{ a.label }}</div>
            </div>
          </div>
          <van-field v-model="newRule.action_content" label="动作内容" type="textarea" rows="3" placeholder="规则触发后执行的内容..." style="margin-top:8px" />
          <div style="display:flex;gap:8px;align-items:center;margin-top:12px">
            <label style="font-size:12px;display:flex;align-items:center;gap:6px">
              <input type="checkbox" v-model="newRule.overrides_llm" /> 覆盖LLM
            </label>
            <span style="flex:1" />
            <van-field v-model.number="newRule.priority" label="优先级" type="number" style="width:100px" />
          </div>
          <div style="display:flex;gap:8px;margin-top:16px">
            <button class="btn-outline" style="flex:1" @click="showAdd = false">取消</button>
            <button class="btn-main" style="flex:1" @click="addRule">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listRules, createRule } from '@/api/xzb'

const router = useRouter()
const showAdd = ref(false)

interface Rule {
  id: string; rule_name: string; action_type: string
  priority: number; overrides_llm: boolean; is_active: boolean
}

const rules = ref<Rule[]>([])

const actionTypes = [
  { key: 'warn', label: '警告' },
  { key: 'block', label: '阻断' },
  { key: 'suggest', label: '建议' },
  { key: 'escalate', label: '上报' },
  { key: 'auto_reply', label: '自动回复' },
]

const newRule = reactive({
  rule_name: '', action_type: 'suggest', action_content: '',
  condition_json: {}, priority: 5, overrides_llm: false,
})

async function loadData() {
  try {
    const res = await listRules()
    rules.value = res.data.items || []
  } catch { rules.value = [] }
}

async function addRule() {
  try {
    await createRule({
      rule_name: newRule.rule_name,
      condition_json: newRule.condition_json,
      action_type: newRule.action_type,
      action_content: newRule.action_content,
      priority: newRule.priority,
      overrides_llm: newRule.overrides_llm,
    })
    showAdd.value = false
    loadData()
  } catch { /* ignore */ }
}

onMounted(loadData)
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 10px;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.rule-badge {
  font-size: 9px; font-weight: 800; padding: 3px 8px; border-radius: 6px;
  background: var(--xzb-primary-l); color: var(--xzb-primary);
}
.rule-badge.override { background: #FEE; color: var(--xzb-red); }
.modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: flex-end; z-index: 200;
}
.modal-body {
  background: white; width: 100%; max-width: 480px; margin: 0 auto;
  border-radius: 20px 20px 0 0; padding: 24px 20px env(safe-area-inset-bottom, 20px);
  max-height: 80vh; overflow-y: auto;
}
.filter-chip {
  padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;
  border: 1.5px solid var(--border); color: var(--sub); cursor: pointer; transition: all .2s;
}
.filter-chip.sel { border-color: var(--xzb-primary); background: var(--xzb-primary-l); color: var(--xzb-primary); }
</style>
