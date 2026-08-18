/**
 * High-Speed Voice Service for JARVIS
 * Combines zero-latency crystal-clear local speech synthesis with instant barge-in support.
 */
import { ttsService } from './TextToSpeech';

export interface GeminiVoiceOptions {
  voice?: string;
  rate?: number;
  pitch?: number;
}

class GeminiVoiceService {
  private selectedVoice: string = "Puck";

  public setVoice(voice: string) {
    this.selectedVoice = voice;
    ttsService.setVoiceByName(voice);
  }

  public getVoice(): string {
    return this.selectedVoice;
  }

  public async speak(
    text: string,
    onStart?: () => void,
    onEnd?: () => void,
    onError?: (err: any) => void
  ): Promise<void> {
    // Direct zero-latency voice synthesis
    ttsService.speak(text, onStart, onEnd, onError);
  }

  public stop(): void {
    ttsService.stop();
  }

  public isSpeaking(): boolean {
    return ttsService.isSpeaking();
  }

  public setRate(rate: number) {
    ttsService.setRate(rate);
  }

  public setPitch(pitch: number) {
    ttsService.setPitch(pitch);
  }
}

export const geminiVoiceService = new GeminiVoiceService();
