"""
Senaryo yazımı için Pydantic modelleri.
Gemini API Structured Output ile uyumlu.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ==================== METODOLOJI TANIMLARI ====================

class StoryMethodology(str, Enum):
    """Hikaye anlatım metodolojileri"""
    SAVE_THE_CAT = "save_the_cat"      # Blake Snyder - 15 Beat
    SYD_FIELD = "syd_field"            # Syd Field - 3 Perde Paradigması
    TRUBY = "truby"                    # John Truby - 7/22 Adım
    HEROS_JOURNEY = "heros_journey"    # Vogler/Campbell - 12 Aşama
    STORY_CIRCLE = "story_circle"      # Dan Harmon - 8 Adım


class MethodologyStep(BaseModel):
    """Metodoloji adımı tanımı"""
    number: int = Field(description="Adım numarası")
    name: str = Field(description="Adım adı")
    english_name: str = Field(description="İngilizce adı (referans için)")
    description: str = Field(description="Bu adımda ne olması gerektiği")
    percentage_of_story: float = Field(description="Hikayedeki yüzdelik konumu (0-100)")
    act: int = Field(description="Hangi perdede (1, 2 veya 3)")


# Her metodoloji için adım tanımları
METHODOLOGY_DEFINITIONS: Dict[StoryMethodology, Dict[str, Any]] = {
    
    StoryMethodology.SAVE_THE_CAT: {
        "name": "Save the Cat!",
        "author": "Blake Snyder",
        "description": "Hollywood'un en popüler yapısal şablonu. 15 beat ile hikayeyi ticari başarıya optimize eder.",
        "best_for": ["Ticari filmler", "Hollywood yapımları", "Net yapılı hikayeler"],
        "step_count": 15,
        "steps": [
            {"number": 1, "name": "Açılış Görüntüsü", "english_name": "Opening Image", "description": "Kahramanın başlangıç durumunu gösteren görsel metafor", "percentage_of_story": 0, "act": 1},
            {"number": 2, "name": "Tema Belirtilir", "english_name": "Theme Stated", "description": "Filmin ana teması dolaylı olarak ifade edilir", "percentage_of_story": 5, "act": 1},
            {"number": 3, "name": "Kurulum", "english_name": "Set-Up", "description": "Kahramanın dünyası, kusurları ve ihtiyaçları tanıtılır", "percentage_of_story": 10, "act": 1},
            {"number": 4, "name": "Katalizör", "english_name": "Catalyst", "description": "Hikayeyi başlatan tetikleyici olay", "percentage_of_story": 10, "act": 1},
            {"number": 5, "name": "Tartışma", "english_name": "Debate", "description": "Kahraman maceraya çıkıp çıkmamayı tartışır", "percentage_of_story": 12.5, "act": 1},
            {"number": 6, "name": "2. Perdeye Geçiş", "english_name": "Break into Two", "description": "Kahraman eski dünyasını terk eder", "percentage_of_story": 25, "act": 2},
            {"number": 7, "name": "B Hikayesi", "english_name": "B Story", "description": "Genellikle aşk ya da dostluk - temayı taşır", "percentage_of_story": 30, "act": 2},
            {"number": 8, "name": "Eğlence ve Oyunlar", "english_name": "Fun and Games", "description": "Konseptin vaadini yerine getiren sahneler", "percentage_of_story": 35, "act": 2},
            {"number": 9, "name": "Orta Nokta", "english_name": "Midpoint", "description": "Sahte zafer veya sahte yenilgi", "percentage_of_story": 50, "act": 2},
            {"number": 10, "name": "Kötüler Yaklaşıyor", "english_name": "Bad Guys Close In", "description": "Dış ve iç baskılar artar", "percentage_of_story": 55, "act": 2},
            {"number": 11, "name": "Her Şey Kayıp", "english_name": "All Is Lost", "description": "En düşük nokta - ölüm anı", "percentage_of_story": 75, "act": 2},
            {"number": 12, "name": "Ruhun Karanlık Gecesi", "english_name": "Dark Night of the Soul", "description": "Kahraman yıkımla yüzleşir", "percentage_of_story": 80, "act": 2},
            {"number": 13, "name": "3. Perdeye Geçiş", "english_name": "Break into Three", "description": "Çözüm bulunur, plan yapılır", "percentage_of_story": 85, "act": 3},
            {"number": 14, "name": "Final", "english_name": "Finale", "description": "A ve B hikayeler birleşir, savaş kazanılır", "percentage_of_story": 90, "act": 3},
            {"number": 15, "name": "Kapanış Görüntüsü", "english_name": "Final Image", "description": "Değişimi gösteren görsel - açılışın tersi", "percentage_of_story": 100, "act": 3}
        ]
    },
    
    StoryMethodology.SYD_FIELD: {
        "name": "Syd Field Paradigması",
        "author": "Syd Field",
        "description": "Modern senaryo yazımının temeli. Üç perde ve kritik dönüm noktalarına odaklanır.",
        "best_for": ["Klasik yapı", "Esnek ama sağlam iskelet", "Her tür için uygun"],
        "step_count": 8,
        "steps": [
            {"number": 1, "name": "Kurulum", "english_name": "Setup", "description": "Karakterler, dünya ve durum tanıtılır", "percentage_of_story": 0, "act": 1},
            {"number": 2, "name": "Tetikleyici Olay", "english_name": "Inciting Incident", "description": "Hikayeyi harekete geçiren ilk kıvılcım", "percentage_of_story": 10, "act": 1},
            {"number": 3, "name": "1. Dönüm Noktası", "english_name": "Plot Point 1", "description": "Hikayeyi yeni yöne çeviren büyük olay", "percentage_of_story": 25, "act": 1},
            {"number": 4, "name": "Yüzleşme - Yükseliş", "english_name": "Confrontation Rising", "description": "Engeller ve çatışmalar yoğunlaşır", "percentage_of_story": 37.5, "act": 2},
            {"number": 5, "name": "Orta Nokta", "english_name": "Midpoint", "description": "Büyük bir keşif veya değişim anı", "percentage_of_story": 50, "act": 2},
            {"number": 6, "name": "Yüzleşme - Düşüş", "english_name": "Confrontation Falling", "description": "Kahraman zorluklarla boğuşur", "percentage_of_story": 62.5, "act": 2},
            {"number": 7, "name": "2. Dönüm Noktası", "english_name": "Plot Point 2", "description": "Son perdeyı tetikleyen kriz anı", "percentage_of_story": 75, "act": 2},
            {"number": 8, "name": "Çözüm", "english_name": "Resolution", "description": "Doruk noktası ve sonuç", "percentage_of_story": 90, "act": 3}
        ]
    },
    
    StoryMethodology.TRUBY: {
        "name": "John Truby 7 Adım",
        "author": "John Truby",
        "description": "Karakterin içsel değişimine odaklanan organik yapı. Zayıflık → Kendini Keşfetme yolculuğu.",
        "best_for": ["Karakter odaklı dramalar", "Derin psikolojik hikayeler", "Ödüllü filmler"],
        "step_count": 7,
        "steps": [
            {"number": 1, "name": "Zayıflık ve İhtiyaç", "english_name": "Weakness and Need", "description": "Kahramanın hayatını mahveden eksiklik. Psikolojik + ahlaki ihtiyaç.", "percentage_of_story": 0, "act": 1},
            {"number": 2, "name": "Arzu", "english_name": "Desire", "description": "Kahramanın somut hedefi - hikayeyi sürükleyen motor", "percentage_of_story": 15, "act": 1},
            {"number": 3, "name": "Rakip", "english_name": "Opponent", "description": "Kahramanın zayıflığına en çok saldıran karakter", "percentage_of_story": 25, "act": 2},
            {"number": 4, "name": "Plan", "english_name": "Plan", "description": "Hedefe ulaşmak için strateji", "percentage_of_story": 40, "act": 2},
            {"number": 5, "name": "Savaş", "english_name": "Battle", "description": "Kahraman ve rakip arasında nihai çatışma", "percentage_of_story": 75, "act": 3},
            {"number": 6, "name": "Kendini Keşfetme", "english_name": "Self-Revelation", "description": "Kahramanın değiştiği an - gerçeği görür", "percentage_of_story": 85, "act": 3},
            {"number": 7, "name": "Yeni Denge", "english_name": "New Equilibrium", "description": "Değişim sonrası yeni durum", "percentage_of_story": 95, "act": 3}
        ]
    },
    
    StoryMethodology.HEROS_JOURNEY: {
        "name": "Kahramanın Yolculuğu",
        "author": "Christopher Vogler / Joseph Campbell",
        "description": "Evrensel mitolojik yapı. Epik maceralar ve dönüşüm hikayeleri için ideal.",
        "best_for": ["Epik maceralar", "Fantastik hikayeler", "Star Wars, LOTR tarzı"],
        "step_count": 12,
        "steps": [
            {"number": 1, "name": "Sıradan Dünya", "english_name": "Ordinary World", "description": "Kahramanın günlük yaşamı", "percentage_of_story": 0, "act": 1},
            {"number": 2, "name": "Maceraya Çağrı", "english_name": "Call to Adventure", "description": "Kahraman eyleme çağrılır", "percentage_of_story": 10, "act": 1},
            {"number": 3, "name": "Çağrının Reddi", "english_name": "Refusal of the Call", "description": "Kahraman tereddüt eder", "percentage_of_story": 15, "act": 1},
            {"number": 4, "name": "Akıl Hocası ile Buluşma", "english_name": "Meeting the Mentor", "description": "Rehber/bilge kişi ortaya çıkar", "percentage_of_story": 20, "act": 1},
            {"number": 5, "name": "İlk Eşiği Geçiş", "english_name": "Crossing the First Threshold", "description": "Kahraman bilinmeyen dünyaya girer", "percentage_of_story": 25, "act": 2},
            {"number": 6, "name": "Sınavlar, Müttefikler, Düşmanlar", "english_name": "Tests, Allies, Enemies", "description": "Yeni dünyanın kurallarını öğrenir", "percentage_of_story": 35, "act": 2},
            {"number": 7, "name": "En Derin Mağaraya Yaklaşma", "english_name": "Approach to Inmost Cave", "description": "Büyük sınava hazırlık", "percentage_of_story": 45, "act": 2},
            {"number": 8, "name": "Büyük Sınav", "english_name": "Ordeal", "description": "Ölüm ve yeniden doğuş anı", "percentage_of_story": 55, "act": 2},
            {"number": 9, "name": "Ödül", "english_name": "Reward (Seizing the Sword)", "description": "Kahraman ganimet kazanır", "percentage_of_story": 65, "act": 2},
            {"number": 10, "name": "Geri Dönüş Yolu", "english_name": "The Road Back", "description": "Eve dönüş başlar", "percentage_of_story": 75, "act": 3},
            {"number": 11, "name": "Diriliş", "english_name": "Resurrection", "description": "Son sınav - tamamen dönüşür", "percentage_of_story": 85, "act": 3},
            {"number": 12, "name": "İksir ile Dönüş", "english_name": "Return with the Elixir", "description": "Değişmiş olarak eve döner", "percentage_of_story": 95, "act": 3}
        ]
    },
    
    StoryMethodology.STORY_CIRCLE: {
        "name": "Dan Harmon Story Circle",
        "author": "Dan Harmon",
        "description": "Kahramanın Yolculuğu'nun basitleştirilmiş versiyonu. TV dizileri ve kısa formlar için ideal.",
        "best_for": ["TV dizileri", "Kısa filmler", "Episodik içerik", "Animasyonlar"],
        "step_count": 8,
        "steps": [
            {"number": 1, "name": "Konfor Alanı", "english_name": "You (A character is in a zone of comfort)", "description": "Karakter tanıdık ortamında", "percentage_of_story": 0, "act": 1},
            {"number": 2, "name": "İstek", "english_name": "Need (But they want something)", "description": "Bir şey ister veya ihtiyaç duyar", "percentage_of_story": 12.5, "act": 1},
            {"number": 3, "name": "Bilinmeyene Giriş", "english_name": "Go (They enter an unfamiliar situation)", "description": "Yeni, bilinmeyen bir duruma girer", "percentage_of_story": 25, "act": 2},
            {"number": 4, "name": "Arayış", "english_name": "Search (Adapt to it)", "description": "Yeni duruma uyum sağlar, arar", "percentage_of_story": 37.5, "act": 2},
            {"number": 5, "name": "Bulma", "english_name": "Find (Get what they wanted)", "description": "İstediğini bulur veya elde eder", "percentage_of_story": 50, "act": 2},
            {"number": 6, "name": "Bedel Ödeme", "english_name": "Take (Pay a heavy price for it)", "description": "Ağır bir bedel öder", "percentage_of_story": 62.5, "act": 2},
            {"number": 7, "name": "Dönüş", "english_name": "Return (Then return to their familiar situation)", "description": "Tanıdık duruma geri döner", "percentage_of_story": 75, "act": 3},
            {"number": 8, "name": "Değişim", "english_name": "Change (Having changed)", "description": "Değişmiş olarak döngüyü tamamlar", "percentage_of_story": 90, "act": 3}
        ]
    }
}


def get_methodology_info(methodology: StoryMethodology) -> Dict[str, Any]:
    """Metodoloji bilgilerini döndür"""
    return METHODOLOGY_DEFINITIONS.get(methodology, METHODOLOGY_DEFINITIONS[StoryMethodology.SAVE_THE_CAT])


def get_methodology_steps(methodology: StoryMethodology) -> List[Dict[str, Any]]:
    """Metodoloji adımlarını döndür"""
    info = get_methodology_info(methodology)
    return info.get("steps", [])


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
    Hikaye adımı/vuruşu.
    Her metodoloji için kullanılabilir esnek yapı.
    """
    number: int = Field(ge=1, description="Beat/Adım numarası")
    name: str = Field(
        description="Adım adı (Opening Image, Catalyst, Weakness vb.)"
    )
    english_name: Optional[str] = Field(
        default=None,
        description="İngilizce adı (referans için)"
    )
    description: str = Field(
        description="Bu adımda ne olur - kısa özet"
    )
    estimated_duration_seconds: int = Field(
        ge=0,
        description="Tahmini ekran süresi (saniye)"
    )
    key_moment: Optional[str] = Field(
        default=None,
        description="Bu adımdaki en kritik an"
    )
    act: int = Field(
        default=1,
        ge=1, le=3,
        description="Hangi perdede (1, 2 veya 3)"
    )


class BeatSheet(BaseModel):
    """
    Hikaye iskeleti - Metodolojiye göre esnek adım sayısı.
    Save the Cat (15), Syd Field (8), Truby (7), Hero's Journey (12), Story Circle (8)
    """
    methodology: StoryMethodology = Field(
        default=StoryMethodology.SAVE_THE_CAT,
        description="Kullanılan metodoloji"
    )
    beats: List[Beat] = Field(
        min_length=1,
        description="Hikaye adımları listesi"
    )
    total_duration_minutes: int = Field(
        ge=1,
        description="Toplam süre (dakika)"
    )
    # Perde sınırları - metodolojiye göre otomatik hesaplanabilir
    act_one_end: Optional[int] = Field(
        default=None,
        description="1. Perde sonu (beat numarası)"
    )
    midpoint: Optional[int] = Field(
        default=None,
        description="Midpoint/Orta nokta (beat numarası)"
    )
    act_two_end: Optional[int] = Field(
        default=None,
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
    methodology: StoryMethodology = Field(
        default=StoryMethodology.SAVE_THE_CAT,
        description="Kullanılan hikaye metodolojisi"
    )
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
