"""
Project Session.
Proje oturumu yönetimi ve durum takibi.
"""

import json
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
        api_key: Optional[str] = None
    ):
        """
        ProjectSession başlat.
        
        Args:
            project_name: Proje adı
            config: Proje konfigürasyonu
            project_id: Mevcut proje ID (yükleme için)
            api_key: Gemini API key
        """
        self.project_id = project_id or str(uuid.uuid4())
        
        # Proje oluştur
        self.project = Project(
            id=self.project_id,
            name=project_name,
            config=config or ProjectConfig()
        )
        
        # Clients
        self.gemini = GeminiClient(api_key=api_key)
        self.context = ContextManager(
            max_tokens=1_000_000,
            project_id=self.project_id
        )
        
        # Senaryo durumu
        self.screenplay: Optional[Screenplay] = None
        
        # Aktif chat ID'leri ve kaynak dosya
        self._active_chats: Dict[str, str] = {}  # module -> chat_id
        self._source_file: Optional[Any] = None  # Yüklenen dosya objesi
        
        # Proje dizini oluştur
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
        Modül için chat başlat.
        
        Args:
            module: Modül türü
            cache_id: Kullanılacak cache ID
            
        Returns:
            Chat ID
        """
        chat_id = f"{self.project_id}_{module.value}_chat"
        
        # Önceki chat varsa sil
        if module.value in self._active_chats:
            self.gemini.delete_chat(self._active_chats[module.value])
        
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
        """Proje durumunu kaydet"""
        state_file = self.project_dir / "state.json"
        
        state = {
            "project": self.project.model_dump(mode="json"),
            "context": self.context.to_dict(),
            "active_chats": self._active_chats
        }
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)
    
    def save_screenplay(self) -> Path:
        """Senaryoyu dosyaya kaydet"""
        if not self.screenplay:
            raise ValueError("Kaydedilecek senaryo yok")
        
        output_file = self.project_dir / "screenplay.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(self.screenplay.model_dump_json(indent=2))
        
        self.project.output_files.append(str(output_file))
        self._save_state()
        
        return output_file
    
    @classmethod
    def load(cls, project_id: str, api_key: Optional[str] = None) -> "ProjectSession":
        """
        Mevcut projeyi yükle.
        
        Args:
            project_id: Proje ID
            api_key: Gemini API key
            
        Returns:
            ProjectSession instance
        """
        state_file = cls.DATA_DIR / project_id / "state.json"
        
        if not state_file.exists():
            raise FileNotFoundError(f"Proje bulunamadı: {project_id}")
        
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        # Proje oluştur
        project = Project.model_validate(state["project"])
        
        session = cls(
            project_name=project.name,
            config=project.config,
            project_id=project.id,
            api_key=api_key
        )
        session.project = project
        session._active_chats = state.get("active_chats", {})
        
        # Context bilgilerini yükle (kümülatif token kullanımı)
        if "context" in state:
            session.context.load_from_dict(state["context"])
        
        # Senaryo varsa yükle
        screenplay_file = session.project_dir / "screenplay.json"
        if screenplay_file.exists():
            with open(screenplay_file, "r", encoding="utf-8") as f:
                session.screenplay = Screenplay.model_validate_json(f.read())
        
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
        
        return session
    
    @classmethod
    def list_projects(cls) -> list[Dict[str, Any]]:
        """Tüm projeleri listele"""
        projects = []
        
        if not cls.DATA_DIR.exists():
            return projects
        
        for project_dir in cls.DATA_DIR.iterdir():
            if project_dir.is_dir():
                state_file = project_dir / "state.json"
                if state_file.exists():
                    with open(state_file, "r", encoding="utf-8") as f:
                        state = json.load(f)
                    
                    projects.append({
                        "id": state["project"]["id"],
                        "name": state["project"]["name"],
                        "progress": state["project"].get("overall_progress", 0),
                        "updated_at": state["project"].get("updated_at")
                    })
        
        return sorted(projects, key=lambda x: x.get("updated_at", ""), reverse=True)
    
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
