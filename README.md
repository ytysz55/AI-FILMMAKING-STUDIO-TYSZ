# AI Film Yapım Stüdyosu

🎬 Kaynak materyallerden (kitap, PDF, nutuk vb.) Hollywood standartlarında film senaryoları, asset listeleri, shotlistler ve storyboardlar üreten AI destekli film yapım platformu.

## ✨ Özellikler

- **Senaryo Yazımı**: Visual Decompression tekniğiyle mikro-aksiyonlar içeren ekrana hazır senaryo
- **Asset Yönetimi**: Karakter, mekan ve objelerin tutarlılık için prompt sistemi
- **Shotlist Oluşturma**: AI Video üretimi için optimize edilmiş çekim listeleri
- **Storyboard Üretimi**: Twin-Keyframe görsel promptları ve Veo 3.1 video promptları

## 🚀 Hızlı Başlangıç

### Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını oluştur
cp .env.example .env
# GEMINI_API_KEY değerini düzenle
```

### API Key Alma

1. [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) adresine git
2. "Create API Key" butonuna tıkla
3. API key'i `.env` dosyasına yapıştır

## 📁 Proje Yapısı

```
AI-FILMMAKING-STUDIO/
├── src/
│   ├── core/                  # Çekirdek bileşenler
│   │   ├── gemini_client.py   # Gemini API wrapper
│   │   ├── context_manager.py # Token takibi
│   │   └── session.py         # Proje oturumu
│   ├── models/                # Pydantic şemaları
│   │   ├── screenplay.py      # Senaryo modelleri
│   │   ├── asset.py           # Asset modelleri
│   │   └── project.py         # Proje modelleri
│   └── modules/               # İş modülleri
│       ├── senaryo/           # Senaryo yazımı
│       ├── asset/             # Asset üretimi
│       ├── shotlist/          # Shotlist üretimi
│       └── storyboard/        # Storyboard üretimi
├── workflows/                 # Prompt şablonları
├── data/projects/             # Proje verileri
├── frontend/                  # Web arayüzü (yakında)
├── cli.py                     # Komut satırı aracı
├── requirements.txt           # Python bağımlılıkları
└── PRD.md                     # Ürün gereksinimleri
```

## 🔧 Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| AI Engine | Gemini 3 Pro/Flash (1M context) |
| API | google-genai SDK |
| Data Validation | Pydantic v2 |
| CLI | Click + Rich |
| (Yakında) API | FastAPI |
| (Yakında) Frontend | Vite + React |

## 📊 Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                   AI FILM YAPIM STÜDYOSU                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [SENARYO] ──► [ASSET] ──► [SHOTLIST] ──► [STORYBOARD]     │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              CONTEXT CACHING (%75 indirim)            │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                   GEMINI 3 API                        │ │
│  │            Pro (yaratıcı) / Flash (hızlı)            │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Senaryo Yazım Akışı

1. **Kaynak Analizi** → 3 film konsepti önerisi
2. **Konsept Seçimi** → Hedef süre belirleme
3. **Karakter Kartı** → Syd Field metodolojisi
4. **Beat Sheet** → Save the Cat 15 vuruş
5. **Sahne Listesi** → Zaman etiketli outline
6. **Sahne Yazımı** → Visual Decompression ile mikro-aksiyonlar
7. **Optimizasyon** → Script Doctor analizi

## 🔑 Anahtar Özellikler

### Context Caching
- Kaynak materyal bir kez yüklenir, cache'lenir
- Sonraki isteklerde %75 token indirimi
- 48 saat dosya saklama (Files API)

### Structured Output
- Tüm çıktılar JSON formatında
- Pydantic ile tip güvenliği
- Parse edilebilir, entegre edilebilir

### Token Takibi
- Gerçek zamanlı kullanım bilgisi
- %80'de uyarı, %95'te kritik uyarı
- Cache hit oranı gösterimi

## 📄 Lisans

MIT License

## 🤝 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır!
