import { useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import type { ConsensusUpdate } from '../types';

interface DivergenceChartProps {
  updates: ConsensusUpdate[];
}

export function DivergenceChart({ updates }: DivergenceChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  // Prepare data for plotting
  const timestamps = updates.map((u) => new Date(u.timestamp).toLocaleTimeString());
  const agents = new Set(updates.flatMap((u) => u.consensus_with_others.map((c) => c.agent)));
  const agentList = Array.from(agents);

  const traces = agentList.map((agent) => ({
    x: timestamps,
    y: updates.map((u) => {
      const consensus = u.consensus_with_others.find((c) => c.agent === agent);
      return consensus ? consensus.divergence * 100 : 0;
    }),
    type: 'scatter' as const,
    mode: 'lines+markers' as const,
    name: agent,
    line: { width: 2, color: '#38bdf8' },
    marker: { color: '#38bdf8', size: 6 },
  }));

  return (
    <div ref={chartRef} className="w-full h-64">
      <Plot
        data={traces}
        layout={{
          title: {
            text: 'Divergence Score Over Time',
            font: { color: '#f8fafc', size: 16 }
          },
          xaxis: { 
            title: { text: 'Time', font: { color: '#cbd5e1' } },
            tickfont: { color: '#cbd5e1' },
            gridcolor: '#334155'
          },
          yaxis: { 
            title: { text: 'Divergence (%)', font: { color: '#cbd5e1' } },
            range: [0, 100],
            tickfont: { color: '#cbd5e1' },
            gridcolor: '#334155'
          },
          margin: { t: 40, r: 20, b: 40, l: 50 },
          showlegend: true,
          legend: { 
            x: 0, 
            y: 1,
            font: { color: '#cbd5e1' },
            bgcolor: 'rgba(30, 41, 59, 0.8)',
            bordercolor: '#334155'
          },
          hovermode: 'closest',
          paper_bgcolor: 'rgba(15, 23, 42, 0.5)',
          plot_bgcolor: 'rgba(15, 23, 42, 0.3)',
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}
