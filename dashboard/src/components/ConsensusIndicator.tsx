import React from 'react';

interface ConsensusIndicatorProps {
  level: 'green' | 'yellow' | 'red';
  divergenceScore: number;
  animated?: boolean;
}

export const ConsensusIndicator = ({
  level,
  divergenceScore,
  animated = true
}: ConsensusIndicatorProps) => {
  const getColors = () => {
    switch (level) {
      case 'green':
        return {
          outer: 'from-green-500 to-emerald-500',
          glow: 'shadow-green-500/50',
          text: 'text-green-400',
          label: 'ALIGNED ✅'
        };
      case 'yellow':
        return {
          outer: 'from-yellow-500 to-amber-500',
          glow: 'shadow-yellow-500/50',
          text: 'text-yellow-400',
          label: 'CAUTION ⚠️'
        };
      case 'red':
        return {
          outer: 'from-red-500 to-pink-500',
          glow: 'shadow-red-500/50',
          text: 'text-red-400',
          label: 'CRITICAL 🛑'
        };
    }
  };

  const colors = getColors();

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Circular indicator */}
      <div className="relative">
        {/* Outer ring (animated) */}
        <div className={`
          absolute inset-0 rounded-full
          bg-gradient-to-br ${colors.outer}
          animate-spin
          opacity-30
          blur-lg
          ${!animated && 'animate-none'}
        `}
        style={{
          animationDuration: '3s',
          width: '140px',
          height: '140px',
          left: '-20px',
          top: '-20px'
        }}></div>

        {/* Main circle */}
        <div className={`
          relative w-24 h-24 rounded-full
          bg-gradient-to-br ${colors.outer}
          flex items-center justify-center
          shadow-2xl ${colors.glow}
          backdrop-blur-xl
          border-4 border-white/20
        `}>
          {/* Inner content */}
          <div className="text-center">
            <div className={`text-4xl font-bold ${colors.text}`}>
              {Math.round((1 - divergenceScore) * 100)}%
            </div>
            <div className="text-xs text-white/60 mt-1">Consensus</div>
          </div>
        </div>
      </div>

      {/* Status text */}
      <div className={`text-lg font-bold ${colors.text}`}>
        {colors.label}
      </div>

      {/* Divergence detail */}
      <div className="text-sm text-white/60">
        Divergence: {(divergenceScore * 100).toFixed(1)}%
      </div>
    </div>
  );
};
