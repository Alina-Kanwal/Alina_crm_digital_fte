"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, PlayCircle, Send, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import Image from "next/image";

const fadeUpVariant = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

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
    <div className="min-h-screen bg-background text-text-primary font-sans selection:bg-accent/20 transition-colors duration-300">
      
      {/* Refined Navigation */}
      <motion.nav 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full px-6 py-4 md:px-12 flex justify-between items-center glass-panel sticky top-0 z-40 border-b-0 shadow-sm"
      >
        <div className="flex items-center gap-3">
          <div className="relative w-9 h-9 flex items-center justify-center p-0.5">
            <Image 
              src="/brand/logo.png" 
              alt="Digital FTE Logo" 
              width={36} 
              height={36} 
              className="object-contain"
            />
          </div>
          <span className="font-serif text-xl font-semibold tracking-tight text-text-primary">Digital FTE</span>
        </div>
        <Link href="/dashboard" className="text-sm font-medium text-text-muted hover:text-text-primary transition-colors flex items-center gap-2 group">
          Go to Console <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
        </Link>
      </motion.nav>

      <main className="max-w-[1200px] mx-auto px-6 py-16 md:py-24 grid lg:grid-cols-12 gap-16 lg:gap-24 relative">
        
        {/* LEFT COLUMN: Narrative & Live System Feel */}
        <motion.div 
          className="lg:col-span-7 flex flex-col justify-center"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          
          <motion.div variants={fadeUpVariant} className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border bg-text-primary/5 text-xs font-semibold text-text-muted mb-8 w-max backdrop-blur-md">
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse"></div>
            Autonomous Workflow Active
          </motion.div>

          <motion.h1 variants={fadeUpVariant} className="font-serif text-5xl md:text-7xl lg:text-[5.5rem] leading-[1.05] tracking-tight text-text-primary mb-8 font-medium">
            Intelligence <br/>
            <span className="text-text-muted italic opacity-80">that operates.</span>
          </motion.h1>
          
          <motion.p variants={fadeUpVariant} className="text-text-muted text-lg md:text-xl leading-relaxed max-w-lg mb-14 font-light">
            An elegant, autonomous customer success foundation. It reasons through inquiries, assigns ownership, and logs every action—so your team can focus on the relationships that matter.
          </motion.p>

          {/* Clean Enterprise Log (Replaces Hacker Terminal) */}
          <motion.div variants={fadeUpVariant} className="w-full max-w-lg border border-border glass-panel rounded-2xl shadow-lg overflow-hidden flex flex-col h-[260px]">
            <div className="bg-text-primary/5 px-5 py-3 border-b border-border flex items-center justify-between backdrop-blur-md">
               <span className="text-xs font-semibold text-text-muted tracking-wide uppercase">System Activity Log</span>
               <div className="flex items-center gap-1.5 text-[11px] font-medium text-accent">
                 <PlayCircle size={12} /> Syncing
               </div>
            </div>
            
            <div className="p-5 flex-1 overflow-y-auto flex flex-col gap-4 text-sm font-sans bg-surface/50">
                <AnimatePresence>
                  {liveFeed.length > 0 ? liveFeed.map((log, i) => (
                    <motion.div 
                      key={log.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="flex gap-4 items-start pb-4 border-b border-border/50 last:border-0 last:pb-0"
                    >
                      <div className="text-text-muted text-xs font-mono pt-0.5 whitespace-nowrap opacity-60">
                        {log.timestamp.split('T')[1].split('.')[0]}
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="font-semibold text-text-primary text-xs uppercase tracking-wide">
                          {log.action.replace(/_/g, ' ')}
                        </span>
                        <span className="text-text-muted font-light leading-relaxed">
                          {log.message}
                        </span>
                      </div>
                    </motion.div>
                  )) : (
                    <motion.div 
                      initial={{ opacity: 0 }} 
                      animate={{ opacity: 1 }} 
                      className="h-full flex items-center justify-center text-text-muted italic font-light text-sm"
                    >
                       Waiting for system events...
                    </motion.div>
                  )}
                </AnimatePresence>
            </div>
          </motion.div>

        </motion.div>

        {/* RIGHT COLUMN: Action Form */}
        <motion.div 
          className="lg:col-span-5 flex flex-col justify-center"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
        >
          <div className="glass-panel bg-surface/80 rounded-3xl p-8 shadow-2xl relative overflow-hidden transition-all duration-500 border border-glass-border">
             
             {/* Progress indicator bar at top */}
             <AnimatePresence>
               {isProcessing && (
                 <motion.div 
                   initial={{ opacity: 0 }} 
                   animate={{ opacity: 1 }} 
                   exit={{ opacity: 0 }} 
                   className="absolute top-0 left-0 w-full h-1 bg-border"
                 >
                   <div className="h-full bg-text-primary animate-pulse"></div>
                 </motion.div>
               )}
             </AnimatePresence>

             {status.type === 'success' ? (
               <motion.div 
                 initial={{ opacity: 0, scale: 0.95 }}
                 animate={{ opacity: 1, scale: 1 }}
                 className="py-12 flex flex-col items-center text-center space-y-6"
               >
                  <div className="w-16 h-16 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center text-green-500 mb-2">
                     <Check size={32} />
                  </div>
                  <h3 className="font-serif text-3xl font-medium text-text-primary">Received</h3>
                  <div className="p-5 bg-text-primary/5 rounded-xl border border-border text-text-secondary text-sm leading-relaxed font-light mb-4">
                     "{status.response}"
                  </div>
                  <button 
                    onClick={() => setStatus({type:'idle'})}
                    className="text-sm font-semibold text-text-primary hover:text-accent transition-colors uppercase tracking-widest pt-4"
                  >
                    Submit Another Request
                  </button>
               </motion.div>
             ) : (
               <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                 <div className="mb-2">
                   <h2 className="text-xl font-semibold text-text-primary mb-1 font-serif">Interact with Digital FTE</h2>
                   <p className="text-sm text-text-muted font-light">Submit an inquiry and watch the system process it in real-time.</p>
                 </div>

                 <div className="space-y-4">
                   <div>
                     <label className="block text-xs font-semibold text-text-muted uppercase tracking-wide mb-1.5 ml-1">Name</label>
                     <input 
                       type="text" required placeholder="Jane Doe"
                       className="input-anthropic w-full bg-surface text-text-primary placeholder:text-text-muted/50"
                       value={formData.name} onChange={e=>setFormData(p=>({...p, name: e.target.value}))}
                     />
                   </div>

                   <div>
                     <label className="block text-xs font-semibold text-text-muted uppercase tracking-wide mb-1.5 ml-1">Email <span className="text-accent font-normal">*</span></label>
                     <input 
                       type="email" required placeholder="jane@example.com"
                       className="input-anthropic w-full bg-surface text-text-primary placeholder:text-text-muted/50"
                       value={formData.email} onChange={e=>setFormData(p=>({...p, email: e.target.value}))}
                     />
                   </div>

                   <div>
                     <label className="block text-xs font-semibold text-text-muted uppercase tracking-wide mb-1.5 ml-1">Topic</label>
                     <input 
                       type="text" placeholder="Partnership inquiry..."
                       className="input-anthropic w-full bg-surface text-text-primary placeholder:text-text-muted/50"
                       value={formData.subject} onChange={e=>setFormData(p=>({...p, subject: e.target.value}))}
                     />
                   </div>

                   <div>
                     <label className="block text-xs font-semibold text-text-muted uppercase tracking-wide mb-1.5 ml-1">Request Details <span className="text-accent font-normal">*</span></label>
                     <textarea 
                       required placeholder="How can the autonomous workforce assist you today?"
                       className="input-anthropic w-full min-h-[130px] resize-y bg-surface text-text-primary placeholder:text-text-muted/50"
                       value={formData.message} onChange={e=>setFormData(p=>({...p, message: e.target.value}))}
                     />
                   </div>
                 </div>

                 <motion.button 
                   whileHover={{ scale: 1.01 }}
                   whileTap={{ scale: 0.98 }}
                   type="submit"
                   disabled={!isValid || status.type === 'loading'}
                   className="mt-4 w-full py-4 rounded-xl bg-text-primary hover:bg-text-secondary text-background font-medium text-sm transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-text-primary disabled:opacity-40 flex items-center justify-center gap-2 shadow-lg h-[56px]"
                 >
                   {status.type === 'loading' ? (
                     <Loader2 className="animate-spin text-background/80" size={18} />
                   ) : (
                     <span className="flex items-center gap-2 text-background">Submit Request <Send size={16} className="text-background/80" /></span>
                   )}
                 </motion.button>
                 
                 <AnimatePresence>
                   {status.type === 'error' && (
                     <motion.p 
                       initial={{ opacity: 0, y: -10 }}
                       animate={{ opacity: 1, y: 0 }}
                       exit={{ opacity: 0 }}
                       className="text-center text-xs text-red-500 font-medium mt-2 bg-red-500/10 p-3 rounded-lg border border-red-500/20"
                     >
                       {status.message}
                     </motion.p>
                   )}
                 </AnimatePresence>
               </form>
             )}
          </div>
        </motion.div>
      </main>

      {/* Elegant Footer */}
      <footer className="w-full py-10 border-t border-border mt-10">
        <div className="max-w-[1200px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-medium text-text-muted uppercase tracking-widest">
          <span>Digital FTE © {new Date().getFullYear()}</span>
          <span>Designed for Elegance & Autonomy</span>
        </div>
      </footer>
    </div>
  );
}
