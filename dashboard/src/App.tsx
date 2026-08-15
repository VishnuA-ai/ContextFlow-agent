import { useEffect, useState } from 'react';
import { Brain, RefreshCw, Play, Square, Zap, Plus } from 'lucide-react';
import { useDashboardStore } from './store';
import { apiClient } from './api';
import { wsManager } from './websocket';
import { AgentCard } from './components/AgentCard';
import { ConsensusBadge } from './components/ConsensusBadge';
import { DivergenceChart } from './components/DivergenceChart';
import { JournalTable } from './components/JournalTable';
import { MetricsPanel } from './components/MetricsPanel';
import { AddAgentModal } from './components/AddAgentModal';
import { ConsensusGraph } from './components/ConsensusGraph';
import { ToastContainer } from './components/Toast';
import { DemoAlert } from './components/DemoAlert';

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
    setWsError,
    clearUpdates,
    setModal,
    addToast,
    isDemoRunning,
    setDemoRunning,
  } = useDashboardStore();

  const [isLoading, setIsLoading] = useState(true);
  const [demoStage, setDemoStage] = useState<'setup' | 'divergence' | 'detecting' | 'syncing' | 'resolved' | null>(null);

  // Helper function for sleep
  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  // Fetch initial data and load existing agents
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [health, metricsData, agentsData] = await Promise.all([
          apiClient.getHealth(),
          apiClient.getMetrics(),
          apiClient.getAgents(),
        ]);
        setMetrics(metricsData);
        
        // Load existing agents
        for (const agentId of agentsData.agents) {
          try {
            const historyData = await apiClient.getAgentHistory(agentId);
            if (historyData.history.length > 0) {
              const latestEntry = historyData.history[0];
              setAgent(agentId, {
                id: agentId,
                task: latestEntry.state_delta.task as string || 'Unknown task',
                confidence: 0.8, // Default confidence
                state_hash: latestEntry.hash_change.split(' → ')[1]?.replace('...', '') || '',
                timestamp: latestEntry.timestamp,
              });
            }
          } catch (error) {
            console.error(`Failed to load agent ${agentId}:`, error);
          }
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
        addToast({ type: 'error', message: 'Failed to connect to API. Make sure the backend is running.' });
        setIsLoading(false);
      }
    };

    fetchData();

    // Poll metrics every 5 seconds
    const interval = setInterval(async () => {
      try {
        const metricsData = await apiClient.getMetrics();
        setMetrics(metricsData);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [setMetrics, setAgent, addToast]);

  // Fetch agent history when agent is selected
  useEffect(() => {
    if (selectedAgent) {
      const fetchHistory = async () => {
        try {
          const historyData = await apiClient.getAgentHistory(selectedAgent);
          setAgentHistory(selectedAgent, historyData.history);
        } catch (error) {
          console.error('Failed to fetch agent history:', error);
        }
      };
      fetchHistory();
    }
  }, [selectedAgent, setAgentHistory]);

  // Handle WebSocket connection
  const handleConnect = (agentId: string) => {
    if (isConnected) {
      wsManager.disconnect();
      setConnected(false);
    } else {
      wsManager.connect(agentId);
    }
  };

  const handleAddAgent = () => {
    setModal({ isOpen: true, type: 'addAgent' });
  };

  const handleRunDemo = async () => {
    if (isDemoRunning) return;
    
    setDemoRunning(true);
    
    try {
      // Stage 1: Setup (2 seconds)
      setDemoStage('setup');
      await sleep(2000);

      // Call API to create demo agents
      const result = await apiClient.runDemo();
      
      // Add demo agents to the store
      for (const agentId of result.agents_created) {
        const agentData = result.consensus_results[`scout_vs_${agentId === 'scout' ? 'critic' : agentId === 'critic' ? 'synthesis' : 'scout'}`];
        setAgent(agentId, {
          id: agentId,
          task: agentId === 'scout' ? 'Research emerging AI safety techniques' : 
                agentId === 'critic' ? 'Critique AI safety research methodology' : 
                'Synthesize findings into recommendations',
          confidence: agentId === 'scout' ? 0.85 : agentId === 'critic' ? 0.75 : 0.90,
          state_hash: 'demo-hash',
          timestamp: Date.now() / 1000,
        });
      }
      
      // Stage 2: Show divergence (3 seconds) - the PROBLEM
      setDemoStage('divergence');
      await sleep(3000);

      // Stage 3: Detecting (2 seconds)
      setDemoStage('detecting');
      await sleep(2000);

      // Stage 4: Syncing (2 seconds)
      setDemoStage('syncing');
      await sleep(2000);

      // Stage 5: Resolved (3 seconds) - the SOLUTION
      setDemoStage('resolved');
      await sleep(3000);

      // Reset and refresh agents
      setDemoStage(null);
      
      // Refresh metrics
      const metricsData = await apiClient.getMetrics();
      setMetrics(metricsData);
      
      addToast({ type: 'success', message: 'Demo completed! Scout, Critic, and Synthesis agents created.' });
    } catch (error) {
      console.error('Demo error:', error);
      setDemoStage(null);
      addToast({ type: 'error', message: 'Demo failed. Make sure the API is running.' });
    } finally {
      setDemoRunning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen animated-gradient flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-primary-400" size={48} />
          <p className="text-gray-300">Loading ContextFlow Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen animated-gradient">
      <ToastContainer />
      <AddAgentModal />
      {demoStage && <DemoAlert stage={demoStage} />}
      
      {/* Header */}
      <header className="glass border-b border-gray-700/50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="text-primary-400" size={32} />
            <div>
              <h1 className="text-xl font-bold text-white">ContextFlow</h1>
              <p className="text-sm text-gray-400">Multi-Agent Consensus Engine</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full glass ${
              isConnected ? 'bg-green-500/20 text-green-400 border-green-500/50' : 'bg-gray-700/50 text-gray-400 border-gray-600/50'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse-glow' : 'bg-gray-400'}`} />
              <span className="text-sm font-medium">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <button
              onClick={handleRunDemo}
              disabled={isDemoRunning}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all btn-glow disabled:opacity-50 disabled:cursor-not-allowed"
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Metrics */}
        <section className="mb-8">
          <MetricsPanel metrics={metrics} />
        </section>

        {/* Consensus Graph */}
        {Object.keys(agents).length > 0 && (
          <section className="mb-8">
            <ConsensusGraph />
          </section>
        )}

        {/* Agents Grid */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Active Agents</h2>
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
            <div className="glass p-8 rounded-lg border border-gray-700/50 text-center">
              <Brain className="mx-auto mb-4 text-gray-500" size={48} />
              <p className="text-gray-400 mb-4">No agents registered yet</p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleRunDemo}
                  disabled={isDemoRunning}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all btn-glow disabled:opacity-50"
                >
                  <Zap size={18} />
                  Run Demo
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
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.values(agents).map((agent) => {
                const latestUpdate = consensusUpdates
                  .filter((u) => u.agent === agent.id)
                  .pop();
                const consensusStatus = latestUpdate?.consensus_with_others[0];

                return (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    consensusLevel={consensusStatus?.level}
                    divergence={consensusStatus?.divergence}
                    onClick={() => setSelectedAgent(agent.id)}
                    isSelected={selectedAgent === agent.id}
                  />
                );
              })}
            </div>
          )}
        </section>

        {/* Divergence Chart */}
        {consensusUpdates.length > 0 && (
          <section className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Divergence Over Time</h2>
              <button
                onClick={clearUpdates}
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                Clear History
              </button>
            </div>
            <div className="glass p-6 rounded-lg border border-gray-700/50">
              <DivergenceChart updates={consensusUpdates} />
            </div>
          </section>
        )}

        {/* Agent History */}
        {selectedAgent && agentHistory[selectedAgent] && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-4">
              Agent History: {selectedAgent}
            </h2>
            <div className="glass p-6 rounded-lg border border-gray-700/50">
              <JournalTable entries={agentHistory[selectedAgent]} />
            </div>
          </section>
        )}

        {/* WebSocket Error */}
        {wsError && (
          <div className="mb-8 glass bg-red-500/20 border border-red-500/50 p-4 rounded-lg">
            <p className="text-red-400">{wsError}</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
