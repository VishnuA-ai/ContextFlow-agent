import { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { useDashboardStore } from '../store';
import { apiClient } from '../api';

export function AddAgentModal() {
  const { modal, setModal, setAgent, addToast } = useDashboardStore();
  const [formData, setFormData] = useState({
    agentId: '',
    task: '',
    observations: '{}',
    decisions: '[]',
    constraints: '{}',
    confidence: 0.8,
  });

  const isOpen = modal.isOpen && modal.type === 'addAgent';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const observations = JSON.parse(formData.observations);
      const decisions = JSON.parse(formData.decisions);
      const constraints = JSON.parse(formData.constraints);

      const result = await apiClient.generateSSV({
        agent_id: formData.agentId,
        current_task: formData.task,
        observations,
        decisions_made: decisions,
        constraints,
        confidence: formData.confidence,
      });

      setAgent(formData.agentId, {
        id: formData.agentId,
        task: formData.task,
        confidence: result.confidence,
        state_hash: result.state_hash,
        timestamp: result.timestamp,
      });

      addToast({ type: 'success', message: `Agent "${formData.agentId}" created successfully` });
      setModal({ isOpen: false, type: null });
      
      // Reset form
      setFormData({
        agentId: '',
        task: '',
        observations: '{}',
        decisions: '[]',
        constraints: '{}',
        confidence: 0.8,
      });
    } catch (error) {
      addToast({ type: 'error', message: 'Failed to create agent. Please check your inputs.' });
    }
  };

  const handleClose = () => {
    setModal({ isOpen: false, type: null });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="glass-strong rounded-xl p-6 w-full max-w-lg animate-slide-in">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Add New Agent</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Agent ID
            </label>
            <input
              type="text"
              value={formData.agentId}
              onChange={(e) => setFormData({ ...formData, agentId: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bgSecondary border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500 transition-colors"
              placeholder="e.g., research_agent_1"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Task
            </label>
            <textarea
              value={formData.task}
              onChange={(e) => setFormData({ ...formData, task: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bgSecondary border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500 transition-colors resize-none"
              rows={3}
              placeholder="Describe the agent's task..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Observations (JSON)
            </label>
            <textarea
              value={formData.observations}
              onChange={(e) => setFormData({ ...formData, observations: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bgSecondary border border-gray-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-primary-500 transition-colors resize-none"
              rows={3}
              placeholder='{"key": "value"}'
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Decisions Made (JSON array)
            </label>
            <textarea
              value={formData.decisions}
              onChange={(e) => setFormData({ ...formData, decisions: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bgSecondary border border-gray-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-primary-500 transition-colors resize-none"
              rows={2}
              placeholder='["decision1", "decision2"]'
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Constraints (JSON)
            </label>
            <textarea
              value={formData.constraints}
              onChange={(e) => setFormData({ ...formData, constraints: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bgSecondary border border-gray-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-primary-500 transition-colors resize-none"
              rows={2}
              placeholder='{"constraint": "value"}'
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Confidence: {Math.round(formData.confidence * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.confidence}
              onChange={(e) => setFormData({ ...formData, confidence: parseFloat(e.target.value) })}
              className="w-full h-2 bg-dark-bgSecondary rounded-lg appearance-none cursor-pointer accent-primary-500"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
            >
              <Plus size={18} />
              Create Agent
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
