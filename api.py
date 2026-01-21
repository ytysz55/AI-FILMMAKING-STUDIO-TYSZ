"""
FastAPI Backend - Senaryo Modülü API
"""

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

# ==================== IN-MEMORY STORAGE ====================
# Production'da veritabanı kullanılacak
projects: dict[str, Project] = {}
sessions: dict[str, ProjectSession] = {}
services: dict[str, ScenarioService] = {}
screenplays: dict[str, Screenplay] = {}

# ==================== REQUEST/RESPONSE MODELS ====================
class CreateProjectRequest(BaseModel):
    name: str
    target_duration_minutes: int = 30
    language: str = "tr"

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
    """Proje oturumunu al veya oluştur"""
    if project_id not in sessions:
        if project_id not in projects:
            raise HTTPException(status_code=404, detail="Proje bulunamadı")
        project = projects[project_id]
        sessions[project_id] = ProjectSession(
            project_name=project.name,
            config=project.config,
            project_id=project.id
        )
    return sessions[project_id]

def get_service(project_id: str) -> ScenarioService:
    """Senaryo servisini al veya oluştur"""
    if project_id not in services:
        session = get_session(project_id)
        services[project_id] = ScenarioService(session)
    return services[project_id]

# ==================== PROJECT ENDPOINTS ====================
@app.post("/api/v1/projects", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest):
    """Yeni proje oluştur"""
    import uuid
    project_id = str(uuid.uuid4())[:8]
    
    config = ProjectConfig(
        target_duration_minutes=request.target_duration_minutes,
        language=request.language
    )
    
    # ProjectSession oluştur (disk'e de kaydeder)
    session = ProjectSession(
        project_name=request.name,
        config=config,
        project_id=project_id
    )
    
    # RAM'e ekle
    projects[project_id] = session.project
    sessions[project_id] = session
    
    return ProjectResponse(
        id=project_id,
        name=session.project.name,
        status="created",
        progress=0,
        token_usage={},
        message=f"Proje '{request.name}' oluşturuldu"
    )

@app.get("/api/v1/projects")
async def list_projects():
    """Tüm projeleri listele - RAM ve disk'ten"""
    # Disk'teki projeleri de yükle (server restart durumu için)
    disk_projects = ProjectSession.list_projects()
    
    # Disk'teki projeler RAM'de yoksa yükle
    for dp in disk_projects:
        if dp["id"] not in projects:
            try:
                session = ProjectSession.load(dp["id"])
                projects[dp["id"]] = session.project
                sessions[dp["id"]] = session
                
                # Screenplay varsa RAM'e yükle
                if session.screenplay:
                    screenplays[dp["id"]] = session.screenplay
                    
            except Exception as e:
                print(f"Proje yüklenemedi: {dp['id']}, hata: {e}")
    
    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "created_at": p.created_at.isoformat() if hasattr(p, 'created_at') else None,
                "progress": p.get_module_progress(ModuleType.SENARYO).progress_percentage if hasattr(p, 'get_module_progress') else 0
            }
            for p in projects.values()
        ]
    }

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """Proje detayını al"""
    # RAM'de yoksa disk'ten yüklemeyi dene
    if project_id not in projects:
        try:
            session = ProjectSession.load(project_id)
            projects[project_id] = session.project
            sessions[project_id] = session
            if session.screenplay:
                screenplays[project_id] = session.screenplay
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Proje bulunamadı")
    
    project = projects[project_id]
    
    # Screenplay: önce screenplays dict, sonra session'dan al
    screenplay = screenplays.get(project_id)
    if not screenplay and project_id in sessions:
        screenplay = sessions[project_id].screenplay
    
    return {
        "project": project.model_dump() if hasattr(project, 'model_dump') else project.__dict__,
        "screenplay": screenplay.model_dump() if screenplay and hasattr(screenplay, 'model_dump') else None,
        "context_status": sessions[project_id].context.check_status() if project_id in sessions else None
    }

