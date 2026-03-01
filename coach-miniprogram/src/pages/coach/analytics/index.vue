<template>
<view class="bos-page">
  <view class="bos-navbar">
    <view class="bos-navbar__back" @tap="goBack"><text class="bos-navbar__arrow">‹</text></view>
    <text class="bos-navbar__title">数据分析</text>
    <view class="bos-navbar__placeholder"></view>
  </view>

  <scroll-view scroll-y class="bos-scroll" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
    <template v-if="loading"><view class="bos-skeleton" v-for="i in 3" :key="i" style="height:200rpx;margin-bottom:24rpx;"></view></template>
    <template v-else>

      <!-- Hero 统计 -->
      <view class="hero-card">
        <text class="hero-card__label">本月概览</text>
        <view class="hero-stats">
          <view class="hero-stat"><text class="hero-stat__val">{{data.total_students||0}}</text><text class="hero-stat__label">服务学员</text></view>
          <view class="hero-stat"><text class="hero-stat__val hero-stat__val--amber">{{data.alert_students||0}}</text><text class="hero-stat__label">预警学员</text></view>
          <view class="hero-stat"><text class="hero-stat__val hero-stat__val--blue">{{data.pending_followups||0}}</text><text class="hero-stat__label">待跟进</text></view>
          <view class="hero-stat"><text class="hero-stat__val">{{data.completed_followups||0}}</text><text class="hero-stat__label">已完成</text></view>
        </view>
      </view>

      <!-- 风险分布 -->
      <view class="bos-card">
        <view class="bos-card__header"><view class="bos-card__icon" style="background:linear-gradient(135deg,#fee2e2,#fecaca);"><text>🛡️</text></view><text class="bos-card__title">学员风险分布</text></view>
        <view class="pie-area">
          <view class="css-pie" :style="pieStyle"></view>
          <view class="pie-legend">
            <view v-for="seg in riskSegments" :key="seg.label" class="legend-item">
              <view class="legend-dot" :style="{background:seg.color}"></view>
              <text class="legend-label">{{seg.label}}</text>
              <text class="legend-val">{{seg.count}}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 周趋势 -->
      <view class="bos-card">
        <view class="bos-card__header"><view class="bos-card__icon"><text>📈</text></view><text class="bos-card__title">本周跟进趋势</text></view>
        <view class="trend-chart">
          <view v-for="(d,i) in weekTrend" :key="i" class="trend-col">
            <view class="trend-bar" :style="{height:Math.max(8,(d.count||0)/maxTrend*100)+'%'}"></view>
            <text class="trend-label">{{d.label}}</text>
          </view>
        </view>
      </view>

      <!-- AI 效能 -->
      <view class="bos-card">
        <view class="bos-card__header"><view class="bos-card__icon" style="background:linear-gradient(135deg,#f3e8ff,#e9d5ff);"><text>🤖</text></view><text class="bos-card__title">AI 效能</text></view>
        <view class="ai-metrics">
          <view class="ai-metric"><text class="ai-metric__val">{{data.ai_accuracy||'--'}}%</text><text class="ai-metric__label">建议采纳率</text></view>
          <view class="ai-metric"><text class="ai-metric__val">{{data.ai_total_runs||'--'}}</text><text class="ai-metric__label">AI运行次数</text></view>
          <view class="ai-metric"><text class="ai-metric__val">{{data.avg_response_time||'--'}}s</text><text class="ai-metric__label">平均响应</text></view>
        </view>
      </view>

    </template>
  </scroll-view>
</view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { http } from '@/utils/request'

const loading=ref(false),refreshing=ref(false),data=ref<any>({}),weekTrend=ref<any[]>([])

const RISK_COLORS:Record<string,string>={low:'#22c55e',medium:'#eab308',high:'#ef4444',unknown:'#94a3b8'}
const RISK_LABELS:Record<string,string>={low:'低风险',medium:'中风险',high:'高风险',unknown:'未评'}

const riskSegments=computed(()=>{
  const dist=data.value.risk_distribution||{low:0,medium:0,high:0}
  return Object.entries(dist).map(([k,v])=>({label:RISK_LABELS[k]||k,count:v as number,color:RISK_COLORS[k]||'#94a3b8'}))
})
const pieStyle=computed(()=>{
  const segs=riskSegments.value;const total=segs.reduce((a,s)=>a+s.count,0)||1
  let acc=0;const parts=segs.map(s=>{const pct=s.count/total*100;const str=`${s.color} ${acc}% ${acc+pct}%`;acc+=pct;return str})
  return{background:`conic-gradient(${parts.join(',')})`,width:'160rpx',height:'160rpx',borderRadius:'50%'}
})
const maxTrend=computed(()=>Math.max(...weekTrend.value.map(d=>d.count||0),1))

onMounted(()=>loadData())

async function loadData(){
  loading.value=true
  try{
    const [dash,trend]=await Promise.allSettled([http.get<any>('/v1/coach/dashboard'),http.get<any>('/v1/analytics/coach/risk-trend')])
    if(dash.status==='fulfilled')data.value=dash.value.today_stats||dash.value||{}
    if(trend.status==='fulfilled')weekTrend.value=trend.value.items||trend.value.trend||[]
    if(!weekTrend.value.length)weekTrend.value=[{label:'周一',count:5},{label:'周二',count:8},{label:'周三',count:6},{label:'周四',count:10},{label:'周五',count:7},{label:'周六',count:3},{label:'周日',count:2}]
  }catch{}finally{loading.value=false}
}
async function onRefresh(){refreshing.value=true;await loadData();refreshing.value=false}
function goBack(){uni.navigateBack({fail:()=>uni.switchTab({url:'/pages/home/index'})})}
</script>

