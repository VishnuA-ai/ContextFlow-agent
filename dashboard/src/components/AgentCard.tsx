import { useState } from 'react';
import { Cpu, Clock, Hash, Zap } from 'lucide-react';
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

  const borderColor =
    isSelected ? 'border-primary-500' :
    consensusLevel === 'aligned' ? 'border-green-500/40' :
    consensusLevel === 'minor_drift' ? 'border-yellow-500/40' :
    consensusLevel === 'critical' ? 'border-red-500/40' :
    'border-gray-700/50';

  const glowClass =
    isSelected ? 'glow-blue' :
    consensusLevel === 'aligned' ? 'glow-green' :
    consensusLevel === 'minor_drift' ? 'glow-yellow' :
    consensusLevel === 'critical' ? 'glow-red' : '';

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        group relative glass p-4 rounded-xl border-2 cursor-pointer
        transition-all duration-300 animate-fade-in
        ${borderColor} ${glowClass}
        ${isHovered && !isSelected ? 'scale-[1.03]' : ''}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Cpu size={18} className="text-primary-400 flex-shrink-0" />
          <h3 className="font-semibold text-white truncate">{agent.id}</h3>
          {agent.using_strands && (
            <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
              <Zap size={10} />
              Strands
            </span>
          )}
        </div>
        {consensusLevel !== undefined && divergence !== undefined && (
          <ConsensusBadge level={consensusLevel} divergence={divergence} />
        )}
      </div>

      {/* Task */}
      <p className="text-sm text-gray-300 mb-3 line-clamp-2 leading-relaxed">{agent.task}</p>

      {/* Hash + time */}
      <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
        <div className="flex items-center gap-1">
          <Hash size={11} />
          <span className="font-mono">{agent.state_hash.slice(0, 8)}...</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock size={11} />
          <span>{new Date(agent.timestamp * 1000).toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="pt-3 border-t border-gray-700/50">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-gray-400">Confidence</span>
          <span className="text-xs font-semibold text-white">{(agent.confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full h-1.5 bg-gray-700/60 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-full transition-all duration-700"
            style={{ width: `${agent.confidence * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
