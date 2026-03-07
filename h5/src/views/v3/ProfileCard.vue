<template>
  <div class="profile-card-page">
    <template v-if="loading">
      <div class="loading">加载中...</div>
    </template>
    <template v-else-if="!profile">
      <div class="empty">
        <p>尚未完成评估</p>
        <button class="btn-primary" @click="$router.push('/v3/motivation-quiz')">开始评估</button>
      </div>
    </template>
    <template v-else>
      <!-- 三维标签 (UI-01) -->
      <div class="tags-row">
        <!-- 人格类型 -->
        <div class="tag-block personality" v-if="profile.personality_archetype">
          <span class="tag-label">人格类型</span>
          <span class="tag-value">{{ archetypeLabels[profile.personality_archetype]?.name || profile.personality_archetype }}</span>
          <span class="tag-desc">{{ archetypeLabels[profile.personality_archetype]?.desc || '' }}</span>
        </div>
        <!-- 动机类型 -->
        <div class="tag-block motivation" v-if="profile.motivation_type">
          <span class="tag-label">动机类型</span>
          <span class="tag-value">{{ motivationLabels[profile.motivation_type]?.name || profile.motivation_type }}</span>
          <span class="tag-desc">{{ motivationLabels[profile.motivation_type]?.desc || '' }}</span>
        </div>
        <!-- 行为风格 (UI-01: BPT-6第三标签) -->
        <div class="tag-block bpt6" v-if="profile.bpt6_type">
          <span class="tag-label">行为风格</span>
          <span class="tag-value">{{ profile.bpt6_label?.name || profile.bpt6_type }}</span>
          <span class="tag-desc">{{ profile.bpt6_label?.desc || '' }}</span>
        </div>
      </div>

      <!-- 阶段信息 -->
      <div class="stage-card" v-if="profile.stage">
        <div class="stage-badge">{{ profile.stage }}</div>
        <div class="stage-info">
          <span class="stage-name">{{ profile.stage_name || '评估中' }}</span>
          <span class="stage-spi" v-if="profile.spi_score">
            准备度 {{ Math.round(profile.spi_score) }}%
          </span>
        </div>
      </div>

      <!-- 大五雷达 -->
      <div class="big5-section" v-if="profile.big5_scores">
        <h3>人格维度</h3>
        <div class="big5-bars">
          <div v-for="(dim, key) in big5Dims" :key="key" class="dim-bar">
            <span class="dim-name">{{ dim.name }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: dimPct(profile.big5_scores[key]) + '%' }"></div>
            </div>
            <span class="dim-level">{{ profile.big5_scores[key]?.level || '-' }}</span>
          </div>
        </div>
      </div>

      <!-- 能力与弱项 -->
      <div class="capacity-section" v-if="profile.capacity_total">
        <h3>改变潜力 <span class="capacity-score">{{ profile.capacity_total }}分</span></h3>
        <div class="capacity-tags">
          <span v-for="s in (profile.capacity_strong || [])" :key="s" class="cap-tag strong">{{ s }}</span>
          <span v-for="w in (profile.capacity_weak || [])" :key="w" class="cap-tag weak">{{ w }}</span>
        </div>
      </div>

      <!-- P×M 策略建议 -->
      <div class="strategy-section" v-if="profile.strategy">
        <h3>你的专属策略</h3>
        <div class="strategy-card">
          <p v-if="profile.strategy.entry"><strong>切入点：</strong>{{ profile.strategy.entry }}</p>
          <p v-if="profile.strategy.prescription"><strong>处方：</strong>{{ profile.strategy.prescription }}</p>
          <p v-if="profile.strategy.format"><strong>形式：</strong>{{ profile.strategy.format }}</p>
          <p v-if="profile.strategy.caution" class="caution"><strong>注意：</strong>{{ profile.strategy.caution }}</p>
        </div>
      </div>

      <!-- 行动按钮 -->
      <div class="actions">
        <button class="btn-primary" @click="$router.push('/v3/prescription-card')">查看行为处方</button>
        <button class="btn-secondary" @click="$router.push('/v3/motivation-quiz')">重新评估</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'

