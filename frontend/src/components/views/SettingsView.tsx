import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Key, User, Volume2, Globe, Shield, CheckCircle, Save, Play } from 'lucide-react';
import { fetchSettings, saveSettings } from '../../lib/api';
import { soundFX } from '../../lib/sound/SoundFX';
import { ttsService } from '../../lib/voice/TextToSpeech';

interface SettingsViewProps {
  onTestVoice?: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onTestVoice }) => {
  const [userName, setUserName] = useState('RAVIT');
  const [wakeWord, setWakeWord] = useState('Jarvis');
  const [language, setLanguage] = useState('en');
  const [geminiKey, setGeminiKey] = useState('');
  const [speechRate, setSpeechRate] = useState(1.02);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoiceName, setSelectedVoiceName] = useState<string>('');
  const [savedStatus, setSavedStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings().then(data => {
      if (data.user_name) setUserName(data.user_name);
      if (data.wake_word) setWakeWord(data.wake_word);
      if (data.language) setLanguage(data.language);
    });

    const voices = ttsService.getAvailableVoices();
    setAvailableVoices(voices);
    const curr = ttsService.getSelectedVoice();
    if (curr) setSelectedVoiceName(curr.name);
  }, []);

  const handleVoiceChange = (voiceName: string) => {
    setSelectedVoiceName(voiceName);
    ttsService.setVoiceByName(voiceName);
  };

  const handleSpeechRateChange = (rate: number) => {
    setSpeechRate(rate);
    ttsService.setRate(rate);
  };

  const handleTestSpeech = () => {
    soundFX.playProcessingBeep();
    ttsService.speak(
      `Greetings, Commander ${userName}. JARVIS voice synthesis online and calibrated.`,
      undefined,
      undefined
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    soundFX.playSuccessTone();
    await saveSettings({
      user_name: userName,
      wake_word: wakeWord,
      language: language,
      gemini_api_key: geminiKey || undefined,
    });
    setSavedStatus("All parameters saved and synchronized with AI Core.");
    setTimeout(() => setSavedStatus(null), 3000);
  };

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <SettingsIcon className="w-6 h-6 text-[#FF1E42]" />
            <span>COMMAND CENTER CONFIGURATION</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Voice, neural API keys, multilingual settings, and voice personality
          </p>
        </div>

        {savedStatus && (
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded bg-[#1A050B] border border-[#FF1E42]/40 text-xs font-mono text-[#FF2B56]">
            <CheckCircle className="w-4 h-4 text-[#FF1E42]" />
            <span>{savedStatus}</span>
          </div>
        )}
      </div>

      {/* Settings Form */}
      <form onSubmit={handleSave} className="space-y-5 max-w-3xl">
        {/* Section 1: Voice Engine & Audio Output */}
        <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-3">
          <div className="flex items-center justify-between border-b border-[#FF1E42]/15 pb-2">
            <div className="flex items-center space-x-2 text-xs font-mono text-[#FF1E42] font-semibold">
              <Volume2 className="w-4 h-4" />
              <span>JARVIS VOICE SYNTHESIS ENGINE</span>
            </div>
            <button
              type="button"
              onClick={handleTestSpeech}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#FF1E42]/20 border border-[#FF1E42] text-[11px] font-mono text-[#FF2B56] hover:bg-[#FF1E42] hover:text-white transition-all"
            >
              <Play className="w-3 h-3" />
              <span>TEST VOICE OUTPUT</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] font-mono text-[#8F8F98] uppercase block mb-1">Synthesizer Voice</label>
              <select
                value={selectedVoiceName}
                onChange={(e) => handleVoiceChange(e.target.value)}
                className="w-full bg-[#050508] border border-[#FF1E42]/30 rounded px-3 py-1.5 text-xs text-[#FF1E42] font-mono focus:outline-none"
              >
                {availableVoices.map((v) => (
                  <option key={v.name} value={v.name}>
                    {v.name} ({v.lang})
                  </option>
                ))}
                {availableVoices.length === 0 && (
                  <option value="">Default System Voice</option>
                )}
              </select>
            </div>

            <div>
              <label className="text-[10px] font-mono text-[#8F8F98] uppercase block mb-1">Speech Speed Rate ({speechRate}x)</label>
              <input
                type="range"
                min="0.8"
                max="1.3"
                step="0.02"
                value={speechRate}
                onChange={(e) => handleSpeechRateChange(parseFloat(e.target.value))}
                className="w-full accent-[#FF1E42] mt-2 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Section 2: AI Brain & Gemini Key */}
        <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#FF1E42] font-semibold border-b border-[#FF1E42]/15 pb-2">
            <Key className="w-4 h-4" />
            <span>GOOGLE GEMINI AI BRAIN</span>
          </div>
          <p className="text-xs text-[#8F8F98]">
            Connected with Google Gemini AI Core for multi-modal reasoning and dynamic tool execution.
          </p>
          <input
            type="password"
            value={geminiKey}
            onChange={(e) => setGeminiKey(e.target.value)}
            placeholder="Gemini API Key configured"
            className="w-full bg-[#050508] border border-[#FF1E42]/30 rounded px-3 py-2 text-xs text-[#F5F5F5] font-mono focus:outline-none"
          />
        </div>

        {/* Section 3: Identity & Wake Word */}
        <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#FF1E42] font-semibold border-b border-[#FF1E42]/15 pb-2">
            <User className="w-4 h-4" />
            <span>USER IDENTITY & WAKE WORD</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] font-mono text-[#8F8F98] uppercase block mb-1">Commander / User Name</label>
              <input
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                className="w-full bg-[#050508] border border-[#FF1E42]/30 rounded px-3 py-1.5 text-xs text-[#F5F5F5] font-sans focus:outline-none"
              />
            </div>

            <div>
              <label className="text-[10px] font-mono text-[#8F8F98] uppercase block mb-1">Wake Word Trigger</label>
              <select
                value={wakeWord}
                onChange={(e) => setWakeWord(e.target.value)}
                className="w-full bg-[#050508] border border-[#FF1E42]/30 rounded px-3 py-1.5 text-xs text-[#FF1E42] font-mono focus:outline-none"
              >
                <option value="Jarvis">Jarvis</option>
                <option value="Nova">Nova</option>
                <option value="Friday">Friday</option>
                <option value="Athena">Athena</option>
                <option value="Computer">Computer</option>
                <option value="Brahma">Brahma</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 4: Multilingual */}
        <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#FF1E42] font-semibold border-b border-[#FF1E42]/15 pb-2">
            <Globe className="w-4 h-4" />
            <span>MULTILINGUAL CONFIG</span>
          </div>

          <div>
            <label className="text-[10px] font-mono text-[#8F8F98] uppercase block mb-1">Primary Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full bg-[#050508] border border-[#FF1E42]/30 rounded px-3 py-1.5 text-xs text-[#FF1E42] font-mono focus:outline-none"
            >
              <option value="en">English (US / UK)</option>
              <option value="ta">Tamil (தமிழ்)</option>
              <option value="si">Sinhala (සිංහල)</option>
            </select>
          </div>
        </div>

        {/* Section 5: Google OAuth & Gmail Integration */}
        <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#FF1E42] font-semibold border-b border-[#FF1E42]/15 pb-2">
            <Shield className="w-4 h-4" />
            <span>GOOGLE GMAIL & CALENDAR OAUTH 2.0</span>
          </div>
          <p className="text-xs text-[#8F8F98]">
            Authorizes JARVIS to securely interact with your personal Gmail mailbox and Google Calendar via OAuth tokens.
          </p>
          <div className="flex items-center justify-between pt-1">
            <span className="text-xs font-mono text-[#8F8F98]">
              Status: <span className="text-emerald-400 font-semibold">OAuth Server-Side Store Ready</span>
            </span>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="px-6 py-2 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold hover:bg-[#FF2B56] shadow-hud-red transition-all flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>SAVE CONFIGURATION</span>
          </button>
        </div>
      </form>
    </div>
  );
};
