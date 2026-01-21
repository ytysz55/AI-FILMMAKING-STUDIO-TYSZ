/**
 * API Client - Backend ile iletişim
 */

const API_BASE = 'http://localhost:8000/api/v1';

// ==================== TYPES ====================
export interface ApiResponse<T> {
    success: boolean;
    message?: string;
    data?: T;
    error?: string;
}

// ==================== HELPER ====================
async function fetchApi<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'API hatası' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

// ==================== PROJECT API ====================
export const projectApi = {
    // Proje oluştur (metodoloji seçimiyle)
    create: (name: string, duration: number = 30, methodology: string = 'save_the_cat') =>
        fetchApi<{ id: string; name: string; message: string }>('/projects', {
            method: 'POST',
            body: JSON.stringify({
                name,
                target_duration_minutes: duration,
                methodology: methodology
            }),
        }),

    // Projeleri listele
    list: () =>
        fetchApi<{ projects: Array<{ id: string; name: string; progress: number }> }>('/projects'),

    // Proje detayı
    get: (projectId: string) =>
        fetchApi<{ project: any; screenplay: any; context_status: any }>(`/projects/${projectId}`),

    // Proje sil
    delete: (projectId: string) =>
        fetchApi<{ success: boolean }>(`/projects/${projectId}`, { method: 'DELETE' }),
};

// ==================== METHODOLOGY API ====================
export const methodologyApi = {
    // Tüm metodolojileri listele
    list: () =>
        fetchApi<{
            methodologies: Array<{
                id: string;
                name: string;
                author: string;
                description: string;
                best_for: string[];
                step_count: number;
            }>
        }>('/methodologies'),

    // Belirli metodoloji detayı
    get: (methodologyId: string) =>
        fetchApi<{
            id: string;
            name: string;
            author: string;
            description: string;
            best_for: string[];
            step_count: number;
            steps: Array<{
                number: number;
                name: string;
                english_name: string;
                description: string;
                percentage_of_story: number;
                act: number;
            }>;
        }>(`/methodologies/${methodologyId}`),
};

// ==================== SOURCE API ====================
export const sourceApi = {
    // Kaynak dosya yükle
    upload: async (projectId: string, file: File) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/projects/${projectId}/source`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Yükleme hatası' }));
            throw new Error(error.detail);
        }

        return response.json();
    },
};

// ==================== SENARYO API ====================
export const scenarioApi = {
    // Kaynağı analiz et
    analyze: (projectId: string) =>
        fetchApi<{
            success: boolean;
            concepts: Array<{ genre: string; logline: string; tone: string }>;
            source_summary: string;
            status: any;
        }>(`/projects/${projectId}/senaryo/analyze`, { method: 'POST' }),

    // Konsept seç
    selectConcept: (projectId: string, conceptIndex: number, duration?: number) =>
        fetchApi<{
            success: boolean;
            protagonist: any;
            suggested_supporting: string[];
            status: any;
        }>(`/projects/${projectId}/senaryo/select-concept`, {
            method: 'POST',
            body: JSON.stringify({ concept_index: conceptIndex, duration_minutes: duration }),
        }),

    // Beat sheet oluştur
    createBeatSheet: (projectId: string) =>
        fetchApi<{
            success: boolean;
            beat_sheet: any;
            status: any;
        }>(`/projects/${projectId}/senaryo/beat-sheet`, { method: 'POST' }),

    // Beat sheet güncelle
    updateBeatSheet: (projectId: string, beatSheet: any) =>
        fetchApi<{ success: boolean }>(`/projects/${projectId}/senaryo/beat-sheet`, {
            method: 'PUT',
            body: JSON.stringify(beatSheet),
        }),

    // Sahne listesi oluştur
    createSceneOutlines: (projectId: string) =>
        fetchApi<{
            success: boolean;
            outlines: any[];
            total_duration_seconds: number;
            status: any;
        }>(`/projects/${projectId}/senaryo/scene-outline`, { method: 'POST' }),

    // Sonraki sahneyi yaz
    writeNextScene: (projectId: string) =>
        fetchApi<{
            success: boolean;
            scene: any;
            quality_check: any;
            status: any;
            user_guidance: string;
            all_scenes_completed?: boolean;
        }>(`/projects/${projectId}/senaryo/scenes/next`, { method: 'POST' }),

    // Streaming ile sahne yaz
    writeNextSceneStream: (projectId: string) => {
        const eventSource = new EventSource(
            `${API_BASE}/projects/${projectId}/senaryo/scenes/next/stream`
        );
        return eventSource;
    },

    // Sahneyi revize et
    reviseScene: (projectId: string, sceneNumber: number, notes: string) =>
        fetchApi<{
            success: boolean;
            scene: any;
            status: any;
        }>(`/projects/${projectId}/senaryo/scenes/${sceneNumber}`, {
            method: 'PUT',
            body: JSON.stringify({ scene_number: sceneNumber, revision_notes: notes }),
        }),

    // Sahneyi genişlet
    expandScene: (projectId: string, sceneNumber: number) =>
        fetchApi<{
            success: boolean;
            scene: any;
            status: any;
        }>(`/projects/${projectId}/senaryo/scenes/${sceneNumber}/expand`, { method: 'POST' }),

    // Sahneyi onayla
    approveScene: (projectId: string, sceneNumber: number) =>
        fetchApi<{ success: boolean; message: string }>(
            `/projects/${projectId}/senaryo/scenes/${sceneNumber}/approve`,
            { method: 'POST' }
        ),

    // Optimizasyon çalıştır
    runOptimization: (projectId: string) =>
        fetchApi<{
            success: boolean;
            report: any;
            status: any;
        }>(`/projects/${projectId}/senaryo/optimize`, { method: 'POST' }),

    // Export
    exportScreenplay: (projectId: string, format: 'json' | 'markdown' = 'json') =>
        fetchApi<any>(`/projects/${projectId}/senaryo/export?format=${format}`),
};

// ==================== STATUS API ====================
export const statusApi = {
    // Proje durumu
    getProjectStatus: (projectId: string) =>
        fetchApi<any>(`/projects/${projectId}/status`),

    // Bağlam durumu
    getContextStatus: (projectId: string) =>
        fetchApi<{
            level: 'ok' | 'warning' | 'critical';
            message: string;
            current_tokens: number;
            max_tokens: number;
            percentage: number;
        }>(`/projects/${projectId}/context`),

    // Sağlık kontrolü
    healthCheck: () =>
        fetchApi<{ status: string; api_key_configured: boolean }>('/health'),
};

// ==================== COMBINED API ====================
export const api = {
    project: projectApi,
    source: sourceApi,
    scenario: scenarioApi,
    status: statusApi,
};

export default api;
