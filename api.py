"""
FastAPI Backend - Senaryo Modülü API
"""

import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Modül importları
from src.core import GeminiClient, ContextManager, ProjectSession
from src.models.project import Project, ProjectConfig, ModuleType
from src.models.screenplay import (
    FilmConcept, CharacterCard, BeatSheet, 
    SceneOutline, Scene, Screenplay,
    ConceptsResponse, CharacterCardResponse,
    BeatSheetResponse, SceneOutlinesResponse, SceneResponse,
    OptimizationReport
)
from src.modules.senaryo import ScenarioService
from src.db import ProjectRepository, get_db
from src.models.screenplay import StoryMethodology, METHODOLOGY_DEFINITIONS, get_methodology_info

# ==================== APP SETUP ====================
app = FastAPI(
    title="🎬 AI Film Yapım Stüdyosu API",
    description="Senaryo yazımı, asset yönetimi, shotlist ve storyboard üretimi",
    version="1.0.0"
)

# CORS - Frontend erişimi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== REPOSITORY & CACHE ====================
# SQLite repository (global instance)
repo = ProjectRepository()

# RAM önbellek (performans için - SQLite her zaman source of truth)
sessions: dict[str, ProjectSession] = {}
services: dict[str, ScenarioService] = {}

# ==================== REQUEST/RESPONSE MODELS ====================
class CreateProjectRequest(BaseModel):
    name: str
    target_duration_minutes: int = 30
    language: str = "tr"
    methodology: str = "save_the_cat"  # Varsayılan Save the Cat

class SelectConceptRequest(BaseModel):
    concept_index: int
    duration_minutes: Optional[int] = None

class ReviseSceneRequest(BaseModel):
    scene_number: int
    revision_notes: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    status: str
    progress: float
    token_usage: dict
    message: str

class StatusResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# ==================== HELPER FUNCTIONS ====================
def get_session(project_id: str) -> ProjectSession:
    """Proje oturumunu al veya SQLite'tan yükle"""
    if project_id not in sessions:
        # SQLite'tan yüklemeyi dene
        try:
            sessions[project_id] = ProjectSession.load(project_id)
            logger.info(f"Session yüklendi: {project_id}")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Proje bulunamadı")
    return sessions[project_id]

def get_service(project_id: str) -> ScenarioService:
    """Senaryo servisini al veya oluştur"""
    if project_id not in services:
        session = get_session(project_id)
        services[project_id] = ScenarioService(session)
    return services[project_id]

def get_screenplay(project_id: str) -> Optional[Screenplay]:
    """Senaryoyu al (session'dan veya SQLite'tan)"""
    session = get_session(project_id)
    return session.screenplay

# ==================== PROJECT ENDPOINTS ====================
@app.post("/api/v1/projects", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest):
    """Yeni proje oluştur (SQLite'a kaydedilir)"""
    import uuid
    project_id = str(uuid.uuid4())[:8]
    
    # Metodoloji string'den enum'a çevir
    try:
        methodology = StoryMethodology(request.methodology)
    except ValueError:
        methodology = StoryMethodology.SAVE_THE_CAT
    
    config = ProjectConfig(
        target_duration_minutes=request.target_duration_minutes,
        language=request.language,
        story_methodology=methodology
    )
    
    # ProjectSession oluştur (SQLite'a kaydeder)
    session = ProjectSession(
        project_name=request.name,
        config=config,
        project_id=project_id
    )
    
    # RAM cache'e ekle
    sessions[project_id] = session
    
    method_info = get_methodology_info(methodology)
    logger.info(f"Yeni proje oluşturuldu: {project_id} - {request.name} - Metodoloji: {method_info['name']}")
    
    return ProjectResponse(
        id=project_id,
        name=session.project.name,
        status="created",
        progress=0,
        token_usage={},
        message=f"Proje '{request.name}' oluşturuldu ({method_info['name']})"
    )

@app.get("/api/v1/projects")
async def list_projects():
    """Tüm projeleri SQLite'tan listele"""
    projects_list = repo.list_projects()
    
    return {
        "projects": projects_list
    }

