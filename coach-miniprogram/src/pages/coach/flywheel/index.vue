<template>
<view class="bos-page">
  <view class="bos-navbar">
    <view class="bos-navbar__back" @tap="goBack"><text class="bos-navbar__arrow">‹</text></view>
    <text class="bos-navbar__title">AI 飞轮</text>
    <view class="nav-refresh" @tap="refreshAll"><text>↻</text></view>
  </view>

  <!-- 飞轮可视化 -->
  <view class="wheel-wrap">
    <view class="wheel-center"><text style="font-size:40rpx;">🤖</text><text class="wheel-center__label">AI飞轮</text></view>
    <view class="wheel-steps">
      <view v-for="(s,i) in WHEEL_STEPS" :key="i" class="wheel-step" :class="{'wheel-step--active':s.active}">
        <text class="wheel-step__icon">{{s.icon}}</text>
        <text class="wheel-step__text">{{s.label}}</text>
        <view class="wheel-step__badge" v-if="s.count>0"><text>{{s.count}}</text></view>
      </view>
    </view>
  </view>

  <!-- 统计栏 -->
  <view class="bos-card" style="margin:24rpx 32rpx 0;padding:24rpx;">
    <view class="bos-stats">
      <view class="bos-stat"><text class="bos-stat__val" style="-webkit-text-fill-color:#f59e0b;">{{stats.pending}}</text><text class="bos-stat__label">待审核</text></view>
      <view class="bos-stat"><text class="bos-stat__val">{{stats.approved}}</text><text class="bos-stat__label">已通过</text></view>
      <view class="bos-stat"><text class="bos-stat__val" style="-webkit-text-fill-color:#ef4444;">{{stats.rejected}}</text><text class="bos-stat__label">已退回</text></view>
      <view class="bos-stat"><text class="bos-stat__val" style="-webkit-text-fill-color:#3b82f6;">{{stats.ai_runs}}</text><text class="bos-stat__label">AI运行</text></view>
    </view>
  </view>

  <!-- Tab -->
  <view class="tab-wrap">
    <view class="bos-tabs">
      <view v-for="tab in TABS" :key="tab.key" class="bos-tab" :class="{'bos-tab--active':activeTab===tab.key}" @tap="activeTab=tab.key">
        <text>{{tab.label}}</text>
        <view class="bos-tab__badge" v-if="getTabCount(tab.key)>0"><text>{{getTabCount(tab.key)}}</text></view>
      </view>
    </view>
  </view>

  <scroll-view scroll-y class="bos-scroll" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">

    <!-- 待审核 Tab -->
    <template v-if="activeTab==='pending'">
      <view class="batch-bar" v-if="pendingItems.length>1">
        <text class="batch-bar__count">{{pendingItems.length}} 条待审核</text>
        <view class="bos-btn bos-btn--primary bos-btn--pill" @tap="batchApprove"><text style="color:#fff;font-size:22rpx;font-weight:700;">全部通过</text></view>
      </view>
      <template v-if="loading"><view class="bos-skeleton" v-for="i in 3" :key="i" style="height:200rpx;margin-bottom:16rpx;"></view></template>
      <template v-else-if="pendingItems.length">
        <view v-for="item in pendingItems" :key="item.id" class="q-card">
          <view class="q-card__head">
            <text class="q-card__name">{{item.student_name||'学员'}}</text>
            <view class="q-card__type" :class="`q-card__type--${item.type||'push'}`"><text>{{TYPE_LABEL[item.type]||'推送'}}</text></view>
            <view class="q-card__urgent" v-if="item.priority==='urgent'"><text>🔴 紧急</text></view>
          </view>
          <text class="q-card__summary" v-if="item.ai_summary">{{item.ai_summary}}</text>
          <view class="q-card__content" v-if="item.content_title||item.ai_draft" @tap="item._expanded=!item._expanded">
            <text class="q-card__content-title" v-if="item.content_title">{{item.content_title}}</text>
            <text :class="item._expanded?'':'q-card__clamp'">{{item.content_body||item.ai_draft||''}}</text>
            <text class="q-card__toggle">{{item._expanded?'收起 ▲':'展开 ▼'}}</text>
          </view>
          <view class="q-card__actions">
            <view class="bos-btn bos-btn--primary" style="flex:1;" @tap="handleApprove(item)"><text style="color:#fff;font-size:24rpx;font-weight:700;">✓ 通过</text></view>
            <view class="bos-btn bos-btn--outline" style="flex:1;" @tap="openEditModal(item)"><text style="color:#3b82f6;font-size:24rpx;font-weight:700;">✎ 编辑</text></view>
            <view class="bos-btn bos-btn--danger-outline" style="flex:1;" @tap="openRejectModal(item)"><text style="color:#ef4444;font-size:24rpx;font-weight:700;">✗ 退回</text></view>
          </view>
        </view>
      </template>
      <view v-else class="bos-empty"><text class="bos-empty__icon">✓</text><text class="bos-empty__text">审核已全部完成</text></view>
    </template>

    <!-- 已处理 Tab -->
    <template v-if="activeTab==='handled'">
      <view v-for="item in handledItems" :key="item.id" class="q-card q-card--done">
        <view class="q-card__done-badge" :class="item._action==='approved'?'q-card__done-badge--green':'q-card__done-badge--red'">
          <text>{{item._action==='approved'?'已通过 ✓':'已退回 ✗'}}</text>
        </view>
        <view class="q-card__head"><text class="q-card__name">{{item.student_name||'学员'}}</text></view>
        <text class="q-card__summary" v-if="item.ai_summary">{{item.ai_summary}}</text>
      </view>
      <view v-if="!handledItems.length" class="bos-empty"><text class="bos-empty__icon">📋</text><text class="bos-empty__text">暂无已处理记录</text></view>
    </template>

    <!-- AI历史 Tab -->
    <template v-if="activeTab==='ai_history'">
      <view v-for="(run,i) in aiHistory" :key="i" class="ai-card">
        <view class="ai-card__head"><text class="ai-card__name">{{run.student_name}}</text><text class="ai-card__time">{{formatDate(run.created_at)}}</text></view>
        <view class="ai-card__conf" v-if="run.confidence!=null">
          <text class="ai-card__conf-label">置信度</text>
          <view class="ai-card__conf-bar"><view class="ai-card__conf-fill" :style="{width:Math.round(run.confidence*100)+'%'}"></view></view>
          <text class="ai-card__conf-val">{{Math.round(run.confidence*100)}}%</text>
        </view>
        <view v-for="(sug,j) in (run.suggestions||[]).slice(0,3)" :key="j" class="ai-card__sug">
          <text class="ai-card__sug-idx">{{j+1}}</text>
          <text class="ai-card__sug-text">{{sug.text||sug.content||sug}}</text>
        </view>
      </view>
      <view v-if="!aiHistory.length" class="bos-empty"><text class="bos-empty__icon">🤖</text><text class="bos-empty__text">暂无AI运行记录</text></view>
    </template>
  </scroll-view>

  <!-- 底部生成按钮 -->
  <view class="gen-footer">
    <view class="gen-btn" :class="{'gen-btn--loading':generating}" @tap="showStudentPicker=true">
      <text class="gen-btn__text">{{generating?'🤖 AI 分析中...':'🚀 生成跟进计划'}}</text>
    </view>
  </view>

  <!-- 学员选择弹窗 -->
  <view class="modal-mask" v-if="showStudentPicker" @tap="showStudentPicker=false">
    <view class="modal-box" @tap.stop>
      <text class="modal-box__title">选择学员生成跟进计划</text>
      <picker :range="studentNames" @change="onPickStudent">
        <view class="picker-trigger"><text>{{pickedStudent?pickedStudent.name:'请选择学员'}}</text><text style="color:#94a3b8;">▼</text></view>
      </picker>
      <view style="margin-top:16rpx;"><text style="font-size:24rpx;font-weight:600;color:#64748b;">AI 指令（可选）</text></view>
      <textarea class="modal-textarea" v-model="agentPrompt" placeholder="例: 重点关注血糖控制和运动习惯" :maxlength="200" />
      <view class="modal-actions">
        <view class="bos-btn bos-btn--ghost" style="flex:1;" @tap="showStudentPicker=false"><text style="color:#64748b;font-size:26rpx;">取消</text></view>
        <view class="bos-btn bos-btn--primary" style="flex:1;" @tap="runFollowup"><text style="color:#fff;font-size:26rpx;font-weight:700;">开始生成</text></view>
      </view>
    </view>
  </view>

  <!-- 退回原因弹窗 -->
  <view class="modal-mask" v-if="rejectTarget" @tap="rejectTarget=null">
    <view class="modal-box" @tap.stop>
      <text class="modal-box__title">退回原因</text>
      <textarea class="modal-textarea" v-model="rejectReason" placeholder="请输入退回原因（AI将学习改进）..." :maxlength="200" />
      <view class="modal-actions">
        <view class="bos-btn bos-btn--ghost" style="flex:1;" @tap="rejectTarget=null"><text style="color:#64748b;">取消</text></view>
        <view class="bos-btn bos-btn--danger" style="flex:1;" @tap="confirmReject"><text style="color:#fff;font-weight:700;">确认退回</text></view>
      </view>
    </view>
  </view>

  <!-- 编辑弹窗 -->
  <view class="modal-mask" v-if="editTarget" @tap="editTarget=null">
    <view class="modal-box" @tap.stop>
      <text class="modal-box__title">编辑后通过</text>
      <view style="margin-bottom:12rpx;"><text style="font-size:24rpx;font-weight:600;color:#64748b;">标题</text></view>
      <input class="modal-input" v-model="editTitle" />
      <view style="margin:12rpx 0 8rpx;"><text style="font-size:24rpx;font-weight:600;color:#64748b;">内容</text></view>
      <textarea class="modal-textarea" v-model="editContent" :maxlength="500" />
      <view class="modal-actions">
        <view class="bos-btn bos-btn--ghost" style="flex:1;" @tap="editTarget=null"><text style="color:#64748b;">取消</text></view>
        <view class="bos-btn bos-btn--primary" style="flex:1;" @tap="confirmEdit"><text style="color:#fff;font-weight:700;">修改并通过</text></view>
      </view>
    </view>
  </view>
