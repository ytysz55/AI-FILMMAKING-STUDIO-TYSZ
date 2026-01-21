"""
Proje yönetimi için Pydantic modelleri.
Proje konfigürasyonu ve durumu.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pathlib import Path

# Metodoloji import
from src.models.screenplay import StoryMethodology


class ModuleType(str, Enum):
    """Modül türleri"""
    SENARYO = "senaryo"
    ASSET = "asset"
    SHOTLIST = "shotlist"
    STORYBOARD = "storyboard"


class ModelChoice(str, Enum):
    """Kullanılabilir Gemini modelleri"""
    GEMINI_3_PRO = "gemini-3-pro-preview"
    GEMINI_3_FLASH = "gemini-3-flash-preview"
    NANO_BANANA_PRO = "nano-banana-pro"


class ThinkingLevel(str, Enum):
    """Düşünme seviyesi"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProjectConfig(BaseModel):
    """Proje konfigürasyonu"""
    
    # Temel ayarlar
    target_duration_minutes: int = Field(
        default=30,  # Varsayılan 30 dakika
        ge=1,
        le=180,
        description="Hedef film süresi (dakika)"
    )
    language: str = Field(
        default="tr",
        description="Senaryo dili (tr, en)"
    )
    
    # 🎬 Metodoloji seçimi
    story_methodology: StoryMethodology = Field(
        default=StoryMethodology.SAVE_THE_CAT,
        description="Hikaye yazım metodolojisi (Save the Cat, Syd Field, Truby, Hero's Journey, Story Circle)"
    )
    
    # Model seçimleri
    scenario_model: ModelChoice = Field(
        default=ModelChoice.GEMINI_3_FLASH,  # Test için flash model
        description="Senaryo yazımı modeli"
    )
    asset_model: ModelChoice = Field(
        default=ModelChoice.GEMINI_3_FLASH,
        description="Asset üretim modeli"
    )
    shotlist_model: ModelChoice = Field(
        default=ModelChoice.GEMINI_3_FLASH,
        description="Shotlist üretim modeli"
    )
    storyboard_model: ModelChoice = Field(
        default=ModelChoice.GEMINI_3_FLASH,
        description="Storyboard prompt modeli"
    )
    image_model: ModelChoice = Field(
        default=ModelChoice.NANO_BANANA_PRO,
        description="Görsel üretim modeli"
    )
    
    # Thinking level
    analysis_thinking: ThinkingLevel = Field(
        default=ThinkingLevel.LOW,
        description="Analiz için thinking level"
    )
    beat_sheet_thinking: ThinkingLevel = Field(
        default=ThinkingLevel.MEDIUM,
        description="Beat sheet için thinking level"
    )
    scene_writing_thinking: ThinkingLevel = Field(
        default=ThinkingLevel.HIGH,
        description="Sahne yazımı için thinking level"
    )
    
    # Cache ayarları
    cache_ttl_seconds: int = Field(
        default=10800,  # 3 saat
        ge=300,  # Minimum 5 dakika
        le=86400,  # Maximum 24 saat
        description="Cache TTL (saniye)"
    )
    
    # İleri seviye
    auto_save: bool = Field(
        default=True,
        description="Otomatik kaydetme"
    )
    streaming_enabled: bool = Field(
        default=True,
        description="Streaming yanıt etkin"
    )


class TokenUsage(BaseModel):
    """Token kullanım bilgisi"""
    prompt_tokens: int = Field(default=0, description="Input token sayısı")
    cached_tokens: int = Field(default=0, description="Cache'den gelen token")
    output_tokens: int = Field(default=0, description="Output token sayısı")
    total_tokens: int = Field(default=0, description="Toplam token")
    
    @property
    def cache_hit_ratio(self) -> float:
        """Cache hit oranı"""
        if self.prompt_tokens == 0:
            return 0.0
        return self.cached_tokens / self.prompt_tokens


