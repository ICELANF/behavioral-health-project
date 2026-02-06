import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Zap, Heart, Eye } from 'lucide-react';

interface RuleProps {
  rule: {
    trigger: string;
    logic: string;
    octopus_clamp: string;
    narrative_override: string;
  };
}

export const LogicInterpreter: React.FC<RuleProps> = ({ rule }) => {
  const translateTrigger = (t: string) => {
    const map: any = {
      'CGM_HIGH_VOLATILITY': '检测到血糖剧烈波动',
      'LOW_ACTIVITY_DETECTED': '检测到长时间静坐',
      'HEART_RATE_SPIKE': '心率异常升高'
    };
    return map[t] || t;
  };

  const parseRisk = (logic: string) => {
    if (logic.includes('R3')) return { label: '中高风险 (R3)', color: 'text-amber-600', bg: 'bg-amber-50' };
    if (logic.includes('R4')) return { label: '紧急预警 (R4)', color: 'text-red-600', bg: 'bg-red-50' };
    return { label: '常规波动', color: 'text-blue-600', bg: 'bg-blue-50' };
  };

  const risk = parseRisk(rule.logic);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      <div className="bg-slate-50 px-5 py-3 border-b border-slate-200 flex justify-between items-center">
        <h3 className="text-sm font-bold text-slate-700 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-growth-500" />
          系统决策自动解析
        </h3>
        <span className="text-[10px] bg-slate-200 px-2 py-0.5 rounded text-slate-500 font-mono">
          DECISION_LOGIC_V1
        </span>
      </div>

      <div className="p-5 space-y-6">
        <section className="flex gap-4">
          <div className="flex-none w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
            <Eye className="w-4 h-4" />
          </div>
          <div>
            <p className="text-[11px] text-slate-400 uppercase font-bold tracking-tight">感知层 (Input)</p>
            <p className="text-sm text-slate-700 font-medium">
              系统通过触手感知到：<span className="text-blue-600">{translateTrigger(rule.trigger)}</span>
            </p>
          </div>
        </section>

        <section className="flex gap-4">
          <div className={`flex-none w-8 h-8 rounded-full ${risk.bg} flex items-center justify-center ${risk.color}`}>
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <p className="text-[11px] text-slate-400 uppercase font-bold tracking-tight">判定层 (Logic)</p>
            <p className="text-sm text-slate-700">
              判定结果为 <span className={`font-bold ${risk.color}`}>{risk.label}</span>。
              <span className="text-slate-500 ml-1">依据规则："{rule.logic}"</span>
            </p>
          </div>
        </section>

        <section className="flex gap-4">
          <div className="flex-none w-8 h-8 rounded-full bg-growth-100 flex items-center justify-center text-growth-600">
            <Heart className="w-4 h-4" />
          </div>
          <div>
            <p className="text-[11px] text-slate-400 uppercase font-bold tracking-tight">人文保护层 (Action)</p>
            <div className="mt-2 space-y-2">
              <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 p-2 rounded-lg border border-dashed border-slate-300">
                <div className="w-1.5 h-1.5 bg-growth-500 rounded-full" />
                <span><strong>效能钳制：</strong>已自动减少干扰，仅保留 1 项核心建议。</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 p-2 rounded-lg border border-dashed border-slate-300">
                <div className="w-1.5 h-1.5 bg-growth-500 rounded-full" />
                <span><strong>话术转换：</strong>强制开启"温暖共情"风格，屏蔽医疗术语。</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="px-5 py-3 bg-slate-50 text-[10px] text-slate-400 italic border-t border-slate-100 text-right">
        * 本解析由 BehavioralBrain 审计引擎自动生成
      </div>
    </motion.div>
  );
};
