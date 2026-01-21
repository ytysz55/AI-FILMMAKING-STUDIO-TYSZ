"""
Senaryo yazım servisi.
Ana iş mantığını içerir.
"""

from typing import Optional, Generator
from pathlib import Path

from ...core.session import ProjectSession
from ...core.context_manager import ContextManager
from ...models.project import ModuleType, TokenUsage
from ...models.screenplay import (
    Screenplay,
    FilmConcept,
    CharacterCard,
    BeatSheet,
    SceneOutline,
    Scene,
    ConceptsResponse,
    CharacterCardResponse,
    BeatSheetResponse,
    SceneOutlinesResponse,
    SceneResponse,
    OptimizationReport,
    ProjectStatus,
    StoryMethodology,
    get_methodology_info,
    get_methodology_steps
)
from .prompts import SYSTEM_PROMPT, STEP_PROMPTS, USER_GUIDANCE


class ScenarioService:
    """
    Senaryo yazım servisi.
    Tüm senaryo yazım akışını yönetir.
    """
    
    def __init__(self, session: ProjectSession):
        """
        ScenarioService başlat.
        
        Args:
            session: Aktif proje oturumu
        """
        self.session = session
        self.module = ModuleType.SENARYO
        
        # Durum takibi
        self._current_step = "init"
        self._current_scene_index = 0
        
    # ==================== ADIM 1: ANALİZ ====================
    
    def analyze_source(self) -> ConceptsResponse:
        """
        Kaynak materyali analiz et ve 3 konsept öner.
        
        Returns:
            ConceptsResponse (3 film konsepti)
        """
        # Cache oluştur (yoksa)
        cache_id = f"{self.session.project_id}_{self.module.value}"
        if not self.session.gemini.get_cache(cache_id):
            self.session.create_module_cache(
                module=self.module,
                system_prompt=SYSTEM_PROMPT
            )
        
        # Chat başlat
        self.session.start_module_chat(
            module=self.module,
            cache_id=cache_id
        )
        
        # Analiz promptu gönder
        result = self.session.generate_structured(
            module=self.module,
            prompt=STEP_PROMPTS["analyze"],
            response_schema=ConceptsResponse,
            cache_id=cache_id
        )
        
        # Durumu güncelle
        self._current_step = "concepts_generated"
        self.session.update_progress(self.module, 10, "Konseptler oluşturuldu")
        
        return result
    
    def select_concept(
        self,
        concept_index: int,
        duration_minutes: int
    ) -> CharacterCardResponse:
        """
        Konsept seç ve karakter kartı oluştur.
        
        Chat history sayesinde AI önceki konuşmayı (konseptleri) hatırlıyor.
        
        Args:
            concept_index: Seçilen konsept indeksi (0-2)
            duration_minutes: Hedef film süresi
            
        Returns:
            CharacterCardResponse (karakter kartı)
        """
        # Proje config güncelle
        self.session.project.config.target_duration_minutes = duration_minutes
        
        # Prompt'u doldur (sadece seçili konsept index ve süre)
        character_prompt = STEP_PROMPTS["character_card"].format(
            concept_index=concept_index + 1,  # 1-indexed göster
            duration_minutes=duration_minutes
        )
        
        # Karakter kartı oluştur - Chat history'den önceki konuşmalar alınacak
        result = self.session.generate_structured(
            module=self.module,
            prompt=character_prompt,
            response_schema=CharacterCardResponse
        )
        
        self._current_step = "character_created"
        self.session.update_progress(self.module, 20, "Karakter kartı oluşturuldu")
        
        return result
    
    # ==================== ADIM 2: BEAT SHEET ====================
    
    def create_beat_sheet(self) -> BeatSheetResponse:
        """
        Hikaye iskeletini oluştur.
        Metodolojiye göre farklı adım sayısı ve yapı kullanılır.
        
        Chat history sayesinde AI önceki konuşmaları (konsept, karakter) hatırlıyor.
        
        Returns:
            BeatSheetResponse
        """
        duration = self.session.project.config.target_duration_minutes
        methodology = self.session.project.config.story_methodology
        
        # Metodoloji bilgilerini al
        method_info = get_methodology_info(methodology)
        method_steps = get_methodology_steps(methodology)
        
        # Adımları formatla
        steps_text = "\n".join([
            f"  {s['number']}. {s['name']} ({s['english_name']}): {s['description']}"
            for s in method_steps
        ])
        
        prompt = STEP_PROMPTS["beat_sheet"].format(
            methodology_name=method_info["name"],
            methodology_description=method_info["description"],
            step_count=method_info["step_count"],
            duration=duration,
            methodology_steps=f"Adımlar:\n{steps_text}"
        )
        
        result = self.session.generate_structured(
            module=self.module,
            prompt=prompt,
            response_schema=BeatSheetResponse
        )
        
        self._current_step = "beat_sheet_created"
        self.session.update_progress(self.module, 30, f"Beat sheet oluşturuldu ({method_info['name']})")
        
        return result
    
    # ==================== ADIM 3: SAHNE LİSTESİ ====================
    
    def create_scene_outlines(self) -> SceneOutlinesResponse:
        """
        Zaman ayarlı sahne listesi oluştur.
        
        Returns:
            SceneOutlinesResponse
        """
        duration = self.session.project.config.target_duration_minutes
        total_seconds = duration * 60
        
        prompt = STEP_PROMPTS["scene_outline"].format(
            duration=duration,
            total_seconds=total_seconds
        )
        
        result = self.session.generate_structured(
            module=self.module,
            prompt=prompt,
            response_schema=SceneOutlinesResponse
        )
        
        self._current_step = "outlines_created"
        self.session.update_progress(self.module, 40, "Sahne listesi oluşturuldu")
        
        return result
    
    # ==================== ADIM 4: SAHNE YAZIMI ====================
    
    def write_next_scene(
        self,
        scene_outlines: list[SceneOutline],
        stream: bool = False
    ) -> SceneResponse | Generator[str, None, SceneResponse]:
        """
        Sıradaki sahneyi yaz.
        
        Args:
            scene_outlines: Sahne outline listesi
            stream: Streaming yanıt mı
            
        Returns:
            SceneResponse veya Generator (stream=True ise)
        """
        if self._current_scene_index >= len(scene_outlines):
            raise ValueError("Tüm sahneler yazıldı!")
        
        outline = scene_outlines[self._current_scene_index]
        
        prompt = STEP_PROMPTS["write_scene"].format(
            scene_number=outline.scene_number,
            location=outline.location,
            time_of_day=outline.time_of_day,
            duration_seconds=outline.duration_seconds,
            description=outline.brief_description
        )
        
        if stream:
            return self._write_scene_streaming(outline, prompt, len(scene_outlines))
        
        result = self.session.generate_structured(
            module=self.module,
            prompt=prompt,
            response_schema=SceneResponse
        )
        
        self._current_scene_index += 1
        self._update_scene_progress(len(scene_outlines))
        
        return result
    
    def _write_scene_streaming(
        self,
        outline: SceneOutline,
        prompt: str,
        total_scenes: int
    ) -> Generator[str, None, SceneResponse]:
        """
        Streaming modunda sahne yaz.
        
        Yields:
            str: Metin parçaları
            
        Returns:
            SceneResponse: Final sonuç
        """
        # Streaming için chat API kullan
        full_text = ""
        
        # generate_content_stream metodunu kullan
        model = self.session.project.config.scenario_model.value
        cache_id = f"{self.session.project_id}_{self.module.value}"
        
        for chunk in self.session.gemini.generate_content_stream(
            model=model,
            prompt=prompt,
            cache_id=cache_id
        ):
            full_text += chunk
            yield chunk
        
        # Sonucu parse et
        import json
        try:
            scene_data = json.loads(full_text)
            result = SceneResponse(**scene_data)
        except (json.JSONDecodeError, Exception):
            # Fallback: Manuel oluştur
            result = SceneResponse(
                scene=Scene(
                    scene_number=outline.scene_number,
                    header=f"SCENE {outline.scene_number}: {outline.location} - {outline.time_of_day} - [SÜRE: {outline.duration_seconds} Saniye]",
                    action=full_text,
                    duration_seconds=outline.duration_seconds,
                    status="draft",
                    revision_count=0
                )
            )
        
        self._current_scene_index += 1
        self._update_scene_progress(total_scenes)
        
        return result
    
    def _update_scene_progress(self, total_scenes: int):
        """İlerleme durumunu güncelle"""
        base_progress = 40  # Outline'a kadar
        scene_progress = 50  # Sahneler için ayrılan
        progress = base_progress + (scene_progress * self._current_scene_index / total_scenes)
        
        self.session.update_progress(
            self.module,
            progress,
            f"Sahne {self._current_scene_index}/{total_scenes} yazıldı"
        )
    
    def expand_scene(self, scene: Scene) -> SceneResponse:
        """
        Mevcut sahneyi genişlet (2x).
        
        Args:
            scene: Genişletilecek sahne
            
        Returns:
            SceneResponse (genişletilmiş sahne)
        """
        new_duration = scene.duration_seconds * 2
        
        prompt = STEP_PROMPTS["expand_scene"].format(
            current_scene=scene.model_dump_json(),
            new_duration=new_duration
        )
        
        result = self.session.generate_structured(
            module=self.module,
            prompt=prompt,
            response_schema=SceneResponse
        )
        
        return result
    
    def revise_scene(
        self,
        scene: Scene,
        revision_notes: str
    ) -> SceneResponse:
        """
        Sahneyi revize et.
        
        Args:
            scene: Revize edilecek sahne
            revision_notes: Revizyon notları
            
        Returns:
            SceneResponse
        """
        prompt = STEP_PROMPTS["revise_scene"].format(
            current_scene=scene.model_dump_json(),
            revision_notes=revision_notes
        )
        
        result = self.session.generate_structured(
            module=self.module,
            prompt=prompt,
            response_schema=SceneResponse
        )
        
        # Revizyon sayısını artır
        result.scene.revision_count = scene.revision_count + 1
        
        return result
    
    def quality_check(self, scene: Scene) -> dict:
        """
        Sahneyi kalite kontrolünden geçir.
        
        Args:
            scene: Kontrol edilecek sahne
            
        Returns:
            Kalite raporu (issues, score, suggestions)
        """
        prompt = STEP_PROMPTS["quality_check"].format(
            scene=scene.model_dump_json(),
            target_duration=scene.duration_seconds
        )
        
        # Basit dict olarak döndür (özel model gerekmez)
        result, usage = self.session.send_message(self.module, prompt)
        
        # JSON parse et
        import json
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "issues": [],
                "score": 0,
                "suggestions": ["Kalite kontrolü yapılamadı"],
                "raw_response": result
            }
    
    # ==================== ADIM 5: OPTİMİZASYON ====================
    
    def run_optimization(self, screenplay: Screenplay) -> OptimizationReport:
        """
        Script Doctor analizi çalıştır.
        
        Args:
            screenplay: Analiz edilecek senaryo
            
        Returns:
            OptimizationReport
        """
        # Senaryo metnini hazırla
        screenplay_text = self._format_screenplay_for_analysis(screenplay)
        
        prompt = STEP_PROMPTS["optimization"].format(
            screenplay=screenplay_text
        )
        
        result = self.session.generate_structured(
            module=self.module,
            prompt=prompt,
            response_schema=OptimizationReport
        )
        
        self.session.update_progress(self.module, 95, "Optimizasyon tamamlandı")
        
        return result
    
    # ==================== YARDIMCI METODLAR ====================
    
    def get_status(self) -> dict:
        """Mevcut durumu döndür"""
        return {
            "current_step": self._current_step,
            "current_scene_index": self._current_scene_index,
            "progress": self.session.project.get_module_progress(self.module),
            "context_status": self.session.context.check_status()
        }
    
    def get_user_guidance(self) -> str:
        """Kullanıcı yönlendirme metnini döndür"""
        return USER_GUIDANCE
    
    def _format_screenplay_for_analysis(self, screenplay: Screenplay) -> str:
        """Senaryoyu analiz için metin formatına çevir"""
        lines = [
            f"# {screenplay.title}",
            f"Tür: {screenplay.selected_concept.genre}",
            f"Logline: {screenplay.selected_concept.logline}",
            "",
            "## SAHNELER",
            ""
        ]
        
        for scene in screenplay.scenes:
            lines.append(scene.header)
            lines.append("")
            lines.append(scene.action)
            
            if scene.dialogue:
                lines.append("")
                for d in scene.dialogue:
                    # Pydantic model veya dict olabilir, her iki durumu da destekle
                    if hasattr(d, 'parenthetical'):
                        paren = f" ({d.parenthetical})" if d.parenthetical else ""
                        char_name = d.character
                        line_text = d.line
                    else:
                        paren = f" ({d.get('parenthetical')})" if d.get("parenthetical") else ""
                        char_name = d.get('character', '')
                        line_text = d.get('line', '')
                    lines.append(f"{char_name}{paren}")
                    lines.append(f"    {line_text}")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def finalize(self) -> Path:
        """
        Senaryo yazımını tamamla ve kaydet.
        
        Returns:
            Kaydedilen dosya yolu
        """
        self.session.update_progress(self.module, 100, "Tamamlandı")
        
        if self.session.screenplay:
            self.session.screenplay.status = ProjectStatus.COMPLETED
            return self.session.save_screenplay()
        
        raise ValueError("Kaydedilecek senaryo yok")
