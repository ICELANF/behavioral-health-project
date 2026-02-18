<template>
  <div class="bg-white p-8 rounded-3xl shadow-xl border-2 border-slate-100/50 backdrop-blur">
    <div class="flex items-center gap-2 mb-6">
      <div
        class="w-1.5 h-8 rounded-full"
        :style="{ background: `linear-gradient(to bottom, ${config.gradientFrom}, ${config.gradientTo})` }"
      ></div>
      <h2 class="text-base font-semibold text-slate-600">
        {{ config.taskTitle }}
      </h2>
    </div>

    <div class="relative bg-gradient-to-br from-slate-50 to-slate-100/50 p-6 rounded-2xl mb-8 border border-slate-200/50">
      <div class="text-3xl font-bold text-slate-900 mb-2 leading-tight">
        {{ taskName }}
      </div>
      <div class="absolute top-4 right-4 text-4xl opacity-10">
        {{ config.icon }}
      </div>
    </div>

    <div class="space-y-4">
      <button
        @click="handleAction('DONE')"
        class="group relative w-full py-5 rounded-2xl font-bold text-lg overflow-hidden transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
        :style="{
          background: `linear-gradient(135deg, ${config.gradientFrom} 0%, ${config.gradientTo} 100%)`,
          color: 'white'
        }"
      >
        <div class="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-300"></div>
        <span class="relative z-10 flex items-center justify-center gap-2">
          <span>&#10003;</span>
          <span>我已完成</span>
        </span>
      </button>

      <button
        @click="handleAction('ATTEMPTED')"
        class="group relative w-full py-5 bg-white border-3 rounded-2xl font-semibold text-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-md hover:shadow-lg"
        :style="{
          borderColor: config.gradientFrom,
          borderWidth: '2px',
          color: config.textColor
        }"
      >
        <div class="absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-300 rounded-2xl"
          :style="{ background: config.gradientFrom }"></div>
        <span class="relative z-10 flex items-center justify-center gap-2">
          <span>&#9208;&#65039;</span>
          <span>我尝试了，但没完成</span>
        </span>
      </button>
    </div>

    <div class="mt-8 text-center">
      <div class="inline-flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-full">
        <span class="text-slate-400">&#128161;</span>
        <span class="text-sm text-slate-500 font-medium">诚实记录比完美表现更重要</span>
      </div>
    </div>
  </div>

  <Transition
    enter-active-class="transition-opacity duration-300"
    leave-active-class="transition-opacity duration-200"
    enter-from-class="opacity-0"
    leave-to-class="opacity-0"
  >
    <div
      v-if="showFeedback"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      @click="showFeedback = false"
    >
      <Transition
        enter-active-class="transition-all duration-300"
        leave-active-class="transition-all duration-200"
        enter-from-class="opacity-0 scale-95"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="showFeedback"
          class="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl"
          @click.stop
        >
          <div class="text-center mb-6">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4"
              :style="{ background: `linear-gradient(135deg, ${config.gradientFrom}, ${config.gradientTo})` }">
              <span class="text-3xl">&#128154;</span>
            </div>
            <div class="text-2xl font-bold text-slate-900 mb-2">系统反馈</div>
          </div>
          <p class="text-slate-700 text-lg leading-relaxed text-center mb-8">
            收到。尝试本身就是一种成功，今天到此为止，好好休息。
          </p>
          <button
            @click="showFeedback = false"
            class="w-full py-4 rounded-2xl font-bold text-lg text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
            :style="{ background: `linear-gradient(135deg, ${config.gradientFrom}, ${config.gradientTo})` }"
          >
            知道了
          </button>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { STAGE_CONFIG, type Stage, type CompletionState } from '../core/types';

const props = defineProps<{
  stage: Stage;
  taskName: string;
}>();

const emit = defineEmits<{
  interact: [state: CompletionState];
}>();

const config = computed(() => STAGE_CONFIG[props.stage]);
const showFeedback = ref(false);

const handleAction = (state: CompletionState) => {
  emit('interact', state);

  if (state === 'ATTEMPTED') {
    showFeedback.value = true;
  }
};
</script>
