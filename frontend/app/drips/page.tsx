'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { isAuthenticated } from '@/lib/auth';
import { api } from '@/lib/api';
import BottomNav from '@/components/BottomNav';
import {
  Zap, Plus, Edit2, Trash2, RefreshCw, ChevronLeft, X, Save,
  Clock, MessageSquare, ChevronRight, Calendar
} from 'lucide-react';

interface Drip {
  DripId: number;
  DripName: string;
  DripDescription: string | null;
  MessageCount: number;
  TotalDays: number | null;
  IsActive: boolean;
  CreatedAt: string;
  Messages?: DripMessage[];
}

interface DripMessage {
  DripMessageId: number;
  MessageId: number;
  MessageTitle: string;
  MessageType: string;
  DayNumber: number;
  SendTime: string;
  SortOrder: number;
}

interface Message {
  MessageId: number;
  MessageTitle: string;
  MessageType: string;
}

export default function DripConfigPage() {
  const router = useRouter();
  const [drips, setDrips] = useState<Drip[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showAddMessageModal, setShowAddMessageModal] = useState(false);
  const [selectedDrip, setSelectedDrip] = useState<Drip | null>(null);
  const [saving, setSaving] = useState(false);

  // Create form
  const [dripName, setDripName] = useState('');
  const [dripDesc, setDripDesc] = useState('');

  // Add message form
  const [selectedMessageId, setSelectedMessageId] = useState<number | null>(null);
  const [dayNumber, setDayNumber] = useState(0);
  const [sendTime, setSendTime] = useState('10:00');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/auth/login');
      return;
    }
    loadDrips();
    loadMessages();
  }, [router]);

  const loadDrips = async () => {
    try {
      setLoading(true);
      const data = await api.getDrips(false);
      setDrips(data);
    } catch (error) {
      console.error('Failed to load drips:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async () => {
    try {
      const data = await api.getMessages(true);
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const loadDripDetails = async (dripId: number) => {
    try {
      const drip = await api.getDrip(dripId);
      setSelectedDrip(drip);
      setShowDetailModal(true);
    } catch (error) {
      console.error('Failed to load drip details:', error);
    }
  };

  const handleCreateDrip = async () => {
    if (!dripName.trim()) {
      toast.error('Please enter a drip name');
      return;
    }

    setSaving(true);
    try {
      await api.createDrip({
        name: dripName,
        description: dripDesc || undefined
      });
      setShowCreateModal(false);
      setDripName('');
      setDripDesc('');
      loadDrips();
      toast.success('Drip sequence created successfully');
    } catch (error: any) {
      console.error('Failed to create drip:', error);
      toast.error(error.response?.data?.detail || 'Failed to create drip');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteDrip = async (dripId: number) => {
    if (!confirm('Delete this drip sequence?')) return;

    try {
      await api.deleteDrip(dripId);
      loadDrips();
      toast.success('Drip sequence deleted');
    } catch (error: any) {
      console.error('Failed to delete:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete drip');
    }
  };

  const handleAddMessage = async () => {
    if (!selectedMessageId || !selectedDrip) {
      toast.error('Please select a message');
      return;
    }

    setSaving(true);
    try {
      await api.addMessageToDrip(selectedDrip.DripId, {
        message_id: selectedMessageId,
        day_number: dayNumber,
        send_time: sendTime
      });
      setShowAddMessageModal(false);
      setSelectedMessageId(null);
      setDayNumber(0);
      setSendTime('10:00');
      loadDripDetails(selectedDrip.DripId);
      toast.success('Message added to drip sequence');
    } catch (error: any) {
      console.error('Failed to add message:', error);
      toast.error(error.response?.data?.detail || 'Failed to add message');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveMessage = async (dripMessageId: number) => {
    if (!confirm('Remove this message from drip?')) return;

    try {
      await api.removeDripMessage(dripMessageId);
      if (selectedDrip) {
        loadDripDetails(selectedDrip.DripId);
      }
      toast.success('Message removed from drip');
    } catch (error: any) {
      console.error('Failed to remove message:', error);
      toast.error(error.response?.data?.detail || 'Failed to remove message');
    }
  };

  if (!isAuthenticated()) return null;

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-4 py-4 shadow-lg sticky top-0 z-10">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-3 flex-1">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-white/20 rounded-lg transition flex-shrink-0"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Drip Configuration
              </h1>
              <p className="text-blue-100 text-sm truncate">Create and manage drip sequences</p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => router.push('/messages')}
              className="bg-purple-500 text-white px-3 py-2 rounded-lg hover:bg-purple-600 transition shadow-md text-sm flex items-center gap-1 whitespace-nowrap"
            >
              <MessageSquare className="w-4 h-4" />
              Messages
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-green-500 text-white p-2 rounded-full hover:bg-green-600 transition shadow-md"
            >
              <Plus className="w-5 h-5" />
            </button>
            <button
              onClick={loadDrips}
              className="bg-white text-blue-600 p-2 rounded-full hover:bg-blue-50 transition shadow-md"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Drips List */}
      <div className="flex-1 overflow-y-auto px-4 py-4 pb-20">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : drips.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-8 h-8 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No drip sequences</h3>
            <p className="text-gray-500 mb-4">Create your first drip sequence</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Create Drip
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {drips.map((drip) => (
              <div
                key={drip.DripId}
                className={`bg-white rounded-xl shadow-md border p-4 ${!drip.IsActive ? 'opacity-50' : ''}`}
              >
                <div className="flex items-start justify-between">
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => loadDripDetails(drip.DripId)}
                  >
                    <div className="flex items-center gap-2">
                      <Zap className="w-5 h-5 text-yellow-500" />
                      <h3 className="font-semibold text-gray-900">{drip.DripName}</h3>
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    </div>
                    {drip.DripDescription && (
                      <p className="text-sm text-gray-500 mt-1">{drip.DripDescription}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" />
                        {drip.MessageCount} messages
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {drip.TotalDays ?? 0} days
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteDrip(drip.DripId)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Drip Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Create Drip</h2>
                <button onClick={() => setShowCreateModal(false)} className="p-2">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Drip Name *
                  </label>
                  <input
                    type="text"
                    value={dripName}
                    onChange={(e) => setDripName(e.target.value)}
                    placeholder="e.g., Exhibition Follow-up"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={dripDesc}
                    onChange={(e) => setDripDesc(e.target.value)}
                    rows={3}
                    placeholder="Describe the purpose of this drip..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateDrip}
                  disabled={!dripName.trim() || saving}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Creating...' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Drip Detail Modal */}
      {showDetailModal && selectedDrip && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{selectedDrip.DripName}</h2>
                  {selectedDrip.DripDescription && (
                    <p className="text-sm text-gray-500">{selectedDrip.DripDescription}</p>
                  )}
                </div>
                <button onClick={() => setShowDetailModal(false)} className="p-2">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Messages Timeline */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-gray-700">Messages</h3>
                  <button
                    onClick={() => setShowAddMessageModal(true)}
                    className="text-sm bg-green-500 text-white px-3 py-1 rounded-lg hover:bg-green-600 flex items-center gap-1"
                  >
                    <Plus className="w-4 h-4" />
                    Add Message
                  </button>
                </div>

                {(!selectedDrip.Messages || selectedDrip.Messages.length === 0) ? (
                  <div className="text-center py-8 bg-gray-50 rounded-lg">
                    <MessageSquare className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-gray-500">No messages added yet</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {selectedDrip.Messages
                      .sort((a, b) => a.DayNumber - b.DayNumber || a.SortOrder - b.SortOrder)
                      .map((msg) => (
                        <div
                          key={msg.DripMessageId}
                          className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border"
                        >
                          <div className="w-12 h-12 bg-blue-100 rounded-full flex flex-col items-center justify-center text-blue-700">
                            <span className="text-xs">Day</span>
                            <span className="font-bold">{msg.DayNumber}</span>
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{msg.MessageTitle}</p>
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <span className="bg-gray-200 px-2 py-0.5 rounded">{msg.MessageType}</span>
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {msg.SendTime}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => handleRemoveMessage(msg.DripMessageId)}
                            className="p-2 text-red-500 hover:bg-red-100 rounded-lg"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                  </div>
                )}
              </div>

              <button
                onClick={() => setShowDetailModal(false)}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Message Modal */}
      {showAddMessageModal && selectedDrip && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Add Message to Drip</h2>
                <button onClick={() => setShowAddMessageModal(false)} className="p-2">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Message Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select Message *
                  </label>
                  <select
                    value={selectedMessageId || ''}
                    onChange={(e) => setSelectedMessageId(Number(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Choose a message...</option>
                    {messages.map((msg) => (
                      <option key={msg.MessageId} value={msg.MessageId}>
                        {msg.MessageTitle} ({msg.MessageType})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Day Number */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Day Number
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={dayNumber}
                    onChange={(e) => setDayNumber(parseInt(e.target.value) || 0)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Day 0 = sent immediately when drip is applied
                  </p>
                </div>

                {/* Send Time */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Send Time
                  </label>
                  <input
                    type="time"
                    value={sendTime}
                    onChange={(e) => setSendTime(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowAddMessageModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddMessage}
                  disabled={!selectedMessageId || saving}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Adding...' : 'Add Message'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <BottomNav />
    </div>
  );
}
