'use client';

import { useState } from 'react';
import Sidebar from "@/components/Sidebar";
import { Menu } from 'lucide-react';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="flex-1 bg-slate-50/50 relative">
        {/* Mobile Header with Hamburger */}
        <div className="lg:hidden sticky top-0 z-30 bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center justify-between">
          <span className="text-lg font-bold text-white tracking-tight">KANBIX Agent</span>
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Open menu"
          >
            <Menu size={24} />
          </button>
        </div>
        <div className="p-4 sm:p-6 lg:p-10 animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
