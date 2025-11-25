import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  Download, 
  RefreshCw,
  ExternalLink,
  Eye,
  FileText,
  Trash2,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { getDomains, exportToCSV, exportToJSON } from '../api/api';
import { format } from 'date-fns';

const DomainExplorer = () => {
  // Load saved state from localStorage or use defaults
  const loadSavedState = () => {
    try {
      const saved = localStorage.getItem('domainExplorerState');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (error) {
      console.error('Failed to load saved state:', error);
    }
    return null;
  };

  const savedState = loadSavedState();

  const [domains, setDomains] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState(savedState?.searchTerm || '');
  const [filters, setFilters] = useState(savedState?.filters || {
    active_only: true,
    changed_only: false,
    with_profile_only: false,
    category: '',
    risk_level: ''
  });
  const [pagination, setPagination] = useState(savedState?.pagination || {
    limit: 50,
    offset: 0
  });
  const [sortConfig, setSortConfig] = useState(savedState?.sortConfig || {
    sort_by: 'first_seen',
    sort_order: 1
  });

  // Save state to localStorage whenever it changes
  useEffect(() => {
    const stateToSave = {
      searchTerm,
      filters,
      pagination,
      sortConfig,
      scrollPosition: window.scrollY
    };
    localStorage.setItem('domainExplorerState', JSON.stringify(stateToSave));
  }, [searchTerm, filters, pagination, sortConfig]);

  // Restore scroll position on mount
  useEffect(() => {
    if (savedState?.scrollPosition) {
      setTimeout(() => {
        window.scrollTo(0, savedState.scrollPosition);
      }, 100);
    }
  }, []);

  useEffect(() => {
    loadDomains();
  }, [filters, pagination, sortConfig]);

  const loadDomains = async () => {
    setLoading(true);
    try {
      const params = {
        ...filters,
        ...pagination,
        ...sortConfig,
        search: searchTerm || undefined
      };
      const data = await getDomains(params);
      setDomains(data.domains || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Failed to load domains:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination({ ...pagination, offset: 0 });
    loadDomains();
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value });
    setPagination({ ...pagination, offset: 0 });
    // Save scroll position before filter change
    const stateToSave = {
      searchTerm,
      filters: { ...filters, [key]: value },
      pagination: { ...pagination, offset: 0 },
      sortConfig,
      scrollPosition: 0 // Reset scroll on filter change
    };
    localStorage.setItem('domainExplorerState', JSON.stringify(stateToSave));
  };

  const handleSort = (column) => {
    setSortConfig({
      sort_by: column,
      sort_order: sortConfig.sort_by === column && sortConfig.sort_order === -1 ? 1 : -1
    });
  };

  const handleExport = async (type) => {
    try {
      const blob = type === 'csv' 
        ? await exportToCSV(filters) 
        : await exportToJSON(filters);
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `domains_export.${type}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const nextPage = () => {
    if (pagination.offset + pagination.limit < total) {
      setPagination({ ...pagination, offset: pagination.offset + pagination.limit });
    }
  };

  const prevPage = () => {
    if (pagination.offset > 0) {
      setPagination({ ...pagination, offset: Math.max(0, pagination.offset - pagination.limit) });
    }
  };

  const currentPage = Math.floor(pagination.offset / pagination.limit) + 1;
  const totalPages = Math.ceil(total / pagination.limit);

  const getRiskLevelColor = (riskLevel) => {
    switch(riskLevel) {
      case 'critical': return 'bg-red-600 text-white';
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  const getRiskLevelLabel = (riskLevel) => {
    switch(riskLevel) {
      case 'critical': return '🔴 Critical';
      case 'high': return '🟠 High';
      case 'medium': return '🟡 Medium';
      case 'low': return '🟢 Low';
      default: return '⚪ Unknown';
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="domain-explorer">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Domain Explorer</h1>
          <p className="text-gray-600 mt-1">Browse and manage monitored domains</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            data-testid="export-csv-btn"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            data-testid="export-json-btn"
          >
            <Download className="w-4 h-4" />
            Export JSON
          </button>
          <button
            onClick={loadDomains}
            className="flex items-center gap-2 px-4 py-2 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] transition-colors"
            data-testid="refresh-btn"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search domains..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ED0000]"
              data-testid="search-input"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] transition-colors"
            data-testid="search-btn"
          >
            Search
          </button>
        </form>

        {/* Filter Toggles */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleFilterChange('active_only', !filters.active_only)}
            className={`px-4 py-2 rounded-lg border transition-colors ${
              filters.active_only 
                ? 'bg-green-50 border-green-500 text-green-700' 
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            data-testid="filter-active-btn"
          >
            {filters.active_only && '✓ '}Active Only
          </button>
          <button
            onClick={() => handleFilterChange('changed_only', !filters.changed_only)}
            className={`px-4 py-2 rounded-lg border transition-colors ${
              filters.changed_only 
                ? 'bg-orange-50 border-orange-500 text-orange-700' 
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            data-testid="filter-changed-btn"
          >
            {filters.changed_only && '✓ '}Changed Only
          </button>
          <button
            onClick={() => handleFilterChange('with_profile_only', !filters.with_profile_only)}
            className={`px-4 py-2 rounded-lg border transition-colors ${
              filters.with_profile_only 
                ? 'bg-purple-50 border-purple-500 text-purple-700' 
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            data-testid="filter-profile-btn"
          >
            {filters.with_profile_only && '✓ '}With Profile
          </button>

          {/* Risk Level Filter */}
          <select
            value={filters.risk_level}
            onChange={(e) => handleFilterChange('risk_level', e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ED0000]"
            data-testid="filter-risk-select"
          >
            <option value="">All Risk Levels</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>

          {/* Category Filter */}
          <select
            value={filters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ED0000]"
            data-testid="filter-category-select"
          >
            <option value="">All Categories</option>
            <option value="golden">Golden Matches</option>
            <option value="coza">.co.za Only</option>
            <option value="absa">absa Only</option>
            <option value="africa">.africa Only</option>
            <option value="pattern">Pattern Matches</option>
          </select>
        </div>

        {/* Results Count */}
        <div className="text-sm text-gray-600">
          Showing {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, total)} of {total} domains
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="spinner"></div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="data-table" data-testid="domains-table">
                <thead>
                  <tr>
                    <th className="cursor-pointer hover:bg-gray-100" onClick={() => handleSort('domain')}>
                      Domain {sortConfig.sort_by === 'domain' && (sortConfig.sort_order === -1 ? '↓' : '↑')}
                    </th>
                    <th className="cursor-pointer hover:bg-gray-100" onClick={() => handleSort('is_active')}>
                      Status {sortConfig.sort_by === 'is_active' && (sortConfig.sort_order === -1 ? '↓' : '↑')}
                    </th>
                    <th>Category</th>
                    <th className="cursor-pointer hover:bg-gray-100" onClick={() => handleSort('first_seen')}>
                      First Seen {sortConfig.sort_by === 'first_seen' && (sortConfig.sort_order === -1 ? '↓' : '↑')}
                    </th>
                    <th className="cursor-pointer hover:bg-gray-100" onClick={() => handleSort('last_checked')}>
                      Last Checked {sortConfig.sort_by === 'last_checked' && (sortConfig.sort_order === -1 ? '↓' : '↑')}
                    </th>
                    <th>Risk Level</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {domains.map((domain, index) => (
                    <tr key={index} data-testid={`domain-row-${index}`}>
                      <td>
                        <div className="flex items-center gap-2">
                          <Link 
                            to={`/domains/${domain.domain}`} 
                            className="text-sm font-medium text-gray-900 hover:text-[#ED0000]"
                          >
                            {domain.domain}
                          </Link>
                          {domain.has_profile && (
                            <span className="text-purple-600" title="Has Profile">📋</span>
                          )}
                        </div>
                      </td>
                      <td>
                        {domain.is_active ? (
                          <span className="status-badge active">🟢 Active</span>
                        ) : (
                          <span className="status-badge inactive">⚪ Inactive</span>
                        )}
                        {domain.content_changed && (
                          <span className="ml-2 text-orange-600" title="Content Changed">⚠️</span>
                        )}
                      </td>
                      <td>
                        {domain.category ? (
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                            {domain.category}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-xs">-</span>
                        )}
                      </td>
                      <td className="text-sm text-gray-600">
                        {domain.first_seen && domain.first_seen !== '' ? format(new Date(domain.first_seen), 'MM dd, yyyy') : 'Unknown'}
                      </td>
                      <td className="text-sm text-gray-600">
                        {domain.last_checked && domain.last_checked !== '' ? format(new Date(domain.last_checked), 'MM dd, HH:mm') : 'Unknown'}
                      </td>
                      <td>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(domain.risk_level || 'unknown')}`}>
                          {getRiskLevelLabel(domain.risk_level || 'unknown')}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <Link
                            to={`/domains/${domain.domain}`}
                            className="p-2 hover:bg-gray-100 rounded transition-colors"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4 text-gray-600" />
                          </Link>
                          <a
                            href={`https://${domain.domain}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 hover:bg-gray-100 rounded transition-colors"
                            title="Open Domain"
                          >
                            <ExternalLink className="w-4 h-4 text-gray-600" />
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={prevPage}
                  disabled={pagination.offset === 0}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  data-testid="prev-page-btn"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={nextPage}
                  disabled={pagination.offset + pagination.limit >= total}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  data-testid="next-page-btn"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DomainExplorer;
