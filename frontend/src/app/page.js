"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, Command, Shield, Activity, Fingerprint } from "lucide-react";

export default function Home() {
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' });
  const [status, setStatus] = useState({ type: 'idle', message: '' });

  const isValid = formData.email?.includes('@') && formData.message?.length > 5;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid || status.type === 'loading') return;
    setStatus({ type: 'loading', message: '' });

    const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    try {
      const res = await fetch(`${BACKEND}/api/v1/inquiries/webform`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: 'webform',
          subject: formData.subject || 'General Enquiry',
          body: formData.message,
          sender: formData.email,
          metadata: { name: formData.name },
        }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'System unavailable');
      
      setStatus({ type: 'success', message: 'Transmission received.', response: data.response });
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#050505] selection:bg-white/10 font-sans antialiased text-slate-200">
      
      {/* Background: Subtle Grain & Depth */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-soft-light pointer-events-none"></div>
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-gradient-to-b from-indigo-500/10 to-transparent blur-[120px] pointer-events-none"></div>

      {/* Navigation */}
      <nav className="fixed top-0 w-full p-8 flex justify-between items-center z-50">
        <div className="flex items-center gap-2 group cursor-default">
          <div className="w-8 h-8 border border-white/20 rounded-lg flex items-center justify-center bg-white/5 transition-colors group-hover:border-white/40">
            <Command size={14} className="text-white/70" />
          </div>
          <span className="text-sm font-bold tracking-[0.2em] uppercase text-white/90">Digital FTE</span>
        </div>
        <Link href="/dashboard" className="text-xs font-bold tracking-widest uppercase py-2 px-4 border border-white/10 rounded hover:bg-white/5 transition-all flex items-center gap-3">
          Console <ArrowRight size={12} />
        </Link>
      </nav>

      <main className="relative z-10 pt-40 pb-20 px-6 max-w-5xl mx-auto flex flex-col items-center">
        
        {/* Minimal Badge */}
        <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full border border-white/5 bg-white/[0.02] text-[10px] uppercase tracking-[0.3em] font-medium text-white/40 mb-12 animate-reveal">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white/20 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-white/40"></span>
          </span>
          Autonomous Instance // v.2.4
        </div>

        {/* Headline: Clean & Brutalist */}
        <div className="text-center mb-16 animate-reveal" style={{ animationDelay: '0.1s' }}>
          <h1 className="text-4xl md:text-6xl font-black text-white leading-tight mb-6 tracking-tight">
            INTELLIGENT <br/>
            <span className="text-white/30">OPERATIONAL SCALE</span>
          </h1>
          <p className="text-base md:text-lg text-white/40 max-w-xl mx-auto leading-relaxed font-medium">
            Deploy cognitive customer success pipelines. <br/>
            Automated reasoning for the high-frequency enterprise.
          </p>
        </div>

        {/* Form Section: Minimal Glass */}
        <div className="w-full max-w-lg animate-reveal" style={{ animationDelay: '0.2s' }}>
          <div className="border border-white/10 rounded-2xl bg-white/[0.01] p-1 backdrop-blur-sm">
            <div className="bg-black/40 rounded-[calc(1rem-2px)] p-8 md:p-10">
              
              {status.type === 'success' ? (
                <div className="py-10 flex flex-col items-center text-center animate-reveal">
                  <div className="w-12 h-12 rounded border border-white/20 flex items-center justify-center mb-6">
                    <Fingerprint size={20} className="text-white/60" />
                  </div>
                  <h3 className="text-lg font-bold text-white uppercase tracking-widest mb-4">Transmission Logged</h3>
                  <div className="p-5 bg-white/[0.02] border border-white/5 rounded-lg text-white/50 text-[13px] leading-relaxed font-mono">
                    {status.response}
                  </div>
                  <button 
                    onClick={() => setStatus({type:'idle'})}
                    className="mt-10 text-[10px] uppercase font-bold tracking-[0.2em] text-white/40 underline hover:text-white transition-colors"
                  >
                    Initialize New Request
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-8">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-3">
                       <label className="text-[10px] uppercase tracking-widest font-bold text-white/30 px-1">Identity</label>
                       <input 
                         type="text" required placeholder="User-01"
                         className="w-full bg-transparent border-b border-white/10 px-1 py-3 text-sm text-white focus:outline-none focus:border-white/40 transition-all placeholder:text-white/10"
                         value={formData.name} onChange={e=>setFormData(p=>({...p, name: e.target.value}))}
                       />
                    </div>
                    <div className="space-y-3">
                       <label className="text-[10px] uppercase tracking-widest font-bold text-white/30 px-1">Network</label>
                       <input 
                         type="email" required placeholder="name@domain.com"
                         className="w-full bg-transparent border-b border-white/10 px-1 py-3 text-sm text-white focus:outline-none focus:border-white/40 transition-all placeholder:text-white/10"
                         value={formData.email} onChange={e=>setFormData(p=>({...p, email: e.target.value}))}
                       />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="text-[10px] uppercase tracking-widest font-bold text-white/30 px-1">Classification</label>
                    <input 
                      type="text" placeholder="Objective summary"
                      className="w-full bg-transparent border-b border-white/10 px-1 py-3 text-sm text-white focus:outline-none focus:border-white/40 transition-all placeholder:text-white/10"
                      value={formData.subject} onChange={e=>setFormData(p=>({...p, subject: e.target.value}))}
                    />
                  </div>

                  <div className="space-y-3">
                    <label className="text-[10px] uppercase tracking-widest font-bold text-white/30 px-1">Data Payload</label>
                    <textarea 
                      required placeholder="Enter operational request details..."
                      className="w-full bg-transparent border-b border-white/10 px-1 py-3 text-sm text-white focus:outline-none focus:border-white/40 transition-all min-h-[100px] resize-none placeholder:text-white/10"
                      value={formData.message} onChange={e=>setFormData(p=>({...p, message: e.target.value}))}
                    />
                  </div>

                  <button 
                    type="submit"
                    disabled={!isValid || status.type === 'loading'}
                    className="w-full py-4 rounded bg-white text-black font-black text-[11px] uppercase tracking-[0.3em] overflow-hidden hover:bg-slate-200 active:scale-95 transition-all disabled:opacity-20 mt-4 shadow-xl shadow-white/5"
                  >
                    {status.type === 'loading' ? <Loader2 className="animate-spin mx-auto" size={16} /> : "Transmit Process"}
                  </button>
                  
                  {status.type === 'error' && (
                    <div className="p-3 border border-red-500/20 bg-red-500/5 text-[10px] font-bold text-red-500/60 text-center uppercase tracking-widest">
                      {status.message}
                    </div>
                  )}
                </form>
              )}
            </div>
          </div>
        </div>

        {/* Minimal Proof Points */}
        <div className="mt-24 grid grid-cols-3 gap-12 border-t border-white/5 pt-12 animate-reveal" style={{ animationDelay: '0.3s' }}>
           <div className="flex flex-col gap-2">
             <span className="text-[10px] uppercase tracking-widest font-bold text-white/20">Protocol</span>
             <span className="text-xs font-bold text-white/60 flex items-center gap-2"><Shield size={12} /> SSL-256</span>
           </div>
           <div className="flex flex-col gap-2">
             <span className="text-[10px] uppercase tracking-widest font-bold text-white/20">Response</span>
             <span className="text-xs font-bold text-white/60 flex items-center gap-2"><Activity size={12} /> &lt; 200ms</span>
           </div>
           <div className="flex flex-col gap-2">
             <span className="text-[10px] uppercase tracking-widest font-bold text-white/20">Uptime</span>
             <span className="text-xs font-bold text-white/60 tracking-widest">99.9%</span>
           </div>
        </div>
      </main>

      <footer className="py-12 text-center text-[10px] tracking-[0.5em] text-white/10 font-bold uppercase overflow-hidden">
        Digital FTE Factory // 2026 Internal Utility
      </footer>
    </div>
  );
}
