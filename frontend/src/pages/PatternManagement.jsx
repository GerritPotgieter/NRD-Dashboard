import React, { useState, useEffect } from 'react';
import { Plus, Save, Trash2, FileCode } from 'lucide-react';
import { getPatterns, updatePattern } from '../api/api';

const PatternManagement = () => {
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingPattern, setEditingPattern] = useState(null);
  const [newPatternText, setNewPatternText] = useState('');

  useEffect(() => {
    loadPatterns();
  }, []);

  const loadPatterns = async () => {
    setLoading(true);
    try {
      const data = await getPatterns();
      setPatterns(data.patterns || []);
    } catch (error) {
      console.error('Failed to load patterns:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePattern = async (patternName, updatedPatterns) => {
    try {
      await updatePattern(patternName, updatedPatterns);
      await loadPatterns();
      setEditingPattern(null);
      alert('Pattern saved successfully!');
    } catch (error) {
      console.error('Failed to save pattern:', error);
      alert('Failed to save pattern');
    }
  };

  const handleAddPattern = (patternName, currentPatterns) => {
    if (newPatternText.trim()) {
      const updated = [...currentPatterns, newPatternText.trim()];
      handleSavePattern(patternName, updated);
      setNewPatternText('');
    }
  };

  const handleRemovePattern = (patternName, currentPatterns, index) => {
    const updated = currentPatterns.filter((_, i) => i !== index);
    handleSavePattern(patternName, updated);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="pattern-management">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Pattern Management</h1>
        <p className="text-gray-600 mt-1">Manage detection patterns for domain filtering</p>
      </div>

      {/* Pattern Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {patterns.map((pattern, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#ED0000] rounded-lg flex items-center justify-center">
                  <FileCode className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 capitalize">{pattern.name}</h2>
                  <p className="text-sm text-gray-500">{pattern.count} patterns</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    pattern.enabled
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {pattern.enabled ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            </div>

            {/* Pattern List */}
            <div className="space-y-2 mb-4">
              <div className="max-h-64 overflow-y-auto space-y-2">
                {pattern.patterns.map((p, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100">
                    <code className="text-sm text-gray-900 flex-1">{p}</code>
                    <button
                      onClick={() => handleRemovePattern(pattern.name, pattern.patterns, idx)}
                      className="p-1 hover:bg-red-100 rounded transition-colors"
                      title="Remove pattern"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Add New Pattern */}
            {editingPattern === pattern.name ? (
              <div className="space-y-2">
                <input
                  type="text"
                  value={newPatternText}
                  onChange={(e) => setNewPatternText(e.target.value)}
                  placeholder="Enter new pattern..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ED0000]"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleAddPattern(pattern.name, pattern.patterns);
                    }
                  }}
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAddPattern(pattern.name, pattern.patterns)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] transition-colors"
                  >
                    <Save className="w-4 h-4" />
                    Add Pattern
                  </button>
                  <button
                    onClick={() => {
                      setEditingPattern(null);
                      setNewPatternText('');
                    }}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setEditingPattern(pattern.name)}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-[#ED0000] hover:text-[#ED0000] transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add New Pattern
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Pattern Types</h3>
        <div className="space-y-2 text-sm text-blue-800">
          <p><strong>Keywords:</strong> Suspicious keywords that may indicate phishing (e.g., "login-absa", "secure-absa")</p>
          <p><strong>Typos:</strong> Common typosquatting variations (e.g., "abza", "abssa")</p>
          <p><strong>Prefix/Suffix:</strong> Brand name with prefixes or suffixes (e.g., "my-absa", "absa-bank")</p>
          <p><strong>TLD:</strong> Specific top-level domains to monitor (e.g., ".co.za", ".africa")</p>
        </div>
      </div>
    </div>
  );
};

export default PatternManagement;