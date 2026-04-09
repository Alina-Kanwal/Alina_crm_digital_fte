"use client";

import { useState, useEffect } from "react";
import { Plus, GripVertical } from "lucide-react";

export default function DealsPage() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
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
    fetchDeals();
  }, [BACKEND]);

  const stages = [
    { id: "new", name: "New Opportunity" },
    { id: "qualified", name: "Qualified" },
    { id: "proposition", name: "Value Proposition" },
    { id: "negotiation", name: "Negotiation" },
    { id: "won", name: "Closed Won" }
  ];

  const dealsByStage = stages.reduce((acc, stage) => {
    acc[stage.id] = deals.filter(d => d.stage === stage.id);
    return acc;
  }, {});

  return (
    <div className="h-full flex flex-col space-y-6 animate-fade-in">
      <div className="flex justify-between items-end flex-shrink-0">
        <div>
          <h1 className="font-serif text-3xl font-medium tracking-tight text-text">Pipeline</h1>
          <p className="text-muted text-sm mt-1">Track and manage your ongoing deals.</p>
        </div>
        <button className="bg-text text-surface px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-text/90 transition-colors shadow-soft">
          <Plus size={16} /> New Deal
        </button>
      </div>

      <div className="flex-1 flex gap-6 overflow-x-auto pb-4 scrollbar-hide">
        {stages.map((stage) => (
          <div key={stage.id} className="w-80 flex-shrink-0 flex flex-col h-full bg-background rounded-xl">
            <div className="flex items-center justify-between mb-4 px-1">
              <h3 className="text-sm font-semibold text-text">{stage.name}</h3>
              <span className="bg-surface border border-border px-2 py-0.5 rounded-full text-xs font-medium text-muted">
                {loading ? '-' : dealsByStage[stage.id]?.length || 0}
              </span>
            </div>

            <div className="flex-1 space-y-3 overflow-y-auto">
              {loading ? (
                <div className="bg-surface border border-border rounded-lg p-4 animate-pulse h-28"></div>
              ) : dealsByStage[stage.id]?.length > 0 ? (
                dealsByStage[stage.id].map(deal => (
                  <div key={deal.id} className="bg-surface border border-border rounded-lg p-4 shadow-sm hover:shadow hover:border-border/80 transition-all cursor-grab active:cursor-grabbing group">
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-sm font-semibold text-text truncate pr-2">{deal.title}</div>
                      <GripVertical size={14} className="text-muted/0 group-hover:text-muted/50 transition-opacity" />
                    </div>
                    <div className="text-lg font-serif font-medium text-text mb-3">
                      ${deal.value?.toLocaleString() || '0'}
                    </div>
                    <div className="flex items-center justify-between text-xs mt-auto">
                      <span className="text-muted font-medium px-2 py-1 bg-background rounded">
                        {deal.expected_close_date ? new Date(deal.expected_close_date).toLocaleDateString([],{month:'short', day:'numeric'}) : 'No date'}
                      </span>
                      <span className={`w-2.5 h-2.5 rounded-full ${deal.probability > 70 ? 'bg-green-500' : deal.probability > 30 ? 'bg-yellow-500' : 'bg-red-500'}`} title={`${deal.probability}% probability`} />
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
    </div>
  );
}
