import { useEffect, useState, useCallback } from 'react';
import { Brain, RefreshCw, Play, Square, Zap, Plus, GitCompare } from 'lucide-react';
import { useDashboardStore } from './store';
import { apiClient } from './api';
import { wsManager } from './websocket';
import { AgentCard } from './components/AgentCard';
import { DivergenceChart } from './components/DivergenceChart';
import { JournalTable } from './components/JournalTable';
import { MetricsPanel } from './components/MetricsPanel';
import { AddAgentModal } from './components/AddAgentModal';
import { ConsensusGraph } from './components/ConsensusGraph';
import { ToastContainer } from './components/Toast';
import { SuperbDemoAlert } from './components/SuperbDemoAlert';
import { ParticleBackground } from './components/ParticleBackground';
import { ResearchAssistant } from './components/ResearchAssistant';
import type { BeforeAfterResult, MultiAgentConsensus } from './types';

function App() {
  const {
    agents,
    consensusUpdates,
    metrics,
    selectedAgent,
    agentHistory,
    isConnected,
    wsError,
    setAgent,
    setSelectedAgent,
    setMetrics,
    setAgentHistory,
    setConnected,
    clearUpdates,
    setModal,
    addToast,
    isDemoRunning,
    setDemoRunning,
  } = useDashboardStore();

  const [isLoading, setIsLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [demoStage, setDemoStage] = useState<'setup' | 'divergence' | 'detecting' | 'syncing' | 'resolved' | null>(null);
  const [multiConsensus, setMultiConsensus] = useState<MultiAgentConsensus | null>(null);
  const [beforeAfter, setBeforeAfter] = useState<BeforeAfterResult | null>(null);
  const [showBeforeAfter, setShowBeforeAfter] = useState(false);
  const [strandsMode, setStrandsMode] = useState<string>('');

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  useEffect(() => { setMounted(true); }, []);

  // ─── Load agents from /agents endpoint (uses task from details, not history) ───
  const loadAgents = useCallback(async () => {
    try {
      const agentsData = await apiClient.getAgents();
      // Use the details map which has the correct task field
      if (agentsData.details) {
        for (const [agentId, detail] of Object.entries(agentsData.details)) {
          setAgent(agentId, {
            id: agentId,
            task: detail.task,
            confidence: detail.confidence,
            state_hash: detail.state_hash,
            timestamp: detail.timestamp,
            using_strands: detail.using_strands,
          });
        }
      }
    } catch {
      // no agents yet — that's fine
    }
  }, [setAgent]);

  // ─── Poll multi-agent consensus so ConsensusGraph has edges without WebSocket ───
  const pollMultiConsensus = useCallback(async () => {
    const agentIds = Object.keys(useDashboardStore.getState().agents);
    if (agentIds.length < 2) return;
    try {
      const result = await apiClient.checkMultiAgentConsensus(agentIds);
      setMultiConsensus(result);
    } catch {
      // silent
    }
  }, []);

  // ─── Initial load ───
  useEffect(() => {
    const init = async () => {
      try {
        const [, metricsData] = await Promise.all([
          apiClient.getHealth(),
          apiClient.getMetrics(),
        ]);
        setMetrics(metricsData);
        await loadAgents();
      } catch {
        addToast({ type: 'error', message: 'Cannot reach API. Make sure the backend is running on :8000' });
      } finally {
        setIsLoading(false);
      }
    };
    init();

    const metricsInterval = setInterval(async () => {
      try { setMetrics(await apiClient.getMetrics()); } catch { /* silent */ }
    }, 5000);

    const consensusInterval = setInterval(pollMultiConsensus, 4000);

    return () => {
      clearInterval(metricsInterval);
      clearInterval(consensusInterval);
    };
  }, [setMetrics, loadAgents, addToast, pollMultiConsensus]);

  // ─── Agent history on select ───
  useEffect(() => {
    if (!selectedAgent) return;
    apiClient.getAgentHistory(selectedAgent)
      .then(data => setAgentHistory(selectedAgent, data.history))
      .catch(() => {});
  }, [selectedAgent, setAgentHistory]);

  // ─── WebSocket ───
  const handleConnect = (agentId: string) => {
    if (isConnected) { wsManager.disconnect(); setConnected(false); }
    else { wsManager.connect(agentId); }
  };

  // ─── Add agent modal ───
  const handleAddAgent = () => setModal({ isOpen: true, type: 'addAgent' });

  // ─── Main demo ───
  const handleRunDemo = async () => {
    if (isDemoRunning) return;
    setDemoRunning(true);
    setShowBeforeAfter(false);

    try {
      setDemoStage('setup');
      await sleep(1800);

      const result = await apiClient.runDemo();
      setStrandsMode(result.strands_mode);

      // Populate agents with correct task from agent_summaries
      for (const agentId of result.agents_created) {
        setAgent(agentId, {
          id: agentId,
          task: result.agent_summaries[agentId] || agentId,
          confidence: agentId === 'scout' ? 0.85 : agentId === 'critic' ? 0.75 : 0.90,
          state_hash: result.consensus_results.scout_vs_critic?.mismatches?.join('') || 'demo',
          timestamp: Date.now() / 1000,
          using_strands: result.strands_mode !== 'simulation',
        });
      }

      setDemoStage('divergence');
      await sleep(2500);

      setDemoStage('detecting');
      await sleep(2000);

      setDemoStage('syncing');
      await sleep(2000);

      setDemoStage('resolved');

      // Fetch before/after data while showing resolved stage
      const ba = await apiClient.getBeforeAfter();
      setBeforeAfter(ba);

      // Refresh multi-agent consensus graph
      await pollMultiConsensus();

      await sleep(3000);
      setDemoStage(null);
      setShowBeforeAfter(true);

      setMetrics(await apiClient.getMetrics());
      addToast({
        type: 'success',
        message: `Demo complete! Strands mode: ${result.strands_mode}. Scout↔Critic divergence: ${result.consensus_results.scout_vs_critic.divergence_percent}`,
      });
    } catch (err) {
      console.error(err);
      setDemoStage(null);
      addToast({ type: 'error', message: 'Demo failed — is the backend running?' });
    } finally {
      setDemoRunning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen animated-gradient flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-primary-400" size={48} />
          <p className="text-gray-300 text-lg">Loading ContextFlow...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen animated-gradient transition-opacity duration-500 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
      <ToastContainer />
      <AddAgentModal />
      <ParticleBackground />
      {demoStage && <SuperbDemoAlert stage={demoStage} />}

      {/* ── HEADER ── */}
      <header className="glass border-b border-gray-700/50 px-6 py-4 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="text-primary-400" size={32} />
            <div>
              <h1 className="text-xl font-bold text-white">ContextFlow</h1>
              <p className="text-xs text-gray-400">Multi-Agent Consensus Engine · Strands Agents SDK</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {strandsMode && (
              <div className="px-3 py-1 rounded-full glass bg-purple-500/20 border border-purple-500/40 text-xs text-purple-300 font-mono">
                {strandsMode === 'real_bedrock' ? '🟢 Bedrock' : '🔵 Simulation'}
              </div>
            )}
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full glass ${
              isConnected ? 'bg-green-500/20 text-green-400 border-green-500/50' : 'bg-gray-700/50 text-gray-400 border-gray-600/50'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`} />
              <span className="text-sm font-medium">{isConnected ? 'Live' : 'Offline'}</span>
            </div>
            <button
              onClick={handleRunDemo}
              disabled={isDemoRunning}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all btn-glow disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            >
              <Zap size={18} />
              {isDemoRunning ? 'Running...' : 'Run Demo'}
            </button>
            <button
              onClick={handleAddAgent}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors btn-glow"
            >
              <Plus size={18} />
              Add Agent
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">

        {/* ── METRICS ── */}
        <section className="mb-8">
          <MetricsPanel metrics={metrics} />
        </section>

        {/* ── RESEARCH ASSISTANT ── */}
        <section className="mb-8">
          <ResearchAssistant />
        </section>

        {/* ── BEFORE / AFTER PANEL ── */}
        {showBeforeAfter && beforeAfter && (
          <section className="mb-8 animate-fade-in">
            <div className="flex items-center gap-3 mb-4">
              <GitCompare className="text-pink-400" size={22} />
              <h2 className="text-lg font-semibold text-white">Before vs After ContextFlow</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* WITHOUT */}
              <div className="glass rounded-xl p-6 border-2 border-red-500/40 glow-red">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">❌</span>
                  <h3 className="font-bold text-red-400 text-lg">Without ContextFlow</h3>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="bg-red-500/10 rounded-lg p-3 font-mono">
                    <p className="text-gray-300">Scout says: <span className="text-red-300 font-bold">{beforeAfter.without_contextflow.scout_says.citations} citations</span></p>
                    <p className="text-gray-300 mt-1">Critic says: <span className="text-red-300 font-bold">{beforeAfter.without_contextflow.critic_says.citations} citations</span></p>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Divergence</span>
                    <span className="text-red-400 font-bold text-lg">{beforeAfter.without_contextflow.divergence_percent}</span>
                  </div>
                  <p className="text-red-300/80 text-xs italic">{beforeAfter.without_contextflow.outcome}</p>
                  <p className="text-gray-500 text-xs">{beforeAfter.without_contextflow.cost_of_failure}</p>
                </div>
              </div>

              {/* WITH */}
              <div className="glass rounded-xl p-6 border-2 border-green-500/40 glow-green">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">✅</span>
                  <h3 className="font-bold text-green-400 text-lg">With ContextFlow</h3>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="bg-green-500/10 rounded-lg p-3 font-mono">
                    <p className="text-gray-300">Detected: <span className="text-yellow-300 font-bold">{beforeAfter.with_contextflow.detection.divergence_percent} drift</span></p>
                    <p className="text-gray-300 mt-1">Resolved to: <span className="text-green-300 font-bold">{beforeAfter.with_contextflow.resolution.consensus_citations} citations</span></p>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Strategy</span>
                    <span className="text-green-400 font-medium capitalize">{beforeAfter.with_contextflow.resolution.strategy.replace('_', ' ')}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Prevention Rate</span>
                    <span className="text-green-400 font-bold text-lg">{beforeAfter.with_contextflow.prevention_rate}</span>
                  </div>
                  <p className="text-green-300/80 text-xs italic">{beforeAfter.with_contextflow.outcome}</p>
                </div>
              </div>
            </div>

            {/* Summary bar */}
            <div className="mt-4 glass rounded-xl p-4 border border-purple-500/30 grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Detection Latency', value: beforeAfter.summary.latency },
                { label: 'Extra LLM Calls', value: `${beforeAfter.summary.llm_calls_for_sync}` },
                { label: 'Strands Agents', value: `${beforeAfter.summary.strands_agents_used}` },
                { label: 'Algorithm', value: 'SHA-256 SSV + DCP' },
              ].map(({ label, value }) => (
                <div key={label} className="text-center">
                  <p className="text-gray-400 text-xs">{label}</p>
                  <p className="text-white font-bold mt-1">{value}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── CONSENSUS GRAPH ── */}
        {Object.keys(agents).length > 0 && (
          <section className="mb-8">
            <ConsensusGraph multiConsensus={multiConsensus} />
          </section>
        )}

        {/* ── AGENTS GRID ── */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">
              Active Agents
              {Object.keys(agents).length > 0 && (
                <span className="ml-2 text-sm text-gray-400">({Object.keys(agents).length})</span>
              )}
            </h2>
            {selectedAgent && (
              <button
                onClick={() => handleConnect(selectedAgent)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg glass transition-colors ${
                  isConnected
                    ? 'bg-red-500/20 text-red-400 border-red-500/50 hover:bg-red-500/30'
                    : 'bg-green-500/20 text-green-400 border-green-500/50 hover:bg-green-500/30'
                }`}
              >
                {isConnected ? <Square size={16} /> : <Play size={16} />}
                {isConnected ? 'Stop WebSocket' : 'Start WebSocket'}
              </button>
            )}
          </div>

          {Object.keys(agents).length === 0 ? (
            <div className="glass p-10 rounded-xl border border-gray-700/50 text-center">
              <Brain className="mx-auto mb-4 text-gray-500" size={56} />
              <p className="text-gray-300 text-lg font-medium mb-1">No agents running yet</p>
              <p className="text-gray-500 text-sm mb-6">Click "Run Demo" to see ContextFlow prevent hallucination in real-time</p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleRunDemo}
                  disabled={isDemoRunning}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all btn-glow disabled:opacity-50 font-semibold"
                >
                  <Zap size={18} />
                  Run Demo
                </button>
                <button
                  onClick={handleAddAgent}
                  className="flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors btn-glow"
                >
                  <Plus size={18} />
                  Add Agent
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.values(agents).map((agent) => {
                // Get consensus status from multiConsensus pairwise results
                const pairKey = Object.keys(multiConsensus?.consensus_graph || {}).find(k =>
                  k.includes(agent.id)
                );
                const pairData = pairKey ? multiConsensus?.consensus_graph[pairKey] : undefined;

                // Also check WS updates as fallback
                const latestUpdate = consensusUpdates.filter(u => u.agent === agent.id).pop();
                const wsStatus = latestUpdate?.consensus_with_others[0];

                const level = (pairData?.level || wsStatus?.level) as 'aligned' | 'minor_drift' | 'critical' | undefined;
                const divergence = pairData?.divergence ?? wsStatus?.divergence;

                return (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    consensusLevel={level}
                    divergence={divergence}
                    onClick={() => setSelectedAgent(agent.id)}
                    isSelected={selectedAgent === agent.id}
                  />
                );
              })}
            </div>
          )}
        </section>

        {/* ── DIVERGENCE CHART ── */}
        {consensusUpdates.length > 0 && (
          <section className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Divergence Over Time</h2>
              <button onClick={clearUpdates} className="text-sm text-gray-400 hover:text-white transition-colors">
                Clear
              </button>
            </div>
            <div className="glass p-6 rounded-xl border border-gray-700/50">
              <DivergenceChart updates={consensusUpdates} />
            </div>
          </section>
        )}

        {/* ── AGENT HISTORY ── */}
        {selectedAgent && agentHistory[selectedAgent] && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-4">
              Audit Trail — <span className="text-primary-400">{selectedAgent}</span>
            </h2>
            <div className="glass p-6 rounded-xl border border-gray-700/50">
              <JournalTable entries={agentHistory[selectedAgent]} />
            </div>
          </section>
        )}

        {wsError && (
          <div className="mb-8 glass bg-red-500/20 border border-red-500/50 p-4 rounded-xl">
            <p className="text-red-400">{wsError}</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
