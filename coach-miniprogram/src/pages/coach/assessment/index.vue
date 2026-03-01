<template>
<view class="bos-page">
  <view class="bos-navbar">
    <view class="bos-navbar__back" @tap="goBack"><text class="bos-navbar__arrow">‹</text></view>
    <text class="bos-navbar__title">评估管理</text>
    <view class="nav-action" @tap="showAssignModal=true"><text>+ 分配</text></view>
  </view>

  <!-- 状态筛选 -->
  <view class="tab-wrap"><view class="bos-tabs">
    <view v-for="t in STATUS_TABS" :key="t.key" class="bos-tab" :class="{'bos-tab--active':statusFilter===t.key}" @tap="statusFilter=t.key"><text>{{t.label}}</text></view>
  </view></view>

  <scroll-view scroll-y class="bos-scroll" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
    <template v-if="loading"><view class="bos-skeleton" v-for="i in 4" :key="i" style="height:130rpx;margin-bottom:16rpx;"></view></template>
    <template v-else-if="filteredList.length">
      <view v-for="a in filteredList" :key="a.id" class="assess-card" @tap="goReview(a)">
        <view class="assess-card__left">
          <view class="bos-avatar bos-avatar--green" style="width:64rpx;height:64rpx;border-radius:18rpx;font-size:24rpx;"><text>{{(a.student_name||'?')[0]}}</text></view>
        </view>
        <view class="assess-card__body">
          <text class="assess-card__name">{{a.student_name||a.student?.full_name||'学员'}}</text>
          <text class="assess-card__type">{{a.assessment_name||a.title||'综合评估'}}</text>
          <text class="assess-card__time">{{formatTime(a.created_at)}}</text>
        </view>
        <view class="status-badge" :class="`status-badge--${a.status}`"><text>{{STATUS_LABEL[a.status]||a.status}}</text></view>
      </view>
    </template>
    <view v-else class="bos-empty"><text class="bos-empty__icon">📝</text><text class="bos-empty__text">暂无评估记录</text></view>
  </scroll-view>

  <!-- 分配弹窗 -->
  <view class="modal-mask" v-if="showAssignModal" @tap="showAssignModal=false">
    <view class="modal-box" @tap.stop>
      <text class="modal-box__title">分配新评估</text>
      <picker :range="studentNames" @change="onPickStudent">
        <view class="picker-trigger"><text>{{pickedStudent?pickedStudent.name:'选择学员'}}</text><text style="color:#94a3b8;">▼</text></view>
      </picker>
      <picker :range="scaleNames" @change="onPickScale" style="margin-top:12rpx;">
        <view class="picker-trigger"><text>{{pickedScale||'选择量表'}}</text><text style="color:#94a3b8;">▼</text></view>
      </picker>
      <view class="modal-actions">
        <view class="bos-btn bos-btn--ghost" style="flex:1;" @tap="showAssignModal=false"><text style="color:#64748b;">取消</text></view>
        <view class="bos-btn bos-btn--primary" style="flex:1;" @tap="doAssign"><text style="color:#fff;font-weight:700;">确认分配</text></view>
      </view>
    </view>
  </view>
</view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { http } from '@/utils/request'

const STATUS_TABS=[{key:'all',label:'全部'},{key:'pending_review',label:'待审核'},{key:'assigned',label:'待完成'},{key:'reviewed',label:'已审核'}]
const STATUS_LABEL:Record<string,string>={assigned:'待完成',submitted:'已提交',pending_review:'待审核',reviewed:'已审核'}
const SCALES=['综合评估','PHQ-9','GAD-7','BPT-6','大五人格','TTM阶段评估']

const loading=ref(false),refreshing=ref(false),statusFilter=ref('all'),list=ref<any[]>([])
const showAssignModal=ref(false),studentList=ref<any[]>([]),pickedStudent=ref<any>(null),pickedScale=ref('')

const studentNames=computed(()=>studentList.value.map(s=>s.name))
const scaleNames=SCALES
const filteredList=computed(()=>statusFilter.value==='all'?list.value:list.value.filter(i=>i.status===statusFilter.value))

onMounted(()=>{loadList();loadStudents()})

async function loadList(){loading.value=true;try{const res=await http.get<any>('/v1/assessment-assignments/review-list');list.value=res.items||res.assignments||(Array.isArray(res)?res:[])}catch{list.value=[]}finally{loading.value=false}}
async function loadStudents(){try{const res=await http.get<any>('/v1/coach/students');studentList.value=(res.items||res.students||[]).map((s:any)=>({...s,name:s.name||s.full_name||s.username}))}catch{}}
async function onRefresh(){refreshing.value=true;await loadList();refreshing.value=false}
function onPickStudent(e:any){pickedStudent.value=studentList.value[Number(e.detail.value)]||null}
function onPickScale(e:any){pickedScale.value=SCALES[Number(e.detail.value)]||''}
async function doAssign(){if(!pickedStudent.value){uni.showToast({title:'请选择学员',icon:'none'});return};try{await http.post('/v1/assessment-assignments/assign',{student_id:pickedStudent.value.id,assessment_name:pickedScale.value||'综合评估'});showAssignModal.value=false;uni.showToast({title:'已分配',icon:'success'});loadList()}catch{uni.showToast({title:'分配失败',icon:'none'})}}
function goReview(a:any){if(a.status==='pending_review')uni.navigateTo({url:`/pages/coach/assessment/review?id=${a.id}`})}
function formatTime(dt:string):string{if(!dt)return'';return dt.slice(0,10)}
function goBack(){uni.navigateBack({fail:()=>uni.switchTab({url:'/pages/home/index'})})}
</script>

