<template>
  <div class="screen">
    <div class="land-bg" style="opacity:.5">
      <div class="orb" :style="{ background: doorData.color, width: '200px', height: '200px', top: '-50px', right: '-50px', opacity: '.15', position:'absolute', borderRadius:'50%', filter:'blur(60px)' }" />
    </div>
    <div class="scene-hdr fu">
      <div class="scene-back" @click="$router.push('/')">← 返回</div>
      <div class="scene-title">{{ doorData.title }}</div>
      <div class="scene-sub">{{ doorData.desc }}</div>
      <div class="scene-hint">可多选，选择所有符合你的场景</div>
    </div>
    <div class="pg" style="padding-top:0">
      <div class="scene-items">
        <div v-for="(s, i) in doorData.scenes" :key="i"
          :class="['scene-item', 'fu', `d${(i % 4) + 1}`, { sel: store.scenes.includes(i) }]"
          @click="store.toggleScene(i)">
          <div class="scene-item-ico">{{ s.ico }}</div>
          <div class="scene-item-body">
            <div class="scene-item-text">{{ s.text }}</div>
            <div class="scene-item-sub">{{ s.sub }}</div>
          </div>
          <div class="scene-item-check" :style="store.scenes.includes(i) ? { background: doorData.color, borderColor: doorData.color } : {}">
            {{ store.scenes.includes(i) ? '✓' : '' }}
          </div>
        </div>
      </div>
      <button class="btn-main" :disabled="store.scenes.length === 0"
        :style="{ background: store.scenes.length > 0 ? doorData.color : 'rgba(0,0,0,.06)',
                   color: store.scenes.length > 0 ? '#fff' : D.muted, marginTop: '4px',
                   boxShadow: store.scenes.length > 0 ? `0 4px 14px ${doorData.color}40` : 'none' }"
        @click="$router.push('/belief')">
        {{ store.scenes.length > 0 ? `已选 ${store.scenes.length} 项，继续 →` : '请选择至少一项' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'
import { DOORS } from '@/data/doors'
import { D } from '@/design/tokens'

const store = useAssessmentStore()
const doorData = computed(() => DOORS.find(d => d.key === store.door) || DOORS[0])
</script>

<style scoped>
.scene-hdr { padding: 24px 22px 16px; position: relative; z-index: 2; }
.scene-back { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--sub); cursor: pointer; margin-bottom: 16px; padding: 6px 0; }
.scene-title { font-family: 'ZCOOL XiaoWei', serif; font-size: 28px; color: var(--ink); line-height: 1.3; margin-bottom: 6px; }
.scene-sub { font-size: 13px; color: var(--sub); line-height: 1.6; }
.scene-hint { font-size: 11px; color: var(--teal); margin-top: 6px; font-weight: 500; }
.scene-items { display: flex; flex-direction: column; gap: 10px; }
.scene-item {
  border-radius: 18px; padding: 16px; cursor: pointer;
  border: 1.5px solid var(--border); background: var(--card);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  display: flex; align-items: center; gap: 14px; transition: all .25s;
}
.scene-item.sel {
  border-color: v-bind('doorData.color');
  background: var(--card);
  box-shadow: 0 0 0 3px color-mix(in srgb, v-bind('doorData.color') 12%, transparent);
}
.scene-item:active { transform: scale(.98); }
.scene-item-ico { font-size: 24px; width: 40px; text-align: center; flex-shrink: 0; }
.scene-item-body { flex: 1; }
.scene-item-text { font-size: 14px; font-weight: 600; color: var(--ink); margin-bottom: 2px; }
.scene-item-sub { font-size: 11px; color: var(--sub); line-height: 1.4; }
.scene-item-check {
  width: 22px; height: 22px; border-radius: 6px; border: 1.5px solid var(--border-m);
  flex-shrink: 0; display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #fff; transition: all .25s;
}
</style>
