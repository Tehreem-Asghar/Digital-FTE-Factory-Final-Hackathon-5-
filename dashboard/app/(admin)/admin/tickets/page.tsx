'use client';

import { useEffect, useState } from 'react';
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ChannelIcon from '@/components/ChannelIcon';
import { api } from '@/lib/api';

export default function TicketsPage() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function loadTickets() {
      try {
        const data = await api.getTickets();
        setTickets(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadTickets();
  }, []);

  const filteredTickets = tickets.filter(ticket => 
    ticket.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ticket.customer_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ticket.id.includes(searchTerm)
  );

  return (
    <div className="space-y-10 animate-fade-in">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Tickets</h1>
          <p className="text-lg text-slate-500 mt-1">Manage and track all customer requests</p>
        </div>
        <div className="flex space-x-4">
          <button className="px-6 py-3 bg-white border-2 border-slate-100 rounded-xl text-base font-bold text-slate-700 hover:bg-slate-50 hover:border-slate-200 flex items-center shadow-sm transition-all">
            <Filter size={20} className="mr-2" /> Filter
          </button>
          <button className="px-6 py-3 bg-blue-600 text-white rounded-xl text-base font-bold hover:bg-blue-700 shadow-xl shadow-blue-100 transition-all">
            Export CSV
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors" size={22} />
            <input 
              type="text" 
              placeholder="Search by ID, customer name or email..."
              className="w-full pl-12 pr-6 py-4 border-2 border-slate-100 rounded-2xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all text-base md:text-lg"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-50/50 text-slate-500 text-sm uppercase tracking-widest font-bold">
                <th className="px-8 py-5">
                  <div className="flex items-center cursor-pointer hover:text-slate-900 transition-colors">
                    ID <ArrowUpDown size={14} className="ml-1.5" />
                  </div>
                </th>
                <th className="px-8 py-5">Customer</th>
                <th className="px-8 py-5">Channel</th>
                <th className="px-8 py-5">Status</th>
                <th className="px-8 py-5">Priority</th>
                <th className="px-8 py-5">Date</th>
                <th className="px-8 py-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                Array(5).fill(0).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-8 py-8"><div className="h-5 bg-slate-100 rounded w-16"></div></td>
                    <td className="px-8 py-8"><div className="h-5 bg-slate-100 rounded w-32"></div></td>
                    <td className="px-8 py-8"><div className="h-5 bg-slate-100 rounded w-8"></div></td>
                    <td className="px-8 py-8"><div className="h-7 bg-slate-100 rounded-full w-20"></div></td>
                    <td className="px-8 py-8"><div className="h-5 bg-slate-100 rounded w-16"></div></td>
                    <td className="px-8 py-8"><div className="h-5 bg-slate-100 rounded w-24"></div></td>
                    <td className="px-8 py-8"><div className="h-5 bg-slate-100 rounded w-12 ml-auto"></div></td>
                  </tr>
                ))
              ) : filteredTickets.length > 0 ? (
                filteredTickets.map((ticket) => (
                  <tr key={ticket.id} className="hover:bg-slate-50/80 transition-all group">
                    <td className="px-8 py-6 text-base font-mono text-slate-400">
                      {ticket.id.substring(0, 8)}...
                    </td>
                    <td className="px-8 py-6">
                      <div className="text-base font-bold text-slate-900">{ticket.customer_name || 'Anonymous'}</div>
                      <div className="text-sm text-slate-500 mt-0.5">{ticket.customer_email || 'No email'}</div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="scale-110 origin-left">
                        <ChannelIcon channel={ticket.source_channel} />
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <StatusBadge status={ticket.status} />
                    </td>
                    <td className="px-8 py-6">
                      <span className={`text-sm font-extrabold uppercase tracking-wider ${
                        ticket.priority === 'high' ? 'text-red-600' : 
                        ticket.priority === 'medium' ? 'text-amber-600' : 'text-green-600'
                      }`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-8 py-6 text-base text-slate-500">
                      {new Date(ticket.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="px-8 py-6 text-right">
                      <button className="px-4 py-2 bg-slate-100 text-blue-600 rounded-lg text-sm font-bold hover:bg-blue-600 hover:text-white transition-all opacity-0 group-hover:opacity-100">
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-8 py-20 text-center text-slate-500">
                    <div className="text-lg font-medium">No tickets found matching your search.</div>
                    <p className="mt-1">Try a different search term or filter.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        <div className="p-6 border-t border-slate-100 bg-slate-50/30 flex items-center justify-between">
          <div className="text-base text-slate-500">
            Showing <span className="font-bold text-slate-900">{filteredTickets.length}</span> of <span className="font-bold text-slate-900">{tickets.length}</span> tickets
          </div>
          <div className="flex space-x-3">
            <button className="p-2.5 border-2 border-slate-100 rounded-xl bg-white text-slate-400 hover:bg-slate-50 hover:border-slate-200 disabled:opacity-30 transition-all" disabled>
              <ChevronLeft size={20} />
            </button>
            <button className="p-2.5 border-2 border-slate-100 rounded-xl bg-white text-slate-400 hover:bg-slate-50 hover:border-slate-200 disabled:opacity-30 transition-all" disabled>
              <ChevronRight size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
