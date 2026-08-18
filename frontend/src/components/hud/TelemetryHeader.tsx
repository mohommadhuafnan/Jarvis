import React, { useState, useEffect } from 'react';
import { SystemTelemetry, AssistantState } from '../../types';

interface TelemetryHeaderProps {
  userName?: string;
  state?: AssistantState;
  telemetry?: SystemTelemetry;
}

export const TelemetryHeader: React.FC<TelemetryHeaderProps> = ({
  userName = "RAVIT",
  state = "IDLE",
  telemetry
}) => {
  const [currentTime, setCurrentTime] = useState<string>('');
  const [currentDate, setCurrentDate] = useState<string>('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toTimeString().split(' ')[0]);
      setCurrentDate(now.toLocaleDateString(undefined, {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      }));
    };
    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'GOOD MORNING';
    if (hour < 18) return 'GOOD AFTERNOON';
    return 'GOOD EVENING';
  };

  const getStatusBadge = () => {
    if (state === 'LISTENING') return { text: 'LISTENING', color: 'bg-[#FF1E42] text-[#F5F5F5] border-[#FF2B56]' };
    if (state === 'THINKING') return { text: 'THINKING', color: 'bg-[#FF1E42]/40 text-[#FF2B56] border-[#FF1E42]' };
    if (state === 'EXECUTING') return { text: 'WORKING', color: 'bg-[#1A050B] text-[#FF1E42] border-[#FF1E42]' };
    if (state === 'SPEAKING') return { text: 'SPEAKING', color: 'bg-[#FF1E42]/20 text-[#FF2B56] border-[#FF1E42]' };
    return { text: 'STANDBY', color: 'bg-[#0D0B0E] text-[#8F8F98] border-[#FF1E42]/30' };
  };

  const badge = getStatusBadge();
  const cpu = telemetry?.cpu_usage || 23;
  const ram = telemetry?.ram_usage || 45;
  const uptime = telemetry?.uptime || "04:23:11";

  return (
    <header className="w-full flex items-start justify-between px-6 pt-4 pb-2 select-none z-20">
      {/* Left Greeting & Telemetry */}
      <div className="space-y-1">
        <h1 className="text-2xl md:text-3xl font-bold tracking-wider text-[#F5F5F5] font-sans">
          {getGreeting()}, <span className="text-[#FF1E42] text-glow-red">{userName}</span>
        </h1>
        <p className="text-xs text-[#8F8F98] tracking-wide font-sans">
          How can I help you today?
        </p>

        {/* Telemetry Status Line */}
        <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-[10px] text-[#8F8F98]/80">
          <span>JARVIS AI Core v2.5.1</span>
          <span className="text-[#FF1E42]">|</span>
          <span className="text-emerald-400">Connected</span>
          <span className="text-[#FF1E42]">|</span>
          <span>Memory: 2.43 TB</span>
          <span className="text-[#FF1E42]">|</span>
          <span>Uptime: {uptime}</span>
        </div>

        {/* Active Status Pill */}
        <div className="pt-1.5">
          <span className={`inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full border text-[10px] font-mono tracking-widest font-semibold shadow-hud-red/20 ${badge.color}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-[#FF1E42] animate-pulse" />
            <span>● {badge.text}</span>
          </span>
        </div>
      </div>

      {/* Right Realtime Clock & Mini Metric HUD */}
      <div className="p-3 bg-[#0D0B0E]/80 rounded border border-[#FF1E42]/25 shadow-hud-red/10 text-right font-mono min-w-[150px]">
        {/* Large Digital Clock */}
        <div className="text-xl md:text-2xl font-bold tracking-widest text-[#FF1E42] text-glow-red">
          {currentTime || "20:53:47"}
        </div>
        <div className="text-[10px] text-[#8F8F98] tracking-wide">
          {currentDate || "Tuesday, May 14, 2024"}
        </div>

        {/* Mini Technical Metrics */}
        <div className="mt-2 pt-2 border-t border-[#FF1E42]/20 space-y-0.5 text-[9px] text-left">
          <div className="flex justify-between">
            <span className="text-[#8F8F98]">CPU</span>
            <span className="text-[#F5F5F5] font-semibold">{cpu}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#8F8F98]">RAM</span>
            <span className="text-[#F5F5F5] font-semibold">{ram}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#8F8F98]">AI CORE</span>
            <span className="text-[#FF1E42] font-semibold">100%</span>
          </div>
        </div>
      </div>
    </header>
  );
};
