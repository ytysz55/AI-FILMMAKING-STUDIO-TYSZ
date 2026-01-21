/**
 * Zustand Store - Global State Management
 */

import { create } from 'zustand';
import type {
    Project,
    Screenplay,
    FilmConcept,
    CharacterCard,
    BeatSheet,
    SceneOutline,
    Scene,
    ContextStatus,
    WorkflowStep
} from '../types';
import api from '../services/api';

// ==================== STORE TYPES ====================
interface AppState {
    // Proje
    projects: Project[];
    currentProject: Project | null;

    // Senaryo
    screenplay: Screenplay | null;
    concepts: FilmConcept[];
    protagonist: CharacterCard | null;
    beatSheet: BeatSheet | null;
    sceneOutlines: SceneOutline[];
    scenes: Scene[];
    currentSceneIndex: number;

    // UI State
    isLoading: boolean;
    error: string | null;
    currentStep: WorkflowStep;
    streamingText: string;
    isStreaming: boolean;

    // Context
    contextStatus: ContextStatus | null;

    // Actions
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    setCurrentStep: (step: WorkflowStep) => void;

    // Project Actions
    loadProjects: () => Promise<void>;
    createProject: (name: string, duration: number) => Promise<string>;
    selectProject: (projectId: string) => Promise<void>;
    deleteProject: (projectId: string) => Promise<void>;

    // Source Actions
    uploadSource: (file: File) => Promise<void>;

    // Scenario Actions
    analyzeSource: () => Promise<void>;
    selectConcept: (index: number) => Promise<void>;
    createBeatSheet: () => Promise<void>;
    createSceneOutlines: () => Promise<void>;
    writeNextScene: (stream?: boolean) => Promise<void>;
    approveScene: (sceneNumber: number) => Promise<void>;
    expandScene: (sceneNumber: number) => Promise<void>;
    reviseScene: (sceneNumber: number, notes: string) => Promise<void>;
    runOptimization: () => Promise<void>;

    // Streaming
    setStreamingText: (text: string) => void;
    appendStreamingText: (chunk: string) => void;

    // Context
    refreshContextStatus: () => Promise<void>;

    // Reset
    reset: () => void;
}

// ==================== INITIAL STATE ====================
const initialState = {
    projects: [],
    currentProject: null,
    screenplay: null,
    concepts: [],
    protagonist: null,
    beatSheet: null,
    sceneOutlines: [],
    scenes: [],
    currentSceneIndex: 0,
    isLoading: false,
    error: null,
    currentStep: 'upload' as WorkflowStep,
    streamingText: '',
    isStreaming: false,
    contextStatus: null,
};

