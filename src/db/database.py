"""
SQLite Database Manager.
Tek kullanıcılı lokal uygulama için basit veritabanı yönetimi.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List
from contextlib import contextmanager
from datetime import datetime

# Logging ayarları
logger = logging.getLogger(__name__)


class Database:
    """
    SQLite veritabanı yöneticisi.
    Thread-safe değil (tek kullanıcı için tasarlandı).
    """
    
    # Singleton instance
    _instance: Optional["Database"] = None
    
    def __init__(self, db_path: str = "data/filmstudio.db"):
        """
        Database başlat.
        
        Args:
            db_path: SQLite veritabanı dosya yolu
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._connection: Optional[sqlite3.Connection] = None
        self._init_database()
    
    @classmethod
    def get_instance(cls, db_path: str = "data/filmstudio.db") -> "Database":
        """Singleton instance al"""
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Veritabanı bağlantısı"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False  # Tek kullanıcı için güvenli
            )
            self._connection.row_factory = sqlite3.Row
            # WAL mode - daha güvenli yazma
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
        return self._connection
    
    def _init_database(self) -> None:
        """Veritabanı tablolarını oluştur"""
        logger.info(f"Veritabanı başlatılıyor: {self.db_path}")
        
        cursor = self.connection.cursor()
        
        # Projects tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                config_json TEXT NOT NULL,
                source_file_uri TEXT,
                source_file_name TEXT,
                total_token_usage_json TEXT DEFAULT '{}',
                active_caches_json TEXT DEFAULT '[]',
                output_files_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Module Progress tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS module_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                module TEXT NOT NULL,
                is_started INTEGER DEFAULT 0,
                is_completed INTEGER DEFAULT 0,
                progress_percentage REAL DEFAULT 0,
                current_step TEXT,
                total_steps INTEGER,
                completed_steps INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE(project_id, module)
            )
        """)
        
        # Screenplays tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenplays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                source_summary TEXT,
                concepts_json TEXT DEFAULT '[]',
                selected_concept_index INTEGER,
                protagonist_json TEXT,
                beat_sheet_json TEXT,
                scene_outlines_json TEXT DEFAULT '[]',
                scenes_json TEXT DEFAULT '[]',
                total_duration_minutes INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                optimization_report_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        # Context tablosu (token kullanımı geçmişi)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                components_json TEXT DEFAULT '{}',
                total_usage_json TEXT DEFAULT '{}',
                max_tokens INTEGER DEFAULT 1000000,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        # Active Chats tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                module TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE(project_id, module)
            )
        """)
        
        self.connection.commit()
        logger.info("Veritabanı tabloları oluşturuldu")
    
    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction hatası: {e}")
            raise
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """SQL sorgusu çalıştır"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"SQL hatası: {query[:100]}... - {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Çoklu SQL sorgusu çalıştır"""
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        self.connection.commit()
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Tek satır getir"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Tüm satırları getir"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def close(self) -> None:
        """Bağlantıyı kapat"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Veritabanı bağlantısı kapatıldı")


# Global instance
_db_instance: Optional[Database] = None


def get_db(db_path: str = "data/filmstudio.db") -> Database:
    """Global veritabanı instance al"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance
