'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import BottomNav from '@/components/BottomNav';
import type { Exhibition } from '@/lib/types';
import { MapPin, Calendar, Plus, CheckCircle, X, Edit2, Trash2 } from 'lucide-react';
import { format } from 'date-fns';

export default function ExhibitionsPage() {
  const router = useRouter();
  const [exhibitions, setExhibitions] = useState<Exhibition[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editingExhibition, setEditingExhibition] = useState<Exhibition | null>(null);
  const [deletingExhibition, setDeletingExhibition] = useState<Exhibition | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    start_date: '',
    end_date: '',
    description: ''
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/auth/login');
      return;
    }

    // Get currently selected exhibition
    const stored = localStorage.getItem('selected_exhibition');
    if (stored) {
      setSelectedId(parseInt(stored));
    }

    loadExhibitions();
  }, [router]);

  const loadExhibitions = async () => {
    try {
      const data = await api.getExhibitions();
      setExhibitions(data);
    } catch (error) {
      console.error('Failed to load exhibitions:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectExhibition = (exhibitionId: number) => {
    localStorage.setItem('selected_exhibition', exhibitionId.toString());
    setSelectedId(exhibitionId);
    // Navigate to leads page
    setTimeout(() => router.push('/leads'), 300);
  };

  const handleCreateExhibition = async () => {
    if (!formData.name || !formData.start_date || !formData.end_date) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (new Date(formData.end_date) < new Date(formData.start_date)) {
      toast.error('End date must be after start date');
      return;
    }

    setCreating(true);
    try {
      await api.createExhibition({
        name: formData.name,
        location: formData.location || undefined,
        start_date: formData.start_date,
        end_date: formData.end_date,
        description: formData.description || undefined
      });

      toast.success('Exhibition created successfully!');
      setShowCreateModal(false);
      setFormData({ name: '', location: '', start_date: '', end_date: '', description: '' });
      loadExhibitions();
    } catch (error: any) {
      console.error('Failed to create exhibition:', error);
      toast.error(error.response?.data?.detail || 'Failed to create exhibition');
    } finally {
      setCreating(false);
    }
  };

  const openEditModal = (exhibition: Exhibition, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingExhibition(exhibition);
    setFormData({
      name: exhibition.Name,
      location: exhibition.Location || '',
      start_date: format(new Date(exhibition.StartDate), 'yyyy-MM-dd'),
      end_date: format(new Date(exhibition.EndDate), 'yyyy-MM-dd'),
      description: exhibition.Description || ''
    });
    setShowEditModal(true);
  };

  const handleUpdateExhibition = async () => {
    if (!editingExhibition) return;

    if (!formData.name || !formData.start_date || !formData.end_date) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (new Date(formData.end_date) < new Date(formData.start_date)) {
      toast.error('End date must be after start date');
      return;
    }

    setUpdating(true);
    try {
      await api.updateExhibition(editingExhibition.ExhibitionId, {
        name: formData.name,
        location: formData.location || undefined,
        start_date: formData.start_date,
        end_date: formData.end_date,
        description: formData.description || undefined
      });

      toast.success('Exhibition updated successfully!');
      setShowEditModal(false);
      setEditingExhibition(null);
      setFormData({ name: '', location: '', start_date: '', end_date: '', description: '' });
      loadExhibitions();
    } catch (error: any) {
      console.error('Failed to update exhibition:', error);
      toast.error(error.response?.data?.detail || 'Failed to update exhibition');
    } finally {
      setUpdating(false);
    }
  };

  const openDeleteConfirm = (exhibition: Exhibition, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingExhibition(exhibition);
    setShowDeleteConfirm(true);
  };

  const handleDeleteExhibition = async () => {
    if (!deletingExhibition) return;

    setDeleting(true);
    try {
      await api.deleteExhibition(deletingExhibition.ExhibitionId);
      toast.success('Exhibition deleted successfully!');
      setShowDeleteConfirm(false);
      setDeletingExhibition(null);

      // If the deleted exhibition was selected, clear selection
      if (selectedId === deletingExhibition.ExhibitionId) {
        localStorage.removeItem('selected_exhibition');
        setSelectedId(null);
      }

      loadExhibitions();
    } catch (error: any) {
      console.error('Failed to delete exhibition:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete exhibition');
    } finally {
      setDeleting(false);
    }
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
            <p className="text-gray-600">Loading exhibitions...</p>
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Exhibitions</h1>
            <p className="text-blue-100 text-sm mt-1">Select active exhibition</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-white text-blue-600 p-2 rounded-full hover:bg-blue-50 transition"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Exhibitions List */}
      <div className="flex-1 overflow-y-auto px-4 py-4 pb-20">
        {exhibitions.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <MapPin className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No exhibitions</h3>
            <p className="text-gray-500 mb-6">Create your first exhibition to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Create Exhibition
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {exhibitions.map((exhibition) => {
              const isSelected = selectedId === exhibition.ExhibitionId;
              const startDate = new Date(exhibition.StartDate);
              const endDate = new Date(exhibition.EndDate);

              return (
                <div
                  key={exhibition.ExhibitionId}
                  className={`w-full bg-white rounded-lg shadow-sm hover:shadow-md transition p-4 border-2 ${
                    isSelected ? 'border-blue-500 bg-blue-50' : 'border-transparent'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <button
                      onClick={() => selectExhibition(exhibition.ExhibitionId)}
                      className="flex-1 text-left min-w-0"
                    >
                      <h3 className="text-base font-semibold text-gray-900 mb-1">
                        {exhibition.Name}
                      </h3>
                      <p className="text-sm text-gray-600 flex items-center">
                        <MapPin className="w-3 h-3 mr-1 flex-shrink-0" />
                        <span className="truncate">{exhibition.Location}</span>
                      </p>
                    </button>

                    <div className="flex items-center gap-2 ml-2">
                      {isSelected && (
                        <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
                      )}
                      <button
                        onClick={(e) => openEditModal(exhibition, e)}
                        className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                        title="Edit exhibition"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => openDeleteConfirm(exhibition, e)}
                        className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition"
                        title="Delete exhibition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <button
                    onClick={() => selectExhibition(exhibition.ExhibitionId)}
                    className="w-full text-left"
                  >
                    <div className="flex items-center text-sm text-gray-500 mt-3">
                      <Calendar className="w-3 h-3 mr-1" />
                      <span>
                        {format(startDate, 'MMM d')} - {format(endDate, 'MMM d, yyyy')}
                      </span>
                    </div>

                    {exhibition.IsActive && (
                      <div className="mt-3">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          Active
                        </span>
                      </div>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Exhibition Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Create Exhibition</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Exhibition Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Tech Summit 2025"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Location */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="e.g., Mumbai Convention Center"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Start Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date *
                  </label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* End Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date *
                  </label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    min={formData.start_date}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    placeholder="Brief description of the exhibition..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateExhibition}
                  disabled={!formData.name || !formData.start_date || !formData.end_date || creating}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Exhibition Modal */}
      {showEditModal && editingExhibition && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Edit Exhibition</h2>
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingExhibition(null);
                    setFormData({ name: '', location: '', start_date: '', end_date: '', description: '' });
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Exhibition Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Tech Summit 2025"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Location */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="e.g., Mumbai Convention Center"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Start Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date *
                  </label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* End Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date *
                  </label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    min={formData.start_date}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    placeholder="Brief description of the exhibition..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingExhibition(null);
                    setFormData({ name: '', location: '', start_date: '', end_date: '', description: '' });
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                  disabled={updating}
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdateExhibition}
                  disabled={!formData.name || !formData.start_date || !formData.end_date || updating}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {updating ? 'Updating...' : 'Update'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && deletingExhibition && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-md p-6">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
            </div>

            <h2 className="text-xl font-bold text-gray-900 text-center mb-2">Delete Exhibition</h2>
            <p className="text-gray-600 text-center mb-6">
              Are you sure you want to delete <strong>{deletingExhibition.Name}</strong>? This action cannot be undone.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeletingExhibition(null);
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteExhibition}
                disabled={deleting}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? 'Deleting...' : 'Delete'}
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