</view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { http, tryGet } from '@/utils/request'

const TABS=[{key:'pending',label:'待审核'},{key:'handled',label:'已处理'},{key:'ai_history',label:'AI记录'}]
const TYPE_LABEL:Record<string,string>={rx_push:'处方推送',prescription:'行为处方',assessment:'评估审核',ai_reply:'AI回复',push:'内容推送',followup:'跟进计划',alert:'风险预警'}

const activeTab=ref('pending'),loading=ref(false),refreshing=ref(false)
const queue=ref<any[]>([]),handledItems=ref<any[]>([]),aiHistory=ref<any[]>([])
const stats=ref({pending:0,approved:0,rejected:0,ai_runs:0})
const rejectTarget=ref<any>(null),rejectReason=ref(''),editTarget=ref<any>(null),editTitle=ref(''),editContent=ref('')
const showStudentPicker=ref(false),studentList=ref<any[]>([]),pickedStudent=ref<any>(null),agentPrompt=ref(''),generating=ref(false)
let refreshTimer:any=null

const studentNames=computed(()=>studentList.value.map(s=>s.name))
const pendingItems=computed(()=>queue.value.filter(i=>!i._handled))

const WHEEL_STEPS=computed(()=>[
  {icon:'📊',label:'数据采集',active:true,count:0},
  {icon:'🤖',label:'AI分析',active:generating.value,count:stats.value.ai_runs},
  {icon:'📋',label:'教练审核',active:stats.value.pending>0,count:stats.value.pending},
  {icon:'📤',label:'推送执行',active:false,count:stats.value.approved},
  {icon:'📈',label:'效果追踪',active:false,count:0},
])

