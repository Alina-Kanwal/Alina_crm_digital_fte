"use client";

import { useState, useEffect } from "react";
import { Plus, GripVertical, X, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function DealsPage() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ title: "", value: "", customer_id: "", stage: "new" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'https://alina-crm-digital-fte.onrender.com';

  const fetchDeals = async () => {
    try {
      const res = await fetch(`${BACKEND}/api/v1/crm/deals?skip=0&limit=50`);
      if (res.ok) {
        setDeals(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch deals", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeals();
  }, [BACKEND]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await fetch(`${BACKEND}/api/v1/crm/deals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: formData.title,
          amount: parseFloat(formData.value) || 0,
          customer_id: formData.customer_id,
          stage: formData.stage
        }),
      });

      if (res.ok) {
        setIsModalOpen(false);
        setFormData({ title: "", value: "", customer_id: "", stage: "new" });
        fetchDeals();
      } else {
        const errorData = await res.json();
        alert(errorData.detail || "Failed to create deal. Ensure Customer ID is valid.");
      }
    } catch (err) {
      console.error("Error creating deal", err);
      alert("Network error. Is the backend running?");
    } finally {
      setIsSubmitting(false);
    }
  };

  const stages = [
    { id: "new", name: "New Opportunity" },
    { id: "qualified", name: "Qualified" },
    { id: "proposition", name: "Value Proposition" },
    { id: "negotiation", name: "Negotiation" },
    { id: "won", name: "Closed Won" }
  ];

  const dealsByStage = stages.reduce((acc, stage) => {
    acc[stage.id] = (deals || []).filter(d => d.stage === stage.id);
    return acc;
  }, {});

  return (
    <div className="h-full flex flex-col space-y-6 animate-fade-in relative text-text">
      <div className="flex justify-between items-end flex-shrink-0">
        <div>
          <h1 className="font-serif text-3xl font-medium tracking-tight">Pipeline</h1>
          <p className="text-muted text-sm mt-1">Track and manage your ongoing deals.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-text text-surface px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-text/90 transition-colors shadow-soft"
        >
          <Plus size={16} /> New Deal
        </button>
      </div>

      <div className="flex-1 flex gap-6 overflow-x-auto pb-4 scrollbar-hide">
        {stages.map((stage) => (
          <div key={stage.id} className="w-80 flex-shrink-0 flex flex-col h-full bg-background rounded-xl">
            <div className="flex items-center justify-between mb-4 px-1">
              <h3 className="text-sm font-semibold">{stage.name}</h3>
              <span className="bg-surface border border-border px-2 py-0.5 rounded-full text-xs font-medium text-muted">
                {loading ? '-' : (dealsByStage[stage.id]?.length || 0)}
              </span>
            </div>

            <div className="flex-1 space-y-3 overflow-y-auto min-h-[400px]">
              {loading ? (
                <div className="bg-surface border border-border rounded-lg p-4 animate-pulse h-28"></div>
              ) : dealsByStage[stage.id]?.length > 0 ? (
                dealsByStage[stage.id].map(deal => (
                  <div key={deal.id} className="bg-surface border border-border rounded-lg p-4 shadow-sm hover:shadow hover:border-border/80 transition-all cursor-grab active:cursor-grabbing group">
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-sm font-semibold truncate pr-2">{deal.title}</div>
                      <GripVertical size={14} className="text-muted/0 group-hover:text-muted/50 transition-opacity" />
                    </div>
                    <div className="text-lg font-serif font-medium mb-3">
                      ${(deal.amount || deal.value)?.toLocaleString() || '0'}
                    </div>
                    <div className="flex items-center justify-between text-xs mt-auto">
                      <span className="text-muted font-medium px-2 py-1 bg-background rounded">
                        {deal.expected_close_date ? new Date(deal.expected_close_date).toLocaleDateString([],{month:'short', day:'numeric'}) : 'No date'}
                      </span>
                      <span className={`w-2.5 h-2.5 rounded-full ${deal.probability > 70 ? 'bg-green-500' : deal.probability > 30 ? 'bg-yellow-500' : 'bg-red-500'}`} title={`${deal.probability || 0}% probability`} />
                    </div>
                  </div>
                ))
              ) : (
                <div className="h-full min-h-[100px] border-2 border-dashed border-border/80 rounded-lg flex items-center justify-center text-xs text-muted font-medium bg-background/50">
                  Drop to move
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* New Deal Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-surface border border-border rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
            >
              <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-background/50">
                <h2 className="text-lg font-semibold text-text">New Deal</h2>
                <button onClick={() => setIsModalOpen(false)} className="text-muted hover:text-text transition-colors">
                  <X size={20} />
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Deal Title</label>
                  <input 
                    type="text" required placeholder="Cloud Migration Project"
                    className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                    value={formData.title} onChange={e => setFormData(p => ({...p, title: e.target.value}))}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Value ($)</label>
                    <input 
                      type="number" required placeholder="5000"
                      className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                      value={formData.value} onChange={e => setFormData(p => ({...p, value: e.target.value}))}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Stage</label>
                    <select 
                      className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                      value={formData.stage} onChange={e => setFormData(p => ({...p, stage: e.target.value}))}
                    >
                      {stages.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Customer ID</label>
                  <input 
                    type="text" required placeholder="Enter customer UUID"
                    className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                    value={formData.customer_id} onChange={e => setFormData(p => ({...p, customer_id: e.target.value}))}
                  />
                </div>
                
                <div className="pt-4 flex gap-3">
                  <button 
                    type="button" 
                    onClick={() => setIsModalOpen(false)}
                    className="flex-1 py-2 text-sm font-medium text-text border border-border rounded-lg hover:bg-border/50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    disabled={isSubmitting}
                    className="flex-1 py-2 text-sm font-medium bg-text text-surface rounded-lg hover:bg-text/90 transition-colors flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? <Loader2 className="animate-spin" size={16} /> : "Create Deal"}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
