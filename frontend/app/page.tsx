'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import toast from 'react-hot-toast';
import { isAuthenticated, getEmployee } from '@/lib/auth';
import BottomNav from '@/components/BottomNav';
import ChatHeader from '@/components/chat/ChatHeader';
import MessageBubble from '@/components/chat/MessageBubble';
import ChatInput from '@/components/chat/ChatInput';
import { api } from '@/lib/api';

export const dynamic = 'force-dynamic';

interface Message {
  message_id: number;
  sender_type: 'employee' | 'visitor' | 'system';
  message_text: string;
  created_at: string;
  attachment_type?: 'image' | 'audio' | null;
  attachment_url?: string | null;
}

interface Lead {
  lead_id: number;
  primary_visitor_name?: string;
  company_name?: string;
  status_code?: string;
}

export default function ChatScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const leadIdParam = searchParams.get('lead_id');

  const [lead, setLead] = useState<Lead | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    if (!isAuthenticated()) {
      router.push('/auth/login');
      return;
    }

    if (!leadIdParam) {
      // No lead selected, show empty state
      setLoading(false);
      return;
    }

    loadLeadAndMessages(parseInt(leadIdParam));
  }, [leadIdParam, router, mounted]);

  const loadLeadAndMessages = async (leadId: number) => {
    try {
      setLoading(true);

      // Fetch lead details
      const leadData = await api.getLead(leadId);
      setLead({
        lead_id: leadData.LeadId,
        primary_visitor_name: leadData.PrimaryVisitorName,
        company_name: leadData.CompanyName,
        status_code: leadData.StatusCode,
      });

      // Fetch messages
      const messagesData = await api.getLeadMessages(leadId);
      setMessages(messagesData || []);
    } catch (error) {
      console.error('Failed to load lead/messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (messageText: string) => {
    if (!lead) return;

    const employee = getEmployee();
    if (!employee) return;

    try {
      await api.addMessage(lead.lead_id, 'employee', messageText, employee.employee_id);

      // Reload messages
      const messagesData = await api.getLeadMessages(lead.lead_id);
      setMessages(messagesData || []);
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message');
    }
  };

  const handleCameraClick = () => {
    // Navigate to chat interface for lead capture
    router.push('/chat');
  };

  const handleVoiceRecording = async (audioBlob: Blob) => {
    if (!lead) return;

    const employee = getEmployee();
    if (!employee) return;

    try {
      await api.extractVoice(audioBlob, lead.lead_id, employee.employee_id);

      // Reload messages
      const messagesData = await api.getLeadMessages(lead.lead_id);
      setMessages(messagesData || []);
    } catch (error) {
      console.error('Failed to upload voice note:', error);
      toast.error('Failed to upload voice note');
    }
  };

  // Prevent hydration errors by not rendering until mounted
  if (!mounted) {
    return null;
  }

  if (!isAuthenticated()) {
    return null;
  }

  if (!leadIdParam) {
    return (
      <>
        <div className="flex flex-col h-screen bg-gray-50">
          <div className="flex-1 flex flex-col items-center justify-center p-6">
            <div className="text-center max-w-md">
              <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg
                  className="w-12 h-12 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">No Lead Selected</h2>
              <p className="text-gray-600 mb-6">
                Select a lead from the Leads tab or create a new one to start chatting
              </p>
              <button
                onClick={() => router.push('/chat')}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                Create New Lead
              </button>
            </div>
          </div>
          <div className="pb-16">
            <BottomNav />
          </div>
        </div>
      </>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading chat...</p>
          </div>
        </div>
        <BottomNav />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <ChatHeader
        leadId={lead?.lead_id}
        visitorName={lead?.primary_visitor_name}
        companyName={lead?.company_name}
        status={lead?.status_code}
        onOptionsClick={() => {
          if (lead) {
            router.push(`/leads/${lead.lead_id}`);
          }
        }}
      />

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 mb-16">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-10">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.message_id}
              senderType={msg.sender_type}
              messageText={msg.message_text}
              createdAt={msg.created_at}
              attachmentType={msg.attachment_type}
              attachmentUrl={msg.attachment_url}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="fixed bottom-16 left-0 right-0 bg-white">
        <ChatInput
          leadId={lead?.lead_id}
          onSendMessage={handleSendMessage}
          onCameraClick={handleCameraClick}
          onVoiceRecording={handleVoiceRecording}
        />
      </div>

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
}
