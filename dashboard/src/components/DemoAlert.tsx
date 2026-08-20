import { Settings, AlertTriangle, Search, RefreshCw, CheckCircle } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface DemoAlertProps {
  stage: 'setup' | 'divergence' | 'detecting' | 'syncing' | 'resolved';
}

interface StageConfig {
  icon: LucideIcon;
  title: string;
  message: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  animation: string;
  animationDuration?: string;
  progress?: string;
  details?: string[];
}

export const DemoAlert = ({ stage }: DemoAlertProps) => {
  const stageConfig: Record<string, StageConfig> = {
    setup: {
      icon: Settings,
      title: 'Setting Up Demo',
      message: 'Creating Scout and Critic agents...',
      bgColor: 'bg-blue-500/20',
      borderColor: 'border-blue-500/50',
      textColor: 'text-blue-300',
      animation: 'animate-pulse',
    },
    divergence: {
      icon: AlertTriangle,
      title: '🚨 DIVERGENCE DETECTED',
      message: 'Scout and Critic have different information!',
      bgColor: 'bg-red-500/20',
      borderColor: 'border-red-500/50',
      textColor: 'text-red-300',
      animation: 'animate-pulse',
      animationDuration: 'duration-500',
      details: [
        'Scout says: "Paper citations = 145"',
        'Critic says: "Paper citations = 156"',
        'Divergence: 7.1% — CRITICAL ❌',
      ],
    },
    detecting: {
      icon: Search,
      title: 'Detecting Context Drift',
      message: 'Running Dynamic Consensus Protocol...',
      progress: 'Analyzing agent states...',
      bgColor: 'bg-yellow-500/20',
      borderColor: 'border-yellow-500/50',
      textColor: 'text-yellow-300',
      animation: 'animate-pulse',
    },
    syncing: {
      icon: RefreshCw,
      title: 'Auto-Syncing Agents',
      message: 'Resolving divergence...',
      progress: 'Merging state vectors...',
      bgColor: 'bg-purple-500/20',
      borderColor: 'border-purple-500/50',
      textColor: 'text-purple-300',
      animation: 'animate-spin',
    },
    resolved: {
      icon: CheckCircle,
      title: 'CONSENSUS REACHED',
      message: 'Agents now aligned and ready to work together!',
      bgColor: 'bg-green-500/20',
      borderColor: 'border-green-500/50',
      textColor: 'text-green-300',
      animation: 'animate-bounce',
      details: [
        'Both agree: "Paper citations = 150 (average)"',
        'Divergence: 0% — ALIGNED ✅',
        'Hallucination Prevention: 100%',
      ],
    },
  };

  const config = stageConfig[stage];
  const Icon = config.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className={`glass ${config.bgColor} ${config.borderColor} border-2 rounded-2xl p-8 max-w-lg w-full mx-4 ${config.animationDuration ?? ''}`}>
        <div className="flex flex-col items-center text-center">
          <div className={`mb-4 p-4 rounded-full ${config.bgColor} ${config.borderColor} border`}>
            <Icon size={48} className={`${config.textColor} ${config.animation}`} />
          </div>

          <h2 className={`text-2xl font-bold mb-2 ${config.textColor}`}>{config.title}</h2>
          <p className={`text-lg mb-4 ${config.textColor} opacity-90`}>{config.message}</p>

          {config.details && (
            <div className="w-full mt-2 p-4 bg-black/30 rounded-lg border border-white/10 font-mono text-sm space-y-2 text-left">
              {config.details.map((d, i) => (
                <p key={i} className="text-white/70">→ {d}</p>
              ))}
            </div>
          )}

          {config.progress && (
            <div className="w-full mt-4">
              <p className="text-sm mb-2 opacity-75 text-left">{config.progress}</p>
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-purple-500 to-blue-500 animate-pulse w-full rounded-full" />
              </div>
            </div>
          )}

          <div className="mt-6 flex gap-2">
            {['setup', 'divergence', 'detecting', 'syncing', 'resolved'].map((s, idx) => {
              const stageIndex = ['setup', 'divergence', 'detecting', 'syncing', 'resolved'].indexOf(stage);
              return (
                <div
                  key={s}
                  className={`h-2 rounded-full transition-all ${
                    s === stage ? `w-8 ${config.textColor.replace('text-', 'bg-')}` :
                    stageIndex > idx ? `w-2 ${config.textColor.replace('text-', 'bg-')} opacity-50` :
                    'w-2 bg-gray-600'
                  }`}
                />
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DemoAlert;
