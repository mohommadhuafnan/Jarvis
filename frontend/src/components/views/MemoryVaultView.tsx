import React, { useState, useEffect } from 'react';
import { Database, Search, Plus, Tag, Trash2, Key } from 'lucide-react';
import { MemoryItem } from '../../types';
import { fetchMemories, storeMemory } from '../../lib/api';
import { soundFX } from '../../lib/sound/SoundFX';

export const MemoryVaultView: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('preferences');
  const [keyInput, setKeyInput] = useState('');
  const [valueInput, setValueInput] = useState('');

  const loadMemories = async () => {
    const data = await fetchMemories();
    if (data.memories) setMemories(data.memories);
  };

  useEffect(() => {
    loadMemories();
  }, []);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyInput.trim() || !valueInput.trim()) return;
    soundFX.playSuccessTone();
    await storeMemory(category, keyInput.trim(), valueInput.trim());
    setKeyInput('');
    setValueInput('');
    loadMemories();
  };

  const filtered = (memories || []).filter(m => 
    (m?.key || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (m?.value || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (m?.category || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <Database className="w-6 h-6 text-[#FF1E42]" />
            <span>LONG-TERM MEMORY VAULT</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Encrypted associative knowledge store & personal facts graph
          </p>
        </div>

        <div className="relative w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#8F8F98]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memory vault..."
            className="w-full bg-[#0D0B0E] border border-[#FF1E42]/30 rounded pl-8 pr-3 py-1.5 text-xs text-[#F5F5F5] placeholder-[#8F8F98]/50 focus:outline-none font-sans"
          />
        </div>
      </div>

      {/* Add Memory Form */}
      <form onSubmit={handleAddMemory} className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 grid grid-cols-1 md:grid-cols-4 gap-3">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="bg-[#1A050B] border border-[#FF1E42]/30 text-xs font-mono text-[#FF1E42] rounded px-3 py-1.5 focus:outline-none"
        >
          <option value="preferences">Preferences</option>
          <option value="projects">Projects</option>
          <option value="people">Important People</option>
          <option value="routines">Routines</option>
          <option value="notes">Personal Notes</option>
        </select>

        <input
          type="text"
          value={keyInput}
          onChange={(e) => setKeyInput(e.target.value)}
          placeholder="Subject / Key (e.g. 'Main Project')"
          className="bg-[#050508] border border-[#FF1E42]/20 rounded px-3 py-1.5 text-xs text-[#F5F5F5] focus:outline-none font-sans"
        />

        <input
          type="text"
          value={valueInput}
          onChange={(e) => setValueInput(e.target.value)}
          placeholder="Fact / Memory to store"
          className="bg-[#050508] border border-[#FF1E42]/20 rounded px-3 py-1.5 text-xs text-[#F5F5F5] focus:outline-none font-sans"
        />

        <button
          type="submit"
          disabled={!keyInput.trim() || !valueInput.trim()}
          className="px-4 py-1.5 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold hover:bg-[#FF2B56] shadow-hud-red disabled:opacity-40 flex items-center justify-center space-x-1"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>STORE MEMORY</span>
        </button>
      </form>

      {/* Memory Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {filtered.map((mem) => (
          <div
            key={mem.id}
            className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/25 shadow-hud-red/10 space-y-2 relative"
          >
            <div className="flex items-center justify-between text-[10px] font-mono">
              <span className="px-2 py-0.5 rounded bg-[#1A050B] border border-[#FF1E42]/30 text-[#FF2B56] uppercase font-bold">
                {mem.category}
              </span>
              <span className="text-[#8F8F98] text-[9px]">ENCRYPTED</span>
            </div>

            <div className="flex items-center space-x-1.5 text-xs font-sans font-bold text-[#F5F5F5] pt-1">
              <Key className="w-3 h-3 text-[#FF1E42]" />
              <span>{mem.key}</span>
            </div>

            <p className="text-xs font-sans text-[#8F8F98] leading-relaxed">
              {mem.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
