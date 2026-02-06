import React, { useState } from 'react';
import { DualSignPanel } from '../Expert/DualSignPanel';
import TracePage from './TracePage';
import { AuditCase } from '../../../types/react-types';

const mockCase: AuditCase = {
  id: 'tr_7721',
  patientId: 'PT-8821',
  rawMetrics: {
    phq9: 18,
    cgmTrend: '波动剧烈',
    riskLevel: 'R3'
  },
  originalL5Output: '检测到中重度抑郁倾向及餐后血糖控制不佳。建议立即启动抗抑郁筛查并限制碳水摄入。',
  narrativeL6Preview: '最近似乎感到身体有些沉重？没关系，这是身体在提醒我们需要一点小小的调整。试试看从一次深呼吸开始，慢慢找回节律。',
  status: 'pending',
  decisionRules: {
    trigger: 'PHQ9_DEPRESSION_CHECK',
    logic: 'IF phq9 >= 15 AND cgm_volatility > 3.9 THEN SET RISK = R3',
    octopus_clamp: 'LIMIT_TASKS = 1',
    narrative_override: 'CONVERT_TO_EMPATHY'
  },
  decisionTraceId: 'trace_20240115_7721',
  createdAt: new Date('2024-01-15')
};

const ExpertWorkspace = () => {
  const [activeTab, setActiveTab] = useState<'audit' | 'trace' | 'brain'>('audit');

  if (activeTab === 'trace') {
    return <TracePage />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100">
      <nav className="h-20 bg-gradient-to-r from-slate-600 via-slate-500 to-slate-600 flex items-center justify-between px-8 text-white shadow-2xl border-b-2 border-slate-400">
        <div className="flex items-center gap-6">
          <div className="flex flex-col">
            <span className="font-bold tracking-tight text-2xl bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              主动健康·吃动守恒
            </span>
            <span className="text-xs text-slate-400 tracking-wider">专家工作台 Expert Workspace</span>
          </div>
          <span className="text-xs bg-growth-600/20 text-growth-400 px-3 py-1 rounded-full border border-growth-600/30">
            v16.1.0
          </span>
        </div>
        <div className="flex gap-8 text-sm">
          <button
            onClick={() => setActiveTab('audit')}
            className={`flex items-center gap-2 transition-opacity cursor-pointer ${
              activeTab === 'audit' ? 'text-growth-400 font-bold' : 'opacity-50 hover:opacity-100'
            }`}
          >
            {activeTab === 'audit' && <span className="w-2 h-2 bg-growth-400 rounded-full animate-pulse"></span>}
            待审队列 (12)
          </button>
          <button
            onClick={() => setActiveTab('trace')}
            className={`transition-opacity cursor-pointer ${
              activeTab === 'trace' ? 'text-growth-400 font-bold' : 'opacity-50 hover:opacity-100'
            }`}
          >
            决策回溯 (Trace)
          </button>
          <button
            onClick={() => setActiveTab('brain')}
            className={`transition-opacity cursor-pointer ${
              activeTab === 'brain' ? 'text-growth-400 font-bold' : 'opacity-50 hover:opacity-100'
            }`}
          >
            规则引擎 (Brain)
          </button>
        </div>
      </nav>

      <main className="max-w-[1400px] mx-auto py-8">
        {activeTab === 'audit' && <DualSignPanel auditCase={mockCase} />}
        {activeTab === 'brain' && (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-400">
            <p>规则引擎功能开发中...</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default ExpertWorkspace;
