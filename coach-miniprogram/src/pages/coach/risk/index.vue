<template>
<view class="bos-page">
  <view class="bos-navbar">
    <view class="bos-navbar__back" @tap="goBack"><text class="bos-navbar__arrow">‹</text></view>
    <text class="bos-navbar__title">风险管理</text>
    <view class="bos-navbar__placeholder"></view>
  </view>

  <!-- 风险概览 -->
  <view class="risk-overview">
    <view v-for="r in RISK_LEVELS" :key="r.key" class="risk-pill" :class="{'risk-pill--active':riskFilter===r.key}" @tap="riskFilter=r.key;loadRisks()">
      <view class="risk-pill__dot" :style="{background:r.color}"></view>
      <text class="risk-pill__label">{{r.label}}</text>
      <text class="risk-pill__count">{{riskCounts[r.key]||0}}</text>
    </view>
  </view>

  <scroll-view scroll-y class="bos-scroll" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
    <template v-if="loading"><view class="bos-skeleton" v-for="i in 4" :key="i" style="height:140rpx;margin-bottom:16rpx;"></view></template>
    <template v-else-if="filteredList.length">
      <view v-for="item in filteredList" :key="item.id" class="risk-card" @tap="goDetail(item.student_id)">
        <view class="risk-card__indicator" :style="{background:RISK_COLOR[item.risk_level]||'#94a3b8'}">
          <text class="risk-card__level">{{item.risk_level||'?'}}</text>
        </view>
        <view class="risk-card__body">
          <view class="risk-card__row1">
            <text class="risk-card__name">{{item.student_name||'学员'}}</text>
            <view v-if="item.risk_level==='R3'||item.risk_level==='R4'" class="risk-pulse"><view class="risk-pulse__dot"></view></view>
          </view>
          <text class="risk-card__reason">{{item.reason||item.description||'风险待评估'}}</text>
          <view class="risk-card__meta">
            <text class="risk-card__time">{{formatTime(item.detected_at||item.created_at)}}</text>
            <text class="risk-card__source" v-if="item.source">来源: {{item.source}}</text>
          </view>
        </view>
        <view class="risk-card__action" v-if="!item.resolved">
          <view class="bos-btn bos-btn--primary bos-btn--sm" @tap.stop="resolveRisk(item)"><text style="color:#fff;font-size:20rpx;font-weight:700;">处理</text></view>
        </view>
        <view v-else class="risk-card__resolved"><text>✓ 已处理</text></view>
      </view>
    </template>
    <view v-else class="bos-empty"><text class="bos-empty__icon">🛡️</text><text class="bos-empty__text">{{riskFilter==='all'?'暂无风险记录':'该级别无风险记录'}}</text></view>
  </scroll-view>

  <!-- 处理弹窗 -->
  <view class="modal-mask" v-if="resolveTarget" @tap="resolveTarget=null">
    <view class="modal-box" @tap.stop>
      <text class="modal-box__title">处理风险</text>
      <text style="font-size:24rpx;color:#64748b;margin-bottom:12rpx;display:block;">{{resolveTarget.student_name}} · {{resolveTarget.risk_level}}</text>
      <textarea class="modal-textarea" v-model="resolveNote" placeholder="输入处理措施..." :maxlength="300" />
      <view class="modal-actions">
        <view class="bos-btn bos-btn--ghost" style="flex:1;" @tap="resolveTarget=null"><text style="color:#64748b;">取消</text></view>
        <view class="bos-btn bos-btn--primary" style="flex:1;" @tap="confirmResolve"><text style="color:#fff;font-weight:700;">确认处理</text></view>
      </view>
    </view>
  </view>
</view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { http } from '@/utils/request'

const RISK_COLOR:Record<string,string>={R0:'#22c55e',R1:'#84cc16',R2:'#eab308',R3:'#f97316',R4:'#ef4444'}
const RISK_LEVELS=[{key:'all',label:'全部',color:'#64748b'},{key:'R4',label:'危险',color:'#ef4444'},{key:'R3',label:'高风险',color:'#f97316'},{key:'R2',label:'中风险',color:'#eab308'},{key:'R1',label:'低风险',color:'#84cc16'},{key:'R0',label:'安全',color:'#22c55e'}]

const loading=ref(false),refreshing=ref(false),riskFilter=ref('all'),riskList=ref<any[]>([]),riskCounts=ref<Record<string,number>>({}),resolveTarget=ref<any>(null),resolveNote=ref('')

const filteredList=computed(()=>riskFilter.value==='all'?riskList.value:riskList.value.filter(i=>i.risk_level===riskFilter.value))

onMounted(()=>loadRisks())

async function loadRisks(){
  loading.value=true
  try{
    const res=await http.get<any>('/v1/coach/students')
    const students=res.items||res.students||(Array.isArray(res)?res:[])
    const items=students.filter((s:any)=>s.risk_level&&s.risk_level!=='R0').map((s:any)=>({id:s.id,student_id:s.id,student_name:s.name||s.full_name||s.username||'学员',risk_level:s.risk_level||'R1',reason:s.risk_reason||s.latest_risk_note||'风险待评估',detected_at:s.risk_updated_at||s.updated_at||s.created_at,source:s.risk_source||'',resolved:false}))
    riskList.value=items
    const counts:Record<string,number>={all:items.length}
    items.forEach((i:any)=>{counts[i.risk_level]=(counts[i.risk_level]||0)+1})
    riskCounts.value=counts
  }catch{riskList.value=[]}finally{loading.value=false}
}
async function onRefresh(){refreshing.value=true;await loadRisks();refreshing.value=false}
function resolveRisk(item:any){resolveTarget.value=item;resolveNote.value=''}
async function confirmResolve(){
  if(!resolveNote.value.trim()){uni.showToast({title:'请输入处理措施',icon:'none'});return}
  resolveTarget.value.resolved=true;resolveTarget.value=null;uni.showToast({title:'已处理',icon:'success'})
}
function goDetail(sid:number){if(sid)uni.navigateTo({url:`/pages/coach/students/detail?id=${sid}`})}
function formatTime(dt:string):string{if(!dt)return'';return dt.slice(0,16).replace('T',' ')}
function goBack(){uni.navigateBack({fail:()=>uni.switchTab({url:'/pages/home/index'})})}
</script>

