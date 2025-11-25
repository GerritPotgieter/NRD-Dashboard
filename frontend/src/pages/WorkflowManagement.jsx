import React, { useState, useEffect } from 'react';
import { Play, RefreshCw, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import { triggerWorkflow, getWorkflowStatus } from '../api/api';

const WorkflowManagement = () => {
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    loadWorkflowStatus();
    const interval = setInterval(loadWorkflowStatus, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const loadWorkflowStatus = async () => {
    try {
      const status = await getWorkflowStatus();
      setWorkflowStatus(status);
      
      // Just set the logs directly from backend
      if (status.logs && Array.isArray(status.logs)) {
        setLogs(status.logs);
      }
    } catch (error) {
      console.error('Failed to load workflow status:', error);
    }
  };

  const handleRunWorkflow = async () => {
    if (workflowStatus?.running) {
      alert('Workflow is already running!');
      return;
    }

    if (!window.confirm('Start the full NRD workflow? This will:\n\n1. Download latest NRD lists (last 7 days)\n2. Parse and filter domains\n3. Scan domains for activity\n4. Capture screenshots\n\nThis may take a few minutes depending on how many domains have to be monitored.')) {
      return;
    }

    setLoading(true);
    setLogs([]); // Clear previous logs
    try {
      const result = await triggerWorkflow();
      await loadWorkflowStatus();
      alert('✅ Workflow started successfully! Check the status below for progress.');
    } catch (error) {
      console.error('Failed to start workflow:', error);
      alert('❌ Failed to start workflow: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const workflowSteps = [
    {
      id: 'download',
      title: 'Download NRD Lists',
      description: 'Retrieve newly registered domains from WhoisDS (last 7 days)',
      icon: '📥',
    },
    {
      id: 'parse',
      title: 'Parse & Filter',
      description: 'Analyze domains against patterns and categorize matches',
      icon: '🔍',
    },
    {
      id: 'scan',
      title: 'Scan Domains',
      description: 'Check domain activity and detect content changes',
      icon: '🌐',
    },
    {
      id: 'screenshot',
      title: 'Capture Screenshots',
      description: 'Take screenshots of active domains with content changes',
      icon: '📸',
    },
  ];

  return (
    <div className="p-6 space-y-6" data-testid="workflow-management">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Management</h1>
          <p className="text-gray-600 mt-1">Monitor and control the NRD scanning workflow</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadWorkflowStatus}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh Status
          </button>
          <button
            onClick={handleRunWorkflow}
            disabled={loading || workflowStatus?.running}
            className="flex items-center gap-2 px-6 py-2 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            data-testid="run-workflow-btn"
          >
            <Play className="w-4 h-4" />
            {loading ? 'Starting...' : workflowStatus?.running ? 'Running...' : 'Run Workflow'}
          </button>
        </div>
      </div>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Current Status</h2>
          {workflowStatus?.running ? (
            <div className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg">
              <div className="spinner w-4 h-4 border-blue-700"></div>
              <span className="font-medium">Running</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg">
              <CheckCircle className="w-4 h-4" />
              <span className="font-medium">Idle</span>
            </div>
          )}
        </div>

        {workflowStatus?.message && (
          <div className={`p-4 rounded-lg mb-6 ${
            workflowStatus.running
              ? 'bg-blue-50 text-blue-800 border-2 border-blue-200'
              : workflowStatus.current_step === 'completed'
              ? 'bg-green-50 text-green-800 border-2 border-green-200'
              : workflowStatus.current_step === 'failed' || workflowStatus.current_step === 'error'
              ? 'bg-red-50 text-red-800 border-2 border-red-200'
              : 'bg-gray-50 text-gray-800'
          }`}>
            <p className="font-medium">{workflowStatus.message}</p>
            {workflowStatus.start_time && (
              <p className="text-xs mt-2 opacity-75">
                Started: {new Date(workflowStatus.start_time).toLocaleString()}
                {workflowStatus.end_time && ` • Ended: ${new Date(workflowStatus.end_time).toLocaleString()}`}
              </p>
            )}
          </div>
        )}

        {workflowStatus?.current_step && workflowStatus.running && (
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">Current Step:</p>
            <div className="flex items-center gap-3">
              <div className="flex-1 bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-[#ED0000] h-3 rounded-full transition-all duration-500"
                  style={{ 
                    width: workflowStatus.current_step === 'download' ? '25%' 
                      : workflowStatus.current_step === 'parse' ? '50%'
                      : workflowStatus.current_step === 'scan' ? '75%'
                      : workflowStatus.current_step === 'screenshot' ? '100%'
                      : '5%'
                  }}
                ></div>
              </div>
              <p className="text-lg font-semibold text-gray-900 capitalize min-w-[120px]">
                {workflowStatus.current_step}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Workflow Steps
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Workflow Steps</h2>
        <div className="space-y-4">
          {workflowSteps.map((step, index) => {
            const isActive = workflowStatus?.running && workflowStatus?.current_step === step.id;
            const isCompleted = workflowStatus?.current_step === 'completed' || 
              (workflowStatus?.current_step && 
               workflowSteps.findIndex(s => s.id === workflowStatus.current_step) > index);
            
            return (
              <div key={step.id} className={`flex items-start gap-4 p-4 rounded-lg transition-all ${
                isActive ? 'bg-blue-50 border-2 border-blue-300 shadow-md' : 
                isCompleted ? 'bg-green-50 border border-green-200' :
                'bg-gray-50 border border-gray-200'
              }`}>
                <div className="flex-shrink-0">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl shadow ${
                    isActive ? 'bg-blue-100 animate-pulse' :
                    isCompleted ? 'bg-green-100' :
                    'bg-white'
                  }`}>
                    {isCompleted ? '✅' : step.icon}
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {index + 1}. {step.title}
                    </h3>
                    {isActive && (
                      <span className="px-3 py-1 bg-blue-500 text-white text-xs font-medium rounded-full animate-pulse">
                        In Progress
                      </span>
                    )}
                    {isCompleted && (
                      <span className="px-3 py-1 bg-green-500 text-white text-xs font-medium rounded-full">
                        Completed
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div> */}

      {/* Live Logs */}
      {logs.length > 0 && (
        <div className="bg-gray-900 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Live Logs ({logs.length} lines)</h2>
            <button
              onClick={() => setLogs([])}
              className="text-m text-gray-400 hover:text-white transition-colors"
            >
              Clear Logs
            </button>
          </div>
          <div className="bg-black rounded p-4 h-96 overflow-y-auto font-mono text-base space-y-0">
            {logs.map((line, index) => (
              <div key={index} className="text-gray-600">
                {line}
              </div>
            ))}
            {workflowStatus?.running && (
              <div className="text-blue-400 animate-pulse">▌</div>
            )}
          </div>
        </div>
      )}

      {/* Information */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-yellow-900 font-semibold mb-2">Important Notes</h3>
            <ul className="space-y-1 text-sm text-yellow-800">
              <li>• The complete workflow may take a few minutes depending on the number of domains</li>
              <li>• Downloaded domains are stored in <code className="bg-yellow-100 px-1 rounded">Domain_Downloads/</code></li>
              <li>• Filtered results are saved in <code className="bg-yellow-100 px-1 rounded">Output/</code> directory</li>
              <li>• Screenshots are captured only for active domains with content changes</li>
              <li>• The workflow runs automatically but can be triggered manually here</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Workflow Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Play className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className="text-lg font-semibold text-gray-900">
                {workflowStatus?.running ? 'Running' : 'Idle'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Last Run</p>
              <p className="text-lg font-semibold text-gray-900">N/A</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Duration</p>
              <p className="text-lg font-semibold text-gray-900">~20 min</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Steps</p>
              <p className="text-lg font-semibold text-gray-900">4 Total</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowManagement;