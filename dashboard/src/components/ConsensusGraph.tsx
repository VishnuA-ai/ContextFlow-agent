import { useEffect, useRef } from 'react';
import { useDashboardStore } from '../store';

interface Node {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface Edge {
  from: string;
  to: string;
  level: 'aligned' | 'minor_drift' | 'critical';
  divergence: number;
}

export function ConsensusGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { agents, consensusUpdates } = useDashboardStore();
  const nodesRef = useRef<Node[]>([]);
  const edgesRef = useRef<Edge[]>([]);
  const animationRef = useRef<number>();

  useEffect(() => {
    // Initialize nodes for each agent
    const agentIds = Object.keys(agents);
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Initialize or update nodes
    if (nodesRef.current.length !== agentIds.length) {
      nodesRef.current = agentIds.map((id, index) => {
        const angle = (index / agentIds.length) * 2 * Math.PI;
        const radius = Math.min(canvas.width, canvas.height) * 0.3;
        return {
          id,
          x: canvas.width / 2 + Math.cos(angle) * radius,
          y: canvas.height / 2 + Math.sin(angle) * radius,
          vx: 0,
          vy: 0,
        };
      });
    }

    // Create edges based on consensus updates
    const latestUpdate = consensusUpdates[consensusUpdates.length - 1];
    if (latestUpdate) {
      edgesRef.current = latestUpdate.consensus_with_others.map((status) => ({
        from: latestUpdate.agent,
        to: status.agent,
        level: status.level,
        divergence: status.divergence,
      }));
    }

    const animate = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw edges
      edgesRef.current.forEach((edge) => {
        const fromNode = nodesRef.current.find((n) => n.id === edge.from);
        const toNode = nodesRef.current.find((n) => n.id === edge.to);
        if (!fromNode || !toNode) return;

        const color = edge.level === 'aligned' ? '#22c55e' : 
                     edge.level === 'minor_drift' ? '#eab308' : '#ef4444';

        ctx.beginPath();
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(toNode.x, toNode.y);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2 + edge.divergence * 10;
        ctx.globalAlpha = 0.6;
        ctx.stroke();
        ctx.globalAlpha = 1;
      });

      // Draw nodes
      nodesRef.current.forEach((node) => {
        // Glow effect
        const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, 40);
        gradient.addColorStop(0, 'rgba(56, 189, 248, 0.3)');
        gradient.addColorStop(1, 'rgba(56, 189, 248, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(node.x, node.y, 40, 0, 2 * Math.PI);
        ctx.fill();

        // Node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, 15, 0, 2 * Math.PI);
        ctx.fillStyle = '#38bdf8';
        ctx.fill();
        ctx.strokeStyle = '#0ea5e9';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Label
        ctx.fillStyle = '#f8fafc';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(node.id, node.x, node.y + 30);
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [agents, consensusUpdates]);

  return (
    <div className="glass rounded-lg p-4 h-80">
      <h3 className="text-lg font-semibold text-white mb-4">Consensus Network</h3>
      <canvas
        ref={canvasRef}
        className="w-full h-full rounded-lg bg-dark-bgSecondary/50"
      />
    </div>
  );
}
