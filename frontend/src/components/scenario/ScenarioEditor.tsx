import { useState } from 'react';
import type { Scene, SceneOutline } from '../../types';
import SceneCard from './SceneCard';
import SceneWriter from './SceneWriter';
import './ScenarioEditor.css';

interface ScenarioEditorProps {
    sceneOutlines: SceneOutline[];
    scenes: Scene[];
    currentSceneIndex: number;
    isWriting?: boolean;
    streamingText?: string;
    onApprove?: (sceneNumber: number) => void;
    onExpand?: (sceneNumber: number) => void;
    onRevise?: (sceneNumber: number, notes: string) => void;
    onContinue?: () => void;
}

export default function ScenarioEditor({
    sceneOutlines,
    scenes,
    currentSceneIndex,
    isWriting = false,
    streamingText = '',
    onApprove,
    onExpand,
    onRevise,
    onContinue,
}: ScenarioEditorProps) {
    const [selectedScene, setSelectedScene] = useState<number | null>(null);
    const [reviseNotes, setReviseNotes] = useState('');
    const [showReviseModal, setShowReviseModal] = useState(false);
    const [reviseSceneNumber, setReviseSceneNumber] = useState<number | null>(null);

    // Veri yoksa boş durum göster
    if (!sceneOutlines || sceneOutlines.length === 0) {
        return (
            <div className="scenario-editor scenario-editor-empty">
                <div className="empty-state">
                    <span className="empty-icon">📝</span>
                    <h3>Sahne Listesi Bekleniyor</h3>
                    <p>Önce sahne listesi oluşturulmalı.</p>
                </div>
            </div>
        );
    }

    const completedScenesCount = scenes?.length || 0;
    const totalScenes = sceneOutlines.length;
    const progress = totalScenes > 0 ? (completedScenesCount / totalScenes) * 100 : 0;

    // Süre hesaplamaları
    const completedDuration = scenes?.reduce((acc, s) => acc + (s.duration_seconds || 0), 0) || 0;
    const totalDuration = sceneOutlines.reduce((acc, s) => acc + (s.duration_seconds || 0), 0);

    // Mevcut sahne
    const currentOutline = sceneOutlines[currentSceneIndex];
    const lastScene = scenes?.[scenes.length - 1];

    // Status badge
    const getStatusBadge = () => {
        if (isWriting) return <span className="status-badge status-badge-warning">Yazılıyor...</span>;
        if (completedScenesCount >= totalScenes) return <span className="status-badge status-badge-success">Tamamlandı</span>;
        return <span className="status-badge status-badge-info">Devam Ediyor</span>;
    };

    // Revize modal
    const handleOpenRevise = (sceneNumber: number) => {
        setReviseSceneNumber(sceneNumber);
        setReviseNotes('');
        setShowReviseModal(true);
    };

    const handleReviseSubmit = () => {
        if (reviseSceneNumber && reviseNotes && onRevise) {
            onRevise(reviseSceneNumber, reviseNotes);
            setShowReviseModal(false);
            setReviseNotes('');
            setReviseSceneNumber(null);
        }
    };

    return (
        <div className="scenario-editor">
            {/* Progress Header */}
            <div className="editor-header">
                <div className="editor-progress">
                    <div className="editor-progress-info">
                        <h2 className="editor-title">Sahne Yazımı</h2>
                        <span className="editor-progress-text">
                            {completedScenesCount} / {totalScenes} sahne tamamlandı
                        </span>
                    </div>
                    <div className="editor-progress-bar">
                        <div
                            className="editor-progress-fill"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>

                <div className="editor-stats">
                    <div className="editor-stat">
                        <span className="editor-stat-label">Süre</span>
                        <span className="editor-stat-value">
                            {Math.floor(completedDuration / 60)}:{(completedDuration % 60).toString().padStart(2, '0')}
                            <span className="editor-stat-divider">/</span>
                            {Math.floor(totalDuration / 60)}:{(totalDuration % 60).toString().padStart(2, '0')}
                        </span>
                    </div>
                    <div className="editor-stat">
                        <span className="editor-stat-label">Durum</span>
                        {getStatusBadge()}
                    </div>
                </div>
            </div>

            {/* Scene Timeline */}
            <div className="scene-timeline">
                {sceneOutlines.map((outline, index) => {
                    const scene = scenes?.find(s => s.scene_number === outline.scene_number);
                    const isCompleted = !!scene;
                    const isCurrent = index === currentSceneIndex;
                    const isSelected = selectedScene === outline.scene_number;

                    return (
                        <div
                            key={outline.scene_number}
                            className={`timeline-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isSelected ? 'selected' : ''}`}
                            onClick={() => setSelectedScene(outline.scene_number)}
                        >
                            <div className="timeline-marker">
                                {isCompleted ? '✓' : outline.scene_number}
                            </div>
                            <div className="timeline-info">
                                <span className="timeline-location">{outline.location}</span>
                                <span className="timeline-duration">{outline.duration_seconds}s</span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Main Editor Area */}
            <div className="editor-content">
                {/* Completed Scenes List */}
                <div className="scenes-list">
                    {scenes?.map((scene) => (
                        <SceneCard
                            key={scene.scene_number}
                            scene={scene}
                            isExpanded={selectedScene === scene.scene_number}
                            onToggle={() => setSelectedScene(
                                selectedScene === scene.scene_number ? null : scene.scene_number
                            )}
                        />
                    ))}

                    {/* Current Writing Scene */}
                    {isWriting && currentOutline && (
                        <SceneWriter
                            outline={currentOutline}
                            streamingText={streamingText}
                            isStreaming={true}
                        />
                    )}
                </div>

                {/* Action Panel */}
                <div className="editor-actions">
                    <div className="action-panel">
                        <h3 className="action-panel-title">Kontroller</h3>

                        {/* Senaryo Tamamlandı Durumu */}
                        {completedScenesCount >= totalScenes && !isWriting ? (
                            <div className="completion-panel">
                                <div className="completion-icon">🎉</div>
                                <h4 className="completion-title">Senaryo Tamamlandı!</h4>
                                <p className="completion-text">
                                    {totalScenes} sahne başarıyla yazıldı.
                                    <br />
                                    Toplam süre: {Math.floor(completedDuration / 60)}:{(completedDuration % 60).toString().padStart(2, '0')}
                                </p>
                                <div className="completion-stats">
                                    <div className="completion-stat">
                                        <span className="stat-value">{totalScenes}</span>
                                        <span className="stat-label">Sahne</span>
                                    </div>
                                    <div className="completion-stat">
                                        <span className="stat-value">{Math.floor(completedDuration / 60)}dk</span>
                                        <span className="stat-label">Süre</span>
                                    </div>
                                </div>
                                <p className="completion-hint">
                                    📥 Senaryonuzu indirmek için sağ üstteki <strong>İndir (.md)</strong> butonunu kullanın.
                                </p>
                            </div>
                        ) : (
                            <>
                                <div className="action-buttons">
                                    {lastScene && completedScenesCount < totalScenes && (
                                        <>
                                            <button
                                                className="btn btn-primary btn-lg action-btn"
                                                onClick={() => onApprove?.(lastScene.scene_number)}
                                                disabled={isWriting}
                                            >
                                                <span>✓</span>
                                                Onayla & Devam
                                            </button>

                                            <button
                                                className="btn btn-secondary action-btn"
                                                onClick={() => onExpand?.(lastScene.scene_number)}
                                                disabled={isWriting}
                                            >
                                                <span>🔄</span>
                                                Uzat (2x)
                                            </button>

                                            <button
                                                className="btn btn-secondary action-btn"
                                                onClick={() => handleOpenRevise(lastScene.scene_number)}
                                                disabled={isWriting}
                                            >
                                                <span>✏️</span>
                                                Düzelt
                                            </button>
                                        </>
                                    )}

                                    {!lastScene && !isWriting && (
                                        <button
                                            className="btn btn-primary btn-lg action-btn"
                                            onClick={onContinue}
                                        >
                                            <span>✍️</span>
                                            Yazmaya Başla
                                        </button>
                                    )}
                                </div>

                                <div className="action-info">
                                    <p className="action-info-text">
                                        💡 <strong>UZAT:</strong> Mevcut sahneyi daha detaylı, mikro-aksiyonlarla yeniden yazar.
                                    </p>
                                    <p className="action-info-text">
                                        ✏️ <strong>DÜZELT:</strong> Spesifik değişiklik talebiyle revize eder.
                                    </p>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Current Scene Info */}
                    {currentOutline && (
                        <div className="current-scene-info">
                            <h4>Şu Anki Sahne</h4>
                            <div className="scene-meta">
                                <div className="scene-meta-item">
                                    <span className="scene-meta-label">Mekan</span>
                                    <span className="scene-meta-value">{currentOutline.location}</span>
                                </div>
                                <div className="scene-meta-item">
                                    <span className="scene-meta-label">Zaman</span>
                                    <span className="scene-meta-value">{currentOutline.time_of_day}</span>
                                </div>
                                <div className="scene-meta-item">
                                    <span className="scene-meta-label">Süre</span>
                                    <span className="scene-meta-value">{currentOutline.duration_seconds} saniye</span>
                                </div>
                                <div className="scene-meta-item">
                                    <span className="scene-meta-label">Beat</span>
                                    <span className="scene-meta-value">#{currentOutline.beat_reference}</span>
                                </div>
                            </div>
                            <p className="scene-description">
                                {currentOutline.brief_description}
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Revise Modal */}
            {showReviseModal && (
                <div className="modal-overlay" onClick={() => setShowReviseModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Sahne {reviseSceneNumber} Düzelt</h3>
                            <button className="modal-close" onClick={() => setShowReviseModal(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <label>Değişiklik Talebi:</label>
                            <textarea
                                value={reviseNotes}
                                onChange={e => setReviseNotes(e.target.value)}
                                placeholder="Örn: Diyaloğu daha kısa yap, daha fazla aksiyon ekle..."
                                rows={4}
                            />
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-ghost" onClick={() => setShowReviseModal(false)}>
                                İptal
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={handleReviseSubmit}
                                disabled={!reviseNotes.trim()}
                            >
                                Revize Et
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
