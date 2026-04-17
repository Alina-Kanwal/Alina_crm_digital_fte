"use client";

import { useState, useEffect } from "react";
import { Search, MoreHorizontal, UserPlus, Filter, X, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function CustomersPage() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", company: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const fetchCustomers = async () => {
    try {
      const res = await fetch(`${BACKEND}/api/v1/crm/customers?skip=0&limit=100`);
      if (res.ok) {
        setCustomers(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch customers", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [BACKEND]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const names = formData.name.split(" ");
      const firstName = names[0];
      const lastName = names.slice(1).join(" ");

      const res = await fetch(`${BACKEND}/api/v1/crm/customers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.email,
          first_name: firstName,
          last_name: lastName || "",
          customer_metadata: { company: formData.company }
        }),
      });

      if (res.ok) {
        setIsModalOpen(false);
        setFormData({ name: "", email: "", company: "" });
        fetchCustomers();
      } else {
        const errorData = await res.json();
        alert(errorData.detail || "Failed to create contact");
      }
    } catch (err) {
      console.error("Error creating contact", err);
      alert("Network error. Is the backend running?");
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredCustomers = (customers || []).filter(c => 
    (c.first_name || "").toLowerCase().includes(search.toLowerCase()) || 
    (c.last_name || "").toLowerCase().includes(search.toLowerCase()) || 
    (c.email || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in relative">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="font-serif text-3xl font-medium tracking-tight text-text">Contacts</h1>
          <p className="text-muted text-sm mt-1">Manage all your customer relationships.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-text text-surface px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-text/90 transition-colors shadow-soft"
        >
          <UserPlus size={16} /> Add Contact
        </button>
      </div>

      <div className="bg-surface border border-border rounded-xl shadow-soft overflow-hidden flex flex-col">
        {/* Table Toolbar */}
        <div className="p-4 border-b border-border flex items-center justify-between gap-4 bg-background/50">
          <div className="relative w-full max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input 
              type="text" 
              placeholder="Search by name or email..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-surface border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30 transition-shadow"
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-2 border border-border bg-surface rounded-md text-sm font-medium text-text hover:bg-border/50 transition-colors">
            <Filter size={16} /> Filter
          </button>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-background/80 text-muted uppercase tracking-wider text-[0.65rem] font-semibold border-b border-border">
              <tr>
                <th className="px-6 py-3">Name</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Company</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3 text-right">Added</th>
                <th className="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                // Skeletons
                Array(5).fill(0).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-6 py-4"><div className="h-4 bg-border/60 rounded w-32"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-border/60 rounded w-48"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-border/60 rounded w-24"></div></td>
                    <td className="px-6 py-4"><div className="h-5 bg-border/60 rounded-full w-16"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-border/60 rounded w-20 ml-auto"></div></td>
                    <td className="px-6 py-4"></td>
                  </tr>
                ))
              ) : filteredCustomers.length > 0 ? (
                filteredCustomers.map((contact) => (
                  <tr key={contact.id} className="hover:bg-background/40 transition-colors">
                    <td className="px-6 py-4 font-medium text-text">{contact.first_name} {contact.last_name}</td>
                    <td className="px-6 py-4 text-text/80">{contact.email}</td>
                    <td className="px-6 py-4 text-muted">{contact.customer_metadata?.company || '—'}</td>
                    <td className="px-6 py-4">
                      {contact.lead_score > 50 ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[0.65rem] font-medium uppercase tracking-wider bg-accent/10 text-accent border border-accent/20">High Lead</span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[0.65rem] font-medium uppercase tracking-wider bg-green-50 text-green-700 border border-green-200">Customer</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right text-muted text-xs">
                      {contact.created_at ? new Date(contact.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="text-muted hover:text-text transition-colors p-1.5 rounded hover:bg-border/80">
                        <MoreHorizontal size={16} />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted">
                    No contacts found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Contact Modal */}
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
                <h2 className="text-lg font-semibold text-text">New Contact</h2>
                <button onClick={() => setIsModalOpen(false)} className="text-muted hover:text-text transition-colors">
                  <X size={20} />
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Full Name</label>
                  <input 
                    type="text" required placeholder="Jane Doe"
                    className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                    value={formData.name} onChange={e => setFormData(p => ({...p, name: e.target.value}))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Email Address</label>
                  <input 
                    type="email" required placeholder="jane@example.com"
                    className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                    value={formData.email} onChange={e => setFormData(p => ({...p, email: e.target.value}))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Company</label>
                  <input 
                    type="text" placeholder="Acme Inc."
                    className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                    value={formData.company} onChange={e => setFormData(p => ({...p, company: e.target.value}))}
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
                    {isSubmitting ? <Loader2 className="animate-spin" size={16} /> : "Create Contact"}
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
