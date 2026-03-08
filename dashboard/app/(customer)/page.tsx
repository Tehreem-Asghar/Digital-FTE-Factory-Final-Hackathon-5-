'use client';

import { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import { 
  Send, 
  CheckCircle, 
  AlertCircle, 
  HelpCircle, 
  MessageCircle, 
  Zap, 
  Mail, 
  MessageSquare,
  ShieldCheck,
  Globe,
  Clock,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import Link from 'next/link';

const CATEGORIES = [
  { value: 'general', label: 'General Question' },
  { value: 'technical', label: 'Technical Support' },
  { value: 'billing', label: 'Billing Inquiry' },
  { value: 'bug_report', label: 'Bug Report' },
  { value: 'feedback', label: 'Feedback' }
];

type Channel = 'web' | 'email' | 'whatsapp';

export default function HelpCenterPage() {
  const [activeChannel, setActiveChannel] = useState<Channel>('web');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    category: 'general',
    message: ''
  });
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'polling' | 'responded' | 'error'>('idle');
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showEmailNotif, setShowEmailNotif] = useState(false);
  const [agentResponse, setAgentResponse] = useState<string | null>(null);
  const [conversationMessages, setConversationMessages] = useState<any[]>([]);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const pollCountRef = useRef(0);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // Start polling for web form AI response
  const startPolling = (tid: string) => {
    setStatus('polling');
    pollCountRef.current = 0;

    pollingRef.current = setInterval(async () => {
      pollCountRef.current += 1;

      // Stop after 60 polls (~3 minutes)
      if (pollCountRef.current > 60) {
        if (pollingRef.current) clearInterval(pollingRef.current);
        setStatus('success'); // Fallback to normal success view
        return;
      }

      try {
        const data = await api.getTicketStatus(tid);
        if (data.messages && data.messages.length > 0) {
          setConversationMessages(data.messages);
          // Check if there's an agent (outbound) response
          const agentMsg = data.messages.find((m: any) => m.role === 'agent');
          if (agentMsg) {
            if (pollingRef.current) clearInterval(pollingRef.current);
            setAgentResponse(agentMsg.content);
            setStatus('responded');
          }
        }
      } catch {
        // Silently retry on poll failure
      }
    }, 3000);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('submitting');
    setError(null);

    try {
      let data;
      if (activeChannel === 'web') {
        data = await api.submitSupport({
          name: formData.name,
          email: formData.email,
          subject: formData.subject,
          category: formData.category,
          message: formData.message
        });
      } else if (activeChannel === 'email') {
        data = await api.submitEmail({
          name: formData.name || 'Customer',
          email: formData.email,
          subject: formData.subject,
          message: formData.message
        });
      } else {
        data = await api.submitWhatsApp({
          phone: formData.phone,
          message: formData.message
        });
      }
      const tid = data.ticket_id || 'QUEUED';
      setTicketId(tid);

      if (activeChannel === 'web' && tid !== 'QUEUED') {
        // Web form: poll for on-screen response
        startPolling(tid);
      } else {
        // Email / WhatsApp: show success + notification
        setStatus('success');
        setShowEmailNotif(true);
        setTimeout(() => setShowEmailNotif(false), 6000);
      }
    } catch (err: any) {
      setError(err.message || 'Submission failed');
      setStatus('error');
    }
  };

  const getChannelStyles = () => {
    switch (activeChannel) {
      case 'web': return 'from-purple-600 to-indigo-600';
      case 'email': return 'from-blue-600 to-cyan-600';
      case 'whatsapp': return 'from-green-600 to-emerald-600';
    }
  };

  return (
    <div className="flex flex-col">
      {/* Email/WhatsApp Notification Popup (not shown for web form) */}
      {showEmailNotif && activeChannel !== 'web' && (
        <div className="fixed top-6 right-6 z-50 animate-fade-in">
          <div className="flex items-start gap-4 px-6 py-5 bg-white rounded-2xl shadow-2xl shadow-slate-300/40 border border-slate-200 max-w-md">
            <div className="flex-shrink-0 h-12 w-12 rounded-xl bg-green-100 flex items-center justify-center">
              {activeChannel === 'whatsapp' ? <MessageCircle size={24} className="text-green-600" /> : <Mail size={24} className="text-green-600" />}
            </div>
            <div className="flex-1">
              <p className="text-sm font-bold text-slate-900 mb-1">
                {activeChannel === 'whatsapp' ? 'WhatsApp Message Queued!' : 'Email Sent Successfully!'}
              </p>
              <p className="text-sm text-slate-500 leading-relaxed">
                {activeChannel === 'whatsapp'
                  ? <>A response will be sent to <span className="font-semibold text-slate-700">{formData.phone}</span> on WhatsApp.</>
                  : <>A response has been sent to <span className="font-semibold text-slate-700">{formData.email}</span>. Check your inbox for the AI response.</>
                }
              </p>
            </div>
            <button
              onClick={() => setShowEmailNotif(false)}
              className="flex-shrink-0 text-slate-400 hover:text-slate-600 transition-colors mt-0.5"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
            </button>
          </div>
        </div>
      )}

      {/* Dynamic Hero Section */}
      <section className="relative pt-16 pb-24 overflow-hidden">
        <div className="max-w-6xl mx-auto px-4 relative">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50/80 backdrop-blur-sm text-blue-600 font-bold text-sm mb-6 shadow-sm border border-blue-100">
              <Sparkles size={16} className="animate-pulse" /> <span>AI Agent is Online 24/7</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-extrabold text-slate-900 mb-6 tracking-tight leading-tight">
              Modern Support for <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">The Digital Age.</span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-500 max-w-3xl mx-auto leading-relaxed">
              Trusted by <span className="font-bold text-slate-700">15,000+ teams</span> across <span className="font-bold text-slate-700">40+ countries</span>.
              Experience lightning-fast AI-powered support across <span className="font-bold text-slate-700">Web, Email, and WhatsApp</span>.
              No queues, no waiting — just solutions in under 30 seconds.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-8 bg-white/80 backdrop-blur-md rounded-3xl border border-white shadow-xl shadow-slate-200/30 hover:shadow-2xl hover:-translate-y-1 transition-all group">
              <div className="h-14 w-14 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 mb-6 group-hover:bg-blue-600 group-hover:text-white transition-all">
                <Clock size={32} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Sub-30s Response</h3>
              <p className="text-slate-500 leading-relaxed font-medium">Our AI employee handles <span className="font-bold text-slate-700">90% of queries</span> in under 30 seconds with <span className="font-bold text-slate-700">98% accuracy</span>.</p>
            </div>
            <div className="p-8 bg-white/80 backdrop-blur-md rounded-3xl border border-white shadow-xl shadow-slate-200/30 hover:shadow-2xl hover:-translate-y-1 transition-all group">
              <div className="h-14 w-14 rounded-2xl bg-purple-50 flex items-center justify-center text-purple-600 mb-6 group-hover:bg-purple-600 group-hover:text-white transition-all">
                <Globe size={32} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Omnichannel Flow</h3>
              <p className="text-slate-500 leading-relaxed font-medium">Start on Web, follow up on WhatsApp, and get email receipts—all <span className="font-bold text-slate-700">synced perfectly</span>.</p>
            </div>
            <div className="p-8 bg-white/80 backdrop-blur-md rounded-3xl border border-white shadow-xl shadow-slate-200/30 hover:shadow-2xl hover:-translate-y-1 transition-all group">
              <div className="h-14 w-14 rounded-2xl bg-green-50 flex items-center justify-center text-green-600 mb-6 group-hover:bg-green-600 group-hover:text-white transition-all">
                <ShieldCheck size={32} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Enterprise Security</h3>
              <p className="text-slate-500 leading-relaxed font-medium"><span className="font-bold text-slate-700">SOC 2 Type II compliant</span>. Your data is encrypted with bank-grade security protocols.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Main interaction section */}
      <section className="py-20 max-w-6xl mx-auto w-full px-4 grid grid-cols-1 lg:grid-cols-12 gap-16 items-start">
        {/* Left Side: Copy and Stats */}
        <div className="lg:col-span-5 space-y-10">
          <div>
            <h2 className="text-3xl font-extrabold text-slate-900 mb-6">Test the Multi-Channel Power</h2>
            <p className="text-lg text-slate-600 leading-relaxed font-medium">
              We've built three distinct handlers. Use the tabs to test how our AI processes messages differently across Web, Email, and WhatsApp.
            </p>
          </div>

          <div className="space-y-6">
            <div className="flex items-center gap-4 p-5 bg-white/60 backdrop-blur-sm rounded-2xl border border-white shadow-sm hover:bg-white transition-all group">
              <div className="h-12 w-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                <Zap size={24} />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-[0.2em]">Real-time Ingestion</p>
                <p className="text-lg font-bold text-slate-900 uppercase">Kafka Stream Enabled</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-5 bg-white/60 backdrop-blur-sm rounded-2xl border border-white shadow-sm hover:bg-white transition-all group">
              <div className="h-12 w-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-all">
                <MessageSquare size={24} />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-[0.2em]">Conversation Tracking</p>
                <p className="text-lg font-bold text-slate-900 uppercase">Cross-Channel Continuity</p>
              </div>
            </div>
          </div>

          <div className="p-8 bg-slate-900 rounded-[2.5rem] text-white relative overflow-hidden shadow-2xl group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-700">
              <ShieldCheck size={160} />
            </div>
            <h4 className="text-2xl font-bold mb-2">Need to track?</h4>
            <p className="text-slate-400 text-lg mb-8 leading-relaxed">Already submitted a request? Check your live status here.</p>
            <Link
              href="/portal/status"
              className="inline-flex items-center gap-3 px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-bold transition-all shadow-lg shadow-blue-900/20"
            >
              Track Ticket <ArrowRight size={20} />
            </Link>
          </div>
        </div>

        {/* Right Side: Tabbed Form */}
        <div className="lg:col-span-7 w-full">
          <div className="bg-white/90 backdrop-blur-xl rounded-[3rem] border border-white shadow-[0_32px_64px_-12px_rgba(0,0,0,0.1)] overflow-hidden animate-fade-in relative">
            {/* Form Headers / Tabs */}
            <div className="flex p-3 bg-slate-100/50 border-b border-slate-100">
              <button 
                onClick={() => { setActiveChannel('web'); setStatus('idle'); if (pollingRef.current) clearInterval(pollingRef.current); }}
                className={`flex-1 flex items-center justify-center gap-2 py-4 rounded-2xl font-bold transition-all ${activeChannel === 'web' ? 'bg-white text-purple-600 shadow-md' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <MessageSquare size={20} /> Web
              </button>
              <button 
                onClick={() => { setActiveChannel('email'); setStatus('idle'); if (pollingRef.current) clearInterval(pollingRef.current); }}
                className={`flex-1 flex items-center justify-center gap-2 py-4 rounded-2xl font-bold transition-all ${activeChannel === 'email' ? 'bg-white text-blue-600 shadow-md' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <Mail size={20} /> Email
              </button>
              <button 
                onClick={() => { setActiveChannel('whatsapp'); setStatus('idle'); if (pollingRef.current) clearInterval(pollingRef.current); }}
                className={`flex-1 flex items-center justify-center gap-2 py-4 rounded-2xl font-bold transition-all ${activeChannel === 'whatsapp' ? 'bg-white text-green-600 shadow-md' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <MessageCircle size={20} /> WhatsApp
              </button>
            </div>

            <div className={`h-2 bg-gradient-to-r ${getChannelStyles()}`}></div>

            {/* Polling state: waiting for AI response (web form only) */}
            {status === 'polling' ? (
              <div className="p-12 text-center space-y-8 animate-fade-in">
                <div className="inline-flex items-center justify-center h-24 w-24 rounded-full bg-purple-50">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                </div>
                <h2 className="text-3xl font-extrabold text-slate-900">Processing Your Request...</h2>
                <p className="text-xl text-slate-500 max-w-md mx-auto leading-relaxed">
                  Our AI agent is analyzing your message. The response will appear here shortly.
                </p>
                <div className="bg-slate-50 p-8 rounded-3xl inline-block border border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Tracking ID</p>
                  <span className="text-3xl font-mono font-extrabold text-slate-900">{ticketId}</span>
                </div>
                <div className="flex items-center gap-3 justify-center text-purple-600">
                  <div className="animate-pulse flex gap-1">
                    <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                    <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                    <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                  </div>
                  <span className="text-base font-semibold">AI is composing a response</span>
                </div>
              </div>

            ) : status === 'responded' ? (
              /* AI response received — show chat on screen (web form) */
              <div className="p-8 md:p-12 space-y-8 animate-fade-in">
                <div className="text-center space-y-4">
                  <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-green-50">
                    <CheckCircle size={40} className="text-green-600" />
                  </div>
                  <h2 className="text-2xl font-extrabold text-slate-900">AI Response Ready</h2>
                  <div className="bg-slate-50 px-6 py-3 rounded-2xl inline-block border border-slate-100">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Tracking ID</p>
                    <span className="text-xl font-mono font-extrabold text-slate-900">{ticketId}</span>
                  </div>
                </div>

                {/* Conversation chat bubbles */}
                <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                  {conversationMessages.map((msg: any, i: number) => (
                    <div key={i} className={`p-5 rounded-2xl text-base leading-relaxed ${
                      msg.role === 'customer'
                        ? 'bg-slate-50 text-slate-700 mr-12 border border-slate-100'
                        : 'bg-purple-600 text-white ml-12 shadow-xl shadow-purple-100'
                    }`}>
                      <p className={`font-bold mb-2 uppercase text-xs tracking-widest ${msg.role === 'customer' ? 'text-slate-400' : 'text-purple-200'}`}>
                        {msg.role === 'customer' ? 'You' : 'AI Assistant'}
                      </p>
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  ))}
                </div>

                <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                  <button
                    onClick={() => {
                      setStatus('idle');
                      setAgentResponse(null);
                      setConversationMessages([]);
                    }}
                    className="px-10 py-4 text-white rounded-2xl font-bold text-lg hover:scale-105 transition-all shadow-xl bg-gradient-to-r from-purple-600 to-indigo-600"
                  >
                    Send Another Request
                  </button>
                  <a
                    href={`/portal/status`}
                    className="px-10 py-4 text-purple-600 rounded-2xl font-bold text-lg hover:bg-purple-50 transition-all border-2 border-purple-200 text-center"
                  >
                    Track Ticket
                  </a>
                </div>
              </div>

            ) : status === 'success' ? (
              /* Email / WhatsApp success */
              <div className="p-12 text-center space-y-8 animate-fade-in">
                <div className={`inline-flex items-center justify-center h-24 w-24 rounded-full bg-slate-50`}>
                  <CheckCircle size={48} className={activeChannel === 'email' ? 'text-blue-600' : 'text-green-600'} />
                </div>
                <h2 className="text-3xl font-extrabold text-slate-900">Successfully Queued!</h2>
                <p className="text-xl text-slate-500 max-w-md mx-auto leading-relaxed">
                  Our AI agent is processing your {activeChannel} request.
                </p>
                <div className="bg-slate-50 p-8 rounded-3xl inline-block border border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Live Tracking ID</p>
                  <span className="text-3xl font-mono font-extrabold text-slate-900">{ticketId}</span>
                </div>

                {/* Email/WhatsApp notification banner */}
                <div className="flex items-center gap-4 p-5 bg-green-50 border border-green-200 rounded-2xl max-w-lg mx-auto">
                  <div className="h-10 w-10 rounded-xl bg-green-100 flex items-center justify-center flex-shrink-0">
                    {activeChannel === 'whatsapp' ? <MessageCircle size={20} className="text-green-600" /> : <Mail size={20} className="text-green-600" />}
                  </div>
                  <p className="text-base text-green-800 font-medium text-left">
                    {activeChannel === 'whatsapp'
                      ? <>A WhatsApp response will be sent to <span className="font-bold">{formData.phone}</span>.</>
                      : <>An email response will be sent to <span className="font-bold">{formData.email}</span>. Check your inbox!</>
                    }
                  </p>
                </div>

                <div>
                  <button
                    onClick={() => setStatus('idle')}
                    className={`px-10 py-4 text-white rounded-2xl font-bold text-lg hover:scale-105 transition-all shadow-xl bg-gradient-to-r ${getChannelStyles()}`}
                  >
                    Send Another Test
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="p-8 md:p-12 space-y-8">
                {activeChannel === 'web' && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      <div className="space-y-3">
                        <label className="text-base font-bold text-slate-700 ml-1">Full Name</label>
                        <input 
                          type="text" name="name" required value={formData.name} onChange={handleChange}
                          placeholder="John Doe"
                          className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring text-lg"
                        />
                      </div>
                      <div className="space-y-3">
                        <label className="text-base font-bold text-slate-700 ml-1">Email Address</label>
                        <input 
                          type="email" name="email" required value={formData.email} onChange={handleChange}
                          placeholder="john@company.com"
                          className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring text-lg"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      <div className="space-y-3">
                        <label className="text-base font-bold text-slate-700 ml-1">Subject</label>
                        <input 
                          type="text" name="subject" required value={formData.subject} onChange={handleChange}
                          placeholder="Issue summary"
                          className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring text-lg"
                        />
                      </div>
                      <div className="space-y-3">
                        <label className="text-base font-bold text-slate-700 ml-1">Category</label>
                        <select 
                          name="category" value={formData.category} onChange={handleChange}
                          className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring appearance-none cursor-pointer text-lg"
                        >
                          {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                        </select>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <label className="text-base font-bold text-slate-700 ml-1">Message</label>
                      <textarea 
                        name="message" required value={formData.message} onChange={handleChange}
                        placeholder="Tell us everything..."
                        rows={4}
                        className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring resize-none text-lg"
                      ></textarea>
                    </div>
                  </>
                )}

                {activeChannel === 'email' && (
                  <>
                    <div className="space-y-3">
                      <label className="text-base font-bold text-slate-700 ml-1">From Email</label>
                      <input 
                        type="email" name="email" required value={formData.email} onChange={handleChange}
                        placeholder="your-email@example.com"
                        className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring text-lg"
                      />
                    </div>
                    <div className="space-y-3">
                      <label className="text-base font-bold text-slate-700 ml-1">Subject</label>
                      <input 
                        type="text" name="subject" required value={formData.subject} onChange={handleChange}
                        placeholder="Email Subject"
                        className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring text-lg"
                      />
                    </div>
                    <div className="space-y-3">
                      <label className="text-base font-bold text-slate-700 ml-1">Email Body</label>
                      <textarea 
                        name="message" required value={formData.message} onChange={handleChange}
                        placeholder="Write your email content here..."
                        rows={6}
                        className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring resize-none text-lg"
                      ></textarea>
                    </div>
                  </>
                )}

                {activeChannel === 'whatsapp' && (
                  <>
                    <div className="space-y-3">
                      <label className="text-base font-bold text-slate-700 ml-1">WhatsApp Number</label>
                      <input 
                        type="text" name="phone" required value={formData.phone} onChange={handleChange}
                        placeholder="+1234567890"
                        className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring text-lg"
                      />
                    </div>
                    <div className="space-y-3">
                      <label className="text-base font-bold text-slate-700 ml-1">Message</label>
                      <div className="relative">
                        <textarea 
                          name="message" required value={formData.message} onChange={handleChange}
                          placeholder="Type your WhatsApp message..."
                          rows={6}
                          className="w-full px-5 py-4 bg-slate-50/50 border border-slate-200 rounded-2xl focus-ring resize-none pr-12 text-lg"
                        ></textarea>
                        <div className="absolute right-5 bottom-5 text-green-500">
                          <MessageCircle size={28} />
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {error && (
                  <div className="flex items-center gap-3 text-red-600 bg-red-50 p-5 rounded-2xl border border-red-100 animate-fade-in">
                    <AlertCircle size={22} /> <span className="text-lg font-medium">{error}</span>
                  </div>
                )}

                <button 
                  type="submit" disabled={status === 'submitting'}
                  className={`w-full py-5 text-white rounded-2xl font-bold hover:scale-[1.01] active:scale-[0.99] disabled:bg-slate-300 disabled:cursor-not-allowed transition-all shadow-xl flex items-center justify-center gap-3 text-xl bg-gradient-to-r ${getChannelStyles()}`}
                >
                  {status === 'submitting' ? (
                    <>
                      <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-white"></div>
                      Processing...
                    </>
                  ) : (
                    <>
                      <Send size={22} /> {activeChannel === 'web' ? 'Submit Ticket' : activeChannel === 'email' ? 'Send Email' : 'Send WhatsApp'}
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* Brand Promise Section */}
      <section className="py-24 bg-transparent relative z-10 border-t border-slate-200">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 uppercase tracking-wider">Our Support Promise</h2>
            <p className="text-xl text-slate-500">How we serve our 15,000+ teams worldwide</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8 lg:gap-12 text-center">
            <div className="space-y-3 md:space-y-4 p-4 md:p-6 lg:p-8 rounded-3xl bg-white/50 border border-white shadow-sm hover:shadow-lg transition-all">
              <div className="text-blue-600 font-black text-3xl md:text-4xl mb-2 italic">01</div>
              <h4 className="text-lg md:text-xl font-bold text-slate-900">Empathy First</h4>
              <p className="text-sm md:text-base text-slate-500 leading-relaxed font-medium">We acknowledge your challenges before jumping to technical steps.</p>
            </div>
            <div className="space-y-3 md:space-y-4 p-4 md:p-6 lg:p-8 rounded-3xl bg-white/50 border border-white shadow-sm hover:shadow-lg transition-all">
              <div className="text-indigo-600 font-black text-3xl md:text-4xl mb-2 italic">02</div>
              <h4 className="text-lg md:text-xl font-bold text-slate-900">Radical Honesty</h4>
              <p className="text-sm md:text-base text-slate-500 leading-relaxed font-medium">If we don't know the answer, we connect you with a human expert immediately.</p>
            </div>
            <div className="space-y-3 md:space-y-4 p-4 md:p-6 lg:p-8 rounded-3xl bg-white/50 border border-white shadow-sm hover:shadow-lg transition-all">
              <div className="text-purple-600 font-black text-3xl md:text-4xl mb-2 italic">03</div>
              <h4 className="text-lg md:text-xl font-bold text-slate-900">No Jargon</h4>
              <p className="text-sm md:text-base text-slate-500 leading-relaxed font-medium">We speak like teammates, providing clear and actionable instructions.</p>
            </div>
            <div className="space-y-3 md:space-y-4 p-4 md:p-6 lg:p-8 rounded-3xl bg-white/50 border border-white shadow-sm hover:shadow-lg transition-all">
              <div className="text-emerald-600 font-black text-3xl md:text-4xl mb-2 italic">04</div>
              <h4 className="text-lg md:text-xl font-bold text-slate-900">24/7 Availability</h4>
              <p className="text-sm md:text-base text-slate-500 leading-relaxed font-medium">Day or night, our AI agent is ready to solve your workflow blockers.</p>
            </div>
          </div>

          <div className="mt-20 pt-16 border-t border-slate-200/60 flex flex-wrap justify-center items-center gap-x-16 gap-y-8 grayscale opacity-50 hover:grayscale-0 hover:opacity-100 transition-all duration-700">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 bg-slate-900 rounded-lg"></div>
              <span className="text-xl font-black text-slate-900 tracking-tighter">KANBIX PRO</span>
            </div>
            <span className="text-xl font-bold text-slate-400 italic font-medium">Trusted by <span className="text-slate-700 not-italic">15,000+ teams</span> and <span className="text-slate-700 not-italic">60,000+ users</span></span>
            <div className="flex items-center gap-2 font-bold text-slate-900">
              <Globe size={20} className="text-blue-500" /> <span className="text-slate-700">40+ COUNTRIES</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
