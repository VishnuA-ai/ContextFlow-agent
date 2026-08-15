import { Shield, AlertTriangle, XCircle } from 'lucide-react';

interface ConsensusBadgeProps {
  level: 'aligned' | 'minor_drift' | 'critical';
  divergence: number;
}

export function ConsensusBadge({ level, divergence }: ConsensusBadgeProps) {
  const config = {
    aligned: {
      color: 'bg-green-500',
      textColor: 'text-green-400',
      bgColor: 'bg-green-500/20',
      borderColor: 'border-green-500/50',
      icon: Shield,
      label: 'GREEN',
      glow: 'glow-green',
    },
    minor_drift: {
      color: 'bg-yellow-500',
      textColor: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20',
      borderColor: 'border-yellow-500/50',
      icon: AlertTriangle,
      label: 'YELLOW',
      glow: 'glow-yellow',
    },
    critical: {
      color: 'bg-red-500',
      textColor: 'text-red-400',
      bgColor: 'bg-red-500/20',
      borderColor: 'border-red-500/50',
      icon: XCircle,
      label: 'RED',
      glow: 'glow-red',
    },
  };

  const { textColor, bgColor, borderColor, icon: Icon, label, glow } = config[level];
  const isCritical = level === 'critical';

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full glass ${bgColor} ${borderColor} border ${isCritical ? 'animate-pulse-glow' : ''} ${glow}`}>
      <Icon size={16} className={textColor} />
      <span className={`font-semibold text-sm ${textColor}`}>{label}</span>
      <span className={`text-xs opacity-75 ${textColor}`}>({(divergence * 100).toFixed(1)}%)</span>
    </div>
  );
}
