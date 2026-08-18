import React from 'react';
import { AlertTriangle, Check, X, ShieldAlert } from 'lucide-react';
import { soundFX } from '../../lib/sound/SoundFX';

interface PermissionModalProps {
  isOpen: boolean;
  toolName: string;
  actionDescription: string;
  details?: any;
  onConfirm: () => void;
  onCancel: () => void;
}

export const PermissionModal: React.FC<PermissionModalProps> = ({
  isOpen,
  toolName,
  actionDescription,
  details,
  onConfirm,
  onCancel
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-md bg-[#0D0B0E] border-2 border-[#FF1E42] rounded-lg shadow-hud-red-lg p-5 space-y-4 font-sans relative">
        {/* HUD Corner Notches */}
        <span className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-[#FF2B56]" />
        <span className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-[#FF2B56]" />

        {/* Modal Header */}
        <div className="flex items-center space-x-3 text-[#FF1E42] pb-2 border-b border-[#FF1E42]/25 font-mono text-sm">
          <ShieldAlert className="w-5 h-5 animate-pulse" />
          <span className="font-bold tracking-widest uppercase">SECURITY PROTOCOL REQUIRED</span>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <div className="text-xs font-mono text-[#8F8F98]">
            TOOL: <span className="text-[#FF1E42] font-semibold">{toolName}</span>
          </div>
          <p className="text-sm text-[#F5F5F5] font-medium leading-relaxed">
            {actionDescription}
          </p>

          {details && (
            <pre className="p-2 bg-[#050508] border border-[#FF1E42]/20 rounded text-[10px] font-mono text-[#8F8F98] max-h-32 overflow-y-auto">
              {typeof details === 'string' ? details : JSON.stringify(details, null, 2)}
            </pre>
          )}
        </div>

        <p className="text-[11px] text-[#8F8F98]/80 font-mono">
          Say <span className="text-[#FF1E42] font-bold">"Yes, proceed"</span> or click confirm to authorize this action.
        </p>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-2">
          <button
            onClick={() => { soundFX.playClick(); onCancel(); }}
            className="px-4 py-1.5 rounded bg-[#1A050B] border border-[#FF1E42]/30 text-xs font-mono text-[#8F8F98] hover:text-[#F5F5F5] transition-colors flex items-center space-x-1.5"
          >
            <X className="w-3.5 h-3.5" />
            <span>CANCEL</span>
          </button>
          <button
            onClick={() => { soundFX.playSuccessTone(); onConfirm(); }}
            className="px-5 py-1.5 rounded bg-[#FF1E42] text-xs font-mono text-white font-bold hover:bg-[#FF2B56] shadow-hud-red transition-all flex items-center space-x-1.5"
          >
            <Check className="w-3.5 h-3.5" />
            <span>AUTHORIZE</span>
          </button>
        </div>
      </div>
    </div>
  );
};
