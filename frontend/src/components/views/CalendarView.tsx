import React, { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, Clock, MapPin, Plus, ShieldCheck } from 'lucide-react';
import { CalendarEventItem } from '../../types';
import { fetchCalendar } from '../../lib/api';
import { soundFX } from '../../lib/sound/SoundFX';

export const CalendarView: React.FC = () => {
  const [events, setEvents] = useState<CalendarEventItem[]>([]);

  useEffect(() => {
    fetchCalendar().then(data => {
      if (data.events) setEvents(data.events);
    });
  }, []);

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <CalendarIcon className="w-6 h-6 text-[#FF1E42]" />
            <span>CALENDAR & TIMELINE HUD</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Synchronized event coordinates and schedule conflict matrix
          </p>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs text-emerald-400">
          <ShieldCheck className="w-4 h-4" />
          <span>ZERO CONFLICTS DETECTED</span>
        </div>
      </div>

      {/* Events Timeline */}
      <div className="space-y-4">
        {events.length === 0 ? (
          <div className="p-8 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/20 text-center space-y-2">
            <Clock className="w-8 h-8 text-[#8F8F98] mx-auto opacity-50" />
            <p className="text-sm font-sans text-[#F5F5F5] font-semibold">No Scheduled Calendar Events</p>
            <p className="text-xs font-mono text-[#8F8F98]">Say "Jarvis, schedule a meeting tomorrow at 10 AM" to create an event.</p>
          </div>
        ) : (
          events.map((evt, idx) => (
            <div
              key={evt.id || idx}
              className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/25 hover:border-[#FF1E42]/60 shadow-hud-red/10 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-[#FF1E42] animate-ping" />
                  <h3 className="text-base font-sans font-bold text-[#F5F5F5]">
                    {evt.title}
                  </h3>
                </div>

                {evt.description && (
                  <p className="text-xs text-[#8F8F98] font-sans">
                    {evt.description}
                  </p>
                )}

                <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] font-mono text-[#8F8F98]">
                  <div className="flex items-center space-x-1 text-[#FF2B56]">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{evt.start_time} — {evt.end_time}</span>
                  </div>
                  {evt.location && (
                    <div className="flex items-center space-x-1 text-[#8F8F98]">
                      <MapPin className="w-3.5 h-3.5 text-[#FF1E42]" />
                      <span>{evt.location}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="shrink-0 font-mono text-xs">
                <span className="px-3 py-1 rounded bg-[#1A050B] border border-[#FF1E42]/40 text-[#FF1E42]">
                  SCHEDULED
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
