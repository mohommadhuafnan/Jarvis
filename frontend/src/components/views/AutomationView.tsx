import React from 'react';
import { Workflow, Play, Clock, Zap, CheckCircle2 } from 'lucide-react';
import { soundFX } from '../../lib/sound/SoundFX';

export const AutomationView: React.FC = () => {
  const routines = [
    {
      id: "auto_1",
      title: "Morning Tactical Briefing",
      trigger: "Daily at 08:00 AM",
      actions: ["Fetch calendar events", "Summarize unread emails", "Read top 3 high priority tasks", "Voice speech synthesis"],
      active: true
    },
    {
      id: "auto_2",
      title: "Perimeter Camera & Security Scan",
      trigger: "Every 2 hours",
      actions: ["Capture screenshot / camera telemetry", "Analyze anomalies with Gemini Vision", "Log to Activity Feed"],
      active: true
    },
    {
      id: "auto_3",
      title: "Workspace Memory Optimization",
      trigger: "Daily at Midnight",
      actions: ["Index long-term memory graph", "Clean temporary execution sandbox", "Generate diagnostics snapshot"],
      active: false
    }
  ];

  const handleTriggerRoutine = (title: string) => {
    soundFX.playSuccessTone();
    alert(`Triggered automation routine: "${title}". AI pipeline dispatched.`);
  };

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <Workflow className="w-6 h-6 text-[#FF1E42]" />
            <span>AUTOMATION & AGENT ROUTINES</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Proactive background agent workflows and automated tactical routines
          </p>
        </div>

        <span className="px-3 py-1 rounded bg-[#1A050B] border border-[#FF1E42]/40 text-xs font-mono text-[#FF2B56]">
          2 ACTIVE WORKFLOWS
        </span>
      </div>

      {/* Routine Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {routines.map((rt) => (
          <div
            key={rt.id}
            className="p-5 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 shadow-hud-red/10 space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-[#FF1E42]" />
                <h3 className="font-sans font-bold text-sm text-[#F5F5F5]">{rt.title}</h3>
              </div>
              <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold ${
                rt.active ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-zinc-800 text-zinc-400'
              }`}>
                {rt.active ? 'ENABLED' : 'PAUSED'}
              </span>
            </div>

            <div className="flex items-center space-x-1.5 text-xs font-mono text-[#8F8F98]">
              <Clock className="w-3.5 h-3.5 text-[#FF1E42]" />
              <span>{rt.trigger}</span>
            </div>

            <div className="space-y-1.5 pt-2 border-t border-[#FF1E42]/15">
              <span className="text-[10px] font-mono text-[#8F8F98] uppercase">PIPELINE ACTIONS:</span>
              {rt.actions.map((act, i) => (
                <div key={i} className="flex items-center space-x-2 text-xs font-sans text-[#8F8F98]">
                  <CheckCircle2 className="w-3 h-3 text-[#FF1E42]" />
                  <span>{act}</span>
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => handleTriggerRoutine(rt.title)}
                className="px-3 py-1 rounded bg-[#1A050B] border border-[#FF1E42]/40 text-xs font-mono text-[#FF2B56] hover:bg-[#FF1E42]/20 transition-all flex items-center space-x-1.5"
              >
                <Play className="w-3 h-3 fill-current" />
                <span>TRIGGER NOW</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
