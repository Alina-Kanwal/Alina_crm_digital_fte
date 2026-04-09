"use client";

import { useState, useEffect } from "react";
import { Check, Clock, AlertCircle, Plus } from "lucide-react";

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
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
    fetchTasks();
  }, [BACKEND]);

  const toggleTask = (taskId) => {
    // Optimistic UI update
    setTasks(prev => prev.map(t => 
      t.id === taskId ? { ...t, status: t.status === 'completed' ? 'pending' : 'completed' } : t
    ));
    
    // In a real app, we would make a PUT/PATCH request here to sync with the backend
    // fetch(`${BACKEND}/api/v1/crm/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify({ status: 'completed' }) })
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="font-serif text-3xl font-medium tracking-tight text-text">Tasks</h1>
          <p className="text-muted text-sm mt-1">Checklist for your day and automated agent actions.</p>
        </div>
        <button className="bg-text text-surface px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-text/90 transition-colors shadow-soft">
          <Plus size={16} /> New Task
        </button>
      </div>

      <div className="bg-surface border border-border rounded-xl shadow-soft divide-y divide-border">
        <div className="px-6 py-4 bg-background/50 flex justify-between items-center rounded-t-xl">
          <h2 className="text-sm font-semibold text-text">Today's Agenda</h2>
          <div className="text-xs font-medium text-muted bg-border px-2 py-0.5 rounded-full">
            {loading ? '-' : tasks.filter(t => t.status !== 'completed').length} Pending
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
        ) : tasks.length > 0 ? (
          <div className="divide-y divide-border/50">
            {tasks.map((task) => {
              const isCompleted = task.status === 'completed';
              return (
                <div key={task.id} className={`flex gap-4 p-6 hover:bg-background/40 transition-colors group ${isCompleted ? 'opacity-60' : ''}`}>
                  <button 
                    onClick={() => toggleTask(task.id)}
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
    </div>
  );
}
