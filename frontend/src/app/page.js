"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, PlayCircle, Bot, Mail, AlignLeft, Send, Check } from "lucide-react";

export default function Home() {
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' });
  const [status, setStatus] = useState({ type: 'idle', message: '' });
  const [liveFeed, setLiveFeed] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const feedEndRef = useRef(null);

  const isValid = formData.email?.includes('@') && formData.message?.length > 5;

  // Poll Live System Feed
  useEffect(() => {
    const fetchFeed = async () => {
      try {
        const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${BACKEND}/api/v1/reports/live-feed?limit=5`);
        if (res.ok) {
          const data = await res.json();
          setLiveFeed(data);
        }
      } catch (e) { /* silent fail for clean UI */ }
    };
    
    fetchFeed();
    const interval = setInterval(fetchFeed, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid || status.type === 'loading') return;
    
    setStatus({ type: 'loading', message: '' });
    setIsProcessing(true);

    const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    try {
      const res = await fetch(`${BACKEND}/api/v1/inquiries/webform`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: 'webform',
          subject: formData.subject || 'General Request',
          body: formData.message,
          sender: formData.email,
          metadata: { name: formData.name },
        }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'System busy. Please try again.');
      
      // Intentional delay for refined UX feel
      setTimeout(() => {
        setStatus({ type: 'success', message: 'Action complete.', response: data.response });
        setIsProcessing(false);
      }, 1000);
      
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF9F7] text-[#1A1C20] font-sans selection:bg-brand-200">
      
      {/* Refined Navigation */}
      <nav className="w-full px-6 py-5 md:px-12 flex justify-between items-center bg-[#FAF9F7]/80 backdrop-blur-md sticky top-0 z-50 border-b border-black/5">
        <div className="flex items-center gap-3">
          <div className="bg-[#1A1C20] p-1.5 rounded flex items-center justify-center">
            <Bot className="text-white" size={16} />
          </div>
          <span className="font-serif text-lg font-semibold tracking-tight text-[#1A1C20]">Digital FTE</span>
        </div>
        <Link href="/dashboard" className="text-sm font-medium text-[#63656A] hover:text-[#1A1C20] transition-colors flex items-center gap-2 group">
          Go to Console <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
        </Link>
      </nav>

      <main className="max-w-[1200px] mx-auto px-6 py-16 md:py-24 grid lg:grid-cols-12 gap-16 lg:gap-24 relative">
        
        {/* LEFT COLUMN: Narrative & Live System Feel */}
        <div className="lg:col-span-7 flex flex-col justify-center animate-fade-in-up">
          
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-black/5 bg-black/[0.02] text-xs font-semibold text-[#63656A] mb-8 w-max">
            <div className="w-2 h-2 rounded-full bg-brand-600 animate-pulse"></div>
            Autonomous Workflow Active
          </div>

          <h1 className="font-serif text-5xl md:text-7xl lg:text-[5.5rem] leading-[1.05] tracking-tight text-[#1A1C20] mb-8 font-medium">
            Intelligence <br/>
            <span className="text-[#84878E] italic">that operates.</span>
          </h1>
          
          <p className="text-[#63656A] text-lg md:text-xl leading-relaxed max-w-lg mb-14 font-light">
            An elegant, autonomous customer success foundation. It reasons through inquiries, assigns ownership, and logs every action—so your team can focus on the relationships that matter.
          </p>

          {/* Clean Enterprise Log (Replaces Hacker Terminal) */}
          <div className="w-full max-w-lg border border-black/5 bg-white rounded-xl shadow-sm overflow-hidden flex flex-col h-[260px]">
            <div className="bg-[#F5F4F1] px-5 py-3 border-b border-black/5 flex items-center justify-between">
              <span className="text-xs font-semibold text-[#63656A] tracking-wide uppercase">System Activity Log</span>
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-brand-600">
                <PlayCircle size={12} /> Syncing
              </div>
            </div>
            
            <div className="p-5 flex-1 overflow-y-auto flex flex-col gap-4 text-sm font-sans bg-[#FCFBF9]">
                {liveFeed.length > 0 ? liveFeed.map((log, i) => (
                  <div key={log.id} className="flex gap-4 items-start pb-4 border-b border-black/[0.03] last:border-0 last:pb-0 fade-in" style={{ animationDelay: `${i*100}ms` }}>
                    <div className="text-[#A1A3A8] text-xs font-mono pt-0.5 whitespace-nowrap">
                      {log.timestamp.split('T')[1].split('.')[0]}
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span className="font-semibold text-[#35221b] text-xs uppercase tracking-wide">
                        {log.action.replace(/_/g, ' ')}
                      </span>
                      <span className="text-[#63656A] font-light leading-relaxed">
                        {log.message}
                      </span>
                    </div>
                  </div>
                )) : (
                  <div className="h-full flex items-center justify-center text-[#A1A3A8] italic font-light text-sm">
                     Waiting for system events...
                  </div>
                )}
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: Action Form */}
        <div className="lg:col-span-5 flex flex-col justify-center animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          
          <div className="bg-white rounded-2xl p-8 border border-black/5 shadow-xl shadow-black/[0.03] relative overflow-hidden transition-all duration-500">
             
             {/* Progress indicator bar at top */}
             {isProcessing && (
               <div className="absolute top-0 left-0 w-full h-1 bg-black/5">
                 <div className="h-full bg-[#1A1C20] animate-pulse"></div>
               </div>
             )}

             {status.type === 'success' ? (
               <div className="py-12 flex flex-col items-center text-center space-y-6 animate-fade-in-up">
                  <div className="w-14 h-14 rounded-full bg-green-50 border border-green-100 flex items-center justify-center text-green-600 mb-2">
                     <Check size={28} />
                  </div>
                  <h3 className="font-serif text-3xl font-medium text-[#1A1C20]">Received</h3>
                  <div className="p-5 bg-[#FAF9F7] rounded-lg border border-black/5 text-[#63656A] text-sm leading-relaxed font-light mb-4">
                     "{status.response}"
                  </div>
                  <button 
                    onClick={() => setStatus({type:'idle'})}
                    className="text-sm font-semibold text-[#1A1C20] hover:text-brand-600 transition-colors uppercase tracking-widest pt-4"
                  >
                    Submit Another Request
                  </button>
               </div>
             ) : (
               <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                 <div className="mb-2">
                   <h2 className="text-xl font-semibold text-[#1A1C20] mb-1 font-serif">Interact with Digital FTE</h2>
                   <p className="text-sm text-[#84878E] font-light">Submit an inquiry and watch the system process it in real-time.</p>
                 </div>

                 <div className="space-y-4">
                   <div>
                     <label className="block text-xs font-semibold text-[#63656A] uppercase tracking-wide mb-1.5 ml-1">Name</label>
                     <input 
                       type="text" required placeholder="Jane Doe"
                       className="input-anthropic w-full"
                       value={formData.name} onChange={e=>setFormData(p=>({...p, name: e.target.value}))}
                     />
                   </div>

                   <div>
                     <label className="block text-xs font-semibold text-[#63656A] uppercase tracking-wide mb-1.5 ml-1">Email <span className="text-brand-600 font-normal">*</span></label>
                     <input 
                       type="email" required placeholder="jane@example.com"
                       className="input-anthropic w-full"
                       value={formData.email} onChange={e=>setFormData(p=>({...p, email: e.target.value}))}
                     />
                   </div>

                   <div>
                     <label className="block text-xs font-semibold text-[#63656A] uppercase tracking-wide mb-1.5 ml-1">Topic</label>
                     <input 
                       type="text" placeholder="Partnership inquiry..."
                       className="input-anthropic w-full"
                       value={formData.subject} onChange={e=>setFormData(p=>({...p, subject: e.target.value}))}
                     />
                   </div>

                   <div>
                     <label className="block text-xs font-semibold text-[#63656A] uppercase tracking-wide mb-1.5 ml-1">Request Details <span className="text-brand-600 font-normal">*</span></label>
                     <textarea 
                       required placeholder="How can the autonomous workforce assist you today?"
                       className="input-anthropic w-full min-h-[130px] resize-y"
                       value={formData.message} onChange={e=>setFormData(p=>({...p, message: e.target.value}))}
                     />
                   </div>
                 </div>

                 <button 
                   type="submit"
                   disabled={!isValid || status.type === 'loading'}
                   className="mt-4 w-full py-3.5 rounded-lg bg-[#1A1C20] hover:bg-[#2C2E33] text-white font-medium text-sm transition-all focus:ring-2 focus:ring-offset-2 focus:ring-[#1A1C20] disabled:opacity-40 flex items-center justify-center gap-2 h-[52px]"
                 >
                   {status.type === 'loading' ? (
                     <Loader2 className="animate-spin text-white/70" size={18} />
                   ) : (
                     <>Submit Request <Send size={16} className="text-white/80" /></>
                   )}
                 </button>
                 
                 {status.type === 'error' && (
                   <p className="text-center text-xs text-red-600 font-medium mt-2 bg-red-50 p-2 rounded border border-red-100">
                     {status.message}
                   </p>
                 )}
               </form>
             )}
          </div>
        </div>
      </main>

      {/* Elegant Footer */}
      <footer className="w-full py-10 border-t border-black/5 mt-10">
        <div className="max-w-[1200px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-medium text-[#A1A3A8] uppercase tracking-widest">
          <span>Digital FTE © {new Date().getFullYear()}</span>
          <span>Designed for Elegance & Autonomy</span>
        </div>
      </footer>
    </div>
  );
}
