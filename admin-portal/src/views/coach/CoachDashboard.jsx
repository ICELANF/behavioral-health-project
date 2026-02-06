import React, { useState } from 'react';

// 模拟数据
const mockStudent = {
  id: 'U1024',
  name: '张XX',
  gender: '女',
  age: 48,
  avatar: '👩',
  chiefComplaint: '糖化血红蛋白6.5%，空腹血糖偏高',
  enrollmentDate: '2026-01-15',
  daysEnrolled: 18,
  currentStage: 'S1',
  stageName: '思考期',
  lastActive: '2小时前',
  riskLevel: 'YELLOW'
};

const mockDiagnosis = {
  spiScore: 52,
  spiLevel: 'medium_high',
  spiInterpretation: '中等偏上',
  successRate: '50-70%',
  psychLevel: 'L3',
  psychLevelName: '妥协与接受',
  psychLevelDisplay: '准备期',
  coefficient: 0.6,
  confidence: 0.82,
  updatedAt: '2026-01-28',
  dataSource: '隐性+补充问卷',
  
  problemDifficultyPurpose: {
    surfaceProblem: '糖化血红蛋白6.5%，空腹血糖偏高',
    behaviorDifficulty: ['情绪性进食(压力大时吃零食)', '缺乏运动习惯', '睡眠不足'],
    deepPurpose: '保持健康陪伴孩子成长，维持工作状态'
  },
  
  sixReasons: [
    { id: 'D1', name: '内在驱动力', score: 16, max: 20, source: '目标陈述', isWeak: false },
    { id: 'D2', name: '外在事件', score: 12, max: 20, source: '体检报告', isWeak: false },
    { id: 'D3', name: '情绪体验', score: 14, max: 20, source: '对话分析', isWeak: false },
    { id: 'D4', name: '认知知识', score: 9, max: 20, source: '问答表现', isWeak: true },
    { id: 'D5', name: '能力资源', score: 8, max: 20, source: '任务完成', isWeak: true },
    { id: 'D6', name: '社会支持', score: 18, max: 25, source: '互动分析', isWeak: false }
  ],
  
  psychLevelEvidence: [
    { type: 'language', content: "用户多次说'试试看'", weight: 0.3 },
    { type: 'behavior', content: '任务完成率50%，有尝试但不稳定', weight: 0.4 },
    { type: 'emotion', content: '担心但愿意', weight: 0.3 }
  ]
};

const mockPrescription = {
  version: 'v2',
  effectiveDate: '2026-01-25',
  currentPhase: '启动期',
  weekNumber: 2,
  
  targetBehaviors: [
    { id: 'B1', name: '餐后散步', target: '30分钟', frequency: '每日', difficulty: 2, completionRate: 0.8 },
    { id: 'B2', name: '糖代谢知识学习', target: '15分钟', frequency: '每周3次', difficulty: 1, completionRate: 0.6 },
    { id: 'B3', name: '饮食记录', target: '-', frequency: '每日', difficulty: 2, completionRate: 0.3 }
  ],
  
  coreStrategies: ['微习惯培养', '即时正向反馈', '认知教育'],
  weeklyCompletionRate: 0.57
};

const mockAISuggestions = [
  {
    id: 1,
    priority: 'high',
    type: 'address_obstacle',
    icon: '🎯',
    title: '饮食记录连续3天未完成，建议了解原因',
    message: '最近饮食记录好像有些中断，是遇到什么困难了吗？有时候觉得麻烦是很正常的，我们可以一起想想更简单的方式...'
  },
  {
    id: 2,
    priority: 'medium',
    type: 'knowledge_push',
    icon: '📚',
    title: '认知知识得分较低，建议推送教育内容',
    content: { id: 'KC_POSTMEAL_GLUCOSE', title: '餐后血糖为什么重要' }
  },
  {
    id: 3,
    priority: 'low',
    type: 'positive_reinforcement',
    icon: '🌟',
    title: '散步任务完成较好，建议正向强化',
    message: '这周的餐后散步坚持得很棒！身体有没有感觉轻松一些？'
  }
];

