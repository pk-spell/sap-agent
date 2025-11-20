"""
Database Operations
===================

SQLite database operations for session persistence.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from models.session import ChatSession
from config import DB_PATH

logger = logging.getLogger(__name__)


def init_database():
    """Initialize SQLite database with schema"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT,
                current_prompt INTEGER DEFAULT 0,
                user_data TEXT,
                tfvars_content TEXT,
                tfvars_ready BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"✅ Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def save_session_to_db(session: ChatSession):
    """Persist session to database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Save session metadata
        cursor.execute("""
            INSERT OR REPLACE INTO chat_sessions
            (session_id, title, current_prompt, user_data, tfvars_content, tfvars_ready, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            session.session_id,
            session.get_title(),
            session.current_prompt,
            json.dumps(session.user_data),
            session.tfvars_content,
            session.tfvars_ready
        ))

        # Delete old messages for this session
        cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session.session_id,))

        # Save all messages
        for msg in session.messages:
            cursor.execute("""
                INSERT INTO chat_messages (session_id, role, content)
                VALUES (?, ?, ?)
            """, (session.session_id, msg["role"], msg["content"]))

        conn.commit()
        conn.close()
        logger.info(f"✅ Session {session.session_id} saved to database")
    except Exception as e:
        logger.error(f"❌ Failed to save session {session.session_id}: {e}")
        raise


def load_session_from_db(session_id: str) -> Optional[ChatSession]:
    """Load session from database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Load session metadata
        cursor.execute("""
            SELECT title, current_prompt, user_data, tfvars_content, tfvars_ready, created_at, updated_at
            FROM chat_sessions WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # Create session object
        session = ChatSession(session_id)
        session.current_prompt = row[1]
        session.user_data = json.loads(row[2] or "{}")
        session.tfvars_content = row[3] or ""
        session.tfvars_ready = bool(row[4])

        # Load messages
        cursor.execute("""
            SELECT role, content FROM chat_messages
            WHERE session_id = ? ORDER BY timestamp ASC
        """, (session_id,))

        session.messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]

        conn.close()
        logger.info(f"✅ Session {session_id} loaded from database")
        return session
    except Exception as e:
        logger.error(f"❌ Failed to load session {session_id}: {e}")
        return None


def list_all_sessions() -> List[Dict[str, Any]]:
    """List all sessions with metadata"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.session_id, s.title, s.current_prompt, s.tfvars_ready, s.created_at, s.updated_at,
                   COUNT(m.id) as message_count
            FROM chat_sessions s
            LEFT JOIN chat_messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.updated_at DESC
        """)

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "title": row[1],
                "current_prompt": row[2],
                "tfvars_ready": bool(row[3]),
                "created_at": row[4],
                "updated_at": row[5],
                "message_count": row[6]
            })

        conn.close()
        return sessions
    except Exception as e:
        logger.error(f"❌ Failed to list sessions: {e}")
        return []


def delete_session_from_db(session_id: str) -> bool:
    """Delete a session from database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        logger.info(f"✅ Session {session_id} deleted")
        return deleted
    except Exception as e:
        logger.error(f"❌ Failed to delete session {session_id}: {e}")
        return False
