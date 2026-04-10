"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, Sparkles, ShieldCheck, Zap, Globe } from "lucide-react";

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
      if (!res.ok) throw new Error(data?.detail || 'System busy. Try again.');
      
      setStatus({ type: 'success', message: 'Transmission received.', response: data.response });
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden premium-gradient selection:bg-indigo-500/30 font-sans">
      
      {/* Dynamic Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/20 blur-[120px] rounded-full animate-float"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[30%] bg-blue-600/10 blur-[100px] rounded-full animate-float" style={{ animationDelay: '2s' }}></div>

      {/* Navigation */}
      <nav className="fixed top-0 w-full p-6 flex justify-between items-center z-50 bg-black/5 backdrop-blur-md border-b border-white/5 px-8 md:px-16 overflow-hidden">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-tr from-indigo-500 to-purple-500 p-2 rounded-xl shadow-lg shadow-indigo-500/20">
            <Zap className="text-white fill-white" size={20} />
          </div>
          <span className="text-xl font-bold tracking-tighter text-white">Digital FTE</span>
        </div>
        <Link href="/dashboard" className="px-6 py-2.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white text-sm font-semibold transition-all hover:scale-105 active:scale-95 flex items-center gap-2">
          Agent Console <ArrowRight size={16} />
        </Link>
      </nav>

      <main className="relative z-10 pt-32 pb-20 px-6 max-w-6xl mx-auto grid lg:grid-cols-2 gap-16 items-center min-h-screen">
        
        {/* Left: Content */}
        <div className="animate-reveal">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] uppercase tracking-[0.2em] font-bold text-indigo-300 mb-8 overflow-hidden">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            SYSTEMS ONLINE • REVISION 2.1
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-white leading-tight mb-8">
            The World's First <br/>
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">Living CRM</span>
          </h1>

          <p className="text-xl text-slate-400 mb-10 leading-relaxed max-w-xl">
             We deliver autonomous customer success pipelines that don't just store data—they think, respond, and act. 24/7 intelligence for enterprise scale.
          </p>

          <div className="grid grid-cols-2 gap-6 mb-12">
            <div className="flex items-center gap-3 text-slate-300">
               <ShieldCheck className="text-indigo-400" size={20} />
               <span className="text-sm font-medium">SOC2 Compliant</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300">
               <Globe className="text-indigo-400" size={20} />
               <span className="text-sm font-medium">Global Delivery</span>
            </div>
          </div>
        </div>

        {/* Right: Form */}
        <div className="animate-reveal overflow-hidden" style={{ animationDelay: '0.2s' }}>
          <div className="glass-panel p-1 rounded-[2rem]">
            <div className="bg-slate-900/40 rounded-[1.8rem] p-8 md:p-10 border border-white/5">
              
              {status.type === 'success' ? (
                <div className="py-12 flex flex-col items-center text-center space-y-6">
                  <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center animate-bounce">
                    <ShieldCheck size={32} />
                  </div>
                  <h3 className="text-3xl font-bold text-white italic">"Understood."</h3>
                  <div className="p-4 bg-white/5 rounded-xl border border-white/5 text-slate-300 text-sm italic leading-relaxed">
                    {status.response}
                  </div>
                  <button 
                    onClick={() => setStatus({type:'idle'})}
                    className="mt-6 px-8 py-3 rounded-full bg-white/10 hover:bg-white/20 text-white text-sm font-bold transition-all"
                  >
                    Open New Session
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                       <label className="text-[10px] uppercase tracking-widest font-bold text-slate-500 ml-1">Identity</label>
                       <input 
                         type="text" required placeholder="Full Name"
                         className="w-full bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-slate-600"
                         value={formData.name} onChange={e=>setFormData(p=>({...p, name: e.target.value}))}
                       />
                    </div>
                    <div className="space-y-2">
                       <label className="text-[10px] uppercase tracking-widest font-bold text-slate-500 ml-1">Terminal</label>
                       <input 
                         type="email" required placeholder="Professional Email"
                         className="w-full bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-slate-600"
                         value={formData.email} onChange={e=>setFormData(p=>({...p, email: e.target.value}))}
                       />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] uppercase tracking-widest font-bold text-slate-500 ml-1">Objective</label>
                    <input 
                      type="text" placeholder="Subject of inquiry"
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-slate-600"
                      value={formData.subject} onChange={e=>setFormData(p=>({...p, subject: e.target.value}))}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] uppercase tracking-widest font-bold text-slate-500 ml-1">Manifest</label>
                    <textarea 
                      required placeholder="Describe your operational needs..."
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all min-h-[140px] placeholder:text-slate-600"
                      value={formData.message} onChange={e=>setFormData(p=>({...p, message: e.target.value}))}
                    />
                  </div>

                  <button 
                    type="submit"
                    disabled={!isValid || status.type === 'loading'}
                    className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold text-sm shadow-xl shadow-indigo-600/20 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 flex items-center justify-center gap-3 mt-4"
                  >
                    {status.type === 'loading' ? <Loader2 className="animate-spin" size={20} /> : <>Initialize Intelligence Sequence <Sparkles size={18} /></>}
                  </button>
                  
                  {status.type === 'error' && (
                    <p className="text-center text-xs text-red-400 font-medium bg-red-400/10 py-3 rounded-lg border border-red-400/20">
                      {status.message}
                    </p>
                  )}
                </form>
              )}
            </div>
          </div>
        </div>
      </main>

      <footer className="relative z-10 w-full py-12 text-center text-slate-500 text-xs">
        <p className="tracking-widest uppercase">© {new Date().getFullYear()} Digital FTE Factory • Autonomous Operations Active</p>
      </footer>
    </div>
  );
}