@app.delete("/api/v1/projects/{project_id}")
async def delete_project(project_id: str):
    """Projeyi sil"""
    import shutil
    
    # RAM'den sil
    if project_id in projects:
        del projects[project_id]
    if project_id in sessions:
        del sessions[project_id]
    if project_id in services:
        del services[project_id]
    if project_id in screenplays:
        del screenplays[project_id]
    
    # Disk'ten de sil
    project_dir = Path("data/projects") / project_id
    if project_dir.exists():
        try:
            shutil.rmtree(project_dir)
        except Exception as e:
            print(f"Proje klasörü silinemedi: {e}")
    
    return {"success": True, "message": "Proje silindi"}

# ==================== SOURCE UPLOAD ====================
@app.post("/api/v1/projects/{project_id}/source")
async def upload_source(project_id: str, file: UploadFile = File(...)):
    """Kaynak materyal yükle"""
    session = get_session(project_id)
    
    # Dosyayı kaydet
    data_dir = Path("data/projects") / project_id
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Dosya adını sanitize et (Türkçe karakter sorununu çöz)
    import unicodedata
    safe_filename = unicodedata.normalize('NFKD', file.filename).encode('ascii', 'ignore').decode('ascii')
    if not safe_filename:
        # Tüm karakterler filtrelendiyse basit isim kullan
        ext = Path(file.filename).suffix if '.' in file.filename else '.txt'
        safe_filename = f"source_{project_id}{ext}"
    
    file_path = data_dir / safe_filename
    content = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Gemini Files API'ye yükle
    try:
        file_uri = session.upload_source(str(file_path))
        
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
    """Kaynağı analiz et ve 3 konsept öner"""
    service = get_service(project_id)
    session = sessions.get(project_id)
    
    try:
        result = service.analyze_source()
        
        # Screenplay başlat
        if project_id not in screenplays:
            screenplays[project_id] = Screenplay(
                title=projects[project_id].name,
                source_summary=result.source_summary,
                concepts=result.concepts
            )
        else:
            screenplays[project_id].concepts = result.concepts
            screenplays[project_id].source_summary = result.source_summary
        
        # AUTO-SAVE: Disk'e kaydet
        if session:
            session.screenplay = screenplays[project_id]
            session.save_screenplay()
        
        return {
            "success": True,
            "concepts": [c.model_dump() for c in result.concepts],
            "source_summary": result.source_summary,
            "status": service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/select-concept")
async def select_concept(project_id: str, request: SelectConceptRequest):
    """Konsept seç ve karakter kartı oluştur"""
    service = get_service(project_id)
    session = sessions.get(project_id)
    
    duration = request.duration_minutes or projects[project_id].config.target_duration_minutes
    screenplay = screenplays.get(project_id)
    
    try:
        # Chat history sayesinde AI önceki konuşmayı hatırlıyor
        result = service.select_concept(
            concept_index=request.concept_index, 
            duration_minutes=duration
        )
        
        # Screenplay güncelle
        if screenplay:
            screenplay.selected_concept_index = request.concept_index
            screenplay.protagonist = result.protagonist
        
        # AUTO-SAVE: Disk'e kaydet
        if session and screenplay:
            session.screenplay = screenplay
            session.save_screenplay()
        
        return {
            "success": True,
            "protagonist": result.protagonist.model_dump(),
            "suggested_supporting": result.suggested_supporting,
            "status": service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/beat-sheet")
async def create_beat_sheet(project_id: str):
    """Beat sheet (15 vuruş) oluştur"""
    service = get_service(project_id)
    session = sessions.get(project_id)
    
    try:
        # Chat history sayesinde AI önceki konuşmaları hatırlıyor
        result = service.create_beat_sheet()
        
        # Screenplay güncelle
        if project_id in screenplays:
            screenplays[project_id].beat_sheet = result.beat_sheet
        
        # AUTO-SAVE: Disk'e kaydet
        if session and project_id in screenplays:
            session.screenplay = screenplays[project_id]
            session.save_screenplay()
        
        return {
            "success": True,
            "beat_sheet": result.beat_sheet.model_dump(),
            "status": service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/projects/{project_id}/senaryo/beat-sheet")
async def update_beat_sheet(project_id: str, beat_sheet: BeatSheet):
    """Beat sheet güncelle"""
    if project_id not in screenplays:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    screenplays[project_id].beat_sheet = beat_sheet
    
    return {"success": True, "message": "Beat sheet güncellendi"}

@app.post("/api/v1/projects/{project_id}/senaryo/scene-outline")
async def create_scene_outlines(project_id: str):
    """Zaman ayarlı sahne listesi oluştur"""
    service = get_service(project_id)
    session = sessions.get(project_id)
    
    try:
        result = service.create_scene_outlines()
        
        # Screenplay güncelle
        screenplays[project_id].scene_outlines = result.outlines
        
        # AUTO-SAVE: Disk'e kaydet
        if session:
            session.screenplay = screenplays[project_id]
            session.save_screenplay()
        
        return {
            "success": True,
            "outlines": [o.model_dump() for o in result.outlines],
            "total_duration_seconds": result.total_duration_seconds,
            "status": service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/scenes/next")
async def write_next_scene(project_id: str):
    """Sıradaki sahneyi yaz"""
    service = get_service(project_id)
    session = sessions.get(project_id)
    screenplay = screenplays.get(project_id)
    
    if not screenplay or not screenplay.scene_outlines:
        raise HTTPException(status_code=400, detail="Önce sahne listesi oluşturulmalı")
    
    try:
        result = service.write_next_scene(screenplay.scene_outlines)
        
        # Screenplay güncelle
        screenplay.scenes.append(result.scene)
        
        # AUTO-SAVE: Her sahne sonrası disk'e kaydet
        if session:
            session.screenplay = screenplay
            session.save_screenplay()
        
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/senaryo/scenes/next/stream")
async def write_next_scene_stream(project_id: str):
    """Sıradaki sahneyi streaming olarak yaz"""
    service = get_service(project_id)
    screenplay = screenplays.get(project_id)
    
    if not screenplay or not screenplay.scene_outlines:
        raise HTTPException(status_code=400, detail="Önce sahne listesi oluşturulmalı")
    
    async def generate():
        try:
            for chunk in service.write_next_scene(screenplay.scene_outlines, stream=True):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.put("/api/v1/projects/{project_id}/senaryo/scenes/{scene_number}")
async def revise_scene(project_id: str, scene_number: int, request: ReviseSceneRequest):
    """Sahneyi revize et"""
    service = get_service(project_id)
    screenplay = screenplays.get(project_id)
    
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
        
        return {
            "success": True,
            "scene": result.scene.model_dump(),
            "status": service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/scenes/{scene_number}/expand")
async def expand_scene(project_id: str, scene_number: int):
    """Sahneyi genişlet (2x)"""
    service = get_service(project_id)
    screenplay = screenplays.get(project_id)
    
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
        
        return {
            "success": True,
            "scene": result.scene.model_dump(),
            "status": service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/senaryo/scenes/{scene_number}/approve")
async def approve_scene(project_id: str, scene_number: int):
    """Sahneyi onayla"""
    screenplay = screenplays.get(project_id)
    
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    for i, s in enumerate(screenplay.scenes):
        if s.scene_number == scene_number:
            screenplay.scenes[i].status = "approved"
            return {"success": True, "message": f"Sahne {scene_number} onaylandı"}
    
    raise HTTPException(status_code=404, detail="Sahne bulunamadı")

@app.post("/api/v1/projects/{project_id}/senaryo/optimize")
async def run_optimization(project_id: str):
    """Script Doctor analizi çalıştır"""
    service = get_service(project_id)
    screenplay = screenplays.get(project_id)
    
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay bulunamadı")
    
    try:
        result = service.run_optimization(screenplay)
        
        return {
            "success": True,
            "report": result.model_dump(),
            "status": service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/senaryo/export")
async def export_screenplay(project_id: str, format: str = "json"):
    """Senaryoyu export et"""
    screenplay = screenplays.get(project_id)
    
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
    if project_id not in services:
        return {"status": "not_started", "progress": 0}
    
    service = services[project_id]
    return service.get_status()

@app.get("/api/v1/projects/{project_id}/context")
async def get_context_status(project_id: str):
    """Bağlam durumunu al"""
    session = get_session(project_id)
    return session.context.check_status()

# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    """API sağlık kontrolü"""
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
        "projects_count": len(projects)
    }

# ==================== MAIN ====================
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
