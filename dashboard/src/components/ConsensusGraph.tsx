import { useEffect, useRef } from 'react';
import { useDashboardStore } from '../store';
import type { MultiAgentConsensus } from '../types';

interface ConsensusGraphProps {
  multiConsensus: MultiAgentConsensus | null;
}

interface Node {
  id: string;
  x: number;
  y: number;
  pulse: number;
}

interface Edge {
  from: string;
  to: string;
  level: string;
  divergence: number;
}

const LEVEL_COLOR: Record<string, string> = {
  aligned: '#22c55e',
  minor_drift: '#eab308',
  critical: '#ef4444',
};

export function ConsensusGraph({ multiConsensus }: ConsensusGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { agents } = useDashboardStore();
  const nodesRef = useRef<Node[]>([]);
  const animRef = useRef<number>();
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width || 600;
    canvas.height = rect.height || 260;

    const agentIds = Object.keys(agents);
    if (agentIds.length === 0) return;

    // Place nodes in a circle
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const r = Math.min(cx, cy) * 0.6;

    nodesRef.current = agentIds.map((id, i) => {
      const angle = (i / agentIds.length) * 2 * Math.PI - Math.PI / 2;
      return { id, x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r, pulse: Math.random() * Math.PI * 2 };
    });

    // Build edges from multiConsensus
    const edges: Edge[] = [];
    if (multiConsensus?.consensus_graph) {
      for (const [key, val] of Object.entries(multiConsensus.consensus_graph)) {
        const [from, to] = key.split('<->');
        if (from && to) edges.push({ from, to, level: val.level, divergence: val.divergence });
      }
    } else {
      // Fallback: connect all pairs with neutral state
      for (let i = 0; i < agentIds.length; i++) {
        for (let j = i + 1; j < agentIds.length; j++) {
          edges.push({ from: agentIds[i], to: agentIds[j], level: 'aligned', divergence: 0 });
        }
      }
    }

    const draw = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      frameRef.current++;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw edges
      for (const edge of edges) {
        const fromNode = nodesRef.current.find(n => n.id === edge.from);
        const toNode = nodesRef.current.find(n => n.id === edge.to);
        if (!fromNode || !toNode) continue;

        const color = LEVEL_COLOR[edge.level] || '#38bdf8';
        const alpha = edge.level === 'critical'
          ? 0.5 + 0.3 * Math.sin(frameRef.current * 0.05)
          : 0.55;

        // Glow
        ctx.shadowColor = color;
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(toNode.x, toNode.y);
        ctx.strokeStyle = color;
        ctx.globalAlpha = alpha;
        ctx.lineWidth = 2 + edge.divergence * 8;
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;

        // Divergence label on edge midpoint
        if (edge.divergence > 0) {
          const mx = (fromNode.x + toNode.x) / 2;
          const my = (fromNode.y + toNode.y) / 2;
          ctx.font = '11px monospace';
          ctx.fillStyle = color;
          ctx.globalAlpha = 0.9;
          ctx.textAlign = 'center';
          ctx.fillText(`${(edge.divergence * 100).toFixed(1)}%`, mx, my - 6);
          ctx.globalAlpha = 1;
        }
      }

      // Draw nodes
      for (const node of nodesRef.current) {
        node.pulse += 0.03;

        // Outer glow ring
        const glowR = 28 + 4 * Math.sin(node.pulse);
        const grad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, glowR);
        grad.addColorStop(0, 'rgba(56,189,248,0.35)');
        grad.addColorStop(1, 'rgba(56,189,248,0)');
        ctx.beginPath();
        ctx.arc(node.x, node.y, glowR, 0, 2 * Math.PI);
        ctx.fillStyle = grad;
        ctx.fill();

        // Node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, 16, 0, 2 * Math.PI);
        ctx.fillStyle = '#0ea5e9';
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 16;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Ring
        ctx.beginPath();
        ctx.arc(node.x, node.y, 16, 0, 2 * Math.PI);
        ctx.strokeStyle = '#7dd3fc';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Label
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.fillStyle = '#f1f5f9';
        ctx.textAlign = 'center';
        ctx.shadowBlur = 0;
        ctx.fillText(node.id, node.x, node.y + 34);
      }

      animRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [agents, multiConsensus]);

  const agentCount = Object.keys(agents).length;

  return (
    <div className="glass rounded-xl p-4 border border-gray-700/50">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-white">Consensus Network</h3>
        {multiConsensus && (
          <div className={`px-3 py-1 rounded-full text-xs font-semibold glass border ${
            multiConsensus.system_health === 'healthy'
              ? 'border-green-500/50 text-green-400 bg-green-500/10'
              : multiConsensus.system_health === 'critical'
              ? 'border-red-500/50 text-red-400 bg-red-500/10'
              : 'border-yellow-500/50 text-yellow-400 bg-yellow-500/10'
          }`}>
            System: {multiConsensus.system_health.toUpperCase()}
          </div>
        )}
      </div>

      {agentCount === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500 text-sm">
          Run Demo to see the live consensus graph
        </div>
      ) : (
        <canvas
          ref={canvasRef}
          className="w-full rounded-lg"
          style={{ height: '280px', background: 'rgba(15,23,42,0.4)' }}
        />
      )}

      {/* Edge legend */}
      {agentCount > 0 && (
        <div className="flex items-center gap-6 mt-3 px-2">
          {[
            { color: '#22c55e', label: 'Aligned' },
            { color: '#eab308', label: 'Minor drift' },
            { color: '#ef4444', label: 'Critical' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2">
              <div className="w-6 h-0.5 rounded" style={{ backgroundColor: color }} />
              <span className="text-xs text-gray-400">{label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
