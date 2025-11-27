'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { isAuthenticated } from '@/lib/auth';
import { api } from '@/lib/api';
import BottomNav from '@/components/BottomNav';
import {
  MessageSquare, Plus, Edit2, Trash2, RefreshCw,
  FileText, Image, Video, File, X, Save, ChevronLeft
} from 'lucide-react';

interface Message {
  MessageId: number;
  MessageTitle: string;
  MessageType: 'text' | 'image' | 'document' | 'video';
  MessageBody: string | null;
  FileUrl: string | null;
  Variables: string | null;
  IsActive: boolean;
  CreatedAt: string;
}

export default function MessageMasterPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingMessage, setEditingMessage] = useState<Message | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [title, setTitle] = useState('');
  const [messageType, setMessageType] = useState<'text' | 'image' | 'document' | 'video'>('text');
  const [body, setBody] = useState('');
  const [variables, setVariables] = useState<string[]>([]);
  const [newVariable, setNewVariable] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/auth/login');
      return;
    }
    loadMessages();
  }, [router]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      const data = await api.getMessages(false);
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setTitle('');
    setMessageType('text');
    setBody('');
    setVariables([]);
    setNewVariable('');
    setEditingMessage(null);
  };

  const openCreateModal = () => {
    resetForm();
    setShowModal(true);
  };

  const openEditModal = (msg: Message) => {
    setEditingMessage(msg);
    setTitle(msg.MessageTitle);
    setMessageType(msg.MessageType);
    setBody(msg.MessageBody || '');
    try {
      setVariables(msg.Variables ? JSON.parse(msg.Variables) : []);
    } catch {
      setVariables([]);
    }
    setShowModal(true);
  };

  const addVariable = () => {
    if (newVariable.trim() && !variables.includes(newVariable.trim())) {
      setVariables([...variables, newVariable.trim()]);
      setNewVariable('');
    }
  };

  const removeVariable = (v: string) => {
    setVariables(variables.filter(x => x !== v));
  };

  const insertVariable = (v: string) => {
    setBody(body + `{{${v}}}`);
  };

  const handleSave = async () => {
    if (!title.trim()) {
      toast.error('Please enter a title');
      return;
    }

    setSaving(true);
    try {
      if (editingMessage) {
        await api.updateMessage(editingMessage.MessageId, {
          title,
          message_type: messageType,
          body: body || undefined,
          variables: variables.length > 0 ? variables : undefined
        });
        toast.success('Message updated successfully');
      } else {
        await api.createMessage({
          title,
          message_type: messageType,
          body: body || undefined,
          variables: variables.length > 0 ? variables : undefined
        });
        toast.success('Message created successfully');
      }
      setShowModal(false);
      resetForm();
      loadMessages();
    } catch (error: any) {
      console.error('Failed to save message:', error);
      toast.error(error.response?.data?.detail || 'Failed to save message');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (messageId: number) => {
    if (!confirm('Delete this message template?')) return;

    try {
      await api.deleteMessage(messageId);
      loadMessages();
      toast.success('Message deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete message');
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'text': return <FileText className="w-5 h-5 text-blue-500" />;
      case 'image': return <Image className="w-5 h-5 text-green-500" />;
      case 'video': return <Video className="w-5 h-5 text-purple-500" />;
      case 'document': return <File className="w-5 h-5 text-orange-500" />;
      default: return <MessageSquare className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'text': return 'bg-blue-100 text-blue-700';
      case 'image': return 'bg-green-100 text-green-700';
      case 'video': return 'bg-purple-100 text-purple-700';
      case 'document': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  if (!isAuthenticated()) return null;

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-4 py-4 shadow-lg sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.back()} className="p-1">
              <ChevronLeft className="w-6 h-6" />
            </button>
            <div>
              <h1 className="text-xl font-bold flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Message Master
              </h1>
              <p className="text-blue-100 text-sm">Reusable message templates</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={openCreateModal}
              className="bg-green-500 text-white p-2 rounded-full hover:bg-green-600 transition shadow-md"
            >
              <Plus className="w-5 h-5" />
            </button>
            <button
              onClick={loadMessages}
              className="bg-white text-blue-600 p-2 rounded-full hover:bg-blue-50 transition shadow-md"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Messages List */}
      <div className="flex-1 overflow-y-auto px-4 py-4 pb-20">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-8 h-8 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No message templates</h3>
            <p className="text-gray-500 mb-4">Create your first message template</p>
            <button
              onClick={openCreateModal}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Create Message
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((msg) => (
              <div
                key={msg.MessageId}
                className={`bg-white rounded-xl shadow-md border p-4 ${!msg.IsActive ? 'opacity-50' : ''}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getTypeIcon(msg.MessageType)}
                    <div>
                      <h3 className="font-semibold text-gray-900">{msg.MessageTitle}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getTypeColor(msg.MessageType)}`}>
                        {msg.MessageType}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => openEditModal(msg)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(msg.MessageId)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {msg.MessageBody && (
                  <p className="text-sm text-gray-600 mt-2 line-clamp-2 bg-gray-50 p-2 rounded">
                    {msg.MessageBody}
                  </p>
                )}

                {msg.Variables && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {JSON.parse(msg.Variables).map((v: string) => (
                      <span key={v} className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                        {`{{${v}}}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  {editingMessage ? 'Edit Message' : 'Create Message'}
                </h2>
                <button onClick={() => { setShowModal(false); resetForm(); }} className="p-2">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g., Welcome Message"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type *
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    {['text', 'image', 'document', 'video'].map((type) => (
                      <button
                        key={type}
                        onClick={() => setMessageType(type as any)}
                        className={`p-3 rounded-lg border text-center transition ${
                          messageType === type
                            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-500'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        {getTypeIcon(type)}
                        <div className="text-xs mt-1 capitalize">{type}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Body */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Message Body
                  </label>
                  <textarea
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    rows={4}
                    placeholder="Enter your message. Use {{variable}} for dynamic content."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  {variables.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      <span className="text-xs text-gray-500">Click to insert:</span>
                      {variables.map((v) => (
                        <button
                          key={v}
                          onClick={() => insertVariable(v)}
                          className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded hover:bg-purple-200"
                        >
                          {`{{${v}}}`}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Variables */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Variables
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newVariable}
                      onChange={(e) => setNewVariable(e.target.value)}
                      placeholder="e.g., name, company"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      onKeyPress={(e) => e.key === 'Enter' && addVariable()}
                    />
                    <button
                      onClick={addVariable}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                    >
                      Add
                    </button>
                  </div>
                  {variables.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {variables.map((v) => (
                        <span
                          key={v}
                          className="inline-flex items-center gap-1 bg-purple-100 text-purple-700 px-2 py-1 rounded"
                        >
                          {v}
                          <button onClick={() => removeVariable(v)}>
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => { setShowModal(false); resetForm(); }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!title.trim() || saving}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {saving ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {saving ? 'Saving...' : 'Save'}
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
