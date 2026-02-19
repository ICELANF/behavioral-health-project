import React from 'react';
import ReactECharts from 'echarts-for-react';

interface CGMDataPoint {
  time: string;
  glucose: number;
}

interface CGMChartProps {
  data?: CGMDataPoint[];
}

export const CGMChart: React.FC<CGMChartProps> = ({ data }) => {
  const cgmData = data || [];

  const option = {
    backgroundColor: 'transparent',
    title: {
      text: '连续血糖监测 (CGM)',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#f1f5f9',
      },
      left: 10,
      top: 10,
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const param = params[0];
        return `${param.name}<br/>血糖: ${param.value} mg/dL`;
      },
    },
    grid: {
      left: 50,
      right: 20,
      top: 50,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      data: cgmData.map((d) => d.time),
      axisLabel: {
        rotate: 45,
        fontSize: 10,
        interval: 5,
        color: '#cbd5e1',
      },
      axisLine: {
        lineStyle: {
          color: '#94a3b8',
        },
      },
    },
    yAxis: {
      type: 'value',
      name: 'mg/dL',
      nameTextStyle: {
        color: '#cbd5e1',
      },
      min: 60,
      max: 250,
      axisLabel: {
        color: '#cbd5e1',
      },
      splitLine: {
        lineStyle: {
          color: '#64748b',
          type: 'dashed',
        },
      },
      axisLine: {
        lineStyle: {
          color: '#94a3b8',
        },
      },
    },
    series: [
      {
        name: '血糖',
        type: 'line',
        data: cgmData.map((d) => d.glucose),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 3,
          color: '#f59e0b',
        },
        itemStyle: {
          color: '#f59e0b',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(245, 158, 11, 0.4)' },
              { offset: 1, color: 'rgba(245, 158, 11, 0.05)' },
            ],
          },
        },
        markLine: {
          silent: true,
          lineStyle: {
            color: '#ef4444',
            type: 'dashed',
            width: 2,
          },
          label: {
            color: '#fca5a5',
            fontSize: 10,
          },
          data: [
            { yAxis: 180, label: { formatter: '高血糖线', position: 'end' } },
            { yAxis: 70, label: { formatter: '低血糖线', position: 'end' } },
          ],
        },
      },
    ],
  };

  return (
    <div className="bg-slate-700/40 backdrop-blur-sm rounded-xl border border-slate-400/60 p-4 shadow-lg">
      <ReactECharts option={option} style={{ height: '280px', width: '100%' }} />
      <div className="mt-3 flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-amber-500"></span>
            <span className="text-slate-100">血糖曲线</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 border-t-2 border-dashed border-red-500"></span>
            <span className="text-slate-100">安全阈值</span>
          </span>
        </div>
        <span className="font-mono font-bold text-amber-300">CV: 42%</span>
      </div>
    </div>
  );
};
