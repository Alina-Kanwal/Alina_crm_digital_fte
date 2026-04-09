"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, MessageSquare, Check, Plus } from "lucide-react";

export default function Home() {
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' });
  const [status, setStatus] = useState({ type: 'idle', message: '' }); // idle | loading | success | error

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
      if (!res.ok) throw new Error(data?.detail || 'Failed to submit request');
      
      setStatus({ type: 'success', message: 'Message securely transmitted.', data });
    } catch (err) {
      setStatus({ type: 'error', message: err.message || 'Transmission failed.' });
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background relative selection:bg-accent/20">
      
      {/* Top Navigation */}
      <nav className="absolute top-0 w-full p-8 flex justify-between items-center z-10 max-w-6xl mx-auto left-0 right-0">
        <div className="font-serif text-xl font-semibold tracking-tight text-text flex items-center gap-2">
          <div className="w-6 h-6 bg-text rounded-sm flex items-center justify-center text-surface text-sm">D</div>
          Digital FTE
        </div>
        <Link href="/dashboard" className="text-sm font-medium text-text bg-border/50 hover:bg-border px-4 py-2 rounded-full transition-colors flex items-center gap-2">
          Console <ArrowRight size={14} />
        </Link>
      </nav>

      <main className="flex-1 flex flex-col items-center justify-center px-4 py-20 animate-fade-in text-center max-w-3xl mx-auto w-full z-10 mt-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-border/50 text-xs font-medium text-text/70 mb-8 tracking-wide">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span> 
          Autonomous Systems Active
        </div>

        <h1 className="font-serif text-5xl md:text-7xl font-bold text-text leading-[1.1] mb-6 tracking-tight">
          Enterprise intelligence, <br/>
          <span className="text-text/60">delivered.</span>
        </h1>
        
        <p className="text-lg text-text/70 mb-12 max-w-xl mx-auto leading-relaxed">
          Digital FTE is a robust, autonomous foundation for your customer success and pipeline operations. Always available. Always professional.
        </p>

        {/* Form Container */}
        <div className="w-full max-w-lg bg-surface border border-border rounded-2xl shadow-soft p-1 transition-all duration-300 relative text-left">
          
          {status.type === 'success' ? (
            <div className="p-8 flex flex-col items-center text-center animate-fade-in space-y-4">
              <div className="w-12 h-12 rounded-full bg-green-50 text-green-600 flex items-center justify-center mb-2">
                <Check size={24} />
              </div>
              <h3 className="font-serif text-2xl font-semibold text-text">Transmission Complete</h3>
              <p className="text-muted text-sm">
                Your message has been received by our autonomous systems. We will process it and reach out shortly.
              </p>
              <div className="pt-6 w-full">
                <button 
                  onClick={() => { setStatus({ type: 'idle' }); setFormData({name:'', email:'', subject:'', message: ''}); }}
                  className="w-full bg-background hover:bg-border border border-border text-text font-medium py-3 rounded-lg transition-colors flex justify-center items-center gap-2 text-sm"
                >
                  <Plus size={16} /> New Request
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="p-6 md:p-8 flex flex-col gap-5">
              <div className="flex gap-4">
                <div className="flex-1 space-y-1.5">
                  <label className="text-xs font-medium text-text/80 px-1">Name</label>
                  <input 
                    type="text" 
                    className="w-full bg-background border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30 transition-all placeholder:text-muted/50" 
                    placeholder="Jane Doe"
                    value={formData.name} onChange={e => setFormData(p => ({...p, name: e.target.value}))}
                  />
                </div>
                <div className="flex-1 space-y-1.5">
                  <label className="text-xs font-medium text-text/80 px-1">Email *</label>
                  <input 
                    type="email" 
                    required
                    className="w-full bg-background border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30 transition-all placeholder:text-muted/50" 
                    placeholder="jane@example.com"
                    value={formData.email} onChange={e => setFormData(p => ({...p, email: e.target.value}))}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text/80 px-1">Subject</label>
                <input 
                  type="text" 
                  className="w-full bg-background border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30 transition-all placeholder:text-muted/50" 
                  placeholder="How can we help?"
                  value={formData.subject} onChange={e => setFormData(p => ({...p, subject: e.target.value}))}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text/80 px-1">Message *</label>
                <textarea 
                  required
                  className="w-full bg-background border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30 transition-all min-h-[120px] resize-y placeholder:text-muted/50" 
                  placeholder="Enter your inquiry..."
                  value={formData.message} onChange={e => setFormData(p => ({...p, message: e.target.value}))}
                />
              </div>

              {status.type === 'error' && (
                <div className="text-xs text-accent text-center bg-accent/10 py-2 rounded">
                  {status.message}
                </div>
              )}

              <button 
                type="submit" 
                disabled={!isValid || status.type === 'loading'}
                className="mt-2 w-full bg-text hover:bg-black text-surface font-medium py-3 rounded-lg transition-all flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-soft hover:shadow-md h-[48px]"
              >
                {status.type === 'loading' ? <Loader2 size={18} className="animate-spin" /> : <>Transmit <MessageSquare size={16} /></>}
              </button>
            </form>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-8 text-center text-xs text-muted font-medium pb-12">
        <p>© {new Date().getFullYear()} Digital FTE. Designed for autonomous scale.</p>
      </footer>
    </div>
  );
}