// 样式
const styles = {
  container: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    backgroundColor: '#f5f7fa',
    minHeight: '100vh',
    padding: '20px'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    padding: '16px 24px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
  },
  studentInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  avatar: {
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    backgroundColor: '#e6f7ff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '28px'
  },
  studentMeta: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },
  studentName: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1a1a1a'
  },
  studentTags: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center'
  },
  tag: {
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500'
  },
  headerButtons: {
    display: 'flex',
    gap: '12px'
  },
  button: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.2s'
  },
  primaryButton: {
    backgroundColor: '#1890ff',
    color: 'white'
  },
  secondaryButton: {
    backgroundColor: '#f0f0f0',
    color: '#666'
  },
  tabs: {
    display: 'flex',
    gap: '0',
    marginBottom: '20px',
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '4px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
  },
  tab: {
    padding: '10px 20px',
    border: 'none',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    color: '#666',
    borderRadius: '6px',
    transition: 'all 0.2s'
  },
  activeTab: {
    backgroundColor: '#1890ff',
    color: 'white'
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '20px'
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
    paddingBottom: '12px',
    borderBottom: '1px solid #f0f0f0'
  },
  cardTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#1a1a1a',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  cardMeta: {
    fontSize: '12px',
    color: '#999'
  },
  spiCircle: {
    width: '120px',
    height: '120px',
    borderRadius: '50%',
    border: '8px solid #1890ff',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 16px'
  },
  spiScore: {
    fontSize: '36px',
    fontWeight: '700',
    color: '#1890ff'
  },
  spiLabel: {
    fontSize: '12px',
    color: '#666'
  },
  barContainer: {
    marginBottom: '12px'
  },
  barLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '4px',
    fontSize: '13px'
  },
  barTrack: {
    height: '20px',
    backgroundColor: '#f0f0f0',
    borderRadius: '4px',
    overflow: 'hidden',
    position: 'relative'
  },
  barFill: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.3s ease'
  },
  levelBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 16px',
    borderRadius: '20px',
    backgroundColor: '#e6f7ff',
    color: '#1890ff',
    fontWeight: '600',
    fontSize: '14px'
  },
  evidenceList: {
    marginTop: '12px'
  },
  evidenceItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '8px',
    padding: '8px 0',
    borderBottom: '1px solid #f5f5f5',
    fontSize: '13px',
    color: '#666'
  },
  suggestionCard: {
    padding: '16px',
    borderRadius: '8px',
    backgroundColor: '#fafafa',
    marginBottom: '12px',
    border: '1px solid #f0f0f0'
  },
  suggestionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px'
  },
  suggestionTitle: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#1a1a1a'
  },
  suggestionMessage: {
    fontSize: '13px',
    color: '#666',
    backgroundColor: 'white',
    padding: '12px',
    borderRadius: '6px',
    marginTop: '8px',
    borderLeft: '3px solid #1890ff'
  },
  suggestionButtons: {
    display: 'flex',
    gap: '8px',
    marginTop: '12px'
  },
  smallButton: {
    padding: '6px 12px',
    fontSize: '12px',
    borderRadius: '4px',
    border: '1px solid #d9d9d9',
    backgroundColor: 'white',
    cursor: 'pointer'
  },
  infoBox: {
    backgroundColor: '#f6ffed',
    border: '1px solid #b7eb8f',
    borderRadius: '8px',
    padding: '12px 16px',
    marginBottom: '16px'
  },
  warningBox: {
    backgroundColor: '#fff7e6',
    border: '1px solid #ffd591',
    borderRadius: '8px',
    padding: '12px 16px',
    marginBottom: '16px'
  },
  taskList: {
    marginTop: '12px'
  },
  taskItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 0',
    borderBottom: '1px solid #f5f5f5'
  },
  taskInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },
  taskName: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#1a1a1a'
  },
  taskMeta: {
    fontSize: '12px',
    color: '#999'
  },
  miniProgress: {
    width: '100px',
    height: '8px',
    backgroundColor: '#f0f0f0',
    borderRadius: '4px',
    overflow: 'hidden'
  },
  fullWidth: {
    gridColumn: '1 / -1'
  }
};

// 辅助函数
const getRiskColor = (level) => {
  const colors = {
    GREEN: { bg: '#f6ffed', text: '#52c41a' },
    YELLOW: { bg: '#fffbe6', text: '#faad14' },
    ORANGE: { bg: '#fff7e6', text: '#fa8c16' },
    RED: { bg: '#fff1f0', text: '#f5222d' }
  };
  return colors[level] || colors.YELLOW;
};

