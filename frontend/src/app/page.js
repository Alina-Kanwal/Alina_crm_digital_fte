"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, Bot, Terminal, Cpu, Database, Network } from "lucide-react";

export default function Home() {
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' });
  const [status, setStatus] = useState({ type: 'idle', message: '' });
  const [liveFeed, setLiveFeed] = useState([]);
  const [isNeuralActive, setIsNeuralActive] = useState(false);
  
  const feedRef = useRef(null);

  const isValid = formData.email?.includes('@') && formData.message?.length > 5;

  // Poll Live Feed
  useEffect(() => {
    const fetchFeed = async () => {
      try {
        const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${BACKEND}/api/v1/reports/live-feed?limit=5`);
        if (res.ok) {
          const data = await res.json();
          setLiveFeed(data);
        }
      } catch (e) { /* silent fail */ }
    };
    
    fetchFeed();
    const interval = setInterval(fetchFeed, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid || status.type === 'loading') return;
    
    setStatus({ type: 'loading', message: '' });
    setIsNeuralActive(true); // Trigger Neural Pulse

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
      if (!res.ok) throw new Error(data?.detail || 'Logic overflow. Retrying...');
      
      setTimeout(() => {
        setStatus({ type: 'success', message: 'Cognitive Cycle Completed.', response: data.response });
        setIsNeuralActive(false);
      }, 1500); // Artificial delay to show "Thinking"
      
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
      setIsNeuralActive(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#020203] selection:bg-indigo-500/30 font-sans antialiased text-slate-400">
      
      {/* 3D Neural Background Effect */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
         <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-600/10 blur-[150px] rounded-full"></div>
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 w-full p-8 flex justify-between items-center z-50 mix-blend-difference">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 border border-white/10 rounded-full flex items-center justify-center bg-white/5 backdrop-blur-md">
            <Cpu size={18} className="text-indigo-400 animate-pulse" />
          </div>
          <span className="text-sm font-black tracking-[0.4em] uppercase text-white">Digital FTE Factory</span>
        </div>
        <Link href="/dashboard" className="text-[10px] font-bold tracking-[0.3em] uppercase py-2.5 px-6 border border-white/5 rounded-full hover:bg-white/5 transition-all flex items-center gap-3 text-white/60">
          CORE CONSOLE <ArrowRight size={14} />
        </Link>
      </nav>

      <main className="relative z-10 pt-32 pb-20 px-6 max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 items-start">
        
        {/* LEFT: Live Operational Terminal & 3D Neural Core */}
        <div className="lg:col-span-7 space-y-12">
          
          {/* Headline */}
          <div className="animate-reveal">
            <h1 className="text-6xl md:text-8xl font-black text-white leading-[0.9] mb-8 tracking-tighter">
              LIVING <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-purple-500 to-slate-500">INTELLIGENCE</span>
            </h1>
            <p className="text-lg font-medium text-white/30 max-w-xl leading-relaxed">
              Your autonomous workforce is active. Monitoring 24,000+ data points for real-time pipeline resolution and enterprise alignment.
            </p>
          </div>

          {/* 3D NEURAL ORB - The "AI Brain" */}
          <div className="relative h-[300px] flex items-center justify-center group">
             {/* The Orb */}
             <div className={`
               relative w-48 h-48 rounded-full transition-all duration-1000
               ${isNeuralActive ? 'scale-125 shadow-[0_0_100px_rgba(99,102,241,0.4)]' : 'scale-100 shadow-[0_0_60px_rgba(99,102,241,0.1)]'}
               bg-gradient-to-tr from-indigo-600/40 via-purple-600/40 to-slate-900/40 backdrop-blur-3xl border border-white/10 animate-float
             `}>
                <div className="absolute inset-2 rounded-full border border-white/5 animate-spin-slow opacity-30"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                   <Network size={32} className={`transition-all ${isNeuralActive ? 'text-white animate-spin' : 'text-indigo-400/50'}`} />
                </div>
             </div>
             {/* Labels revolving around */}
             <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-1/2 left-1/2 -translate-x-[150%] -translate-y-full text-[10px] font-mono tracking-widest text-indigo-400 opacity-40 uppercase">Memory: OK</div>
                <div className="absolute top-1/2 left-1/2 translate-x-[50%] translate-y-[100%] text-[10px] font-mono tracking-widest text-purple-400 opacity-40 uppercase">Logic: 98.9%</div>
             </div>
          </div>

          {/* LIVE TERMINAL FEED */}
          <div className="border border-white/5 bg-white/[0.02] rounded-2xl p-6 backdrop-blur-md animate-reveal" style={{ animationDelay: '0.2s' }}>
             <div className="flex justify-between items-center mb-6 pb-4 border-b border-white/5">
                <div className="flex items-center gap-3 text-white/80 font-bold text-xs tracking-widest uppercase">
                  <Terminal size={14} className="text-indigo-500" /> Operational Live-Feed
                </div>
                <div className="text-[10px] font-bold text-green-500 flex items-center gap-2">
                  <span className="w-1 h-1 bg-green-500 rounded-full animate-ping"></span> LOG_STREAM_OPEN
                </div>
             </div>
             <div className="space-y-4 font-mono text-[11px] h-[180px] overflow-hidden" ref={feedRef}>
                {liveFeed.length > 0 ? liveFeed.map((log, i) => (
                  <div key={log.id} className="flex gap-4 animate-reveal" style={{ animationDelay: `${i*100}ms` }}>
                    <span className="text-white/20 whitespace-nowrap">[{log.timestamp.split('T')[1].split('.')[0]}]</span>
                    <span className="text-indigo-400 uppercase tracking-tighter">{log.action}:</span>
                    <span className="text-white/50">{log.message}</span>
                  </div>
                )) : (
                  <div className="text-white/10 italic">Initializing cognitive telemetry...</div>
                )}
             </div>
          </div>
        </div>

        {/* RIGHT: Interaction Payload (The Form) */}
        <div className="lg:col-span-5 lg:sticky lg:top-32 animate-reveal" style={{ animationDelay: '0.3s' }}>
          <div className="bg-white/[0.03] border border-white/10 rounded-[2.5rem] p-1 shadow-2xl">
            <div className="bg-[#0A0A0B] rounded-[2.4rem] p-10 border border-white/5 relative overflow-hidden">
               
               {/* Success State */}
               {status.type === 'success' ? (
                 <div className="py-12 flex flex-col items-center text-center space-y-8 animate-reveal">
                    <div className="w-20 h-20 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 animate-float">
                       <Bot size={40} />
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-3xl font-black text-white italic tracking-tighter">AI AGENT: "CONFIRMED"</h3>
                      <p className="text-slate-400 text-sm italic leading-relaxed px-4">
                         "{status.response}"
                      </p>
                    </div>
                    <button 
                      onClick={() => setStatus({type:'idle'})}
                      className="mt-8 px-10 py-4 rounded-full bg-white text-black text-[11px] font-black uppercase tracking-[0.3em] hover:bg-slate-200 transition-all shadow-xl shadow-white/5"
                    >
                      Initiate New Command
                    </button>
                 </div>
               ) : (
                 <form onSubmit={handleSubmit} className="space-y-8">
                   <div className="space-y-6">
                      <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-white/20 border-b border-white/5 pb-4">Payload Manifest</h3>
                      
                      <div className="grid grid-cols-2 gap-8">
                        <div className="space-y-3">
                           <label className="text-[10px] uppercase font-black text-indigo-400 tracking-widest">ID</label>
                           <input 
                             type="text" required placeholder="Subject-Alpha"
                             className="w-full bg-transparent border-b border-white/10 py-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all placeholder:text-white/5"
                             value={formData.name} onChange={e=>setFormData(p=>({...p, name: e.target.value}))}
                           />
                        </div>
                        <div className="space-y-3">
                           <label className="text-[10px] uppercase font-black text-indigo-400 tracking-widest">Target</label>
                           <input 
                             type="email" required placeholder="target@node.com"
                             className="w-full bg-transparent border-b border-white/10 py-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all placeholder:text-white/5"
                             value={formData.email} onChange={e=>setFormData(p=>({...p, email: e.target.value}))}
                           />
                        </div>
                      </div>

                      <div className="space-y-3">
                        <label className="text-[10px] uppercase font-black text-indigo-400 tracking-widest">Objective</label>
                        <input 
                          type="text" placeholder="Strategic summary"
                          className="w-full bg-transparent border-b border-white/10 py-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all placeholder:text-white/5"
                          value={formData.subject} onChange={e=>setFormData(p=>({...p, subject: e.target.value}))}
                        />
                      </div>

                      <div className="space-y-3">
                        <label className="text-[10px] uppercase font-black text-indigo-400 tracking-widest">Instructions</label>
                        <textarea 
                          required placeholder="Input cognitive sequence requirements..."
                          className="w-full bg-transparent border-b border-white/10 py-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all min-h-[120px] resize-none placeholder:text-white/5"
                          value={formData.message} onChange={e=>setFormData(p=>({...p, message: e.target.value}))}
                        />
                      </div>
                   </div>

                   <button 
                     type="submit"
                     disabled={!isValid || status.type === 'loading'}
                     className={`
                       w-full py-5 rounded-2xl font-black text-[12px] uppercase tracking-[0.4em] transition-all relative overflow-hidden
                       ${status.type === 'loading' ? 'bg-indigo-900 text-white/40' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-2xl shadow-indigo-600/30'}
                       active:scale-[0.98] disabled:opacity-20
                     `}
                   >
                     {status.type === 'loading' ? (
                       <div className="flex items-center justify-center gap-4">
                         <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                         <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay:'0.2s'}}></div>
                         <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay:'0.4s'}}></div>
                         Processing Logic
                       </div>
                     ) : (
                       "EXECUTE SEQUENCE"
                     )}
                   </button>
                   
                   {status.type === 'error' && (
                     <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-500 text-[10px] font-black uppercase tracking-[0.2em] text-center rounded-lg">
                       ERROR: {status.message}
                     </div>
                   )}
                 </form>
               )}

               {/* Stats Overlay */}
               <div className="mt-10 pt-10 border-t border-white/5 grid grid-cols-2 gap-8 text-[10px] font-bold text-white/20 uppercase tracking-widest">
                  <div className="flex items-center gap-2"><Database size={14} /> Synchronized</div>
                  <div className="flex items-center gap-2"><Activity size={14} /> Neural-Active</div>
               </div>
            </div>
          </div>
        </div>
      </main>

      <style jsx global>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 12s linear infinite;
        }
      `}</style>
    </div>
  );
}
