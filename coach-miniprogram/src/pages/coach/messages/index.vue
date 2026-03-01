<template>
<view class="bos-page">
  <view class="bos-navbar">
    <view class="bos-navbar__back" @tap="goBack"><text class="bos-navbar__arrow">‹</text></view>
    <text class="bos-navbar__title">教练消息</text>
    <view class="bos-navbar__placeholder"></view>
  </view>

  <!-- 搜索 -->
  <view class="search-wrap">
    <view class="search-box">
      <text class="search-box__icon">🔍</text>
      <input class="search-box__input" v-model="keyword" placeholder="搜索学员..." confirm-type="search" @confirm="filterConvos" />
    </view>
  </view>

  <!-- 消息分类 Tab -->
  <view class="tab-wrap"><view class="bos-tabs">
    <view v-for="t in MSG_TABS" :key="t.key" class="bos-tab" :class="{'bos-tab--active':activeTab===t.key}" @tap="activeTab=t.key">
      <text>{{t.label}}</text>
      <view class="bos-tab__dot" v-if="t.key==='unread'&&unreadCount>0"></view>
    </view>
  </view></view>

  <scroll-view scroll-y class="bos-scroll" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
    <template v-if="loading"><view class="bos-skeleton" v-for="i in 5" :key="i" style="height:100rpx;margin-bottom:12rpx;"></view></template>
    <template v-else-if="displayList.length">
      <view v-for="convo in displayList" :key="convo.id" class="convo-item" :class="{'convo-item--unread':convo.unread>0}" @tap="goChat(convo)">
        <view class="convo-avatar" :class="avatarClass(convo.risk_level)">
          <text>{{(convo.student_name||'?')[0]}}</text>
          <view class="convo-avatar__dot" v-if="convo.unread>0"></view>
        </view>
        <view class="convo-item__body">
          <view class="convo-item__row1">
            <text class="convo-item__name">{{convo.student_name}}</text>
            <text class="convo-item__time">{{formatTime(convo.last_message_at)}}</text>
          </view>
          <view class="convo-item__row2">
            <text class="convo-item__preview">{{convo.last_message||'暂无消息'}}</text>
            <view class="convo-item__badge" v-if="convo.unread>0"><text>{{convo.unread>99?'99+':convo.unread}}</text></view>
          </view>
        </view>
      </view>
    </template>
    <view v-else class="bos-empty"><text class="bos-empty__icon">💬</text><text class="bos-empty__text">暂无消息记录</text></view>
  </scroll-view>
</view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { http } from '@/utils/request'

const MSG_TABS=[{key:'all',label:'全部'},{key:'unread',label:'未读'},{key:'starred',label:'重要'}]

const loading=ref(false),refreshing=ref(false),keyword=ref(''),activeTab=ref('all'),conversations=ref<any[]>([])

const unreadCount=computed(()=>conversations.value.reduce((a,c)=>a+(c.unread||0),0))
const displayList=computed(()=>{
  let list=conversations.value
  if(keyword.value){const kw=keyword.value.toLowerCase();list=list.filter(c=>(c.student_name||'').toLowerCase().includes(kw))}
  if(activeTab.value==='unread')list=list.filter(c=>c.unread>0)
  if(activeTab.value==='starred')list=list.filter(c=>c.starred)
  return list
})

function avatarClass(risk:string){const m:Record<string,string>={high:'convo-avatar--red',medium:'convo-avatar--amber',low:'convo-avatar--green'};return m[risk]||'convo-avatar--green'}

onMounted(()=>loadConversations())

async function loadConversations(){
  loading.value=true
  try{
    const res=await http.get<any>('/v1/coach/students-with-messages')
    conversations.value=res.items||res.conversations||(Array.isArray(res)?res:[])
  }catch{conversations.value=[]}finally{loading.value=false}
}
async function onRefresh(){refreshing.value=true;await loadConversations();refreshing.value=false}
function filterConvos(){}
function goChat(convo:any){uni.navigateTo({url:`/pages/coach/students/detail?id=${convo.student_id}&tab=message`})}
function formatTime(dt:string):string{if(!dt)return'';const d=new Date(dt);const now=new Date();const diff=now.getTime()-d.getTime();if(diff<86400000)return dt.slice(11,16);if(diff<604800000)return['周日','周一','周二','周三','周四','周五','周六'][d.getDay()];return dt.slice(5,10)}
function goBack(){uni.navigateBack({fail:()=>uni.switchTab({url:'/pages/home/index'})})}
</script>

