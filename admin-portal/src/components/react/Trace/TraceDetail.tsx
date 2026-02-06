import React from 'react';
import { TraceNode } from '../../../types/react-types';
import { Clock, Database, GitBranch, FileOutput } from 'lucide-react';

interface TraceDetailProps {
  node: TraceNode | null;
}

const getNodeIcon = (type: TraceNode['type']) => {
  switch (type) {
    case 'INPUT':
      return <Database className="w-5 h-5" />;
    case 'RULE':
      return <GitBranch className="w-5 h-5" />;
    case 'DECISION':
      return <GitBranch className="w-5 h-5" />;
    case 'OUTPUT':
      return <FileOutput className="w-5 h-5" />;
  }
};

const getNodeTypeLabel = (type: TraceNode['type']) => {
  switch (type) {
    case 'INPUT':
      return '输入数据';
    case 'RULE':
      return '规则判断';
    case 'DECISION':
      return '决策节点';
    case 'OUTPUT':
      return '输出结果';
  }
};

const getNodeColor = (type: TraceNode['type']) => {
  switch (type) {
    case 'INPUT':
      return 'bg-blue-500';
    case 'RULE':
      return 'bg-purple-500';
    case 'DECISION':
      return 'bg-amber-500';
    case 'OUTPUT':
      return 'bg-emerald-500';
  }
};

export const TraceDetail: React.FC<TraceDetailProps> = ({ node }) => {
  if (!node) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-400">
        <GitBranch className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p className="text-sm">选择一个节点查看详情</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className={`${getNodeColor(node.type)} text-white p-4 flex items-center gap-3`}>
        {getNodeIcon(node.type)}
        <div>
          <div className="text-xs opacity-75">{getNodeTypeLabel(node.type)}</div>
          <div className="font-bold text-lg">{node.label}</div>
        </div>
      </div>

      <div className="p-6 space-y-4">
        <div>
          <div className="text-xs font-semibold text-slate-500 mb-2">节点ID</div>
          <div className="font-mono text-sm bg-slate-50 px-3 py-2 rounded border border-slate-200">
            {node.id}
          </div>
        </div>

        <div>
          <div className="text-xs font-semibold text-slate-500 mb-2">节点值</div>
          <div className="text-sm bg-slate-50 px-3 py-2 rounded border border-slate-200 whitespace-pre-wrap">
            {node.value}
          </div>
        </div>

        <div>
          <div className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-2">
            <Clock className="w-3 h-3" />
            时间戳
          </div>
          <div className="text-sm text-slate-600">
            {new Date(node.timestamp).toLocaleString('zh-CN')}
          </div>
        </div>
      </div>
    </div>
  );
};
