import React from 'react';
import { Minus, Square, X, Cpu } from 'lucide-react';

interface WindowHeaderProps {
  status?: string;
}

export const WindowHeader: React.FC<WindowHeaderProps> = ({ status = "Command Center" }) => {
  return (
    <div className="h-7 w-full bg-[#050508] border-b border-[#FF1E42]/20 flex items-center justify-between px-3 text-xs select-none z-50">
      {/* Left title */}
      <div className="flex items-center space-x-2">
        <div className="w-3.5 h-3.5 rounded-sm bg-[#FF1E42]/20 border border-[#FF1E42] flex items-center justify-center">
          <Cpu className="w-2.5 h-2.5 text-[#FF1E42]" />
        </div>
        <span className="font-mono text-[11px] font-bold tracking-wider text-[#F5F5F5]">
          JARVIS AI
        </span>
        <span className="text-[#8F8F98] text-[10px]">—</span>
        <span className="text-[#8F8F98] font-mono text-[10px] uppercase tracking-wider">
          {status}
        </span>
      </div>

      {/* Center status badge */}
      <div className="hidden md:flex items-center space-x-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[#FF1E42] animate-ping" />
        <span className="font-mono text-[10px] text-[#8F8F98] tracking-widest uppercase">
          SECURE PROTOCOL v2.5 // ENCRYPTED NODE
        </span>
      </div>

      {/* Right window controls */}
      <div className="flex items-center space-x-3 text-[#8F8F98]">
        <button className="hover:text-[#F5F5F5] transition-colors p-1" title="Minimize">
          <Minus className="w-3 h-3" />
        </button>
        <button className="hover:text-[#F5F5F5] transition-colors p-1" title="Maximize">
          <Square className="w-2.5 h-2.5" />
        </button>
        <button className="hover:text-[#FF1E42] transition-colors p-1" title="Close">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
