// Audio Context Manager with AnalyserNode for Real-time Reactive Waveforms & Spectrum
export class AudioContextManager {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private micStream: MediaStream | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private dataArray: Uint8Array | null = null;
  private isCapturing = false;

  async initMic(): Promise<boolean> {
    try {
      if (this.isCapturing && this.micStream) return true;

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioCtx();
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      this.micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      });

      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.8;

      this.sourceNode = this.audioContext.createMediaStreamSource(this.micStream);
      this.sourceNode.connect(this.analyser);

      const bufferLength = this.analyser.frequencyBinCount;
      this.dataArray = new Uint8Array(bufferLength);
      this.isCapturing = true;
      return true;
    } catch (err) {
      console.warn("[AudioContextManager] Mic permission error or unavailable:", err);
      this.isCapturing = false;
      return false;
    }
  }

  // Get real-time audio amplitude (0.0 to 1.0)
  getAudioLevel(): number {
    if (!this.analyser || !this.dataArray) return 0;
    (this.analyser as any).getByteFrequencyData(this.dataArray);
    let sum = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      sum += this.dataArray[i];
    }
    const avg = sum / this.dataArray.length;
    return Math.min(1, avg / 128);
  }

  // Get time-domain waveform data array for drawing SVG/Canvas waveforms
  getWaveformData(): Uint8Array {
    if (!this.analyser) return new Uint8Array(128).fill(128);
    const waveArray = new Uint8Array(this.analyser.fftSize);
    (this.analyser as any).getByteTimeDomainData(waveArray);
    return waveArray;
  }

  stopMic() {
    if (this.micStream) {
      this.micStream.getTracks().forEach((track) => track.stop());
      this.micStream = null;
    }
    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }
    this.isCapturing = false;
  }
}

export const audioManager = new AudioContextManager();
