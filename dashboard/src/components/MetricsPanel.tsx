import { Activity, Database, AlertTriangle, Wifi } from 'lucide-react';
import { GlowingMetricCard } from './GlowingMetricCard';
import type { Metrics } from '../types';

interface MetricsPanelProps {
  metrics: Metrics | null;
}

export function MetricsPanel({ metrics }: MetricsPanelProps) {
  if (!metrics) {
    return (
      <div className="glass p-6 rounded-lg">
        <p className="text-gray-400 text-center">Loading metrics...</p>
      </div>
    );
  }

  const metricCards = [
    {
      label: 'Agents Tracked',
      value: metrics.agents_tracked,
      icon: <Activity size={24} />,
      status: 'blue' as const,
    },
    {
      label: 'Journal Entries',
      value: metrics.journal_entries,
      icon: <Database size={24} />,
      status: 'green' as const,
    },
    {
      label: 'Critical Events',
      value: metrics.critical_events,
      icon: <AlertTriangle size={24} />,
      status: 'red' as const,
    },
    {
      label: 'Active Connections',
      value: metrics.active_connections,
      icon: <Wifi size={24} />,
      status: 'blue' as const,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {metricCards.map((card) => (
        <GlowingMetricCard
          key={card.label}
          title={card.label}
          value={card.value}
          icon={card.icon}
          status={card.status}
          animated={true}
        />
      ))}
      <div className="col-span-2 md:col-span-4 glass p-4 rounded-lg border border-gray-700/50 glow-green animate-fade-in">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-300">Hallucination Prevention Rate</span>
          <span className="text-lg font-bold text-green-400">{metrics.hallucination_prevention_rate}</span>
        </div>
      </div>
    </div>
  );
}
