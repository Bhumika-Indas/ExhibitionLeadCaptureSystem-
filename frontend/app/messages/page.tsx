'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { isAuthenticated } from '@/lib/auth';
import { api } from '@/lib/api';
import BottomNav from '@/components/BottomNav';
import {
  MessageSquare, Plus, Edit2, Trash2, RefreshCw,
  FileText, Image, Video, File, X, Save, ChevronLeft, Upload
} from 'lucide-react';

interface Message {
  MessageId: number;
  MessageTitle: string;
  MessageType: 'text' | 'image' | 'document' | 'video';
  MessageBody: string | null;
  FileUrl: string | null;
  FileName: string | null;
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
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [messageType, setMessageType] = useState<'text' | 'image' | 'document' | 'video'>('text');
  const [body, setBody] = useState('');
  const [variables, setVariables] = useState<string[]>([]);
  const [newVariable, setNewVariable] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);

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
    setSelectedFile(null);
    setFilePreview(null);
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
    if (msg.FileUrl) {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:9000';
      setFilePreview(`${API_BASE_URL}${msg.FileUrl}`);
    }
    setShowModal(true);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type based on message type
    const validTypes: Record<string, string[]> = {
      image: ['image/jpeg', 'image/jpg', 'image/png'],
      video: ['video/mp4', 'video/webm', 'video/ogg'],
      document: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    };

    if (messageType !== 'text' && validTypes[messageType]) {
      if (!validTypes[messageType].includes(file.type)) {
        toast.error(`Please select a valid ${messageType} file`);
        return;
      }
    }

    setSelectedFile(file);

    // Create preview for images
    if (messageType === 'image' && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setFilePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setFilePreview(file.name);
    }
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

    if (messageType !== 'text' && !editingMessage && !selectedFile) {
      toast.error(`Please upload a ${messageType} file`);
      return;
    }

    setSaving(true);
    try {
      if (editingMessage) {
        // Edit mode - only update text fields
        await api.updateMessage(editingMessage.MessageId, {
          title,
          message_type: messageType,
          body: body || undefined,
          variables: variables.length > 0 ? variables : undefined
        });
        toast.success('Message updated successfully');
      } else {
        // Create mode
        if (messageType === 'text') {
          // Text message - no file
          await api.createMessage({
            title,
            message_type: messageType,
            body: body || undefined,
            variables: variables.length > 0 ? variables : undefined
          });
        } else {
          // Media message - with file
          const formData = new FormData();
          formData.append('title', title);
          formData.append('message_type', messageType);
          if (body) formData.append('body', body);
          if (variables.length > 0) {
            formData.append('variables', JSON.stringify(variables));
          }
          if (selectedFile) {
            formData.append('file', selectedFile);
          }

          await api.createMessageWithMedia(formData);
        }
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
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-10 h-10 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No message templates</h3>
            <p className="text-gray-500 mb-4">Create your first message template</p>
            <button
              onClick={openCreateModal}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
            >
              Create Message
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.MessageId}
                className={`bg-white rounded-xl shadow-lg border-2 border-gray-200 p-5 transition-all hover:shadow-xl hover:border-blue-300 ${!msg.IsActive ? 'opacity-50' : ''}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      {getTypeIcon(msg.MessageType)}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-bold text-gray-900 text-lg mb-2">{msg.MessageTitle}</h3>
                      <span className={`text-xs px-3 py-1 rounded-full font-medium ${getTypeColor(msg.MessageType)}`}>
                        {msg.MessageType.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => openEditModal(msg)}
                      className="p-2.5 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                    >
                      <Edit2 className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(msg.MessageId)}
                      className="p-2.5 text-red-500 hover:bg-red-50 rounded-lg transition"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {msg.MessageBody && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{msg.MessageBody}</p>
                  </div>
                )}

                {msg.FileUrl && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200 flex items-center gap-2">
                    <File className="w-4 h-4 text-blue-600" />
                    <span className="text-sm text-blue-700 font-medium">{msg.FileName || 'Attached file'}</span>
                  </div>
                )}

                {msg.Variables && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="text-xs text-gray-500 font-medium">Variables:</span>
                    {JSON.parse(msg.Variables).map((v: string) => (
                      <span key={v} className="text-xs bg-purple-100 text-purple-700 px-3 py-1 rounded-full font-medium">
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
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {editingMessage ? 'Edit Message' : 'Create Message Template'}
                </h2>
                <button onClick={() => { setShowModal(false); resetForm(); }} className="p-2 hover:bg-gray-100 rounded-lg">
                  <X className="w-6 h-6 text-gray-500" />
                </button>
              </div>

              <div className="space-y-5">
                {/* Title */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Template Title *
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g., Welcome Message, Product Brochure"
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  />
                </div>

                {/* Type */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Message Type *
                  </label>
                  <div className="grid grid-cols-4 gap-3">
                    {['text', 'image', 'document', 'video'].map((type) => (
                      <button
                        key={type}
                        onClick={() => setMessageType(type as any)}
                        disabled={editingMessage !== null}
                        className={`p-4 rounded-lg border-2 text-center transition ${
                          messageType === type
                            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-500'
                            : 'border-gray-200 hover:border-gray-300'
                        } ${editingMessage ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        {getTypeIcon(type)}
                        <div className="text-sm mt-2 font-medium capitalize">{type}</div>
                      </button>
                    ))}
                  </div>
                  {editingMessage && (
                    <p className="text-xs text-gray-500 mt-2">Message type cannot be changed when editing</p>
                  )}
                </div>

                {/* File Upload for Media Types */}
                {messageType !== 'text' && !editingMessage && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Upload {messageType.charAt(0).toUpperCase() + messageType.slice(1)} *
                    </label>
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition"
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleFileChange}
                        accept={
                          messageType === 'image' ? 'image/*' :
                          messageType === 'video' ? 'video/*' :
                          messageType === 'document' ? '.pdf,.doc,.docx' : '*'
                        }
                        className="hidden"
                      />
                      {filePreview ? (
                        <div className="space-y-2">
                          {messageType === 'image' && typeof filePreview === 'string' && filePreview.startsWith('data:') ? (
                            <img src={filePreview} alt="Preview" className="max-h-40 mx-auto rounded-lg" />
                          ) : (
                            <File className="w-12 h-12 mx-auto text-blue-500" />
                          )}
                          <p className="text-sm text-gray-700 font-medium">{selectedFile?.name || filePreview}</p>
                          <p className="text-xs text-blue-600">Click to change file</p>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <Upload className="w-12 h-12 mx-auto text-gray-400" />
                          <p className="text-sm text-gray-600">Click to upload {messageType}</p>
                          <p className="text-xs text-gray-400">
                            {messageType === 'image' && 'JPG, PNG (Max 10MB)'}
                            {messageType === 'video' && 'MP4, WebM (Max 10MB)'}
                            {messageType === 'document' && 'PDF, DOC, DOCX (Max 10MB)'}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Caption/Body */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    {messageType === 'text' ? 'Message Body' : 'Caption (Optional)'}
                  </label>
                  <textarea
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    rows={5}
                    placeholder="Enter your message. Use {{variable}} for dynamic content like {{name}} or {{company}}."
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  />
                  {variables.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="text-xs text-gray-600 font-medium">Quick insert:</span>
                      {variables.map((v) => (
                        <button
                          key={v}
                          onClick={() => insertVariable(v)}
                          className="text-xs bg-purple-100 text-purple-700 px-3 py-1 rounded-full hover:bg-purple-200 font-medium"
                        >
                          {`{{${v}}}`}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Variables */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Variables (Dynamic Fields)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newVariable}
                      onChange={(e) => setNewVariable(e.target.value)}
                      placeholder="e.g., name, company, phone"
                      className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      onKeyPress={(e) => e.key === 'Enter' && addVariable()}
                    />
                    <button
                      onClick={addVariable}
                      className="px-5 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium"
                    >
                      Add
                    </button>
                  </div>
                  {variables.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {variables.map((v) => (
                        <span
                          key={v}
                          className="inline-flex items-center gap-2 bg-purple-100 text-purple-700 px-3 py-1.5 rounded-full font-medium"
                        >
                          {v}
                          <button onClick={() => removeVariable(v)} className="hover:bg-purple-200 rounded-full p-0.5">
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-3 mt-8">
                <button
                  onClick={() => { setShowModal(false); resetForm(); }}
                  className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium text-base"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!title.trim() || saving}
                  className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center justify-center gap-2 font-medium text-base"
                >
                  {saving ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : (
                    <Save className="w-5 h-5" />
                  )}
                  {saving ? 'Saving...' : (editingMessage ? 'Update Message' : 'Create Message')}
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
