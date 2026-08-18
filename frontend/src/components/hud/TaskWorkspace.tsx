import React, { useState } from 'react';
import { 
  SlidersHorizontal, 
  Settings as SettingsIcon, 
  CheckCircle2, 
  Circle, 
  Terminal, 
  Camera, 
  FileText, 
  Mail, 
  CheckSquare, 
  Sparkles,
  ChevronRight
} from 'lucide-react';
import { ActivityLogItem, CurrentTaskState, ChatMessage } from '../../types';
import { soundFX } from '../../lib/sound/SoundFX';

interface TaskWorkspaceProps {
  currentTask: CurrentTaskState;
  activityLogs: ActivityLogItem[];
  chatMessages: ChatMessage[];
  onClearLogs?: () => void;
}

export const TaskWorkspace: React.FC<TaskWorkspaceProps> = ({
  currentTask,
  activityLogs,
  chatMessages,
  onClearLogs
}) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'history'>('chat');

  const getModuleIcon = (module?: string) => {
    const m = (module || '').toLowerCase();
    if (m.includes('camera')) return Camera;
    if (m.includes('email') || m.includes('mail')) return Mail;
    if (m.includes('presentation') || m.includes('file') || m.includes('doc')) return FileText;
    if (m.includes('task')) return CheckSquare;
    if (m.includes('ai') || m.includes('gemini')) return Sparkles;
    return Terminal;
  };

  return (
    <aside className="w-80 md:w-96 h-full bg-[#070508]/90 border-l border-[#FF1E42]/20 flex flex-col p-3.5 select-none z-30 overflow-y-auto space-y-3.5">
      {/* Workspace Top Header */}
      <div className="flex items-center justify-between pb-1 border-b border-[#FF1E42]/15">
        <span className="font-mono text-[11px] font-bold tracking-wider text-[#F5F5F5] uppercase">
          CHAT • TASK WORKSPACE
        </span>

        {/* Action icons */}
        <div className="flex items-center space-x-2 text-[#8F8F98]">
          <button 
            onClick={() => soundFX.playClick()}
            className="hover:text-[#FF1E42] transition-colors p-1 rounded hover:bg-[#1A050B]/50" 
            title="Filter activities"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
          </button>
          <button 
            onClick={() => soundFX.playClick()}
            className="hover:text-[#FF1E42] transition-colors p-1 rounded hover:bg-[#1A050B]/50" 
            title="Workspace settings"
          >
            <SettingsIcon className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Tabs: CHAT / HISTORY */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => { soundFX.playClick(); setActiveTab('chat'); }}
          className={`px-4 py-1 rounded text-xs font-mono font-semibold tracking-wider transition-all ${
            activeTab === 'chat'
              ? 'bg-[#FF1E42] text-white shadow-hud-red/40'
              : 'bg-[#0D0B0E] border border-[#FF1E42]/20 text-[#8F8F98] hover:text-[#F5F5F5]'
          }`}
        >
          CHAT
        </button>
        <button
          onClick={() => { soundFX.playClick(); setActiveTab('history'); }}
          className={`px-4 py-1 rounded text-xs font-mono font-semibold tracking-wider transition-all ${
            activeTab === 'history'
              ? 'bg-[#FF1E42] text-white shadow-hud-red/40'
              : 'bg-[#0D0B0E] border border-[#FF1E42]/20 text-[#8F8F98] hover:text-[#F5F5F5]'
          }`}
        >
          HISTORY
        </button>
      </div>

      {/* --- Tab 1: Live Chat & Current Task Flow --- */}
      {activeTab === 'chat' ? (
        <div className="space-y-3.5">
          {/* CURRENT TASK CARD */}
          <div className="p-3 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 shadow-hud-red/10 space-y-2.5">
            {/* Task Card Header with Progress */}
            <div className="flex items-center justify-between font-mono text-[10px]">
              <span className="text-[#FF1E42] font-bold tracking-widest uppercase">CURRENT TASK</span>
              <span className="text-[#FF2B56] font-semibold">{currentTask?.progressPercent ?? 0}%</span>
            </div>

            {/* Command string */}
            <div className="text-xs text-[#F5F5F5] font-sans font-medium">
              <span className="text-[#8F8F98] text-[10px] font-mono block">Command:</span>
              <span className="text-[#F5F5F5]">{currentTask?.title || 'System Standby'}</span>
            </div>

            {/* Step Checkboxes */}
            <div className="space-y-1.5 pt-1">
              {(currentTask?.steps || []).map((step, idx) => (
                <div key={idx} className="flex items-start space-x-2 text-[11px] font-sans">
                  {step.completed ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#FF1E42] shrink-0 mt-0.5" />
                  ) : step.current ? (
                    <Circle className="w-3.5 h-3.5 text-[#FF2B56] animate-ping shrink-0 mt-0.5" />
                  ) : (
                    <Circle className="w-3.5 h-3.5 text-[#8F8F98]/40 shrink-0 mt-0.5" />
                  )}
                  <span className={step.completed ? 'text-[#8F8F98] line-through' : step.current ? 'text-[#F5F5F5] font-semibold text-glow-red' : 'text-[#8F8F98]'}>
                    {step.text}
                  </span>
                </div>
              ))}
            </div>

            {/* Status text & Progress Bar */}
            <div className="pt-2 border-t border-[#FF1E42]/15 space-y-1.5 font-mono text-[9px]">
              <div className="flex justify-between text-[#8F8F98]">
                <span>Status:</span>
                <span className="text-[#FF1E42]">{currentTask?.statusText || 'Ready'}</span>
              </div>
              <div className="w-full bg-[#1A050B] h-1.5 rounded-full overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-[#FF1E42] to-[#FF2B56] h-full shadow-[0_0_8px_#FF1E42] transition-all duration-500"
                  style={{ width: `${currentTask?.progressPercent ?? 0}%` }}
                />
              </div>
            </div>
          </div>

          {/* ACTIVITY FEED CARD */}
          <div className="p-3 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/20 space-y-2">
            <div className="flex items-center justify-between font-mono text-[10px]">
              <span className="text-[#8F8F98] uppercase tracking-wider font-semibold">ACTIVITY FEED</span>
              {onClearLogs && (
                <button 
                  onClick={onClearLogs}
                  className="text-[9px] text-[#8F8F98] hover:text-[#FF1E42] transition-colors uppercase tracking-wider"
                >
                  CLEAR
                </button>
              )}
            </div>

            {/* Activity Items List */}
            <div className="space-y-2 pt-1 max-h-72 overflow-y-auto pr-1">
              {(activityLogs || []).map((item, idx) => {
                const raw = item as any;
                const moduleName = item.module || raw.agent || raw.tool || 'SYSTEM';
                const actionText = item.action || raw.tool || raw.permissionDecision || 'System action logged';
                const timeText = item.created_at || raw.timestamp || 'Ready';
                const detailsText = item.details;
                const Icon = getModuleIcon(moduleName);

                return (
                  <div 
                    key={item.id || raw._id || idx}
                    className="flex items-start space-x-2.5 p-2 rounded bg-[#050508]/60 border border-[#FF1E42]/15 hover:border-[#FF1E42]/40 transition-colors"
                  >
                    {/* Glowing module icon */}
                    <div className="w-6 h-6 rounded bg-[#1A050B] border border-[#FF1E42]/30 flex items-center justify-center shrink-0 mt-0.5">
                      <Icon className="w-3 h-3 text-[#FF1E42]" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="font-semibold text-[#F5F5F5] truncate">{moduleName}</span>
                        <span className="text-[#8F8F98] text-[9px]">{timeText}</span>
                      </div>
                      <p className="text-[11px] font-sans text-[#8F8F98] line-clamp-2 mt-0.5">
                        {actionText}
                      </p>
                      {detailsText && (
                        <p className="text-[10px] font-mono text-[#FF1E42]/80 truncate mt-0.5">
                          {typeof detailsText === 'object' ? JSON.stringify(detailsText) : detailsText}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* --- Tab 2: Full Conversation Log --- */
        <div className="p-3 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/20 space-y-2 max-h-[500px] overflow-y-auto">
          <span className="font-mono text-[10px] text-[#8F8F98] uppercase tracking-wider block">
            CONVERSATION HISTORY
          </span>

          {chatMessages.length === 0 ? (
            <p className="text-xs text-[#8F8F98] italic">No active dialog recorded.</p>
          ) : (
            chatMessages.map((msg) => (
              <div 
                key={msg.id}
                className={`p-2.5 rounded text-xs font-sans space-y-1 ${
                  msg.role === 'user' 
                    ? 'bg-[#1A050B]/60 border border-[#FF1E42]/30 text-[#F5F5F5]' 
                    : 'bg-[#050508]/80 border border-[#FF1E42]/15 text-[#F5F5F5]'
                }`}
              >
                <div className="flex justify-between font-mono text-[9px] text-[#8F8F98]">
                  <span className="text-[#FF1E42] font-semibold uppercase">{msg.role === 'user' ? 'COMMANDER' : 'JARVIS AI'}</span>
                  <span>{msg.timestamp}</span>
                </div>
                <p className="leading-relaxed">{msg.content}</p>
                {msg.tool_name && (
                  <div className="text-[9px] font-mono text-emerald-400">
                    TOOL: {msg.tool_name}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </aside>
  );
};
