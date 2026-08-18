import React from 'react';
import { 
  LayoutDashboard, 
  MessageSquareCode, 
  CheckSquare, 
  Calendar, 
  Mail, 
  Code2, 
  FolderTree, 
  Workflow, 
  Database, 
  Settings,
  Radio,
  Terminal as TerminalIcon
} from 'lucide-react';
import { SystemTelemetry } from '../../types';
import { soundFX } from '../../lib/sound/SoundFX';

export type NavTab = 
  | 'dashboard' 
  | 'chat' 
  | 'tasks' 
  | 'calendar' 
  | 'email' 
  | 'code' 
  | 'files' 
  | 'automation' 
  | 'memory' 
  | 'settings';

interface CyberSidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  telemetry?: SystemTelemetry;
}

export const CyberSidebar: React.FC<CyberSidebarProps> = ({
  activeTab,
  onSelectTab,
  telemetry
}) => {
  const navItems = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'chat' as NavTab, label: 'Chat Workspace', icon: MessageSquareCode },
    { id: 'tasks' as NavTab, label: 'Tasks', icon: CheckSquare },
    { id: 'calendar' as NavTab, label: 'Calendar', icon: Calendar },
    { id: 'email' as NavTab, label: 'Email', icon: Mail },
    { id: 'code' as NavTab, label: 'Code Assistant', icon: Code2 },
    { id: 'files' as NavTab, label: 'Files & System', icon: FolderTree },
    { id: 'automation' as NavTab, label: 'Automation', icon: Workflow },
    { id: 'memory' as NavTab, label: 'Memory Vault', icon: Database },
    { id: 'settings' as NavTab, label: 'Settings', icon: Settings },
  ];

  const handleNavClick = (tab: NavTab) => {
    soundFX.playClick();
    onSelectTab(tab);
  };

  const cpuVal = telemetry?.cpu_usage || 23;
  const ramVal = telemetry?.ram_usage || 45;

  return (
    <aside className="w-64 h-full bg-[#070508]/90 border-r border-[#FF1E42]/20 flex flex-col justify-between p-3 select-none z-30 overflow-y-auto">
      {/* Top Branding Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-3 p-2 bg-[#0D0B0E]/80 rounded-md border border-[#FF1E42]/25 shadow-hud-red/20">
          {/* Circular radar reticle */}
          <div className="relative w-10 h-10 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border border-[#FF1E42]/40 animate-spin-slow" />
            <div className="absolute inset-1 rounded-full border border-dashed border-[#FF1E42]/60" />
            <div className="w-3 h-3 rounded-full bg-[#FF1E42]/30 flex items-center justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FF1E42] animate-ping" />
            </div>
          </div>

          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-sans text-base font-bold tracking-widest text-[#F5F5F5]">
                JARVIS
              </span>
            </div>
            <span className="font-mono text-[9px] tracking-widest text-[#8F8F98] uppercase block">
              AI ASSISTANT
            </span>
            <div className="mt-0.5 inline-flex items-center space-x-1 px-1.5 py-0.2 rounded bg-[#FF1E42]/20 border border-[#FF1E42]/40 text-[8px] font-mono text-[#FF2B56] font-semibold">
              <span className="w-1 h-1 rounded-full bg-[#FF1E42]" />
              <span>ONLINE</span>
            </div>
          </div>
        </div>

        {/* Navigation Category Label */}
        <div>
          <div className="px-2 mb-1 flex items-center justify-between text-[10px] font-mono uppercase tracking-widest text-[#8F8F98]/70">
            <span>NAVIGATION</span>
            <Radio className="w-2.5 h-2.5 text-[#FF1E42]" />
          </div>

          {/* Navigation Links */}
          <nav className="space-y-0.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded text-xs font-medium tracking-wide transition-all text-left relative ${
                    isActive
                      ? 'bg-gradient-to-r from-[#1A050B] to-[#0D0B0E] text-[#F5F5F5] border border-[#FF1E42]/50 shadow-[0_0_12px_rgba(255,30,66,0.3)]'
                      : 'text-[#8F8F98] hover:text-[#F5F5F5] hover:bg-[#0D0B0E]/60'
                  }`}
                >
                  {/* Red active left indicator */}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-4 bg-[#FF1E42] rounded-r shadow-[0_0_8px_#FF1E42]" />
                  )}

                  <Icon className={`w-3.5 h-3.5 transition-colors ${isActive ? 'text-[#FF1E42]' : 'text-[#8F8F98]'}`} />
                  <span className="font-sans text-[13px]">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Bottom Widgets: System Status & Terminal */}
      <div className="space-y-2.5 pt-3 border-t border-[#FF1E42]/15">
        {/* System Status Telemetry Card */}
        <div className="p-2.5 bg-[#0D0B0E]/90 rounded border border-[#FF1E42]/20 font-mono text-[10px] space-y-1.5">
          <div className="flex items-center justify-between text-[#8F8F98] text-[9px] uppercase tracking-wider">
            <span>SYSTEM STATUS</span>
            <span className="text-[#FF1E42]">● READY</span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[#8F8F98]">System Online</span>
              <span className="text-[#FF1E42] font-semibold">100%</span>
            </div>
            <div className="w-full bg-[#1A050B] h-1 rounded-full overflow-hidden">
              <div className="bg-[#FF1E42] h-full w-full shadow-[0_0_6px_#FF1E42]" />
            </div>

            <div className="flex items-center justify-between pt-0.5">
              <span className="text-[#8F8F98]">Core AI</span>
              <span className="text-[#FF1E42] font-semibold">100%</span>
            </div>
            <div className="w-full bg-[#1A050B] h-1 rounded-full overflow-hidden">
              <div className="bg-[#FF1E42] h-full w-full shadow-[0_0_6px_#FF1E42]" />
            </div>

            <div className="flex items-center justify-between pt-0.5">
              <span className="text-[#8F8F98]">Memory</span>
              <span className="text-[#FF2B56]">78%</span>
            </div>
            <div className="w-full bg-[#1A050B] h-1 rounded-full overflow-hidden">
              <div className="bg-[#FF1E42] h-full w-[78%]" />
            </div>

            <div className="flex items-center justify-between pt-0.5">
              <span className="text-[#8F8F98]">CPU Usage</span>
              <span className="text-[#F5F5F5]">{cpuVal}%</span>
            </div>
            <div className="w-full bg-[#1A050B] h-1 rounded-full overflow-hidden">
              <div className="bg-[#FF1E42] h-full" style={{ width: `${Math.min(100, cpuVal)}%` }} />
            </div>

            <div className="flex items-center justify-between pt-0.5">
              <span className="text-[#8F8F98]">RAM Usage</span>
              <span className="text-[#F5F5F5]">{ramVal}%</span>
            </div>
            <div className="w-full bg-[#1A050B] h-1 rounded-full overflow-hidden">
              <div className="bg-[#FF1E42] h-full" style={{ width: `${Math.min(100, ramVal)}%` }} />
            </div>

            <div className="flex items-center justify-between pt-0.5">
              <span className="text-[#8F8F98]">Network</span>
              <span className="text-emerald-400 font-semibold">Up</span>
            </div>
          </div>
        </div>

        {/* Monospace Hacker Terminal Box */}
        <div className="p-2 bg-[#050508] rounded border border-[#FF1E42]/20 font-mono text-[10px]">
          <div className="flex items-center space-x-1.5 text-[#8F8F98] text-[9px] mb-1">
            <TerminalIcon className="w-2.5 h-2.5 text-[#FF1E42]" />
            <span>TERMINAL</span>
          </div>
          <div className="text-[#FF1E42] truncate">
            jarvis@system:~$ <span className="inline-block w-1.5 h-3 bg-[#FF1E42] animate-pulse align-middle" />
          </div>
        </div>
      </div>
    </aside>
  );
};
