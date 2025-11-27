'use client';

import { formatDistanceToNow } from 'date-fns';
import { User, Bot, CheckCircle, AlertCircle, Image as ImageIcon, Mic } from 'lucide-react';

interface MessageBubbleProps {
  senderType: 'employee' | 'visitor' | 'system';
  messageText: string;
  createdAt: string;
  attachmentType?: 'image' | 'audio' | null;
  attachmentUrl?: string | null;
}

export default function MessageBubble({
  senderType,
  messageText,
  createdAt,
  attachmentType,
  attachmentUrl,
}: MessageBubbleProps) {
  const isSystem = senderType === 'system';
  const isEmployee = senderType === 'employee';

  if (isSystem) {
    return (
      <div className="flex justify-center my-3">
        <div className="bg-gray-100 text-gray-700 text-sm px-4 py-2 rounded-full max-w-xs text-center">
          <Bot className="w-4 h-4 inline mr-1" />
          {messageText}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex mb-4 ${isEmployee ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%] ${isEmployee ? 'order-2' : 'order-1'}`}>
        {/* Attachment */}
        {attachmentType === 'image' && attachmentUrl && (
          <div className="mb-2">
            <img
              src={attachmentUrl}
              alt="Attachment"
              className="rounded-lg max-w-full h-auto shadow-md cursor-pointer hover:opacity-90"
              onClick={() => window.open(attachmentUrl, '_blank')}
            />
          </div>
        )}

        {attachmentType === 'audio' && attachmentUrl && (
          <div className="mb-2 bg-gray-100 p-3 rounded-lg">
            <Mic className="w-4 h-4 inline mr-2" />
            <audio controls className="w-full mt-2">
              <source src={attachmentUrl} type="audio/webm" />
            </audio>
          </div>
        )}

        {/* Message Bubble */}
        {messageText && (
          <div
            className={`px-4 py-2 rounded-2xl shadow-sm ${
              isEmployee
                ? 'bg-blue-500 text-white rounded-br-none'
                : 'bg-gray-200 text-gray-900 rounded-bl-none'
            }`}
          >
            <p className="whitespace-pre-wrap break-words">{messageText}</p>
          </div>
        )}

        {/* Timestamp */}
        <div
          className={`text-xs text-gray-500 mt-1 px-2 ${
            isEmployee ? 'text-right' : 'text-left'
          }`}
        >
          {formatDistanceToNow(new Date(createdAt), { addSuffix: true })}
        </div>
      </div>

      {/* Avatar */}
      <div className={`${isEmployee ? 'order-1 mr-2' : 'order-2 ml-2'} flex-shrink-0`}>
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isEmployee ? 'bg-blue-100 text-blue-600' : 'bg-gray-300 text-gray-700'
          }`}
        >
          <User className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
}
