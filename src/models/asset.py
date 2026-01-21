"""
Asset yönetimi için Pydantic modelleri.
Karakter, mekan ve objelerin tutarlılık için tanımları.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
import re


class AssetType(str, Enum):
    """Asset türü"""
    CHARACTER = "char"
    LOCATION = "loc"
    PROP = "prop"


class Asset(BaseModel):
    """
    Görsel tutarlılık için varlık tanımı.
    Nano Banana Pro ile uyumlu prompt içerir.
    """
    asset_id: str = Field(
        description="Standart ID (char_mete_han, loc_arena, prop_kilic)"
    )
    asset_type: AssetType = Field(description="Asset türü")
    name: str = Field(description="Görüntülenen ad (Mete Han, Arena, Kılıç)")
    description_tr: str = Field(description="Türkçe açıklama")
    description_en: str = Field(description="İngilizce açıklama (prompt için)")
    prompt: str = Field(description="Nano Banana Pro görsel prompt")
    
    # Opsiyonel detaylar
    age: Optional[str] = Field(default=None, description="Yaş (karakterler için)")
    ethnicity: Optional[str] = Field(default=None, description="Etnisite (karakterler için)")
    physical_traits: Optional[List[str]] = Field(
        default=None,
        description="Fiziksel özellikler (yara izi, sakal, vb.)"
    )
    clothing: Optional[str] = Field(default=None, description="Kıyafet detayları")
    materials: Optional[List[str]] = Field(
        default=None,
        description="Malzemeler (deri, metal, ahşap vb.)"
    )
    era: Optional[str] = Field(default=None, description="Dönem/çağ")
    
    @field_validator('asset_id')
    @classmethod
    def validate_asset_id(cls, v: str) -> str:
        """Asset ID formatını doğrula: lowercase, underscore ile ayrılmış"""
        if not re.match(r'^(char|loc|prop)_[a-z0-9_]+$', v):
            raise ValueError(
                f"Asset ID '{v}' geçersiz format. "
                "Format: char_isim, loc_mekan veya prop_obje olmalı (küçük harf)"
            )
        return v
    
    @property
    def type_prefix(self) -> str:
        """Asset türü prefix'i"""
        return self.asset_id.split('_')[0]


class AssetList(BaseModel):
    """Proje varlık listesi"""
    project_id: str = Field(description="Proje ID")
    universe_era: str = Field(
        description="Evren ve dönem (Örn: Antik Türk, M.Ö. 3. yüzyıl)"
    )
    universe_description: str = Field(
        description="Evren açıklaması ve teknoloji seviyesi"
    )
    assets: List[Asset] = Field(description="Tüm asset listesi")
    
    @property
    def characters(self) -> List[Asset]:
        """Sadece karakterler"""
        return [a for a in self.assets if a.asset_type == AssetType.CHARACTER]
    
    @property
    def locations(self) -> List[Asset]:
        """Sadece mekanlar"""
        return [a for a in self.assets if a.asset_type == AssetType.LOCATION]
    
    @property
    def props(self) -> List[Asset]:
        """Sadece objeler"""
        return [a for a in self.assets if a.asset_type == AssetType.PROP]
    
    def get_asset_by_id(self, asset_id: str) -> Optional[Asset]:
        """ID ile asset bul"""
        for asset in self.assets:
            if asset.asset_id == asset_id:
                return asset
        return None


# === YAPILANDIRILMIŞ ÇIKTI İÇİN YARDIMCI MODELLER ===

class AssetExtractionResponse(BaseModel):
    """Asset çıkarım yanıtı"""
    universe_era: str = Field(description="Evren ve dönem")
    universe_description: str = Field(description="Evren açıklaması")
    characters: List[Asset] = Field(description="Karakter listesi")
    locations: List[Asset] = Field(description="Mekan listesi")
    props: List[Asset] = Field(description="Obje listesi")
