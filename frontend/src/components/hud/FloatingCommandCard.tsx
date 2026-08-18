import React from 'react';
import { ChevronRight } from 'lucide-react';

interface FloatingCommandCardProps {
  command?: string;
}

export const FloatingCommandCard: React.FC<FloatingCommandCardProps> = ({
  command = "check my cameras and tell what you can see"
}) => {
  return (
    <div className="relative w-56 md:w-64 p-3.5 bg-[#0D0B0E]/85 backdrop-blur-md rounded border border-[#FF1E42]/30 shadow-hud-red/10 text-left font-mono text-xs select-none">
      {/* HUD Corner Notches */}
      <span className="absolute -top-[1px] -left-[1px] w-2 h-2 border-t-2 border-l-2 border-[#FF1E42]" />
      <span className="absolute -bottom-[1px] -right-[1px] w-2 h-2 border-b-2 border-r-2 border-[#FF1E42]" />

      {/* Header */}
      <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-[#FF1E42] font-semibold mb-2">
        <span>COMMAND</span>
        <span className="text-[9px] text-[#8F8F98]">01</span>
      </div>

      {/* Command Text */}
      <p className="text-[#F5F5F5] font-sans text-sm leading-relaxed break-words font-medium min-h-[40px]">
        {command || "Awaiting voice or text input..."}
      </p>

      {/* Bottom prompt chevron */}
      <div className="mt-2 pt-1.5 border-t border-[#FF1E42]/15 flex items-center text-[#FF1E42] text-[10px]">
        <ChevronRight className="w-3.5 h-3.5 animate-pulse" />
        <span className="text-[9px] text-[#8F8F98] ml-1">PROMPT ACTIVE</span>
      </div>
    </div>
  );
};
