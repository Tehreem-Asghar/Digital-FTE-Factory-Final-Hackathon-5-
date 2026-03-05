'use client';

import { useState } from 'react';
import { Search, Ticket, Clock, CheckCircle, AlertCircle, MessageSquare } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';

export default function TicketStatusPage() {
  const [ticketId, setTicketId] = useState('');
  const [ticket, setTicket] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketId.trim()) return;

    setLoading(true);
    setError(null);
    setTicket(null);

    try {
      // Using the public endpoint we have for support status
      const response = await fetch(`http://localhost:8000/support/ticket/${ticketId}`);
      if (!response.ok) {
        if (response.status === 404) throw new Error('Ticket not found. Please check the ID.');
        throw new Error('Failed to fetch ticket status');
      }
      const data = await response.json();
      setTicket(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-16 px-4 animate-fade-in">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold text-slate-900 mb-6 tracking-tight">Track Your Request</h1>
        <p className="text-xl text-slate-500 max-w-2xl mx-auto">Enter your tracking ID to see the current status and history of your ticket.</p>
      </div>

      <div className="max-w-xl mx-auto mb-16">
        <form onSubmit={handleSearch} className="relative group">
          <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors">
            <Search size={28} />
          </div>
          <input 
            type="text" 
            placeholder="Enter Tracking ID..."
            value={ticketId}
            onChange={(e) => setTicketId(e.target.value)}
            className="w-full pl-16 pr-36 py-6 bg-white border-2 border-slate-200 rounded-3xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 focus:outline-none transition-all text-xl font-mono"
          />
          <button 
            type="submit"
            disabled={loading || !ticketId.trim()}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 px-8 py-3.5 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 disabled:bg-slate-300 transition-all shadow-xl shadow-blue-100"
          >
            {loading ? 'Searching...' : 'Track'}
          </button>
        </form>
        {error && (
          <div className="mt-6 flex items-center gap-3 text-red-600 bg-red-50 p-5 rounded-2xl border border-red-100 text-base animate-fade-in">
            <AlertCircle size={22} /> {error}
          </div>
        )}
      </div>

      {ticket && (
        <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-2xl overflow-hidden animate-fade-in">
          <div className="p-10 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="flex items-center gap-5">
              <div className="h-16 w-16 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-200">
                <Ticket size={32} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-[0.2em] mb-1">Ticket Information</h3>
                <p className="text-2xl font-mono font-extrabold text-slate-900">{ticket.ticket_id.split('-')[0]}...</p>
              </div>
            </div>
            <div className="scale-110 origin-right">
              <StatusBadge status={ticket.status} />
            </div>
          </div>

          <div className="p-10">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mb-14">
              <div className="space-y-6">
                <div className="flex items-center gap-4 text-slate-600">
                  <div className="p-2.5 bg-blue-50 rounded-xl text-blue-600">
                    <Clock size={24} />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Created On</p>
                    <p className="text-base font-bold text-slate-900">{new Date(ticket.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-slate-600">
                  <div className="p-2.5 bg-green-50 rounded-xl text-green-600">
                    <CheckCircle size={24} />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Last Updated</p>
                    <p className="text-base font-bold text-slate-900">{new Date(ticket.last_updated).toLocaleString()}</p>
                  </div>
                </div>
              </div>
              <div className="bg-blue-50/80 p-8 rounded-3xl border border-blue-100 shadow-inner">
                <h4 className="font-bold text-blue-900 mb-3 flex items-center gap-2 text-lg">
                  <MessageSquare size={20} /> AI Agent Summary
                </h4>
                <p className="text-base text-blue-800 leading-relaxed font-medium italic">
                  "Our AI assistant has processed your request and is currently {ticket.status === 'open' ? 'analyzing the solution' : ticket.status === 'resolved' ? 'has resolved the issue' : 'working on it'}."
                </p>
              </div>
            </div>

            <div>
              <h4 className="font-extrabold text-slate-900 mb-8 flex items-center gap-3 text-xl">
                <MessageSquare size={24} className="text-blue-600" /> Conversation History
              </h4>
              <div className="space-y-6">
                {ticket.messages && ticket.messages.length > 0 ? (
                  ticket.messages.map((msg: any, i: number) => (
                    <div key={i} className={`p-6 rounded-2xl text-base leading-relaxed ${
                      msg.role === 'customer' 
                        ? 'bg-slate-50 text-slate-700 ml-0 mr-12 border border-slate-100' 
                        : 'bg-blue-600 text-white ml-12 mr-0 shadow-xl shadow-blue-100'
                    }`}>
                      <p className={`font-bold mb-2 uppercase text-xs tracking-widest opacity-70 ${msg.role === 'customer' ? 'text-slate-500' : 'text-blue-100'}`}>
                        {msg.role === 'customer' ? 'You' : 'AI Assistant'}
                      </p>
                      {msg.content}
                    </div>
                  ))
                ) : (
                  <p className="text-lg text-slate-400 text-center py-12 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                    Your request is in the queue. No messages to show yet.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
