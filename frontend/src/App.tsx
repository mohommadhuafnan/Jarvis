import React, { useState, useEffect, useRef } from 'react';
import { AssistantState, SystemTelemetry, ActivityLogItem, CurrentTaskState, ChatMessage } from './types';
import { NavTab, CyberSidebar } from './components/hud/CyberSidebar';
import { WindowHeader } from './components/hud/WindowHeader';
import { HudBackground } from './components/hud/HudBackground';
import { TaskWorkspace } from './components/hud/TaskWorkspace';
import { PermissionModal } from './components/hud/PermissionModal';

// Views
import { DashboardView } from './components/views/DashboardView';
import { ChatWorkspaceView } from './components/views/ChatWorkspaceView';
import { TasksView } from './components/views/TasksView';
import { CalendarView } from './components/views/CalendarView';
import { EmailView } from './components/views/EmailView';
import { CodeAssistantView } from './components/views/CodeAssistantView';
import { FilesSystemView } from './components/views/FilesSystemView';
import { AutomationView } from './components/views/AutomationView';
import { MemoryVaultView } from './components/views/MemoryVaultView';
import { SettingsView } from './components/views/SettingsView';

// Audio & Voice Services
import { audioManager } from './lib/voice/AudioContextManager';
import { speechEngine, VoiceMode } from './lib/voice/SpeechToText';
import { geminiVoiceService } from './lib/voice/GeminiVoiceService';
import { livekitVoiceManager, LiveKitVoiceState } from './lib/voice/LiveKitVoiceManager';
import { soundFX } from './lib/sound/SoundFX';
import { fetchSystemStats, sendChatMessage, processVoiceGatewayTurn, interruptVoiceGateway, fetchVoiceTelemetry, fetchDueReminders, fetchLiveKitStatus } from './lib/api';


export function App() {
  // State Machine
  const [state, setState] = useState<AssistantState>('IDLE');
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [continuousConversation, setContinuousConversation] = useState<boolean>(true);

  // Command & Action status displayed in HUD
  const [currentCommand, setCurrentCommand] = useState<string>("Say 'Jarvis hello' or tap mic to speak");
  const [actionStatus, setActionStatus] = useState<string>("Standby — Voice Engine Online");
  const [currentTool, setCurrentTool] = useState<string | null>(null);

  // Telemetry & Logs
  const [telemetry, setTelemetry] = useState<SystemTelemetry | undefined>();
  const [voiceTelemetry, setVoiceTelemetry] = useState<any>({
    stt_latency_ms: 18.4,
    gemini_latency_ms: 82.5,
    agent_latency_ms: 45.0,
    tts_latency_ms: 22.0,
    total_latency_ms: 167.9,
    state: 'IDLE'
  });
  const [userName, setUserName] = useState<string>("Sir");
  const [activityLogs, setActivityLogs] = useState<ActivityLogItem[]>([
    { id: "act_1", module: "System", action: "JARVIS AI Voice Core v2.5.1 Online", details: "Direct 2-way speech channel active", status: "success", created_at: "Ready" },
    { id: "act_2", module: "Neural Core", action: "Gemini AI Connected", details: "Instant multi-modal reasoning", status: "success", created_at: "Online" },
  ]);

  // Current Task Execution State
  const [currentTask, setCurrentTask] = useState<CurrentTaskState>({
    title: "Direct Voice Communication Channel",
    progressPercent: 100,
    steps: [
      { text: "Speech Recognition Engine", completed: true, current: false },
      { text: "Gemini Neural Core", completed: true, current: false },
      { text: "High-Fidelity Voice Synthesis", completed: true, current: false },
      { text: "Barge-In Interruption Handler", completed: true, current: false },
    ],
    statusText: "Ready for conversation."
  });

  // Chat conversation messages
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "msg_init",
      role: "assistant",
      content: "JARVIS AI Command Center online. I am listening, Commander. How can I help you?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  // Permission Modal
  const [permissionModalOpen, setPermissionModalOpen] = useState(false);
  const [pendingToolAction, setPendingToolAction] = useState<any>(null);

  const audioAnimRef = useRef<number | null>(null);
  const replyTimeoutRef = useRef<any>(null);
  // LiveKit Cloud Connection State
  const [isLiveKitConnected, setIsLiveKitConnected] = useState<boolean>(false);

  // 1. Initial System Data & Polling
  useEffect(() => {
    const loadStats = async () => {
      const data = await fetchSystemStats();
      if (data.telemetry) setTelemetry(data.telemetry);
      if (data.user_name) setUserName(data.user_name);
      if (data.logs && data.logs.length > 0) setActivityLogs(data.logs);
      if (data.voice_telemetry) setVoiceTelemetry(data.voice_telemetry);
    };

    loadStats();
    const interval = setInterval(loadStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // 2. LiveKit Realtime Voice Manager Setup & Event Subscriptions
  useEffect(() => {
    livekitVoiceManager.setCallbacks({
      onStateChange: (lkState: LiveKitVoiceState) => {
        if (lkState === 'CONNECTED' || lkState === 'LISTENING') {
          setIsLiveKitConnected(true);
          setState('LISTENING');
          setIsListening(true);
          setActionStatus('LiveKit WebRTC: Listening to speech (Hands-Free)...');
          setCurrentCommand('Listening...');
        } else if (lkState === 'THINKING') {
          setIsLiveKitConnected(true);
          setState('THINKING');
          setIsListening(false);
          setActionStatus('Gemini Live: Realtime neural reasoning & tool execution...');
        } else if (lkState === 'SPEAKING') {
          setIsLiveKitConnected(true);
          setState('SPEAKING');
          setIsListening(false);
          setActionStatus('JARVIS speaking (Barge-In active)...');
        } else if (lkState === 'DISCONNECTED') {
          setIsLiveKitConnected(false);
          setState('IDLE');
          setIsListening(false);
          setActionStatus('Standby (LiveKit Cloud Ready)');
          setCurrentCommand("Say 'Jarvis' or tap mic to speak");
        } else if (lkState === 'ERROR') {
          setIsLiveKitConnected(false);
          setState('ERROR');
          setIsListening(false);
          soundFX.playErrorBuzz();
          setActionStatus('LiveKit WebRTC Connection Error');
          setTimeout(() => setState('IDLE'), 3000);
        }
      },
      onAudioLevel: (level: number) => {
        setAudioLevel(level);
      },
      onTranscript: (transcript: string, isUser: boolean) => {
        const clean = transcript.trim();
        if (!clean) return;

        setCurrentCommand(clean);
        const msg: ChatMessage = {
          id: `lk_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
          role: isUser ? 'user' : 'assistant',
          content: clean,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setChatMessages(prev => [...prev, msg]);
      },
      onToolAction: (toolName: string, status: string) => {
        setCurrentTool(toolName);
        if (status === 'executing') {
          setState('EXECUTING');
          setActionStatus(`Executing ${toolName}...`);
        } else {
          setActionStatus(`Completed ${toolName}`);
          const newLog: ActivityLogItem = {
            id: `act_${Date.now()}`,
            module: toolName.split('.')[0].toUpperCase(),
            action: `Executed ${toolName}`,
            details: `Completed successfully`,
            status: 'success',
            created_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          setActivityLogs(prev => [newLog, ...prev]);
        }
      },
      onError: (errorMsg: string) => {
        console.error("[JARVIS LiveKit] Voice error:", errorMsg);
        setActionStatus(`LiveKit Error: ${errorMsg}`);
      }
    });

    return () => {
      livekitVoiceManager.disconnect();
    };
  }, []);

  // 2. Continuous Audio Amplitude Monitoring
  useEffect(() => {
    const monitorAudio = () => {
      const micLevel = audioManager.getAudioLevel();
      // If speaking via Voice TTS, generate reactive waveform pulsation
      if (geminiVoiceService.isSpeaking()) {
        const ttsLevel = 0.35 + Math.random() * 0.5;
        setAudioLevel(ttsLevel);
      } else {
        setAudioLevel(micLevel);
      }
      audioAnimRef.current = requestAnimationFrame(monitorAudio);
    };

    audioAnimRef.current = requestAnimationFrame(monitorAudio);
    return () => {
      if (audioAnimRef.current) cancelAnimationFrame(audioAnimRef.current);
    };
  }, []);

  // 3. Master Speech Engine Lifecycle & Callbacks (Always-Ready Hands-Free)
  useEffect(() => {
    // Automatically initialize mic stream for visualizer and speech
    audioManager.initMic().catch((err) => {
      console.warn("[JARVIS Voice] Mic auto-init waiting for permission:", err);
    });

    speechEngine.setCallbacks({
      onWakeWord: (word, followUpCommand) => {
        soundFX.playWakeChime();
        if (followUpCommand && followUpCommand.trim().length > 1) {
          handleExecuteCommand(followUpCommand.trim());
        } else {
          // User said "Hello Jarvis" or "Jarvis" -> Speak greeting and enter hands-free listening
          handleGreetingAndListen();
        }
      },
      onSpeechDetected: () => {
        // Instant Barge-In on any detected speech while speaking
        if (geminiVoiceService.isSpeaking()) {
          geminiVoiceService.stop();
          interruptVoiceGateway().catch(() => {});
          setState('LISTENING');
          setIsListening(true);
          setActionStatus('Listening...');
        }
      },
      onInterim: (interimText) => {
        setCurrentCommand(interimText);
        if (geminiVoiceService.isSpeaking()) {
          geminiVoiceService.stop();
          interruptVoiceGateway().catch(() => {});
        }
      },
      onFinal: (finalText) => {
        if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current);
        const clean = finalText.trim();
        if (clean) {
          handleExecuteCommand(clean);
        } else {
          setState('IDLE');
          setActionStatus('Standby (Listening for "Jarvis")');
          speechEngine.setMode('WAKE_WORD');
        }
      },
      onStateChange: (mode: VoiceMode) => {
        setIsListening(mode === 'COMMAND' || mode === 'CONVERSATION');
      }
    });

    // Start in Always-Ready Wake Word listening mode
    speechEngine.setMode('WAKE_WORD');
    speechEngine.start();

    return () => {
      speechEngine.stop();
      if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current);
    };
  }, [continuousConversation, userName]);

  // Background Reminder Notification Daemon Listener (Fires without button clicks)
  useEffect(() => {
    const reminderInterval = setInterval(async () => {
      try {
        const res = await fetchDueReminders();
        if (res.due_reminders && res.due_reminders.length > 0) {
          for (const rem of res.due_reminders) {
            const spokenText = rem.spoken_notification || `Boss, this is your reminder. You have your ${rem.title} scheduled for ${rem.reminder_time}.`;
            soundFX.playAlertTone();
            
            // Add notification to HUD chat
            const reminderChatMsg: ChatMessage = {
              id: `rem_${Date.now()}_${rem.id}`,
              role: 'assistant',
              content: `🔔 **SCHEDULED REMINDER:** ${spokenText}`,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setChatMessages(prev => [...prev, reminderChatMsg]);

            // Speak reminder automatically out loud
            setState('SPEAKING');
            setActionStatus(`Alert: Reminder for ${rem.title}`);
            geminiVoiceService.speak(
              spokenText,
              () => {
                setState('SPEAKING');
              },
              () => {
                // When reminder finishes speaking -> open hands-free listening window
                setState('LISTENING');
                setIsListening(true);
                setActionStatus('Listening for follow-up (Hands-Free)...');
                speechEngine.resumeRecognition();
                speechEngine.setMode('COMMAND');
                if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current);
                replyTimeoutRef.current = setTimeout(() => {
                  setState('IDLE');
                  setIsListening(false);
                  setActionStatus('Standby (Say "Jarvis" to wake)');
                  speechEngine.setMode('WAKE_WORD');
                }, 8000);
              }
            );
          }
        }
      } catch (e) {
        // Backend offline
      }
    }, 3000);

    return () => clearInterval(reminderInterval);
  }, []);

  // Voice Interaction Functions
  const handleGreetingAndListen = () => {
    if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current);
    geminiVoiceService.stop();
    interruptVoiceGateway().catch(() => {});

    const greeting = `Hello, Boss. How can I help you?`;
    
    // Add to chat
    const aiMsg: ChatMessage = {
      id: `ai_${Date.now()}`,
      role: 'assistant',
      content: greeting,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, aiMsg]);

    setState('SPEAKING');
    setActionStatus('Speaking greeting...');
    setCurrentCommand('Hello Jarvis');

    geminiVoiceService.speak(
      greeting,
      () => {
        setState('SPEAKING');
        setActionStatus('Speaking greeting...');
      },
      () => {
        // When greeting finishes speaking -> Enter active hands-free listening loop
        setState('LISTENING');
        setIsListening(true);
        setActionStatus('Listening for your command (Hands-Free)...');
        setCurrentCommand('Listening...');
        speechEngine.resumeRecognition();
        speechEngine.setMode('COMMAND');

        // Allow 10 seconds of listening window before returning to standby
        replyTimeoutRef.current = setTimeout(() => {
          setState('IDLE');
          setIsListening(false);
          setActionStatus('Standby (Say "Jarvis" to wake)');
          speechEngine.setMode('WAKE_WORD');
        }, 10000);
      },
      () => {
        setState('LISTENING');
        setIsListening(true);
        speechEngine.resumeRecognition();
        speechEngine.setMode('COMMAND');
      }
    );
  };

  const startCommandListening = async () => {
    if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current);

    if (geminiVoiceService.isSpeaking()) {
      geminiVoiceService.stop();
      interruptVoiceGateway().catch(() => {});
    }

    await audioManager.initMic();
    setIsListening(true);
    setState('LISTENING');
    setActionStatus('Listening to your voice command...');
    setCurrentCommand('Listening...');

    speechEngine.setMode('COMMAND');
    speechEngine.start();
  };

  const stopVoiceListening = () => {
    if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current);
    setIsListening(false);
    speechEngine.setMode('WAKE_WORD');
    setState('IDLE');
    setActionStatus('Standby (Say "Jarvis" to wake)');
  };

  const toggleMic = async () => {
    // 1. If currently connected to LiveKit WebRTC session -> disconnect
    if (livekitVoiceManager.isConnected()) {
      soundFX.playClick();
      await livekitVoiceManager.disconnect();
      stopVoiceListening();
      return;
    }

    // 2. Stop any active TTS audio
    if (geminiVoiceService.isSpeaking()) {
      geminiVoiceService.stop();
      interruptVoiceGateway().catch(() => {});
    }

    // 3. Connect to LiveKit Cloud Realtime Voice
    soundFX.playWakeChime();
    setActionStatus('Connecting to LiveKit Cloud & Gemini Live...');
    setState('THINKING');

    const connected = await livekitVoiceManager.connect('jarvis-room-default', userName);
    if (!connected) {
      // If LiveKit is temporarily unreachable, fallback to client-side STT
      console.warn('[JARVIS] Falling back to Web Speech engine...');
      startCommandListening();
    }
  };

  // Main Command & AI Dispatcher
  const handleExecuteCommand = async (commandText: string) => {
    if (!commandText || !commandText.trim()) return;

    if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current);

    const lowerCmd = commandText.toLowerCase().trim();

    // Emergency Stop Intercept
    if (["stop", "jarvis stop", "stop jarvis", "halt", "emergency stop", "abort"].includes(lowerCmd)) {
      geminiVoiceService.stop();
      interruptVoiceGateway().catch(() => {});
      fetch('/api/kernel/stop', { method: 'POST' }).catch(() => {});
      soundFX.playProcessingBeep();
      setState('IDLE');
      setIsListening(false);
      setIsProcessing(false);
      setActionStatus('Emergency Stop: All tasks halted.');
      setCurrentCommand('Emergency Stop');
      speechEngine.setMode('WAKE_WORD');
      speechEngine.resumeRecognition();
      return;
    }

    // Stop speaking if in progress
    geminiVoiceService.stop();
    interruptVoiceGateway().catch(() => {});
    speechEngine.pauseRecognition();

    setCurrentCommand(commandText);
    setIsProcessing(true);
    setIsListening(false);
    setState('THINKING');
    setActionStatus('Voice Gateway: Neural processing & intent resolution...');
    soundFX.playProcessingBeep();

    // Append user message to chat history
    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: commandText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, userMsg]);

    // Update Current Task workspace card
    const rawSteps = [
      `Processing: "${commandText.slice(0, 32)}..."`,
      "Evaluating neural tools",
      "Executing routine",
      "Synthesizing voice response"
    ];

    setCurrentTask({
      title: commandText,
      progressPercent: 30,
      steps: rawSteps.map((s, i) => ({ text: s, completed: i === 0, current: i === 1 })),
      statusText: "Processing query..."
    });

    try {
      // Step 1: Query Voice Gateway Backend
      const response = await processVoiceGatewayTurn(commandText);
      const tool = response.tool_used;

      if (response.telemetry) {
        setVoiceTelemetry(response.telemetry.latencies ? { ...response.telemetry.latencies, state: 'SPEAKING' } : response.telemetry);
      }

      if (tool) {
        setCurrentTool(tool);
        setState('EXECUTING');
        setActionStatus(`Executing ${tool}...`);

        setCurrentTask(prev => ({
          ...prev,
          progressPercent: 70,
          steps: prev.steps.map((s, i) => ({
            ...s,
            completed: i <= 1,
            current: i === 2
          })),
          statusText: `Executed ${tool}`
        }));

        // Log to activity feed
        const newLog: ActivityLogItem = {
          id: `act_${Date.now()}`,
          module: tool.split('.')[0].toUpperCase(),
          action: `Executed ${tool}`,
          details: typeof response.tool_result === 'string' ? response.tool_result : "Completed successfully",
          status: 'success',
          created_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setActivityLogs(prev => [newLog, ...prev]);

        await new Promise(r => setTimeout(r, 400));
      }

      // Step 2: Transition to SPEAKING state
      setState('SPEAKING');
      setActionStatus('Speaking response...');
      setCurrentTask(prev => ({
        ...prev,
        progressPercent: 100,
        steps: prev.steps.map(s => ({ ...s, completed: true, current: false })),
        statusText: "Task completed."
      }));

      const replyText = response.reply || "Command processed.";

      // Add AI reply to chat
      const aiMsg: ChatMessage = {
        id: `ai_${Date.now()}`,
        role: 'assistant',
        content: replyText,
        tool_name: tool,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, aiMsg]);

      // Step 3: Speak response using instant high-fidelity TTS
      geminiVoiceService.speak(
        replyText,
        () => {
          setState('SPEAKING');
          setActionStatus('Speaking response...');
        },
        () => {
          // When speech completes
          setCurrentTool(null);

          if (continuousConversation) {
            // Hands-Free Loop: Stay in listening mode for follow-up
            setState('LISTENING');
            setIsListening(true);
            setActionStatus('Listening for your reply (Hands-Free)...');
            setCurrentCommand('Listening for reply...');
            speechEngine.resumeRecognition();
            speechEngine.setMode('COMMAND');

            // If no user reply within 8 seconds, return to Standby
            replyTimeoutRef.current = setTimeout(() => {
              setState('IDLE');
              setIsListening(false);
              setActionStatus('Standby (Say "Jarvis" or tap mic)');
              speechEngine.setMode('WAKE_WORD');
            }, 8000);
          } else {
            // Wake Word mode: Return to standby
            setState('IDLE');
            setIsListening(false);
            setActionStatus('Standby (Say "Jarvis" or tap mic)');
            speechEngine.resumeRecognition();
            speechEngine.setMode('WAKE_WORD');
          }
        },
        (err) => {
          console.warn("[Voice] Speech error:", err);
          setState('IDLE');
          setIsListening(false);
          speechEngine.resumeRecognition();
          speechEngine.setMode('WAKE_WORD');
        }
      );

    } catch (err) {
      console.error("[JARVIS] Command error:", err);
      soundFX.playErrorBuzz();
      setState('ERROR');
      setActionStatus('System execution error.');
      speechEngine.resumeRecognition();
      speechEngine.setMode('WAKE_WORD');
      setTimeout(() => setState('IDLE'), 2500);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#050508] text-[#F5F5F5] font-sans overflow-hidden relative select-none">
      {/* Top Window Bar */}
      <WindowHeader status={activeTab.toUpperCase()} />

      {/* Cyberpunk HUD Animated Background */}
      <HudBackground />

      {/* Main Body Layout: Left Sidebar + Center View + Right Workspace */}
      <div className="flex-1 flex overflow-hidden relative z-10">
        {/* Left HUD Navigation & Telemetry Sidebar */}
        <CyberSidebar 
          activeTab={activeTab} 
          onSelectTab={setActiveTab} 
          telemetry={telemetry} 
        />

        {/* Center Main View Switcher */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative">
          {activeTab === 'dashboard' && (
            <DashboardView 
              state={state}
              audioLevel={audioLevel}
              isListening={isListening}
              currentCommand={currentCommand}
              actionStatus={actionStatus}
              currentTool={currentTool}
              userName={userName}
              telemetry={telemetry}
              voiceTelemetry={voiceTelemetry}
              onToggleMic={toggleMic}
              onSendMessage={handleExecuteCommand}
              isProcessing={isProcessing}
              continuousConversation={continuousConversation}
              onToggleContinuousConversation={() => setContinuousConversation(!continuousConversation)}
              isLiveKitConnected={isLiveKitConnected}
            />
          )}


          {activeTab === 'chat' && (
            <ChatWorkspaceView 
              messages={chatMessages}
              onSendMessage={handleExecuteCommand}
              isProcessing={isProcessing}
            />
          )}

          {activeTab === 'tasks' && <TasksView />}
          {activeTab === 'calendar' && <CalendarView />}
          {activeTab === 'email' && <EmailView />}
          {activeTab === 'code' && <CodeAssistantView />}
          {activeTab === 'files' && <FilesSystemView />}
          {activeTab === 'automation' && <AutomationView />}
          {activeTab === 'memory' && <MemoryVaultView />}
          {activeTab === 'settings' && (
            <SettingsView 
              onTestVoice={() => handleExecuteCommand("Hello Commander, I am JARVIS. All voice channels and neural cores are online.")}
            />
          )}
        </main>

        {/* Right Task & Activity Panel (Shown on Dashboard) */}
        {activeTab === 'dashboard' && (
          <TaskWorkspace 
            currentTask={currentTask}
            activityLogs={activityLogs}
            chatMessages={chatMessages}
            onClearLogs={() => setActivityLogs([])}
          />
        )}
      </div>

      {/* High-Risk Action Permission Modal */}
      <PermissionModal
        isOpen={permissionModalOpen}
        toolName={pendingToolAction?.toolName || 'System Command'}
        actionDescription={pendingToolAction?.description || 'Confirm execution'}
        details={pendingToolAction?.details}
        onConfirm={() => {
          setPermissionModalOpen(false);
          if (pendingToolAction?.onConfirm) pendingToolAction.onConfirm();
        }}
        onCancel={() => {
          setPermissionModalOpen(false);
          setState('IDLE');
        }}
      />
    </div>
  );
}

export default App;
