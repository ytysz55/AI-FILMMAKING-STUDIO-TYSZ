import { useState } from 'react';
import { useStore } from '../../store/useStore';
import api from '../../services/api';

interface HeaderProps {
    projectName?: string;
    currentStep?: string;
    isConnected?: boolean;
}

export default function Header({
    projectName,
    currentStep,
    isConnected = true
}: HeaderProps) {
    const { currentProject, scenes, sceneOutlines, setError } = useStore();
    const [isSaving, setIsSaving] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [saveMessage, setSaveMessage] = useState<string | null>(null);

    // Kaydet fonksiyonu
    const handleSave = async () => {
        if (!currentProject) return;

        setIsSaving(true);
        setSaveMessage(null);

        try {
            // Proje durumunu kaydet (backend otomatik kaydediyor ama biz de tetikleyebiliriz)
            await api.status.getProjectStatus(currentProject.id);
            setSaveMessage('✓ Kaydedildi');
            setTimeout(() => setSaveMessage(null), 2000);
        } catch (error) {
            setError('Kaydetme hatası');
        } finally {
            setIsSaving(false);
        }
    };

    // Senaryo indirme fonksiyonu
    const handleExportMarkdown = async () => {
        if (!currentProject) return;

        try {
            const result = await api.scenario.exportScreenplay(currentProject.id, 'markdown');

            // Markdown dosyası olarak indir
            const blob = new Blob([result.markdown], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${projectName || 'senaryo'}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            setError('Export hatası');
        }
    };

    const handleExportJSON = async () => {
        if (!currentProject) return;

        try {
            const result = await api.scenario.exportScreenplay(currentProject.id, 'json');

            // JSON dosyası olarak indir
            const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${projectName || 'senaryo'}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            setError('Export hatası');
        }
    };

    // Tamamlanma durumu
    const isCompleted = scenes.length > 0 && sceneOutlines.length > 0 && scenes.length >= sceneOutlines.length;

    return (
        <header className="header">
            <div className="header-left">
                <div className="header-breadcrumb">
                    <span>Projeler</span>
                    <span className="header-breadcrumb-divider">/</span>
                    <span>{projectName || 'Proje Seçilmedi'}</span>
                    {currentStep && (
                        <>
                            <span className="header-breadcrumb-divider">/</span>
                            <span className="header-breadcrumb-current">{currentStep}</span>
                        </>
                    )}
                </div>
            </div>

            <div className="header-right">
                <div className="header-status">
                    <span className={`header-status-dot ${!isConnected ? 'disconnected' : ''}`} />
                    <span>{isConnected ? 'Bağlı' : 'Bağlantı Yok'}</span>
                </div>

                {/* Export Butonları - Senaryo tamamlandıysa göster */}
                {isCompleted && (
                    <div className="header-export-group">
                        <button
                            className="btn btn-success"
                            onClick={handleExportMarkdown}
                            title="Markdown formatında indir"
                        >
                            <span>📥</span>
                            İndir (.md)
                        </button>
                        <button
                            className="btn btn-secondary"
                            onClick={handleExportJSON}
                            title="JSON formatında indir"
                        >
                            <span>📋</span>
                            JSON
                        </button>
                    </div>
                )}

                {/* Ayarlar Butonu */}
                <div className="header-settings-wrapper">
                    <button
                        className="btn btn-secondary"
                        onClick={() => setShowSettings(!showSettings)}
                    >
                        <span>⚙️</span>
                        Ayarlar
                    </button>

                    {showSettings && (
                        <div className="header-settings-dropdown">
                            <div className="settings-item">
                                <label>Model</label>
                                <span>gemini-3-flash-preview</span>
                            </div>
                            <div className="settings-item">
                                <label>Dil</label>
                                <span>Türkçe</span>
                            </div>
                            <div className="settings-item">
                                <label>Hedef Süre</label>
                                <span>{currentProject?.config?.target_duration_minutes || 30} dk</span>
                            </div>
                            <hr />
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => setShowSettings(false)}
                            >
                                Kapat
                            </button>
                        </div>
                    )}
                </div>

                {/* Kaydet Butonu */}
                <button
                    className="btn btn-primary"
                    onClick={handleSave}
                    disabled={isSaving || !currentProject}
                >
                    {isSaving ? (
                        <>
                            <span className="loading-spinner small" />
                            Kaydediliyor...
                        </>
                    ) : saveMessage ? (
                        <>{saveMessage}</>
                    ) : (
                        <>
                            <span>💾</span>
                            Kaydet
                        </>
                    )}
                </button>
            </div>
        </header>
    );
}
