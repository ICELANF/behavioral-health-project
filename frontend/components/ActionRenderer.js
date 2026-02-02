/**
 * 行为健康数字平台 - ActionRenderer 全局组件
 * Action Renderer Component (Vue3)
 * 
 * [v15-NEW] Frontend UI Component
 * 
 * 功能：
 * - 通过 Props 接收后端 DSL（Action Package）
 * - 动态渲染不同类型的 UI 组件
 * - 统一处理用户交互回调
 * 
 * 使用方式：
 * <ActionRenderer 
 *   :action="actionPackage" 
 *   @callback="handleAction"
 * />
 * 
 * Action Package DSL 结构：
 * {
 *   "action_id": "PKG_WAKE_UP_CALL",
 *   "render_type": "INTERACTIVE_CARD",
 *   "payload": {
 *     "title": "晨间觉察",
 *     "content": "昨晚睡得怎么样？",
 *     "components": [...]
 *   }
 * }
 */

// ============================================
// ComponentFactory.vue - 组件工厂
// ============================================
export const ComponentFactory = {
  name: 'ComponentFactory',
  
  template: `
    <component 
      :is="componentMap[action.render_type]" 
      :data="action.payload"
      :action-id="action.action_id"
      @callback="handleCallback"
    />
  `,
  
  props: {
    action: {
      type: Object,
      required: true,
      validator: (value) => {
        return value.action_id && value.render_type && value.payload;
      }
    }
  },
  
  emits: ['callback'],
  
  setup(props, { emit }) {
    // 组件映射表
    const componentMap = {
      'INTERACTIVE_CARD': 'BehaviorCard',
      'QUICK_REPLY': 'QuickButtons',
      'SURVEY_MINI': 'StandardSurvey',
      'NOTIFICATION': 'NotificationCard',
      'COMPANION_MESSAGE': 'CompanionMessage',
      'TASK_CARD': 'TaskCard',
      'PROGRESS_TRACKER': 'ProgressTracker'
    };
    
    const handleCallback = (data) => {
      emit('callback', {
        action_id: props.action.action_id,
        ...data
      });
    };
    
    return {
      componentMap,
      handleCallback
    };
  }
};


