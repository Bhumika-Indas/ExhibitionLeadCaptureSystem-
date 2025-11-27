'use client';

import { usePathname, useRouter } from 'next/navigation';
import { MessageSquare, Building2, Users, Repeat, BarChart3 } from 'lucide-react';

export default function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();

  const navItems = [
    { name: 'Chat', path: '/chat', icon: MessageSquare },
    { name: 'Leads', path: '/leads', icon: Users },
    { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
    { name: 'Exhibitions', path: '/exhibitions', icon: Building2 },
    { name: 'Drip', path: '/drip-sequence', icon: Repeat },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
      <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.path || (item.path === '/chat' && pathname.startsWith('/chat'));

          return (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              className={`flex flex-col items-center justify-center flex-1 h-full transition-all duration-200 transform active:scale-95 ${
                isActive
                  ? 'text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className={`w-6 h-6 mb-1 transition-all duration-200 ${isActive ? 'scale-110' : ''}`} />
              <span className="text-xs font-medium">{item.name}</span>
              {isActive && (
                <div className="absolute bottom-0 w-12 h-1 bg-blue-600 rounded-t-full animate-fadeIn" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
