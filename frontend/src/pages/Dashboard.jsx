import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  FileCheck,
  Shield,
  Clock,
  ExternalLink
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  BarChart, 
  Bar, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { getStats, getRecentActivity, getRecentChanges, getCategoryStats, getTimeline, syncDomainProfiles } from '../api/api';
import { format } from 'date-fns';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [recentChanges, setRecentChanges] = useState([]);
  const [categoryStats, setCategoryStats] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [profilesSynced, setProfilesSynced] = useState(false);

  useEffect(() => {
    // Sync profiles once on mount
    if (!profilesSynced) {
      syncProfiles();
    }
    loadDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const syncProfiles = async () => {
    try {
      await syncDomainProfiles();
      setProfilesSynced(true);
      console.log('Domain profiles synced successfully');
    } catch (error) {
      console.error('Failed to sync profiles:', error);
    }
  };

  const loadDashboardData = async () => {
    try {
      const [statsData, activityData, changesData, categoriesData, timelineData] = await Promise.all([
        getStats(),
        getRecentActivity(20),
        getRecentChanges(10),
        getCategoryStats(),
        getTimeline(30)
      ]);

      setStats(statsData);
      setRecentActivity(activityData.recent_activity || []);
      setRecentChanges(changesData.recent_changes || []);
      
      // Format category data for charts
      const categoryArray = Object.entries(categoriesData.categories || {}).map(([name, count]) => ({
        name: name || 'Uncategorized',
        value: count
      }));
      setCategoryStats(categoryArray);
      
      setTimeline(timelineData.timeline || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner"></div>
      </div>
    );
  }

  const COLORS = ['#ED0000', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6'];

  return (
    <div className="p-6 space-y-6" data-testid="dashboard">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Executive Summary</h1>
        <p className="text-gray-600 mt-1">Newly Registered Domain Monitoring Dashboard</p>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="metric-card" data-testid="metric-total-domains">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Total Domains</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats?.total || 0}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileCheck className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            Total tracked domains
          </div>
        </div>

        <div className="metric-card" data-testid="metric-active-domains">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Active Domains</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{stats?.active || 0}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            {stats?.total > 0 ? `${((stats.active / stats.total) * 100).toFixed(1)}% of total` : '0%'}
          </div>
        </div>

        <div className="metric-card" data-testid="metric-inactive-domains">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Inactive Domains</p>
              <p className="text-3xl font-bold text-gray-600 mt-2">{stats?.inactive || 0}</p>
            </div>
            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
              <XCircle className="w-6 h-6 text-gray-600" />
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            Not responding
          </div>
        </div>

        <div className="metric-card" data-testid="metric-content-changes">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Content Changes</p>
              <p className="text-3xl font-bold text-orange-600 mt-2">{stats?.changed || 0}</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            Detected changes
          </div>
        </div>

        <div className="metric-card" data-testid="metric-golden-matches">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Golden Matches</p>
              <p className="text-3xl font-bold text-[#ED0000] mt-2">{stats?.golden_matches || 0}</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-[#ED0000]" />
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            High priority threats
          </div>
        </div>

        <div className="metric-card" data-testid="metric-threat-profiles">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Threat Profiles</p>
              <p className="text-3xl font-bold text-purple-600 mt-2">{stats?.with_profiles || 0}</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            Documented threats
          </div>
        </div>

        <div className="metric-card bg-red-50 border border-red-200" data-testid="metric-high-risk">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-red-700 font-medium">High Risk</p>
              <p className="text-3xl font-bold text-red-700 mt-2">{stats?.risk_high || 0}</p>
            </div>
            <div className="w-12 h-12 bg-red-200 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-700" />
            </div>
          </div>
          <div className="mt-3 text-xs text-red-600">
            Immediate attention required
          </div>
        </div>

        <div className="metric-card bg-orange-50 border border-orange-200" data-testid="metric-medium-risk">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-orange-700 font-medium">Medium Risk</p>
              <p className="text-3xl font-bold text-orange-700 mt-2">{stats?.risk_medium || 0}</p>
            </div>
            <div className="w-12 h-12 bg-orange-200 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-orange-700" />
            </div>
          </div>
          <div className="mt-3 text-xs text-orange-600">
            Monitor closely
          </div>
        </div>
      </div>

       {/* Recent Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recently Detected */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recently Detected</h2>
            <Link to="/domains" className="text-sm text-[#ED0000] hover:text-[#C70000] font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            {recentActivity.slice(0, 10).map((domain, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex-1 min-w-0">
                  <Link to={`/domains/${domain.domain}`} className="text-sm font-medium text-gray-900 hover:text-[#ED0000] truncate block">
                    {domain.domain}
                  </Link>
                  <p className="text-xs text-gray-500 mt-1">
                    First seen: {domain.first_seen && domain.first_seen !== '' ? format(new Date(domain.first_seen), 'MMM dd, yyyy HH:mm') : 'Unknown'}
                  </p>
                </div>
                <div className="ml-3">
                  {domain.is_active ? (
                    <span className="status-badge active">
                      🟢 Active
                    </span>
                  ) : (
                    <span className="status-badge inactive">
                      ⚪ Inactive
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Content Changes */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Content Changes</h2>
            <Link to="/domains?changed=true" className="text-sm text-[#ED0000] hover:text-[#C70000] font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            {recentChanges.map((domain, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors">
                <div className="flex-1 min-w-0">
                  <Link to={`/domains/${domain.domain}`} className="text-sm font-medium text-gray-900 hover:text-[#ED0000] truncate block">
                    {domain.domain}
                  </Link>
                  <p className="text-xs text-gray-500 mt-1">
                    Last checked: {domain.last_checked && domain.last_checked !== '' ? format(new Date(domain.last_checked), 'MMM dd, yyyy HH:mm') : 'Unknown'}
                  </p>
                </div>
                <div className="ml-3">
                  <span className="status-badge changed">
                    ⚠️ Changed
                  </span>
                </div>
              </div>
            ))}
            {recentChanges.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">No recent changes</p>
            )}
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline Chart */}
        <div className="chart-container">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Discovery Timeline (30 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#ED0000" strokeWidth={2} name="New Domains" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Activity Distribution */}
        <div className="chart-container">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Activity Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Active', value: stats?.active || 0 },
                  { name: 'Inactive', value: stats?.inactive || 0 }
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                <Cell fill="#10B981" />
                <Cell fill="#6B7280" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Category Distribution */}
        <div className="chart-container">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Domains by Category</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categoryStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" name="Count">
                {categoryStats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Level Distribution */}
        <div className="chart-container">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Level Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={[
                { level: 'High', count: stats?.risk_high || 0 },
                { level: 'Medium', count: stats?.risk_medium || 0 },
                { level: 'Low', count: stats?.risk_low || 0 }
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="level" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" name="Domains">
                <Cell fill="#EF4444" />
                <Cell fill="#F59E0B" />
                <Cell fill="#3B82F6" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
