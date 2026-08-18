import React, { useState, useEffect } from 'react';
import { CheckSquare, Plus, CheckCircle2, Circle, Clock, Tag } from 'lucide-react';
import { TaskItem } from '../../types';
import { fetchTasks, createTask, completeTask } from '../../lib/api';
import { soundFX } from '../../lib/sound/SoundFX';

export const TasksView: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all');

  const loadTasks = async () => {
    const data = await fetchTasks(filter);
    if (data.tasks) {
      setTasks(data.tasks);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [filter]);

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    soundFX.playSuccessTone();
    await createTask(newTitle.trim(), priority);
    setNewTitle('');
    loadTasks();
  };

  const handleComplete = async (taskId: string) => {
    soundFX.playClick();
    await completeTask(taskId);
    loadTasks();
  };

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <CheckSquare className="w-6 h-6 text-[#FF1E42]" />
            <span>TASK MATRIX & PROTOCOLS</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Active operational goals and tactical task queue
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex space-x-2">
          {(['all', 'pending', 'completed'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => { soundFX.playClick(); setFilter(tab); }}
              className={`px-3 py-1 rounded text-xs font-mono uppercase tracking-wider transition-all ${
                filter === tab
                  ? 'bg-[#FF1E42] text-white shadow-hud-red'
                  : 'bg-[#0D0B0E] border border-[#FF1E42]/20 text-[#8F8F98] hover:text-[#F5F5F5]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* New Task Creator Bar */}
      <form onSubmit={handleAddTask} className="p-3 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 flex items-center space-x-3">
        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="Add new task (e.g. 'Audit firewall logs')..."
          className="flex-1 bg-transparent text-sm text-[#F5F5F5] placeholder-[#8F8F98]/50 focus:outline-none font-sans"
        />

        <select
          value={priority}
          onChange={(e: any) => setPriority(e.target.value)}
          className="bg-[#1A050B] border border-[#FF1E42]/30 text-xs font-mono text-[#FF1E42] rounded px-2 py-1 focus:outline-none"
        >
          <option value="low">LOW</option>
          <option value="medium">MEDIUM</option>
          <option value="high">HIGH</option>
        </select>

        <button
          type="submit"
          disabled={!newTitle.trim()}
          className="px-4 py-1.5 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold hover:bg-[#FF2B56] shadow-hud-red disabled:opacity-40 flex items-center space-x-1"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>ADD</span>
        </button>
      </form>

      {/* Tasks List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {tasks.map((task) => {
          const isDone = task.status === 'completed';

          return (
            <div
              key={task.id}
              className={`p-4 rounded border transition-all relative ${
                isDone
                  ? 'bg-[#0A0608]/60 border-[#FF1E42]/10 opacity-70'
                  : 'bg-[#0D0B0E]/90 border-[#FF1E42]/30 hover:border-[#FF1E42]/60 shadow-hud-red/10'
              }`}
            >
              {/* Top Row: Priority Badge + Completion Trigger */}
              <div className="flex items-center justify-between mb-2">
                <span className={`px-2 py-0.5 rounded font-mono text-[9px] uppercase font-bold tracking-wider ${
                  task.priority === 'high' 
                    ? 'bg-[#FF1E42]/20 text-[#FF2B56] border border-[#FF1E42]/40' 
                    : task.priority === 'medium'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {task.priority} PRIORITY
                </span>

                <button
                  onClick={() => handleComplete(task.id)}
                  className="text-[#8F8F98] hover:text-[#FF1E42] transition-colors"
                  title={isDone ? "Completed" : "Mark completed"}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-[#FF1E42]" />
                  ) : (
                    <Circle className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Task Title */}
              <h3 className={`text-sm font-sans font-semibold mb-1 ${isDone ? 'line-through text-[#8F8F98]' : 'text-[#F5F5F5]'}`}>
                {task.title}
              </h3>

              {task.description && (
                <p className="text-xs text-[#8F8F98] font-sans mb-3 line-clamp-2">
                  {task.description}
                </p>
              )}

              {/* Footer: Date & Tags */}
              <div className="flex items-center justify-between text-[10px] font-mono text-[#8F8F98] pt-2 border-t border-[#FF1E42]/15">
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-[#FF1E42]" />
                  <span>{task.deadline || "No deadline"}</span>
                </div>
                {task.tags && (
                  <div className="flex items-center space-x-1">
                    <Tag className="w-3 h-3 text-[#8F8F98]" />
                    <span className="text-[#FF1E42]/80">{task.tags}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