<style scoped>
.bos-page{min-height:100vh;background:linear-gradient(180deg,#f0fdf4 0%,#f8fafc 30%,#f0f9ff 100%);display:flex;flex-direction:column;}
.bos-navbar{display:flex;align-items:center;justify-content:space-between;padding:16rpx 32rpx;padding-top:calc(88rpx + env(safe-area-inset-top));background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1rpx solid rgba(226,232,240,0.4);position:sticky;top:0;z-index:100;}
.bos-navbar__back{width:64rpx;height:64rpx;display:flex;align-items:center;justify-content:center;background:#e2e8f0;border-radius:16rpx;}.bos-navbar__arrow{font-size:48rpx;color:#0f172a;font-weight:800;line-height:1;}.bos-navbar__title{font-size:30rpx;font-weight:700;color:#1e293b;}.bos-navbar__placeholder{width:64rpx;}

.search-wrap{padding:12rpx 32rpx;background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);}
.search-box{display:flex;align-items:center;gap:12rpx;background:#f1f5f9;border-radius:20rpx;padding:0 20rpx;height:68rpx;}
.search-box__icon{font-size:26rpx;flex-shrink:0;}.search-box__input{flex:1;font-size:26rpx;background:transparent;}

.tab-wrap{padding:0 32rpx;padding-top:8rpx;background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);}
.bos-tabs{display:flex;gap:4rpx;background:#f1f5f9;padding:6rpx;border-radius:20rpx;}
.bos-tab{flex:1;padding:14rpx 8rpx;border-radius:16rpx;font-size:22rpx;font-weight:600;color:#64748b;text-align:center;position:relative;}.bos-tab--active{background:#fff;color:#16a34a;box-shadow:0 4rpx 12rpx rgba(0,0,0,0.06);}
.bos-tab__dot{position:absolute;top:6rpx;right:calc(50% - 40rpx);width:12rpx;height:12rpx;background:#ef4444;border-radius:50%;animation:bos-breathe 1.5s ease-in-out infinite;}
@keyframes bos-breathe{0%,100%{transform:scale(1);opacity:1;}50%{transform:scale(1.4);opacity:0.5;}}
.bos-scroll{flex:1;padding:16rpx 32rpx 120rpx;}

.convo-item{display:flex;align-items:center;gap:20rpx;padding:20rpx;background:rgba(255,255,255,0.75);border-radius:24rpx;margin-bottom:12rpx;border:2rpx solid rgba(226,232,240,0.3);}
.convo-item--unread{background:rgba(240,253,244,0.8);border-color:rgba(187,247,208,0.5);}
.convo-avatar{width:80rpx;height:80rpx;border-radius:24rpx;display:flex;align-items:center;justify-content:center;font-size:32rpx;font-weight:700;color:#fff;flex-shrink:0;position:relative;}
.convo-avatar--green{background:linear-gradient(135deg,#22c55e,#16a34a);}.convo-avatar--amber{background:linear-gradient(135deg,#f59e0b,#d97706);}.convo-avatar--red{background:linear-gradient(135deg,#ef4444,#dc2626);}
.convo-avatar__dot{position:absolute;top:-4rpx;right:-4rpx;width:20rpx;height:20rpx;background:#ef4444;border-radius:50%;border:3rpx solid #fff;animation:bos-breathe 1.5s ease-in-out infinite;}
.convo-item__body{flex:1;min-width:0;}
.convo-item__row1{display:flex;justify-content:space-between;align-items:center;margin-bottom:6rpx;}
.convo-item__name{font-size:28rpx;font-weight:700;color:#1e293b;}.convo-item__time{font-size:20rpx;color:#94a3b8;}
.convo-item__row2{display:flex;justify-content:space-between;align-items:center;}
.convo-item__preview{font-size:24rpx;color:#64748b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;}
.convo-item__badge{min-width:32rpx;height:32rpx;border-radius:999rpx;background:#ef4444;color:#fff;font-size:18rpx;font-weight:700;display:flex;align-items:center;justify-content:center;padding:0 8rpx;flex-shrink:0;margin-left:12rpx;}

.bos-empty{display:flex;flex-direction:column;align-items:center;padding:160rpx 0;gap:20rpx;}.bos-empty__icon{font-size:96rpx;opacity:0.6;}.bos-empty__text{font-size:26rpx;color:#94a3b8;}
.bos-skeleton{background:linear-gradient(90deg,#f1f5f9 25%,#f8fafc 50%,#f1f5f9 75%);background-size:200% 100%;animation:bos-shimmer 1.5s ease-in-out infinite;border-radius:24rpx;}
@keyframes bos-shimmer{0%{background-position:200% 0;}100%{background-position:-200% 0;}}
</style>