const getBarColor = (score, max, isWeak) => {
  if (isWeak) return '#fa8c16';
  const ratio = score / max;
  if (ratio >= 0.7) return '#52c41a';
  if (ratio >= 0.5) return '#1890ff';
  return '#faad14';
};

const getDifficultyStars = (level) => {
  return '★'.repeat(level) + '☆'.repeat(5 - level);
};

// 组件
const CoachDashboard = () => {
  const [activeTab, setActiveTab] = useState('diagnosis');
  
  const riskColor = getRiskColor(mockStudent.riskLevel);
  
  return (
    <div style={styles.container}>
      {/* 头部 */}
      <div style={styles.header}>
        <div style={styles.studentInfo}>
          <div style={styles.avatar}>{mockStudent.avatar}</div>
          <div style={styles.studentMeta}>
            <div style={styles.studentName}>
              学员档案: {mockStudent.name} ({mockStudent.gender}, {mockStudent.age}岁)
            </div>
            <div style={styles.studentTags}>
              <span style={{...styles.tag, backgroundColor: riskColor.bg, color: riskColor.text}}>
                ● {mockStudent.stageName}
              </span>
              <span style={{...styles.tag, backgroundColor: '#f0f0f0', color: '#666'}}>
                入组 {mockStudent.daysEnrolled} 天
              </span>
              <span style={{...styles.tag, backgroundColor: '#f0f0f0', color: '#666'}}>
                最近活跃: {mockStudent.lastActive}
              </span>
            </div>
          </div>
        </div>
        <div style={styles.headerButtons}>
          <button style={{...styles.button, ...styles.secondaryButton}}>导出报告</button>
          <button style={{...styles.button, ...styles.secondaryButton}}>编辑</button>
          <button style={{...styles.button, ...styles.primaryButton}}>发消息</button>
        </div>
      </div>
      
      {/* 标签页 */}
      <div style={styles.tabs}>
        {['基本信息', '诊断评估', '行为处方', '执行记录', '沟通历史'].map((tab, idx) => {
          const tabKey = ['info', 'diagnosis', 'prescription', 'execution', 'history'][idx];
          return (
            <button
              key={tabKey}
              style={{
                ...styles.tab,
                ...(activeTab === tabKey ? styles.activeTab : {})
              }}
              onClick={() => setActiveTab(tabKey)}
            >
              {tab}
            </button>
          );
        })}
      </div>
      
      {/* 诊断评估内容 */}
      {activeTab === 'diagnosis' && (
        <div style={styles.grid}>
          {/* 第一层：问题-困难-目的 */}
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <div style={styles.cardTitle}>
                <span>📋</span> 第一层：行为诊断
              </div>
              <div style={styles.cardMeta}>
                置信度: {Math.round(mockDiagnosis.confidence * 100)}% | 更新: {mockDiagnosis.updatedAt}
              </div>
            </div>
            
            <div style={styles.infoBox}>
              <div style={{fontWeight: '600', marginBottom: '8px', color: '#389e0d'}}>问题-困难-目的</div>
              <div style={{fontSize: '13px', lineHeight: 1.8}}>
                <div><strong>表层问题:</strong> {mockDiagnosis.problemDifficultyPurpose.surfaceProblem}</div>
                <div><strong>中层困难:</strong> {mockDiagnosis.problemDifficultyPurpose.behaviorDifficulty.join('、')}</div>
                <div><strong>深层目的:</strong> {mockDiagnosis.problemDifficultyPurpose.deepPurpose}</div>
              </div>
            </div>
            
            <div style={{fontWeight: '600', marginBottom: '12px', fontSize: '14px'}}>六类原因评分</div>
            {mockDiagnosis.sixReasons.map(reason => (
              <div key={reason.id} style={styles.barContainer}>
                <div style={styles.barLabel}>
                  <span>
                    {reason.name} {reason.isWeak && <span style={{color: '#fa8c16'}}>⚠️</span>}
                  </span>
                  <span>{reason.score}/{reason.max}</span>
                </div>
                <div style={styles.barTrack}>
                  <div style={{
                    ...styles.barFill,
                    width: `${(reason.score / reason.max) * 100}%`,
                    backgroundColor: getBarColor(reason.score, reason.max, reason.isWeak)
                  }} />
                </div>
                <div style={{fontSize: '11px', color: '#999', marginTop: '2px'}}>
                  来源: {reason.source}
                </div>
              </div>
            ))}
            
            <div style={{marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #f0f0f0'}}>
              <div style={{fontWeight: '600', marginBottom: '8px', fontSize: '14px'}}>心理层次</div>
              <div style={styles.levelBadge}>
                {mockDiagnosis.psychLevel} {mockDiagnosis.psychLevelName}
              </div>
              <div style={{fontSize: '13px', color: '#666', marginTop: '8px'}}>
                核心心理: "改变可能是必要的，但我想可控地去做"
              </div>
              <div style={styles.evidenceList}>
                {mockDiagnosis.psychLevelEvidence.map((ev, idx) => (
                  <div key={idx} style={styles.evidenceItem}>
                    <span style={{color: '#1890ff'}}>•</span>
                    <span>{ev.content}</span>
                    <span style={{color: '#999', marginLeft: 'auto'}}>权重 {ev.weight}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* 第二层：SPI评估 */}
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <div style={styles.cardTitle}>
                <span>📊</span> 第二层：SPI评估
              </div>
              <div style={styles.cardMeta}>
                评估日期: {mockDiagnosis.updatedAt}
              </div>
            </div>
            
            <div style={styles.spiCircle}>
              <div style={styles.spiScore}>{mockDiagnosis.spiScore}</div>
              <div style={styles.spiLabel}>{mockDiagnosis.spiInterpretation}</div>
            </div>
            
            <div style={{textAlign: 'center', marginBottom: '20px'}}>
              <div style={{fontSize: '14px', color: '#666'}}>预测成功率</div>
              <div style={{fontSize: '24px', fontWeight: '600', color: '#1890ff'}}>{mockDiagnosis.successRate}</div>
            </div>
            
            <div style={{backgroundColor: '#fafafa', borderRadius: '8px', padding: '16px', fontSize: '13px'}}>
              <div style={{fontWeight: '600', marginBottom: '8px'}}>计算公式</div>
              <div style={{fontFamily: 'monospace', color: '#666'}}>
                SPI = (77/125) × 0.6 × (22/30) × 100
              </div>
              <div style={{fontFamily: 'monospace', color: '#666'}}>
                = 0.616 × 0.6 × 0.733 × 100 ≈ 52
              </div>
            </div>
            
            <div style={{marginTop: '16px'}}>
              <div style={{fontWeight: '600', marginBottom: '8px', fontSize: '14px'}}>干预强度建议</div>
              <div style={{...styles.warningBox, marginBottom: 0}}>
                <div style={{fontWeight: '500', color: '#d48806'}}>中等强度支持性干预</div>
                <div style={{fontSize: '13px', color: '#666', marginTop: '4px'}}>
                  • 接触频率: 每2周1次深度访谈<br/>
                  • 日常支持: 每日打卡 + AI陪伴消息<br/>
                  • 重点方向: 先强化认知教育，提升能力资源
                </div>
              </div>
            </div>
          </div>
          
          {/* 当前处方 */}
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <div style={styles.cardTitle}>
                <span>💊</span> 第四层：当前处方
              </div>
              <div style={styles.cardMeta}>
                版本 {mockPrescription.version} | 生效: {mockPrescription.effectiveDate}
              </div>
            </div>
            
            <div style={{display: 'flex', gap: '16px', marginBottom: '16px'}}>
              <div style={{...styles.tag, backgroundColor: '#e6f7ff', color: '#1890ff', padding: '6px 12px'}}>
                {mockPrescription.currentPhase} (第{mockPrescription.weekNumber}周)
              </div>
              <div style={{fontSize: '14px', color: '#666'}}>
                本周完成率: <strong style={{color: mockPrescription.weeklyCompletionRate >= 0.6 ? '#52c41a' : '#fa8c16'}}>
                  {Math.round(mockPrescription.weeklyCompletionRate * 100)}%
                </strong>
              </div>
            </div>
            
            <div style={{fontWeight: '600', marginBottom: '8px', fontSize: '14px'}}>目标行为</div>
            <div style={styles.taskList}>
              {mockPrescription.targetBehaviors.map(task => (
                <div key={task.id} style={styles.taskItem}>
                  <div style={styles.taskInfo}>
                    <div style={styles.taskName}>
                      {task.name} {task.target}
                      <span style={{fontSize: '12px', color: '#999', marginLeft: '8px'}}>
                        {getDifficultyStars(task.difficulty)}
                      </span>
                    </div>
                    <div style={styles.taskMeta}>{task.frequency}</div>
                  </div>
                  <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                    <div style={styles.miniProgress}>
                      <div style={{
                        height: '100%',
                        width: `${task.completionRate * 100}%`,
                        backgroundColor: task.completionRate >= 0.6 ? '#52c41a' : task.completionRate >= 0.4 ? '#faad14' : '#fa8c16',
                        borderRadius: '4px'
                      }} />
                    </div>
                    <span style={{
                      fontSize: '14px',
                      fontWeight: '600',
                      color: task.completionRate >= 0.6 ? '#52c41a' : task.completionRate >= 0.4 ? '#faad14' : '#fa8c16'
                    }}>
                      {Math.round(task.completionRate * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
            
            <div style={{marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #f0f0f0'}}>
              <div style={{fontWeight: '600', marginBottom: '8px', fontSize: '14px'}}>干预策略</div>
              <div style={{display: 'flex', flexWrap: 'wrap', gap: '8px'}}>
                {mockPrescription.coreStrategies.map((strategy, idx) => (
                  <span key={idx} style={{...styles.tag, backgroundColor: '#f0f0f0', color: '#666', padding: '4px 10px'}}>
                    {strategy}
                  </span>
                ))}
              </div>
            </div>
            
            <div style={{marginTop: '16px', display: 'flex', gap: '8px'}}>
              <button style={{...styles.button, ...styles.primaryButton, flex: 1}}>编辑处方</button>
              <button style={{...styles.button, ...styles.secondaryButton, flex: 1}}>生成新版</button>
            </div>
          </div>
          
          {/* AI跟进建议 */}
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <div style={styles.cardTitle}>
                <span>🤖</span> AI跟进建议
              </div>
              <div style={{display: 'flex', gap: '8px'}}>
                <button style={{...styles.smallButton, border: 'none', color: '#1890ff'}}>刷新</button>
              </div>
            </div>
            
            <div style={{fontSize: '13px', color: '#666', marginBottom: '16px'}}>
              基于最近3天数据分析，建议今日跟进:
            </div>
            
            {mockAISuggestions.map(suggestion => (
              <div key={suggestion.id} style={styles.suggestionCard}>
                <div style={styles.suggestionHeader}>
                  <span style={{fontSize: '18px'}}>{suggestion.icon}</span>
                  <span style={styles.suggestionTitle}>{suggestion.title}</span>
                </div>
                
                {suggestion.message && (
                  <div style={styles.suggestionMessage}>
                    "{suggestion.message}"
                  </div>
                )}
                
                {suggestion.content && (
                  <div style={{
                    marginTop: '8px',
                    padding: '8px 12px',
                    backgroundColor: 'white',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <span>📄</span>
                    <span style={{fontSize: '13px'}}>{suggestion.content.title}</span>
                  </div>
                )}
                
                <div style={styles.suggestionButtons}>
                  <button style={{...styles.smallButton, backgroundColor: '#1890ff', color: 'white', border: 'none'}}>
                    {suggestion.type === 'knowledge_push' ? '推送卡片' : '使用此话术'}
                  </button>
                  <button style={styles.smallButton}>
                    {suggestion.type === 'knowledge_push' ? '选择其他' : '修改'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* 其他标签页占位 */}
      {activeTab !== 'diagnosis' && (
        <div style={{...styles.card, textAlign: 'center', padding: '60px 20px'}}>
          <div style={{fontSize: '48px', marginBottom: '16px'}}>🚧</div>
          <div style={{fontSize: '18px', fontWeight: '600', color: '#666'}}>
            {activeTab === 'info' && '基本信息页面'}
            {activeTab === 'prescription' && '行为处方详情页面'}
            {activeTab === 'execution' && '执行记录页面'}
            {activeTab === 'history' && '沟通历史页面'}
          </div>
          <div style={{fontSize: '14px', color: '#999', marginTop: '8px'}}>
            开发中...
          </div>
        </div>
      )}
    </div>
  );
};

export default CoachDashboard;
