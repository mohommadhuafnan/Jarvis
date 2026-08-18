import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { AssistantState } from '../../types';

interface ReactorOrbProps {
  state: AssistantState;
  audioLevel: number; // 0.0 to 1.0 from microphone or TTS
  currentTool?: string | null;
  onOrbClick?: () => void;
}

export const ReactorOrb: React.FC<ReactorOrbProps> = ({
  state,
  audioLevel,
  currentTool,
  onOrbClick
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Dynamic state colors and glow
  const isListening = state === 'LISTENING';
  const isThinking = state === 'THINKING';
  const isExecuting = state === 'EXECUTING';
  const isSpeaking = state === 'SPEAKING';
  const isError = state === 'ERROR';

  // Base scale calculation with audio reactivity
  const scaleBoost = isSpeaking || isListening ? 1 + audioLevel * 0.25 : 1;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let angle1 = 0;
    let angle2 = 0;
    let pulseAngle = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const baseRadius = 110 * scaleBoost;

      // Speed multipliers based on state
      const speed1 = isThinking ? 0.04 : isExecuting ? 0.03 : isListening ? 0.02 : 0.006;
      const speed2 = isThinking ? -0.05 : isExecuting ? -0.035 : isListening ? -0.025 : -0.008;

      angle1 += speed1;
      angle2 += speed2;
      pulseAngle += 0.03;

      const dynamicGlow = Math.sin(pulseAngle) * 0.3 + 0.7;

      // 1. Draw Outer Segmented HUD Ring with Ticks
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(angle1);
      ctx.strokeStyle = isError ? '#EF4444' : `rgba(255, 30, 66, ${0.4 * dynamicGlow})`;
      ctx.lineWidth = 1.5;

      const numTicks = 60;
      for (let i = 0; i < numTicks; i++) {
        const rad = (i * 2 * Math.PI) / numTicks;
        const tickLength = i % 5 === 0 ? 9 : 4;
        const r1 = baseRadius + 22;
        const r2 = r1 + tickLength;
        ctx.beginPath();
        ctx.moveTo(Math.cos(rad) * r1, Math.sin(rad) * r1);
        ctx.lineTo(Math.cos(rad) * r2, Math.sin(rad) * r2);
        ctx.stroke();
      }
      ctx.restore();

      // 2. Draw Segmented Primary Arcs
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(angle2);
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = isError ? '#DC2626' : `rgba(255, 30, 66, ${0.75 * dynamicGlow})`;
      ctx.shadowColor = '#FF1E42';
      ctx.shadowBlur = isListening || isSpeaking ? 16 : 8;

      // 4 quadrant segmented arcs
      for (let i = 0; i < 4; i++) {
        const start = (i * Math.PI) / 2 + 0.15;
        const end = start + (Math.PI / 2) - 0.3;
        ctx.beginPath();
        ctx.arc(0, 0, baseRadius + 12, start, end);
        ctx.stroke();
      }
      ctx.restore();

      // 3. Draw Inner Targeting Reticle & Crosshairs
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.strokeStyle = `rgba(255, 30, 66, ${0.35 * dynamicGlow})`;
      ctx.lineWidth = 1;

      // Crosshair lines
      ctx.beginPath();
      ctx.moveTo(-baseRadius - 30, 0);
      ctx.lineTo(-baseRadius + 5, 0);
      ctx.moveTo(baseRadius - 5, 0);
      ctx.lineTo(baseRadius + 30, 0);
      ctx.moveTo(0, -baseRadius - 30);
      ctx.lineTo(0, -baseRadius + 5);
      ctx.moveTo(0, baseRadius - 5);
      ctx.lineTo(0, baseRadius + 30);
      ctx.stroke();

      // Corner target brackets
      const bracketSize = 16;
      const bDist = baseRadius + 35;
      const corners = [
        [-bDist, -bDist, 1, 1],
        [bDist, -bDist, -1, 1],
        [-bDist, bDist, 1, -1],
        [bDist, bDist, -1, -1]
      ];
      ctx.strokeStyle = '#FF1E42';
      ctx.lineWidth = 1.5;
      corners.forEach(([x, y, dx, dy]) => {
        ctx.beginPath();
        ctx.moveTo(x, y + dy * bracketSize);
        ctx.lineTo(x, y);
        ctx.lineTo(x + dx * bracketSize, y);
        ctx.stroke();
      });

      ctx.restore();

      // 4. Center Glowing Reactor Core Ring
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.beginPath();
      ctx.arc(0, 0, baseRadius - 8, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(255, 30, 66, ${0.6 * dynamicGlow})`;
      ctx.lineWidth = 2;
      ctx.shadowColor = '#FF1E42';
      ctx.shadowBlur = 20;
      ctx.stroke();

      // Audio-reactive expanding wave ring if speaking or listening
      if ((isSpeaking || isListening) && audioLevel > 0.05) {
        ctx.beginPath();
        ctx.arc(0, 0, (baseRadius - 8) + (audioLevel * 30), 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 43, 86, ${0.4 * (1 - audioLevel)})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [state, audioLevel, isListening, isThinking, isExecuting, isSpeaking, isError, scaleBoost]);

  return (
    <div 
      className="relative flex items-center justify-center cursor-pointer group"
      onClick={onOrbClick}
      title="Click to toggle voice activation"
    >
      {/* Background ambient radial glow */}
      <motion.div 
        className="absolute w-72 h-72 rounded-full bg-[#FF1E42]/10 blur-2xl"
        animate={{
          scale: isListening ? [1, 1.25, 1] : isThinking ? [1, 1.15, 1] : [1, 1.05, 1],
          opacity: isListening || isSpeaking ? [0.6, 0.9, 0.6] : [0.3, 0.5, 0.3],
        }}
        transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* HTML Canvas with animated procedural HUD rings */}
      <canvas 
        ref={canvasRef} 
        width={380} 
        height={380} 
        className="relative z-10 select-none max-w-full max-h-full"
      />

      {/* Center Core Typography & Status Display */}
      <div className="absolute z-20 flex flex-col items-center justify-center text-center pointer-events-none">
        <motion.div
          animate={{ scale: isSpeaking ? [1, 1.06, 1] : 1 }}
          transition={{ duration: 0.3, repeat: isSpeaking ? Infinity : 0 }}
        >
          <span className="font-sans text-2xl md:text-3xl font-bold tracking-widest text-[#F5F5F5] text-glow-red block">
            JARVIS
          </span>
          <span className="font-mono text-[9px] md:text-[10px] tracking-[0.25em] text-[#FF1E42] uppercase font-semibold block mt-0.5">
            AI ASSISTANT
          </span>
        </motion.div>

        {/* Dynamic Reactor State Pill */}
        <div className="mt-2.5">
          {isListening && (
            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-[#FF1E42]/20 border border-[#FF1E42] text-[9px] font-mono text-[#FF2B56] animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FF1E42]" />
              <span>REC STATUS</span>
            </span>
          )}
          {isThinking && (
            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-[#FF1E42]/20 border border-[#FF1E42] text-[9px] font-mono text-[#FF2B56]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FF1E42] animate-ping" />
              <span>NEURAL SCAN</span>
            </span>
          )}
          {isExecuting && (
            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-[#FF1E42]/30 border border-[#FF2B56] text-[9px] font-mono text-[#F5F5F5]">
              <span>{currentTool ? currentTool.toUpperCase() : 'EXECUTING'}</span>
            </span>
          )}
          {isSpeaking && (
            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-[#FF1E42]/20 border border-[#FF1E42] text-[9px] font-mono text-[#FF2B56]">
              <span>TRANSMITTING</span>
            </span>
          )}
          {isIdle(state) && (
            <span className="font-mono text-[9px] tracking-widest text-[#8F8F98]/60 uppercase">
              STANDBY
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

function isIdle(state: AssistantState) {
  return state === 'IDLE';
}
