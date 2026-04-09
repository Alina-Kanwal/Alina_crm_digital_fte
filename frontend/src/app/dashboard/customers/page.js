"use client";

import { useState, useEffect } from "react";
import { Search, MoreHorizontal, UserPlus, Filter } from "lucide-react";

export default function CustomersPage() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const res = await fetch(`${BACKEND}/api/v1/crm/contacts?skip=0&limit=50`);
        if (res.ok) {
          setCustomers(await res.json());
        }
      } catch (err) {
        console.error("Failed to fetch customers", err);
      } finally {
        setLoading(false);
      }
    };
    fetchCustomers();
  }, [BACKEND]);

  const filteredCustomers = customers.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) || 
    c.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="font-serif text-3xl font-medium tracking-tight text-text">Contacts</h1>
          <p className="text-muted text-sm mt-1">Manage all your customer relationships.</p>
        </div>
        <button className="bg-text text-surface px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-text/90 transition-colors shadow-soft">
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
                    <td className="px-6 py-4 font-medium text-text">{contact.name}</td>
                    <td className="px-6 py-4 text-text/80">{contact.email}</td>
                    <td className="px-6 py-4 text-muted">{contact.company || '—'}</td>
                    <td className="px-6 py-4">
                      {contact.is_lead ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[0.65rem] font-medium uppercase tracking-wider bg-accent/10 text-accent border border-accent/20">Lead</span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[0.65rem] font-medium uppercase tracking-wider bg-green-50 text-green-700 border border-green-200">Customer</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right text-muted text-xs">
                      {new Date(contact.created_at).toLocaleDateString()}
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
    </div>
  );
}
