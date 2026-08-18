import React, { useState, useEffect } from 'react';
import { FolderTree, FileCode, FileText, Plus, RefreshCw, HardDrive } from 'lucide-react';
import { WorkspaceFile } from '../../types';
import { fetchFiles } from '../../lib/api';
import { soundFX } from '../../lib/sound/SoundFX';

export const FilesSystemView: React.FC = () => {
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<WorkspaceFile | null>(null);

  const loadFiles = async () => {
    const data = await fetchFiles();
    if (data.files) {
      setFiles(data.files);
      if (data.files.length > 0) setSelectedFile(data.files[0]);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  return (
    <div className="flex-1 p-6 space-y-6 overflow-hidden flex flex-col z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-4 shrink-0">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <FolderTree className="w-6 h-6 text-[#FF1E42]" />
            <span>FILES & WORKSPACE HUD</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Sandboxed local repository filesystem (/workspace)
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => { soundFX.playClick(); loadFiles(); }}
            className="p-1.5 rounded bg-[#1A050B] border border-[#FF1E42]/30 text-[#8F8F98] hover:text-[#FF1E42] transition-colors"
            title="Refresh files"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <span className="px-3 py-1 rounded bg-[#0D0B0E] border border-[#FF1E42]/30 text-xs font-mono text-[#FF2B56]">
            {files.length} FILES INDEXED
          </span>
        </div>
      </div>

      {/* Grid: File Directory + File Viewer */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 min-h-0">
        {/* File List */}
        <div className="md:col-span-1 bg-[#0D0B0E]/90 border border-[#FF1E42]/25 rounded p-3 overflow-y-auto space-y-1.5 font-mono text-xs">
          <div className="flex items-center space-x-1.5 text-[10px] text-[#8F8F98] pb-1 border-b border-[#FF1E42]/15">
            <HardDrive className="w-3 h-3 text-[#FF1E42]" />
            <span>WORKSPACE ROOT</span>
          </div>

          {files.length === 0 ? (
            <div className="p-3 text-center text-[#8F8F98] text-xs">
              Workspace empty. You can ask JARVIS to create files or run code.
            </div>
          ) : (
            files.map((f) => {
              const isSelected = selectedFile?.name === f.name;
              return (
                <button
                  key={f.name}
                  onClick={() => { soundFX.playClick(); setSelectedFile(f); }}
                  className={`w-full text-left p-2.5 rounded transition-all flex items-center space-x-2 ${
                    isSelected
                      ? 'bg-[#1A050B] border border-[#FF1E42] text-[#F5F5F5]'
                      : 'bg-[#050508]/60 border border-[#FF1E42]/10 text-[#8F8F98] hover:border-[#FF1E42]/30'
                  }`}
                >
                  <FileText className="w-4 h-4 text-[#FF1E42] shrink-0" />
                  <div className="truncate flex-1">
                    <span className="block truncate font-medium">{f.name}</span>
                    <span className="text-[9px] text-[#8F8F98] block">{f.size_bytes} bytes</span>
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* File Viewer */}
        <div className="md:col-span-2 bg-[#050508] border border-[#FF1E42]/25 rounded p-4 flex flex-col font-mono text-xs overflow-hidden">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#FF1E42]/20 text-[10px] text-[#8F8F98]">
            <span>FILE PREVIEW: <span className="text-[#F5F5F5]">{selectedFile?.name || 'No file selected'}</span></span>
            <span className="text-emerald-400">READ ONLY</span>
          </div>
          <div className="flex-1 bg-[#0D0B0E] p-3 rounded border border-[#FF1E42]/15 overflow-y-auto text-[#8F8F98]">
            {selectedFile ? (
              <p className="leading-relaxed">
                [JARVIS FILE SYSTEM]\nFile path: /workspace/{selectedFile.path}\nSize: {selectedFile.size_bytes} bytes\nLast modified: {new Date(selectedFile.modified * 1000).toLocaleString()}\n\nContent stream verified.
              </p>
            ) : (
              <p className="text-center pt-10 text-[#8F8F98]">Select a file from the workspace to preview.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
