'use client';

import { useState, useEffect } from 'react';
import { Zap, Clock, CheckCircle, AlertCircle, Pause, Play, XCircle, Calendar } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';

interface DripSequenceCardProps {
  leadId: number;
}

interface DripAssignment {
  AssignmentId: number;
  DripId: number;
  DripName: string;
  StartDate: string;
  Status: string;
  CompletedAt?: string;
}

interface ScheduledMessage {
  ScheduledId: number;
  MessageTitle: string;
  DayNumber: number;
  SendTime: string;
  ScheduledAt: string;
  Status: string;
  SentAt?: string;
}

export default function DripSequenceCard({ leadId }: DripSequenceCardProps) {
  const [loading, setLoading] = useState(true);
  const [assignment, setAssignment] = useState<DripAssignment | null>(null);
  const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadDripStatus();
  }, [leadId]);

  const loadDripStatus = async () => {
    try {
      setLoading(true);
      const data = await api.getLeadDripStatus(leadId);
      setAssignment(data.assignment);
      setScheduledMessages(data.scheduled_messages || []);
    } catch (error) {
      console.error('Failed to load drip status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePauseDrip = async () => {
    if (!assignment) return;

    setActionLoading(true);
    try {
      await api.pauseDrip(leadId, assignment.AssignmentId);
      toast.success('Drip sequence paused');
      await loadDripStatus();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to pause drip');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResumeDrip = async () => {
    if (!assignment) return;

    setActionLoading(true);
    try {
      await api.resumeDrip(leadId, assignment.AssignmentId);
      toast.success('Drip sequence resumed');
      await loadDripStatus();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to resume drip');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelDrip = async () => {
    if (!assignment) return;

    if (!confirm('Are you sure you want to cancel this drip sequence? All pending messages will be removed.')) {
      return;
    }

    setActionLoading(true);
    try {
      await api.stopDrip(leadId, assignment.AssignmentId);
      toast.success('Drip sequence cancelled');
      await loadDripStatus();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to cancel drip');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'text-green-600 bg-green-50';
      case 'paused':
        return 'text-yellow-600 bg-yellow-50';
      case 'completed':
        return 'text-blue-600 bg-blue-50';
      case 'stopped':
      case 'cancelled':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getMessageStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'sent':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'skipped':
        return <XCircle className="w-4 h-4 text-gray-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center animate-pulse">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-sm font-semibold text-gray-700">Drip Sequence</h2>
        </div>
        <div className="text-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-600 border-t-transparent mx-auto"></div>
        </div>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5 hover:shadow-lg transition-shadow duration-200">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-sm font-semibold text-gray-700">Drip Sequence</h2>
        </div>
        <div className="text-center py-6">
          <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <Zap className="w-8 h-8 text-purple-400" />
          </div>
          <p className="text-gray-500 text-sm">No drip sequence assigned</p>
          <p className="text-gray-400 text-xs mt-1">Go to Drip Sequence tab to apply automation</p>
        </div>
      </div>
    );
  }

  const nextMessage = scheduledMessages.find(m => m.Status?.toLowerCase() === 'pending');
  const sentMessages = scheduledMessages.filter(m => m.Status?.toLowerCase() === 'sent');
  const pendingMessages = scheduledMessages.filter(m => m.Status?.toLowerCase() === 'pending');

  return (
    <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5 hover:shadow-lg transition-shadow duration-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-sm font-semibold text-gray-700">Drip Sequence</h2>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(assignment.Status)}`}>
          {assignment.Status?.toUpperCase()}
        </span>
      </div>

      {/* Drip Info */}
      <div className="bg-purple-50 rounded-xl p-4 mb-4">
        <p className="text-sm font-semibold text-gray-900 mb-1">{assignment.DripName}</p>
        <div className="flex items-center gap-1 text-xs text-gray-600">
          <Calendar className="w-3 h-3" />
          <span>Started: {format(parseISO(assignment.StartDate), 'dd MMM yyyy, hh:mm a')}</span>
        </div>
      </div>

      {/* Next Message */}
      {nextMessage && assignment.Status?.toLowerCase() === 'active' && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 mb-4">
          <div className="flex items-start gap-2">
            <Clock className="w-4 h-4 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-xs font-semibold text-blue-900">Next Message</p>
              <p className="text-sm text-blue-800 mt-1">{nextMessage.MessageTitle}</p>
              <p className="text-xs text-blue-600 mt-1">
                {format(parseISO(nextMessage.ScheduledAt), 'dd MMM, hh:mm a')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Message History */}
      <div className="mb-4">
        <h3 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <span>Message History</span>
          <span className="text-gray-400">({sentMessages.length} sent, {pendingMessages.length} pending)</span>
        </h3>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {scheduledMessages.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-4">No messages scheduled</p>
          ) : (
            scheduledMessages.map((msg) => (
              <div
                key={msg.ScheduledId}
                className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="mt-0.5">
                  {getMessageStatusIcon(msg.Status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-gray-900 truncate">{msg.MessageTitle}</p>
                    <span className="text-xs text-gray-500 whitespace-nowrap">Day {msg.DayNumber}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {msg.Status?.toLowerCase() === 'sent' && msg.SentAt
                      ? `Sent: ${format(parseISO(msg.SentAt), 'dd MMM, hh:mm a')}`
                      : `Scheduled: ${format(parseISO(msg.ScheduledAt), 'dd MMM, hh:mm a')}`
                    }
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Actions */}
      {assignment.Status?.toLowerCase() !== 'completed' && assignment.Status?.toLowerCase() !== 'stopped' && (
        <div className="flex gap-2 pt-3 border-t border-gray-100">
          {assignment.Status?.toLowerCase() === 'active' ? (
            <button
              onClick={handlePauseDrip}
              disabled={actionLoading}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Pause className="w-4 h-4" />
              {actionLoading ? 'Pausing...' : 'Pause'}
            </button>
          ) : assignment.Status?.toLowerCase() === 'paused' ? (
            <button
              onClick={handleResumeDrip}
              disabled={actionLoading}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4" />
              {actionLoading ? 'Resuming...' : 'Resume'}
            </button>
          ) : null}

          <button
            onClick={handleCancelDrip}
            disabled={actionLoading}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XCircle className="w-4 h-4" />
            {actionLoading ? 'Cancelling...' : 'Cancel'}
          </button>
        </div>
      )}
    </div>
  );
}