# ==================== METODOLOJI ENDPOINTS ====================
@app.get("/api/v1/methodologies")
async def list_methodologies():
    """Kullanılabilir hikaye metodolojilerini listele"""
    methodologies = []
    
    for method in StoryMethodology:
        info = METHODOLOGY_DEFINITIONS[method]
        methodologies.append({
            "id": method.value,
            "name": info["name"],
            "author": info["author"],
            "description": info["description"],
            "best_for": info["best_for"],
            "step_count": info["step_count"]
        })
    
    return {"methodologies": methodologies}

@app.get("/api/v1/methodologies/{methodology_id}")
async def get_methodology(methodology_id: str):
    """Belirli bir metodolojinin detaylarını al"""
    try:
        methodology = StoryMethodology(methodology_id)
        info = METHODOLOGY_DEFINITIONS[methodology]
        
        return {
            "id": methodology.value,
            "name": info["name"],
            "author": info["author"],
            "description": info["description"],
            "best_for": info["best_for"],
            "step_count": info["step_count"],
            "steps": info["steps"]
        }
    except ValueError:
        raise HTTPException(status_code=404, detail="Metodoloji bulunamadı")

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """Proje detayını SQLite'tan al"""
    try:
        session = get_session(project_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    
    screenplay = session.screenplay
    
    return {
        "project": session.project.model_dump() if hasattr(session.project, 'model_dump') else session.project.__dict__,
        "screenplay": screenplay.model_dump() if screenplay and hasattr(screenplay, 'model_dump') else None,
        "context_status": session.context.check_status()
    }

@app.delete("/api/v1/projects/{project_id}")
async def delete_project(project_id: str):
    """Projeyi SQLite ve RAM'den sil"""
    import shutil
    
    # SQLite'tan sil
    deleted = repo.delete_project(project_id)
    
    # RAM cache'den sil
    if project_id in sessions:
        del sessions[project_id]
    if project_id in services:
        del services[project_id]
    
    # Proje klasörünü de sil (dosya yüklemeleri için)
    project_dir = Path("data/projects") / project_id
    if project_dir.exists():
        try:
            shutil.rmtree(project_dir)
        except Exception as e:
            logger.warning(f"Proje klasörü silinemedi: {e}")
    
    if deleted:
        logger.info(f"Proje silindi: {project_id}")
        return {"success": True, "message": "Proje silindi"}
    else:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")

# ==================== SOURCE UPLOAD ====================
@app.post("/api/v1/projects/{project_id}/source")
async def upload_source(project_id: str, file: UploadFile = File(...)):
    """Kaynak materyal yükle"""
    from fastapi.concurrency import run_in_threadpool
    from datetime import datetime
    
    session = get_session(project_id)
    
    # Dosyayı kaydet
    data_dir = Path("data/projects") / project_id
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Dosya adına timestamp ekle (üzerine yazma sorununu önle)
    timestamp = int(datetime.now().timestamp())
    ext = Path(file.filename).suffix if '.' in file.filename else '.txt'
    safe_filename = f"source_{project_id}_{timestamp}{ext}"
    
    file_path = data_dir / safe_filename
    content = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Gemini Files API'ye yükle (thread pool'da çalıştır - event loop'u bloklamaz)
    try:
        file_uri = await run_in_threadpool(session.upload_source, str(file_path))
        
        return {
            "success": True,
            "file_name": file.filename,  # Orijinal ad göster
            "file_uri": file_uri,
            "message": "Kaynak dosya yüklendi"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SENARYO WORKFLOW ====================
@app.post("/api/v1/projects/{project_id}/senaryo/analyze")
async def analyze_source(project_id: str):
    """Kaynakı analiz et ve 3 konsept öner"""
    service = get_service(project_id)
    session = get_session(project_id)
    
    try:
        result = service.analyze_source()
        
        # Screenplay başlat veya güncelle
        if session.screenplay is None:
            session.screenplay = Screenplay(
                title=session.project.name,
                source_summary=result.source_summary,
                concepts=result.concepts
            )
        else:
            session.screenplay.concepts = result.concepts
            session.screenplay.source_summary = result.source_summary
        
        # SQLite'a kaydet
        session.save_screenplay()
        
        logger.info(f"Kaynak analiz edildi: {project_id}")
        
        return {
            "success": True,
            "concepts": [c.model_dump() for c in result.concepts],
            "source_summary": result.source_summary,
            "status": service.get_status()
        }
    except Exception as e:
        logger.error(f"Analiz hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/select-concept")
async def select_concept(project_id: str, request: SelectConceptRequest):
    """Konsept seç ve karakter kartı oluştur"""
    service = get_service(project_id)
    session = get_session(project_id)
    
    duration = request.duration_minutes or session.project.config.target_duration_minutes
    
    try:
        # Chat history sayesinde AI önceki konuşmayı hatırlıyor
        result = service.select_concept(
            concept_index=request.concept_index, 
            duration_minutes=duration
        )
        
        # Screenplay güncelle
        if session.screenplay:
            session.screenplay.selected_concept_index = request.concept_index
            session.screenplay.protagonist = result.protagonist
            session.save_screenplay()
        
        logger.info(f"Konsept seçildi: {project_id} - index {request.concept_index}")
        
        return {
            "success": True,
            "protagonist": result.protagonist.model_dump(),
            "suggested_supporting": result.suggested_supporting,
            "status": service.get_status()
        }
    except Exception as e:
        logger.error(f"Konsept seçim hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CreateBeatSheetRequest(BaseModel):
    methodology: Optional[str] = None  # Kullanıcı seçimi

@app.post("/api/v1/projects/{project_id}/senaryo/beat-sheet")
async def create_beat_sheet(project_id: str, request: CreateBeatSheetRequest = None):
    """Beat sheet oluştur (metodoloji seçilebilir)"""
    service = get_service(project_id)
    session = get_session(project_id)
    
    # Eğer metodoloji gönderildiyse proje config'ini güncelle
    if request and request.methodology:
        try:
            new_methodology = StoryMethodology(request.methodology)
            session.project.config.story_methodology = new_methodology
            logger.info(f"Metodoloji güncellendi: {project_id} - {request.methodology}")
        except ValueError:
            logger.warning(f"Geçersiz metodoloji: {request.methodology}, varsayılan kullanılıyor")
    
    try:
        # Chat history sayesinde AI önceki konuşmaları hatırlıyor
        result = service.create_beat_sheet()
        
        # Screenplay güncelle
        if session.screenplay:
            session.screenplay.beat_sheet = result.beat_sheet
            session.screenplay.methodology = session.project.config.story_methodology
            session.save_screenplay()
        
        method_info = get_methodology_info(session.project.config.story_methodology)
        logger.info(f"Beat sheet oluşturuldu: {project_id} - {method_info['name']}")
        
        return {
            "success": True,
            "beat_sheet": result.beat_sheet.model_dump(),
            "methodology": session.project.config.story_methodology.value,
            "methodology_name": method_info["name"],
            "status": service.get_status()
        }
    except Exception as e:
        logger.error(f"Beat sheet hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/projects/{project_id}/senaryo/beat-sheet")
async def update_beat_sheet(project_id: str, beat_sheet: BeatSheet):
    """Beat sheet güncelle"""
    session = get_session(project_id)
    
    if not session.screenplay:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    session.screenplay.beat_sheet = beat_sheet
    session.save_screenplay()
    
    return {"success": True, "message": "Beat sheet güncellendi"}

@app.post("/api/v1/projects/{project_id}/senaryo/scene-outline")
async def create_scene_outlines(project_id: str):
    """Zaman ayarlı sahne listesi oluştur"""
    service = get_service(project_id)
    session = get_session(project_id)
    
    try:
        result = service.create_scene_outlines()
        
        # Screenplay güncelle
        if session.screenplay:
            session.screenplay.scene_outlines = result.outlines
            session.save_screenplay()
        
        logger.info(f"Sahne listesi oluşturuldu: {project_id} - {len(result.outlines)} sahne")
        
        return {
            "success": True,
            "outlines": [o.model_dump() for o in result.outlines],
            "total_duration_seconds": result.total_duration_seconds,
            "status": service.get_status()
        }
    except Exception as e:
        logger.error(f"Sahne listesi hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/scenes/next")
async def write_next_scene(project_id: str):
    """Sıradaki sahneyi yaz"""
    service = get_service(project_id)
    session = get_session(project_id)
    screenplay = session.screenplay
    
    if not screenplay or not screenplay.scene_outlines:
        raise HTTPException(status_code=400, detail="Önce sahne listesi oluşturulmalı")
    
    try:
        result = service.write_next_scene(screenplay.scene_outlines)
        
        # Screenplay güncelle
        screenplay.scenes.append(result.scene)
        session.save_screenplay()
        
        logger.info(f"Sahne yazıldı: {project_id} - Sahne {result.scene.scene_number}")
        
        return {
            "success": True,
            "scene": result.scene.model_dump(),
            "quality_notes": result.quality_notes,
            "status": service.get_status(),
            "user_guidance": service.get_user_guidance()
        }
    except ValueError as e:
        return {"success": False, "message": str(e), "all_scenes_completed": True}
    except Exception as e:
        logger.error(f"Sahne yazma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/senaryo/scenes/next/stream")
async def write_next_scene_stream(project_id: str):
    """Sıradaki sahneyi SSE (Server-Sent Events) ile streaming olarak yaz"""
    import json
    
    session = get_session(project_id)
    service = get_service(project_id)
    screenplay = session.screenplay
    
    if not screenplay or not screenplay.scene_outlines:
        # SSE formatında hata dön
        async def error_generator():
            yield f"data: {json.dumps({'error': 'Önce sahne listesi oluşturulmalı'})}\n\n"
        return StreamingResponse(error_generator(), media_type="text/event-stream")
    
    async def event_generator():
        """SSE event generator"""
        try:
            # Streaming modunda sahne yaz
            scene_generator = service.write_next_scene(
                screenplay.scene_outlines,
                stream=True
            )
            
            full_text = ""
            for chunk in scene_generator:
                if chunk:
                    full_text += chunk
                    # SSE formatı: data: {...}\n\n
                    payload = json.dumps({"text": chunk, "type": "chunk"})
                    yield f"data: {payload}\n\n"
            
            # Final sonuç - generator'dan SceneResponse gelir
            # Ama generator protocol'ü farklı çalışıyor, result zor
            # Bu yüzden full_text'i parse etmeye çalış
            try:
                scene_data = json.loads(full_text)
                result_payload = json.dumps({
                    "type": "complete",
                    "scene": scene_data
                })
                yield f"data: {result_payload}\n\n"
                
                # Screenplay'e kaydet
                from src.models.screenplay import Scene, SceneResponse
                scene_response = SceneResponse(**scene_data)
                screenplay.scenes.append(scene_response.scene)
                session.save_screenplay()
                
            except json.JSONDecodeError:
                # Parse edilemezse raw text olarak kaydet
                logger.warning("Streaming sonucu JSON olarak parse edilemedi")
                yield f"data: {json.dumps({'type': 'complete', 'raw_text': full_text[:500]})}\n\n"
            
            # Stream sonu
            yield "data: [DONE]\n\n"
            
        except ValueError as e:
            # Tüm sahneler tamamlandı
            payload = json.dumps({"type": "complete", "message": str(e), "all_scenes_completed": True})
            yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Streaming hatası: {e}")
            payload = json.dumps({"error": str(e)})
            yield f"data: {payload}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # nginx için
        }
    )

@app.put("/api/v1/projects/{project_id}/senaryo/scenes/{scene_number}")
async def revise_scene(project_id: str, scene_number: int, request: ReviseSceneRequest):
    """Sahneyi revize et"""
    service = get_service(project_id)
    session = get_session(project_id)
    screenplay = session.screenplay
    
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    # Sahneyi bul
    scene = next((s for s in screenplay.scenes if s.scene_number == scene_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail="Sahne bulunamadı")
    
    try:
        result = service.revise_scene(scene, request.revision_notes)
        
        # Sahneyi güncelle
        for i, s in enumerate(screenplay.scenes):
            if s.scene_number == scene_number:
                screenplay.scenes[i] = result.scene
                break
        
        session.save_screenplay()
        
        return {
            "success": True,
            "scene": result.scene.model_dump(),
            "status": service.get_status()
        }
    except Exception as e:
        logger.error(f"Revizyon hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/scenes/{scene_number}/expand")
async def expand_scene(project_id: str, scene_number: int):
    """Sahneyi genişlet (2x)"""
    service = get_service(project_id)
    session = get_session(project_id)
    screenplay = session.screenplay
    
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    scene = next((s for s in screenplay.scenes if s.scene_number == scene_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail="Sahne bulunamadı")
    
    try:
        result = service.expand_scene(scene)
        
        # Sahneyi güncelle
        for i, s in enumerate(screenplay.scenes):
            if s.scene_number == scene_number:
                screenplay.scenes[i] = result.scene
                break
        
        session.save_screenplay()
        
        return {
            "success": True,
            "scene": result.scene.model_dump(),
            "status": service.get_status()
        }
    except Exception as e:
        logger.error(f"Genişletme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/scenes/{scene_number}/approve")
async def approve_scene(project_id: str, scene_number: int):
    """Sahneyi onayla"""
    session = get_session(project_id)
    screenplay = session.screenplay
    
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    for i, s in enumerate(screenplay.scenes):
        if s.scene_number == scene_number:
            screenplay.scenes[i].status = "approved"
            session.save_screenplay()
            return {"success": True, "message": f"Sahne {scene_number} onaylan dı"}
    
    raise HTTPException(status_code=404, detail="Sahne bulunamadı")

@app.post("/api/v1/projects/{project_id}/senaryo/optimize")
async def run_optimization(project_id: str):
    """Script Doctor analizi çalıştır"""
    service = get_service(project_id)
    session = get_session(project_id)
    screenplay = session.screenplay
    
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    try:
        result = service.run_optimization(screenplay)
        
        logger.info(f"Optimizasyon tamamlandı: {project_id}")
        
        return {
            "success": True,
            "report": result.model_dump(),
            "status": service.get_status()
        }
    except Exception as e:
        logger.error(f"Optimizasyon hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/senaryo/export")
async def export_screenplay(project_id: str, format: str = "json"):
    """Senaryoyu export et"""
    session = get_session(project_id)
    screenplay = session.screenplay
    
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    if format == "json":
        return screenplay.model_dump()
    elif format == "markdown":
        # Markdown formatında çıktı
        lines = [
            f"# {screenplay.title}",
            "",
            f"**Tür:** {screenplay.selected_concept.genre if screenplay.selected_concept else 'N/A'}",
            f"**Logline:** {screenplay.selected_concept.logline if screenplay.selected_concept else 'N/A'}",
            "",
            "---",
            ""
        ]
        
        for scene in screenplay.scenes:
            lines.append(f"## {scene.header}")
            lines.append("")
            lines.append(scene.action)
            
            if scene.dialogue:
                lines.append("")
                for d in scene.dialogue:
                    # Pydantic model veya dict olabilir
                    if hasattr(d, 'parenthetical'):
                        paren = f" ({d.parenthetical})" if d.parenthetical else ""
                        char_name = d.character
                        line_text = d.line
                    else:
                        paren = f" ({d.get('parenthetical')})" if d.get("parenthetical") else ""
                        char_name = d.get('character', '')
                        line_text = d.get('line', '')
                    lines.append(f"**{char_name}**{paren}")
                    lines.append(f"> {line_text}")
                    lines.append("")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return {"markdown": "\n".join(lines)}
    else:
        raise HTTPException(status_code=400, detail="Desteklenmeyen format")

# ==================== STATUS ENDPOINTS ====================
@app.get("/api/v1/projects/{project_id}/status")
async def get_status(project_id: str):
    """Proje durumunu al"""
    try:
        service = get_service(project_id)
        return service.get_status()
    except HTTPException:
        return {"status": "not_started", "progress": 0}

@app.get("/api/v1/projects/{project_id}/context")
async def get_context_status(project_id: str):
    """Bağlam durumunu al"""
    session = get_session(project_id)
    return session.context.check_status()

# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    """API sağlık kontrolü"""
    project_count = len(repo.list_projects())
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
        "projects_count": project_count,
        "database": "SQLite"
    }

# ==================== MAIN ====================
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
