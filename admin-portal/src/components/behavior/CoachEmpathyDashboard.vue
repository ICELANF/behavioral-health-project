<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 p-6 bg-gradient-to-br from-sky-50 via-emerald-50/30 to-blue-50/50 min-h-screen">

    <section class="bg-white/80 backdrop-blur-sm p-8 rounded-3xl shadow-2xl border-2 border-slate-200/50 relative overflow-hidden">
      <div class="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-slate-100 to-transparent opacity-30 rounded-full -mr-48 -mt-48"></div>

      <div class="relative z-10">
        <div class="flex items-center justify-between mb-8">
          <div class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-full bg-emerald-400 animate-pulse"></div>
            <h3 class="text-sm font-bold text-slate-600 uppercase tracking-widest">
              用户视角 (镜像)
            </h3>
          </div>
          <span class="px-4 py-2 bg-slate-900 text-white rounded-full text-xs font-bold shadow-lg">
            {{ userData.user_id }}
          </span>
        </div>

        <div class="pointer-events-none opacity-95 scale-[0.96] origin-top">
          <UserIdentityHeader :stage="userData.stage" />
          <BehaviorTaskCard
            :stage="userData.stage"
            :task-name="userData.current_task"
            @interact="() => {}"
          />
        </div>
      </div>
    </section>

    <section class="space-y-6">
      <div class="bg-gradient-to-r from-slate-900 to-slate-800 p-8 rounded-3xl shadow-2xl text-white">
        <h3 class="text-2xl font-bold mb-2 flex items-center gap-3">
          <span class="text-3xl">&#127919;</span>
          <span>干预决策支持</span>
        </h3>
        <p class="text-slate-300 text-sm">基于行为数据与阶段的建议</p>
      </div>

      <div class="bg-white p-8 rounded-3xl shadow-xl border-2 border-slate-200/50">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
            <span class="text-xl">&#128202;</span>
          </div>
          <div class="text-sm font-bold text-slate-500 uppercase tracking-wide">最近行为状态</div>
        </div>

        <div class="flex items-center gap-4 mb-6">
          <div :class="[
            'text-3xl font-bold px-6 py-3 rounded-2xl',
            lastStatus.state === 'DONE' ? 'bg-emerald-50 text-emerald-600' :
            lastStatus.state === 'ATTEMPTED' ? 'bg-amber-50 text-amber-600' : 'bg-slate-50 text-slate-400'
          ]">
            {{
              lastStatus.state === 'DONE' ? '&#10003; 已完成' :
              lastStatus.state === 'ATTEMPTED' ? '&#9208;&#65039; 尝试但未完成' : '&#9675; 未响应'
            }}
          </div>
        </div>

        <div
          v-if="lastStatus.state === 'ATTEMPTED'"
          class="relative mt-6 p-6 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 text-amber-900 rounded-2xl overflow-hidden"
        >
          <div class="absolute top-0 right-0 text-8xl opacity-5">&#128161;</div>
          <div class="relative z-10">
            <div class="flex items-start gap-3 mb-3">
              <span class="text-2xl">&#128161;</span>
              <div>
                <div class="font-bold text-lg mb-2">系统建议</div>
                <p class="text-sm leading-relaxed">
                  用户有改变意愿，但遇到了阻力。建议发送支持性消息，询问：<br>
                  <span class="font-semibold">"在这个过程中，哪里让你感觉最困难？"</span>
                </p>
              </div>
            </div>
            <div class="mt-4 p-4 bg-amber-100 rounded-xl border-l-4 border-amber-600">
              <span class="font-bold text-amber-900">&#9888;&#65039; 切勿责备或施压。</span>
            </div>
          </div>
        </div>
      </div>

      <div class="grid gap-4">
        <button class="group relative p-6 bg-white border-2 border-slate-200 rounded-2xl hover:border-slate-300 text-left transition-all duration-300 hover:shadow-xl overflow-hidden">
          <div class="absolute inset-0 bg-gradient-to-r from-blue-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div class="relative z-10 flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center text-2xl">
              &#128172;
            </div>
            <div>
              <div class="font-bold text-slate-900 mb-1">发送阶段性鼓励</div>
              <div class="text-sm text-slate-500">Template A - 支持性消息</div>
            </div>
          </div>
        </button>

        <button class="group relative p-6 bg-white border-2 border-red-200 rounded-2xl hover:border-red-300 text-left transition-all duration-300 hover:shadow-xl overflow-hidden">
          <div class="absolute inset-0 bg-gradient-to-r from-red-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div class="relative z-10 flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-red-100 to-red-200 flex items-center justify-center text-2xl">
              &#128680;
            </div>
            <div>
              <div class="font-bold text-slate-900 mb-1">标记为需要专家介入</div>
              <div class="text-sm text-slate-500">Escalate - 升级处理</div>
            </div>
          </div>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import UserIdentityHeader from './UserIdentityHeader.vue';
import BehaviorTaskCard from './BehaviorTaskCard.vue';
import type { Stage, CompletionState } from '../core/types';

interface HistoryEntry {
  state: CompletionState;
  date: string;
}

interface UserData {
  user_id: string;
  stage: Stage;
  current_task: string;
  history: HistoryEntry[];
}

const props = defineProps<{
  userData: UserData;
}>();

const lastStatus = computed(() =>
  props.userData.history[0] || { state: 'PENDING' as CompletionState, date: '今日' }
);
</script>
