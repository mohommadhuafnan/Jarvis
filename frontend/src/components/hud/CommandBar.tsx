import React, { useState } from 'react';
import { Paperclip, Mic, Send, Lock, ShieldCheck } from 'lucide-react';
import { soundFX } from '../../lib/sound/SoundFX';

interface CommandBarProps {
  onSendMessage: (msg: string) => void;
  isListening: boolean;
  onToggleMic: () => void;
  isProcessing: boolean;
}

export const CommandBar: React.FC<CommandBarProps> = ({
  onSendMessage,
  isListening,
  onToggleMic,
  isProcessing
}) => {
  const [inputVal, setInputVal] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim() || isProcessing) return;
    soundFX.playProcessingBeep();
    onSendMessage(inputVal.trim());
    setInputVal('');
  };

  const handleMicClick = () => {
    soundFX.playWakeChime();
    onToggleMic();
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-3 select-none z-30">
      {/* Angular Beveled Command Input Deck */}
      <form 
        onSubmit={handleSubmit}
        className="hud-command-bar flex items-center px-4 py-2.5 space-x-3 transition-all"
      >
        {/* Attachment Button */}
        <button
          type="button"
          onClick={() => soundFX.playClick()}
          className="text-[#8F8F98] hover:text-[#FF1E42] transition-colors p-1.5 rounded hover:bg-[#1A050B]/50"
          title="Attach telemetry data / file"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        {/* Input Text Field */}
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          placeholder="Ask Jarvis anything..."
          disabled={isProcessing}
          className="flex-1 bg-transparent text-[#F5F5F5] placeholder-[#8F8F98]/50 font-sans text-sm focus:outline-none tracking-wide"
        />

        {/* Inline Mic Button */}
        <button
          type="button"
          onClick={handleMicClick}
          className={`p-1.5 rounded transition-colors ${
            isListening 
              ? 'text-[#FF2B56] bg-[#FF1E42]/20 animate-pulse' 
              : 'text-[#8F8F98] hover:text-[#FF1E42] hover:bg-[#1A050B]/50'
          }`}
          title={isListening ? "Stop listening" : "Voice input"}
        >
          <Mic className="w-4 h-4" />
        </button>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!inputVal.trim() || isProcessing}
          className={`p-1.5 rounded transition-all ${
            inputVal.trim() && !isProcessing
              ? 'text-[#FF1E42] hover:text-[#FF2B56] hover:bg-[#FF1E42]/20'
              : 'text-[#8F8F98]/40 cursor-not-allowed'
          }`}
          title="Send command"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

      {/* Futuristic Bottom Status Strip */}
      <div className="flex items-center justify-between px-3 pt-2 font-mono text-[9px] text-[#8F8F98]/60 uppercase tracking-wider">
        <div className="flex items-center space-x-1.5">
          <Lock className="w-2.5 h-2.5 text-[#FF1E42]" />
          <span>SECURE CONNECTION</span>
        </div>
        <div>
          <span>ENCRYPTED CHANNEL ACTIVE</span>
        </div>
        <div className="flex items-center space-x-1.5 text-emerald-400">
          <ShieldCheck className="w-2.5 h-2.5" />
          <span>ALL SYSTEMS OPERATIONAL</span>
        </div>
      </div>
    </div>
  );
};