<style scoped>
.bos-page{min-height:100vh;background:linear-gradient(180deg,#f0fdf4 0%,#f8fafc 30%,#f0f9ff 100%);display:flex;flex-direction:column;}
.bos-navbar{display:flex;align-items:center;justify-content:space-between;padding:16rpx 32rpx;padding-top:calc(88rpx + env(safe-area-inset-top));background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1rpx solid rgba(226,232,240,0.4);position:sticky;top:0;z-index:100;}
.bos-navbar__back{width:64rpx;height:64rpx;display:flex;align-items:center;justify-content:center;background:#e2e8f0;border-radius:16rpx;}.bos-navbar__arrow{font-size:48rpx;color:#0f172a;font-weight:800;line-height:1;}.bos-navbar__title{font-size:30rpx;font-weight:700;color:#1e293b;}
.nav-action{padding:10rpx 24rpx;background:linear-gradient(135deg,#22c55e,#16a34a);border-radius:999rpx;font-size:24rpx;color:#fff;font-weight:700;}

.tab-wrap{padding:16rpx 32rpx 0;background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);}
.bos-tabs{display:flex;gap:4rpx;background:#f1f5f9;padding:6rpx;border-radius:20rpx;}
.bos-tab{flex:1;padding:14rpx 8rpx;border-radius:16rpx;font-size:22rpx;font-weight:600;color:#64748b;text-align:center;}.bos-tab--active{background:#fff;color:#16a34a;box-shadow:0 4rpx 12rpx rgba(0,0,0,0.06);}
.bos-scroll{flex:1;padding:20rpx 32rpx 120rpx;}

.assess-card{display:flex;align-items:center;gap:16rpx;background:rgba(255,255,255,0.85);backdrop-filter:blur(8px);border-radius:24rpx;padding:20rpx;margin-bottom:12rpx;border:2rpx solid rgba(226,232,240,0.5);box-shadow:0 4rpx 16rpx rgba(0,0,0,0.04);}
.bos-avatar{display:flex;align-items:center;justify-content:center;font-weight:700;color:#fff;flex-shrink:0;}.bos-avatar--green{background:linear-gradient(135deg,#22c55e,#16a34a);}
.assess-card__body{flex:1;min-width:0;}
.assess-card__name{display:block;font-size:28rpx;font-weight:700;color:#1e293b;}
.assess-card__type{display:block;font-size:22rpx;color:#64748b;margin-top:4rpx;}
.assess-card__time{display:block;font-size:20rpx;color:#94a3b8;margin-top:2rpx;}
.status-badge{font-size:20rpx;font-weight:700;padding:6rpx 16rpx;border-radius:999rpx;flex-shrink:0;}
.status-badge--assigned,.status-badge--pending{background:#fef3c7;color:#92400e;}.status-badge--submitted,.status-badge--pending_review{background:#dbeafe;color:#1e40af;}.status-badge--reviewed{background:#dcfce7;color:#15803d;}

.modal-mask{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:999;}
.modal-box{width:88%;background:#fff;border-radius:32rpx;padding:32rpx;}.modal-box__title{display:block;font-size:30rpx;font-weight:700;color:#1e293b;margin-bottom:20rpx;}
.picker-trigger{display:flex;justify-content:space-between;align-items:center;padding:20rpx 24rpx;background:#f8fafc;border-radius:16rpx;border:2rpx solid #e2e8f0;font-size:28rpx;color:#1e293b;}
.modal-actions{display:flex;gap:16rpx;margin-top:24rpx;}
.bos-btn{display:inline-flex;align-items:center;justify-content:center;padding:16rpx 24rpx;border-radius:24rpx;}.bos-btn--primary{background:linear-gradient(135deg,#22c55e,#16a34a);}.bos-btn--ghost{background:#f1f5f9;}

.bos-empty{display:flex;flex-direction:column;align-items:center;padding:160rpx 0;gap:20rpx;}.bos-empty__icon{font-size:96rpx;opacity:0.6;}.bos-empty__text{font-size:26rpx;color:#94a3b8;}
.bos-skeleton{background:linear-gradient(90deg,#f1f5f9 25%,#f8fafc 50%,#f1f5f9 75%);background-size:200% 100%;animation:bos-shimmer 1.5s ease-in-out infinite;border-radius:24rpx;}
@keyframes bos-shimmer{0%{background-position:200% 0;}100%{background-position:-200% 0;}}
</style>
