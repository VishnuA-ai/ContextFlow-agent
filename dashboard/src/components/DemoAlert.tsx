import React from 'react';
import { Settings, AlertTriangle, Search, RefreshCw, CheckCircle } from 'lucide-react';

/**
 * DemoAlert Component
 * 
 * Displays a 5-stage demo flow that tells the story of ContextFlow:
 * 1. Setup - Creating agents
 * 2. Divergence - Shows the PROBLEM (agents have different information)
 * 3. Detecting - ContextFlow detects the drift
 * 4. Syncing - Auto-syncing in progress
 * 5. Resolved - Shows the SOLUTION (consensus achieved)
 * 
 * Each stage is visually distinct with appropriate colors, icons, and animations.
 */

interface DemoAlertProps {
  stage: 'setup' | 'divergence' | 'detecting' | 'syncing' | 'resolved';
  agents?: { name: string; value: string | number }[];
}

export const DemoAlert = ({ stage, agents }: DemoAlertProps) => {
  const stageConfig = {
    setup: {
      icon: Settings,
      emoji: '⚙️',
      title: 'Setting Up Demo',
      message: 'Creating Scout and Critic agents...',
      color: 'blue',
      bgColor: 'bg-blue-500/20',
      borderColor: 'border-blue-500/50',
      textColor: 'text-blue-300',
      animation: 'animate-pulse',
    },
    divergence: {
      icon: AlertTriangle,
      emoji: '⚠️',
      title: '🚨 DIVERGENCE DETECTED',
      message: 'Scout and Critic have different information!',
      color: 'red',
      bgColor: 'bg-red-500/20',
      borderColor: 'border-red-500/50',
      textColor: 'text-red-300',
      animation: 'animate-pulse',
      animationDuration: 'duration-500',
    },
    detecting: {
      icon: Search,
      emoji: '🔍',
      title: 'Detecting Context Drift',
      message: 'Running Dynamic Consensus Protocol...',
      progress: 'Analyzing agent states...',
      color: 'yellow',
      bgColor: 'bg-yellow-500/20',
      borderColor: 'border-yellow-500/50',
      textColor: 'text-yellow-300',
      animation: 'animate-pulse',
    },
    syncing: {
      icon: RefreshCw,
      emoji: '🔄',
      title: 'Auto-Syncing Agents',
      message: 'Resolving divergence...',
      progress: 'Merging state vectors...',
      color: 'purple',
      bgColor: 'bg-purple-500/20',
      borderColor: 'border-purple-500/50',
      textColor: 'text-purple-300',
      animation: 'animate-spin',
    },
    resolved: {
      icon: CheckCircle,
      emoji: '✅',
      title: 'CONSENSUS REACHED',
      message: 'Agents now aligned and ready to work together!',
      color: 'green',
      bgColor: 'bg-green-500/20',
      borderColor: 'border-green-500/50',
      textColor: 'text-green-300',
      animation: 'animate-bounce',
    },
  };

  const config = stageConfig[stage];
  const Icon = config.icon;

  const renderDivergenceDetails = () => (
    <div className="mt-4 p-4 bg-black/30 rounded-lg border border-red-500/30 font-mono text-sm">
      <div className="space-y-2">
        <div className="text-red-400">
          <span className="text-gray-400">Scout says:</span> "Paper citations = 145"
        </div>
        <div className="text-red-400">
          <span className="text-gray-400">Critic says:</span> "Paper citations = 156"
        </div>
        <div className="text-red-300 font-bold">
          Divergence: 9.5%
        </div>
        <div className="text-red-500 font-bold text-lg">
          Status: CRITICAL ❌
        </div>
      </div>
    </div>
  );

  const renderResolvedDetails = () => (
    <div className="mt-4 p-4 bg-black/30 rounded-lg border border-green-500/30 font-mono text-sm">
      <div className="space-y-2">
        <div className="text-green-400">
          <span className="text-gray-400">Both agree:</span> "Paper citations = 150 (average)"
        </div>
        <div className="text-green-300 font-bold">
          Divergence: 0%
        </div>
        <div className="text-green-400 font-bold text-lg">
          Status: GREEN ✅
        </div>
        <div className="text-green-300 font-bold">
          Hallucination Prevention: 100%
        </div>
      </div>
    </div>
  );

  const renderProgressBar = () => (
    <div className="mt-4">
      <div className="text-sm mb-2 opacity-75">{config.progress}</div>
      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full bg-gradient-to-r from-purple-500 to-blue-500 ${config.animation}`}
          style={{ width: '100%' }}
        />
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div 
        className={`glass ${config.bgColor} ${config.borderColor} border-2 rounded-2xl p-8 max-w-lg w-full mx-4 ${config.animation} ${config.animationDuration || ''}`}
      >
        <div className="flex flex-col items-center text-center">
          {/* Icon */}
          <div className={`mb-4 p-4 rounded-full ${config.bgColor} ${config.borderColor} border`}>
            <Icon size={48} className={config.textColor} />
          </div>

          {/* Title */}
          <h2 className={`text-2xl font-bold mb-2 ${config.textColor}`}>
            {config.title}
          </h2>

          {/* Message */}
          <p className={`text-lg mb-4 ${config.textColor} opacity-90`}>
            {config.message}
          </p>

          {/* Stage-specific content */}
          {stage === 'divergence' && renderDivergenceDetails()}
          {stage === 'resolved' && renderResolvedDetails()}
          {(stage === 'detecting' || stage === 'syncing') && renderProgressBar()}

          {/* Stage indicator */}
          <div className="mt-6 flex gap-2">
            {['setup', 'divergence', 'detecting', 'syncing', 'resolved'].map((s, index) => (
              <div
                key={s}
                className={`h-2 rounded-full transition-all ${
                  s === stage 
                    ? 'w-8 bg-current' 
                    : ['setup', 'divergence', 'detecting', 'syncing', 'resolved'].indexOf(stage) > index
                    ? 'w-2 bg-current opacity-50'
                    : 'w-2 bg-gray-600'
                } ${config.textColor}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DemoAlert;
