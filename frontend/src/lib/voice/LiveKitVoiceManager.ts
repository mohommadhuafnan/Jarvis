/**
 * LiveKit Realtime Voice Transport Manager for JARVIS
 * Connects frontend directly to LiveKit Cloud WebRTC room.
 * Handles microphone capture, audio playback, barge-in,
 * amplitude analysis for reactor orb, and real-time state synchronization.
 */

import {
  Room,
  RoomEvent,
  Track,
  RemoteTrackPublication,
  RemoteParticipant,
  ConnectionState,
  createLocalAudioTrack,
  LocalAudioTrack,
} from 'livekit-client';
import { fetchLiveKitToken, fetchLiveKitStatus } from '../api';

export type LiveKitVoiceState = 'DISCONNECTED' | 'CONNECTING' | 'CONNECTED' | 'LISTENING' | 'THINKING' | 'SPEAKING' | 'ERROR';

export interface LiveKitCallbacks {
  onStateChange?: (state: LiveKitVoiceState) => void;
  onAudioLevel?: (level: number) => void;
  onTranscript?: (transcript: string, isUser: boolean) => void;
  onToolAction?: (toolName: string, status: string) => void;
  onError?: (errorMsg: string) => void;
}

export class LiveKitVoiceManager {
  private room: Room | null = null;
  private localAudioTrack: LocalAudioTrack | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioLevelAnimId: number | null = null;
  private state: LiveKitVoiceState = 'DISCONNECTED';
  private callbacks: LiveKitCallbacks = {};
  private audioElement: HTMLAudioElement | null = null;
  private isMuted: boolean = false;

  constructor() {
    // Hidden persistent audio element for WebRTC playback
    if (typeof window !== 'undefined') {
      this.audioElement = document.createElement('audio');
      this.audioElement.autoplay = true;
      this.audioElement.style.display = 'none';
      document.body.appendChild(this.audioElement);
    }
  }

  public setCallbacks(callbacks: LiveKitCallbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  public getState(): LiveKitVoiceState {
    return this.state;
  }

  public isConnected(): boolean {
    return this.state === 'CONNECTED' || this.state === 'LISTENING' || this.state === 'THINKING' || this.state === 'SPEAKING';
  }

  private _setState(newState: LiveKitVoiceState) {
    this.state = newState;
    if (this.callbacks.onStateChange) {
      this.callbacks.onStateChange(newState);
    }
  }

  /**
   * Connect to LiveKit Cloud Room using short-lived backend token.
   */
  public async connect(roomName = "jarvis-room-default", userName = "RAVIT"): Promise<boolean> {
    if (this.isConnected() || this.state === 'CONNECTING') {
      return true;
    }

    try {
      this._setState('CONNECTING');

      // 1. Fetch short-lived token from backend
      const tokenRes = await fetchLiveKitToken(roomName, undefined, userName);
      if (!tokenRes.success || !tokenRes.token || !tokenRes.server_url) {
        throw new Error(tokenRes.error || "Failed to retrieve secure LiveKit token.");
      }

      // 2. Initialize Room
      this.room = new Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
          autoGainControl: true,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // 3. Register Room Event Handlers
      this._setupRoomEvents();

      // 4. Connect to WebRTC Room
      await this.room.connect(tokenRes.server_url, tokenRes.token);
      console.log(`[JARVIS LiveKit] Connected to room: ${roomName}`);

      // 5. Publish Local Microphone Track
      this.localAudioTrack = await createLocalAudioTrack({
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      });

      await this.room.localParticipant.publishTrack(this.localAudioTrack);
      this._setupAudioAnalyser(this.localAudioTrack.mediaStreamTrack);

      this._setState('LISTENING');
      return true;

    } catch (err: any) {
      console.error("[JARVIS LiveKit] Connection error:", err);
      this._setState('ERROR');
      if (this.callbacks.onError) {
        this.callbacks.onError(err.message || "Failed to establish LiveKit WebRTC connection");
      }
      this.disconnect();
      return false;
    }
  }

  private _setupRoomEvents() {
    if (!this.room) return;

    // Track Subscribed (Remote JARVIS audio)
    this.room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      if (track.kind === Track.Kind.Audio) {
        console.log("[JARVIS LiveKit] Subscribed to Agent Audio Track from", participant.identity);
        if (this.audioElement) {
          track.attach(this.audioElement);
        }
        this._setupAudioAnalyser(track.mediaStreamTrack);
        this._setState('SPEAKING');
      }
    });

