import React from 'react';
import { motion } from 'framer-motion';
import { TraceNode } from '../../../types/react-types';

interface DecisionTraceProps {
  nodes: TraceNode[];
  ruleJson?: string;
}

const getNodeColor = (type: TraceNode['type']) => {
  switch (type) {
    case 'INPUT':
      return 'bg-blue-500 shadow-blue-500/20';
    case 'RULE':
      return 'bg-amber-500 shadow-amber-500/20';
    case 'DECISION':
      return 'bg-purple-500 shadow-purple-500/20';
    case 'OUTPUT':
      return 'bg-growth-500 shadow-growth-500/20';
    default:
      return 'bg-slate-500';
  }
};

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

export const DecisionTrace: React.FC<DecisionTraceProps> = ({ nodes, ruleJson }) => {
  const defaultRuleJson = `{
  "trigger": "CGM_HIGH_VOLATILITY",
  "logic": "IF val > 10.0 AND trend == 'UP' THEN SET RISK = R3",
  "octopus_clamp": "LIMIT_TASKS = 1",
  "narrative_override": "CONVERT_TO_EMPATHY"
}`;

  return (
    <div className="bg-white/80 backdrop-blur-sm p-10 rounded-3xl border border-blue-300 shadow-2xl overflow-hidden relative">
      <div className="absolute top-4 left-6 text-blue-600 font-mono text-[10px] uppercase tracking-widest">
        Logic Flow Trace System // Trace_ID: TR-88921-X
      </div>

      <div className="flex flex-col md:flex-row items-center justify-between gap-4 relative z-10 mt-8">
        {nodes.map((node, index) => (
          <React.Fragment key={node.id}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.2 }}
              className="flex flex-col items-center group"
            >
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 shadow-lg transition-transform group-hover:scale-110 ${getNodeColor(
                  node.type
                )}`}
              >
                <span className="text-white text-xs font-bold">{node.type[0]}</span>
              </div>
              <div className="bg-white/90 backdrop-blur p-4 rounded-xl border border-blue-200 w-48 text-center shadow-md">
                <p className="text-blue-600 text-[10px] uppercase font-semibold">{node.label}</p>
                <p className="text-blue-900 text-xs mt-1 font-medium leading-relaxed">
                  {node.value}
                </p>
                <p className="text-blue-500 text-[9px] mt-2 font-mono">
                  {formatTimestamp(node.timestamp)}
                </p>
              </div>
            </motion.div>

            {index < nodes.length - 1 && (
              <div className="hidden md:block w-20 h-[2px] bg-blue-200 relative">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ delay: index * 0.2 + 0.1, duration: 0.5 }}
                  className="h-full bg-growth-500 shadow-[0_0_10px_#4ade80]"
                />
                <div className="absolute -right-1 -top-1 w-2 h-2 bg-growth-500 rounded-full blur-[2px]" />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      <div className="mt-12 bg-blue-50/60 p-6 rounded-2xl border border-blue-200 font-mono text-[11px]">
        <h4 className="text-blue-700 mb-3 flex items-center gap-2 font-semibold">
          <span className="w-2 h-2 bg-growth-500 rounded-full" />
          DECISION_RULES_JSON (spi_mapping.json)
        </h4>
        <pre className="text-blue-700/80 leading-5 overflow-x-auto">
          {ruleJson || defaultRuleJson}
        </pre>
      </div>
    </div>
  );
};
