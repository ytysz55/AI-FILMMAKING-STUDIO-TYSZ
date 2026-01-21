"""
Project Repository.
Proje CRUD işlemleri ve veritabanı yönetimi.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from .database import get_db, Database
from ..models.project import (
    Project, ProjectConfig, ModuleType, ModuleProgress,
    TokenUsage, CacheInfo
)
from ..models.screenplay import Screenplay, ProjectStatus

logger = logging.getLogger(__name__)


class ProjectRepository:
    """
    Proje Repository.
    Tüm proje CRUD işlemlerini ve veritabanı etkileşimlerini yönetir.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Repository başlat.
        
        Args:
            db: Database instance (None ise global instance kullanılır)
        """
        self.db = db or get_db()
        self._cache: Dict[str, Project] = {}  # RAM önbellek
    
    # ==================== PROJECT CRUD ====================
    
    def create_project(
        self,
        project_id: str,
        name: str,
        config: Optional[ProjectConfig] = None
    ) -> Project:
        """
        Yeni proje oluştur.
        
        Args:
            project_id: Proje ID
            name: Proje adı
            config: Proje konfigürasyonu
            
        Returns:
            Oluşturulan Project instance
        """
        config = config or ProjectConfig()
        now = datetime.now().isoformat()
        
        project = Project(
            id=project_id,
            name=name,
            config=config,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Veritabanına kaydet
        self.db.execute("""
            INSERT INTO projects (
                id, name, config_json, source_file_uri, source_file_name,
                total_token_usage_json, active_caches_json, output_files_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            name,
            config.model_dump_json(),
            None,
            None,
            project.total_token_usage.model_dump_json(),
            json.dumps([]),
            json.dumps([]),
            now,
            now
        ))
        
        # Modül progress kayıtlarını oluştur
        for module in ModuleType:
            self.db.execute("""
                INSERT INTO module_progress (
                    project_id, module, is_started, is_completed,
                    progress_percentage, current_step
                ) VALUES (?, ?, 0, 0, 0, NULL)
            """, (project_id, module.value))
        
        # Context state oluştur
        self.db.execute("""
            INSERT INTO context_state (project_id, components_json, total_usage_json, max_tokens)
            VALUES (?, '{}', '{}', 1000000)
        """, (project_id,))
        
        # Cache'e ekle
        self._cache[project_id] = project
        
        logger.info(f"Proje oluşturuldu: {project_id} - {name}")
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Proje getir.
        
        Args:
            project_id: Proje ID
            
        Returns:
            Project instance veya None
        """
        # Önce cache'e bak
        if project_id in self._cache:
            return self._cache[project_id]
        
        # Veritabanından getir
        row = self.db.fetch_one("""
            SELECT * FROM projects WHERE id = ?
        """, (project_id,))
        
        if not row:
            return None
        
        # Project oluştur
        project = self._row_to_project(row)
        
        # Module progress yükle
        progress_rows = self.db.fetch_all("""
            SELECT * FROM module_progress WHERE project_id = ?
        """, (project_id,))
        
        project.module_progress = [
            ModuleProgress(
                module=ModuleType(r["module"]),
                is_started=bool(r["is_started"]),
                is_completed=bool(r["is_completed"]),
                progress_percentage=r["progress_percentage"],
                current_step=r["current_step"],
                total_steps=r["total_steps"],
                completed_steps=r["completed_steps"]
            )
            for r in progress_rows
        ]
        
        # Cache'e ekle
        self._cache[project_id] = project
        
        return project
    
    def update_project(self, project: Project) -> None:
        """
        Projeyi güncelle.
        
        Args:
            project: Güncellenecek proje
        """
        now = datetime.now().isoformat()
        
        # Active caches JSON olarak serialize et
        caches_json = json.dumps([
            c.model_dump(mode="json") for c in project.active_caches
        ])
        
        self.db.execute("""
            UPDATE projects SET
                name = ?,
                config_json = ?,
                source_file_uri = ?,
                source_file_name = ?,
                total_token_usage_json = ?,
                active_caches_json = ?,
                output_files_json = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            project.name,
            project.config.model_dump_json(),
            project.source_file_uri,
            project.source_file_name,
            project.total_token_usage.model_dump_json(),
            caches_json,
            json.dumps(project.output_files),
            now,
            project.id
        ))
        
        # Module progress güncelle
        for mp in project.module_progress:
            self.db.execute("""
                UPDATE module_progress SET
                    is_started = ?,
                    is_completed = ?,
                    progress_percentage = ?,
                    current_step = ?,
                    total_steps = ?,
                    completed_steps = ?
                WHERE project_id = ? AND module = ?
            """, (
                int(mp.is_started),
                int(mp.is_completed),
                mp.progress_percentage,
                mp.current_step,
                mp.total_steps,
                mp.completed_steps,
                project.id,
                mp.module.value
            ))
        
        # Cache güncelle
        self._cache[project.id] = project
        
        logger.debug(f"Proje güncellendi: {project.id}")
    
    def delete_project(self, project_id: str) -> bool:
        """
        Projeyi sil.
        
        Args:
            project_id: Silinecek proje ID
            
        Returns:
            Başarılı mı
        """
        # Veritabanından sil (CASCADE ile ilişkili kayıtlar da silinir)
        cursor = self.db.execute("""
            DELETE FROM projects WHERE id = ?
        """, (project_id,))
        
        # Cache'den sil
        if project_id in self._cache:
            del self._cache[project_id]
        
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Proje silindi: {project_id}")
        return success
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        Tüm projeleri listele.
        
        Returns:
            Proje listesi (özet bilgiler)
        """
        rows = self.db.fetch_all("""
            SELECT p.id, p.name, p.created_at, p.updated_at,
                   mp.progress_percentage
            FROM projects p
            LEFT JOIN module_progress mp ON p.id = mp.project_id AND mp.module = 'senaryo'
            ORDER BY p.updated_at DESC
        """)
        
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "progress": r["progress_percentage"] or 0
            }
            for r in rows
        ]
    
    # ==================== SCREENPLAY CRUD ====================
    
    def save_screenplay(self, project_id: str, screenplay: Screenplay) -> None:
        """
        Senaryoyu kaydet.
        
        Args:
            project_id: Proje ID
            screenplay: Kaydedilecek senaryo
        """
        now = datetime.now().isoformat()
        
        # JSON serialize
        concepts_json = json.dumps([c.model_dump() for c in screenplay.concepts])
        protagonist_json = screenplay.protagonist.model_dump_json() if screenplay.protagonist else None
        beat_sheet_json = screenplay.beat_sheet.model_dump_json() if screenplay.beat_sheet else None
        scene_outlines_json = json.dumps([o.model_dump() for o in screenplay.scene_outlines])
        scenes_json = json.dumps([s.model_dump() for s in screenplay.scenes])
        optimization_json = screenplay.optimization_report.model_dump_json() if screenplay.optimization_report else None
        
        # UPSERT
        existing = self.db.fetch_one("""
            SELECT id FROM screenplays WHERE project_id = ?
        """, (project_id,))
        
        if existing:
            self.db.execute("""
                UPDATE screenplays SET
                    title = ?,
                    source_summary = ?,
                    concepts_json = ?,
                    selected_concept_index = ?,
                    protagonist_json = ?,
                    beat_sheet_json = ?,
                    scene_outlines_json = ?,
                    scenes_json = ?,
                    total_duration_minutes = ?,
                    status = ?,
                    optimization_report_json = ?,
                    updated_at = ?
                WHERE project_id = ?
            """, (
                screenplay.title,
                screenplay.source_summary,
                concepts_json,
                screenplay.selected_concept_index,
                protagonist_json,
                beat_sheet_json,
                scene_outlines_json,
                scenes_json,
                screenplay.total_duration_minutes,
                screenplay.status.value if isinstance(screenplay.status, ProjectStatus) else screenplay.status,
                optimization_json,
                now,
                project_id
            ))
        else:
            self.db.execute("""
                INSERT INTO screenplays (
                    project_id, title, source_summary, concepts_json,
                    selected_concept_index, protagonist_json, beat_sheet_json,
                    scene_outlines_json, scenes_json, total_duration_minutes,
                    status, optimization_report_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                screenplay.title,
                screenplay.source_summary,
                concepts_json,
                screenplay.selected_concept_index,
                protagonist_json,
                beat_sheet_json,
                scene_outlines_json,
                scenes_json,
                screenplay.total_duration_minutes,
                screenplay.status.value if isinstance(screenplay.status, ProjectStatus) else screenplay.status,
                optimization_json,
                now,
                now
            ))
        
        logger.debug(f"Screenplay kaydedildi: {project_id}")
    
    def get_screenplay(self, project_id: str) -> Optional[Screenplay]:
        """
        Senaryoyu getir.
        
        Args:
            project_id: Proje ID
            
        Returns:
            Screenplay instance veya None
        """
        from ..models.screenplay import (
            FilmConcept, CharacterCard, BeatSheet, Beat,
            SceneOutline, Scene, DialogueLine, OptimizationReport
        )
        
        row = self.db.fetch_one("""
            SELECT * FROM screenplays WHERE project_id = ?
        """, (project_id,))
        
        if not row:
            return None
        
        # JSON deserialize
        concepts = [FilmConcept(**c) for c in json.loads(row["concepts_json"] or "[]")]
        protagonist = CharacterCard.model_validate_json(row["protagonist_json"]) if row["protagonist_json"] else None
        beat_sheet = BeatSheet.model_validate_json(row["beat_sheet_json"]) if row["beat_sheet_json"] else None
        scene_outlines = [SceneOutline(**o) for o in json.loads(row["scene_outlines_json"] or "[]")]
        scenes = [Scene(**s) for s in json.loads(row["scenes_json"] or "[]")]
        optimization = OptimizationReport.model_validate_json(row["optimization_report_json"]) if row["optimization_report_json"] else None
        
        return Screenplay(
            title=row["title"],
            source_summary=row["source_summary"],
            concepts=concepts,
            selected_concept_index=row["selected_concept_index"],
            protagonist=protagonist,
            beat_sheet=beat_sheet,
            scene_outlines=scene_outlines,
            scenes=scenes,
            total_duration_minutes=row["total_duration_minutes"],
            status=row["status"],
            optimization_report=optimization
        )
    
    # ==================== CONTEXT STATE ====================
    
    def save_context_state(
        self,
        project_id: str,
        components: Dict[str, Any],
        total_usage: TokenUsage
    ) -> None:
        """Context state kaydet"""
        self.db.execute("""
            UPDATE context_state SET
                components_json = ?,
                total_usage_json = ?
            WHERE project_id = ?
        """, (
            json.dumps(components),
            total_usage.model_dump_json(),
            project_id
        ))
    
    def get_context_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Context state getir"""
        row = self.db.fetch_one("""
            SELECT * FROM context_state WHERE project_id = ?
        """, (project_id,))
        
        if not row:
            return None
        
        return {
            "components": json.loads(row["components_json"] or "{}"),
            "total_usage": json.loads(row["total_usage_json"] or "{}"),
            "max_tokens": row["max_tokens"]
        }
    
    # ==================== ACTIVE CHATS ====================
    
    def save_active_chats(self, project_id: str, chats: Dict[str, str]) -> None:
        """Active chats kaydet"""
        # Önce mevcut kayıtları sil
        self.db.execute("""
            DELETE FROM active_chats WHERE project_id = ?
        """, (project_id,))
        
        # Yeni kayıtları ekle
        for module, chat_id in chats.items():
            self.db.execute("""
                INSERT INTO active_chats (project_id, module, chat_id)
                VALUES (?, ?, ?)
            """, (project_id, module, chat_id))
    
    def get_active_chats(self, project_id: str) -> Dict[str, str]:
        """Active chats getir"""
        rows = self.db.fetch_all("""
            SELECT module, chat_id FROM active_chats WHERE project_id = ?
        """, (project_id,))
        
        return {r["module"]: r["chat_id"] for r in rows}
    
    # ==================== HELPER METHODS ====================
    
    def _row_to_project(self, row: Any) -> Project:
        """SQLite row'u Project'e dönüştür"""
        config = ProjectConfig.model_validate_json(row["config_json"])
        token_usage = TokenUsage.model_validate_json(row["total_token_usage_json"]) if row["total_token_usage_json"] else TokenUsage()
        
        # Active caches parse
        caches_data = json.loads(row["active_caches_json"] or "[]")
        active_caches = []
        for c in caches_data:
            try:
                # datetime string'leri parse et
                if isinstance(c.get("created_at"), str):
                    c["created_at"] = datetime.fromisoformat(c["created_at"])
                if isinstance(c.get("expires_at"), str):
                    c["expires_at"] = datetime.fromisoformat(c["expires_at"])
                active_caches.append(CacheInfo(**c))
            except Exception as e:
                logger.warning(f"Cache parse hatası: {e}")
        
        return Project(
            id=row["id"],
            name=row["name"],
            config=config,
            source_file_uri=row["source_file_uri"],
            source_file_name=row["source_file_name"],
            total_token_usage=token_usage,
            active_caches=active_caches,
            output_files=json.loads(row["output_files_json"] or "[]"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            module_progress=[]  # Ayrı sorguyla yüklenecek
        )
    
    def clear_cache(self) -> None:
        """RAM cache'i temizle"""
        self._cache.clear()
