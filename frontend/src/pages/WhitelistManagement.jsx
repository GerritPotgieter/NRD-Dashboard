import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Shield, AlertTriangle, Download, Upload } from 'lucide-react';
import { getIgnoreDomains, addIgnoreDomain, removeIgnoreDomain, getIncludedDomains } from '../api/api';

const WhitelistManagement = () => {
  const [ignoreDomains, setIgnoreDomains] = useState([]);
  const [includedDomains, setIncludedDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ignore');
  const [newDomain, setNewDomain] = useState('');

  useEffect(() => {
    loadWhitelists();
  }, []);

  const loadWhitelists = async () => {
    setLoading(true);
    try {
      const [ignoreData, includedData] = await Promise.all([
        getIgnoreDomains(),
        getIncludedDomains()
      ]);
      setIgnoreDomains(ignoreData.domains || []);
      setIncludedDomains(includedData.domains || []);
    } catch (error) {
      console.error('Failed to load whitelists:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddDomain = async () => {
    if (!newDomain.trim()) return;
    
    try {
      await addIgnoreDomain(newDomain.trim());
      setNewDomain('');
      await loadWhitelists();
      alert('Domain added successfully!');
    } catch (error) {
      console.error('Failed to add domain:', error);
      alert('Failed to add domain');
    }
  };

  const handleRemoveDomain = async (domain) => {
    if (window.confirm(`Remove ${domain} from ignore list?`)) {
      try {
        await removeIgnoreDomain(domain);
        await loadWhitelists();
      } catch (error) {
        console.error('Failed to remove domain:', error);
        alert('Failed to remove domain');
      }
    }
  };

  const handleBulkImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (file) {
        const text = await file.text();
        const domains = text.split('\n').map(d => d.trim()).filter(d => d && !d.startsWith('#'));
        
        try {
          for (const domain of domains) {
            await addIgnoreDomain(domain);
          }
          await loadWhitelists();
          alert(`Imported ${domains.length} domains`);
        } catch (error) {
          console.error('Failed to import domains:', error);
          alert('Failed to import some domains');
        }
      }
    };
    input.click();
  };

  const handleExport = () => {
    const domains = activeTab === 'ignore' ? ignoreDomains : includedDomains;
    const blob = new Blob([domains.join('\n')], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeTab}_domains.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner"></div>
      </div>
    );
  }

  const currentDomains = activeTab === 'ignore' ? ignoreDomains : includedDomains;

  return (
    <div className="p-6 space-y-6" data-testid="whitelist-management">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Whitelist Management</h1>
          <p className="text-gray-600 mt-1">Manage safe domains and confirmed threats</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleBulkImport}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Import
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex gap-1 px-6">
            <button
              onClick={() => setActiveTab('ignore')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === 'ignore'
                  ? 'border-[#ED0000] text-[#ED0000] font-medium'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <Shield className="w-4 h-4" />
              Ignore Domains ({ignoreDomains.length})
            </button>
            <button
              onClick={() => setActiveTab('included')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === 'included'
                  ? 'border-[#ED0000] text-[#ED0000] font-medium'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
              Confirmed Threats ({includedDomains.length})
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Info Banner */}
          {activeTab === 'ignore' ? (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="text-green-900 font-semibold mb-1">Ignore Domains (Safe List)</h3>
              <p className="text-sm text-green-800">
                Domains in this list are considered safe and will be excluded from monitoring.
                Use this for legitimate domains that match your patterns but are not threats.
              </p>
            </div>
          ) : (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="text-red-900 font-semibold mb-1">Confirmed Threats</h3>
              <p className="text-sm text-red-800">
                Domains in this list are confirmed phishing or impersonation threats.
                They will always be included in monitoring regardless of patterns.
              </p>
            </div>
          )}

          {/* Add Domain Form */}
          {activeTab === 'ignore' && (
            <div className="mb-6 flex gap-2">
              <input
                type="text"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="Enter domain to add (e.g., example.com)..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ED0000]"
                onKeyPress={(e) => e.key === 'Enter' && handleAddDomain()}
              />
              <button
                onClick={handleAddDomain}
                className="flex items-center gap-2 px-6 py-2 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Domain
              </button>
            </div>
          )}

          {/* Domain List */}
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-700">
                {currentDomains.length} domain(s)
              </h3>
            </div>
            
            <div className="max-h-96 overflow-y-auto space-y-2">
              {currentDomains.map((domain, index) => (
                <div
                  key={index}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    activeTab === 'ignore'
                      ? 'bg-green-50 hover:bg-green-100'
                      : 'bg-red-50 hover:bg-red-100'
                  } transition-colors`}
                >
                  <div className="flex items-center gap-3">
                    {activeTab === 'ignore' ? (
                      <Shield className="w-5 h-5 text-green-600" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                    )}
                    <code className="text-sm font-mono text-gray-900">{domain}</code>
                  </div>
                  {activeTab === 'ignore' && (
                    <button
                      onClick={() => handleRemoveDomain(domain)}
                      className="p-2 hover:bg-red-100 rounded transition-colors"
                      title="Remove domain"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  )}
                </div>
              ))}
              {currentDomains.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No domains in this list
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Safe Domains</p>
              <p className="text-2xl font-bold text-gray-900">{ignoreDomains.length}</p>
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Excluded from monitoring
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Confirmed Threats</p>
              <p className="text-2xl font-bold text-gray-900">{includedDomains.length}</p>
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Always monitored
          </p>
        </div>
      </div>
    </div>
  );
};

export default WhitelistManagement;