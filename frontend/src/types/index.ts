// API ve Model Tipleri

// ==================== PROJE ====================
export interface Project {
    id: string;
    name: string;
    config: ProjectConfig;
    source_file_uri?: string;
    source_file_name?: string;
    module_progress: ModuleProgress[];
    total_token_usage: TokenUsage;
    created_at: string;
    updated_at: string;
}

export interface ProjectConfig {
    target_duration_minutes: number;
    language: string;
    scenario_model: string;
    cache_ttl_seconds: number;
}

export interface ModuleProgress {
    module: ModuleType;
    is_started: boolean;
    is_completed: boolean;
    progress_percentage: number;
    current_step?: string;
}

export type ModuleType = 'senaryo' | 'asset' | 'shotlist' | 'storyboard';

export interface TokenUsage {
    prompt_tokens: number;
    cached_tokens: number;
    output_tokens: number;
    total_tokens: number;
}

// ==================== SENARYO ====================
export interface FilmConcept {
    genre: string;
    logline: string;
    tone: string;
    unique_selling_point?: string;
}

export interface CharacterCard {
    name: string;
    dramatic_need: string;
    point_of_view: string;
    attitude: string;
    arc: string;
    backstory?: string;
    flaws?: string[];
}

export interface Beat {
    number: number;
    name: string;
    description: string;
    estimated_duration_seconds: number;
    key_moment?: string;
}

export interface BeatSheet {
    beats: Beat[];
    total_duration_minutes: number;
}

export interface SceneOutline {
    scene_number: number;
    location: string;
    time_of_day: string;
    duration_seconds: number;
    brief_description: string;
    beat_reference?: number;
    emotional_arc?: string;
}

export interface DialogueLine {
    character: string;
    line: string;
    parenthetical?: string;
}

export interface Scene {
    scene_number: number;
    header: string;
    action: string;
    dialogue?: DialogueLine[];
    duration_seconds: number;
    status: 'draft' | 'approved' | 'revised';
    revision_count: number;
    notes?: string;
}

export interface Screenplay {
    title: string;
    concepts: FilmConcept[];
    selected_concept_index: number;
    protagonist: CharacterCard;
    beat_sheet: BeatSheet;
    scene_outlines: SceneOutline[];
    scenes: Scene[];
    total_duration_minutes: number;
    status: ProjectStatus;
}

export type ProjectStatus =
    | 'draft'
    | 'analyzing'
    | 'concept_selection'
    | 'beat_sheet'
    | 'scene_outline'
    | 'writing'
    | 'optimization'
    | 'completed';

// ==================== API RESPONSES ====================
export interface ConceptsResponse {
    concepts: FilmConcept[];
    source_summary: string;
}

export interface CharacterCardResponse {
    protagonist: CharacterCard;
    suggested_supporting?: string[];
}

export interface BeatSheetResponse {
    beat_sheet: BeatSheet;
}

export interface SceneOutlinesResponse {
    outlines: SceneOutline[];
    total_duration_seconds: number;
}

export interface SceneResponse {
    scene: Scene;
    quality_notes?: string;  // Backend'de quality_notes: Optional[str] olarak tanımlı
}

// ==================== UI STATE ====================
export interface ContextStatus {
    level: 'ok' | 'warning' | 'critical';
    message: string;
    current_tokens: number;
    max_tokens: number;
    percentage: number;
    remaining: number;
    cached_tokens: number;
    cache_ratio: number;
}

export interface AppState {
    currentProject?: Project;
    screenplay?: Screenplay;
    isLoading: boolean;
    error?: string;
    contextStatus?: ContextStatus;
}

// ==================== WORKFLOW STEPS ====================
export type WorkflowStep =
    | 'upload'
    | 'analyze'
    | 'select_concept'
    | 'character_card'
    | 'beat_sheet'
    | 'scene_outline'
    | 'writing'
    | 'optimization'
    | 'complete';

export interface StepInfo {
    id: WorkflowStep;
    title: string;
    description: string;
    icon: string;
}

export const WORKFLOW_STEPS: StepInfo[] = [
    { id: 'upload', title: 'Kaynak Yükle', description: 'PDF veya metin dosyası', icon: '📄' },
    { id: 'analyze', title: 'Analiz', description: '3 konsept önerisi', icon: '🔍' },
    { id: 'select_concept', title: 'Konsept Seç', description: 'Tür ve süre belirle', icon: '🎬' },
    { id: 'character_card', title: 'Karakter', description: 'Protagonist kimliği', icon: '👤' },
    { id: 'beat_sheet', title: 'Beat Sheet', description: '15 vuruşluk iskelet', icon: '📋' },
    { id: 'scene_outline', title: 'Sahneler', description: 'Zaman etiketli liste', icon: '🎭' },
    { id: 'writing', title: 'Yazım', description: 'Sahne sahne üretim', icon: '✍️' },
    { id: 'optimization', title: 'Optimizasyon', description: 'Script Doctor', icon: '🔧' },
    { id: 'complete', title: 'Tamamlandı', description: 'Export hazır', icon: '✅' },
];