    // Track Unsubscribed
    this.room.on(RoomEvent.TrackUnsubscribed, (track) => {
      if (track.kind === Track.Kind.Audio) {
        if (this.audioElement) {
          track.detach(this.audioElement);
        }
        if (this.isConnected()) {
          this._setState('LISTENING');
        }
      }
    });

    // Active Speaker Updates
    this.room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
      const isAgentSpeaking = speakers.some(s => !(s instanceof this.room!.localParticipant.constructor));
      const isUserSpeaking = speakers.some(s => s === this.room!.localParticipant);

      if (isAgentSpeaking) {
        this._setState('SPEAKING');
      } else if (isUserSpeaking) {
        this._setState('LISTENING');
      }
    });

    // Data Channel Messages (Transcripts, Tool events)
    this.room.on(RoomEvent.DataReceived, (payload: Uint8Array, participant) => {
      try {
        const text = new TextDecoder().decode(payload);
        const data = JSON.parse(text);

        if (data.type === 'TRANSCRIPT' && this.callbacks.onTranscript) {
          this.callbacks.onTranscript(data.text, data.is_user || false);
        } else if (data.type === 'TOOL_CALL' && this.callbacks.onToolAction) {
          this.callbacks.onToolAction(data.tool, data.status || 'executing');
          if (data.status === 'executing') {
            this._setState('THINKING');
          }
        } else if (data.type === 'STATE_CHANGE') {
          if (data.state) this._setState(data.state);
        }
      } catch (e) {
        // Plain text message
        const text = new TextDecoder().decode(payload);
        if (this.callbacks.onTranscript) {
          this.callbacks.onTranscript(text, false);
        }
      }
    });

    // Connection State Changes
    this.room.on(RoomEvent.ConnectionStateChanged, (state) => {
      if (state === ConnectionState.Disconnected) {
        this._setState('DISCONNECTED');
      } else if (state === ConnectionState.Reconnecting) {
        this._setState('CONNECTING');
      }
    });

    this.room.on(RoomEvent.Disconnected, () => {
      this._setState('DISCONNECTED');
      this._stopAudioLevelMonitoring();
    });
  }

  private _setupAudioAnalyser(mediaStreamTrack: MediaStreamTrack) {
    try {
      if (!this.audioContext) {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        this.audioContext = new AudioContextClass();
      }

      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }

      const stream = new MediaStream([mediaStreamTrack]);
      const source = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 128;
      this.analyser.smoothingTimeConstant = 0.8;
      source.connect(this.analyser);

      this._startAudioLevelMonitoring();
    } catch (e) {
      console.warn("[JARVIS LiveKit] Analyser setup skipped:", e);
    }
  }

  private _startAudioLevelMonitoring() {
    this._stopAudioLevelMonitoring();
    const dataArray = new Uint8Array(this.analyser ? this.analyser.frequencyBinCount : 32);

    const checkLevel = () => {
      if (this.analyser) {
        this.analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        const normalized = Math.min(1.0, avg / 128.0);
        if (this.callbacks.onAudioLevel) {
          this.callbacks.onAudioLevel(normalized);
        }
      }
      this.audioLevelAnimId = requestAnimationFrame(checkLevel);
    };

    this.audioLevelAnimId = requestAnimationFrame(checkLevel);
  }

  private _stopAudioLevelMonitoring() {
    if (this.audioLevelAnimId) {
      cancelAnimationFrame(this.audioLevelAnimId);
      this.audioLevelAnimId = null;
    }
  }

  /**
   * Mute / Unmute microphone track.
   */
  public toggleMute(): boolean {
    if (this.localAudioTrack) {
      if (this.isMuted) {
        this.localAudioTrack.unmute();
        this.isMuted = false;
      } else {
        this.localAudioTrack.mute();
        this.isMuted = true;
      }
    }
    return this.isMuted;
  }

  /**
   * Disconnect from LiveKit Room cleanly.
   */
  public async disconnect() {
    this._stopAudioLevelMonitoring();

    if (this.localAudioTrack) {
      this.localAudioTrack.stop();
      this.localAudioTrack = null;
    }

    if (this.room) {
      try {
        await this.room.disconnect();
      } catch (e) {}
      this.room = null;
    }

    if (this.audioElement) {
      this.audioElement.srcObject = null;
    }

    this._setState('DISCONNECTED');
    if (this.callbacks.onAudioLevel) {
      this.callbacks.onAudioLevel(0);
    }
    console.log("[JARVIS LiveKit] Disconnected from room.");
  }
}

export const livekitVoiceManager = new LiveKitVoiceManager();