<style scoped>
.bos-page{min-height:100vh;background:linear-gradient(180deg,#f0fdf4 0%,#f8fafc 30%,#f0f9ff 100%);display:flex;flex-direction:column;}
.bos-navbar{display:flex;align-items:center;justify-content:space-between;padding:16rpx 32rpx;padding-top:calc(88rpx + env(safe-area-inset-top));background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1rpx solid rgba(226,232,240,0.4);position:sticky;top:0;z-index:100;}
.bos-navbar__back{width:64rpx;height:64rpx;display:flex;align-items:center;justify-content:center;background:#e2e8f0;border-radius:16rpx;}.bos-navbar__arrow{font-size:48rpx;color:#0f172a;font-weight:800;line-height:1;}.bos-navbar__title{font-size:30rpx;font-weight:700;color:#1e293b;}.bos-navbar__placeholder{width:64rpx;}

.risk-overview{display:flex;flex-wrap:wrap;gap:8rpx;padding:16rpx 32rpx;background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);}
.risk-pill{display:flex;align-items:center;gap:8rpx;padding:10rpx 20rpx;border-radius:999rpx;background:#f1f5f9;border:2rpx solid transparent;}
.risk-pill--active{background:#fff;border-color:#e2e8f0;box-shadow:0 4rpx 12rpx rgba(0,0,0,0.06);}
.risk-pill__dot{width:16rpx;height:16rpx;border-radius:50%;}.risk-pill__label{font-size:22rpx;color:#475569;font-weight:600;}.risk-pill__count{font-size:20rpx;color:#94a3b8;font-weight:700;}

.bos-scroll{flex:1;padding:20rpx 32rpx 120rpx;}

.risk-card{display:flex;align-items:stretch;gap:16rpx;background:rgba(255,255,255,0.85);backdrop-filter:blur(8px);border-radius:24rpx;padding:20rpx;margin-bottom:16rpx;border:2rpx solid rgba(226,232,240,0.5);box-shadow:0 4rpx 16rpx rgba(0,0,0,0.04);}
.risk-card__indicator{width:64rpx;display:flex;align-items:center;justify-content:center;border-radius:16rpx;flex-shrink:0;}
.risk-card__level{font-size:24rpx;font-weight:800;color:#fff;}
.risk-card__body{flex:1;min-width:0;}
.risk-card__row1{display:flex;align-items:center;gap:10rpx;margin-bottom:6rpx;}
.risk-card__name{font-size:28rpx;font-weight:700;color:#1e293b;}
.risk-card__reason{font-size:24rpx;color:#64748b;line-height:1.5;display:block;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;}
.risk-card__meta{display:flex;gap:16rpx;margin-top:8rpx;}.risk-card__time{font-size:20rpx;color:#94a3b8;}.risk-card__source{font-size:20rpx;color:#94a3b8;}
.risk-card__action{display:flex;align-items:center;flex-shrink:0;}
.risk-card__resolved{font-size:22rpx;color:#16a34a;font-weight:700;display:flex;align-items:center;flex-shrink:0;}

.risk-pulse{position:relative;width:20rpx;height:20rpx;}
.risk-pulse__dot{width:12rpx;height:12rpx;background:#ef4444;border-radius:50%;position:absolute;top:4rpx;left:4rpx;animation:bos-breathe 1.5s ease-in-out infinite;}
@keyframes bos-breathe{0%,100%{transform:scale(1);opacity:1;}50%{transform:scale(1.6);opacity:0.5;}}

.bos-btn{display:inline-flex;align-items:center;justify-content:center;padding:16rpx 24rpx;border-radius:24rpx;}.bos-btn--sm{padding:10rpx 20rpx;}.bos-btn--primary{background:linear-gradient(135deg,#22c55e,#16a34a);}.bos-btn--ghost{background:#f1f5f9;}

.modal-mask{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:999;}
.modal-box{width:88%;background:#fff;border-radius:32rpx;padding:32rpx;}.modal-box__title{display:block;font-size:30rpx;font-weight:700;color:#1e293b;margin-bottom:16rpx;}
.modal-textarea{width:100%;min-height:160rpx;padding:16rpx 20rpx;background:#f8fafc;border-radius:16rpx;border:2rpx solid #e2e8f0;font-size:26rpx;color:#1e293b;box-sizing:border-box;margin-top:8rpx;}
.modal-actions{display:flex;gap:16rpx;margin-top:24rpx;}

.bos-empty{display:flex;flex-direction:column;align-items:center;padding:160rpx 0;gap:20rpx;}.bos-empty__icon{font-size:96rpx;opacity:0.6;}.bos-empty__text{font-size:26rpx;color:#94a3b8;}
.bos-skeleton{background:linear-gradient(90deg,#f1f5f9 25%,#f8fafc 50%,#f1f5f9 75%);background-size:200% 100%;animation:bos-shimmer 1.5s ease-in-out infinite;border-radius:24rpx;}
@keyframes bos-shimmer{0%{background-position:200% 0;}100%{background-position:-200% 0;}}
</style>
