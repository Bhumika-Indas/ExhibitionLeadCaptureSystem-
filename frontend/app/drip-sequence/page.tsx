'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { isAuthenticated } from '@/lib/auth';
import { api } from '@/lib/api';
import BottomNav from '@/components/BottomNav';
import {
  RefreshCw, Plus, Play, ArrowRight, FileText, Image as ImageIcon,
  Zap, Clock, CheckCircle, AlertCircle
} from 'lucide-react';
import { format } from 'date-fns';

interface DripTemplate {
  dripId: number;
  name: string;
  description: string;
  icon: string;
  totalMessages: number;
  dayRange: string;
  updatedAt: string;
  messages: DripMessage[];
}

interface DripMessage {
  messageId: number;
  dayOffset: number;
  timeOfDay: string;
  messageType: 'text' | 'image' | 'document' | 'video';
  content: string;
  templateName?: string;
}

export default function DripSequencePage() {
  const router = useRouter();
  const [drips, setDrips] = useState<DripTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDrip, setSelectedDrip] = useState<DripTemplate | null>(null);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [leads, setLeads] = useState<any[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/auth/login');
      return;
    }
    loadDrips();
  }, [router]);

  const loadDrips = async () => {
    try {
      setLoading(true);

      // Load drips from backend API
      const dripData = await api.getDrips(true);

      // Transform backend data to match frontend interface
      const transformedDrips: DripTemplate[] = await Promise.all(
        dripData.map(async (drip: any) => {
          try {
            // Get full drip details with messages
            const fullDrip = await api.getDrip(drip.DripId);
            const dripDetails = fullDrip?.drip || {};

            // Transform messages - safely handle missing messages array
            const messagesArray = Array.isArray(dripDetails.messages) ? dripDetails.messages : [];
            const messages: DripMessage[] = messagesArray.map((msg: any) => ({
            messageId: msg.DripMessageId,
            dayOffset: msg.DayNumber,
            timeOfDay: msg.SendTime,
            messageType: msg.MessageType || 'text',
            content: msg.MessageBody || msg.MediaUrl || '',
            templateName: msg.MessageTitle
          }));

          // Calculate day range
          const days = messages.map(m => m.dayOffset);
          const dayRange = days.length > 0
            ? `Day ${Math.min(...days)} - Day ${Math.max(...days)}`
            : 'No messages';

            return {
              dripId: drip.DripId,
              name: drip.DripName,
              description: drip.DripDescription || '',
              icon: '📋',
              totalMessages: messages.length,
              dayRange,
              updatedAt: drip.UpdatedAt || drip.CreatedAt,
              messages
            };
          } catch (error) {
            console.error(`Error loading drip ${drip.DripId}:`, error);
            // Return minimal drip info on error
            return {
              dripId: drip.DripId,
              name: drip.DripName,
              description: drip.DripDescription || '',
              icon: '📋',
              totalMessages: 0,
              dayRange: 'Error loading messages',
              updatedAt: drip.UpdatedAt || drip.CreatedAt,
              messages: []
            };
          }
        })
      );

      setDrips(transformedDrips);
    } catch (error) {
      console.error('Failed to load drips:', error);
      toast.error('Failed to load drip sequences');

      // Fallback to mock data on error
      const mockDrips: DripTemplate[] = [
        {
          dripId: 1,
          name: 'Hot Lead Drip',
          description: 'Follow-up sequence for hot leads',
          icon: '🔥',
          totalMessages: 5,
          dayRange: 'Day 0, Day 1, Day 2',
          updatedAt: '2025-11-12',
          messages: [
            {
              messageId: 1,
              dayOffset: 0,
              timeOfDay: '10:00',
              messageType: 'text',
              content: 'Welcome to Indas Analytics! Thank you for visiting our booth.',
              templateName: 'Welcome Message'
            },
            {
              messageId: 2,
              dayOffset: 1,
              timeOfDay: '11:00',
              messageType: 'document',
              content: 'Company_Profile.pdf',
              templateName: 'Company Profile PDF'
            },
            {
              messageId: 3,
              dayOffset: 2,
              timeOfDay: '17:00',
              messageType: 'text',
              content: 'Hi! Would you be interested in scheduling a product demo?',
              templateName: 'Demo Request'
            },
            {
              messageId: 4,
              dayOffset: 3,
              timeOfDay: '16:00',
              messageType: 'image',
              content: 'pricing_overview.jpg',
              templateName: 'Pricing Overview'
            },
            {
              messageId: 5,
              dayOffset: 5,
              timeOfDay: '14:00',
              messageType: 'text',
              content: 'Just following up on our previous messages. Any questions?',
              templateName: 'Final Follow-up'
            }
          ]
        },
        {
          dripId: 2,
          name: 'Exhibition Follow-Up Drip',
          description: 'Standard exhibition visitor nurture sequence',
          icon: '📄',
          totalMessages: 7,
          dayRange: 'Day 0 to Day 5',
          updatedAt: '2025-11-08',
          messages: [
            {
              messageId: 6,
              dayOffset: 0,
              timeOfDay: '10:00',
              messageType: 'text',
              content: 'Thank you for visiting our booth!',
              templateName: 'Thank You Message'
            },
            {
              messageId: 7,
              dayOffset: 0,
              timeOfDay: '10:05',
              messageType: 'document',
              content: 'intro_video.mp4',
              templateName: 'Intro Video'
            },
            {
              messageId: 8,
              dayOffset: 1,
              timeOfDay: '11:00',
              messageType: 'text',
              content: 'Just a quick reminder about our special exhibition offer!',
              templateName: 'Follow-up Reminder'
            },
            {
              messageId: 9,
              dayOffset: 3,
              timeOfDay: '10:00',
              messageType: 'image',
              content: 'pricing_sheet.jpg',
              templateName: 'Pricing Message'
            },
            {
              messageId: 10,
              dayOffset: 4,
              timeOfDay: '15:00',
              messageType: 'text',
              content: 'Here is a case study from one of our clients.',
              templateName: 'Case Study'
            },
            {
              messageId: 11,
              dayOffset: 5,
              timeOfDay: '11:00',
              messageType: 'text',
              content: 'Special offer expires in 2 days! Let us know if interested.',
              templateName: 'Urgency Message'
            },
            {
              messageId: 12,
              dayOffset: 5,
              timeOfDay: '17:00',
              messageType: 'text',
              content: 'Final reminder - reach out anytime!',
              templateName: 'Final Touchpoint'
            }
          ]
        },
        {
          dripId: 3,
          name: 'Demo Conversion Drip',
          description: 'Focused on demo scheduling',
          icon: '🤝',
          totalMessages: 4,
          dayRange: 'Day 0 to Day 3',
          updatedAt: '2025-11-10',
          messages: [
            {
              messageId: 13,
              dayOffset: 0,
              timeOfDay: '09:00',
              messageType: 'text',
              content: 'Great to meet you! When would be a good time for a demo?',
              templateName: 'Demo Invitation'
            },
            {
              messageId: 14,
              dayOffset: 1,
              timeOfDay: '14:00',
              messageType: 'text',
              content: 'Just checking if you had a chance to review our proposal?',
              templateName: 'Demo Follow-up'
            },
            {
              messageId: 15,
              dayOffset: 2,
              timeOfDay: '11:00',
              messageType: 'document',
              content: 'demo_highlights.pdf',
              templateName: 'Demo Highlights'
            },
            {
              messageId: 16,
              dayOffset: 3,
              timeOfDay: '16:00',
              messageType: 'text',
              content: 'Let me know if you need any assistance!',
              templateName: 'Final Check-in'
            }
          ]
        }
      ];

      setDrips(mockDrips);
    } finally {
      setLoading(false);
    }
  };

  const loadLeads = async () => {
    try {
      const response = await api.getLeads({ limit: 100 });
      setLeads(response.leads || []);
    } catch (error) {
      console.error('Failed to load leads:', error);
      setLeads([]);
    }
  };

  const handleViewDrip = (drip: DripTemplate) => {
    setSelectedDrip(drip);
  };

  const handleBackToList = () => {
    setSelectedDrip(null);
  };

  const handleApplyDrip = (drip?: DripTemplate) => {
    if (drip) {
      setSelectedDrip(drip);
    }
    setShowApplyModal(true);
    loadLeads();
  };

  const handleConfirmApply = async () => {
    if (!selectedLeadId || !selectedDrip) {
      toast.error('Please select a lead');
      return;
    }

    setApplying(true);
    try {
      // Apply drip to lead via API
      await api.applyDripToLead(selectedLeadId, selectedDrip.dripId);

      toast.success(`Drip "${selectedDrip.name}" applied successfully! Day 0 messages will be sent immediately.`);
      setShowApplyModal(false);
      setSelectedLeadId(null);
      setSelectedDrip(null);
    } catch (error: any) {
      console.error('Failed to apply drip:', error);
      toast.error(error.response?.data?.detail || 'Failed to apply drip sequence');
    } finally {
      setApplying(false);
    }
  };

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'text': return <FileText className="w-4 h-4" />;
      case 'image': return <ImageIcon className="w-4 h-4" />;
      case 'document': return <FileText className="w-4 h-4" />;
      case 'video': return <Play className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };

  if (!isAuthenticated()) return null;

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center animate-fadeIn">
            <div className="relative mx-auto mb-6 w-12 h-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
            <p className="text-gray-600">Loading drip sequences...</p>
          </div>
        </div>
        <BottomNav />
      </div>
    );
  }

  // DRIP DETAILS VIEW
  if (selectedDrip) {
    return (
      <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-4 py-4 shadow-lg sticky top-0 z-10">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={handleBackToList}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition"
            >
              <ArrowRight className="w-5 h-5 rotate-180" />
            </button>
            <div className="flex-1">
              <h1 className="text-xl font-bold flex items-center gap-2">
                <span>{selectedDrip.icon}</span>
                {selectedDrip.name}
              </h1>
              <p className="text-blue-100 text-sm mt-1">{selectedDrip.description}</p>
            </div>
            <button
              onClick={loadDrips}
              className="bg-white text-blue-600 p-2 rounded-full hover:bg-blue-50 transition-all duration-200 active:scale-95 shadow-md"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages Timeline */}
        <div className="flex-1 overflow-y-auto px-4 py-4 pb-24">
          <div className="space-y-6">
            {Array.from(new Set(selectedDrip.messages.map(m => m.dayOffset))).sort((a, b) => a - b).map((day) => {
              const dayMessages = selectedDrip.messages.filter(m => m.dayOffset === day);

              return (
                <div key={day}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-bold">
                      DAY {day}
                    </div>
                    <div className="flex-1 border-t border-gray-300"></div>
                  </div>

                  <div className="space-y-3">
                    {dayMessages.map((message) => (
                      <div
                        key={message.messageId}
                        className="bg-white rounded-xl shadow-md border border-gray-200 p-4"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 flex-shrink-0">
                            {getMessageTypeIcon(message.messageType)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <h3 className="font-semibold text-gray-900">{message.templateName}</h3>
                              <div className="flex items-center gap-1 text-sm text-gray-500">
                                <Clock className="w-3 h-3" />
                                {message.timeOfDay}
                              </div>
                            </div>
                            <div className="text-xs text-gray-500 mb-2 flex items-center gap-2">
                              <span className="px-2 py-0.5 bg-gray-100 rounded-full capitalize">
                                {message.messageType}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 border border-gray-200">
                              {message.content}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Apply Button */}
        <div className="fixed bottom-16 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-lg">
          <button
            onClick={() => handleApplyDrip(selectedDrip)}
            className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-3 rounded-lg font-semibold hover:from-green-600 hover:to-green-700 transition flex items-center justify-center gap-2 shadow-md"
          >
            <Zap className="w-5 h-5" />
            Apply this Drip to Lead
          </button>
        </div>

        <BottomNav />
      </div>
    );
  }

  // DRIP LIST VIEW
  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-4 py-4 shadow-lg sticky top-0 z-10">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Zap className="w-5 h-5" />
              DRIP SEQUENCES
            </h1>
            <p className="text-blue-100 text-sm mt-1">Pre-built automation templates</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => router.push('/drips')}
              className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-all duration-200 active:scale-95 shadow-md flex items-center gap-2 text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              Create New
            </button>
            <button
              onClick={loadDrips}
              className="bg-white text-blue-600 p-2 rounded-full hover:bg-blue-50 transition-all duration-200 active:scale-95 shadow-md"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Drip List */}
      <div className="flex-1 overflow-y-auto px-4 py-4 pb-20">
        {drips.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-10 h-10 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No drip sequences</h3>
            <p className="text-gray-500 mb-4">Create your first automated drip sequence</p>
            <button
              onClick={() => router.push('/drips')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Create Drip Sequence
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {drips.map((drip) => (
              <div
                key={drip.dripId}
                className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-200"
              >
                <div className="p-4">
                  <div className="flex items-start gap-3 mb-3">
                    <div className="text-3xl">{drip.icon}</div>
                    <div className="flex-1">
                      <h3 className="font-bold text-gray-900 text-lg mb-1">
                        {drip.name} <span className="text-sm font-normal text-gray-500">({drip.totalMessages} Messages)</span>
                      </h3>
                      <p className="text-sm text-gray-600 mb-2">{drip.dayRange}</p>
                      <p className="text-xs text-gray-400">Updated: {format(new Date(drip.updatedAt), 'd MMM')}</p>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleViewDrip(drip)}
                      className="flex-1 bg-blue-50 text-blue-600 py-2 px-4 rounded-lg hover:bg-blue-100 transition font-medium text-sm"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleApplyDrip(drip)}
                      className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition font-medium text-sm flex items-center justify-center gap-1"
                    >
                      <Zap className="w-4 h-4" />
                      Apply to Lead
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Apply Drip Modal */}
      {showApplyModal && selectedDrip && (() => {
        const drip: DripTemplate = selectedDrip;
        return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4 text-center">
                APPLY DRIP TO LEAD
              </h2>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Lead *
                  </label>
                  <select
                    value={selectedLeadId || ''}
                    onChange={(e) => setSelectedLeadId(Number(e.target.value))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Choose a lead...</option>
                    {leads.map((lead) => (
                      <option key={lead.LeadId} value={lead.LeadId}>
                        {lead.PrimaryVisitorName || 'Unknown'} - {lead.CompanyName || 'No Company'} - {lead.PrimaryVisitorPhone || 'No Phone'}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Selected Drip:</p>
                  <p className="font-bold text-blue-900 flex items-center gap-2">
                    <span className="text-2xl">{drip.icon}</span>
                    {drip.name} ({drip.totalMessages} Messages)
                  </p>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-yellow-800">
                      Day 0 messages will be sent <strong>immediately</strong> after applying.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowApplyModal(false);
                    setSelectedLeadId(null);
                  }}
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium"
                  disabled={applying}
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmApply}
                  disabled={!selectedLeadId || applying}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition disabled:opacity-50 font-medium flex items-center justify-center gap-2"
                >
                  {applying ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Applying...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Apply Drip
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
        );
      })()}

      <BottomNav />
    </div>
  );
}
