'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Ticket, 
  Users, 
  MessageSquare, 
  BarChart3, 
  LifeBuoy,
  Settings
} from 'lucide-react';

const navigation = [
  { name: 'Overview', href: '/admin', icon: LayoutDashboard },
  { name: 'Tickets', href: '/admin/tickets', icon: Ticket },
  { name: 'Conversations', href: '/admin/conversations', icon: MessageSquare },
  { name: 'Customers', href: '/admin/customers', icon: Users },
  { name: 'Analytics', href: '/admin/analytics', icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 bg-slate-900 h-screen text-slate-300">
      <div className="flex items-center justify-center h-20 bg-slate-950 border-b border-slate-800">
        <span className="text-2xl font-bold text-white tracking-tight">KANBIX Agent</span>
      </div>
      <div className="flex flex-col flex-1 overflow-y-auto pt-6">
        <nav className="px-4 space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-4 py-3.5 text-base font-medium rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'hover:bg-slate-800 hover:text-white'
                }`}
              >
                <item.icon className="mr-3.5 h-6 w-6" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center px-4 py-3.5 text-base font-medium rounded-lg hover:bg-slate-800 transition-colors cursor-pointer">
          <Settings className="mr-3.5 h-6 w-6" />
          Settings
        </div>
      </div>
    </div>
  );
}
