'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { LifeBuoy, Search, Ticket, ArrowRight, ShieldCheck, Globe, Menu, X } from 'lucide-react';

export default function CustomerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Mouse tracking for spotlight effect across all customer pages
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      document.documentElement.style.setProperty('--x', `${e.clientX}px`);
      document.documentElement.style.setProperty('--y', `${e.clientY}px`);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col relative overflow-hidden">
      {/* Global Background Layers - High Visibility */}
      <div className="fixed inset-0 bg-grid-pattern opacity-100 pointer-events-none z-0" />
      <div className="fixed inset-0 spotlight-glow pointer-events-none z-0" />

      {/* Customer Header */}
      <header className="bg-white/70 backdrop-blur-xl border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-20 items-center">
            <div className="flex items-center gap-2.5">
              <div className="bg-blue-600 p-2 rounded-xl text-white shadow-lg shadow-blue-200">
                <LifeBuoy size={28} />
              </div>
              <span className="text-2xl font-extrabold text-slate-900 tracking-tight italic">Kanbix <span className="text-blue-600">FTE</span></span>
            </div>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-10">
              <Link href="/" className="text-base font-bold text-slate-600 hover:text-blue-600 transition-all">Support</Link>
              <Link href="/portal/status" className="text-base font-bold text-slate-600 hover:text-blue-600 transition-all flex items-center gap-1.5">
                <Ticket size={20} /> Track
              </Link>
              <Link href="/admin" className="text-sm font-bold text-slate-400 border-2 border-slate-100 px-4 py-2 rounded-xl hover:bg-white hover:border-blue-200 transition-all uppercase tracking-wider">Admin</Link>
            </nav>

            {/* Mobile Hamburger Button */}
            <button
              className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-blue-600 transition-all"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white/90 backdrop-blur-xl border-t border-slate-200 absolute left-0 right-0 top-20 z-40 shadow-lg animate-in slide-in-from-top-2">
            <nav className="flex flex-col px-4 py-4 gap-2">
              <Link
                href="/"
                className="text-base font-bold text-slate-600 hover:text-blue-600 hover:bg-slate-50 px-4 py-3 rounded-xl transition-all"
                onClick={() => setMobileMenuOpen(false)}
              >
                Support
              </Link>
              <Link
                href="/portal/status"
                className="text-base font-bold text-slate-600 hover:text-blue-600 hover:bg-slate-50 px-4 py-3 rounded-xl transition-all flex items-center gap-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Ticket size={18} /> Track
              </Link>
              <Link
                href="/admin"
                className="text-sm font-bold text-slate-400 bg-slate-50 border-2 border-slate-100 px-4 py-3 rounded-xl hover:bg-white hover:border-blue-200 hover:text-blue-600 transition-all uppercase tracking-wider text-center"
                onClick={() => setMobileMenuOpen(false)}
              >
                Admin
              </Link>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1 relative z-10">
        {children}
      </main>

      {/* Simple Footer */}
      <footer className="bg-white/60 backdrop-blur-md border-t border-slate-200 py-12 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="text-slate-400 text-sm font-medium">
            <p>© 2026 Kanbix SaaS. Powered by Customer Success AI Agent.</p>
          </div>
          <div className="flex items-center gap-8 text-slate-400">
             <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest">
               <ShieldCheck size={16} className="text-green-500" /> Secure
             </div>
             <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest">
               <Globe size={16} className="text-blue-500" /> Global
             </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
