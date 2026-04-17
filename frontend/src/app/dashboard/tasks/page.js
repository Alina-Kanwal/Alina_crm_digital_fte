"use client";

import { useState, useEffect } from "react";
import { Check, Clock, AlertCircle, Plus, X, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ title: "", description: "", priority: "medium" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${BACKEND}/api/v1/crm/tasks?skip=0&limit=50`);
      if (res.ok) {
        setTasks(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch tasks", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [BACKEND]);

  const toggleTask = async (taskId, currentStatus) => {
    const newStatus = currentStatus === 'completed' ? 'pending' : 'completed';
    
    // Optimistic UI update
    setTasks(prev => prev.map(t => 
      t.id === taskId ? { ...t, status: newStatus } : t
    ));
    
    try {
      const res = await fetch(`${BACKEND}/api/v1/crm/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (!res.ok) throw new Error("Sync failed");
    } catch (err) {
      console.error("Failed to toggle task", err);
      // Revert on failure
      fetchTasks();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await fetch(`${BACKEND}/api/v1/crm/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: formData.title,
          description: formData.description,
          priority: formData.priority,
          status: "pending"
        }),
      });

      if (res.ok) {
        setIsModalOpen(false);
        setFormData({ title: "", description: "", priority: "medium" });
        fetchTasks();
      } else {
        const errorData = await res.json();
        alert(errorData.detail || "Failed to create task");
      }
    } catch (err) {
      console.error("Error creating task", err);
      alert("Network error. Is the backend running?");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl relative text-text">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="font-serif text-3xl font-medium tracking-tight">Tasks</h1>
          <p className="text-muted text-sm mt-1">Checklist for your day and automated agent actions.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-text text-surface px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-text/90 transition-colors shadow-soft"
        >
          <Plus size={16} /> New Task
        </button>
      </div>

      <div className="bg-surface border border-border rounded-xl shadow-soft divide-y divide-border">
        <div className="px-6 py-4 bg-background/50 flex justify-between items-center rounded-t-xl">
          <h2 className="text-sm font-semibold">Today's Agenda</h2>
          <div className="text-xs font-medium text-muted bg-border px-2 py-0.5 rounded-full">
            {loading ? '-' : (tasks || []).filter(t => t.status !== 'completed').length} Pending
          </div>
        </div>

        {loading ? (
          <div className="p-6 space-y-4">
            {Array(4).fill(0).map((_, i) => (
              <div key={i} className="flex gap-4 animate-pulse">
                <div className="w-5 h-5 rounded border border-border/80 bg-background flex-shrink-0"></div>
                <div className="space-y-2 flex-1">
                  <div className="h-4 bg-border/60 rounded w-1/3"></div>
                  <div className="h-3 bg-border/60 rounded w-1/4"></div>
                </div>
              </div>
            ))}
          </div>
        ) : tasks?.length > 0 ? (
          <div className="divide-y divide-border/50">
            {tasks.map((task) => {
              const isCompleted = task.status === 'completed';
              return (
                <div key={task.id} className={`flex gap-4 p-6 hover:bg-background/40 transition-colors group ${isCompleted ? 'opacity-60' : ''}`}>
                  <button 
                    onClick={() => toggleTask(task.id, task.status)}
                    className={`w-5 h-5 mt-0.5 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${
                      isCompleted 
                      ? 'bg-text border-text text-surface' 
                      : 'border-border bg-surface hover:border-text/50'
                    }`}
                  >
                    {isCompleted && <Check size={14} strokeWidth={3} />}
                  </button>
                  
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium transition-colors ${isCompleted ? 'text-muted line-through' : 'text-text'}`}>
                      {task.title}
                    </p>
                    
                    {task.description && (
                      <p className="text-sm text-text/70 mt-1 line-clamp-2">
                        {task.description}
                      </p>
                    )}
                    
                    <div className="flex items-center gap-4 mt-3">
                      <div className={`flex items-center gap-1.5 text-xs font-medium ${
                        task.priority === 'high' && !isCompleted ? 'text-accent' : 'text-muted'
                      }`}>
                        {task.priority === 'high' ? <AlertCircle size={14} /> : <Clock size={14} />}
                        {task.due_date ? new Date(task.due_date).toLocaleDateString([], { month: 'short', day: 'numeric' }) : 'No Due Date'}
                      </div>
                      
                      {task.assigned_to && (
                        <div className="flex items-center gap-1.5 text-xs text-muted">
                          <span className="w-4 h-4 rounded-full bg-border flex items-center justify-center text-[0.6rem] text-text font-bold">
                            {task.assigned_to.substring(0, 1).toUpperCase()}
                          </span>
                          Assigned
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-12 text-center text-sm text-muted">
            <Check size={32} className="mx-auto mb-3 text-border opacity-50" />
            No tasks found. You're all caught up!
          </div>
        )}
      </div>

      {/* New Task Modal */}
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
                <h2 className="text-lg font-semibold text-text">New Task</h2>
                <button onClick={() => setIsModalOpen(false)} className="text-muted hover:text-text transition-colors">
                  <X size={20} />
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Task Title</label>
                  <input 
                    type="text" required placeholder="Follow up with client"
                    className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                    value={formData.title} onChange={e => setFormData(p => ({...p, title: e.target.value}))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Description</label>
                  <textarea 
                    placeholder="Provide some details..."
                    className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30 min-h-[80px]"
                    value={formData.description} onChange={e => setFormData(p => ({...p, description: e.target.value}))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">Priority</label>
                  <select 
                    className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-text/10 focus:border-text/30"
                    value={formData.priority} onChange={e => setFormData(p => ({...p, priority: e.target.value}))}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
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
                    {isSubmitting ? <Loader2 className="animate-spin" size={16} /> : "Create Task"}
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
