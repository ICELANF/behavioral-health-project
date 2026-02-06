import React, { useEffect, useState } from 'react';
import { Heart, TrendingUp, Clock } from 'lucide-react';
import { supabase, AuditLog } from '../../../lib/supabase';
import { useBrainContext } from '../../../contexts/BrainContext';
import { TraceNode } from '../../../types/react-types';

export const JourneyPage = () => {
  const [latestMessage, setLatestMessage] = useState<AuditLog | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { addDecisionTrace, calculateRiskScore } = useBrainContext();

  const createDecisionTrace = (message: AuditLog) => {
    const timestamp = new Date().toISOString();
    const traceNodes: TraceNode[] = [
      {
        id: `${message.trace_id}-n1`,
        type: 'INPUT',
        label: '行为事件',
        value: `数据采集 - 用户查看健康洞察`,
        timestamp,
        metadata: { traceId: message.trace_id }
      },
      {
        id: `${message.trace_id}-n2`,
        type: 'RULE',
        label: '触发路由',
        value: `审核通过 - L6 改写输出`,
        timestamp,
        metadata: { approvalStatus: message.approval_status }
      },
      {
        id: `${message.trace_id}-n3`,
        type: 'DECISION',
        label: 'Brain 判定',
        value: `风险评估完成 - 内容披露`,
        timestamp,
        metadata: {}
      },
      {
        id: `${message.trace_id}-n4`,
        type: 'OUTPUT',
        label: '用户界面呈现',
        value: `推送：${message.approved_l6_output?.substring(0, 30)}...`,
        timestamp,
        metadata: {}
      }
    ];

    traceNodes.forEach(node => addDecisionTrace(node));
  };

  useEffect(() => {
    const fetchLatestMessage = async () => {
      try {
        const { data, error } = await supabase
          .from('behavior_audit_logs')
          .select('*')
          .order('approved_at', { ascending: false })
          .limit(1)
          .maybeSingle();

        if (error) throw error;
        setLatestMessage(data);
        if (data) {
          createDecisionTrace(data);
        }
      } catch (error) {
        console.error('Failed to fetch message:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLatestMessage();

    const subscription = supabase
      .channel('audit_logs_changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'behavior_audit_logs',
        },
        (payload) => {
          const newMessage = payload.new as AuditLog;
          setLatestMessage(newMessage);
          createDecisionTrace(newMessage);
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [addDecisionTrace]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-growth-50 to-white flex items-center justify-center">
        <div className="text-growth-600">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-growth-50 via-white to-growth-50">
      <header className="bg-white/80 backdrop-blur-sm border-b border-growth-100 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-growth-500 rounded-full flex items-center justify-center">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-growth-900">OCTOPUS</h1>
                <p className="text-xs text-growth-600">您的健康成长伙伴</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-growth-600">
              <Clock className="w-4 h-4" />
              <span>今日</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        {latestMessage ? (
          <div className="space-y-6">
            <div className="bg-white rounded-3xl shadow-lg p-8 border border-growth-100">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-growth-400 to-growth-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h2 className="text-xl font-bold text-growth-900 mb-2">
                    今日健康洞察
                  </h2>
                  <p className="text-sm text-growth-600">
                    {new Date(latestMessage.approved_at || '').toLocaleDateString('zh-CN', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>

              <div className="prose prose-growth max-w-none">
                <p className="text-lg leading-relaxed text-growth-800 italic">
                  {latestMessage.approved_l6_output}
                </p>
              </div>

              <div className="mt-8 pt-6 border-t border-growth-100">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 text-growth-600">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    <span>由专业团队审核</span>
                  </div>
                  <span className="text-xs text-growth-400 font-mono">
                    {latestMessage.trace_id}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white/50 rounded-2xl p-6 border border-growth-100">
              <h3 className="text-sm font-bold text-growth-900 mb-3">
                持续陪伴，共同成长
              </h3>
              <p className="text-sm text-growth-700 leading-relaxed">
                我们会持续关注您的健康数据，及时为您提供个性化的建议和支持。每一步成长，我们都与您同在。
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-3xl shadow-lg p-12 text-center border border-growth-100">
            <div className="w-16 h-16 bg-growth-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Heart className="w-8 h-8 text-growth-500" />
            </div>
            <h2 className="text-xl font-bold text-growth-900 mb-2">
              暂无新消息
            </h2>
            <p className="text-growth-600">
              当有新的健康洞察时，我们会第一时间通知您
            </p>
          </div>
        )}
      </main>
    </div>
  );
};

export default JourneyPage;
