<template>
  <div class="feed-page">
    <div class="header-mini">医道汇</div>
    <div class="content">
      <button class="btn-main fu" style="width:100%" @click="showCompose = true">+ 发布帖子</button>

      <div v-for="p in posts" :key="p.id" class="card fu fu-1">
        <div style="font-size:14px;font-weight:700;margin-bottom:4px">{{ p.title }}</div>
        <div style="display:flex;gap:4px;margin-bottom:6px">
          <span class="chip chip--teal">{{ p.post_type }}</span>
          <span v-for="t in (p.tags || []).slice(0,2)" :key="t" class="chip chip--gold">{{ t }}</span>
        </div>
        <div style="font-size:11px;color:var(--sub)">
          浏览 {{ p.view_count }} &middot; 点赞 {{ p.like_count }}
        </div>
      </div>

      <div v-if="posts.length === 0" class="card fu fu-1" style="text-align:center;padding:32px">
        <div style="font-size:14px;font-weight:700">暂无帖子</div>
        <div style="font-size:13px;color:var(--sub)">与同道分享知识，交流临床经验。</div>
      </div>

      <div v-if="showCompose" class="modal-mask" @click.self="showCompose = false">
        <div class="modal-body">
          <div style="font-size:16px;font-weight:800;margin-bottom:16px">发布帖子</div>
          <van-field v-model="newTitle" label="标题" placeholder="帖子标题" />
          <textarea class="text-input" rows="4" v-model="newContent" placeholder="分享您的见解..." style="margin-top:8px" />
          <div style="display:flex;gap:8px;margin-top:16px">
            <button class="btn-outline" style="flex:1" @click="showCompose = false">取消</button>
            <button class="btn-main" style="flex:1" @click="publishPost">发布</button>
          </div>
        </div>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listMedCircle, createMedCirclePost } from '@/api/xzb'

const showCompose = ref(false)
const newTitle = ref('')
const newContent = ref('')

interface Post {
  id: string; title: string; post_type: string; tags: string[]
  view_count: number; like_count: number
}

const posts = ref<Post[]>([])

async function loadData() {
  try {
    const res = await listMedCircle()
    posts.value = res.data.items || []
  } catch { posts.value = [] }
}

async function publishPost() {
  try {
    await createMedCirclePost({ title: newTitle.value, content: newContent.value })
    showCompose.value = false
    newTitle.value = ''
    newContent.value = ''
    loadData()
  } catch { /* ignore */ }
}

onMounted(loadData)
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.text-input {
  width: 100%; border: 1.5px solid var(--border); border-radius: 12px;
  padding: 12px; font-size: 13px; resize: none; outline: none;
  color: var(--ink); line-height: 1.6;
}
.modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: flex-end; z-index: 200;
}
.modal-body {
  background: white; width: 100%; max-width: 480px; margin: 0 auto;
  border-radius: 20px 20px 0 0; padding: 24px 20px env(safe-area-inset-bottom, 20px);
}
</style>
