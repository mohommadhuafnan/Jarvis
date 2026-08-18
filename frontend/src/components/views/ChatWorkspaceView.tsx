import React, { useState } from 'react';
import { MessageSquareCode, Send, Bot, User, Sparkles, Terminal } from 'lucide-react';
import { ChatMessage } from '../../types';
import { soundFX } from '../../lib/sound/SoundFX';

interface ChatWorkspaceViewProps {
  messages: ChatMessage[];
  onSendMessage: (msg: string) => void;
  isProcessing: boolean;
}

export const ChatWorkspaceView: React.FC<ChatWorkspaceViewProps> = ({
  messages,
  onSendMessage,
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

  return (
    <div className="flex-1 p-6 space-y-4 overflow-hidden flex flex-col z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-3 shrink-0">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <MessageSquareCode className="w-6 h-6 text-[#FF1E42]" />
            <span>AI CHAT & NEURAL CONVERSATION</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Real-time multimodal dialog with Gemini 2.5 / 2.0 Flash engine
          </p>
        </div>

        <span className="px-3 py-1 rounded bg-[#1A050B] border border-[#FF1E42]/40 text-xs font-mono text-emerald-400">
          ● NEURAL CHAT ACTIVE
        </span>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 bg-[#050508]/80 border border-[#FF1E42]/25 rounded p-4 overflow-y-auto space-y-3 min-h-0">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';

          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 p-3.5 rounded max-w-2xl ${
                isUser
                  ? 'ml-auto bg-[#1A050B]/80 border border-[#FF1E42]/40 text-[#F5F5F5]'
                  : 'mr-auto bg-[#0D0B0E]/90 border border-[#FF1E42]/20 text-[#F5F5F5]'
              }`}
            >
              <div className="w-7 h-7 rounded bg-[#1A050B] border border-[#FF1E42]/40 flex items-center justify-center shrink-0 mt-0.5">
                {isUser ? (
                  <User className="w-4 h-4 text-[#FF1E42]" />
                ) : (
                  <Bot className="w-4 h-4 text-[#FF2B56]" />
                )}
              </div>

              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between font-mono text-[10px] text-[#8F8F98]">
                  <span className="font-bold text-[#FF1E42] uppercase">{isUser ? 'COMMANDER' : 'JARVIS AI'}</span>
                  <span>{msg.timestamp}</span>
                </div>
                <p className="text-sm font-sans leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                </p>

                {msg.tool_name && (
                  <div className="mt-2 p-2 rounded bg-[#050508] border border-emerald-500/30 text-[10px] font-mono text-emerald-400">
                    <div className="flex items-center space-x-1">
                      <Terminal className="w-3 h-3" />
                      <span>EXECUTED TOOL: {msg.tool_name}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Input Deck */}
      <form onSubmit={handleSubmit} className="flex items-center space-x-3 shrink-0">
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          placeholder="Transmit prompt to JARVIS..."
          disabled={isProcessing}
          className="flex-1 bg-[#0D0B0E] border border-[#FF1E42]/30 rounded px-4 py-2 text-sm font-sans text-[#F5F5F5] placeholder-[#8F8F98]/50 focus:outline-none"
        />

        <button
          type="submit"
          disabled={!inputVal.trim() || isProcessing}
          className="px-5 py-2 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold hover:bg-[#FF2B56] shadow-hud-red disabled:opacity-40 flex items-center space-x-1.5"
        >
          <Send className="w-3.5 h-3.5" />
          <span>TRANSMIT</span>
        </button>
      </form>
    </div>
  );
};