function getTabCount(key:string):number{if(key==='pending')return pendingItems.value.length;if(key==='handled')return handledItems.value.length;if(key==='ai_history')return aiHistory.value.length;return 0}

onMounted(()=>{loadAll();refreshTimer=setInterval(()=>{if(activeTab.value==='pending')loadQueue()},30000)})
onUnmounted(()=>{if(refreshTimer)clearInterval(refreshTimer)})

async function loadAll(){await Promise.all([loadQueue(),loadStats(),loadStudentList()])}
async function refreshAll(){uni.showToast({title:'刷新中...',icon:'none',duration:800});await loadAll()}
async function onRefresh(){refreshing.value=true;await loadAll();refreshing.value=false}

async function loadQueue(){
  loading.value=true
  try{const res=await tryGet<any>(['/v1/coach/review-queue','/v1/coach-push/pending']);if(res){const items=res.items||res.results||[];queue.value=items.map((item:any)=>({...item,student_name:item.student_name||item.target_name||'学员',_handled:false,_action:'',_expanded:false}))}else queue.value=[]}
  catch{queue.value=[]}finally{loading.value=false}
}
async function loadStats(){try{const res=await tryGet<any>(['/v1/coach/stats/today','/v1/coach/dashboard']);if(res){const ts=res.today_stats||res;stats.value={pending:ts.pending??pendingItems.value.length,approved:ts.approved??0,rejected:ts.rejected??0,ai_runs:ts.ai_runs??0}}}catch{}}
async function loadStudentList(){try{const res=await tryGet<any>(['/v1/coach/students','/v1/coach/dashboard']);const list=res?.students||res?.items||[];studentList.value=list.map((s:any)=>({...s,name:s.name||s.full_name||s.username}))}catch{studentList.value=[]}}

