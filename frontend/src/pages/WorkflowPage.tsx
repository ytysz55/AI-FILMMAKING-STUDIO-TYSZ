/**
 * Senaryo Workflow Sayfası
 * Kaynak yükleme → Analiz → Konsept → Beat Sheet → Sahne Yazımı
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { ScenarioEditor } from '../components/scenario';
import type { FilmConcept } from '../types';
import { methodologyApi } from '../services/api';
import './WorkflowPage.css';

export default function WorkflowPage() {
    const {
        concepts,
        protagonist,
        beatSheet,
        sceneOutlines,
        scenes,
        currentStep,
        isLoading,
        error,
        isStreaming,
        streamingText,
        uploadSource,
        analyzeSource,
        selectConcept,
        createBeatSheet,
        createSceneOutlines,
        writeNextScene,
        approveScene,
        expandScene,
        reviseScene,
        setCurrentStep,
    } = useStore();

    const [selectedConcept, setSelectedConcept] = useState<number | null>(null);
    const [reviseNotes, setReviseNotes] = useState('');
    const [reviseSceneNumber, setReviseSceneNumber] = useState<number | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Metodoloji seçimi için state
    const [methodologies, setMethodologies] = useState<Array<{
        id: string;
        name: string;
        author: string;
        description: string;
        best_for: string[];
        step_count: number;
    }>>([]);
    const [selectedMethodology, setSelectedMethodology] = useState<string>('save_the_cat');
    const [showMethodologySelector, setShowMethodologySelector] = useState(false);

    // Metodolojileri yükle
    useEffect(() => {
        methodologyApi.list().then(res => {
            setMethodologies(res.methodologies);
        }).catch(console.error);
    }, []);

    // ==================== HANDLERS ====================
    const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            await uploadSource(file);
        } catch (err) {
            console.error('Yükleme hatası:', err);
        }
    }, [uploadSource]);

    const handleAnalyze = useCallback(async () => {
        try {
            await analyzeSource();
        } catch (err) {
            console.error('Analiz hatası:', err);
        }
    }, [analyzeSource]);

    const handleSelectConcept = useCallback(async () => {
        if (selectedConcept === null) return;
        try {
            await selectConcept(selectedConcept);
        } catch (err) {
            console.error('Konsept seçim hatası:', err);
        }
    }, [selectedConcept, selectConcept]);

    const handleCreateBeatSheet = useCallback(async () => {
        try {
            await createBeatSheet(selectedMethodology);
        } catch (err) {
            console.error('Beat sheet hatası:', err);
        }
    }, [createBeatSheet, selectedMethodology]);

    const handleCreateOutlines = useCallback(async () => {
        try {
            await createSceneOutlines();
        } catch (err) {
            console.error('Outline hatası:', err);
        }
    }, [createSceneOutlines]);

    const handleWriteScene = useCallback(async (stream = false) => {
        try {
            await writeNextScene(stream);
        } catch (err) {
            console.error('Sahne yazım hatası:', err);
        }
    }, [writeNextScene]);

    const handleApprove = useCallback(async (sceneNumber: number) => {
        try {
            await approveScene(sceneNumber);

            // Onayladıktan sonra hala yazılacak sahne varsa otomatik yaz
            // scenes.length onay anında mevcut sahne sayısı (henüz güncellenmemiş olabilir)
            // sceneOutlines.length ise toplam outline sayısı
            // Son yazılan sahne = scenes.length (1-indexed için scenes.length yazıldı demek)
            // Eğer scenes.length < sceneOutlines.length ise hala yazılacak sahne var
            if (sceneOutlines.length > 0 && scenes.length < sceneOutlines.length) {
                // Yeni sahne yaz
                await writeNextScene(false);
            }
        } catch (err) {
            console.error('Onay hatası:', err);
        }
    }, [approveScene, writeNextScene, scenes.length, sceneOutlines.length]);

    const handleExpand = useCallback(async (sceneNumber: number) => {
        try {
            await expandScene(sceneNumber);
        } catch (err) {
            console.error('Genişletme hatası:', err);
        }
    }, [expandScene]);

    const handleRevise = useCallback(async () => {
        if (reviseSceneNumber === null || !reviseNotes) return;
        try {
            await reviseScene(reviseSceneNumber, reviseNotes);
            setReviseNotes('');
            setReviseSceneNumber(null);
        } catch (err) {
            console.error('Revizyon hatası:', err);
        }
    }, [reviseSceneNumber, reviseNotes, reviseScene]);

    // ==================== RENDER STEPS ====================
    const renderUploadStep = () => (
        <div className="workflow-step animate-fade-in">
            <div className="step-header">
                <span className="step-icon">📄</span>
                <h2>Kaynak Materyal Yükle</h2>
                <p>PDF, TXT veya DOCX formatında kaynak dosyanızı yükleyin</p>
            </div>

            <div className="upload-area" onClick={() => fileInputRef.current?.click()}>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.txt,.docx,.md"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                />
                <div className="upload-content">
                    <span className="upload-icon">📁</span>
                    <p className="upload-text">Dosya seçmek için tıklayın veya sürükleyip bırakın</p>
                    <span className="upload-hint">PDF, TXT, DOCX, MD • Maks 50MB</span>
                </div>
            </div>

            <div className="step-actions">
                <button
                    className="btn btn-secondary"
                    onClick={() => setCurrentStep('analyze')}
                >
                    Demo ile Devam Et
                </button>
            </div>
        </div>
    );

    const renderAnalyzeStep = () => (
        <div className="workflow-step animate-fade-in">
            <div className="step-header">
                <span className="step-icon">🔍</span>
                <h2>Kaynak Analizi</h2>
                <p>AI, kaynağınızı analiz edip 3 farklı film konsepti önerecek</p>
            </div>

            {concepts.length === 0 ? (
                <div className="action-center">
                    <button
                        className="btn btn-primary btn-lg"
                        onClick={handleAnalyze}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <>
                                <span className="loading-spinner small" />
                                Analiz Ediliyor...
                            </>
                        ) : (
                            <>
                                <span>🔍</span>
                                Analiz Et
                            </>
                        )}
                    </button>
                </div>
            ) : (
                <>
                    <div className="concepts-grid">
                        {concepts.map((concept: FilmConcept, index: number) => (
                            <div
                                key={index}
                                className={`concept-card ${selectedConcept === index ? 'selected' : ''}`}
                                onClick={() => setSelectedConcept(index)}
                            >
                                <div className="concept-badge">{concept.genre}</div>
                                <h3 className="concept-title">Konsept {index + 1}</h3>
                                <p className="concept-logline">{concept.logline}</p>
                                <div className="concept-meta">
                                    <span className="concept-tone">🎭 {concept.tone}</span>
                                </div>
                                {selectedConcept === index && (
                                    <div className="concept-selected-badge">✓ Seçildi</div>
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="step-actions">
                        <button
                            className="btn btn-primary btn-lg"
                            onClick={handleSelectConcept}
                            disabled={selectedConcept === null || isLoading}
                        >
                            {isLoading ? 'İşleniyor...' : 'Konsepti Seç ve Devam Et'}
                        </button>
                    </div>
                </>
            )}
        </div>
    );

    const renderCharacterStep = () => (
        <div className="workflow-step animate-fade-in">
            <div className="step-header">
                <span className="step-icon">👤</span>
                <h2>Karakter Kimlik Kartı</h2>
                <p>Ana karakterin psikolojik profili ve dramatik yayı</p>
            </div>

            {protagonist ? (
                <div className="character-card">
                    <h3 className="character-name">{protagonist.name}</h3>

                    <div className="character-fields">
                        <div className="character-field">
                            <span className="field-icon">🎯</span>
                            <div>
                                <label>Dramatik İhtiyaç</label>
                                <p>{protagonist.dramatic_need}</p>
                            </div>
                        </div>

                        <div className="character-field">
                            <span className="field-icon">👁️</span>
                            <div>
                                <label>Bakış Açısı</label>
                                <p>{protagonist.point_of_view}</p>
                            </div>
                        </div>

                        <div className="character-field">
                            <span className="field-icon">💪</span>
                            <div>
                                <label>Tavır</label>
                                <p>{protagonist.attitude}</p>
                            </div>
                        </div>

                        <div className="character-field">
                            <span className="field-icon">🔄</span>
                            <div>
                                <label>Değişim Yayı</label>
                                <p>{protagonist.arc}</p>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="loading-state">
                    <div className="loading-spinner" />
                    <span>Karakter oluşturuluyor...</span>
                </div>
            )}

            <div className="step-actions">
                <button
                    className="btn btn-primary btn-lg"
                    onClick={handleCreateBeatSheet}
                    disabled={!protagonist || isLoading}
                >
                    {isLoading ? 'İşleniyor...' : 'Beat Sheet Oluştur'}
                </button>
            </div>

            {/* Metodoloji Seçici */}
            {showMethodologySelector && (
                <div className="methodology-selector">
                    <h3>📚 Hikaye Metodolojisi Seçin</h3>
                    <p>Film yapısını belirleyecek yaklaşımı seçin:</p>

                    <div className="methodology-grid">
                        {methodologies.map((method) => (
                            <div
                                key={method.id}
                                className={`methodology-card ${selectedMethodology === method.id ? 'selected' : ''}`}
                                onClick={() => setSelectedMethodology(method.id)}
                            >
                                <div className="methodology-header">
                                    <h4>{method.name}</h4>
                                    <span className="step-badge">{method.step_count} adım</span>
                                </div>
                                <p className="methodology-author">— {method.author}</p>
                                <p className="methodology-desc">{method.description}</p>
                                <div className="methodology-tags">
                                    {method.best_for.map((tag, i) => (
                                        <span key={i} className="tag">{tag}</span>
                                    ))}
                                </div>
                                {selectedMethodology === method.id && (
                                    <div className="selected-badge">✓ Seçildi</div>
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="step-actions">
                        <button
                            className="btn btn-primary btn-lg"
                            onClick={() => {
                                setShowMethodologySelector(false);
                                handleCreateBeatSheet();
                            }}
                            disabled={isLoading}
                        >
                            {isLoading ? 'İşleniyor...' : `${methodologies.find(m => m.id === selectedMethodology)?.name || 'Beat Sheet'} ile Devam Et`}
                        </button>
                    </div>
                </div>
            )}

            {!showMethodologySelector && (
                <div className="step-actions">
                    <button
                        className="btn btn-primary btn-lg"
                        onClick={() => setShowMethodologySelector(true)}
                        disabled={!protagonist || isLoading}
                    >
                        {isLoading ? 'İşleniyor...' : '📚 Metodoloji Seç ve Devam Et'}
                    </button>
                </div>
            )}
        </div>
    );

    const renderBeatSheetStep = () => {
        const currentMethodology = methodologies.find(m => m.id === beatSheet?.methodology) ||
            methodologies.find(m => m.id === selectedMethodology);
        const stepCount = currentMethodology?.step_count || beatSheet?.beats?.length || 15;
        const methodName = currentMethodology?.name || 'Beat Sheet';

        return (
            <div className="workflow-step animate-fade-in">
                <div className="step-header">
                    <span className="step-icon">📋</span>
                    <h2>Beat Sheet ({stepCount} Vuruş)</h2>
                    <p>{methodName} metodolojisi ile hikaye iskeleti</p>
                </div>

                {beatSheet ? (
                    <div className="beat-sheet">
                        <div className="beat-sheet-header">
                            <span>Toplam Süre: {beatSheet.total_duration_minutes} dakika</span>
                        </div>

                        <div className="beats-list">
                            {beatSheet.beats.map((beat, index) => (
                                <div key={index} className="beat-item">
                                    <div className="beat-number">{beat.number}</div>
                                    <div className="beat-content">
                                        <h4 className="beat-name">{beat.name}</h4>
                                        <p className="beat-description">{beat.description}</p>
                                        <span className="beat-duration">
                                            ⏱️ {Math.floor(beat.estimated_duration_seconds / 60)}:{(beat.estimated_duration_seconds % 60).toString().padStart(2, '0')}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="loading-state">
                        <div className="loading-spinner" />
                        <span>Beat sheet oluşturuluyor...</span>
                    </div>
                )}

                <div className="step-actions">
                    <button
                        className="btn btn-primary btn-lg"
                        onClick={handleCreateOutlines}
                        disabled={!beatSheet || isLoading}
                    >
                        {isLoading ? 'İşleniyor...' : 'Sahne Listesi Oluştur'}
                    </button>
                </div>
            </div>
        );
    };

    const renderSceneOutlineStep = () => (
        <div className="workflow-step animate-fade-in">
            <div className="step-header">
                <span className="step-icon">🎭</span>
                <h2>Zaman Ayarlı Sahne Listesi</h2>
                <p>Her sahne için hedef süre belirlenmiş prodüksiyon planı</p>
            </div>

            {sceneOutlines.length > 0 ? (
                <div className="scene-outlines">
                    <div className="outlines-header">
                        <span>Toplam: {sceneOutlines.length} sahne</span>
                        <span>
                            Süre: {Math.floor(sceneOutlines.reduce((a, s) => a + s.duration_seconds, 0) / 60)} dk
                        </span>
                    </div>

                    <div className="outlines-table">
                        <div className="table-header">
                            <span>#</span>
                            <span>Mekan</span>
                            <span>Zaman</span>
                            <span>Süre</span>
                            <span>Açıklama</span>
                        </div>
                        {sceneOutlines.map((outline) => (
                            <div key={outline.scene_number} className="table-row">
                                <span className="row-number">{outline.scene_number}</span>
                                <span className="row-location">{outline.location}</span>
                                <span className="row-time">{outline.time_of_day}</span>
                                <span className="row-duration">{outline.duration_seconds}s</span>
                                <span className="row-desc">{outline.brief_description}</span>
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <div className="loading-state">
                    <div className="loading-spinner" />
                    <span>Sahne listesi oluşturuluyor...</span>
                </div>
            )}

            <div className="step-actions">
                <button
                    className="btn btn-primary btn-lg"
                    onClick={() => handleWriteScene(false)}
                    disabled={sceneOutlines.length === 0 || isLoading}
                >
                    {isLoading ? 'İşleniyor...' : '✍️ Yazmaya Başla'}
                </button>
            </div>
        </div>
    );

    const renderWritingStep = () => (
        <div className="workflow-step writing-step animate-fade-in">
            <ScenarioEditor
                sceneOutlines={sceneOutlines}
                scenes={scenes}
                currentSceneIndex={scenes.length}
                isWriting={isStreaming || isLoading}
                streamingText={streamingText}
                onApprove={handleApprove}
                onExpand={handleExpand}
                onRevise={(num, notes) => {
                    setReviseSceneNumber(num);
                    setReviseNotes(notes);
                    handleRevise();
                }}
                onContinue={() => handleWriteScene(false)}
            />
        </div>
    );

    // ==================== STEP NAVIGATION ====================
    const steps = [
        { id: 'upload', label: 'Yükle', icon: '📄' },
        { id: 'analyze', label: 'Analiz', icon: '🔍' },
        { id: 'character_card', label: 'Karakter', icon: '👤' },
        { id: 'beat_sheet', label: 'Beat Sheet', icon: '📋' },
        { id: 'scene_outline', label: 'Sahneler', icon: '🎭' },
        { id: 'writing', label: 'Yazım', icon: '✍️' },
    ];

    const currentStepIndex = steps.findIndex(s => s.id === currentStep);

    // ==================== MAIN RENDER ====================
    return (
        <div className="workflow-page">
            {/* Step Navigation */}
            <div className="step-navigation">
                {steps.map((step, index) => (
                    <div
                        key={step.id}
                        className={`step-nav-item ${currentStep === step.id ? 'active' : ''} ${index < currentStepIndex ? 'completed' : ''}`}
                    >
                        <span className="step-nav-icon">{index < currentStepIndex ? '✓' : step.icon}</span>
                        <span className="step-nav-label">{step.label}</span>
                    </div>
                ))}
            </div>

            {/* Error Display */}
            {error && (
                <div className="error-banner">
                    <span>⚠️</span>
                    {error}
                </div>
            )}

            {/* Step Content */}
            <div className="workflow-content">
                {currentStep === 'upload' && renderUploadStep()}
                {(currentStep === 'analyze' || currentStep === 'select_concept') && renderAnalyzeStep()}
                {currentStep === 'character_card' && renderCharacterStep()}
                {currentStep === 'beat_sheet' && renderBeatSheetStep()}
                {currentStep === 'scene_outline' && renderSceneOutlineStep()}
                {currentStep === 'writing' && renderWritingStep()}
            </div>
        </div>
    );
}
