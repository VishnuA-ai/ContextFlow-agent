interface StatusBadgeProps {
  level: 'green' | 'yellow' | 'red';
  animated?: boolean;
}

export const StatusBadge = ({ level, animated = true }: StatusBadgeProps) => {
  const configs = {
    green: { bg: 'bg-green-500/20', border: 'border-green-500/50', text: 'text-green-400' },
    yellow: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', text: 'text-yellow-400' },
    red: { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400' },
  };

  const config = configs[level];

  return (
    <div className={`
      inline-flex items-center gap-2 px-4 py-2 rounded-full border-2
      ${config.bg} ${config.border} ${config.text}
      ${animated ? 'animate-pulse' : ''}
      backdrop-blur-md transition-all duration-300
    `}>
      <div className={`w-2 h-2 rounded-full ${config.bg} animate-pulse`} />
      <span className="font-bold text-sm uppercase tracking-wider">{level} Status</span>
    </div>
  );
};