async function handleApprove(item:any){try{try{await http.post(`/v1/coach/review/${item.id}/approve`,{})}catch{await http.post(`/v1/coach-push/${item.id}/approve`,{})};item._handled=true;item._action='approved';handledItems.value.unshift({...item});stats.value.approved++;stats.value.pending=Math.max(0,stats.value.pending-1);uni.showToast({title:'已通过',icon:'success'})}catch{uni.showToast({title:'操作失败',icon:'none'})}}
function openRejectModal(item:any){rejectTarget.value=item;rejectReason.value=''}
async function confirmReject(){if(!rejectReason.value.trim()){uni.showToast({title:'请输入退回原因',icon:'none'});return};const item=rejectTarget.value;try{try{await http.post(`/v1/coach/review/${item.id}/reject`,{reason:rejectReason.value})}catch{await http.post(`/v1/coach-push/${item.id}/reject`,{reason:rejectReason.value})};item._handled=true;item._action='rejected';handledItems.value.unshift({...item});stats.value.rejected++;stats.value.pending=Math.max(0,stats.value.pending-1);rejectTarget.value=null;uni.showToast({title:'已退回',icon:'none'})}catch{uni.showToast({title:'操作失败',icon:'none'})}}
function openEditModal(item:any){editTarget.value=item;editTitle.value=item.content_title||'';editContent.value=item.content_body||item.ai_draft||''}
async function confirmEdit(){const item=editTarget.value;try{try{await http.post(`/v1/coach/review/${item.id}/approve`,{edited_title:editTitle.value,edited_content:editContent.value})}catch{await http.post(`/v1/coach-push/${item.id}/approve`,{edited_title:editTitle.value,edited_content:editContent.value})};item._handled=true;item._action='approved';handledItems.value.unshift({...item});editTarget.value=null;uni.showToast({title:'已修改并通过',icon:'success'})}catch{uni.showToast({title:'操作失败',icon:'none'})}}
async function batchApprove(){const items=pendingItems.value;if(!items.length)return;uni.showModal({title:'批量通过',content:`确认通过全部 ${items.length} 条？`,confirmColor:'#16a34a',success:async(res)=>{if(!res.confirm)return;let ok=0;for(const item of items){try{try{await http.post(`/v1/coach/review/${item.id}/approve`,{})}catch{await http.post(`/v1/coach-push/${item.id}/approve`,{})};item._handled=true;item._action='approved';handledItems.value.unshift({...item});ok++}catch{}};stats.value.approved+=ok;stats.value.pending=Math.max(0,stats.value.pending-ok);uni.showToast({title:`已通过 ${ok} 条`,icon:'success'})}})}

