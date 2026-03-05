'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Search, Mail, Phone, Calendar, Ticket, User } from 'lucide-react';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function loadCustomers() {
      try {
        const data = await api.getCustomers();
        setCustomers(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadCustomers();
  }, []);

  const filteredCustomers = customers.filter(c => 
    c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-10 animate-fade-in">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Customers</h1>
        <p className="text-lg text-slate-500 mt-1">View and manage your unified customer database</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors" size={22} />
            <input 
              type="text" 
              placeholder="Search by name or email..."
              className="w-full pl-12 pr-6 py-4 border-2 border-slate-100 rounded-2xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all text-base md:text-lg"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 p-8">
          {loading ? (
            Array(6).fill(0).map((_, i) => (
              <div key={i} className="animate-pulse bg-slate-50 rounded-2xl p-8 h-64 border border-slate-100"></div>
            ))
          ) : filteredCustomers.length > 0 ? (
            filteredCustomers.map((customer) => (
              <div key={customer.id} className="bg-white rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl hover:border-blue-100 transition-all p-8 flex flex-col justify-between group relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                  <User size={120} />
                </div>
                
                <div className="relative z-10">
                  <div className="flex justify-between items-start mb-6">
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-extrabold text-2xl shadow-lg shadow-blue-100">
                      {customer.name?.charAt(0).toUpperCase() || '?'}
                    </div>
                    <div className="flex items-center text-xs font-extrabold text-blue-600 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100 tracking-wider">
                      <Ticket size={14} className="mr-1.5" /> {customer.ticket_count} TICKETS
                    </div>
                  </div>
                  
                  <h3 className="text-xl font-bold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors">
                    {customer.name || 'Anonymous'}
                  </h3>
                  
                  <div className="space-y-3 mt-6">
                    <div className="flex items-center text-base text-slate-600 font-medium">
                      <Mail size={18} className="mr-3 text-slate-400" /> {customer.email}
                    </div>
                    {customer.phone && (
                      <div className="flex items-center text-base text-slate-600 font-medium">
                        <Phone size={18} className="mr-3 text-slate-400" /> {customer.phone}
                      </div>
                    )}
                    <div className="flex items-center text-sm text-slate-400 font-bold uppercase tracking-wide mt-4">
                      <Calendar size={16} className="mr-3" /> Joined {new Date(customer.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                
                <button className="mt-8 w-full py-3.5 bg-slate-50 text-slate-600 rounded-xl text-base font-bold hover:bg-blue-600 hover:text-white hover:shadow-lg hover:shadow-blue-100 transition-all relative z-10 border border-slate-100">
                  View Full Profile
                </button>
              </div>
            ))
          ) : (
            <div className="col-span-full py-20 text-center text-slate-400">
              <div className="text-xl font-medium">No customers found.</div>
              <p className="mt-1">Try a different search term.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
