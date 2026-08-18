// Single Unified Voice & Speech-To-Text Engine for JARVIS Personal Assistant
// Eliminates Web Speech API collisions by running a single shared recognizer with always-ready wake-word and hands-free multi-turn support.

export type VoiceMode = 'WAKE_WORD' | 'COMMAND' | 'CONVERSATION' | 'MUTED';

export interface SpeechCallbacks {
  onInterim?: (text: string) => void;
  onFinal?: (text: string) => void;
  onWakeWord?: (wakeWord: string, followUpCommand?: string) => void;
  onSpeechDetected?: () => void;
  onStateChange?: (mode: VoiceMode) => void;
  onError?: (err: any) => void;
}

export class SpeechEngine {
  private recognition: any = null;
  private isRunning = false;
  private mode: VoiceMode = 'WAKE_WORD';
  private wakeWords = ["hello jarvis", "hey jarvis", "ok jarvis", "hi jarvis", "jarvis", "computer"];
  private language = 'en-US';
  private callbacks: SpeechCallbacks = {};
  private silenceTimer: any = null;
  private lastTranscript = '';
  private isTemporarilyPaused = false;
  private restartTimeout: any = null;

  constructor() {
    this._initRecognizer();
  }

  private _initRecognizer() {
    if (typeof window === 'undefined') return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("[SpeechEngine] Web Speech API not supported in this browser.");
      return;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = this.language;

      this.recognition.onresult = (event: any) => this._handleResult(event);
      this.recognition.onerror = (event: any) => this._handleError(event);
      this.recognition.onend = () => this._handleEnd();
    } catch (e) {
      console.error("[SpeechEngine] Initialization error:", e);
    }
  }

  private _handleResult(event: any) {
    if (this.isTemporarilyPaused || this.mode === 'MUTED') return;

    if (this.callbacks.onSpeechDetected) {
      this.callbacks.onSpeechDetected();
    }

    let interim = '';
    let final = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const item = event.results[i];
      const text = item[0].transcript;
      if (item.isFinal) {
        final += text;
      } else {
        interim += text;
      }
    }

    const currentText = (final || interim).trim();
    if (!currentText) return;

    // --- MODE A: WAKE WORD LISTENING ---
    if (this.mode === 'WAKE_WORD') {
      const lower = currentText.toLowerCase();
      for (const ww of this.wakeWords) {
        if (lower.includes(ww)) {
          // Extract command spoken after wake word in same utterance
          const wwIndex = lower.indexOf(ww);
          const afterText = currentText.slice(wwIndex + ww.length).replace(/^[,.\s]+/, '').trim();

          console.log(`[SpeechEngine] Wake word "${ww}" detected! Attached command: "${afterText}"`);
          if (this.callbacks.onWakeWord) {
            this.callbacks.onWakeWord(ww, afterText);
          }
          return;
        }
      }
      return;
    }

    // --- MODE B: ACTIVE COMMAND OR CONTINUOUS CONVERSATION ---
    if (this.mode === 'COMMAND' || this.mode === 'CONVERSATION') {
      this.lastTranscript = currentText;

      if (this.callbacks.onInterim) {
        this.callbacks.onInterim(currentText);
      }

      // Reset silence auto-submit timer
      if (this.silenceTimer) clearTimeout(this.silenceTimer);

      if (final) {
        // Recognition flagged a final segment
        this._dispatchFinal(final.trim());
      } else {
        // Wait 1.2 seconds of silence after last spoken word before auto-finalizing
        this.silenceTimer = setTimeout(() => {
          if (this.lastTranscript.trim()) {
            this._dispatchFinal(this.lastTranscript.trim());
          }
        }, 1200);
      }
    }
  }

  private _dispatchFinal(text: string) {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }

    const clean = text.trim();
    this.lastTranscript = '';
    if (!clean) return;

    console.log(`[SpeechEngine] Spoken command captured: "${clean}"`);
    if (this.callbacks.onFinal) {
      this.callbacks.onFinal(clean);
    }
  }

  private _handleError(event: any) {
    if (event.error === 'no-speech') return;
    if (event.error === 'aborted') return;
    console.warn("[SpeechEngine] Recognition event:", event.error);
    if (this.callbacks.onError) {
      this.callbacks.onError(event.error);
    }
  }

  private _handleEnd() {
    // Continuous always-ready loop: Auto-restart recognition if meant to be running
    if (this.isRunning && !this.isTemporarilyPaused && this.mode !== 'MUTED') {
      if (this.restartTimeout) clearTimeout(this.restartTimeout);
      this.restartTimeout = setTimeout(() => {
        if (this.isRunning && this.recognition && !this.isTemporarilyPaused && this.mode !== 'MUTED') {
          try {
            this.recognition.start();
          } catch (e) {
            // Already active
          }
        }
      }, 250);
    }
  }

  // --- Public API ---
  public start(callbacks?: SpeechCallbacks) {
    if (callbacks) {
      this.callbacks = { ...this.callbacks, ...callbacks };
    }
    this.isRunning = true;
    this.isTemporarilyPaused = false;

    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (e) {
        // Recognition might already be running
      }
    }
  }

  public stop() {
    this.isRunning = false;
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    if (this.restartTimeout) clearTimeout(this.restartTimeout);
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
  }

  public setMode(newMode: VoiceMode) {
    this.mode = newMode;
    if (this.callbacks.onStateChange) {
      this.callbacks.onStateChange(newMode);
    }
  }

  public getMode(): VoiceMode {
    return this.mode;
  }

  public pauseRecognition() {
    this.isTemporarilyPaused = true;
  }

  public resumeRecognition() {
    this.isTemporarilyPaused = false;
    if (this.isRunning && this.recognition) {
      try {
        this.recognition.start();
      } catch (e) {}
    }
  }

  public setWakeWord(word: string) {
    const w = word.toLowerCase().trim();
    if (w && !this.wakeWords.includes(w)) {
      this.wakeWords.unshift(w);
    }
  }

  public setLanguage(langCode: string) {
    if (langCode === 'ta') {
      this.language = 'ta-IN';
    } else if (langCode === 'si') {
      this.language = 'si-LK';
    } else {
      this.language = 'en-US';
    }
    if (this.recognition) {
      this.recognition.lang = this.language;
    }
  }

  public setCallbacks(callbacks: SpeechCallbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  // Compatibility wrappers for existing code
  public startListening(onInterim: (text: string) => void, onFinal: (text: string) => void) {
    this.callbacks.onInterim = onInterim;
    this.callbacks.onFinal = onFinal;
    this.setMode('COMMAND');
    this.start();
  }

  public stopListening() {
    if (this.mode === 'COMMAND') {
      this.setMode('WAKE_WORD');
    }
  }

  public isActive(): boolean {
    return this.isRunning && this.mode === 'COMMAND';
  }
}

export const speechEngine = new SpeechEngine();
export const sttService = speechEngine;
