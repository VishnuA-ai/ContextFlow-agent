import { Activity, Database, AlertTriangle, Wifi } from 'lucide-react';
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
      icon: Activity,
      color: 'text-blue-400',
      glow: 'glow-blue',
    },
    {
      label: 'Journal Entries',
      value: metrics.journal_entries,
      icon: Database,
      color: 'text-green-400',
      glow: 'glow-green',
    },
    {
      label: 'Critical Events',
      value: metrics.critical_events,
      icon: AlertTriangle,
      color: 'text-red-400',
      glow: 'glow-red',
    },
    {
      label: 'Active Connections',
      value: metrics.active_connections,
      icon: Wifi,
      color: 'text-purple-400',
      glow: 'glow-purple',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {metricCards.map((card) => (
        <div key={card.label} className={`glass p-4 rounded-lg border border-gray-700/50 ${card.glow} animate-fade-in`}>
          <div className="flex items-center gap-2 mb-2">
            <card.icon size={18} className={card.color} />
            <span className="text-xs text-gray-400">{card.label}</span>
          </div>
          <div className="text-2xl font-bold text-white">{card.value}</div>
        </div>
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
