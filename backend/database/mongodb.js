/**
 * Centralized MongoDB Connection Service (Official MongoDB Node.js Driver)
 * Manages singleton MongoClient, connection pooling, health checks, and graceful shutdown.
 */

const fs = require('fs');
const path = require('path');
const dns = require('dns');
try {
  dns.setServers(['8.8.8.8', '1.1.1.1', '8.8.4.4']);
} catch (_) {}
const { MongoClient, ServerApiVersion } = require('mongodb');

// Attempt dotenv if available, else parse .env directly
try {
  require('dotenv').config();
} catch (e) {
  try {
    const envPath = path.resolve(__dirname, '../../.env');
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, 'utf8');
      content.split('\n').forEach(line => {
        const match = line.match(/^\s*([\w_]+)\s*=\s*(.*)?\s*$/);
        if (match) {
          const key = match[1];
          let val = match[2] || '';
          if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
          if (val.startsWith("'") && val.endsWith("'")) val = val.slice(1, -1);
          if (!process.env[key]) process.env[key] = val.trim();
        }
      });
    }
  } catch (_) {}
}

const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DATABASE || 'jarvis';

let client = null;
let db = null;

/**
 * Connect to MongoDB and return client singleton.
 * Reuses connection pool across requests.
 */
async function getMongoClient() {
  if (client) {
    return client;
  }

  if (!uri) {
    console.warn('[MongoDB Node] MONGODB_URI environment variable is not defined.');
    return null;
  }

  try {
    client = new MongoClient(uri, {
      serverApi: {
        version: ServerApiVersion.v1,
        strict: false,
        deprecationErrors: true,
      },
      maxPoolSize: 50,
      minPoolSize: 5,
      connectTimeoutMS: 5000,
      socketTimeoutMS: 10000,
    });

    await client.connect();
    // Verify connection with admin ping
    await client.db('admin').command({ ping: 1 });
    console.log('[MongoDB Node] Connected successfully to MongoDB Atlas pool.');
    db = client.db(dbName);
    return client;
  } catch (err) {
    console.error('[MongoDB Node] Connection error:', err.message);
    client = null;
    db = null;
    return null;
  }
}

/**
 * Get active database instance.
 */
async function getDatabase() {
  if (db) return db;
  await getMongoClient();
  return db;
}

/**
 * Health check with live ping.
 */
async function checkDatabaseHealth() {
  if (!uri) {
    return { database: 'mongodb', status: 'unconfigured', error: 'MONGODB_URI not set' };
  }

  try {
    const c = await getMongoClient();
    if (!c) {
      return { database: 'mongodb', status: 'disconnected' };
    }
    const start = Date.now();
    await c.db('admin').command({ ping: 1 });
    const latency = Date.now() - start;
    return {
      database: 'mongodb',
      status: 'connected',
      database_name: dbName,
      latency_ms: latency,
    };
  } catch (err) {
    return { database: 'mongodb', status: 'error', error: err.message };
  }
}

/**
 * Graceful shutdown.
 */
async function closeMongoConnection() {
  if (client) {
    try {
      console.log('[MongoDB Node] Closing connection pool...');
      await client.close();
    } catch (err) {
      console.warn('[MongoDB Node] Error during close:', err.message);
    } finally {
      client = null;
      db = null;
    }
  }
}

module.exports = {
  getMongoClient,
  getDatabase,
  checkDatabaseHealth,
  closeMongoConnection,
};
