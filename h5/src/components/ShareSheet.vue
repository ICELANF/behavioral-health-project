<!--
  分享面板组件 — 复制链接 / 二维码占位
-->
<template>
  <van-action-sheet
    :show="visible"
    :title="title || '分享'"
    @update:show="(val: boolean) => $emit('update:visible', val)"
  >
    <div class="share-content">
      <div class="share-options">
        <div class="share-option" @click="copyLink">
          <div class="share-icon copy-icon">
            <van-icon name="link-o" size="28" color="#1989fa" />
          </div>
          <span class="share-label">复制链接</span>
        </div>
        <div class="share-option" @click="showQrCode">
          <div class="share-icon qr-icon">
            <van-icon name="qr" size="28" color="#07c160" />
          </div>
          <span class="share-label">二维码</span>
        </div>
      </div>

      <!-- 二维码占位区域 -->
      <div v-if="qrVisible" class="qr-section">
        <div class="qr-placeholder">
          <van-icon name="qr" size="120" color="#c8c9cc" />
          <p class="qr-hint">二维码生成中...</p>
          <p class="qr-url">{{ url }}</p>
        </div>
      </div>

      <div class="share-cancel">
        <van-button block plain @click="$emit('update:visible', false)">取消</van-button>
      </div>
    </div>
  </van-action-sheet>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'

const props = defineProps<{
  visible: boolean
  title?: string
  url: string
}>()

defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const qrVisible = ref(false)

async function copyLink() {
  try {
    await navigator.clipboard.writeText(props.url)
    showToast({ message: '链接已复制', type: 'success' })
  } catch {
    // 降级方案
    const input = document.createElement('input')
    input.value = props.url
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    showToast({ message: '链接已复制', type: 'success' })
  }
}

function showQrCode() {
  qrVisible.value = !qrVisible.value
}
</script>

<style scoped>
.share-content {
  padding: 16px;
}

.share-options {
  display: flex;
  justify-content: center;
  gap: 40px;
  padding: 20px 0;
}

.share-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.share-option:active {
  opacity: 0.7;
}

.share-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copy-icon {
  background: rgba(25, 137, 250, 0.1);
}

.qr-icon {
  background: rgba(7, 193, 96, 0.1);
}

.share-label {
  font-size: 12px;
  color: #323233;
}

.qr-section {
  padding: 20px 0;
}

.qr-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  background: #f7f8fa;
  border-radius: 12px;
}

.qr-hint {
  font-size: 14px;
  color: #969799;
  margin-top: 12px;
}

.qr-url {
  font-size: 12px;
  color: #c8c9cc;
  margin-top: 8px;
  word-break: break-all;
  text-align: center;
}

.share-cancel {
  margin-top: 12px;
}
</style>
