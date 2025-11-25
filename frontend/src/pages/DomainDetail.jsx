import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  ExternalLink, 
  Save, 
  Trash2,
  Clock,
  Image as ImageIcon,
  FileText,
  TrendingUp,
  Shield,
  Server,
  AlertTriangle,
  Award,
  RefreshCw
} from 'lucide-react';
import { 
  getDomain, 
  getDomainHistory, 
  updateDomain, 
  deleteDomain, 
  getScreenshots, 
  getScreenshotUrl, 
  captureScreenshot,
  getDomainProfile,
  generateDomainProfile,
  addToIgnoreList
} from '../api/api';
import { format } from 'date-fns';

const DomainDetail = () => {
  const { domain } = useParams();
  const navigate = useNavigate();
  const [domainData, setDomainData] = useState(null);
  const [history, setHistory] = useState([]);
  const [screenshots, setScreenshots] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [notes, setNotes] = useState('');
  const [riskLevel, setRiskLevel] = useState('');
  const [saving, setSaving] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [generatingProfile, setGeneratingProfile] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [addingToIgnore, setAddingToIgnore] = useState(false);

  useEffect(() => {
    loadDomainData();
  }, [domain]);

  const loadDomainData = async () => {
    setLoading(true);
    try {
      const [domainResult, historyResult, screenshotsResult] = await Promise.all([
        getDomain(domain),
        getDomainHistory(domain),
        getScreenshots(domain)
      ]);
      
      setDomainData(domainResult);
      setNotes(domainResult.notes || '');
      setRiskLevel(domainResult.risk_level || '');
      setHistory(historyResult.history || []);
      setScreenshots(screenshotsResult.screenshots || []);
      
      // Try to load profile
      loadProfile();
    } catch (error) {
      console.error('Failed to load domain data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProfile = async () => {
    setProfileError(null);
    try {
      const profileData = await getDomainProfile(domain);
      setProfile(profileData);
    } catch (error) {
      if (error.response?.status === 404) {
        setProfileError('no_profile');
      } else {
        console.error('Failed to load profile:', error);
        setProfileError('error');
      }
    }
  };

  const handleGenerateProfile = async () => {
    setGeneratingProfile(true);
    try {
      await generateDomainProfile(domain);
      alert('Profile generation started! It will be available in a few moments.');
      // Try to reload profile after delay
      setTimeout(() => {
        loadProfile();
        setGeneratingProfile(false);
      }, 10000); // Wait 10 seconds before checking
    } catch (error) {
      console.error('Failed to generate profile:', error);
      alert('Failed to generate profile: ' + (error.response?.data?.detail || error.message));
      setGeneratingProfile(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateDomain(domain, {
        notes,
        risk_level: riskLevel || 'unknown'
      });
      await loadDomainData();
      alert('Changes saved successfully!');
    } catch (error) {
      console.error('Failed to save changes:', error);
      alert('Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete ${domain}?`)) {
      try {
        await deleteDomain(domain);
        navigate('/domains');
      } catch (error) {
        console.error('Failed to delete domain:', error);
        alert('Failed to delete domain');
      }
    }
  };

  const handleCaptureScreenshot = async () => {
    setCapturing(true);
    try {
      await captureScreenshot(domain);
      alert('Screenshot capture initiated! It will appear in a few moments.');
      // Reload screenshots after a short delay
      setTimeout(async () => {
        const screenshotsResult = await getScreenshots(domain);
        setScreenshots(screenshotsResult.screenshots || []);
        setCapturing(false);
      }, 5000);
    } catch (error) {
      console.error('Failed to capture screenshot:', error);
      alert('Failed to capture screenshot: ' + (error.response?.data?.detail || error.message));
      setCapturing(false);
    }
  };


  // Add domain to the ignore list
  const handleAddToIgnoreList = async () => {
    if (window.confirm(`Are you sure you want to add ${domain} to the ignore list?\n\nThis domain will be excluded from future scans.`)) {
      setAddingToIgnore(true);
      try {
        const result = await addToIgnoreList(domain);
        alert(result.message || 'Domain added to ignore list successfully!');
      } catch (error) {
        console.error('Failed to add to ignore list:', error);
        alert('Failed to add domain to ignore list: ' + (error.response?.data?.detail || error.message));
      } finally {
        setAddingToIgnore(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!domainData) {
    return (
      <div className="p-6">
        <p className="text-red-600">Domain not found</p>
        <Link to="/domains" className="text-[#ED0000] hover:underline mt-4 inline-block">
          ← Back to Domain Explorer
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="domain-detail">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/domains" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{domain}</h1>
            <div className="flex items-center gap-3 mt-2">
              {domainData.is_active ? (
                <span className="status-badge active">🟢 Active</span>
              ) : (
                <span className="status-badge inactive">⚪ Inactive</span>
              )}
              {domainData.content_changed && (
                <span className="status-badge changed">⚠️ Content Changed</span>
              )}
              {domainData.has_profile && (
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                  📋 Has Profile
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex gap-2">

          {/* open domain link button */}
          <a
            href={`https://${domain}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Open Domain
          </a>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] disabled:bg-gray-400 transition-colors"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            onClick={handleDelete}
            className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
          <button
            onClick={handleAddToIgnoreList}
            disabled={addingToIgnore}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-200 disabled:bg-gray-400 transition-colors"
            title="Add to ignore list"
          >
            <span className="text-lg">🚫</span>
            {addingToIgnore ? 'Adding...' : 'Ignore'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex gap-1 px-6">
            {[
              { id: 'overview', label: 'Overview', icon: FileText },
              { id: 'profile', label: 'Security Profile', icon: Shield },
              { id: 'history', label: 'History Timeline', icon: Clock },
              { id: 'screenshots', label: 'Screenshots', icon: ImageIcon },
              { id: 'analysis', label: 'Pattern Analysis', icon: TrendingUp }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-[#ED0000] text-[#ED0000] font-medium'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Domain</label>
                  <p className="text-lg font-mono bg-gray-50 p-3 rounded">{domainData.domain}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                  <p className="text-lg">
                    {domainData.is_active ? (
                      <span className="status-badge active">🟢 Active</span>
                    ) : (
                      <span className="status-badge inactive">⚪ Inactive</span>
                    )}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">First Seen</label>
                  <p className="text-gray-900">{domainData.first_seen && domainData.first_seen !== '' ? format(new Date(domainData.first_seen), 'PPpp') : 'Unknown'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Last Checked</label>
                  <p className="text-gray-900">{domainData.last_checked && domainData.last_checked !== '' ? format(new Date(domainData.last_checked), 'PPpp') : 'Unknown'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <p className="text-gray-900">{domainData.category || 'Not categorized'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Content Hash</label>
                  <p className="text-xs font-mono bg-gray-50 p-2 rounded break-all">
                    {domainData.content_hash || 'N/A'}
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Risk Level</label>
                <select
                  value={riskLevel || 'unknown'}
                  onChange={(e) => setRiskLevel(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ED0000]"
                >
                  <option value="unknown">Unknown</option>
                  <option value="low">Low Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="high">High Risk</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={6}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ED0000]"
                  placeholder="Add notes about this domain..."
                />
              </div>
            </div>
          )}

          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              {profileError === 'no_profile' ? (
                <div className="text-center py-12">
                  <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No Security Profile Available</h3>
                  <p className="text-gray-600 mb-6">Generate a comprehensive security profile for this domain</p>
                  <button
                    onClick={handleGenerateProfile}
                    disabled={generatingProfile}
                    className="flex items-center gap-2 px-6 py-3 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] disabled:bg-gray-400 transition-colors mx-auto"
                  >
                    <RefreshCw className={`w-5 h-5 ${generatingProfile ? 'animate-spin' : ''}`} />
                    {generatingProfile ? 'Generating Profile...' : 'Generate Security Profile'}
                  </button>
                </div>
              ) : profileError === 'error' ? (
                <div className="text-center py-12">
                  <AlertTriangle className="w-16 h-16 text-red-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Profile</h3>
                  <p className="text-gray-600 mb-6">There was an error loading the security profile</p>
                  <button
                    onClick={loadProfile}
                    className="px-6 py-3 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] transition-colors"
                  >
                    Retry
                  </button>
                </div>
              ) : profile && profile.summary ? (
                <div className="space-y-6">
                  {/* Action Bar */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Award className="w-4 h-4" />
                      <span>Enriched Profile Data</span>
                    </div>
                    <button
                      onClick={handleGenerateProfile}
                      disabled={generatingProfile}
                      className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:bg-gray-200 transition-colors text-sm"
                    >
                      <RefreshCw className={`w-4 h-4 ${generatingProfile ? 'animate-spin' : ''}`} />
                      {generatingProfile ? 'Regenerating...' : 'Regenerate Profile'}
                    </button>
                  </div>

                  {/* Risk Indicators */}
                  {profile.summary.risk_indicators && profile.summary.risk_indicators.length > 0 && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <h3 className="text-lg font-semibold text-red-900 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5" />
                        Risk Indicators ({profile.summary.risk_indicators.length})
                      </h3>
                      <ul className="space-y-2">
                        {profile.summary.risk_indicators.map((indicator, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-red-800">
                            <span className="text-red-500 mt-1">⚠️</span>
                            <span>{indicator}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Security Analysis */}
                  {profile.summary.security_analysis && (
                    <div className="p-6 bg-white border border-gray-200 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Shield className="w-5 h-5" />
                        Security Analysis
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center p-4 bg-red-50 rounded-lg">
                          <div className="text-3xl font-bold text-red-600">
                            {profile.summary.security_analysis.flagged_as_malicious || 0}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">Malicious</div>
                        </div>
                        <div className="text-center p-4 bg-orange-50 rounded-lg">
                          <div className="text-3xl font-bold text-orange-600">
                            {profile.summary.security_analysis.flagged_as_suspicious || 0}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">Suspicious</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                          <div className="text-3xl font-bold text-green-600">
                            {profile.summary.security_analysis.clean_ratings || 0}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">Clean</div>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <div className="text-3xl font-bold text-gray-600">
                            {profile.summary.security_analysis.unrated || 0}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">Unrated</div>
                        </div>
                      </div>
                      <p className="text-sm text-gray-500 mt-4 text-center">
                        Total security engines checked: {profile.summary.security_analysis.total_engines || 0}
                      </p>
                    </div>
                  )}

                  {/* Infrastructure */}
                  {profile.summary.infrastructure && (
                    <div className="p-6 bg-white border border-gray-200 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Server className="w-5 h-5" />
                        Infrastructure
                      </h3>
                      <div className="space-y-4">
                        {profile.summary.infrastructure.ip_addresses && profile.summary.infrastructure.ip_addresses.length > 0 && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">IP Addresses</label>
                            <div className="flex flex-wrap gap-2">
                              {profile.summary.infrastructure.ip_addresses.map((ip, idx) => (
                                <span key={idx} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-mono">
                                  {ip}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {profile.summary.infrastructure.nameservers && profile.summary.infrastructure.nameservers.length > 0 && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Name Servers</label>
                            <div className="space-y-1">
                              {profile.summary.infrastructure.nameservers.map((ns, idx) => (
                                <div key={idx} className="text-sm font-mono bg-gray-50 p-2 rounded">{ns}</div>
                              ))}
                            </div>
                          </div>
                        )}
                        {profile.summary.infrastructure.hosting_provider && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Hosting Provider</label>
                            <p className="text-gray-900">{profile.summary.infrastructure.hosting_provider}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* SSL Certificate */}
                  {profile.summary.certificate_info && (
                    <div className="p-6 bg-white border border-gray-200 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">SSL Certificate</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Has SSL</label>
                          {profile.summary.certificate_info.has_ssl ? (
                            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                              ✓ Yes
                            </span>
                          ) : (
                            <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                              ✗ No
                            </span>
                          )}
                        </div>
                        {profile.summary.certificate_info.issuer && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Issuer</label>
                            <p className="text-gray-900">{profile.summary.certificate_info.issuer}</p>
                          </div>
                        )}
                        {profile.summary.certificate_info.valid_from && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Valid From</label>
                            <p className="text-gray-900">{profile.summary.certificate_info.valid_from}</p>
                          </div>
                        )}
                        {profile.summary.certificate_info.alternative_names && profile.summary.certificate_info.alternative_names.length > 0 && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Alternative Names</label>
                            <div className="space-y-1">
                              {profile.summary.certificate_info.alternative_names.map((name, idx) => (
                                <div key={idx} className="text-sm font-mono bg-gray-50 p-2 rounded">{name}</div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Domain Dates */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {profile.summary.creation_date && (
                      <div className="p-4 bg-white border border-gray-200 rounded-lg">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Creation Date</label>
                        <p className="text-lg font-semibold text-gray-900">{profile.summary.creation_date}</p>
                      </div>
                    )}
                    {profile.summary.expiry_date && (
                      <div className="p-4 bg-white border border-gray-200 rounded-lg">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Expiry Date</label>
                        <p className="text-lg font-semibold text-gray-900">{profile.summary.expiry_date}</p>
                      </div>
                    )}
                  </div>

                  {/* Subdomains */}
                  {profile.summary.subdomains && profile.summary.subdomains.length > 0 && (
                    <div className="p-6 bg-white border border-gray-200 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Subdomains ({profile.summary.subdomains.length})
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {profile.summary.subdomains.map((subdomain, idx) => (
                          <span key={idx} className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm font-mono">
                            {subdomain}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <div className="spinner"></div>
                </div>
              )}
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Scan History ({history.length} entries)</h3>
              <div className="space-y-3">
                {history.map((entry, index) => (
                  <div key={index} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                    <div className="w-2 h-2 mt-2 rounded-full bg-[#ED0000]"></div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900">
                          {entry.checked_at && entry.checked_at !== '' ? format(new Date(entry.checked_at), 'PPpp') : 'Unknown'}
                        </p>
                        {entry.is_active ? (
                          <span className="status-badge active">🟢 Active</span>
                        ) : (
                          <span className="status-badge inactive">⚪ Inactive</span>
                        )}
                      </div>
                      <div className="mt-2 space-y-1 text-sm text-gray-600">
                        {entry.content_changed && (
                          <p className="text-orange-600 font-medium">⚠️ Content changed detected</p>
                        )}
                        {entry.screenshot_taken && (
                          <p className="text-blue-600">📸 Screenshot captured</p>
                        )}
                        {entry.content_hash && (
                          <p className="text-xs font-mono bg-white p-2 rounded mt-2">
                            Hash: {entry.content_hash.substring(0, 32)}...
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {history.length === 0 && (
                  <p className="text-center text-gray-500 py-8">No history entries</p>
                )}
              </div>
            </div>
          )}

          {/* Screenshots Tab */}
          {activeTab === 'screenshots' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Screenshots ({screenshots.length})
                </h3>
                <button
                  onClick={handleCaptureScreenshot}
                  disabled={capturing || !domainData.is_active}
                  className="flex items-center gap-2 px-4 py-2 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] disabled:bg-gray-400 transition-colors"
                >
                  <ImageIcon className="w-4 h-4" />
                  {capturing ? 'Capturing...' : 'Capture New Screenshot'}
                </button>
              </div>
              
              {!domainData.is_active && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-yellow-800">
                    ⚠️ This domain is inactive. Screenshots can only be captured for active domains.
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {screenshots.map((screenshot, index) => (
                  <div key={index} className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                    <a 
                      href={getScreenshotUrl(domain, screenshot.filename)} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="block"
                    >
                      <img
                        src={getScreenshotUrl(domain, screenshot.filename)}
                        alt={`Screenshot ${screenshot.timestamp}`}
                        className="w-full h-48 object-cover cursor-pointer hover:opacity-90 transition-opacity"
                      />
                    </a>
                    <div className="p-3">
                      <p className="text-sm font-medium text-gray-900">
                        {screenshot.timestamp}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Size: {(screenshot.size / 1024).toFixed(2)} KB
                      </p>
                      <a 
                        href={getScreenshotUrl(domain, screenshot.filename)} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-[#ED0000] hover:underline mt-2 inline-flex items-center gap-1"
                      >
                        View Full Size
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                ))}
                {screenshots.length === 0 && (
                  <div className="col-span-full text-center py-12 bg-gray-50 rounded-lg">
                    <ImageIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">No screenshots available for this domain</p>
                    {domainData.is_active && (
                      <button
                        onClick={handleCaptureScreenshot}
                        disabled={capturing}
                        className="px-6 py-3 bg-[#ED0000] text-white rounded-lg hover:bg-[#C70000] disabled:bg-gray-400 transition-colors"
                      >
                        {capturing ? 'Capturing...' : 'Capture First Screenshot'}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Pattern Analysis Tab */}
          {activeTab === 'analysis' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Pattern Matches</h3>
                <div className="space-y-3">
                  {domainData.domain.includes('absa') && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="font-medium text-red-900">🔴 Contains "absa"</p>
                      <p className="text-sm text-red-700 mt-1">High risk: Direct brand mention</p>
                    </div>
                  )}
                  {domainData.domain.endsWith('.co.za') && (
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="font-medium text-blue-900">🔵 South African TLD (.co.za)</p>
                      <p className="text-sm text-blue-700 mt-1">Targets South African users</p>
                    </div>
                  )}
                  {domainData.domain.endsWith('.africa') && (
                    <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                      <p className="font-medium text-purple-900">🟣 African TLD (.africa)</p>
                      <p className="text-sm text-purple-700 mt-1">Regional targeting</p>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Domain Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Domain Length</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{domainData.domain.length}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Days Active</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {Math.floor((new Date() - new Date(domainData.first_seen)) / (1000 * 60 * 60 * 24))}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DomainDetail;