const loading = ref(true)
const profile = ref<any>(null)

const archetypeLabels: Record<string, { name: string; desc: string }> = {
  P1: { name: '稳定执行者', desc: '纪律性强，可靠务实' },
  P2: { name: '开放探索者', desc: '好奇心强，灵活多变' },
  P3: { name: '完美主义者', desc: '高标准，责任感强' },
  P4: { name: '社交领袖', desc: '善于激励，影响力强' },
  P5: { name: '内向独立者', desc: '自主性强，深度思考' },
}

const motivationLabels: Record<string, { name: string; desc: string }> = {
  M1: { name: '健康守护', desc: '为健康而改变' },
  M2: { name: '家庭责任', desc: '为家人而坚持' },
  M3: { name: '自由成就', desc: '追求更好的自己' },
  M4: { name: '平静安宁', desc: '寻求内心平衡' },
  M5: { name: '意义探索', desc: '探索生命意义' },
}

const big5Dims: Record<string, { name: string }> = {
  E: { name: '外向性' },
  N: { name: '情绪性' },
  C: { name: '尽责性' },
  A: { name: '宜人性' },
  O: { name: '开放性' },
}

function dimPct(dim: any): number {
  if (!dim) return 50
  const score = typeof dim === 'object' ? dim.score : dim
  return Math.max(5, Math.min(95, ((score + 40) / 80) * 100))
}

onMounted(async () => {
  try {
    const res = await request.get('/api/v1/guixin/profile-card')
    profile.value = res.data
  } catch (e: any) {
    if (e?.response?.status !== 404) console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.profile-card-page {
  max-width: 430px;
  margin: 0 auto;
  padding: 20px 16px;
  min-height: 100vh;
  background: linear-gradient(180deg, #f0f4ff 0%, #fff 30%);
}

.loading, .empty {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.tags-row {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}
.tag-block {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 12px 10px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.tag-label {
  display: block;
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
}
.tag-value {
  display: block;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 2px;
}
.tag-desc {
  display: block;
  font-size: 11px;
  color: #888;
  line-height: 1.3;
}
.tag-block.personality .tag-value { color: #4f6ef7; }
.tag-block.motivation .tag-value { color: #e67e22; }
.tag-block.bpt6 .tag-value { color: #27ae60; }

.stage-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stage-badge {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f6ef7, #7b61ff);
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stage-name { font-weight: 600; font-size: 16px; color: #1a1a2e; }
.stage-spi { font-size: 13px; color: #666; margin-left: 8px; }

h3 {
  font-size: 16px;
  color: #1a1a2e;
  margin-bottom: 12px;
}

.big5-section, .capacity-section, .strategy-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.dim-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.dim-name { width: 50px; font-size: 13px; color: #666; }
.bar-track { flex: 1; height: 8px; background: #eee; border-radius: 4px; }
.bar-fill { height: 100%; background: linear-gradient(90deg, #4f6ef7, #7b61ff); border-radius: 4px; transition: width 0.5s; }
.dim-level { width: 36px; font-size: 12px; color: #999; text-align: right; }

.capacity-score { font-size: 14px; color: #4f6ef7; font-weight: 400; }
.capacity-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.cap-tag {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}
.cap-tag.strong { background: #e8f5e9; color: #2e7d32; }
.cap-tag.weak { background: #fff3e0; color: #e65100; }

.strategy-card {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 12px;
}
.strategy-card p { font-size: 14px; color: #333; margin-bottom: 6px; line-height: 1.5; }
.strategy-card .caution { color: #e67e22; }

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 24px;
  padding-bottom: 40px;
}
.btn-primary {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #4f6ef7, #7b61ff);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}
.btn-secondary {
  width: 100%;
  padding: 14px;
  background: #fff;
  color: #4f6ef7;
  border: 1px solid #4f6ef7;
  border-radius: 12px;
  font-size: 16px;
  cursor: pointer;
}
</style>
