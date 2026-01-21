# 🎬 AI Film Yapım Stüdyosu - Ürün Gereksinim Belgesi (PRD)

**Versiyon:** 1.0  
**Tarih:** 21 Ocak 2026  
**Durum:** Taslak  

---

## 📋 İçindekiler

1. [Yönetici Özeti](#1-yönetici-özeti)
2. [Vizyon ve Hedefler](#2-vizyon-ve-hedefler)
3. [Sistem Mimarisi](#3-sistem-mimarisi)
4. [Teknoloji Yığını](#4-teknoloji-yığını)
5. [Modüller ve Özellikler](#5-modüller-ve-özellikler)
6. [Senaryo Yazım Modülü (Faz 1)](#6-senaryo-yazım-modülü-faz-1)
7. [Veri Modelleri](#7-veri-modelleri)
8. [API Tasarımı](#8-api-tasarımı)
9. [Kullanıcı Arayüzü (UI/UX)](#9-kullanıcı-arayüzü-uiux)
10. [Geliştirme Yol Haritası](#10-geliştirme-yol-haritası)
11. [Riskler ve Azaltma Stratejileri](#11-riskler-ve-azaltma-stratejileri)

---

## 1. Yönetici Özeti

### 1.1 Proje Tanımı
**AI Film Yapım Stüdyosu**, kaynak materyallerden (kitap, PDF, nutuk vb.) Hollywood standartlarında film senaryoları, asset listeleri, shotlistler ve storyboardlar üreten, entegre bir AI destekli film yapım platformudur.

### 1.2 Temel Özellikler
- 🎭 **Senaryo Yazımı**: Kaynak materyalden "Visual Decompression" tekniğiyle ekrana hazır senaryo transkripsiyonu
- 🎨 **Asset Yönetimi**: Karakter, mekan ve objelerin tutarlılık için prompt sistemi
- 🎥 **Shotlist Oluşturma**: AI Video üretimi için optimize edilmiş çekim listeleri
- 📐 **Storyboard Üretimi**: Twin-Keyframe görsel promptları ve Veo 3.1 video promptları

### 1.3 Benzersiz Değer Önerisi
- **Tek Bağlam Penceresi**: Gemini 3'ün 1 milyon token context kapasitesi ile tüm senaryo yazım süreci bağlam kopukluğu olmadan yönetilir
- **Yapılandırılmış Çıktı**: Structured Output ile JSON formatında tutarlı, parse edilebilir sonuçlar
- **Modüler Mimari**: Her modül bağımsız çalışabilir, ama birbirine veri aktarabilir

---

## 2. Vizyon ve Hedefler

### 2.1 Uzun Vadeli Vizyon
Profesyonel film yapımcılarının ve içerik üreticilerinin ham kaynak materyallerden yayına hazır görsel içeriklere ulaşmasını sağlayan uçtan uca AI destekli bir prodüksiyon hattı oluşturmak.

### 2.2 İş Hedefleri
| Hedef | Metrik | Hedef Değer |
|-------|--------|-------------|
| Senaryo üretim hızı | Sahne/dakika | 1 sahne < 2 dk |
| Bağlam tutarlılığı | Hata oranı | < %5 |
| Kullanıcı memnuniyeti | NPS | > 70 |

### 2.3 Başarı Kriterleri
1. Kaynak materyal yükleme → Senaryo taslağı (%100 otomatik)
2. Sahne sahne interaktif yazım (kullanıcı kontrolü)
3. Tüm modüller arası veri akışı sorunsuz
4. JSON çıktıları diğer sistemlerle entegre edilebilir

---

## 3. Sistem Mimarisi

### 3.1 Genel Mimari Diyagramı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI FILM YAPIM STÜDYOSU                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   SENARYO   │───▶│    ASSET    │───▶│   SHOTLIST  │───▶│ STORYBOARD  │  │
│  │   MODÜLÜ    │    │   MODÜLÜ    │    │   MODÜLÜ    │    │   MODÜLÜ    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                 │                  │                  │          │
│         └─────────────────┴──────────────────┴──────────────────┘          │
│                                    │                                        │
│                    ┌───────────────▼───────────────┐                       │
│                    │      BAĞLAM YÖNETİCİSİ        │                       │
│                    │   (Context Manager - 1M)      │                       │
│                    └───────────────┬───────────────┘                       │
│                                    │                                        │
│                    ┌───────────────▼───────────────┐                       │
│                    │      GEMINI 3 API LAYER       │                       │
│                    │  (Pro / Flash / Nano Banana)  │                       │
│                    └───────────────────────────────┘                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Bağlam Yönetimi Stratejisi

**Problem**: LLM'ler uzun üretimlerde kalite kaybı yaşar ve özetlemeye başlar.

**Çözüm**: Sliding Window + Checkpoint yaklaşımı

```
┌────────────────────────────────────────────────────────────────┐
│                    1,000,000 TOKEN CONTEXT                     │
├────────────────────────────────────────────────────────────────┤
│ [SYSTEM PROMPT] │ [KAYNAK] │ [BEAT SHEET] │ [ÜRETİLEN SAHNELER]│
│     ~5K         │  ~200K   │     ~10K     │     ~500K          │
└────────────────────────────────────────────────────────────────┘
```

**Strateji**:
1. **System Prompt**: Sabit, her istekte gönderilir (~5K token)
2. **Kaynak Materyal**: İlk yüklemede analiz edilir, özeti saklanır
3. **Beat Sheet**: Onaylandıktan sonra sabit referans olarak tutulur
4. **Üretilen Sahneler**: Rolling buffer - en son 10 sahne aktif bağlamda

---

## 4. Teknoloji Yığını

### 4.1 Backend

| Katman | Teknoloji | Gerekçe |
|--------|-----------|---------|
| **Runtime** | Python 3.11+ | Gemini SDK en iyi Python desteği sağlıyor |
| **AI SDK** | `google-genai` | Resmi Google GenAI SDK |
| **Model** | Gemini 3 Flash/Pro | 1M context, Structured Output desteği |
| **API Framework** | FastAPI | Async/await, OpenAPI, tip güvenliği |
| **Doğrulama** | Pydantic v2 | Structured Output JSON şemaları |
| **Veritabanı** | SQLite (dev) / PostgreSQL (prod) | Proje verisi, checkpoint'ler |
| **Dosya Depolama** | Yerel dosya sistemi (dev) / S3 (prod) | Kaynak materyaller, çıktılar |

### 4.2 Frontend

| Katman | Teknoloji | Gerekçe |
|--------|-----------|---------|
| **Framework** | Vanilla HTML/CSS/JS veya Vite + React | Basitlik veya ölçeklenebilirlik |
| **Styling** | Vanilla CSS | Maksimum kontrol |
| **State** | React Context / Zustand | Basit durum yönetimi |
| **API İletişimi** | Fetch API + SSE | Streaming yanıtlar için |

### 4.3 Gemini API Konfigürasyonu

```python
# Model Seçimi
model_config = {
    "senaryo_analiz": "gemini-3-flash-preview",      # Hızlı, düşük maliyet
    "senaryo_yazim": "gemini-3-pro-preview",         # Yüksek kalite, derin düşünme
    "asset_uretim": "gemini-3-flash-preview",        # Hızlı prompt üretimi
    "gorsel_uretim": "nano-banana-pro"               # Görsel üretim
}

# Thinking Level Stratejisi
thinking_config = {
    "analiz": "low",        # Hızlı kaynak analizi
    "beat_sheet": "medium", # Orta seviye planlama
    "sahne_yazim": "high"   # Derin yaratıcı düşünme
}
```

---

## 5. Modüller ve Özellikler

### 5.1 Modül Haritası

```
AI-FILMMAKING-STUDIO/
├── workflows/              # Prompt şablonları (mevcut)
│   ├── senaryo.md
│   ├── asset.md
│   ├── shotlist.md
│   └── storyboard.md
├── src/
│   ├── core/              # Çekirdek bileşenler
│   │   ├── context_manager.py
│   │   ├── gemini_client.py
│   │   └── session.py
│   ├── modules/           # İş modülleri
│   │   ├── senaryo/
│   │   ├── asset/
│   │   ├── shotlist/
│   │   └── storyboard/
│   ├── models/            # Pydantic şemaları
│   ├── api/               # FastAPI routes
│   └── utils/             # Yardımcı fonksiyonlar
├── frontend/              # Web arayüzü
├── data/                  # Proje verileri
├── tests/                 # Test dosyaları
└── PRD.md                 # Bu belge
```

### 5.2 Modül Bağımlılıkları

```
SENARYO ──────► ASSET ──────► SHOTLIST ──────► STORYBOARD
   │               │              │                │
   │               │              │                │
   ▼               ▼              ▼                ▼
[Script.json]  [Assets.json]  [Shots.json]  [Storyboard.json]
```

---

## 6. Senaryo Yazım Modülü (Faz 1)

### 6.1 Modül Özeti

Senaryo Yazım Modülü, kaynak materyalleri (kitap, PDF, metin) analiz edip Hollywood standartlarında, "Visual Decompression" tekniğiyle ekrana hazır senaryo transkripsiyonları üretir.

### 6.2 İş Akışı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SENARYO YAZIM İŞ AKIŞI                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ADIM 1: KAYNAK ANALİZİ                                                    │
│  ┌─────────────┐                                                           │
│  │ Kaynak      │──▶ [Gemini Analiz] ──▶ 3 Film Konsepti + Logline          │
│  │ Yükleme     │                                                           │
│  └─────────────┘                                                           │
│        │                                                                    │
│        ▼  [Kullanıcı Seçimi: Konsept + Süre]                               │
│                                                                             │
│  ADIM 1.5: KARAKTER KİMLİK KARTI                                           │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Dramatik İhtiyaç + Bakış Açısı + Tavır + Değişim Yayı           │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│        │                                                                    │
│        ▼  [Kullanıcı Onayı]                                                │
│                                                                             │
│  ADIM 2: BEAT SHEET (15 VURUŞ)                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Save the Cat şablonu: Opening, Theme, Catalyst, B-Story...      │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│        │                                                                    │
│        ▼  [Kullanıcı Onayı]                                                │
│                                                                             │
│  ADIM 3: ZAMAN AYARLI SAHNE LİSTESİ                                        │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ SCENE 1: [Mekan] - [Zaman] - [SÜRE: 45 Saniye]                  │       │
│  │ SCENE 2: [Mekan] - [Zaman] - [SÜRE: 60 Saniye]                  │       │
│  │ ...                                                              │       │
│  │ TOPLAM: [Hedef Süre] dakika                                     │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│        │                                                                    │
│        ▼  [Kullanıcı Onayı: "BAŞLA"]                                       │
│                                                                             │
│  ADIM 4: DÖNGÜSEL SAHNE YAZIMI                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  ┌──────────┐     ┌──────────┐     ┌──────────┐                │       │
│  │  │ Sahne 1  │────▶│  ONAY?   │────▶│ Sahne 2  │ ─── ...        │       │
│  │  │ Üret     │     │ Revize?  │     │ Üret     │                │       │
│  │  │ DUR      │     │ Uzat?    │     │ DUR      │                │       │
│  │  └──────────┘     └──────────┘     └──────────┘                │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│        │                                                                    │
│        ▼  [Tüm Sahneler Tamamlandı]                                        │
│                                                                             │
│  ADIM 5: OPTİMİZASYON (İsteğe Bağlı)                                       │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Süreklilik, Mantık Hataları, Karakter Motivasyonu, Klişe Avcısı │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Kritik Yazım Kuralları (System Prompt'a Entegre)

| Kural | Açıklama | Örnek |
|-------|----------|-------|
| **Ekran Süresi** | Her sahne başlığına tahmini süre | `SCENE 1: ARENA - GÜNDÜZ - [SÜRE: 45 Saniye]` |
| **Visual Decompression** | Özet fiiller YASAK, mikro-aksiyon zorunlu | ❌ "Savaşırlar" ✅ "Kılıç göğse saplar, kan fışkırır" |
| **Zaman Kipi** | Geniş zaman veya Şimdiki zaman | ❌ "-maktadır" ✅ "-ar/-er" veya "-iyor" |
| **Kamera Direktifi Yok** | Eylemle betimle | ❌ "CAMERA ZOOMS IN" ✅ "Gözlerindeki korku belirginleşir" |
| **Ham Ses** | Fonetik, aksan, kusurlar dahil | ❌ "Ne yapıyorsun?" ✅ "Napıyon?" |
| **Metafor Yasak** | Fiziksel gerçeklik | ❌ "Köleliğe vurur" ✅ "Çekiç kafatasına çarpar" |

### 6.4 Komutlar ve Tetikleyiciler

| Komut | Eylem |
|-------|-------|
| `BAŞLA` | Sıradaki sahneyi yaz ve DUR |
| `ONAY` / `DEVAM` | Bir sonraki sahneye geç |
| `UZAT` | Mevcut sahneyi 2x uzunlukta yeniden yaz |
| `DÜZELT: [talimat]` | Belirtilen düzeltmeyle revize et |
| `OPTİMİZASYON` | Script Doctor moduna geç |

---

## 7. Veri Modelleri

### 7.1 Proje Şeması

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class FilmConcept(BaseModel):
    """Film konsepti önerisi"""
    genre: str = Field(description="Film türü (Dram, Aksiyon vb.)")
    logline: str = Field(description="Tek cümlelik hikaye özeti")
    tone: str = Field(description="Filmin tonu (Epik, Karanlık vb.)")

class CharacterCard(BaseModel):
    """Syd Field karakter kimlik kartı"""
    name: str = Field(description="Karakter adı")
    dramatic_need: str = Field(description="Film boyunca neyi elde etmek istiyor?")
    point_of_view: str = Field(description="Dünyayı nasıl görüyor?")
    attitude: str = Field(description="Olaylara nasıl tepki veriyor?")
    arc: str = Field(description="Başta kim, sonda kime dönüşecek?")

class Beat(BaseModel):
    """Save the Cat beat (vuruş)"""
    number: int = Field(description="Beat numarası (1-15)")
    name: str = Field(description="Beat adı (Opening Image, Catalyst vb.)")
    description: str = Field(description="Bu beatte ne olur")
    estimated_duration_seconds: int = Field(description="Tahmini ekran süresi")

class BeatSheet(BaseModel):
    """15 vuruşluk hikaye iskeleti"""
    beats: List[Beat] = Field(description="15 adet beat")
    total_duration_minutes: int = Field(description="Toplam süre (dakika)")

class SceneOutline(BaseModel):
    """Zaman ayarlı sahne özeti"""
    scene_number: int = Field(description="Sahne numarası")
    location: str = Field(description="Mekan")
    time_of_day: str = Field(description="Zaman (Gündüz, Gece vb.)")
    duration_seconds: int = Field(description="Hedef süre (saniye)")
    brief_description: str = Field(description="Kısa açıklama")

class Scene(BaseModel):
    """Tam yazılmış sahne"""
    scene_number: int
    header: str = Field(description="SCENE X: [MEKAN] - [ZAMAN] - [SÜRE]")
    action: str = Field(description="Aksiyon betimlemeleri")
    dialogue: Optional[List[dict]] = Field(description="Diyaloglar [{character, line}]")
    duration_seconds: int
    status: str = Field(default="draft", description="draft, approved, revised")

class Screenplay(BaseModel):
    """Tam senaryo"""
    title: str
    concepts: List[FilmConcept]
    selected_concept: Optional[FilmConcept]
    protagonist: Optional[CharacterCard]
    beat_sheet: Optional[BeatSheet]
    scene_outlines: List[SceneOutline]
    scenes: List[Scene]
    total_duration_minutes: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
```

### 7.2 Asset Şeması

```python
class AssetType(str, Enum):
    CHARACTER = "char"
    LOCATION = "loc"
    PROP = "prop"

class Asset(BaseModel):
    """Görsel tutarlılık için varlık"""
    asset_id: str = Field(description="Standart ID (char_mete_han)")
    asset_type: AssetType
    name: str = Field(description="Görüntülenen ad")
    description_tr: str = Field(description="Türkçe açıklama")
    description_en: str = Field(description="İngilizce açıklama (prompt için)")
    prompt: str = Field(description="Nano Banana Pro prompt")

class AssetList(BaseModel):
    """Proje varlık listesi"""
    project_id: str
    assets: List[Asset]
```

### 7.3 Shotlist Şeması

```python
class Shot(BaseModel):
    """Tekil çekim"""
    scene: int
    shot: int
    subjects: List[str] = Field(description="Asset ID'leri")
    description: str = Field(description="Teknik tarif + Eye Trace")
    dialogue: Optional[str]
    ert_seconds: int = Field(description="Estimated Run Time")
    size: str = Field(description="XWS, WS, MS, MCU, CU, ECU")
    perspective: str = Field(description="Low Angle, Eye-Level, High Angle")
    movement: str = Field(description="Static, Pan, Dolly, Tracking")
    focal_length: str = Field(description="16mm, 35mm, 50mm, 85mm, 200mm")
    aspect_ratio: str = Field(default="16:9")
    notes: Optional[str]

class ShotList(BaseModel):
    """Tam çekim listesi"""
    project_id: str
    shots: List[Shot]
    total_duration_seconds: int
```

---

## 8. API Tasarımı

### 8.1 Senaryo Modülü Endpoints

```
POST   /api/v1/projects                    # Yeni proje oluştur
GET    /api/v1/projects/{id}               # Proje detayı
DELETE /api/v1/projects/{id}               # Proje sil

POST   /api/v1/projects/{id}/source        # Kaynak materyal yükle
POST   /api/v1/projects/{id}/analyze       # Analiz et, konsept öner
POST   /api/v1/projects/{id}/select-concept # Konsept seç
POST   /api/v1/projects/{id}/character-card # Karakter kartı oluştur

POST   /api/v1/projects/{id}/beat-sheet    # Beat sheet oluştur
PUT    /api/v1/projects/{id}/beat-sheet    # Beat sheet güncelle

POST   /api/v1/projects/{id}/scene-outline # Sahne listesi oluştur

POST   /api/v1/projects/{id}/scenes/next   # Sıradaki sahneyi yaz
PUT    /api/v1/projects/{id}/scenes/{num}  # Sahne revize et
POST   /api/v1/projects/{id}/scenes/{num}/expand  # Sahneyi uzat

POST   /api/v1/projects/{id}/optimize      # Script Doctor çalıştır
GET    /api/v1/projects/{id}/export        # Senaryo export (JSON/Markdown)
```

### 8.2 Streaming Yanıtlar

Uzun sahne yazımları için Server-Sent Events (SSE) kullanılacak:

```javascript
// Frontend
const eventSource = new EventSource(`/api/v1/projects/${id}/scenes/next/stream`);
eventSource.onmessage = (event) => {
    const chunk = JSON.parse(event.data);
    appendToScene(chunk.text);
};
```

---

## 9. Kullanıcı Arayüzü (UI/UX)

### 9.1 Sayfa Yapısı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🎬 AI Film Yapım Stüdyosu                          [Projeler] [Ayarlar]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SIDEBAR                    │              MAIN CONTENT                     │
│  ┌─────────────────────┐    │    ┌─────────────────────────────────────┐   │
│  │ 📁 Proje Listesi    │    │    │                                     │   │
│  │ ├─ Mete Han         │    │    │   [Senaryo Editörü]                 │   │
│  │ └─ Yeni Proje +     │    │    │                                     │   │
│  │                     │    │    │   SCENE 1: ARENA - GÜNDÜZ           │   │
│  │ 📊 İlerleme         │    │    │   [SÜRE: 45 Saniye]                 │   │
│  │ ├─ Senaryo: %60     │    │    │                                     │   │
│  │ ├─ Asset: %0        │    │    │   Maximus, rakibinin etrafında...   │   │
│  │ ├─ Shotlist: %0     │    │    │                                     │   │
│  │ └─ Storyboard: %0   │    │    │   ─────────────────────────────     │   │
│  │                     │    │    │                                     │   │
│  │ ⚙️ Modüller         │    │    │   [Devam] [Uzat] [Düzelt]           │   │
│  │ ├─ 📝 Senaryo      │    │    │                                     │   │
│  │ ├─ 🎨 Asset        │    │    └─────────────────────────────────────┘   │
│  │ ├─ 🎥 Shotlist     │    │                                               │
│  │ └─ 📐 Storyboard   │    │    CONTEXT PANEL (Sağ Alt)                   │
│  └─────────────────────┘    │    ┌─────────────────────────────────────┐   │
│                              │    │ Token Kullanımı: 245K / 1M          │   │
│                              │    │ Aktif Sahne: 5/12                   │   │
│                              │    │ Toplam Süre: 8:45 / 15:00           │   │
│                              │    └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Senaryo Yazım Arayüzü Akışı

1. **Kaynak Yükleme Ekranı**
   - Dosya sürükle-bırak alanı
   - Metin yapıştırma kutusu
   - Desteklenen formatlar: PDF, TXT, DOCX, MD

2. **Konsept Seçim Ekranı**
   - 3 konsept kartı (Tür + Logline)
   - Hedef süre slider (5-120 dk)
   - "Konsepti Seç" butonu

3. **Beat Sheet Onay Ekranı**
   - 15 beat görsel timeline
   - Her beat düzenlenebilir
   - Toplam süre göstergesi

4. **Sahne Listesi Ekranı**
   - Tablo formatında sahneler
   - Süre dağılımı grafiği
   - "Yazmaya Başla" butonu

5. **Sahne Yazım Ekranı** (Ana Editör)
   - Canlı yazım gösterimi (streaming)
   - Aksiyon/Diyalog renk kodlaması
   - Inline revizyon araçları

---

## 10. Geliştirme Yol Haritası

### 10.1 Fazlar

```
FAZ 1 (Hafta 1-3): SENARYO MODÜLÜ ─────────────────────────►
   ├─ Çekirdek altyapı (Context Manager, Gemini Client)
   ├─ Senaryo iş akışı (Analiz → Beat Sheet → Sahne)
   ├─ CLI arayüzü (ilk test için)
   └─ Temel Web UI

FAZ 2 (Hafta 4-5): ASSET MODÜLÜ ──────────────────────────►
   ├─ Senaryo → Asset çıkarımı
   ├─ Prompt şablonları
   └─ Asset yönetim UI

FAZ 3 (Hafta 6-7): SHOTLIST MODÜLÜ ──────────────────────►
   ├─ Senaryo + Asset → Shotlist
   ├─ Süre hesaplama
   └─ Tablo editörü

FAZ 4 (Hafta 8-9): STORYBOARD MODÜLÜ ────────────────────►
   ├─ Shotlist → Storyboard promptları
   ├─ Veo 3.1 video prompt üretimi
   └─ Görsel önizleme

FAZ 5 (Hafta 10+): POLİSH & ENTEGRASYON ─────────────────►
   ├─ Modüller arası tam entegrasyon
   ├─ Export formatları (FDX, PDF)
   └─ Performans optimizasyonu
```

### 10.2 Faz 1 Detaylı Sprint Planı

#### Sprint 1 (Gün 1-5): Altyapı

| Görev | Süre | Öncelik |
|-------|------|---------|
| Proje yapısı oluştur | 2 saat | P0 |
| Gemini client wrapper | 4 saat | P0 |
| Context manager | 6 saat | P0 |
| Pydantic modelleri | 4 saat | P0 |
| Temel testler | 4 saat | P1 |

#### Sprint 2 (Gün 6-10): Senaryo İş Akışı

| Görev | Süre | Öncelik |
|-------|------|---------|
| Kaynak analiz fonksiyonu | 4 saat | P0 |
| Konsept üretimi | 4 saat | P0 |
| Beat sheet üretimi | 6 saat | P0 |
| Sahne outline | 4 saat | P0 |
| Sahne yazım döngüsü | 8 saat | P0 |

#### Sprint 3 (Gün 11-15): CLI & API

| Görev | Süre | Öncelik |
|-------|------|---------|
| CLI arayüzü | 6 saat | P0 |
| FastAPI endpoints | 8 saat | P1 |
| Streaming desteği | 4 saat | P1 |
| Error handling | 4 saat | P1 |

#### Sprint 4 (Gün 16-21): Web UI

| Görev | Süre | Öncelik |
|-------|------|---------|
| Temel layout | 6 saat | P1 |
| Proje yönetimi sayfası | 6 saat | P1 |
| Senaryo editörü | 10 saat | P1 |
| Onay/Revizyon UI | 6 saat | P1 |

---

## 11. Riskler ve Azaltma Stratejileri

### 11.1 Teknik Riskler

| Risk | Olasılık | Etki | Azaltma |
|------|----------|------|---------|
| Context limit aşımı | Orta | Yüksek | Rolling window, özet checkpoint'ler |
| API rate limiting | Düşük | Orta | Exponential backoff, queue sistemi |
| Kalite düşüşü (uzun üretim) | Yüksek | Yüksek | Sahne bazlı üretim, iç kalite kontrolü |
| Gemini 3 API değişiklikleri | Orta | Orta | Soyutlama katmanı, versiyon kilitleme |

### 11.2 İş Riskleri

| Risk | Olasılık | Etki | Azaltma |
|------|----------|------|---------|
| Kullanıcı beklentisi uyumsuzluğu | Orta | Yüksek | Erken kullanıcı testi, iteratif geliştirme |
| Yaratıcı çıktı kalitesi | Orta | Yüksek | Prompt mühendisliği, örnek eğitimi |

---

## 📎 Ekler

### Ek A: Örnek System Prompt (Senaryo Modülü)

```markdown
### ROL VE KİMLİK
Sen, Hollywood endüstri standartlarında uzmanlaşmış, "Visual Decompression" 
tekniğini kusursuz uygulayan kıdemli bir Görsel Eylem Tasarımcısısın.

[... senaryo.md içeriği buraya entegre edilir ...]
```

### Ek B: Gemini API Örnek Çağrı

```python
from google import genai
from google.genai import types
from models.screenplay import Scene

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents=f"""
    {system_prompt}
    
    Kaynak Materyal: {source_material}
    Beat Sheet: {beat_sheet}
    Önceki Sahneler: {previous_scenes}
    
    Şimdi SCENE {next_scene_number} yaz ve DUR.
    """,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high"),
        response_mime_type="application/json",
        response_json_schema=Scene.model_json_schema(),
    )
)

scene = Scene.model_validate_json(response.text)
```

---
 