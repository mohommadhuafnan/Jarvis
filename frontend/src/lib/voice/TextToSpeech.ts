// High-Performance Browser Text-to-Speech Engine with Barge-In & Voice Tuning
export class TextToSpeechService {
  private synth: SpeechSynthesis | null = null;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private isSpeakingState = false;
  private selectedVoice: SpeechSynthesisVoice | null = null;
  private rate = 1.02;
  private pitch = 0.98;
  private volume = 1.0;
  private keepAliveTimer: any = null;

  constructor() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      this.synth = window.speechSynthesis;
      this._loadVoices();
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = () => this._loadVoices();
      }
    }
  }

  public _loadVoices(): SpeechSynthesisVoice[] {
    if (!this.synth) return [];
    const voices = this.synth.getVoices();
    if (!voices || voices.length === 0) return [];

    // Prioritize natural / British / sophisticated assistant voices
    const preferred = voices.find(v => 
      v.name.includes("Google UK English Male") || 
      v.name.includes("Microsoft George") ||
      v.name.includes("Daniel") || 
      v.name.includes("Natural") ||
      v.name.includes("Guy") ||
      (v.lang.startsWith("en") && (v.name.includes("Male") || v.name.includes("David")))
    );

    this.selectedVoice = preferred || voices.find(v => v.lang.startsWith("en")) || voices[0] || null;
    return voices;
  }

  public getAvailableVoices(): SpeechSynthesisVoice[] {
    if (!this.synth) return [];
    return this.synth.getVoices();
  }

  public setVoiceByName(voiceName: string) {
    if (!this.synth) return;
    const voices = this.synth.getVoices();
    const found = voices.find(v => v.name === voiceName);
    if (found) {
      this.selectedVoice = found;
    }
  }

  public getSelectedVoice(): SpeechSynthesisVoice | null {
    if (!this.selectedVoice) {
      this._loadVoices();
    }
    return this.selectedVoice;
  }

  public speak(
    text: string, 
    onStart?: () => void, 
    onEnd?: () => void,
    onError?: (err: any) => void
  ) {
    if (!this.synth) {
      if (onEnd) onEnd();
      return;
    }

    // 1. Instant Barge-In: Halt any previous speech immediately
    this.stop();

    // 2. Clean text of markdown, code blocks, URLs, brackets for human-like speech
    const cleanSpeech = text
      .replace(/```[\s\S]*?```/g, 'Code block omitted.')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/[*_#~]/g, '')
      .replace(/\[.*?\]\((.*?)\)/g, '$1')
      .replace(/\[.*?\]/g, '')
      .replace(/https?:\/\/\S+/g, 'link')
      .replace(/\{[\s\S]*?\}/g, '')
      .trim();

    if (!cleanSpeech) {
      if (onEnd) onEnd();
      return;
    }

    // Workaround for Chrome bug where speech pauses after 15s
    if (this.synth.paused) {
      this.synth.resume();
    }

    const utterance = new SpeechSynthesisUtterance(cleanSpeech);
    if (!this.selectedVoice) {
      this._loadVoices();
    }
    if (this.selectedVoice) {
      utterance.voice = this.selectedVoice;
    }

    utterance.rate = this.rate;
    utterance.pitch = this.pitch;
    utterance.volume = this.volume;

    utterance.onstart = () => {
      this.isSpeakingState = true;
      // Start keep-alive interval for long utterances in Chrome
      this._startKeepAlive();
      if (onStart) onStart();
    };

    utterance.onend = () => {
      this.isSpeakingState = false;
      this.currentUtterance = null;
      this._stopKeepAlive();
      if (onEnd) onEnd();
    };

    utterance.onerror = (e) => {
      console.warn("[TTS] Utterance event:", e.error);
      this.isSpeakingState = false;
      this.currentUtterance = null;
      this._stopKeepAlive();
      if (onError) onError(e);
      if (onEnd) onEnd();
    };

    this.currentUtterance = utterance;
    this.synth.speak(utterance);
  }

  private _startKeepAlive() {
    this._stopKeepAlive();
    this.keepAliveTimer = setInterval(() => {
      if (this.synth && this.synth.speaking) {
        this.synth.pause();
        this.synth.resume();
      } else {
        this._stopKeepAlive();
      }
    }, 10000);
  }

  private _stopKeepAlive() {
    if (this.keepAliveTimer) {
      clearInterval(this.keepAliveTimer);
      this.keepAliveTimer = null;
    }
  }

  // Instant Barge-In: immediately stop speaking
  public stop() {
    this._stopKeepAlive();
    if (this.synth) {
      this.synth.cancel();
    }
    this.isSpeakingState = false;
    this.currentUtterance = null;
  }

  public isSpeaking(): boolean {
    return this.isSpeakingState || (this.synth ? this.synth.speaking : false);
  }

  public setRate(val: number) {
    this.rate = val;
  }

  public setPitch(val: number) {
    this.pitch = val;
  }
}

export const ttsService = new TextToSpeechService();