// ==================== STORE ====================
export const useStore = create<AppState>((set, get) => ({
    ...initialState,

    // ==================== BASIC SETTERS ====================
    setLoading: (loading) => set({ isLoading: loading }),
    setError: (error) => set({ error }),
    setCurrentStep: (step) => set({ currentStep: step }),
    setStreamingText: (text) => set({ streamingText: text }),
    appendStreamingText: (chunk) => set((state) => ({
        streamingText: state.streamingText + chunk
    })),

    // ==================== PROJECT ACTIONS ====================
    loadProjects: async () => {
        set({ isLoading: true, error: null });
        try {
            const response = await api.project.list();
            set({ projects: response.projects as unknown as Project[], isLoading: false });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
        }
    },

    createProject: async (name, duration) => {
        set({ isLoading: true, error: null });
        try {
            const response = await api.project.create(name, duration);
            await get().loadProjects();
            set({ isLoading: false });
            return response.id;
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    selectProject: async (projectId) => {
        set({ isLoading: true, error: null });
        try {
            const response = await api.project.get(projectId);

            // Mevcut duruma göre workflow adımını belirle
            let step: WorkflowStep = 'upload';
            const screenplay = response.screenplay;

            if (screenplay?.scenes && screenplay.scenes.length > 0) {
                step = 'writing';
            } else if (screenplay?.scene_outlines && screenplay.scene_outlines.length > 0) {
                step = 'scene_outline';
            } else if (screenplay?.beat_sheet) {
                step = 'beat_sheet';
            } else if (screenplay?.protagonist) {
                step = 'character_card';
            } else if (screenplay?.concepts && screenplay.concepts.length > 0) {
                step = 'select_concept';
            } else if (response.project?.source_file_uri) {
                step = 'analyze';
            }

            set({
                currentProject: response.project,
                screenplay: response.screenplay,
                scenes: response.screenplay?.scenes || [],
                sceneOutlines: response.screenplay?.scene_outlines || [],
                beatSheet: response.screenplay?.beat_sheet || null,
                protagonist: response.screenplay?.protagonist || null,
                concepts: response.screenplay?.concepts || [],
                contextStatus: response.context_status,
                isLoading: false,
                currentStep: step
            });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
        }
    },

    deleteProject: async (projectId) => {
        set({ isLoading: true, error: null });
        try {
            await api.project.delete(projectId);
            await get().loadProjects();
            if (get().currentProject?.id === projectId) {
                set({ currentProject: null, screenplay: null });
            }
            set({ isLoading: false });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
        }
    },

    // ==================== SOURCE ACTIONS ====================
    uploadSource: async (file) => {
        const { currentProject } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        set({ isLoading: true, error: null });
        try {
            await api.source.upload(currentProject.id, file);
            set({ isLoading: false, currentStep: 'analyze' });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    // ==================== SCENARIO ACTIONS ====================
    analyzeSource: async () => {
        const { currentProject } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        set({ isLoading: true, error: null });
        try {
            const response = await api.scenario.analyze(currentProject.id);
            set({
                concepts: response.concepts,
                isLoading: false,
                currentStep: 'select_concept'
            });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    selectConcept: async (index) => {
        const { currentProject } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        set({ isLoading: true, error: null });
        try {
            const response = await api.scenario.selectConcept(currentProject.id, index);
            set({
                protagonist: response.protagonist,
                isLoading: false,
                currentStep: 'character_card'
            });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    createBeatSheet: async () => {
        const { currentProject } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        set({ isLoading: true, error: null });
        try {
            const response = await api.scenario.createBeatSheet(currentProject.id);
            set({
                beatSheet: response.beat_sheet,
                isLoading: false,
                currentStep: 'beat_sheet'
            });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    createSceneOutlines: async () => {
        const { currentProject } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        set({ isLoading: true, error: null });
        try {
            const response = await api.scenario.createSceneOutlines(currentProject.id);
            set({
                sceneOutlines: response.outlines,
                isLoading: false,
                currentStep: 'scene_outline'
            });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    writeNextScene: async (stream = false) => {
        const { currentProject, scenes } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        if (stream) {
            set({ isStreaming: true, streamingText: '', error: null });

            const eventSource = api.scenario.writeNextSceneStream(currentProject.id);

            eventSource.onmessage = (event) => {
                if (event.data === '[DONE]') {
                    eventSource.close();
                    set({ isStreaming: false, currentStep: 'writing' });
                    // Sahneyi yeniden yükle
                    get().selectProject(currentProject.id);
                } else if (event.data.startsWith('[ERROR]')) {
                    eventSource.close();
                    set({ isStreaming: false, error: event.data });
                } else {
                    get().appendStreamingText(event.data);
                }
            };

            eventSource.onerror = () => {
                eventSource.close();
                set({ isStreaming: false, error: 'Streaming hatası' });
            };
        } else {
            set({ isLoading: true, error: null });
            try {
                const response = await api.scenario.writeNextScene(currentProject.id);

                if (response.all_scenes_completed) {
                    set({ isLoading: false, currentStep: 'optimization' });
                    return;
                }

                set({
                    scenes: [...scenes, response.scene],
                    currentSceneIndex: scenes.length,
                    isLoading: false,
                    currentStep: 'writing'
                });

                // Context durumunu güncelle
                get().refreshContextStatus();
            } catch (error) {
                set({ error: (error as Error).message, isLoading: false });
                throw error;
            }
        }
    },

    approveScene: async (sceneNumber) => {
        const { currentProject, scenes } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        try {
            await api.scenario.approveScene(currentProject.id, sceneNumber);

            // Local update
            const updatedScenes = scenes.map(s =>
                s.scene_number === sceneNumber ? { ...s, status: 'approved' as const } : s
            );
            set({ scenes: updatedScenes });
        } catch (error) {
            set({ error: (error as Error).message });
            throw error;
        }
    },

    expandScene: async (sceneNumber) => {
        const { currentProject } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        set({ isLoading: true, error: null });
        try {
            const response = await api.scenario.expandScene(currentProject.id, sceneNumber);

            // Sahneyi güncelle
            const { scenes } = get();
            const updatedScenes = scenes.map(s =>
                s.scene_number === sceneNumber ? response.scene : s
            );
            set({ scenes: updatedScenes, isLoading: false });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    reviseScene: async (sceneNumber, notes) => {
        const { currentProject } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        set({ isLoading: true, error: null });
        try {
            const response = await api.scenario.reviseScene(currentProject.id, sceneNumber, notes);

            // Sahneyi güncelle
            const { scenes } = get();
            const updatedScenes = scenes.map(s =>
                s.scene_number === sceneNumber ? response.scene : s
            );
            set({ scenes: updatedScenes, isLoading: false });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    runOptimization: async () => {
        const { currentProject } = get();
        if (!currentProject) throw new Error('Proje seçilmedi');

        set({ isLoading: true, error: null });
        try {
            await api.scenario.runOptimization(currentProject.id);
            set({ isLoading: false, currentStep: 'complete' });
        } catch (error) {
            set({ error: (error as Error).message, isLoading: false });
            throw error;
        }
    },

    // ==================== CONTEXT ====================
    refreshContextStatus: async () => {
        const { currentProject } = get();
        if (!currentProject) return;

        try {
            const status = await api.status.getContextStatus(currentProject.id);
            set({ contextStatus: status });
        } catch (error) {
            console.error('Context status error:', error);
        }
    },

    // ==================== RESET ====================
    reset: () => set(initialState),
}));

export default useStore;
