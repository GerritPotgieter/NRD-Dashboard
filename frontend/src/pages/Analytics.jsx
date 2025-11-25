import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { Download, TrendingUp, Calendar } from 'lucide-react';
import { getStats, getCategoryStats, getTimeline } from '../api/api';

const Analytics = () => {
  const [stats, setStats] = useState(null);
  const [categoryStats, setCategoryStats] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [timeRange, setTimeRange] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const [statsData, categoriesData, timelineData] = await Promise.all([
        getStats(),
        getCategoryStats(),
        getTimeline(timeRange)
      ]);

      setStats(statsData);
      
      const categoryArray = Object.entries(categoriesData.categories || {}).map(([name, count]) => ({
        name: name || 'Uncategorized',
        value: count
      }));
      setCategoryStats(categoryArray);
      
      setTimeline(timelineData.timeline || []);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
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
    <div className="p-6 space-y-6" data-testid="analytics">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics & Reports</h1>
          <p className="text-gray-600 mt-1">Detailed insights and trend analysis</p>
        </div>
        <div className="flex gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ED0000]"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600 font-medium">Total Domains</p>
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats?.total || 0}</p>
          <p className="text-xs text-gray-500 mt-2">All tracked domains</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600 font-medium">Active Rate</p>
            <div className="text-2xl">🟢</div>
          </div>
          <p className="text-3xl font-bold text-green-600">
            {stats?.total > 0 ? ((stats.active / stats.total) * 100).toFixed(1) : 0}%
          </p>
          <p className="text-xs text-gray-500 mt-2">{stats?.active || 0} active domains</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600 font-medium">High Risk</p>
            <div className="text-2xl">🔴</div>
          </div>
          <p className="text-3xl font-bold text-red-600">{stats?.risk_high || 0}</p>
          <p className="text-xs text-gray-500 mt-2">Require attention</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600 font-medium">Golden Matches</p>
            <div className="text-2xl">🛡️</div>
          </div>
          <p className="text-3xl font-bold text-[#ED0000]">{stats?.golden_matches || 0}</p>
          <p className="text-xs text-gray-500 mt-2">Priority threats</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Discovery Timeline</h2>
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

        {/* Category Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryStats}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {categoryStats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Level Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Level Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={[
                { level: 'High', count: stats?.risk_high || 0, fill: '#EF4444' },
                { level: 'Medium', count: stats?.risk_medium || 0, fill: '#F59E0B' },
                { level: 'Low', count: stats?.risk_low || 0, fill: '#3B82F6' }
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="level" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" name="Domains">
                {[{fill: '#EF4444'}, {fill: '#F59E0B'}, {fill: '#3B82F6'}].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Status Overview</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={[
                { status: 'Active', count: stats?.active || 0 },
                { status: 'Inactive', count: stats?.inactive || 0 },
                { status: 'Changed', count: stats?.changed || 0 },
                { status: 'With Profile', count: stats?.with_profiles || 0 }
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="status" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#ED0000" name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Detection Rate</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {timeline.length > 0 ? (timeline.reduce((sum, item) => sum + item.count, 0) / timeline.length).toFixed(1) : 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">avg/day</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Change Rate</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {stats?.total > 0 ? ((stats.changed / stats.total) * 100).toFixed(1) : 0}%
            </p>
            <p className="text-xs text-gray-500 mt-1">content changes</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Profile Coverage</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {stats?.total > 0 ? ((stats.with_profiles / stats.total) * 100).toFixed(1) : 0}%
            </p>
            <p className="text-xs text-gray-500 mt-1">documented threats</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Risk Score</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {stats?.total > 0 ? (
                ((stats.risk_high * 3 + stats.risk_medium * 2 + stats.risk_low) / stats.total).toFixed(1)
              ) : 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">out of 3.0</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;