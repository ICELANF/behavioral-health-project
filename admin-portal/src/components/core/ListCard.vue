<template>
  <div class="list-card" @click="$emit('click')">
    <div class="list-card-avatar" v-if="$slots.avatar">
      <slot name="avatar" />
    </div>
    <div class="list-card-body">
      <div class="list-card-title">
        <slot name="title">{{ title }}</slot>
      </div>
      <div class="list-card-subtitle" v-if="$slots.subtitle || subtitle">
        <slot name="subtitle">{{ subtitle }}</slot>
      </div>
      <div class="list-card-meta" v-if="$slots.meta">
        <slot name="meta" />
      </div>
    </div>
    <div class="list-card-actions" v-if="$slots.actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  subtitle?: string
}>()

defineEmits<{
  click: []
}>()
</script>

<style scoped>
.list-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.15s;
}

.list-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.list-card:active {
  transform: scale(0.995);
}

.list-card-avatar {
  position: relative;
  flex-shrink: 0;
}

.list-card-body {
  flex: 1;
  min-width: 0;
}

.list-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-card-subtitle {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.list-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
  flex-wrap: wrap;
}

.list-card-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .list-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .list-card-actions {
    width: 100%;
    flex-direction: row;
    gap: 8px;
    margin-top: 8px;
  }

  .list-card-actions :deep(.ant-btn) {
    flex: 1;
  }
}
</style>
