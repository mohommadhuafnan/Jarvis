/**
 * MongoDB Indexes Module (Node.js)
 * Creates essential indexes for query acceleration and constraint validation.
 */

const {
  getConversationsCollection,
  getMessagesCollection,
  getMemoriesCollection,
  getTasksCollection,
  getAgentRunsCollection,
  getAuditLogsCollection,
  getPreferencesCollection,
  getVoiceSessionsCollection,
  getUsersCollection,
} = require('./collections');

async function createAllIndexes() {
  try {
    // 1. Conversations
    const conv = await getConversationsCollection();
    if (conv) {
      await conv.createIndex({ conversationId: 1 }, { unique: true, sparse: true });
      await conv.createIndex({ userId: 1 });
      await conv.createIndex({ updatedAt: -1 });
    }

    // 2. Messages
    const msg = await getMessagesCollection();
    if (msg) {
      await msg.createIndex({ conversationId: 1, timestamp: 1 });
      await msg.createIndex({ timestamp: -1 });
    }

    // 3. Memories
    const mem = await getMemoriesCollection();
    if (mem) {
      await mem.createIndex({ userId: 1, key: 1 });
      await mem.createIndex({ type: 1 });
      await mem.createIndex({ updatedAt: -1 });
    }

    // 4. Tasks
    const tasks = await getTasksCollection();
    if (tasks) {
      await tasks.createIndex({ taskId: 1 }, { unique: true, sparse: true });
      await tasks.createIndex({ status: 1 });
      await tasks.createIndex({ updatedAt: -1 });
    }

    // 5. Agent Runs
    const agentRuns = await getAgentRunsCollection();
    if (agentRuns) {
      await agentRuns.createIndex({ taskId: 1 });
      await agentRuns.createIndex({ startedAt: -1 });
    }

    // 6. Audit Logs
    const audit = await getAuditLogsCollection();
    if (audit) {
      await audit.createIndex({ taskId: 1 });
      await audit.createIndex({ timestamp: -1 });
    }

    // 7. Preferences
    const prefs = await getPreferencesCollection();
    if (prefs) {
      await prefs.createIndex({ userId: 1, key: 1 }, { unique: true });
    }

    // 8. Voice Sessions
    const voice = await getVoiceSessionsCollection();
    if (voice) {
      await voice.createIndex({ sessionId: 1 }, { unique: true, sparse: true });
    }

    // 9. Users
    const users = await getUsersCollection();
    if (users) {
      await users.createIndex({ userId: 1 }, { unique: true, sparse: true });
    }

    console.log('[MongoDB Node] All indexes ensured successfully.');
    return true;
  } catch (err) {
    console.error('[MongoDB Node] Index creation error:', err.message);
    return false;
  }
}

module.exports = {
  createAllIndexes,
};
