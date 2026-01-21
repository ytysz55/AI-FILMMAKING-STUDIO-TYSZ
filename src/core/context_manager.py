"""
Context Manager.
Token kullanımı takibi ve bağlam yönetimi.
"""

from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from ..models.project import TokenUsage


@dataclass
class ContextComponent:
    """Bağlam bileşeni"""
    name: str
    token_count: int
    added_at: datetime = field(default_factory=datetime.now)
    is_cached: bool = False
    content_preview: str = ""  # İlk 100 karakter


class ContextManager:
    """
    Bağlam (context) yöneticisi.
    Token kullanımını takip eder ve limit kontrolü yapar.
    """
    
    # Varsayılan limitler
    DEFAULT_MAX_TOKENS = 1_000_000
    WARNING_THRESHOLD = 0.80  # %80'de uyarı
    CRITICAL_THRESHOLD = 0.95  # %95'te kritik uyarı
    
    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        project_id: Optional[str] = None
    ):
        """
        ContextManager başlat.
        
        Args:
            max_tokens: Maksimum token limiti
            project_id: Proje ID
        """
        self.max_tokens = max_tokens
        self.project_id = project_id
        
        # Bileşen takibi
        self._components: Dict[str, ContextComponent] = {}
        
        # Kümülatif kullanım
        self._total_usage = TokenUsage()
        
        # Geçmiş kullanımlar (her istek için)
        self._usage_history: List[TokenUsage] = []
    
    # ==================== BİLEŞEN YÖNETİMİ ====================
    
    def add_component(
        self,
        name: str,
        content: str,
        is_cached: bool = False
    ) -> bool:
        """
        Bağlama bileşen ekle.
        
        Args:
            name: Bileşen adı (system_prompt, source_material, vb.)
            content: İçerik
            is_cached: Cache'lenmiş mi
            
        Returns:
            Başarılı mı (False = limit aşıldı)
        """
        token_count = self._estimate_tokens(content)
        
        # Limit kontrolü
        if self.current_tokens + token_count > self.max_tokens:
            return False
        
        self._components[name] = ContextComponent(
            name=name,
            token_count=token_count,
            is_cached=is_cached,
            content_preview=content[:100] + "..." if len(content) > 100 else content
        )
        
        return True
    
    def update_component(self, name: str, content: str) -> bool:
        """Mevcut bileşeni güncelle"""
        if name in self._components:
            old_tokens = self._components[name].token_count
            new_tokens = self._estimate_tokens(content)
            
            # Limit kontrolü (eski - yeni farkı)
            if self.current_tokens - old_tokens + new_tokens > self.max_tokens:
                return False
            
            self._components[name].token_count = new_tokens
            self._components[name].content_preview = (
                content[:100] + "..." if len(content) > 100 else content
            )
            return True
        return False
    
    def remove_component(self, name: str) -> bool:
        """Bileşeni kaldır"""
        if name in self._components:
            del self._components[name]
            return True
        return False
    
    def get_component(self, name: str) -> Optional[ContextComponent]:
        """Bileşen bilgisi al"""
        return self._components.get(name)
    
    # ==================== TOKEN TAKİBİ ====================
    
    def record_usage(self, usage: TokenUsage) -> None:
        """Token kullanımı kaydet"""
        self._usage_history.append(usage)
        
        # Kümülatif güncelle
        self._total_usage.prompt_tokens += usage.prompt_tokens
        self._total_usage.cached_tokens += usage.cached_tokens
        self._total_usage.output_tokens += usage.output_tokens
        self._total_usage.total_tokens += usage.total_tokens
    
    @property
    def current_tokens(self) -> int:
        """Şu anki toplam token sayısı"""
        return sum(c.token_count for c in self._components.values())
    
    @property
    def cached_tokens(self) -> int:
        """Cache'lenmiş token sayısı"""
        return sum(
            c.token_count for c in self._components.values() 
            if c.is_cached
        )
    
    @property
    def remaining_tokens(self) -> int:
        """Kalan token sayısı"""
        return self.max_tokens - self.current_tokens
    
    @property
    def usage_percentage(self) -> float:
        """Kullanım yüzdesi (0-100)"""
        return (self.current_tokens / self.max_tokens) * 100
    
    @property
    def total_usage(self) -> TokenUsage:
        """Toplam kümülatif kullanım"""
        return self._total_usage
    
    # ==================== DURUM KONTROL ====================
    
    def check_status(self) -> Dict[str, any]:
        """
        Durum kontrolü yap.
        
        Gemini API'den dönen gerçek token kullanımını gösterir.
        _total_usage.prompt_tokens: Toplam prompt (input) token kullanımı
        
        Returns:
            {
                "level": "ok" | "warning" | "critical",
                "message": str,
                "current_tokens": int,
                "max_tokens": int,
                "percentage": float,
                "remaining": int
            }
        """
        # Gerçek token kullanımı (Gemini API'den gelen)
        real_tokens = self._total_usage.prompt_tokens
        
        # Percentage hesapla (gerçek kullanım bazında)
        real_percentage = (real_tokens / self.max_tokens) * 100 if self.max_tokens > 0 else 0
        real_remaining = self.max_tokens - real_tokens
        
        percentage_ratio = real_percentage / 100  # 0-1 arası
        
        if percentage_ratio >= self.CRITICAL_THRESHOLD:
            level = "critical"
            message = (
                f"⚠️ KRİTİK: Token limiti %{real_percentage:.1f} kullanıldı! "
                f"Sadece {real_remaining:,} token kaldı."
            )
        elif percentage_ratio >= self.WARNING_THRESHOLD:
            level = "warning"
            message = (
                f"⚡ UYARI: Token limiti %{real_percentage:.1f} kullanıldı. "
                f"{real_remaining:,} token kaldı."
            )
        else:
            level = "ok"
            message = f"✅ Token durumu normal: %{real_percentage:.1f} kullanıldı."
        
        return {
            "level": level,
            "message": message,
            "current_tokens": real_tokens,
            "max_tokens": self.max_tokens,
            "percentage": real_percentage,
            "remaining": real_remaining,
            "cached_tokens": self._total_usage.cached_tokens,
            "cache_ratio": (self._total_usage.cached_tokens / real_tokens * 100) if real_tokens > 0 else 0,
            # Ek bilgiler
            "total_output_tokens": self._total_usage.output_tokens,
            "total_tokens_all": self._total_usage.total_tokens
        }
    
    def can_add(self, estimated_tokens: int) -> bool:
        """Belirtilen token eklenebilir mi"""
        return self.current_tokens + estimated_tokens <= self.max_tokens
    
    # ==================== RAPORLAMA ====================
    
    def get_breakdown(self) -> Dict[str, Dict]:
        """Bileşen bazlı token dağılımı"""
        breakdown = {}
        for name, component in self._components.items():
            breakdown[name] = {
                "tokens": component.token_count,
                "percentage": (component.token_count / self.current_tokens * 100) 
                    if self.current_tokens > 0 else 0,
                "is_cached": component.is_cached,
                "added_at": component.added_at.isoformat(),
                "preview": component.content_preview
            }
        return breakdown
    
    def get_usage_report(self) -> Dict[str, any]:
        """Detaylı kullanım raporu"""
        status = self.check_status()
        
        return {
            "project_id": self.project_id,
            "status": status,
            "breakdown": self.get_breakdown(),
            "cumulative": {
                "total_requests": len(self._usage_history),
                "total_prompt_tokens": self._total_usage.prompt_tokens,
                "total_cached_tokens": self._total_usage.cached_tokens,
                "total_output_tokens": self._total_usage.output_tokens,
                "cache_hit_ratio": self._total_usage.cache_hit_ratio
            }
        }
    
    def format_status_bar(self, width: int = 40) -> str:
        """ASCII status bar oluştur"""
        filled = int((self.usage_percentage / 100) * width)
        empty = width - filled
        
        # Renk kodları (ANSI)
        if self.usage_percentage >= 95:
            color = "\033[91m"  # Kırmızı
        elif self.usage_percentage >= 80:
            color = "\033[93m"  # Sarı
        else:
            color = "\033[92m"  # Yeşil
        reset = "\033[0m"
        
        bar = f"{color}{'█' * filled}{'░' * empty}{reset}"
        
        return (
            f"📊 Bağlam Kullanımı: [{bar}] "
            f"{self.current_tokens:,} / {self.max_tokens:,} "
            f"({self.usage_percentage:.1f}%)"
        )
    
    # ==================== YARDIMCI METODLAR ====================
    
    def _estimate_tokens(self, text: str) -> int:
        """Yaklaşık token sayısı hesapla (4 karakter ≈ 1 token)"""
        return len(text) // 4
    
    def reset(self) -> None:
        """Bağlamı sıfırla"""
        self._components.clear()
        self._usage_history.clear()
        self._total_usage = TokenUsage()
    
    def to_dict(self) -> Dict:
        """Durumu dict olarak döndür (serialization için)"""
        return {
            "project_id": self.project_id,
            "max_tokens": self.max_tokens,
            "current_tokens": self.current_tokens,
            "components": {
                name: {
                    "token_count": c.token_count,
                    "is_cached": c.is_cached,
                    "added_at": c.added_at.isoformat()
                }
                for name, c in self._components.items()
            },
            "total_usage": {
                "prompt_tokens": self._total_usage.prompt_tokens,
                "cached_tokens": self._total_usage.cached_tokens,
                "output_tokens": self._total_usage.output_tokens,
                "total_tokens": self._total_usage.total_tokens
            }
        }
    
    def load_from_dict(self, data: Dict) -> None:
        """Dict'ten durumu yükle (deserialization için)"""
        if "total_usage" in data:
            usage_data = data["total_usage"]
            self._total_usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                cached_tokens=usage_data.get("cached_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )
