export type AssistantState = 'IDLE' | 'LISTENING' | 'THINKING' | 'EXECUTING' | 'SPEAKING' | 'ERROR';

export interface SystemTelemetry {
  cpu_usage: number;
  ram_usage: number;
  ram_used_gb: number;
  ram_total_gb: number;
  disk_percent: number;
  disk_free_gb: number;
  uptime: string;
  os: string;
  platform: string;
  status: string;
}

export interface ActivityLogItem {
  id: string;
  module: string;
  action: string;
  details?: string;
  status: 'success' | 'warning' | 'error';
  created_at: string;
}

export interface TaskItem {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'completed';
  deadline?: string;
  tags?: string;
  created_at: string;
  updated_at: string;
}

export interface CalendarEventItem {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  location?: string;
}

export interface EmailItem {
  id: string;
  sender: string;
  subject: string;
  snippet: string;
  date: string;
  unread: boolean;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface MemoryItem {
  id: string;
  category: string;
  key: string;
  value: string;
  tags?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceFile {
  name: string;
  path: string;
  size_bytes: number;
  modified: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_name?: string;
  tool_result?: any;
  action_plan?: string[];
  timestamp: string;
}

export interface TaskPlanStep {
  text: string;
  completed: boolean;
  current: boolean;
}

export interface CurrentTaskState {
  title: string;
  progressPercent: number;
  steps: TaskPlanStep[];
  statusText: string;
  toolName?: string;
}
