import React, { useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';
import { AssistantState } from '../../types';
import { soundFX } from '../../lib/sound/SoundFX';

interface VoiceWaveformProps {
  state: AssistantState;
  audioLevel: number;
  isListening: boolean;
  onToggleMic: () => void;
}

export const VoiceWaveform: React.FC<VoiceWaveformProps> = ({
  state,
  audioLevel,
  isListening,
  onToggleMic
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;
      const numBars = 48;
      const barWidth = 3;
      const spacing = width / numBars;

      phase += 0.05;

      const active = isListening || state === 'SPEAKING';
      const ampMultiplier = active ? Math.max(0.2, audioLevel * 1.5) : 0.05;

      for (let i = 0; i < numBars; i++) {
        const x = i * spacing + spacing / 2;
        // Symmetrical gaussian window for center-weighted waveform
        const distFromCenter = Math.abs(i - numBars / 2) / (numBars / 2);
        const windowWeight = Math.exp(-distFromCenter * distFromCenter * 2.5);

        // Sinusoidal wave oscillation
        const wave = Math.sin(phase + i * 0.25) * Math.cos(phase * 0.5 + i * 0.1);
        const barHeight = Math.max(2, (wave * 28 + 6) * windowWeight * ampMultiplier);

        const gradient = ctx.createLinearGradient(0, centerY - barHeight, 0, centerY + barHeight);
        gradient.addColorStop(0, '#FF2B56');
        gradient.addColorStop(0.5, '#FF1E42');
        gradient.addColorStop(1, '#8B0000');

        ctx.fillStyle = active ? gradient : 'rgba(255, 30, 66, 0.15)';
        ctx.fillRect(x - barWidth / 2, centerY - barHeight, barWidth, barHeight * 2);
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [state, audioLevel, isListening]);

  const handleMicClick = () => {
    soundFX.playWakeChime();
    onToggleMic();
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-2 select-none">
      {/* Symmetrical Waveform Canvas */}
      <canvas 
        ref={canvasRef} 
        width={340} 
        height={48} 
        className="w-72 md:w-80 h-10"
      />

      {/* Status text */}
      <span className="font-mono text-[10px] tracking-[0.25em] text-[#FF1E42] uppercase font-semibold">
        {state === 'LISTENING' ? 'LISTENING...' : state === 'SPEAKING' ? 'SPEAKING...' : state === 'THINKING' ? 'PROCESSING...' : 'STANDBY'}
      </span>

      {/* Glowing Microphone Button */}
      <button
        onClick={handleMicClick}
        className={`relative p-3 rounded-full transition-all duration-300 ${
          isListening
            ? 'bg-[#FF1E42] text-white shadow-hud-red-lg scale-110'
            : 'bg-[#0D0B0E] border border-[#FF1E42]/40 text-[#FF1E42] hover:bg-[#1A050B] hover:scale-105 shadow-hud-red/20'
        }`}
        title={isListening ? 'Stop Listening' : 'Start Voice Listening'}
      >
        {isListening && (
          <span className="absolute inset-0 rounded-full border-2 border-[#FF2B56] animate-ping pointer-events-none" />
        )}
        {isListening ? (
          <Mic className="w-5 h-5 animate-pulse" />
        ) : (
          <Mic className="w-5 h-5" />
        )}
      </button>
    </div>
  );
};
