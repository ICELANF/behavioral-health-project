import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { TraceNode, TraceLink } from '../../../types/react-types';

interface TraceGraphProps {
  nodes: TraceNode[];
  links: TraceLink[];
}

const getNodeColor = (type: TraceNode['type']) => {
  switch (type) {
    case 'INPUT':
      return '#3b82f6';
    case 'RULE':
      return '#8b5cf6';
    case 'DECISION':
      return '#f59e0b';
    case 'OUTPUT':
      return '#10b981';
    default:
      return '#64748b';
  }
};

const getNodeSize = (type: TraceNode['type']) => {
  switch (type) {
    case 'INPUT':
    case 'OUTPUT':
      return 80;
    case 'DECISION':
      return 90;
    case 'RULE':
      return 70;
    default:
      return 60;
  }
};

export const TraceGraph: React.FC<TraceGraphProps> = ({ nodes, links }) => {
  const option = useMemo(() => {
    const graphNodes = nodes.map(node => ({
      id: node.id,
      name: node.label,
      value: node.value,
      category: node.type,
      symbolSize: getNodeSize(node.type),
      itemStyle: {
        color: getNodeColor(node.type),
      },
      label: {
        show: true,
        fontSize: 12,
        fontWeight: 'bold',
      },
    }));

    const graphLinks = links.map(link => ({
      source: link.source,
      target: link.target,
      lineStyle: {
        width: Math.max(1, link.weight * 3),
        curveness: 0.2,
      },
    }));

    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            return `
              <div style="padding: 8px;">
                <div style="font-weight: bold; margin-bottom: 4px;">${params.data.name}</div>
                <div style="color: #64748b; font-size: 12px;">类型: ${params.data.category}</div>
                <div style="color: #64748b; font-size: 12px; margin-top: 4px;">值: ${params.data.value}</div>
              </div>
            `;
          }
          return '';
        },
      },
      legend: [
        {
          data: ['INPUT', 'RULE', 'DECISION', 'OUTPUT'],
          top: 20,
          right: 20,
          orient: 'vertical',
          textStyle: {
            fontSize: 12,
          },
        },
      ],
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: graphNodes,
          links: graphLinks,
          categories: [
            { name: 'INPUT', itemStyle: { color: getNodeColor('INPUT') } },
            { name: 'RULE', itemStyle: { color: getNodeColor('RULE') } },
            { name: 'DECISION', itemStyle: { color: getNodeColor('DECISION') } },
            { name: 'OUTPUT', itemStyle: { color: getNodeColor('OUTPUT') } },
          ],
          roam: true,
          draggable: true,
          force: {
            repulsion: 1000,
            edgeLength: [150, 250],
            gravity: 0.1,
          },
          emphasis: {
            focus: 'adjacency',
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
            },
            lineStyle: {
              width: 5,
            },
          },
          lineStyle: {
            color: 'source',
            curveness: 0.2,
            opacity: 0.6,
          },
        },
      ],
    };
  }, [nodes, links]);

  return (
    <ReactECharts
      option={option}
      style={{ height: '600px', width: '100%' }}
      opts={{ renderer: 'canvas' }}
    />
  );
};
