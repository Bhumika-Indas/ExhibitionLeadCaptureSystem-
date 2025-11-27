'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import BottomNav from '@/components/BottomNav';
import type { Lead } from '@/lib/types';
import { Search, Plus, Building2, User, Phone, Calendar, MessageCircle, Edit3, Trash2, AlertTriangle, Copy, X, SlidersHorizontal } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

export default function LeadsPage() {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filteredLeads, setFilteredLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [exhibitionFilter, setExhibitionFilter] = useState<string>('all');
  const [segmentFilter, setSegmentFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('date_desc');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDuplicatesView, setShowDuplicatesView] = useState(false);
  const [exhibitions, setExhibitions] = useState<any[]>([]);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/auth/login');
      return;
    }

    loadLeads();
    loadExhibitions();
  }, [router]);

  useEffect(() => {
    applyFilters();
  }, [leads, searchQuery, statusFilter, sourceFilter, exhibitionFilter, segmentFilter, priorityFilter, dateFrom, dateTo, sortBy]);

  const loadExhibitions = async () => {
    try {
      const data = await api.getExhibitions();
      setExhibitions(data);
    } catch (error) {
      console.error('Failed to load exhibitions:', error);
    }
  };

  const loadLeads = async () => {
    try {
      const { leads: data } = await api.getLeads({ limit: 100 });
      setLeads(data);
    } catch (error) {
      console.error('Failed to load leads:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...leads];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (lead) =>
          lead.CompanyName?.toLowerCase().includes(query) ||
          lead.PrimaryVisitorName?.toLowerCase().includes(query) ||
          lead.PrimaryVisitorPhone?.includes(query)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((lead) => lead.StatusCode === statusFilter);
    }

    // Source filter
    if (sourceFilter !== 'all') {
      filtered = filtered.filter((lead) => lead.SourceCode === sourceFilter);
    }

    // Exhibition filter
    if (exhibitionFilter !== 'all') {
      filtered = filtered.filter((lead) => lead.ExhibitionId?.toString() === exhibitionFilter);
    }

    // Segment filter
    if (segmentFilter !== 'all') {
      filtered = filtered.filter((lead) => lead.Segment === segmentFilter);
    }

    // Priority filter
    if (priorityFilter !== 'all') {
      filtered = filtered.filter((lead) => lead.Priority === priorityFilter);
    }

    // Date range filter
    if (dateFrom) {
      const fromDate = new Date(dateFrom);
      fromDate.setHours(0, 0, 0, 0);
      filtered = filtered.filter((lead) => new Date(lead.CreatedAt) >= fromDate);
    }
    if (dateTo) {
      const toDate = new Date(dateTo);
      toDate.setHours(23, 59, 59, 999);
      filtered = filtered.filter((lead) => new Date(lead.CreatedAt) <= toDate);
    }

    // Sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date_desc':
          return new Date(b.CreatedAt).getTime() - new Date(a.CreatedAt).getTime();
        case 'date_asc':
          return new Date(a.CreatedAt).getTime() - new Date(b.CreatedAt).getTime();
        case 'name_asc':
          return (a.PrimaryVisitorName || '').localeCompare(b.PrimaryVisitorName || '');
        case 'name_desc':
          return (b.PrimaryVisitorName || '').localeCompare(a.PrimaryVisitorName || '');
        case 'company_asc':
          return (a.CompanyName || '').localeCompare(b.CompanyName || '');
        case 'company_desc':
          return (b.CompanyName || '').localeCompare(a.CompanyName || '');
        case 'priority':
          const priorityOrder: Record<string, number> = { high: 3, medium: 2, low: 1 };
          return (priorityOrder[b.Priority || ''] || 0) - (priorityOrder[a.Priority || ''] || 0);
        default:
          return 0;
      }
    });

    setFilteredLeads(filtered);
  };

  const getStatusColor = (status: string) => {
    const styles: Record<string, string> = {
      new: 'bg-blue-100 text-blue-800',
      confirmed: 'bg-green-100 text-green-800',
      needs_correction: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-purple-100 text-purple-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const clearAllFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setSourceFilter('all');
    setExhibitionFilter('all');
    setSegmentFilter('all');
    setPriorityFilter('all');
    setDateFrom('');
    setDateTo('');
    setSortBy('date_desc');
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (statusFilter !== 'all') count++;
    if (sourceFilter !== 'all') count++;
    if (exhibitionFilter !== 'all') count++;
    if (segmentFilter !== 'all') count++;
    if (priorityFilter !== 'all') count++;
    if (dateFrom) count++;
    if (dateTo) count++;
    if (sortBy !== 'date_desc') count++;
    return count;
  };

  const removeFilter = (filterName: string) => {
    switch (filterName) {
      case 'status': setStatusFilter('all'); break;
      case 'source': setSourceFilter('all'); break;
      case 'exhibition': setExhibitionFilter('all'); break;
      case 'segment': setSegmentFilter('all'); break;
      case 'priority': setPriorityFilter('all'); break;
      case 'dateFrom': setDateFrom(''); break;
      case 'dateTo': setDateTo(''); break;
      case 'sort': setSortBy('date_desc'); break;
    }
  };

  const handleDeleteLead = async (leadId: number) => {
    try {
      // Call delete endpoint (soft delete - marks as inactive, keeps data)
      const response = await fetch(`http://localhost:8000/api/leads/${leadId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Delete failed');
      }

      // Refresh leads list (will not show inactive leads)
      await loadLeads();
      setShowDeleteConfirm(false);
      setSelectedLead(null);
      toast.success('Lead deleted successfully');
    } catch (error) {
      console.error('Failed to delete lead:', error);
      toast.error('Failed to delete lead. Please try again.');
    }
  };

  const confirmDelete = (lead: Lead) => {
    setSelectedLead(lead);
    setShowDeleteConfirm(true);
  };

  if (!isAuthenticated()) {
    return null;
  }

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading leads...</p>
          </div>
        </div>
        <BottomNav />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-4 shadow-md">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-xl font-bold">All Leads</h1>
          <div className="flex gap-2">
            <button
              onClick={() => setShowDuplicatesView(!showDuplicatesView)}
              className="bg-white text-blue-600 p-2 rounded-full hover:bg-blue-50 transition"
              title="View Duplicates"
            >
              <Copy className="w-5 h-5" />
            </button>
            <button
              onClick={() => router.push('/chat')}
              className="bg-white text-blue-600 p-2 rounded-full hover:bg-blue-50 transition"
              title="Add New Lead"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name, company, or phone..."
            className="w-full pl-10 pr-4 py-2 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>

        {/* Filter Toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="mt-3 flex items-center text-sm text-blue-100 hover:text-white transition"
        >
          <SlidersHorizontal className="w-4 h-4 mr-1" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
          {getActiveFilterCount() > 0 && (
            <span className="ml-2 bg-white text-blue-600 text-xs font-bold px-2 py-0.5 rounded-full">
              {getActiveFilterCount()}
            </span>
          )}
        </button>
      </div>

      {/* Active Filter Chips */}
      {getActiveFilterCount() > 0 && (
        <div className="bg-blue-50 border-b border-blue-100 px-4 py-2">
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-xs font-medium text-blue-700">Active Filters:</span>
            {statusFilter !== 'all' && (
              <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs border border-blue-200">
                <span className="text-gray-700">Status: <strong>{statusFilter.replace('_', ' ')}</strong></span>
                <button onClick={() => removeFilter('status')} className="text-blue-600 hover:text-blue-800">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            {sourceFilter !== 'all' && (
              <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs border border-blue-200">
                <span className="text-gray-700">Source: <strong>{sourceFilter}</strong></span>
                <button onClick={() => removeFilter('source')} className="text-blue-600 hover:text-blue-800">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            {exhibitionFilter !== 'all' && (
              <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs border border-blue-200">
                <span className="text-gray-700">Exhibition: <strong>{exhibitions.find(e => e.ExhibitionId.toString() === exhibitionFilter)?.Name || exhibitionFilter}</strong></span>
                <button onClick={() => removeFilter('exhibition')} className="text-blue-600 hover:text-blue-800">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            {segmentFilter !== 'all' && (
              <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs border border-blue-200">
                <span className="text-gray-700">Segment: <strong>{segmentFilter.replace('_', ' ')}</strong></span>
                <button onClick={() => removeFilter('segment')} className="text-blue-600 hover:text-blue-800">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            {priorityFilter !== 'all' && (
              <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs border border-blue-200">
                <span className="text-gray-700">Priority: <strong>{priorityFilter}</strong></span>
                <button onClick={() => removeFilter('priority')} className="text-blue-600 hover:text-blue-800">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            {dateFrom && (
              <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs border border-blue-200">
                <span className="text-gray-700">From: <strong>{format(new Date(dateFrom), 'MMM dd, yyyy')}</strong></span>
                <button onClick={() => removeFilter('dateFrom')} className="text-blue-600 hover:text-blue-800">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            {dateTo && (
              <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs border border-blue-200">
                <span className="text-gray-700">To: <strong>{format(new Date(dateTo), 'MMM dd, yyyy')}</strong></span>
                <button onClick={() => removeFilter('dateTo')} className="text-blue-600 hover:text-blue-800">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            {sortBy !== 'date_desc' && (
              <div className="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs border border-blue-200">
                <span className="text-gray-700">Sort: <strong>{sortBy.replace('_', ' ')}</strong></span>
                <button onClick={() => removeFilter('sort')} className="text-blue-600 hover:text-blue-800">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            <button
              onClick={clearAllFilters}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium underline"
            >
              Clear All
            </button>
          </div>
        </div>
      )}

      {/* Enhanced Filters Panel */}
      {showFilters && (
        <div className="bg-white border-b border-gray-200 px-4 py-4 space-y-4">
          {/* Row 1: Status, Source, Exhibition */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="new">New</option>
                <option value="confirmed">Confirmed</option>
                <option value="needs_correction">Needs Correction</option>
                <option value="in_progress">In Progress</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Source</label>
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Sources</option>
                <option value="employee">Employee</option>
                <option value="qr">QR Code</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Exhibition</label>
              <select
                value={exhibitionFilter}
                onChange={(e) => setExhibitionFilter(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Exhibitions</option>
                {exhibitions.map((exhibition) => (
                  <option key={exhibition.ExhibitionId} value={exhibition.ExhibitionId.toString()}>
                    {exhibition.Name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Row 2: Segment, Priority */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Segment</label>
              <select
                value={segmentFilter}
                onChange={(e) => setSegmentFilter(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Segments</option>
                <option value="decision_maker">Decision Maker</option>
                <option value="influencer">Influencer</option>
                <option value="researcher">Researcher</option>
                <option value="general">General</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Priority</label>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          {/* Row 3: Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Date From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Date To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Row 4: Sort By */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="date_desc">Date (Newest First)</option>
              <option value="date_asc">Date (Oldest First)</option>
              <option value="name_asc">Name (A-Z)</option>
              <option value="name_desc">Name (Z-A)</option>
              <option value="company_asc">Company (A-Z)</option>
              <option value="company_desc">Company (Z-A)</option>
              <option value="priority">Priority (High to Low)</option>
            </select>
          </div>

          {/* Clear Filters Button */}
          {getActiveFilterCount() > 0 && (
            <div className="pt-2 border-t border-gray-200">
              <button
                onClick={clearAllFilters}
                className="w-full py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition"
              >
                Clear All Filters
              </button>
            </div>
          )}
        </div>
      )}

      {/* Leads List */}
      <div className="flex-1 overflow-y-auto px-4 py-4 pb-20">
        {filteredLeads.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <User className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No leads found</h3>
            <p className="text-gray-500 mb-6">
              {searchQuery || statusFilter !== 'all' || sourceFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Start capturing leads'}
            </p>
            <button
              onClick={() => router.push('/chat')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Capture New Lead
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredLeads.map((lead) => (
              <div
                key={lead.LeadId}
                className="w-full bg-white rounded-lg shadow-sm hover:shadow-md transition p-4 border border-gray-200"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-gray-900 truncate">
                      {lead.PrimaryVisitorName || 'Unknown Visitor'}
                    </h3>
                    {lead.CompanyName && (
                      <p className="text-sm text-gray-600 flex items-center mt-1">
                        <Building2 className="w-3 h-3 mr-1" />
                        {lead.CompanyName}
                      </p>
                    )}
                  </div>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getStatusColor(
                      lead.StatusCode
                    )}`}
                  >
                    {lead.StatusName || lead.StatusCode}
                  </span>
                </div>

                {lead.PrimaryVisitorPhone && (
                  <p className="text-sm text-gray-500 flex items-center mt-2">
                    <Phone className="w-3 h-3 mr-1" />
                    {lead.PrimaryVisitorPhone}
                  </p>
                )}

                {lead.DiscussionSummary && (
                  <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                    {lead.DiscussionSummary}
                  </p>
                )}

                <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                  <span className="flex items-center">
                    <Calendar className="w-3 h-3 mr-1" />
                    {formatDistanceToNow(new Date(lead.CreatedAt), { addSuffix: true })}
                  </span>
                  <span className="px-2 py-0.5 bg-gray-100 rounded">
                    {lead.SourceName || lead.SourceCode}
                  </span>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
                  <button
                    onClick={() => router.push(`/leads/${lead.LeadId}`)}
                    className="flex-1 flex items-center justify-center gap-1 bg-blue-600 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
                  >
                    <Edit3 className="w-3 h-3" />
                    Edit
                  </button>
                  <button
                    onClick={() => router.push(`/chat/${lead.LeadId}`)}
                    className="flex-1 flex items-center justify-center gap-1 bg-green-600 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition"
                  >
                    <MessageCircle className="w-3 h-3" />
                    Chat
                  </button>
                  <button
                    onClick={() => confirmDelete(lead)}
                    className="flex items-center justify-center gap-1 bg-red-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-red-600 transition"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && selectedLead && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Mark Lead as Inactive?</h3>
                <p className="text-sm text-gray-600">Data will be preserved but hidden from list</p>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-3 mb-3 border border-blue-200">
              <p className="text-xs text-blue-600 font-medium mb-1">💾 Soft Delete - Data Preserved</p>
              <p className="text-xs text-gray-600">This lead will be marked as inactive. All data remains in the database and can be restored later by an administrator.</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-3 mb-4">
              <p className="text-sm font-medium text-gray-900">{selectedLead.PrimaryVisitorName}</p>
              <p className="text-sm text-gray-600">{selectedLead.CompanyName}</p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setSelectedLead(null);
                }}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteLead(selectedLead.LeadId)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
}
