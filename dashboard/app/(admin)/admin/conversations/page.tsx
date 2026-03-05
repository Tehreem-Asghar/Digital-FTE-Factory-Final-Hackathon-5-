'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';
import SentimentBar from '@/components/SentimentBar';
import ChannelIcon from '@/components/ChannelIcon';
import { MessageCircle, Send, User } from 'lucide-react';

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [msgLoading, setMsgLoading] = useState(false);

  useEffect(() => {
    async function loadConversations() {
      try {
        const data = await api.getConversations();
        setConversations(data);
        if (data.length > 0) {
          handleSelect(data[0].id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadConversations();
  }, []);

  const handleSelect = async (id: string) => {
    setSelectedId(id);
    setMsgLoading(true);
    try {
      const data = await api.getMessages(id);
      setMessages(data);
    } catch (err) {
      console.error(err);
    } finally {
      setMsgLoading(false);
    }
  };

  const selectedConversation = conversations.find(c => c.id === selectedId);

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-8 overflow-hidden animate-fade-in">
      {/* Sidebar List */}
      <div className="w-1/3 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <h2 className="text-xl font-bold text-slate-900">Conversations</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              Loading...
            </div>
          ) : conversations.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {conversations.map((conv) => (
                <div 
                  key={conv.id}
                  onClick={() => handleSelect(conv.id)}
                  className={`p-6 cursor-pointer transition-all ${
                    selectedId === conv.id ? 'bg-blue-50/50 border-l-4 border-l-blue-600 shadow-inner' : 'hover:bg-slate-50 border-l-4 border-l-transparent'
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-base font-bold text-slate-900 truncate pr-2">
                      {conv.customer_name || 'Anonymous'}
                    </span>
                    <span className="text-xs font-medium text-slate-400 whitespace-nowrap">
                      {new Date(conv.started_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2.5">
                      <div className="scale-110">
                        <ChannelIcon channel={conv.initial_channel} size={16} />
                      </div>
                      <StatusBadge status={conv.status} />
                    </div>
                    <div className="flex-1 max-w-[100px]">
                      <SentimentBar score={conv.sentiment_score || 0.5} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 text-lg">No conversations found.</div>
          )}
        </div>
      </div>

      {/* Message Thread */}
      <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        {selectedConversation ? (
          <>
            <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <div className="flex items-center gap-4">
                <div className="h-14 w-14 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xl shadow-inner">
                  {selectedConversation.customer_name?.charAt(0).toUpperCase() || '?'}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900">{selectedConversation.customer_name || 'Anonymous'}</h2>
                  <p className="text-sm font-medium text-slate-500">{selectedConversation.customer_email}</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                 <div className="text-right">
                    <div className="text-xs uppercase font-extrabold text-slate-400 mb-2 tracking-widest">Sentiment</div>
                    <div className="w-32">
                      <SentimentBar score={selectedConversation.sentiment_score || 0.5} />
                    </div>
                 </div>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-slate-50/20">
              {msgLoading ? (
                <div className="flex justify-center p-12">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
                </div>
              ) : messages.length > 0 ? (
                messages.map((msg, i) => {
                  const isAgent = msg.role === 'agent' || msg.role === 'system';
                  return (
                    <div key={i} className={`flex ${isAgent ? 'justify-end' : 'justify-start'} animate-fade-in`}>
                      <div className={`flex max-w-[85%] ${isAgent ? 'flex-row-reverse' : 'flex-row'}`}>
                        <div className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center shadow-sm ${
                          isAgent ? 'bg-blue-600 ml-4' : 'bg-white border border-slate-200 mr-4'
                        }`}>
                          {isAgent ? <Send size={18} className="text-white" /> : <User size={18} className="text-slate-500" />}
                        </div>
                        <div className={`p-5 rounded-[1.5rem] shadow-sm text-base leading-relaxed ${
                          isAgent 
                            ? 'bg-blue-600 text-white rounded-tr-none' 
                            : 'bg-white text-slate-700 border border-slate-100 rounded-tl-none shadow-md shadow-slate-100'
                        }`}>
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                          <div className={`text-xs mt-3 font-bold uppercase tracking-wider ${isAgent ? 'text-blue-100' : 'text-slate-400'}`}>
                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            {msg.delivery_status === 'sent' && isAgent && ' • Sent'}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="p-12 text-center text-slate-400 text-lg italic bg-white/50 rounded-3xl border-2 border-dashed border-slate-100">
                  No messages in this thread.
                </div>
              )}
            </div>

            <div className="p-6 border-t border-slate-100 bg-white">
              <div className="relative">
                <textarea 
                  disabled
                  placeholder="AI Agent is handling this conversation in real-time..."
                  className="w-full p-5 border-2 border-slate-100 rounded-2xl bg-slate-50 text-slate-400 text-base font-medium resize-none h-24 focus:outline-none cursor-not-allowed shadow-inner"
                />
                <div className="absolute right-5 bottom-5 text-xs font-extrabold text-slate-300 uppercase tracking-widest">Read Only Mode</div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-300 p-12">
            <div className="p-8 bg-slate-50 rounded-full mb-6">
              <MessageCircle size={80} className="opacity-20" />
            </div>
            <p className="text-xl font-bold">Select a conversation to view the thread</p>
            <p className="text-slate-400 mt-2">All interactions are logged in real-time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
