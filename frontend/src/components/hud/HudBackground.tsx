import React from 'react';

export const HudBackground: React.FC = () => {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
      {/* Deep dark gradient */}
      <div className="absolute inset-0 bg-radial-gradient from-[#1A050B]/30 via-[#050508]/90 to-[#050508]" />

      {/* Subtle World Map Silhouette */}
      <svg className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[85%] h-[75%] opacity-[0.04] text-[#FF1E42]" viewBox="0 0 1000 500" fill="currentColor">
        <path d="M150,120 Q180,100 220,130 T280,150 Q320,190 300,240 T240,280 Q190,260 160,200 Z" />
        <path d="M450,110 Q520,90 580,120 T620,170 Q600,220 540,240 T460,210 Q440,160 450,110 Z" />
        <path d="M680,140 Q750,110 820,150 T880,220 Q840,290 780,280 T690,200 Z" />
        <path d="M720,320 Q780,310 810,350 T760,420 Q710,410 700,360 Z" />
      </svg>

      {/* Diagonal glowing red accent lines matching screenshot */}
      <div className="absolute top-0 left-1/4 w-[1px] h-64 bg-gradient-to-b from-transparent via-[#FF1E42]/20 to-transparent -rotate-45" />
      <div className="absolute bottom-10 right-1/4 w-[1px] h-80 bg-gradient-to-b from-transparent via-[#FF1E42]/15 to-transparent rotate-45" />
      <div className="absolute top-20 right-10 w-96 h-96 bg-[#FF1E42]/5 rounded-full blur-3xl" />
      <div className="absolute bottom-10 left-10 w-80 h-80 bg-[#E11D48]/5 rounded-full blur-3xl" />

      {/* HUD Subtle Grid Overlay */}
      <div 
        className="absolute inset-0 opacity-[0.025]" 
        style={{
          backgroundImage: `linear-gradient(to right, #FF1E42 1px, transparent 1px), linear-gradient(to bottom, #FF1E42 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }} 
      />

      {/* Scanline CRT overlay */}
      <div className="absolute inset-0 scanline-overlay opacity-30" />
    </div>
  );
};
