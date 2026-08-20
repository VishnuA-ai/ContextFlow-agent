import { useState } from 'react';
import { Search, Loader2, CheckCircle, AlertTriangle, ChevronDown, ChevronUp, Shield } from 'lucide-react';
import { apiClient } from '../api';
import type { ResearchReport } from '../types';

export function ResearchAssistant() {
  const [topic, setTopic] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || isRunning) return;

    setIsRunning(true);
    setReport(null);
    setError(null);

    try {
      const result = await apiClient.runResearch(topic.trim());
      setReport(result);
    } catch {
      setError('Research failed — make sure the backend is running on :8000');
    } finally {
      setIsRunning(false);
    }
  };

  const exampleTopics = [
    'AI safety techniques in multi-agent systems',
    'Large language model hallucination prevention',
    'Reinforcement learning from human feedback',
  ];

  return (
    <div className="glass rounded-xl border border-gray-700/50 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-700/50 bg-gradient-to-r from-purple-500/10 to-blue-500/10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/20 border border-purple-500/30">
            <Search size={20} className="text-purple-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Research Assistant</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Submit any research topic — 3 Strands agents work autonomously, ContextFlow verifies the output
            </p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Input form */}
        <form onSubmit={handleSubmit} className="mb-6">
          <div className="flex gap-3">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter a research topic..."
              disabled={isRunning}
              className="flex-1 bg-gray-800/60 border border-gray-600/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/70 focus:ring-1 focus:ring-purple-500/40 transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isRunning || !topic.trim()}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunning ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Search size={18} />
                  Research
                </>
              )}
            </button>
          </div>

          {/* Example topics */}
          <div className="flex flex-wrap gap-2 mt-3">
            {exampleTopics.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTopic(t)}
                disabled={isRunning}
                className="text-xs px-3 py-1.5 glass rounded-full border border-gray-600/50 text-gray-400 hover:text-white hover:border-purple-500/50 transition-all"
              >
                {t}
              </button>
            ))}
          </div>
        </form>

        {/* Running state */}
        {isRunning && (
          <div className="glass bg-blue-500/10 border border-blue-500/30 rounded-xl p-6 text-center animate-pulse">
            <Loader2 size={32} className="animate-spin text-blue-400 mx-auto mb-3" />
            <p className="text-white font-semibold">Agents working in the background...</p>
            <div className="flex justify-center gap-6 mt-4 text-sm text-gray-400">
              <span>🔍 Scout researching</span>
              <span>⚖️ Critic evaluating</span>
              <span>🛡️ ContextFlow monitoring</span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="glass bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Report */}
        {report && !isRunning && (
          <div className="space-y-5 animate-fade-in">

            {/* Status bar */}
            <div className={`rounded-xl p-4 border flex items-start gap-4 ${
              report.contextflow_summary.hallucination_prevented
                ? 'bg-yellow-500/10 border-yellow-500/30'
                : 'bg-green-500/10 border-green-500/30'
            }`}>
              {report.contextflow_summary.hallucination_prevented ? (
                <Shield size={22} className="text-yellow-400 flex-shrink-0 mt-0.5" />
              ) : (
                <CheckCircle size={22} className="text-green-400 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <p className={`font-semibold text-sm ${
                  report.contextflow_summary.hallucination_prevented ? 'text-yellow-400' : 'text-green-400'
                }`}>
                  {report.contextflow_summary.hallucination_prevented
                    ? '⚡ ContextFlow resolved a conflict automatically'
                    : '✅ All agents verified — no conflicts'}
                </p>
                <p className="text-gray-300 text-sm mt-1">{report.executive_summary}</p>
              </div>
            </div>

            {/* ContextFlow stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: 'Conflicts Detected', value: report.contextflow_summary.conflicts_detected, color: report.contextflow_summary.conflicts_detected > 0 ? 'text-yellow-400' : 'text-green-400' },
                { label: 'Conflicts Resolved', value: report.contextflow_summary.conflicts_resolved, color: 'text-green-400' },
                { label: 'Consensus Level', value: report.contextflow_summary.consensus_level, color: 'text-blue-400' },
                { label: 'Audit Entries', value: report.contextflow_summary.audit_trail_entries, color: 'text-purple-400' },
              ].map(({ label, value, color }) => (
                <div key={label} className="glass rounded-lg p-3 border border-gray-700/50 text-center">
                  <p className="text-gray-400 text-xs mb-1">{label}</p>
                  <p className={`font-bold ${color}`}>{String(value)}</p>
                </div>
              ))}
            </div>

            {/* Key findings */}
            <div className="glass rounded-xl p-5 border border-gray-700/50">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <CheckCircle size={16} className="text-green-400" />
                Key Findings
              </h3>
              <ul className="space-y-2">
                {report.key_findings.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-purple-400 font-bold mt-0.5">•</span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>

            {/* Per-agent findings */}
            <div>
              <h3 className="text-white font-semibold mb-3">Agent Findings</h3>
              <div className="space-y-2">
                {report.agent_findings.map((agent) => {
                  const isExpanded = expandedAgent === agent.agent_id;
                  const colors: Record<string, string> = {
                    scout: 'border-blue-500/40 bg-blue-500/5',
                    critic: 'border-yellow-500/40 bg-yellow-500/5',
                    synthesis: 'border-green-500/40 bg-green-500/5',
                  };
                  const badgeColors: Record<string, string> = {
                    scout: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
                    critic: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
                    synthesis: 'bg-green-500/20 text-green-300 border-green-500/30',
                  };
                  return (
                    <div key={agent.agent_id} className={`glass rounded-xl border ${colors[agent.agent_id] || 'border-gray-700/50'}`}>
                      <button
                        onClick={() => setExpandedAgent(isExpanded ? null : agent.agent_id)}
                        className="w-full flex items-center justify-between p-4 text-left"
                      >
                        <div className="flex items-center gap-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${badgeColors[agent.agent_id] || 'bg-gray-500/20 text-gray-300 border-gray-500/30'}`}>
                            {agent.agent_id.toUpperCase()}
                          </span>
                          <span className="text-gray-300 text-sm">{agent.role}</span>
                          <span className="text-gray-500 text-xs">Confidence: {(agent.confidence * 100).toFixed(0)}%</span>
                        </div>
                        {isExpanded ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
                      </button>

                      {isExpanded && (
                        <div className="px-4 pb-4 space-y-3 border-t border-gray-700/30 pt-3">
                          <p className="text-sm text-gray-300">{agent.summary}</p>
                          <ul className="space-y-1.5">
                            {agent.key_facts.map((fact, i) => (
                              <li key={i} className="text-xs text-gray-400 flex gap-2">
                                <span className="text-purple-400">→</span>{fact}
                              </li>
                            ))}
                          </ul>
                          <p className="text-xs text-gray-500 italic">{agent.source}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Request ID */}
            <p className="text-xs text-gray-600 font-mono text-right">
              Request ID: {report.request_id} · Generated {new Date(report.generated_at * 1000).toLocaleTimeString()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
