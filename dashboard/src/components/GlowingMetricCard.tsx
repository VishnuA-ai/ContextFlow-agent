import React, { useState, useEffect } from 'react';

interface GlowingMetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  status: 'green' | 'yellow' | 'red' | 'blue';
  animated?: boolean;
}

export const GlowingMetricCard = ({
  title,
  value,
  icon,
  status,
  animated = true
}: GlowingMetricCardProps) => {
  const [isGlowing, setIsGlowing] = useState(false);

  useEffect(() => {
    if (animated) {
      const interval = setInterval(() => {
        setIsGlowing(prev => !prev);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [animated]);

  const getGlowColor = () => {
    switch (status) {
      case 'green': return 'from-green-500 to-emerald-500';
      case 'yellow': return 'from-yellow-500 to-amber-500';
      case 'red': return 'from-red-500 to-pink-500';
      case 'blue': return 'from-blue-500 to-cyan-500';
      default: return 'from-purple-500 to-blue-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'green': return 'text-green-400';
      case 'yellow': return 'text-yellow-400';
      case 'red': return 'text-red-400';
      case 'blue': return 'text-blue-400';
      default: return 'text-purple-400';
    }
  };

  const getShadowColor = () => {
    switch (status) {
      case 'green': return 'shadow-green-500/50';
      case 'yellow': return 'shadow-yellow-500/50';
      case 'red': return 'shadow-red-500/50';
      case 'blue': return 'shadow-blue-500/50';
      default: return 'shadow-purple-500/50';
    }
  };

  const getBorderColor = () => {
    switch (status) {
      case 'green': return 'border-green-400/50';
      case 'yellow': return 'border-yellow-400/50';
      case 'red': return 'border-red-400/50';
      case 'blue': return 'border-blue-400/50';
      default: return 'border-purple-400/50';
    }
  };

  return (
    <div className={`
      relative rounded-2xl backdrop-blur-xl
      border-2 border-white/10
      p-6 overflow-hidden
      transition-all duration-500
      ${isGlowing ? `
        shadow-2xl
        ${getShadowColor()}
        ${getBorderColor()}
      ` : 'shadow-lg'}
    `}>
      {/* Glowing background effect */}
      <div className={`
        absolute inset-0 bg-gradient-to-br ${getGlowColor()}
        opacity-0 transition-opacity duration-500
        ${isGlowing ? 'opacity-10' : 'opacity-0'}
        blur-2xl
      `}></div>

      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white/60 text-sm font-medium">{title}</p>
            <p className={`text-4xl font-bold mt-2 ${getStatusText()}`}>
              {value}
            </p>
          </div>
          <div className="text-4xl">{icon}</div>
        </div>
      </div>

      {/* Animated border */}
      <div className={`
        absolute inset-0 rounded-2xl
        bg-gradient-to-r ${getGlowColor()}
        opacity-0 group-hover:opacity-20
        transition-opacity duration-500
        pointer-events-none
      `}></div>
    </div>
  );
};
