import React, { useEffect, useState } from 'react';
import { DecisionTrace } from '../Trace/DecisionTrace';
import { TraceNode } from '../../../types/react-types';
import { useBrainContext } from '../../../contexts/BrainContext';

const AdminEvolution = () => {
  const { decisionTraces } = useBrainContext();
  const [displayNodes, setDisplayNodes] = useState<TraceNode[]>([]);

  useEffect(() => {
    if (decisionTraces.length > 0) {
      setDisplayNodes(decisionTraces);
    }
  }, [decisionTraces]);
  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-100 via-blue-200 to-cyan-300 p-8">
      <header className="flex justify-between items-center mb-10 border-b border-blue-300/50 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-blue-900 tracking-tight">
            管理 / 研究 / 进化界面 (Evolution UI)
          </h1>
          <p className="text-blue-700 text-sm mt-1">SOP 6.2 流程监控与决策回溯审计</p>
        </div>
        <div className="flex gap-4">
          <div className="text-right">
            <p className="text-[10px] text-blue-600 uppercase">System Status</p>
            <p className="text-growth-600 font-mono text-sm font-bold">Decision Core Active</p>
          </div>
          <div className="w-10 h-10 bg-white/80 rounded-lg border border-blue-300 flex items-center justify-center shadow-md">
            <div className="w-2 h-2 bg-growth-500 rounded-full animate-ping" />
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto space-y-8">
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-blue-800 font-bold text-sm uppercase">
              BehavioralBrain 决策链路回放
            </h3>
            <button className="text-xs bg-white/80 hover:bg-white text-blue-700 px-3 py-1 rounded transition-colors border border-blue-300 shadow-sm">
              切换 Trace_ID
            </button>
          </div>
          <DecisionTrace nodes={displayNodes} />
        </section>

        <div className="grid grid-cols-3 gap-6">
          <StatBox label="SOP 6.2 拦截效能" value="99.8%" sub="UI-1 -> SILENCE 路径" />
          <StatBox label="SPI 平均增量" value="+4.2%" sub="近24小时阶段迁移" />
          <StatBox label="L6 改写成功率" value="96.5%" sub="4维评分 QA 结果" />
        </div>
      </div>
    </div>
  );
};

const StatBox = ({ label, value, sub }: { label: string; value: string; sub: string }) => (
  <div className="bg-white/70 backdrop-blur-sm border border-blue-300 p-5 rounded-2xl shadow-lg">
    <p className="text-blue-600 text-[10px] uppercase font-bold">{label}</p>
    <p className="text-2xl font-mono text-blue-900 mt-1">{value}</p>
    <p className="text-blue-500 text-[10px] mt-2 italic">{sub}</p>
  </div>
);

export default AdminEvolution;
