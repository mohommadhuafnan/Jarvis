/**
 * MongoDB Collections Accessor Module (Node.js)
 * Defines collection names and getters for all 10 JARVIS database collections.
 */

const { getDatabase } = require('./mongodb');

const COLLECTIONS = {
  USERS: 'users',
  CONVERSATIONS: 'conversations',
  MESSAGES: 'messages',
  MEMORIES: 'memories',
  TASKS: 'tasks',
  AGENT_RUNS: 'agent_runs',
  TOOL_EXECUTIONS: 'tool_executions',
  VOICE_SESSIONS: 'voice_sessions',
  PREFERENCES: 'preferences',
  AUDIT_LOGS: 'audit_logs',
};

async function getCollection(name) {
  const db = await getDatabase();
  if (!db) return null;
  return db.collection(name);
}

module.exports = {
  COLLECTIONS,
  getUsersCollection: () => getCollection(COLLECTIONS.USERS),
  getConversationsCollection: () => getCollection(COLLECTIONS.CONVERSATIONS),
  getMessagesCollection: () => getCollection(COLLECTIONS.MESSAGES),
  getMemoriesCollection: () => getCollection(COLLECTIONS.MEMORIES),
  getTasksCollection: () => getCollection(COLLECTIONS.TASKS),
  getAgentRunsCollection: () => getCollection(COLLECTIONS.AGENT_RUNS),
  getToolExecutionsCollection: () => getCollection(COLLECTIONS.TOOL_EXECUTIONS),
  getVoiceSessionsCollection: () => getCollection(COLLECTIONS.VOICE_SESSIONS),
  getPreferencesCollection: () => getCollection(COLLECTIONS.PREFERENCES),
  getAuditLogsCollection: () => getCollection(COLLECTIONS.AUDIT_LOGS),
};
