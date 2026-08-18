import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[JARVIS UI Crash Caught]:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[#050508] text-[#F5F5F5] p-6 font-mono select-none">
          <div className="p-6 bg-[#0D0B0E] border border-[#FF1E42] rounded-lg shadow-[0_0_20px_rgba(255,30,66,0.3)] max-w-lg w-full text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-[#1A050B] border border-[#FF1E42] flex items-center justify-center text-[#FF1E42] font-bold text-xl">
              !
            </div>
            <h2 className="text-lg font-bold text-[#FF1E42] tracking-wider uppercase">
              HUD Interface Recovery
            </h2>
            <p className="text-xs text-[#8F8F98]">
              An unhandled render exception occurred in the HUD layer:
            </p>
            <div className="p-3 bg-[#050508] border border-[#FF1E42]/20 rounded text-[11px] text-left text-red-400 overflow-x-auto">
              {this.state.error?.message || 'Unknown runtime render error'}
            </div>
            <button
              onClick={() => {
                this.setState({ hasError: false });
                window.location.reload();
              }}
              className="px-4 py-2 bg-[#FF1E42] text-white text-xs font-bold rounded shadow-[0_0_12px_#FF1E42] hover:bg-[#FF2B56] transition-all uppercase tracking-wider"
            >
              Reboot HUD Interface
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
