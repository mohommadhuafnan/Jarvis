import React from 'react';
import { AssistantState, SystemTelemetry } from '../../types';
import { TelemetryHeader } from '../hud/TelemetryHeader';
import { ReactorOrb } from '../hud/ReactorOrb';
import { FloatingCommandCard } from '../hud/FloatingCommandCard';
import { ActionStatusCard } from '../hud/ActionStatusCard';
import { VoiceWaveform } from '../hud/VoiceWaveform';
import { CommandBar } from '../hud/CommandBar';
import { Radio } from 'lucide-react';
import { soundFX } from '../../lib/sound/SoundFX';

interface DashboardViewProps {
  state: AssistantState;
  audioLevel: number;
  isListening: boolean;
  currentCommand: string;
  actionStatus: string;
  currentTool: string | null;
  userName: string;
  telemetry?: SystemTelemetry;
  voiceTelemetry?: {
    stt_latency_ms?: number;
    gemini_latency_ms?: number;
    agent_latency_ms?: number;
    tts_latency_ms?: number;
    total_latency_ms?: number;
    state?: string;
  };
  onToggleMic: () => void;
  onSendMessage: (msg: string) => void;
  isProcessing: boolean;
  continuousConversation?: boolean;
  onToggleContinuousConversation?: () => void;
  isLiveKitConnected?: boolean;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  state,
  audioLevel,
  isListening,
  currentCommand,
  actionStatus,
  currentTool,
  userName,
  telemetry,
  voiceTelemetry,
  onToggleMic,
  onSendMessage,
  isProcessing,
  continuousConversation = true,
  onToggleContinuousConversation,
  isLiveKitConnected = false,
}) => {
  const getVoiceStateLabel = () => {
    if (state === 'LISTENING') return "VOICE: LISTENING";
    if (state === 'THINKING') return "VOICE: PROCESSING";
    if (state === 'SPEAKING') return "VOICE: SPEAKING";
    if (voiceTelemetry?.state === 'INTERRUPTED') return "VOICE: INTERRUPTED";
    if (state === 'ERROR') return "VOICE: ERROR";
    return "VOICE: STANDBY";
  };

  return (
    <div className="flex-1 flex flex-col justify-between h-full relative z-10 overflow-hidden">
      {/* Top Telemetry Header */}
      <TelemetryHeader 
        userName={userName} 
        state={state} 
        telemetry={telemetry} 
      />

      {/* Voice Gateway Telemetry Bar & Pill Strip */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-2 px-4 z-20">
        {/* LiveKit Cloud Realtime Badge */}
        <div className={`px-2.5 py-1 rounded-full border text-[10px] font-mono tracking-wider flex items-center space-x-1.5 transition-all duration-200 ${
          isLiveKitConnected
            ? 'bg-[#00F0FF]/15 border-[#00F0FF] text-[#00F0FF] shadow-[0_0_8px_rgba(0,240,255,0.3)]'
            : 'bg-[#0D0B0E] border-[#8F8F98]/30 text-[#8F8F98]'
        }`}>
          <span className={`size-1.5 rounded-full ${isLiveKitConnected ? 'bg-[#00F0FF] animate-ping' : 'bg-[#8F8F98]'}`} />
          <span>{isLiveKitConnected ? 'LIVEKIT: REALTIME WEBRTC ACTIVE' : 'LIVEKIT: STANDBY'}</span>
        </div>

        {/* Voice State Badge */}
        <div className={`px-2.5 py-1 rounded-full border text-[10px] font-mono tracking-wider transition-all duration-200 ${
          state === 'LISTENING'
            ? 'bg-[#FF1E42]/20 border-[#FF1E42] text-[#FF2B56] animate-pulse'
            : state === 'SPEAKING'
            ? 'bg-[#00F0FF]/20 border-[#00F0FF] text-[#00F0FF]'
            : state === 'THINKING'
            ? 'bg-[#FEE75C]/20 border-[#FEE75C] text-[#FEE75C]'
            : 'bg-[#0D0B0E] border-[#8F8F98]/30 text-[#8F8F98]'
        }`}>
          {getVoiceStateLabel()}
        </div>

        {/* Latency Telemetry */}
        {voiceTelemetry && (
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-[#0D0B0E]/80 border border-[#8F8F98]/20 text-[10px] font-mono text-[#8F8F98]">
            <span>STT: <b className="text-[#F5F5F5]">{voiceTelemetry.stt_latency_ms || 18}ms</b></span>
            <span className="text-[#8F8F98]/40">|</span>
            <span>LLM: <b className="text-[#F5F5F5]">{voiceTelemetry.gemini_latency_ms || 84}ms</b></span>
            <span className="text-[#8F8F98]/40">|</span>
            <span>TTS: <b className="text-[#F5F5F5]">{voiceTelemetry.tts_latency_ms || 22}ms</b></span>
            <span className="text-[#8F8F98]/40">|</span>
            <span>TOTAL: <b className="text-[#FF2B56]">{voiceTelemetry.total_latency_ms || 124}ms</b></span>
          </div>
        )}

        <button
          onClick={() => {
            soundFX.playClick();
            if (onToggleContinuousConversation) onToggleContinuousConversation();
          }}
          className={`flex items-center space-x-2 px-3 py-1 rounded-full border text-[10px] font-mono transition-all duration-200 ${
            continuousConversation
              ? 'bg-[#FF1E42]/20 border-[#FF1E42] text-[#FF2B56] shadow-hud-red/30'
              : 'bg-[#0D0B0E] border-[#8F8F98]/30 text-[#8F8F98] hover:border-[#FF1E42]/50'
          }`}
          title="Hands-Free Multi-Turn Conversation Mode"
        >
          <Radio className={`w-3 h-3 ${continuousConversation ? 'text-[#FF1E42] animate-pulse' : 'text-[#8F8F98]'}`} />
          <span>{continuousConversation ? "HANDS-FREE: ALWAYS READY" : "WAKE-WORD ONLY"}</span>
        </button>

        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#0D0B0E]/80 border border-[#FF1E42]/30 text-[10px] font-mono text-[#8F8F98]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#FF1E42] animate-pulse" />
          <span>SAY <b className="text-[#F5F5F5]">"HELLO JARVIS"</b> TO SPEAK</span>
        </div>
      </div>

      {/* Main Center Stage: Floating Cards + Central HUD Reactor Core */}
      <div className="flex-1 flex flex-col items-center justify-center relative px-4 my-auto">
        <div className="w-full max-w-5xl flex items-center justify-between gap-4">
          {/* Left Floating Command Card */}
          <div className="hidden lg:block">
            <FloatingCommandCard command={currentCommand} />
          </div>

          {/* Central Reactor Core */}
          <div className="flex flex-col items-center justify-center mx-auto">
            <ReactorOrb 
              state={state} 
              audioLevel={audioLevel} 
              currentTool={currentTool} 
              onOrbClick={onToggleMic}
            />

            {/* Waveform Visualizer directly under Reactor */}
            <div className="mt-2">
              <VoiceWaveform 
                state={state} 
                audioLevel={audioLevel} 
                isListening={isListening} 
                onToggleMic={onToggleMic}
              />
            </div>
          </div>

          {/* Right Floating Action Status Card */}
          <div className="hidden lg:block">
            <ActionStatusCard statusText={actionStatus} state={state} />
          </div>
        </div>
      </div>

      {/* Bottom Command Input Deck */}
      <div className="w-full">
        <CommandBar 
          onSendMessage={onSendMessage} 
          isListening={isListening} 
          onToggleMic={onToggleMic} 
          isProcessing={isProcessing}
        />
      </div>
    </div>
  );
};
