/**
 * Ana Sayfa - Proje Listesi ve Oluşturma
 */

import { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import './HomePage.css';

interface HomePageProps {
    onProjectSelect: (projectId: string) => void;
}

export default function HomePage({ onProjectSelect }: HomePageProps) {
    const { projects, loadProjects, createProject, deleteProject, isLoading, error } = useStore();
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newProjectName, setNewProjectName] = useState('');
    const [newProjectDuration, setNewProjectDuration] = useState(30);

    useEffect(() => {
        loadProjects();
    }, [loadProjects]);

    const handleCreateProject = async () => {
        if (!newProjectName.trim()) return;

        try {
            const projectId = await createProject(newProjectName, newProjectDuration);
            setShowCreateModal(false);
            setNewProjectName('');
            onProjectSelect(projectId);
        } catch (err) {
            console.error('Proje oluşturma hatası:', err);
        }
    };

    const handleDeleteProject = async (projectId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (confirm('Bu projeyi silmek istediğinizden emin misiniz?')) {
            await deleteProject(projectId);
        }
    };

    return (
        <div className="home-page">
            {/* Hero Section */}
            <div className="hero-section">
                <div className="hero-content">
                    <h1 className="hero-title">
                        <span className="hero-icon">🎬</span>
                        AI Film Yapım Stüdyosu
                    </h1>
                    <p className="hero-subtitle">
                        Kaynak materyallerden Hollywood standartlarında senaryo üretin.
                        Visual Decompression tekniği ile ekrana hazır film transkriptleri.
                    </p>
                    <button
                        className="btn btn-primary btn-lg hero-cta"
                        onClick={() => setShowCreateModal(true)}
                    >
                        <span>✨</span>
                        Yeni Proje Başlat
                    </button>
                </div>

                <div className="hero-stats">
                    <div className="stat-card">
                        <span className="stat-icon">📝</span>
                        <span className="stat-value">{projects.length}</span>
                        <span className="stat-label">Proje</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-icon">🎭</span>
                        <span className="stat-value">1M</span>
                        <span className="stat-label">Token Kapasitesi</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-icon">⚡</span>
                        <span className="stat-value">4</span>
                        <span className="stat-label">Modül</span>
                    </div>
                </div>
            </div>

            {/* Projects Grid */}
            <div className="projects-section">
                <div className="section-header">
                    <h2>Projelerim</h2>
                    <button
                        className="btn btn-secondary"
                        onClick={() => setShowCreateModal(true)}
                    >
                        <span>➕</span>
                        Yeni Proje
                    </button>
                </div>

                {error && (
                    <div className="error-banner">
                        <span>⚠️</span>
                        {error}
                    </div>
                )}

                {isLoading ? (
                    <div className="loading-state">
                        <div className="loading-spinner" />
                        <span>Projeler yükleniyor...</span>
                    </div>
                ) : projects.length === 0 ? (
                    <div className="empty-state">
                        <span className="empty-icon">📁</span>
                        <h3>Henüz proje yok</h3>
                        <p>İlk projenizi oluşturarak başlayın</p>
                        <button
                            className="btn btn-primary"
                            onClick={() => setShowCreateModal(true)}
                        >
                            Proje Oluştur
                        </button>
                    </div>
                ) : (
                    <div className="projects-grid">
                        {projects.map((project) => (
                            <div
                                key={project.id}
                                className="project-card"
                                onClick={() => onProjectSelect(project.id)}
                            >
                                <div className="project-card-header">
                                    <span className="project-icon">🎬</span>
                                    <button
                                        className="project-delete"
                                        onClick={(e) => handleDeleteProject(project.id, e)}
                                        title="Sil"
                                    >
                                        🗑️
                                    </button>
                                </div>
                                <h3 className="project-name">{project.name}</h3>
                                <div className="project-progress">
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{ width: `${(project as any).progress || 0}%` }}
                                        />
                                    </div>
                                    <span className="progress-text">{(project as any).progress || 0}%</span>
                                </div>
                                <div className="project-meta">
                                    <span>ID: {project.id}</span>
                                </div>
                            </div>
                        ))}

                        {/* Add Project Card */}
                        <div
                            className="project-card add-card"
                            onClick={() => setShowCreateModal(true)}
                        >
                            <span className="add-icon">➕</span>
                            <span className="add-text">Yeni Proje</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>🎬 Yeni Proje Oluştur</h2>
                            <button
                                className="modal-close"
                                onClick={() => setShowCreateModal(false)}
                            >
                                ✕
                            </button>
                        </div>

                        <div className="modal-body">
                            <div className="form-group">
                                <label className="label">Proje Adı</label>
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="Örn: Mete Han"
                                    value={newProjectName}
                                    onChange={(e) => setNewProjectName(e.target.value)}
                                    autoFocus
                                />
                            </div>

                            <div className="form-group">
                                <label className="label">Hedef Süre (dakika)</label>
                                <input
                                    type="number"
                                    className="input"
                                    min={5}
                                    max={180}
                                    value={newProjectDuration}
                                    onChange={(e) => setNewProjectDuration(Number(e.target.value))}
                                />
                                <span className="input-hint">5-180 dakika arası</span>
                            </div>
                        </div>

                        <div className="modal-footer">
                            <button
                                className="btn btn-secondary"
                                onClick={() => setShowCreateModal(false)}
                            >
                                İptal
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={handleCreateProject}
                                disabled={!newProjectName.trim() || isLoading}
                            >
                                {isLoading ? 'Oluşturuluyor...' : 'Oluştur'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
