"""
Senaryo yazımı için Pydantic modelleri.
Gemini API Structured Output ile uyumlu.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class ProjectStatus(str, Enum):
    """Proje durumu"""
    DRAFT = "draft"
    ANALYZING = "analyzing"
    CONCEPT_SELECTION = "concept_selection"
    BEAT_SHEET = "beat_sheet"
    SCENE_OUTLINE = "scene_outline"
    WRITING = "writing"
    OPTIMIZATION = "optimization"
    COMPLETED = "completed"


class FilmConcept(BaseModel):
    """Film konsepti önerisi"""
    genre: str = Field(description="Film türü (Dram, Aksiyon, Macera vb.)")
    logline: str = Field(description="Tek cümlelik hikaye özeti (hook)")
    tone: str = Field(description="Filmin tonu (Epik, Karanlık, Umut Dolu vb.)")
    target_audience: Optional[str] = Field(default=None, description="Hedef kitle")
    unique_selling_point: Optional[str] = Field(default=None, description="Bu konsepti benzersiz yapan özellik")


class CharacterCard(BaseModel):
    """
    Syd Field karakter kimlik kartı.
    Ana karakterin dramatik yapısını tanımlar.
    """
    name: str = Field(description="Karakter adı")
    dramatic_need: str = Field(
        description="Film boyunca neyi elde etmek istiyor? (Somut hedef)"
    )
    point_of_view: str = Field(
        description="Dünyayı nasıl görüyor? (İnanç sistemi)"
    )
    attitude: str = Field(
        description="Olaylara nasıl tepki veriyor? (Davranışsal duruşu)"
    )
    arc: str = Field(
        description="Filmin başında kimdi, sonunda kime dönüşecek?"
    )
    backstory: Optional[str] = Field(
        default=None,
        description="Karakterin geçmişi ve motivasyonlarının kökeni"
    )
    flaws: Optional[List[str]] = Field(
        default=None,
        description="Karakterin kusurları ve zayıflıkları"
    )


class Beat(BaseModel):
    """
    Save the Cat beat (vuruş).
    Blake Snyder'ın 15 vuruşluk şablonundan bir vuruş.
    """
    number: int = Field(ge=1, le=15, description="Beat numarası (1-15)")
    name: str = Field(
        description="Beat adı (Opening Image, Theme Stated, Catalyst vb.)"
    )
    description: str = Field(
        description="Bu beatte ne olur - kısa özet"
    )
    estimated_duration_seconds: int = Field(
        ge=0,
        description="Tahmini ekran süresi (saniye)"
    )
    key_moment: Optional[str] = Field(
        default=None,
        description="Bu beatteki en kritik an"
    )


class BeatSheet(BaseModel):
    """
    15 vuruşluk hikaye iskeleti.
    Save the Cat metodolojisi.
    """
    beats: List[Beat] = Field(
        min_length=15,
        max_length=15,
        description="15 adet beat"
    )
    total_duration_minutes: int = Field(
        ge=1,
        description="Toplam süre (dakika)"
    )
    act_one_end: int = Field(
        default=3,
        description="1. Perde sonu (beat numarası)"
    )
    midpoint: int = Field(
        default=8,
        description="Midpoint (beat numarası)"
    )
    act_two_end: int = Field(
        default=12,
        description="2. Perde sonu (beat numarası)"
    )


class SceneOutline(BaseModel):
    """Zaman ayarlı sahne özeti"""
    scene_number: int = Field(ge=1, description="Sahne numarası")
    location: str = Field(description="Mekan (ARENA, SARAY, DAĞ YAMACI vb.)")
    time_of_day: str = Field(description="Zaman (GÜNDÜZ, GECE, ALACAKARANLIK vb.)")
    duration_seconds: int = Field(ge=1, description="Hedef süre (saniye)")
    brief_description: str = Field(description="Kısa açıklama (1-2 cümle)")
    beat_reference: Optional[int] = Field(
        default=None,
        description="İlişkili beat numarası"
    )
    emotional_arc: Optional[str] = Field(
        default=None,
        description="Sahnenin duygusal yayı (gerilim, rahatlama, patlama vb.)"
    )


class DialogueLine(BaseModel):
    """Tek bir diyalog satırı"""
    character: str = Field(description="Konuşan karakter")
    line: str = Field(description="Diyalog metni (fonetik dahil)")
    parenthetical: Optional[str] = Field(
        default=None,
        description="Oyunculuk notu (fısıldayarak, öfkeyle vb.)"
    )


class Scene(BaseModel):
    """
    Tam yazılmış sahne.
    Visual Decompression tekniğiyle mikro-aksiyonlar içerir.
    """
    scene_number: int = Field(ge=1, description="Sahne numarası")
    header: str = Field(
        description="Sahne başlığı: SCENE X: [MEKAN] - [ZAMAN] - [SÜRE: X Saniye]"
    )
    action: str = Field(
        description="Aksiyon betimlemeleri - mikro-aksiyonlarla detaylı"
    )
    dialogue: Optional[List[DialogueLine]] = Field(
        default=None,
        description="Diyaloglar listesi"
    )
    duration_seconds: int = Field(ge=1, description="Sahne süresi (saniye)")
    status: str = Field(
        default="draft",
        description="Sahne durumu: draft, approved, revised"
    )
    revision_count: int = Field(
        default=0,
        description="Revizyon sayısı"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Yazar/yönetmen notları"
    )


class Screenplay(BaseModel):
    """
    Tam senaryo.
    Tüm senaryo yazım sürecinin çıktısı.
    Aşamalı olarak doldurulur.
    """
    title: str = Field(description="Film başlığı")
    source_summary: Optional[str] = Field(
        default=None,
        description="Kaynak materyalin özeti"
    )
    concepts: List[FilmConcept] = Field(
        default_factory=list,
        description="Önerilen konseptler"
    )
    selected_concept_index: Optional[int] = Field(
        default=None,
        description="Seçilen konseptin indeksi"
    )
    protagonist: Optional[CharacterCard] = Field(
        default=None,
        description="Ana karakter"
    )
    supporting_characters: Optional[List[CharacterCard]] = Field(
        default=None,
        description="Yardımcı karakterler"
    )
    beat_sheet: Optional[BeatSheet] = Field(
        default=None,
        description="Beat sheet"
    )
    scene_outlines: List[SceneOutline] = Field(
        default_factory=list,
        description="Sahne outline listesi"
    )
    scenes: List[Scene] = Field(
        default_factory=list,
        description="Yazılmış sahneler"
    )
    total_duration_minutes: Optional[int] = Field(
        default=None,
        description="Toplam süre (dakika)"
    )
    status: ProjectStatus = Field(
        default=ProjectStatus.DRAFT,
        description="Proje durumu"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Oluşturulma tarihi"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Son güncelleme tarihi"
    )
    
    # Optimization raporu
    optimization_report: Optional[str] = Field(
        default=None,
        description="Script Doctor analiz raporu"
    )

    @property
    def selected_concept(self) -> FilmConcept:
        """Seçilen konsepti döndür"""
        return self.concepts[self.selected_concept_index]
    
    @property
    def completed_scenes_count(self) -> int:
        """Tamamlanan sahne sayısı"""
        return len([s for s in self.scenes if s.status == "approved"])
    
    @property
    def progress_percentage(self) -> float:
        """İlerleme yüzdesi"""
        if not self.scene_outlines:
            return 0.0
        return (len(self.scenes) / len(self.scene_outlines)) * 100


# === YAPILANDIRILMIŞ ÇIKTI İÇİN YARDIMCI MODELLER ===

class ConceptsResponse(BaseModel):
    """Konsept analizi yanıtı"""
    concepts: List[FilmConcept] = Field(
        min_length=3,
        max_length=3,
        description="3 farklı film konsepti"
    )
    source_summary: str = Field(
        description="Kaynak materyalin kısa özeti"
    )


class CharacterCardResponse(BaseModel):
    """Karakter kartı yanıtı"""
    protagonist: CharacterCard = Field(description="Ana karakter kartı")
    suggested_supporting: Optional[List[str]] = Field(
        default=None,
        description="Önerilen yardımcı karakterler (isim listesi)"
    )


class BeatSheetResponse(BaseModel):
    """Beat sheet yanıtı"""
    beat_sheet: BeatSheet = Field(description="15 vuruşluk beat sheet")


class SceneOutlinesResponse(BaseModel):
    """Sahne outline listesi yanıtı"""
    outlines: List[SceneOutline] = Field(description="Sahne outline listesi")
    total_duration_seconds: int = Field(description="Toplam süre (saniye)")


class SceneResponse(BaseModel):
    """Tek sahne yanıtı"""
    scene: Scene = Field(description="Yazılan sahne")
    # quality_check dict yerine str olarak - Gemini API dict tipinde additionalProperties kullanamıyor
    quality_notes: Optional[str] = Field(
        default=None,
        description="Kalite kontrol notları"
    )


class OptimizationReport(BaseModel):
    """Script Doctor analiz raporu"""
    continuity_issues: List[str] = Field(
        default_factory=list,
        description="Süreklilik hataları"
    )
    plot_holes: List[str] = Field(
        default_factory=list,
        description="Mantık hataları"
    )
    motivation_issues: List[str] = Field(
        default_factory=list,
        description="Karakter motivasyon sorunları"
    )
    cliche_warnings: List[str] = Field(
        default_factory=list,
        description="Klişe uyarıları"
    )
    passive_protagonist_issues: List[str] = Field(
        default_factory=list,
        description="Pasif karakter sorunları"
    )
    first_ten_minutes_check: str = Field(
        description="İlk 10 dakika analizi"
    )
    robotic_dialogue_issues: List[str] = Field(
        default_factory=list,
        description="Robotik diyalog uyarıları"
    )
    overall_score: int = Field(
        ge=1, le=10,
        description="Genel kalite puanı (1-10)"
    )
    recommendations: List[str] = Field(
        description="Genel öneriler"
    )
