import { useState } from 'react';
import { Cpu, Clock, Hash } from 'lucide-react';
import { ConsensusBadge } from './ConsensusBadge';
import type { Agent } from '../types';

interface AgentCardProps {
  agent: Agent;
  consensusLevel?: 'aligned' | 'minor_drift' | 'critical';
  divergence?: number;
  onClick: () => void;
  isSelected: boolean;
}

export function AgentCard({ agent, consensusLevel, divergence, onClick, isSelected }: AgentCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const getGlowColor = () => {
    if (!consensusLevel) return '';
    return consensusLevel === 'aligned' ? 'glow-green' : 
           consensusLevel === 'minor_drift' ? 'glow-yellow' : 'glow-red';
  };

  const getHoverBorderColor = () => {
    if (!consensusLevel) return 'border-blue-400/50';
    return consensusLevel === 'aligned' ? 'border-green-400/50' : 
           consensusLevel === 'minor_drift' ? 'border-yellow-400/50' : 'border-red-400/50';
  };

  const getHoverShadowColor = () => {
    if (!consensusLevel) return 'shadow-blue-500/20';
    return consensusLevel === 'aligned' ? 'shadow-green-500/20' : 
           consensusLevel === 'minor_drift' ? 'shadow-yellow-500/20' : 'shadow-red-500/20';
  };

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        group relative glass p-4 rounded-lg border-2 cursor-pointer
        transition-all duration-300 animate-fade-in
        ${isSelected
          ? 'border-primary-500 glow-blue'
          : `border-gray-700/50 ${getGlowColor()}`
        }
        ${isHovered && !isSelected ? `
          ${getHoverBorderColor()}
          shadow-2xl ${getHoverShadowColor()}
          scale-105
        ` : ''}
      `}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Cpu size={20} className="text-primary-400" />
          <h3 className="font-semibold text-white">{agent.id}</h3>
        </div>
        {consensusLevel && divergence !== undefined && (
          <ConsensusBadge level={consensusLevel} divergence={divergence} />
        )}
      </div>

      <p className="text-sm text-gray-300 mb-3 line-clamp-2">{agent.task}</p>

      <div className="flex items-center gap-4 text-xs text-gray-400">
        <div className="flex items-center gap-1">
          <Hash size={12} />
          <span className="font-mono">{agent.state_hash.slice(0, 8)}...</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock size={12} />
          <span>{new Date(agent.timestamp * 1000).toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-700/50">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">Confidence</span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary-500 to-primary-400 transition-all"
                style={{ width: `${agent.confidence * 100}%` }}
              />
            </div>
            <span className="text-xs font-medium text-white">
              {(agent.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
