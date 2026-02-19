import React, { useState } from 'react';
import { DualSignPanel } from '../Expert/DualSignPanel';
import TracePage from './TracePage';
import { AuditCase } from '../../../types/react-types';

const ExpertWorkspace = () => {
  const [activeTab, setActiveTab] = useState<'audit' | 'trace' | 'brain'>('audit');
  const [auditCase, setAuditCase] = useState<AuditCase | null>(null);

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
        {activeTab === 'audit' && (auditCase ? <DualSignPanel auditCase={auditCase} /> : (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-400">
            <p>暂无待审案例</p>
          </div>
        ))}
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