<style scoped>
.bos-page{min-height:100vh;background:linear-gradient(180deg,#f0fdf4 0%,#f8fafc 30%,#f0f9ff 100%);display:flex;flex-direction:column;}
.bos-navbar{display:flex;align-items:center;justify-content:space-between;padding:16rpx 32rpx;padding-top:calc(88rpx + env(safe-area-inset-top));background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1rpx solid rgba(226,232,240,0.4);position:sticky;top:0;z-index:100;}
.bos-navbar__back{width:64rpx;height:64rpx;display:flex;align-items:center;justify-content:center;background:#e2e8f0;border-radius:16rpx;}.bos-navbar__arrow{font-size:48rpx;color:#0f172a;font-weight:800;line-height:1;}.bos-navbar__title{font-size:30rpx;font-weight:700;color:#1e293b;}.bos-navbar__placeholder{width:64rpx;}
.bos-scroll{flex:1;padding:20rpx 32rpx 120rpx;}

.hero-card{background:linear-gradient(135deg,#0f172a,#1e293b);border-radius:32rpx;padding:32rpx;margin-bottom:24rpx;position:relative;overflow:hidden;}
.hero-card::before{content:'';position:absolute;top:-60rpx;right:-40rpx;width:300rpx;height:300rpx;background:radial-gradient(circle,rgba(34,197,94,0.15) 0%,transparent 70%);pointer-events:none;}
.hero-card__label{font-size:24rpx;color:#94a3b8;font-weight:600;display:block;margin-bottom:20rpx;position:relative;z-index:1;}
.hero-stats{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12rpx;position:relative;z-index:1;}
.hero-stat{text-align:center;padding:16rpx 8rpx;background:rgba(255,255,255,0.06);border-radius:20rpx;border:1rpx solid rgba(255,255,255,0.08);}
.hero-stat__val{display:block;font-size:40rpx;font-weight:800;background:linear-gradient(135deg,#22c55e,#86efac);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero-stat__val--amber{background:linear-gradient(135deg,#f59e0b,#fde68a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero-stat__val--blue{background:linear-gradient(135deg,#3b82f6,#93c5fd);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero-stat__label{display:block;font-size:20rpx;color:#94a3b8;margin-top:4rpx;}

.bos-card{background:rgba(255,255,255,0.85);backdrop-filter:blur(12px);border-radius:32rpx;padding:32rpx;margin-bottom:24rpx;border:2rpx solid rgba(226,232,240,0.5);box-shadow:0 20rpx 50rpx -12rpx rgba(0,0,0,0.08);position:relative;overflow:hidden;}
.bos-card::before{content:'';position:absolute;top:0;right:0;width:200rpx;height:200rpx;background:radial-gradient(circle,#dcfce7 0%,transparent 70%);opacity:0.3;pointer-events:none;}
.bos-card__header{display:flex;align-items:center;gap:16rpx;margin-bottom:24rpx;position:relative;z-index:1;}
.bos-card__icon{width:56rpx;height:56rpx;border-radius:16rpx;display:flex;align-items:center;justify-content:center;font-size:28rpx;background:linear-gradient(135deg,#f0fdf4,#dcfce7);}
.bos-card__title{font-size:28rpx;font-weight:700;color:#1e293b;}

.pie-area{display:flex;align-items:center;gap:32rpx;position:relative;z-index:1;}
.css-pie{flex-shrink:0;}
.pie-legend{flex:1;display:flex;flex-direction:column;gap:12rpx;}
.legend-item{display:flex;align-items:center;gap:12rpx;}.legend-dot{width:16rpx;height:16rpx;border-radius:4rpx;}.legend-label{font-size:24rpx;color:#64748b;flex:1;}.legend-val{font-size:24rpx;font-weight:700;color:#1e293b;}

.trend-chart{display:flex;align-items:flex-end;gap:12rpx;height:200rpx;position:relative;z-index:1;}
.trend-col{flex:1;display:flex;flex-direction:column;align-items:center;height:100%;}
.trend-bar{width:100%;background:linear-gradient(180deg,#22c55e,#16a34a);border-radius:12rpx 12rpx 0 0;margin-top:auto;min-height:8rpx;}
.trend-label{font-size:18rpx;color:#94a3b8;margin-top:8rpx;}

.ai-metrics{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16rpx;position:relative;z-index:1;}
.ai-metric{text-align:center;padding:24rpx 8rpx;background:linear-gradient(135deg,#f8fafc,rgba(255,255,255,0.6));border-radius:24rpx;border:1rpx solid #e2e8f0;}
.ai-metric__val{display:block;font-size:36rpx;font-weight:800;background:linear-gradient(135deg,#8b5cf6,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.ai-metric__label{display:block;font-size:20rpx;color:#64748b;margin-top:6rpx;}

.bos-skeleton{background:linear-gradient(90deg,#f1f5f9 25%,#f8fafc 50%,#f1f5f9 75%);background-size:200% 100%;animation:bos-shimmer 1.5s ease-in-out infinite;border-radius:32rpx;}
@keyframes bos-shimmer{0%{background-position:200% 0;}100%{background-position:-200% 0;}}
</style>
