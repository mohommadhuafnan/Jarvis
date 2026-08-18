import React from 'react';
import { AssistantState } from '../../types';

interface ActionStatusCardProps {
  statusText?: string;
  state?: AssistantState;
}

export const ActionStatusCard: React.FC<ActionStatusCardProps> = ({
  statusText = "Action pending",
  state = "IDLE"
}) => {
  const isWorking = state === 'EXECUTING' || state === 'THINKING';

  return (
    <div className="relative w-56 md:w-64 p-3.5 bg-[#0D0B0E]/85 backdrop-blur-md rounded border border-[#FF1E42]/30 shadow-hud-red/10 text-left font-mono text-xs select-none">
      {/* HUD Corner Notches */}
      <span className="absolute -top-[1px] -left-[1px] w-2 h-2 border-t-2 border-l-2 border-[#FF1E42]" />
      <span className="absolute -bottom-[1px] -right-[1px] w-2 h-2 border-b-2 border-r-2 border-[#FF1E42]" />

      {/* Header */}
      <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-[#FF1E42] font-semibold mb-2">
        <span>ACTION STATUS</span>
        <span className={`w-1.5 h-1.5 rounded-full ${isWorking ? 'bg-[#FF1E42] animate-ping' : 'bg-[#8F8F98]'}`} />
      </div>

      {/* Status Body */}
      <p className="text-[#F5F5F5] font-sans text-sm leading-relaxed break-words font-medium min-h-[40px]">
        {statusText || "Action pending"}
      </p>

      {/* Bottom status dots */}
      <div className="mt-2 pt-1.5 border-t border-[#FF1E42]/15 flex items-center justify-between text-[10px] text-[#8F8F98]">
        <span>{state}</span>
        <div className="flex space-x-1">
          <span className={`w-1 h-1 rounded-full ${isWorking ? 'bg-[#FF1E42] animate-bounce' : 'bg-[#8F8F98]'}`} style={{ animationDelay: '0ms' }} />
          <span className={`w-1 h-1 rounded-full ${isWorking ? 'bg-[#FF1E42] animate-bounce' : 'bg-[#8F8F98]'}`} style={{ animationDelay: '150ms' }} />
          <span className={`w-1 h-1 rounded-full ${isWorking ? 'bg-[#FF1E42] animate-bounce' : 'bg-[#8F8F98]'}`} style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
};
