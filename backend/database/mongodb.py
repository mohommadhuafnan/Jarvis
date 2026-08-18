import logging
import time
from typing import Optional, Dict, Any
import dns.resolver
import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError
from backend.config import MONGODB_URI, MONGODB_DATABASE, mask_secret

logger = logging.getLogger("JARVIS.Database.MongoDB")

# Global singleton client instance
_mongo_client: Optional[MongoClient] = None
_db_instance: Optional[Database] = None

# Configure DNS resolver with reliable public fallbacks to ensure SRV resolution on all platforms
try:
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
except Exception as e:
    logger.warning(f"Failed to configure custom DNS resolver: {e}")

# Failure cooldown to prevent blocking requests when cluster is unreachable
_last_failure_time: float = 0.0
_COOLDOWN_SECONDS: float = 30.0

def get_mongo_client(uri: Optional[str] = None, timeout_ms: int = 2500) -> Optional[MongoClient]:
    """
    Get or create the singleton MongoClient instance.
    Reuses connection pool across requests.
    """
    global _mongo_client, _last_failure_time
    if _mongo_client is not None:
        return _mongo_client

    # If recent connection attempt failed, respect cooldown
    if time.time() - _last_failure_time < _COOLDOWN_SECONDS:
        return None

    target_uri = uri or MONGODB_URI
    if not target_uri:
        logger.warning("No MONGODB_URI provided. MongoDB client not initialized.")
        return None

    try:
        masked = mask_secret(target_uri, show_chars=12)
        logger.info(f"Connecting to MongoDB cluster: {masked}")
        
        # Configure client with connection pooling and fast server selection timeout
        client = MongoClient(
            target_uri,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=2500,
            socketTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=5,
            retryWrites=True,
            retryReads=True,
            appname="JARVIS-AI-OperatingSystem"
        )
        
        # Verify connection immediately with a lightweight ping
        client.admin.command("ping")
        _mongo_client = client
        logger.info("MongoDB connection successfully established and verified.")
        return _mongo_client
    except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as err:
        _last_failure_time = time.time()
        logger.error(f"MongoDB connection failed: {err}")
        return None
    except Exception as ex:
        _last_failure_time = time.time()
        logger.error(f"Unexpected error during MongoDB initialization: {ex}")
        return None

def get_database(db_name: Optional[str] = None) -> Optional[Database]:
    """
    Get the active JARVIS MongoDB Database instance.
    """
    global _db_instance
    if _db_instance is not None:
        return _db_instance

    client = get_mongo_client()
    if client is None:
        return None

    target_db = db_name or MONGODB_DATABASE or "jarvis"
    _db_instance = client[target_db]
    return _db_instance

def check_db_health() -> Dict[str, Any]:
    """
    Perform a real live health check against MongoDB using an admin ping command.
    """
    if not MONGODB_URI:
        return {
            "database": "mongodb",
            "status": "unconfigured",
            "error": "MONGODB_URI is not set in environment"
        }

    client = get_mongo_client()
    if client is None:
        return {
            "database": "mongodb",
            "status": "disconnected",
            "error": "Failed to establish connection pool"
        }

    start = time.perf_counter()
    try:
        # Run live ping command on the MongoDB admin database
        client.admin.command("ping")
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "database": "mongodb",
            "status": "connected",
            "database_name": MONGODB_DATABASE or "jarvis",
            "latency_ms": latency_ms
        }
    except Exception as e:
        logger.warning(f"MongoDB health ping failed: {e}")
        return {
            "database": "mongodb",
            "status": "error",
            "error": str(e)
        }

def close_mongo_connection():
    """
    Gracefully close the MongoClient connection pool on server shutdown.
    """
    global _mongo_client, _db_instance
    if _mongo_client is not None:
        try:
            logger.info("Closing MongoDB connection pool...")
            _mongo_client.close()
        except Exception as e:
            logger.warning(f"Error closing MongoDB connection: {e}")
        finally:
            _mongo_client = None
            _db_instance = None
