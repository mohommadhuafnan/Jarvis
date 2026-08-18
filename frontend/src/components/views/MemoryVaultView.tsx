import React, { useState, useEffect } from 'react';
import { Database, Search, Plus, Tag, Trash2, Key, Upload, FileText, Calendar, User, CheckCircle, Clock, BookOpen, AlertCircle, RefreshCw } from 'lucide-react';
import { MemoryItem } from '../../types';
import {
  fetchMemories,
  storeMemory,
  uploadKnowledgeFile,
  confirmSaveKnowledge,
  fetchKnowledgeDocs,
  fetchKnowledgeTimetable,
  fetchPersonalProfile,
  updatePersonalProfile,
  forgetKnowledge
} from '../../lib/api';
import { soundFX } from '../../lib/sound/SoundFX';

type VaultTab = 'profile' | 'timetable' | 'documents' | 'upload' | 'memories';

export const MemoryVaultView: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<VaultTab>('profile');

  // Memories state
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('preferences');
  const [keyInput, setKeyInput] = useState('');
  const [valueInput, setValueInput] = useState('');

  // Knowledge Documents & Timetable State
  const [profile, setProfile] = useState<any>({
    degree: 'BICT',
    year: '2nd Year',
    primary_project: 'AgriMind AI',
    university: 'Faculty of Technology'
  });
  const [documents, setDocuments] = useState<any[]>([]);
  const [timetableData, setTimetableData] = useState<any>({ active_document: null, total_classes: 0, timetable: {} });
  const [loading, setLoading] = useState<boolean>(false);

  // Upload & Analysis State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [previewAnalysis, setPreviewAnalysis] = useState<any | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const loadAllVaultData = async () => {
    setLoading(true);
    try {
      const [memRes, profRes, docsRes, ttRes] = await Promise.all([
        fetchMemories(),
        fetchPersonalProfile(),
        fetchKnowledgeDocs(),
        fetchKnowledgeTimetable()
      ]);

      if (memRes.memories) setMemories(memRes.memories);
      if (profRes.profile) setProfile(profRes.profile);
      if (docsRes.documents) setDocuments(docsRes.documents);
      if (ttRes.timetable) setTimetableData(ttRes);
    } catch (e) {
      console.warn("Error loading vault data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllVaultData();
  }, []);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyInput.trim() || !valueInput.trim()) return;
    soundFX.playSuccessTone();
    await storeMemory(category, keyInput.trim(), valueInput.trim());
    setKeyInput('');
    setValueInput('');
    loadAllVaultData();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];
    setSelectedFile(file);
    setUploading(true);
    setPreviewAnalysis(null);
    setSaveStatus("AI Multimodal Core analyzing document...");
    soundFX.playProcessingBeep();

    const res = await uploadKnowledgeFile(file);
    setUploading(false);
    if (res.success && res.preview) {
      soundFX.playSuccessTone();
      setPreviewAnalysis(res.preview);
      setSaveStatus("Analysis complete. Review extracted information and confirm.");
    } else {
      setSaveStatus("Analysis failed. Please ensure backend is online.");
    }
  };

  const handleConfirmSave = async () => {
    if (!previewAnalysis) return;
    soundFX.playSuccessTone();
    setSaveStatus("Committing knowledge to MongoDB Knowledge Vault...");
    const res = await confirmSaveKnowledge(
      previewAnalysis.doc_id,
      previewAnalysis.filename,
      previewAnalysis.file_path,
      previewAnalysis.extracted_data
    );

    if (res.success) {
      setSaveStatus(`Saved successfully! ${res.timetable_count || 0} classes and ${res.facts_count || 0} facts stored.`);
      setPreviewAnalysis(null);
      setSelectedFile(null);
      loadAllVaultData();
      setTimeout(() => setSaveStatus(null), 4000);
    } else {
      setSaveStatus("Error saving knowledge to vault.");
    }
  };

  const handleForgetItem = async (target: string) => {
    soundFX.playAlertTone();
    await forgetKnowledge(target);
    loadAllVaultData();
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
            <span>PERSONAL KNOWLEDGE VAULT</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Encrypted personal context, active university timetables, profile & document facts
          </p>
        </div>

        {/* Sub-Navigation Tabs */}
        <div className="flex items-center space-x-1 bg-[#1A050B] p-1 rounded border border-[#FF1E42]/30 text-xs font-mono">
          <button
            onClick={() => { soundFX.playClick(); setActiveSubTab('profile'); }}
            className={`px-3 py-1 rounded flex items-center space-x-1.5 transition-all ${
              activeSubTab === 'profile'
                ? 'bg-[#FF1E42] text-white shadow-hud-red font-bold'
                : 'text-[#8F8F98] hover:text-[#F5F5F5]'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>PROFILE</span>
          </button>

          <button
            onClick={() => { soundFX.playClick(); setActiveSubTab('timetable'); }}
            className={`px-3 py-1 rounded flex items-center space-x-1.5 transition-all ${
              activeSubTab === 'timetable'
                ? 'bg-[#FF1E42] text-white shadow-hud-red font-bold'
                : 'text-[#8F8F98] hover:text-[#F5F5F5]'
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>TIMETABLE</span>
          </button>

          <button
            onClick={() => { soundFX.playClick(); setActiveSubTab('documents'); }}
            className={`px-3 py-1 rounded flex items-center space-x-1.5 transition-all ${
              activeSubTab === 'documents'
                ? 'bg-[#FF1E42] text-white shadow-hud-red font-bold'
                : 'text-[#8F8F98] hover:text-[#F5F5F5]'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>DOCUMENTS ({documents.length})</span>
          </button>

          <button
            onClick={() => { soundFX.playClick(); setActiveSubTab('upload'); }}
            className={`px-3 py-1 rounded flex items-center space-x-1.5 transition-all ${
              activeSubTab === 'upload'
                ? 'bg-[#FF1E42] text-white shadow-hud-red font-bold'
                : 'text-[#8F8F98] hover:text-[#F5F5F5]'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>INGEST FILE</span>
          </button>

          <button
            onClick={() => { soundFX.playClick(); setActiveSubTab('memories'); }}
            className={`px-3 py-1 rounded flex items-center space-x-1.5 transition-all ${
              activeSubTab === 'memories'
                ? 'bg-[#FF1E42] text-white shadow-hud-red font-bold'
                : 'text-[#8F8F98] hover:text-[#F5F5F5]'
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>MEMORIES</span>
          </button>
        </div>
      </div>

      {/* --- TAB 1: PROFILE --- */}
      {activeSubTab === 'profile' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-1">
              <div className="text-[10px] font-mono text-[#8F8F98] uppercase">DEGREE PROGRAM</div>
              <div className="text-lg font-bold text-[#F5F5F5] font-sans">{profile.degree || 'BICT'}</div>
              <div className="text-xs font-mono text-[#FF2B56]">Faculty of Technology</div>
            </div>

            <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-1">
              <div className="text-[10px] font-mono text-[#8F8F98] uppercase">ACADEMIC YEAR</div>
              <div className="text-lg font-bold text-[#F5F5F5] font-sans">{profile.year || '2nd Year'}</div>
              <div className="text-xs font-mono text-emerald-400">Active Undergraduate</div>
            </div>

            <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-1">
              <div className="text-[10px] font-mono text-[#8F8F98] uppercase">PRIMARY PROJECT</div>
              <div className="text-lg font-bold text-[#FF1E42] font-sans">{profile.primary_project || 'AgriMind AI'}</div>
              <div className="text-xs font-mono text-[#8F8F98]">Autonomous Agriculture & Vision</div>
            </div>

            <div className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/30 space-y-1">
              <div className="text-[10px] font-mono text-[#8F8F98] uppercase">ACTIVE TIMETABLE</div>
              <div className="text-sm font-bold text-[#F5F5F5] font-sans truncate">
                {timetableData.active_document || 'Semester Timetable'}
              </div>
              <div className="text-xs font-mono text-emerald-400">
                {timetableData.total_classes || 0} scheduled classes
              </div>
            </div>
          </div>

          <div className="p-5 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/20 space-y-4">
            <h3 className="text-sm font-bold font-mono text-[#F5F5F5] flex items-center space-x-2">
              <BookOpen className="w-4 h-4 text-[#FF1E42]" />
              <span>PERSONAL KNOWLEDGE VAULT SUMMARY</span>
            </h3>
            <p className="text-xs text-[#8F8F98] leading-relaxed">
              JARVIS continuously synchronizes your verified personal profile with uploaded documents, timetables, and conversation facts.
              When you ask personal questions (e.g. <i>"What lectures do I have today?"</i> or <i>"What is my main project?"</i>), JARVIS references this verified knowledge vault first with zero hallucination.
            </p>
          </div>
        </div>
      )}

      {/* --- TAB 2: ACTIVE TIMETABLE --- */}
      {activeSubTab === 'timetable' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono text-[#8F8F98]">
              Active Schedule Source: <span className="text-[#FF2B56] font-bold">{timetableData.active_document || 'No Timetable Active'}</span>
            </div>
            <span className="px-2.5 py-0.5 rounded bg-[#1A050B] border border-emerald-500/40 text-[10px] font-mono text-emerald-400">
              {timetableData.total_classes || 0} WEEKLY CLASSES
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map((day) => {
              const dayClasses = (timetableData.timetable && timetableData.timetable[day]) || [];
              return (
                <div key={day} className="p-3 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/20 space-y-2.5">
                  <div className="border-b border-[#FF1E42]/20 pb-1.5 flex items-center justify-between">
                    <span className="text-xs font-bold font-mono text-[#F5F5F5]">{day.toUpperCase()}</span>
                    <span className="text-[10px] font-mono text-[#FF1E42]">{dayClasses.length}</span>
                  </div>

                  {dayClasses.length === 0 ? (
                    <div className="text-[11px] font-mono text-[#8F8F98]/50 py-4 text-center">
                      No classes
                    </div>
                  ) : (
                    dayClasses.map((c: any, i: number) => (
                      <div key={i} className="p-2 rounded bg-[#1A050B]/80 border border-[#FF1E42]/15 space-y-1">
                        <div className="flex items-center justify-between text-[10px] font-mono text-[#FF2B56]">
                          <span>{c.start_time}{c.end_time ? ` - ${c.end_time}` : ''}</span>
                          <span className="text-[#8F8F98]">{c.room || 'TBD'}</span>
                        </div>
                        <div className="text-xs font-bold text-[#F5F5F5] line-clamp-2">{c.subject}</div>
                        {c.lecturer && <div className="text-[10px] text-[#8F8F98]">{c.lecturer}</div>}
                      </div>
                    ))
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* --- TAB 3: DOCUMENTS --- */}
      {activeSubTab === 'documents' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <div key={doc.id} className="p-4 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/25 space-y-3 relative">
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className={`px-2 py-0.5 rounded border uppercase font-bold ${
                    doc.is_active
                      ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-400'
                      : 'bg-[#1A050B] border-[#FF1E42]/20 text-[#8F8F98]'
                  }`}>
                    {doc.is_active ? 'ACTIVE' : 'SUPERSEDED'}
                  </span>
                  <span className="text-[#8F8F98] text-[9px]">{doc.doc_type}</span>
                </div>

                <div className="flex items-center space-x-2 text-xs font-bold text-[#F5F5F5]">
                  <FileText className="w-4 h-4 text-[#FF1E42] shrink-0" />
                  <span className="truncate">{doc.filename}</span>
                </div>

                <p className="text-xs text-[#8F8F98] leading-relaxed line-clamp-3">
                  {doc.summary || 'Ingested knowledge document.'}
                </p>

                <div className="pt-2 border-t border-[#FF1E42]/10 flex items-center justify-between text-[10px] font-mono text-[#8F8F98]">
                  <span>{doc.extracted_count} facts extracted</span>
                  <button
                    onClick={() => handleForgetItem(doc.filename)}
                    className="text-[#FF1E42] hover:text-[#FF2B56] flex items-center space-x-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Forget</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --- TAB 4: UPLOAD & INGEST --- */}
      {activeSubTab === 'upload' && (
        <div className="space-y-6">
          <div className="p-8 bg-[#0D0B0E]/90 rounded border-2 border-dashed border-[#FF1E42]/40 flex flex-col items-center justify-center space-y-4 text-center">
            <Upload className="w-10 h-10 text-[#FF1E42] animate-pulse" />
            <div>
              <h3 className="text-sm font-bold text-[#F5F5F5] font-sans">
                UPLOAD TIMETABLE, PDF, IMAGE, OR ASSIGNMENT
              </h3>
              <p className="text-xs text-[#8F8F98] font-mono mt-1">
                Gemini Multimodal Core extracts schedules, subjects, deadlines, and profile facts automatically.
              </p>
            </div>

            <label className="px-4 py-2 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold hover:bg-[#FF2B56] shadow-hud-red cursor-pointer flex items-center space-x-2">
              <Upload className="w-4 h-4" />
              <span>CHOOSE FILE TO INGEST</span>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.webp,.txt"
                onChange={handleFileUpload}
                className="hidden"
                disabled={uploading}
              />
            </label>

            {uploading && (
              <div className="flex items-center space-x-2 text-xs font-mono text-[#FF2B56]">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Extracting multimodal structured data...</span>
              </div>
            )}
          </div>

          {saveStatus && (
            <div className="p-3 bg-[#1A050B] rounded border border-[#FF1E42]/30 text-xs font-mono text-[#F5F5F5] flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-[#FF1E42]" />
              <span>{saveStatus}</span>
            </div>
          )}

          {/* Analysis Preview & Confirmation Card */}
          {previewAnalysis && (
            <div className="p-5 bg-[#0D0B0E]/95 rounded border border-emerald-500/40 space-y-4 shadow-hud-red/20">
              <div className="flex items-center justify-between border-b border-emerald-500/20 pb-3">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <span className="text-sm font-bold text-[#F5F5F5] font-sans">
                    EXTRACTED KNOWLEDGE PREVIEW — {previewAnalysis.filename}
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-950/50 border border-emerald-500/40 text-[10px] font-mono text-emerald-400 uppercase">
                  {previewAnalysis.doc_type}
                </span>
              </div>

              <p className="text-xs text-[#F5F5F5] font-sans leading-relaxed">
                {previewAnalysis.summary}
              </p>

              {previewAnalysis.extracted_data?.timetable_entries?.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-mono font-bold text-[#FF2B56]">
                    DETECTED TIMETABLE CLASSES ({previewAnalysis.extracted_data.timetable_entries.length}):
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
                    {previewAnalysis.extracted_data.timetable_entries.map((c: any, idx: number) => (
                      <div key={idx} className="p-2 rounded bg-[#1A050B] border border-[#FF1E42]/20 text-[11px] font-mono space-y-0.5">
                        <div className="text-[#FF1E42] font-bold">{c.weekday} {c.start_time}</div>
                        <div className="text-[#F5F5F5] font-sans text-xs truncate">{c.subject}</div>
                        <div className="text-[#8F8F98] text-[10px]">{c.room}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={handleConfirmSave}
                  className="px-5 py-2 rounded bg-emerald-500 text-black text-xs font-mono font-bold hover:bg-emerald-400 shadow-md flex items-center space-x-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>CONFIRM & COMMIT TO VAULT</span>
                </button>
                <button
                  onClick={() => setPreviewAnalysis(null)}
                  className="px-4 py-2 rounded bg-[#1A050B] border border-[#FF1E42]/30 text-xs font-mono text-[#8F8F98] hover:text-[#F5F5F5]"
                >
                  Discard
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* --- TAB 5: MEMORIES --- */}
      {activeSubTab === 'memories' && (
        <div className="space-y-6">
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
                  <button
                    onClick={() => handleForgetItem(mem.key)}
                    className="text-[#8F8F98] hover:text-[#FF1E42]"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
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
      )}
    </div>
  );
};
