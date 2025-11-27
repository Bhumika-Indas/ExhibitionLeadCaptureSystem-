'use client';

import { ArrowLeft, MoreVertical } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface ChatHeaderProps {
  leadId?: number;
  visitorName?: string;
  companyName?: string;
  status?: string;
  onOptionsClick?: () => void;
}

export default function ChatHeader({
  leadId,
  visitorName,
  companyName,
  status,
  onOptionsClick,
}: ChatHeaderProps) {
  const router = useRouter();

  const getStatusColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'new':
        return 'bg-blue-100 text-blue-800';
      case 'needs_correction':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-blue-600 text-white px-4 py-3 flex items-center justify-between shadow-md">
      <div className="flex items-center flex-1 min-w-0">
        <button
          onClick={() => router.push('/leads')}
          className="mr-3 p-1 hover:bg-blue-700 rounded-full transition"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>

        <div className="flex-1 min-w-0">
          <div className="font-semibold text-lg truncate">
            {visitorName || 'New Lead'}
          </div>
          <div className="text-sm text-blue-100 truncate">
            {companyName || 'Company not set'}
          </div>
          {status && (
            <span
              className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full ${getStatusColor(
                status
              )}`}
            >
              {status}
            </span>
          )}
        </div>
      </div>

      <button
        onClick={onOptionsClick}
        className="ml-2 p-2 hover:bg-blue-700 rounded-full transition"
      >
        <MoreVertical className="w-5 h-5" />
      </button>
    </div>
  );
}