class ModuleProgress(BaseModel):
    """Modül ilerleme durumu"""
    module: ModuleType = Field(description="Modül türü")
    is_started: bool = Field(default=False, description="Başladı mı")
    is_completed: bool = Field(default=False, description="Tamamlandı mı")
    progress_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="İlerleme yüzdesi"
    )
    current_step: Optional[str] = Field(
        default=None,
        description="Şu anki adım"
    )
    total_steps: Optional[int] = Field(
        default=None,
        description="Toplam adım sayısı"
    )
    completed_steps: Optional[int] = Field(
        default=None,
        description="Tamamlanan adım sayısı"
    )


class CacheInfo(BaseModel):
    """Cache bilgisi"""
    cache_name: str = Field(description="Cache adı")
    model: str = Field(description="Model adı")
    created_at: datetime = Field(description="Oluşturulma zamanı")
    expires_at: datetime = Field(description="Bitiş zamanı")
    token_count: int = Field(description="Cache'deki token sayısı")
    
    @property
    def is_expired(self) -> bool:
        """Cache süresi doldu mu"""
        return datetime.now() > self.expires_at
    
    @property
    def remaining_seconds(self) -> int:
        """Kalan süre (saniye)"""
        delta = self.expires_at - datetime.now()
        return max(0, int(delta.total_seconds()))


class Project(BaseModel):
    """Ana proje modeli"""
    
    # Kimlik
    id: str = Field(description="Proje ID (UUID)")
    name: str = Field(description="Proje adı")
    
    # Konfigürasyon
    config: ProjectConfig = Field(
        default_factory=ProjectConfig,
        description="Proje konfigürasyonu"
    )
    
    # Dosyalar
    source_file_uri: Optional[str] = Field(
        default=None,
        description="Kaynak dosya URI (Files API)"
    )
    source_file_name: Optional[str] = Field(
        default=None,
        description="Kaynak dosya adı"
    )
    
    # Cache bilgileri
    active_caches: List[CacheInfo] = Field(
        default_factory=list,
        description="Aktif cache'ler"
    )
    
    # Modül durumları
    module_progress: List[ModuleProgress] = Field(
        default_factory=lambda: [
            ModuleProgress(module=ModuleType.SENARYO),
            ModuleProgress(module=ModuleType.ASSET),
            ModuleProgress(module=ModuleType.SHOTLIST),
            ModuleProgress(module=ModuleType.STORYBOARD),
        ],
        description="Modül ilerleme durumları"
    )
    
    # Token kullanımı
    total_token_usage: TokenUsage = Field(
        default_factory=TokenUsage,
        description="Toplam token kullanımı"
    )
    
    # Zaman damgaları
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Oluşturulma tarihi"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Son güncelleme"
    )
    
    # Çıktı dosyaları
    output_files: List[str] = Field(
        default_factory=list,
        description="Üretilen dosya yolları"
    )
    
    def get_module_progress(self, module: ModuleType) -> ModuleProgress:
        """Modül ilerlemesini getir"""
        for mp in self.module_progress:
            if mp.module == module:
                return mp
        raise ValueError(f"Modül bulunamadı: {module}")
    
    def update_module_progress(
        self,
        module: ModuleType,
        progress: float,
        current_step: Optional[str] = None
    ) -> None:
        """Modül ilerlemesini güncelle"""
        mp = self.get_module_progress(module)
        mp.progress_percentage = progress
        mp.current_step = current_step
        if progress >= 100:
            mp.is_completed = True
        self.updated_at = datetime.now()
    
    @property
    def overall_progress(self) -> float:
        """Genel ilerleme yüzdesi"""
        if not self.module_progress:
            return 0.0
        total = sum(mp.progress_percentage for mp in self.module_progress)
        return total / len(self.module_progress)
    
    @property
    def data_directory(self) -> Path:
        """Proje veri dizini"""
        return Path("data/projects") / self.id
    
    def add_token_usage(self, usage: TokenUsage) -> None:
        """Token kullanımı ekle"""
        self.total_token_usage.prompt_tokens += usage.prompt_tokens
        self.total_token_usage.cached_tokens += usage.cached_tokens
        self.total_token_usage.output_tokens += usage.output_tokens
        self.total_token_usage.total_tokens += usage.total_tokens
