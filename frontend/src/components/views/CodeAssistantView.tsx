import React, { useState } from 'react';
import { Code2, Play, Terminal, Sparkles, Copy, Check, RotateCcw } from 'lucide-react';
import { executeCode } from '../../lib/api';
import { soundFX } from '../../lib/sound/SoundFX';

export const CodeAssistantView: React.FC = () => {
  const [language, setLanguage] = useState<'python' | 'javascript'>('python');
  const [code, setCode] = useState<string>(`# JARVIS AI Sandboxed Neural Routine
import math
import time

def compute_fibonacci(n):
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib

print("[JARVIS CORE] Calculating neural Fibonacci sequence...")
result = compute_fibonacci(12)
print("Sequence output:", result)
print("Checksum valid. Execution completed in 0.002s.")
`);

  const [output, setOutput] = useState<string>('Console idle. Click RUN to execute in sandboxed subprocess.');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const handleRunCode = async () => {
    soundFX.playProcessingBeep();
    setIsRunning(true);
    setOutput('Executing in isolated subprocess sandbox (5s timeout)...');

    const res = await executeCode(language, code);
    setIsRunning(false);

    if (res.result) {
      soundFX.playSuccessTone();
      const r = res.result;
      let text = '';
      if (r.stdout) text += r.stdout;
      if (r.stderr) text += '\n[STDERR]: ' + r.stderr;
      setOutput(text || '[Process finished with return code 0]');
    } else if (res.error) {
      soundFX.playErrorBuzz();
      setOutput(`[ERROR]: ${res.error}`);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex-1 p-6 space-y-4 overflow-hidden flex flex-col z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-3 shrink-0">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <Code2 className="w-6 h-6 text-[#FF1E42]" />
            <span>CODE ASSISTANT & SANDBOX</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            Isolated subprocess code generator and execution runtime
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-3">
          <select
            value={language}
            onChange={(e: any) => setLanguage(e.target.value)}
            className="bg-[#0D0B0E] border border-[#FF1E42]/30 text-xs font-mono text-[#FF1E42] rounded px-3 py-1.5 focus:outline-none"
          >
            <option value="python">Python 3.12</option>
            <option value="javascript">Node.js (JS)</option>
          </select>

          <button
            onClick={handleCopy}
            className="p-1.5 rounded bg-[#1A050B] border border-[#FF1E42]/30 text-[#8F8F98] hover:text-[#F5F5F5] transition-colors"
            title="Copy code"
          >
            {copied ? <Check className="w-4 h-4 text-[#FF1E42]" /> : <Copy className="w-4 h-4" />}
          </button>

          <button
            onClick={handleRunCode}
            disabled={isRunning}
            className="px-4 py-1.5 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold hover:bg-[#FF2B56] shadow-hud-red transition-all flex items-center space-x-1.5"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isRunning ? 'RUNNING...' : 'RUN CODE'}</span>
          </button>
        </div>
      </div>

      {/* Editor & Console Split */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 min-h-0">
        {/* Code Editor */}
        <div className="flex flex-col bg-[#050508] border border-[#FF1E42]/30 rounded overflow-hidden">
          <div className="bg-[#0D0B0E] px-3 py-1.5 border-b border-[#FF1E42]/20 flex items-center justify-between font-mono text-[10px] text-[#8F8F98]">
            <span>SCRIPT EDITOR // {language.toUpperCase()}</span>
            <span className="text-[#FF1E42]">SANDBOX MODE</span>
          </div>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="flex-1 bg-transparent text-xs font-mono text-[#F5F5F5] p-3 focus:outline-none resize-none leading-relaxed"
            spellCheck={false}
          />
        </div>

        {/* Output Console */}
        <div className="flex flex-col bg-[#050508] border border-[#FF1E42]/30 rounded overflow-hidden">
          <div className="bg-[#0D0B0E] px-3 py-1.5 border-b border-[#FF1E42]/20 flex items-center justify-between font-mono text-[10px] text-[#8F8F98]">
            <div className="flex items-center space-x-1.5 text-emerald-400">
              <Terminal className="w-3 h-3" />
              <span>TERMINAL OUTPUT</span>
            </div>
            <button 
              onClick={() => setOutput('Console cleared.')}
              className="text-[#8F8F98] hover:text-[#FF1E42]"
            >
              CLEAR
            </button>
          </div>
          <pre className="flex-1 p-3 text-xs font-mono text-emerald-400 overflow-y-auto whitespace-pre-wrap leading-relaxed">
            {output}
          </pre>
        </div>
      </div>
    </div>
  );
};
