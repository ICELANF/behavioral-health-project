<template>
  <div class="profile-editor">
    <!-- 头像编辑 -->
    <div class="avatar-section" @click="triggerUpload">
      <div class="avatar-wrapper">
        <img class="editor-avatar" :src="avatarUrl" alt="avatar" />
        <div class="camera-overlay">
          <van-icon name="photograph" size="16" color="#fff" />
        </div>
      </div>
      <span class="avatar-hint">点击更换头像</span>
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="hidden-input"
        @change="handleFileChange"
      />
    </div>

    <!-- 昵称编辑 -->
    <div class="name-section">
      <van-field
        v-model="editName"
        label="昵称"
        placeholder="输入昵称"
        maxlength="50"
        clearable
      />
      <van-button
        type="primary"
        size="small"
        :loading="saving"
        @click="saveName"
      >
        保存
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import api from '@/api/index'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const fileInput = ref<HTMLInputElement>()
const editName = ref('')
const saving = ref(false)

const avatarUrl = computed(() => userStore.avatarUrl)
const nameChanged = computed(() =>
  editName.value.trim() !== '' && editName.value.trim() !== userStore.name
)

onMounted(() => {
  editName.value = userStore.name || ''
})

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // validate size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    showToast('图片不能超过5MB')
    return
  }

  const loading = showLoadingToast({ message: '上传中...', forbidClick: true, duration: 0 })

  try {
    const formData = new FormData()
    formData.append('file', file)
    const res: any = await api.post('/api/v1/upload/avatar', formData)
    const url = res.url || res.avatar_url || ''
    if (url) {
      userStore.updateAvatar(url)
      showToast('头像更新成功')
    }
  } catch {
    showToast('上传失败，请重试')
  } finally {
    closeToast()
    // reset input so same file can be re-selected
    input.value = ''
  }
}

async function saveName() {
  const trimmed = editName.value.trim()
  if (!trimmed) {
    showToast('昵称不能为空')
    return
  }
  if (trimmed === userStore.name) {
    showToast('昵称未修改')
    return
  }

  saving.value = true
  try {
    const res: any = await api.put('/api/v1/auth/profile', { full_name: trimmed })
    if (res.success) {
      userStore.updateName(res.full_name || trimmed)
      showToast({ message: '昵称已更新', type: 'success' })
    } else {
      showToast({ message: '保存失败', type: 'fail' })
    }
  } catch {
    showToast({ message: '保存失败，请重试', type: 'fail' })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.profile-editor {
  padding: 0 16px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0 16px;
  cursor: pointer;
}

.avatar-wrapper {
  position: relative;
  width: 72px;
  height: 72px;
}

.editor-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e5e7eb;
}

.camera-overlay {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 24px;
  height: 24px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
}

.avatar-hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 8px;
}

.hidden-input {
  display: none;
}

.name-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.name-section :deep(.van-field) {
  flex: 1;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.name-section :deep(.van-button) {
  flex-shrink: 0;
}
</style>
