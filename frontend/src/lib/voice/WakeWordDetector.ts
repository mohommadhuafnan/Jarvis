// Proxy to unified speech engine to prevent multiple SpeechRecognition collisions
import { speechEngine } from './SpeechToText';

export class WakeWordDetector {
  public start(onWakeWord: (detectedWord: string, followUpCommand?: string) => void) {
    speechEngine.setCallbacks({
      onWakeWord: (word, cmd) => {
        onWakeWord(word, cmd);
      }
    });
    speechEngine.setMode('WAKE_WORD');
    speechEngine.start();
  }

  public stop() {
    speechEngine.stop();
  }

  public setWakeWord(word: string) {
    speechEngine.setWakeWord(word);
  }
}

export const wakeWordDetector = new WakeWordDetector();
