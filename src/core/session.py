"""
Project Session.
Proje oturumu yönetimi ve durum takibi.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .gemini_client import GeminiClient
from .context_manager import ContextManager
from ..models.project import (
    Project, 
    ProjectConfig, 
    ModuleType, 
    TokenUsage,
    ThinkingLevel
)
from ..models.screenplay import Screenplay, ProjectStatus
from ..db import ProjectRepository, get_db

logger = logging.getLogger(__name__)


class ProjectSession:
    """
    Proje oturumu.
    GeminiClient ve ContextManager'ı birleştirir.
    Proje durumunu yönetir.
    """
    
    # Veri dizini
    DATA_DIR = Path("data/projects")
    
    def __init__(
        self,
        project_name: str,
        config: Optional[ProjectConfig] = None,
        project_id: Optional[str] = None,
        api_key: Optional[str] = None,
        repository: Optional[ProjectRepository] = None
    ):
        """
        ProjectSession başlat.
        
        Args:
            project_name: Proje adı
            config: Proje konfigürasyonu
            project_id: Mevcut proje ID (yükleme için)
            api_key: Gemini API key
            repository: Proje repository (SQLite)
        """
        self.project_id = project_id or str(uuid.uuid4())
        
        # Repository (SQLite)
        self._repo = repository or ProjectRepository()
        
        # Mevcut proje varsa veritabanından yükle
        existing_project = self._repo.get_project(self.project_id)
        if existing_project:
            self.project = existing_project
        else:
            # Yeni proje oluştur
            self.project = self._repo.create_project(
                project_id=self.project_id,
                name=project_name,
                config=config or ProjectConfig()
            )
        
        # Clients
        self.gemini = GeminiClient(api_key=api_key)
        self.context = ContextManager(
            max_tokens=1_000_000,
            project_id=self.project_id
        )
        
        # Context state yükle (varsa)
        context_state = self._repo.get_context_state(self.project_id)
        if context_state and context_state.get("total_usage"):
            self.context.load_from_dict(context_state)
        
        # Senaryo durumu - veritabanından yükle
        self.screenplay = self._repo.get_screenplay(self.project_id)
        
        # Aktif chat ID'leri ve kaynak dosya
        self._active_chats = self._repo.get_active_chats(self.project_id)
        self._source_file: Optional[Any] = None  # Yüklenen dosya objesi
        
        # Proje dizini oluştur (dosya yüklemeleri için)
        self.project_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def project_dir(self) -> Path:
        """Proje dizini"""
        return self.DATA_DIR / self.project_id
    
    # ==================== KAYNAK YÖNETİMİ ====================
    
    def upload_source(self, file_path: str) -> str:
        """
        Kaynak materyal yükle.
        
        Args:
            file_path: Dosya yolu
            
        Returns:
            Dosya URI
        """
        # Files API ile yükle - File objesi döner
        uploaded_file = self.gemini.upload_file(
            file_path,
            display_name=f"source_{self.project_id}"
        )
        
        # File objesini sakla (cache için)
        self._source_file = uploaded_file
        
        # Proje bilgisini güncelle
        self.project.source_file_uri = uploaded_file.uri
        self.project.source_file_name = Path(file_path).name
        
        # Context'e ekle (tahmini token)
        file_size = Path(file_path).stat().st_size
        estimated_tokens = file_size // 4  # Yaklaşık
        self.context.add_component(
            "source_material",
            f"[Kaynak Materyal: {file_path}, ~{estimated_tokens} token]",
            is_cached=False
        )
        
        self._save_state()
        return uploaded_file.uri
    
    # ==================== CACHE YÖNETİMİ ====================
    
    def create_module_cache(
        self,
        module: ModuleType,
        system_prompt: str,
        additional_content: Optional[str] = None
    ) -> str:
        """
        Modül için cache oluştur.
        
        Args:
            module: Modül türü
            system_prompt: System prompt
            additional_content: Ek içerik (önceki modül çıktısı)
            
        Returns:
            Cache ID
        """
        cache_id = f"{self.project_id}_{module.value}"
        
        # İçerikleri hazırla - File objesi doğrudan geçilebilir
        contents = []
        
        # Kaynak dosya varsa File objesini ekle
        if hasattr(self, '_source_file') and self._source_file:
            contents.append(self._source_file)
        
        # Ek içerik varsa ekle
        if additional_content:
            contents.append(additional_content)
        
        # Model seç
        model = self._get_model_for_module(module)
        
        # Cache oluştur
        cache_info = self.gemini.create_cache(
            cache_id=cache_id,
            model=model,
            system_instruction=system_prompt,
            contents=contents if contents else None,
            ttl_seconds=self.project.config.cache_ttl_seconds,
            display_name=f"{self.project.name}_{module.value}"
        )
        
        # Proje cache listesine ekle
        self.project.active_caches.append(cache_info)
        
        # Context'e ekle
        self.context.add_component(
            f"cache_{module.value}",
            f"[Cache: {cache_id}, {cache_info.token_count} token]",
            is_cached=True
        )
        
        self._save_state()
        return cache_id
    
    # ==================== CHAT YÖNETİMİ ====================
    
    def start_module_chat(
        self,
        module: ModuleType,
        cache_id: Optional[str] = None
    ) -> str:
        """
        Modül için chat başlat veya mevcut chat'i kullan.
        
        ÖNEMLİ: Gemini API'de chat, client-side bir wrapper'dır.
        Chat silindiğinde konuşma geçmişi (context) kaybolur.
        Bu nedenle mevcut chat varsa silmek yerine yeniden kullanıyoruz.
        
        Args:
            module: Modül türü
            cache_id: Kullanılacak cache ID
            
        Returns:
            Chat ID
        """
        chat_id = f"{self.project_id}_{module.value}_chat"
        
        # Mevcut chat varsa ve memory'de ise, aynısını kullan (context korunur)
        if module.value in self._active_chats:
            existing_chat_id = self._active_chats[module.value]
            if existing_chat_id in self.gemini._chats:
                logger.info(f"Mevcut chat oturumu kullanılıyor (context korunuyor): {existing_chat_id}")
                return existing_chat_id
            # Memory'de yok (server restart sonrası) - yeniden oluştur
            logger.info(f"Chat memory'de yok, yeniden oluşturuluyor: {existing_chat_id}")
        
        # Model ve thinking level seç
        model = self._get_model_for_module(module)
        thinking = self._get_thinking_for_module(module)
        
        # Chat oluştur
        self.gemini.create_chat(
            chat_id=chat_id,
            model=model,
            cache_id=cache_id or f"{self.project_id}_{module.value}",
            thinking_level=thinking
        )
        
        self._active_chats[module.value] = chat_id
        
        # Modül başladı
        progress = self.project.get_module_progress(module)
        progress.is_started = True
        
        self._save_state()
        return chat_id
    
    def send_message(
        self,
        module: ModuleType,
        message: str,
        stream: bool = False
    ) -> tuple[str, TokenUsage]:
        """
        Modül chat'ine mesaj gönder.
        
        Args:
            module: Modül türü
            message: Mesaj
            stream: Streaming yanıt mı
            
        Returns:
            (yanıt, token kullanımı)
        """
        chat_id = self._active_chats.get(module.value)
        if not chat_id:
            raise ValueError(f"Modül için aktif chat yok: {module.value}")
        
        # Server restart sonrası chat memory'de olmayabilir - auto-recovery
        if chat_id not in self.gemini._chats:
            # Cache ID'yi bul
            cache_id = f"{self.project_id}_{module.value}"
            
            # Yeniden chat oluştur (cache'i kullanarak)
            model = self._get_model_for_module(module)
            thinking = self._get_thinking_for_module(module)
            
            self.gemini.create_chat(
                chat_id=chat_id,
                model=model,
                cache_id=cache_id,
                thinking_level=thinking
            )
        
        # Mesaj gönder
        response, usage = self.gemini.send_message(chat_id, message, stream)
        
        # Token kullanımı kaydet
        self.context.record_usage(usage)
        self.project.add_token_usage(usage)
        
        self._save_state()
        return response, usage
    
    # ==================== STRUCTURED OUTPUT ====================
    
    def generate_structured(
        self,
        module: ModuleType,
        prompt: str,
        response_schema,
        cache_id: Optional[str] = None,
        use_chat: bool = True
    ):
        """
        Yapılandırılmış yanıt üret.
        
        Chat oturumu varsa ve use_chat=True ise, aynı chat üzerinden
        mesaj gönderir ve history korunur. Yoksa bağımsız çağrı yapar.
        
        Args:
            module: Modül türü
            prompt: Prompt
            response_schema: Pydantic model sınıfı
            cache_id: Cache ID
            use_chat: Chat oturumu kullan
            
        Returns:
            Pydantic model instance
        """
        chat_id = self._active_chats.get(module.value)
        
        # Chat oturumu varsa ve kullanılacaksa, chat üzerinden structured output al
        if use_chat and chat_id:
            # Server restart sonrası chat memory'de olmayabilir - auto-recovery
            if chat_id not in self.gemini._chats:
                # Cache ID'yi bul ve chat'i yeniden oluştur
                target_cache_id = cache_id or f"{self.project_id}_{module.value}"
                model = self._get_model_for_module(module)
                thinking = self._get_thinking_for_module(module)
                
                self.gemini.create_chat(
                    chat_id=chat_id,
                    model=model,
                    cache_id=target_cache_id,
                    thinking_level=thinking
                )
            
            result, usage = self.gemini.send_message_structured(
                chat_id=chat_id,
                message=prompt,
                response_schema=response_schema
            )
        else:
            # Fallback: bağımsız çağrı
            model = self._get_model_for_module(module)
            thinking = self._get_thinking_for_module(module)
            
            result, usage = self.gemini.generate_structured(
                model=model,
                prompt=prompt,
                response_schema=response_schema,
                cache_id=cache_id,
                thinking_level=thinking
            )
        
        # Token kullanımı kaydet
        self.context.record_usage(usage)
        self.project.add_token_usage(usage)
        
        self._save_state()
        return result
    
    # ==================== DURUM YÖNETİMİ ====================
    
    def update_progress(
        self,
        module: ModuleType,
        progress: float,
        current_step: Optional[str] = None
    ) -> None:
        """Modül ilerlemesini güncelle"""
        self.project.update_module_progress(module, progress, current_step)
        self._save_state()
    
    def get_status(self) -> Dict[str, Any]:
        """Proje durumu al"""
        return {
            "project": {
                "id": self.project.id,
                "name": self.project.name,
                "overall_progress": self.project.overall_progress,
                "created_at": self.project.created_at.isoformat(),
                "updated_at": self.project.updated_at.isoformat()
            },
            "context": self.context.check_status(),
            "token_usage": {
                "prompt": self.project.total_token_usage.prompt_tokens,
                "cached": self.project.total_token_usage.cached_tokens,
                "output": self.project.total_token_usage.output_tokens,
                "total": self.project.total_token_usage.total_tokens
            },
            "modules": {
                mp.module.value: {
                    "started": mp.is_started,
                    "completed": mp.is_completed,
                    "progress": mp.progress_percentage,
                    "current_step": mp.current_step
                }
                for mp in self.project.module_progress
            }
        }
    
    # ==================== KAYDETME / YÜKLEME ====================
    
    def _save_state(self) -> None:
        """Proje durumunu SQLite veritabanına kaydet"""
        try:
            # Proje güncelle
            self._repo.update_project(self.project)
            
            # Context state kaydet
            self._repo.save_context_state(
                self.project_id,
                self.context.to_dict().get("components", {}),
                self.context.total_usage
            )
            
            # Active chats kaydet
            self._repo.save_active_chats(self.project_id, self._active_chats)
            
            logger.debug(f"Proje durumu kaydedildi: {self.project_id}")
        except Exception as e:
            logger.error(f"Proje kaydetme hatası: {e}")
            raise
    
    def save_screenplay(self) -> Path:
        """Senaryoyu SQLite veritabanına kaydet"""
        if not self.screenplay:
            raise ValueError("Kaydedilecek senaryo yok")
        
        # Veritabanına kaydet
        self._repo.save_screenplay(self.project_id, self.screenplay)
        
        # Ayrıca JSON dosyası olarak da kaydet (export için)
        output_file = self.project_dir / "screenplay.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(self.screenplay.model_dump_json(indent=2))
        
        self.project.output_files.append(str(output_file))
        self._save_state()
        
        logger.info(f"Screenplay kaydedildi: {self.project_id}")
        return output_file
    
    @classmethod
    def load(cls, project_id: str, api_key: Optional[str] = None) -> "ProjectSession":
        """
        Mevcut projeyi SQLite veritabanından yükle.
        
        Args:
            project_id: Proje ID
            api_key: Gemini API key
            
        Returns:
            ProjectSession instance
        """
        repo = ProjectRepository()
        
        # Veritabanından projeyi kontrol et
        project = repo.get_project(project_id)
        if not project:
            raise FileNotFoundError(f"Proje bulunamadı: {project_id}")
        
        # Session oluştur (constructor otomatik olarak veritabanından yükleyecek)
        session = cls(
            project_name=project.name,
            config=project.config,
            project_id=project.id,
            api_key=api_key,
            repository=repo
        )
        
        # Cache bilgilerini GeminiClient'a aktar (server restart sonrası recovery)
        for cache_info in project.active_caches:
            # Cache ID'yi project_id + module şeklinde oluştur
            cache_id = cache_info.cache_name.split("/")[-1] if "/" in cache_info.cache_name else cache_info.cache_name
            # Senaryo modülü için cache_id oluştur
            for module in ["senaryo", "asset", "shotlist", "storyboard"]:
                if module in cache_id or cache_id.endswith(module):
                    full_cache_id = f"{project_id}_{module}"
                    session.gemini._caches[full_cache_id] = cache_info
                    break
        
        logger.info(f"Proje yüklendi: {project_id}")
        return session
    
    @classmethod
    def list_projects(cls) -> list[Dict[str, Any]]:
        """Tüm projeleri SQLite veritabanından listele"""
        repo = ProjectRepository()
        return repo.list_projects()
    
    # ==================== YARDIMCI METODLAR ====================
    
    def _get_model_for_module(self, module: ModuleType) -> str:
        """Modül için model seç"""
        config = self.project.config
        
        if module == ModuleType.SENARYO:
            return config.scenario_model.value
        elif module == ModuleType.ASSET:
            return config.asset_model.value
        elif module == ModuleType.SHOTLIST:
            return config.shotlist_model.value
        elif module == ModuleType.STORYBOARD:
            return config.storyboard_model.value
        
        return config.scenario_model.value
    
    def _get_thinking_for_module(self, module: ModuleType) -> ThinkingLevel:
        """Modül için thinking level seç"""
        config = self.project.config
        
        if module == ModuleType.SENARYO:
            return config.scene_writing_thinking
        else:
            return config.analysis_thinking