// ============================================
// ActionRenderer.vue - 主渲染组件
// ============================================
export const ActionRendererTemplate = `
<template>
  <div class="action-renderer" :class="renderTypeClass">
    <!-- INTERACTIVE_CARD -->
    <div v-if="action.render_type === 'INTERACTIVE_CARD'" class="behavior-card">
      <div class="card-header" v-if="payload.title">
        <h3>{{ payload.title }}</h3>
        <span v-if="payload.subtitle" class="subtitle">{{ payload.subtitle }}</span>
      </div>
      
      <div class="card-content">
        <p v-if="payload.content">{{ payload.content }}</p>
        <img v-if="payload.image_url" :src="payload.image_url" class="card-image" />
      </div>
      
      <div class="card-components">
        <component
          v-for="comp in payload.components"
          :key="comp.id"
          :is="getComponentType(comp.type)"
          v-bind="comp"
          @action="handleComponentAction"
        />
      </div>
    </div>
    
    <!-- QUICK_REPLY -->
    <div v-else-if="action.render_type === 'QUICK_REPLY'" class="quick-reply">
      <p v-if="payload.content" class="reply-content">{{ payload.content }}</p>
      <div class="quick-buttons">
        <button
          v-for="reply in payload.quick_replies"
          :key="reply.id"
          class="quick-btn"
          @click="handleQuickReply(reply)"
        >
          {{ reply.text }}
        </button>
      </div>
    </div>
    
    <!-- COMPANION_MESSAGE -->
    <div v-else-if="action.render_type === 'COMPANION_MESSAGE'" class="companion-message" :class="uiStyleClass">
      <div class="message-bubble">
        <p>{{ payload.content }}</p>
      </div>
      <div class="message-actions" v-if="payload.components && payload.components.length">
        <component
          v-for="comp in payload.components"
          :key="comp.id"
          :is="getComponentType(comp.type)"
          v-bind="comp"
          @action="handleComponentAction"
        />
      </div>
    </div>
    
    <!-- NOTIFICATION -->
    <div v-else-if="action.render_type === 'NOTIFICATION'" class="notification-card" :class="notificationClass">
      <div class="notification-icon">
        <span v-if="isAlert">⚠️</span>
        <span v-else>📢</span>
      </div>
      <div class="notification-body">
        <h4>{{ payload.title }}</h4>
        <p>{{ payload.content }}</p>
      </div>
      <div class="notification-actions">
        <component
          v-for="comp in payload.components"
          :key="comp.id"
          :is="getComponentType(comp.type)"
          v-bind="comp"
          @action="handleComponentAction"
        />
      </div>
    </div>
    
    <!-- TASK_CARD -->
    <div v-else-if="action.render_type === 'TASK_CARD'" class="task-card">
      <div class="task-header">
        <span class="task-icon">📋</span>
        <h4>{{ payload.title }}</h4>
      </div>
      <p class="task-content">{{ payload.content }}</p>
      <div class="task-actions">
        <component
          v-for="comp in payload.components"
          :key="comp.id"
          :is="getComponentType(comp.type)"
          v-bind="comp"
          @action="handleComponentAction"
        />
      </div>
    </div>
    
    <!-- SURVEY_MINI -->
    <div v-else-if="action.render_type === 'SURVEY_MINI'" class="survey-mini">
      <h4 v-if="payload.title">{{ payload.title }}</h4>
      <form @submit.prevent="handleSurveySubmit">
        <component
          v-for="comp in payload.components"
          :key="comp.id"
          :is="getComponentType(comp.type)"
          v-bind="comp"
          v-model="surveyData[comp.id]"
          @action="handleComponentAction"
        />
      </form>
    </div>
    
    <!-- PROGRESS_TRACKER -->
    <div v-else-if="action.render_type === 'PROGRESS_TRACKER'" class="progress-tracker">
      <div class="progress-header">
        <h4>{{ payload.title }}</h4>
        <span class="progress-value">{{ progressValue }}%</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressValue + '%' }"></div>
      </div>
      <p v-if="payload.content" class="progress-message">{{ payload.content }}</p>
    </div>
    
    <!-- Fallback -->
    <div v-else class="fallback-render">
      <p>{{ payload.content || '未知的渲染类型' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue';

const props = defineProps({
  action: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['callback']);

// 计算属性
const payload = computed(() => props.action.payload || {});
const policyGate = computed(() => props.action.policy_gate || {});

const renderTypeClass = computed(() => {
  return 'render-type-' + (props.action.render_type || 'unknown').toLowerCase().replace(/_/g, '-');
});

const uiStyleClass = computed(() => {
  const style = payload.value.ui_style || policyGate.value.ui_style || 'neutral';
  return 'style-' + style;
});

const notificationClass = computed(() => {
  const title = payload.value.title || '';
  if (title.includes('⚠️') || title.includes('警报')) {
    return 'notification-alert';
  }
  return 'notification-info';
});

const isAlert = computed(() => {
  return notificationClass.value === 'notification-alert';
});

const progressValue = computed(() => {
  return payload.value.extra_data?.progress || 0;
});

// 表单数据
const surveyData = reactive({});

// 组件类型映射
const getComponentType = (type) => {
  const map = {
    'TEXT': 'TextDisplay',
    'BUTTON': 'ActionButton',
    'SLIDER': 'SliderInput',
    'CHECKBOX': 'CheckboxInput',
    'RADIO': 'RadioInput',
    'INPUT': 'TextInput',
    'TEXTAREA': 'TextareaInput',
    'IMAGE': 'ImageDisplay',
    'EMOJI_PICKER': 'EmojiPicker',
    'DATE_PICKER': 'DatePicker',
    'TIME_PICKER': 'TimePicker'
  };
  return map[type] || 'TextDisplay';
};

// 事件处理
const handleComponentAction = (action, data = {}) => {
  emit('callback', {
    action_id: props.action.action_id,
    action_type: action,
    data: data
  });
};

const handleQuickReply = (reply) => {
  emit('callback', {
    action_id: props.action.action_id,
    action_type: reply.action || reply.id,
    data: { reply_id: reply.id, reply_text: reply.text }
  });
};

const handleSurveySubmit = () => {
  emit('callback', {
    action_id: props.action.action_id,
    action_type: 'SUBMIT_SURVEY',
    data: { ...surveyData }
  });
};
</script>
`;


// ============================================
// 基础 UI 组件定义
// ============================================

export const UIComponents = {
  // 按钮组件
  ActionButton: {
    name: 'ActionButton',
    template: `
      <button 
        class="action-btn" 
        :class="btnClass"
        @click="handleClick"
      >
        {{ text }}
      </button>
    `,
    props: {
      id: String,
      text: String,
      action: String,
      style: Object
    },
    emits: ['action'],
    computed: {
      btnClass() {
        const style = this.style || {};
        return {
          'btn-primary': style.type === 'primary',
          'btn-secondary': style.type === 'secondary',
          'btn-outline': style.type === 'outline'
        };
      }
    },
    methods: {
      handleClick() {
        this.$emit('action', this.action, { button_id: this.id });
      }
    }
  },
  
  // 滑块组件
  SliderInput: {
    name: 'SliderInput',
    template: `
      <div class="slider-container">
        <label v-if="label">{{ label }}</label>
        <input 
          type="range" 
          :min="min" 
          :max="max" 
          :step="step"
          :value="modelValue"
          @input="$emit('update:modelValue', Number($event.target.value))"
        />
        <span class="slider-value">{{ modelValue }}</span>
      </div>
    `,
    props: {
      id: String,
      label: String,
      min: { type: Number, default: 0 },
      max: { type: Number, default: 10 },
      step: { type: Number, default: 1 },
      modelValue: { type: Number, default: 5 }
    },
    emits: ['update:modelValue']
  },
  
  // 单选组件
  RadioInput: {
    name: 'RadioInput',
    template: `
      <div class="radio-group">
        <label v-if="label" class="radio-label">{{ label }}</label>
        <div 
          v-for="option in options" 
          :key="option.value"
          class="radio-option"
        >
          <input 
            type="radio" 
            :name="id"
            :value="option.value"
            :checked="modelValue === option.value"
            @change="$emit('update:modelValue', option.value)"
          />
          <span>{{ option.label }}</span>
        </div>
      </div>
    `,
    props: {
      id: String,
      label: String,
      options: Array,
      modelValue: String
    },
    emits: ['update:modelValue']
  },
  
  // 文本显示
  TextDisplay: {
    name: 'TextDisplay',
    template: `<p class="text-display">{{ text }}</p>`,
    props: { text: String }
  }
};


// ============================================
// 样式定义
// ============================================
export const ActionRendererStyles = `
.action-renderer {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  max-width: 400px;
  margin: 0 auto;
}

/* Behavior Card */
.behavior-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  padding: 20px;
  margin: 12px 0;
}

.card-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #333;
}

.card-header .subtitle {
  font-size: 14px;
  color: #666;
}

.card-content p {
  color: #555;
  line-height: 1.6;
}

/* Quick Reply */
.quick-reply {
  padding: 16px;
}

.quick-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-btn {
  padding: 8px 16px;
  border: 1px solid #4A90D9;
  border-radius: 20px;
  background: transparent;
  color: #4A90D9;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: #4A90D9;
  color: #fff;
}

/* Companion Message */
.companion-message {
  padding: 12px;
}

.message-bubble {
  background: #E8F4FD;
  border-radius: 16px 16px 16px 4px;
  padding: 12px 16px;
  max-width: 80%;
}

.style-warm .message-bubble {
  background: #FFF4E5;
}

.style-encouraging .message-bubble {
  background: #E8F5E9;
}

.style-alert .message-bubble {
  background: #FFEBEE;
}

/* Notification */
.notification-card {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  border-radius: 12px;
  margin: 12px 0;
}

.notification-info {
  background: #E3F2FD;
}

.notification-alert {
  background: #FFEBEE;
}

.notification-icon {
  font-size: 24px;
  margin-right: 12px;
}

/* Progress Tracker */
.progress-tracker {
  padding: 16px;
  background: #F5F5F5;
  border-radius: 12px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-bar {
  height: 8px;
  background: #E0E0E0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* Buttons */
.action-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s;
}

.btn-primary {
  background: #4A90D9;
  color: #fff;
}

.btn-primary:hover {
  background: #3A7BC8;
}

.btn-secondary {
  background: #F5F5F5;
  color: #333;
}

/* Slider */
.slider-container {
  margin: 16px 0;
}

.slider-container input[type="range"] {
  width: 100%;
  height: 8px;
  -webkit-appearance: none;
  background: #E0E0E0;
  border-radius: 4px;
}

.slider-container input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  background: #4A90D9;
  border-radius: 50%;
  cursor: pointer;
}
`;


// ============================================
// 导出
// ============================================
export default {
  ComponentFactory,
  ActionRendererTemplate,
  UIComponents,
  ActionRendererStyles
};
