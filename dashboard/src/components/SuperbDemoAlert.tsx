import React, { useEffect, useState } from 'react';

interface SuperbDemoAlertProps {
  stage: 'setup' | 'divergence' | 'detecting' | 'syncing' | 'resolved';
  agents?: string[];
}

export const SuperbDemoAlert = ({ stage, agents }: SuperbDemoAlertProps) => {
  const [shake, setShake] = useState(false);

  useEffect(() => {
    if (stage === 'divergence') {
      setShake(true);
      setTimeout(() => setShake(false), 500);
    }
  }, [stage]);

  const getStageConfig = () => {
    const configs = {
      setup: {
        icon: '⚙️',
        title: 'Initializing Strands Agents',
        message: 'Creating Scout, Critic, and Synthesis agents using Strands SDK...',
        colors: 'from-blue-500/20 to-cyan-500/20 border-blue-500/50',
        bgGradient: 'from-blue-500 to-cyan-500',
        accentColor: 'text-blue-400'
      },
      divergence: {
        icon: '⚠️',
        title: '🚨 CRITICAL DIVERGENCE',
        message: 'Strands agents have different information!',
        details: [
          'Scout (Strands): "Paper citations = 145"',
          'Critic (Strands): "Paper citations = 156"',
          'Divergence: 9.5% (CRITICAL)',
          'Status: NEEDS SYNC ❌'
        ],
        colors: 'from-red-500/20 to-pink-500/20 border-red-500/50',
        bgGradient: 'from-red-500 to-pink-500',
        accentColor: 'text-red-400'
      },
      detecting: {
        icon: '🔍',
        title: 'Running ContextFlow Consensus',
        message: 'Analyzing Strands agent states...',
        colors: 'from-yellow-500/20 to-amber-500/20 border-yellow-500/50',
        bgGradient: 'from-yellow-500 to-amber-500',
        accentColor: 'text-yellow-400'
      },
      syncing: {
        icon: '🔄',
        title: 'Auto-Syncing Strands Agents',
        message: 'Merging state vectors using ContextFlow protocol...',
        colors: 'from-purple-500/20 to-indigo-500/20 border-purple-500/50',
        bgGradient: 'from-purple-500 to-indigo-500',
        accentColor: 'text-purple-400'
      },
      resolved: {
        icon: '✅',
        title: 'CONSENSUS ACHIEVED',
        message: 'All Strands agents aligned and ready!',
        details: [
          'Both agree: "Paper citations = 150 (average)"',
          'Divergence: 0%',
          'Status: CONSENSUS ✅',
          'Hallucination Prevention: 100%'
        ],
        colors: 'from-green-500/20 to-emerald-500/20 border-green-500/50',
        bgGradient: 'from-green-500 to-emerald-500',
        accentColor: 'text-green-400'
      }
    };
    return configs[stage];
  };

  const config = getStageConfig();

  return (
    <div className={`
      mb-8 rounded-3xl border-2
      backdrop-blur-xl
      p-8
      relative overflow-hidden
      transition-all duration-500
      ${config.colors}
      ${shake ? 'animate-shake' : ''}
      shadow-2xl
    `}>
      {/* Animated background */}
      <div className={`
        absolute inset-0 bg-gradient-to-r ${config.bgGradient}
        opacity-5 animate-pulse
        blur-2xl
      `}></div>

      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-start gap-6">
          {/* Icon */}
          <div className="text-5xl animate-bounce flex-shrink-0">
            {config.icon}
          </div>

          {/* Text content */}
          <div className="flex-1">
            <h3 className={`text-3xl font-bold ${config.accentColor} mb-2`}>
              {config.title}
            </h3>
            <p className="text-white/80 text-lg mb-4">
              {config.message}
            </p>

            {/* Details */}
            {config.details && (
              <div className="space-y-2 bg-black/30 rounded-xl p-4 backdrop-blur-sm">
                {config.details.map((detail, i) => (
                  <p
                    key={i}
                    className="text-white/70 font-mono text-sm"
                    style={{
                      animation: `slideIn 0.5s ease ${i * 100}ms forwards`,
                      opacity: 0
                    }}
                  >
                    → {detail}
                  </p>
                ))}
              </div>
            )}

            {/* Progress bars */}
            {(stage === 'detecting' || stage === 'syncing') && (
              <div className="mt-6 space-y-3">
                <div className="h-2 bg-black/50 rounded-full overflow-hidden">
                  <div className={`
                    h-full bg-gradient-to-r ${config.bgGradient}
                    animate-pulse w-3/4 rounded-full
                  `}></div>
                </div>
                <p className="text-white/60 text-sm">
                  {stage === 'detecting' ? 'Analyzing states...' : 'Merging data...'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Shine effect */}
      <div className={`
        absolute top-0 -left-full w-full h-full
        bg-gradient-to-r from-transparent via-white/10 to-transparent
        animate-shimmer
      `}></div>
    </div>
  );
};