function onPickStudent(e:any){pickedStudent.value=studentList.value[Number(e.detail.value)]||null}
async function runFollowup(){if(!pickedStudent.value){uni.showToast({title:'请选择学员',icon:'none'});return};showStudentPicker.value=false;generating.value=true;try{const res=await http.post<any>('/v1/agent/run',{agent_type:'COACHING',user_id:String(pickedStudent.value.id),context:{prompt:agentPrompt.value.trim()||'为学员生成个性化跟进计划'}});const result=res.data||res;aiHistory.value.unshift({student_name:pickedStudent.value.name,created_at:new Date().toISOString(),confidence:result.confidence,suggestions:result.suggestions||[]});stats.value.ai_runs++;uni.showToast({title:'生成完成',icon:'success'})}catch{uni.showToast({title:'生成失败',icon:'none'})}finally{generating.value=false;agentPrompt.value=''}}
function formatDate(dt:string):string{if(!dt)return'';return dt.slice(0,16).replace('T',' ')}
function goBack(){uni.navigateBack({fail:()=>uni.switchTab({url:'/pages/home/index'})})}
</script>

<style scoped>
.bos-page{min-height:100vh;background:linear-gradient(180deg,#f0fdf4 0%,#f8fafc 30%,#f0f9ff 100%);display:flex;flex-direction:column;}
.bos-navbar{display:flex;align-items:center;justify-content:space-between;padding:16rpx 32rpx;padding-top:calc(88rpx + env(safe-area-inset-top));background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1rpx solid rgba(226,232,240,0.4);position:sticky;top:0;z-index:100;}
.bos-navbar__back{width:64rpx;height:64rpx;display:flex;align-items:center;justify-content:center;background:#e2e8f0;border-radius:16rpx;}
.bos-navbar__arrow{font-size:48rpx;color:#0f172a;font-weight:800;line-height:1;}
.bos-navbar__title{font-size:30rpx;font-weight:700;color:#1e293b;}
.nav-refresh{width:64rpx;height:64rpx;display:flex;align-items:center;justify-content:center;font-size:36rpx;color:#16a34a;}

.wheel-wrap{background:rgba(255,255,255,0.85);backdrop-filter:blur(12px);margin:24rpx 32rpx 0;border-radius:32rpx;padding:24rpx;border:2rpx solid rgba(226,232,240,0.5);box-shadow:0 20rpx 50rpx -12rpx rgba(0,0,0,0.08);}
.wheel-center{display:flex;align-items:center;gap:12rpx;margin-bottom:16rpx;}
.wheel-center__label{font-size:28rpx;font-weight:800;color:#1e293b;}
.wheel-steps{display:flex;gap:8rpx;}
.wheel-step{flex:1;display:flex;flex-direction:column;align-items:center;gap:4rpx;padding:12rpx 4rpx;border-radius:16rpx;background:#f8fafc;position:relative;border:2rpx solid transparent;}
.wheel-step--active{background:rgba(22,163,74,0.08);border-color:rgba(22,163,74,0.25);}
.wheel-step__icon{font-size:24rpx;}.wheel-step__text{font-size:18rpx;color:#94a3b8;font-weight:500;}
.wheel-step--active .wheel-step__text{color:#16a34a;font-weight:700;}
.wheel-step__badge{position:absolute;top:-8rpx;right:-4rpx;min-width:28rpx;height:28rpx;border-radius:14rpx;background:#ef4444;color:#fff;font-size:18rpx;font-weight:700;display:flex;align-items:center;justify-content:center;padding:0 6rpx;}

.bos-card{background:rgba(255,255,255,0.85);backdrop-filter:blur(12px);border-radius:32rpx;padding:32rpx;border:2rpx solid rgba(226,232,240,0.5);box-shadow:0 20rpx 50rpx -12rpx rgba(0,0,0,0.08);position:relative;overflow:hidden;}
.bos-stats{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12rpx;}
.bos-stat{text-align:center;padding:16rpx 8rpx;background:linear-gradient(135deg,#f8fafc,rgba(255,255,255,0.6));border-radius:20rpx;border:1rpx solid #e2e8f0;}
.bos-stat__val{display:block;font-size:40rpx;font-weight:800;background:linear-gradient(135deg,#16a34a,#22c55e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.bos-stat__label{display:block;font-size:20rpx;color:#64748b;margin-top:4rpx;font-weight:500;}

.tab-wrap{padding:16rpx 32rpx 0;}
.bos-tabs{display:flex;gap:6rpx;background:#f1f5f9;padding:6rpx;border-radius:20rpx;}
.bos-tab{flex:1;padding:16rpx 12rpx;border-radius:16rpx;font-size:24rpx;font-weight:600;color:#64748b;text-align:center;position:relative;}
.bos-tab--active{background:#fff;color:#16a34a;box-shadow:0 4rpx 12rpx rgba(0,0,0,0.06);}
.bos-tab__badge{position:absolute;top:2rpx;right:8rpx;min-width:28rpx;padding:2rpx 8rpx;background:#ef4444;color:#fff;font-size:18rpx;border-radius:999rpx;font-weight:700;}
.bos-scroll{flex:1;padding:20rpx 32rpx 180rpx;}

.batch-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:16rpx;}
.batch-bar__count{font-size:24rpx;color:#64748b;}

.q-card{background:rgba(255,255,255,0.85);backdrop-filter:blur(8px);border-radius:24rpx;padding:24rpx;margin-bottom:16rpx;border:2rpx solid rgba(226,232,240,0.5);box-shadow:0 4rpx 16rpx rgba(0,0,0,0.04);position:relative;overflow:hidden;}
.q-card--done{opacity:0.55;}
.q-card__done-badge{position:absolute;top:16rpx;right:16rpx;font-size:22rpx;font-weight:700;padding:4rpx 14rpx;border-radius:999rpx;}
.q-card__done-badge--green{background:#dcfce7;color:#16a34a;}.q-card__done-badge--red{background:#fee2e2;color:#dc2626;}
.q-card__head{display:flex;align-items:center;gap:12rpx;margin-bottom:12rpx;flex-wrap:wrap;}
.q-card__name{font-size:28rpx;font-weight:700;color:#1e293b;}
.q-card__type{font-size:20rpx;font-weight:600;padding:4rpx 14rpx;border-radius:999rpx;}
.q-card__type--rx_push,.q-card__type--prescription{background:#dbeafe;color:#2563eb;}
.q-card__type--assessment{background:#f3e8ff;color:#7c3aed;}
.q-card__type--push{background:#fef3c7;color:#d97706;}
.q-card__type--alert{background:#fee2e2;color:#dc2626;}
.q-card__type--ai_reply,.q-card__type--followup{background:#dcfce7;color:#16a34a;}
.q-card__urgent{font-size:18rpx;font-weight:700;padding:2rpx 12rpx;border-radius:999rpx;background:#fee2e2;color:#dc2626;}
.q-card__summary{display:block;font-size:24rpx;color:#64748b;line-height:1.5;margin-bottom:12rpx;}
.q-card__content{background:#f8fafc;border-radius:16rpx;padding:16rpx 20rpx;margin-bottom:12rpx;}
.q-card__content-title{display:block;font-size:26rpx;font-weight:700;color:#1e293b;margin-bottom:8rpx;}
.q-card__clamp{overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;}
.q-card__toggle{display:block;font-size:20rpx;color:#16a34a;margin-top:8rpx;font-weight:600;}
.q-card__actions{display:flex;gap:12rpx;margin-top:16rpx;}

.bos-btn{display:inline-flex;align-items:center;justify-content:center;padding:16rpx 24rpx;border-radius:24rpx;font-size:24rpx;font-weight:700;border:none;}
.bos-btn:active{transform:scale(0.97);}
.bos-btn--primary{background:linear-gradient(135deg,#22c55e,#16a34a);box-shadow:0 8rpx 24rpx -4rpx rgba(22,163,74,0.35);}
.bos-btn--pill{border-radius:999rpx;padding:12rpx 28rpx;}
.bos-btn--outline{background:#fff;border:2rpx solid #bfdbfe;}
.bos-btn--danger-outline{background:#fff;border:2rpx solid #fecaca;}
.bos-btn--danger{background:linear-gradient(135deg,#ef4444,#dc2626);box-shadow:0 8rpx 24rpx -4rpx rgba(239,68,68,0.35);}
.bos-btn--ghost{background:#f1f5f9;}

.ai-card{background:rgba(255,255,255,0.85);backdrop-filter:blur(8px);border-radius:24rpx;padding:24rpx;margin-bottom:16rpx;border:2rpx solid rgba(226,232,240,0.5);}
.ai-card__head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12rpx;}
.ai-card__name{font-size:26rpx;font-weight:700;color:#1e293b;}.ai-card__time{font-size:22rpx;color:#94a3b8;}
.ai-card__conf{display:flex;align-items:center;gap:12rpx;margin-bottom:12rpx;}
.ai-card__conf-label{font-size:22rpx;color:#64748b;flex-shrink:0;}.ai-card__conf-bar{flex:1;height:12rpx;background:#f1f5f9;border-radius:999rpx;overflow:hidden;}
.ai-card__conf-fill{height:100%;background:linear-gradient(90deg,#22c55e,#16a34a);border-radius:999rpx;}.ai-card__conf-val{font-size:22rpx;font-weight:700;color:#16a34a;}
.ai-card__sug{display:flex;gap:10rpx;margin-bottom:8rpx;}.ai-card__sug-idx{font-size:20rpx;font-weight:700;color:#16a34a;}.ai-card__sug-text{font-size:24rpx;color:#475569;line-height:1.5;}

.gen-footer{position:fixed;bottom:0;left:0;right:0;padding:20rpx 32rpx;padding-bottom:calc(20rpx + env(safe-area-inset-bottom));background:rgba(255,255,255,0.85);backdrop-filter:blur(20px);border-top:1rpx solid rgba(226,232,240,0.4);}
.gen-btn{height:88rpx;border-radius:24rpx;background:linear-gradient(135deg,#16a34a 0%,#22c55e 100%);display:flex;align-items:center;justify-content:center;box-shadow:0 8rpx 24rpx rgba(22,163,74,0.3);}
.gen-btn--loading{opacity:0.7;pointer-events:none;}
.gen-btn__text{font-size:30rpx;font-weight:700;color:#fff;}

.modal-mask{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:999;}
.modal-box{width:88%;background:#fff;border-radius:32rpx;padding:32rpx;}
.modal-box__title{display:block;font-size:30rpx;font-weight:700;color:#1e293b;margin-bottom:24rpx;}
.modal-textarea{width:100%;min-height:160rpx;padding:16rpx 20rpx;background:#f8fafc;border-radius:16rpx;border:2rpx solid #e2e8f0;font-size:26rpx;color:#1e293b;box-sizing:border-box;margin-top:8rpx;}
.modal-input{width:100%;height:72rpx;padding:0 20rpx;background:#f8fafc;border-radius:16rpx;border:2rpx solid #e2e8f0;font-size:26rpx;color:#1e293b;box-sizing:border-box;}
.modal-actions{display:flex;gap:16rpx;margin-top:24rpx;}
.picker-trigger{display:flex;justify-content:space-between;align-items:center;padding:20rpx 24rpx;background:#f8fafc;border-radius:16rpx;border:2rpx solid #e2e8f0;font-size:28rpx;color:#1e293b;margin-top:8rpx;}

.bos-empty{display:flex;flex-direction:column;align-items:center;padding:120rpx 0;gap:16rpx;}
.bos-empty__icon{font-size:64rpx;opacity:0.6;}.bos-empty__text{font-size:26rpx;color:#94a3b8;font-weight:500;}
.bos-skeleton{background:linear-gradient(90deg,#f1f5f9 25%,#f8fafc 50%,#f1f5f9 75%);background-size:200% 100%;animation:bos-shimmer 1.5s ease-in-out infinite;border-radius:24rpx;}
@keyframes bos-shimmer{0%{background-position:200% 0;}100%{background-position:-200% 0;}}
</style>
