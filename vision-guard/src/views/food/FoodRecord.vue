<template>
  <div class="record-page">
    <div class="content">
      <!-- Meal selector -->
      <div class="card fu">
        <div class="card-title">选择餐次</div>
        <div class="meal-row">
          <button
            v-for="m in meals" :key="m"
            class="meal-btn" :class="{ on: meal === m }"
            @click="meal = m"
          >{{ m }}</button>
        </div>

        <div class="card-title" style="margin-top:12px">拍照或上传图片</div>
        <div class="upload-zone" :class="{ 'has-img': !!imgSrc }" @click="triggerUpload">
          <img v-if="imgSrc" :src="imgSrc" class="upload-img" />
          <template v-else>
            <div style="font-size:36px;margin-bottom:8px">📷</div>
            <div style="font-size:14px;font-weight:700;color:var(--teal);margin-bottom:4px">点击拍照 / 上传图片</div>
            <div style="font-size:12px;color:var(--sub);line-height:1.5">拍下你的餐食，AI自动识别<br/>视力相关营养素含量</div>
          </template>
        </div>
        <input ref="fileInput" type="file" accept="image/*" capture="environment" style="display:none" @change="onFile" />
        <button v-if="imgSrc" class="btn-outline" style="width:100%;margin-top:8px;text-align:center" @click="imgSrc=''; triggerUpload()">
          🔄 重新拍
        </button>
      </div>

      <!-- Text input -->
      <div class="card fu fu-1">
        <div class="card-title">
          补充说明
          <span style="font-size:12px;color:var(--sub);font-weight:400">（可选）</span>
        </div>
        <textarea
          class="text-input"
          rows="3"
          v-model="textNote"
          placeholder="例如：吃了一碗菠菜炒蛋，一碗米饭，还有半杯牛奶…"
        />
      </div>

      <!-- Actions -->
      <div style="display:flex;gap:8px">
        <button class="btn-outline" @click="router.back()">← 返回</button>
        <button
          class="btn-main" style="flex:1"
          :disabled="!imgSrc && !textNote.trim()"
          @click="analyze"
        >
          {{ analyzing ? '分析中…' : '🔍 AI 分析营养' }}
        </button>
      </div>

      <!-- AI Result -->
      <div v-if="result" class="card fu" style="margin-top:4px">
        <div class="card-title">🤖 AI 识别结果 <span class="chip chip--teal">{{ meal }}</span></div>
        <div class="ai-result">
          <div class="ai-section-title">🍽️ 识别到的食物</div>
          <div class="ai-food-row">
            <span v-for="(f, i) in result.foods" :key="i" class="ai-food-tag">
              {{ f.name }} <span style="color:var(--sub);font-weight:400">{{ f.portion }}</span>
            </span>
          </div>
          <div class="ai-section-title" style="margin-top:10px">👁️ 视力营养贡献</div>
          <div class="ai-nut-grid">
            <div v-for="[k, n] in nutEntries" :key="k" class="ai-nut-item">
              <div style="font-size:16px">{{ n.icon }}</div>
              <div class="ai-nut-pct" :style="{ color: nutPct(k) > 0 ? n.color : 'var(--border)' }">{{ nutPct(k) }}%</div>
              <div class="ai-nut-name">{{ n.name }}</div>
            </div>
          </div>
          <div class="ai-feedback" v-if="result.feedback">
            <div style="font-size:11px;color:var(--teal);font-weight:700;margin-bottom:4px">🌟 AI反馈</div>
            {{ result.feedback }}
          </div>
        </div>
        <button class="btn-main" style="margin-top:12px" @click="save">✅ 保存记录</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NUTRIENTS } from '@/data/nutrients'

const router = useRouter()

const meals = ['早餐', '午餐', '晚餐', '加餐']
const meal = ref('午餐')
const imgSrc = ref('')
const textNote = ref('')
const analyzing = ref(false)
const fileInput = ref<HTMLInputElement>()

interface AIResult {
  foods: { name: string; portion: string }[]
  nutrients: Record<string, number>
  feedback: string
}

const result = ref<AIResult | null>(null)

const nutEntries = computed(() => Object.entries(NUTRIENTS))

function nutPct(key: string) {
  const val = result.value?.nutrients[key] || 0
  const daily = NUTRIENTS[key]?.daily || 1
  return Math.min(Math.round(val / daily * 100), 100)
}

function triggerUpload() { fileInput.value?.click() }

function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (!f) return
  const reader = new FileReader()
  reader.onload = ev => { imgSrc.value = ev.target?.result as string }
  reader.readAsDataURL(f)
}

async function analyze() {
  if (!imgSrc.value && !textNote.value.trim()) return
  analyzing.value = true

  try {
    // TODO: call POST /api/v1/vision/ai/analyze-food when backend ready
    // For now, use mock data
    await new Promise(r => setTimeout(r, 1500))
    result.value = {
      foods: [
        { name: '菠菜炒蛋', portion: '一份' },
        { name: '米饭', portion: '一碗' },
      ],
      nutrients: { lutein: 4.2, dha: 80, vitA: 320, vitC: 18, vitD: 1.1, zinc: 1.2 },
      feedback: '今天吃了菠菜和鸡蛋，叶黄素摄入不错！可以再加些橙色蔬果补充维生素A。',
    }
  } finally {
    analyzing.value = false
  }
}

function save() {
  // TODO: persist to store / API
  router.push('/food')
}
</script>

<style scoped>
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.meal-row { display: flex; gap: 6px; }
.meal-btn {
  flex: 1; padding: 8px 4px; border-radius: 10px;
  border: 1.5px solid var(--border); background: white;
  font-size: 12px; font-weight: 600; cursor: pointer;
  text-align: center; color: var(--sub); transition: all .2s;
}
.meal-btn.on { background: var(--teal-l); border-color: var(--teal); color: var(--teal); }
.upload-zone {
  border: 2px dashed var(--border-m); border-radius: 16px;
  background: var(--teal-l); padding: 28px 20px;
  text-align: center; cursor: pointer; transition: all .2s;
}
.upload-zone.has-img { padding: 0; border-style: solid; border-color: var(--teal); }
.upload-img { width: 100%; border-radius: 14px; display: block; max-height: 220px; object-fit: cover; }
.text-input {
  width: 100%; border: 1.5px solid var(--border); border-radius: 12px;
  padding: 12px; font-size: 13px; resize: none; outline: none;
  color: var(--ink); background: white; transition: border-color .2s; line-height: 1.6;
}
.text-input:focus { border-color: var(--teal); }
.ai-result {
  background: linear-gradient(135deg, var(--teal-l), #E0F7F3);
  border-radius: 16px; padding: 16px; border: 1.5px solid var(--border-m);
}
.ai-section-title { font-size: 13px; font-weight: 700; color: var(--teal); margin-bottom: 8px; }
.ai-food-row { display: flex; gap: 6px; flex-wrap: wrap; }
.ai-food-tag {
  background: white; border: 1px solid var(--border-m); border-radius: 8px;
  padding: 4px 10px; font-size: 12px; font-weight: 600; color: var(--ink);
}
.ai-nut-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 10px; }
.ai-nut-item { background: white; border-radius: 10px; padding: 8px; text-align: center; border: 1px solid var(--border); }
.ai-nut-pct { font-size: 16px; font-weight: 900; }
.ai-nut-name { font-size: 10px; color: var(--sub); margin-top: 2px; }
.ai-feedback {
  background: white; border-radius: 12px; padding: 12px;
  font-size: 13px; color: var(--ink); line-height: 1.6;
  border-left: 4px solid var(--teal); margin-top: 10px;
}
</style>
