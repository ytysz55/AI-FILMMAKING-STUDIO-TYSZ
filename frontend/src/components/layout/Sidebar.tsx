import type { ModuleType } from '../../types';
import { WORKFLOW_STEPS } from '../../types';
import { useStore } from '../../store/useStore';

interface SidebarProps {
    currentModule?: ModuleType;
    moduleProgress?: Record<ModuleType, number>;
    onModuleSelect?: (module: ModuleType) => void;
    currentStep?: string;
}

export default function Sidebar({
    currentModule = 'senaryo',
    moduleProgress = { senaryo: 0, asset: 0, shotlist: 0, storyboard: 0 },
    onModuleSelect,
    currentStep = 'upload'
}: SidebarProps) {
    // Store'dan gerçek verileri al
    const { currentProject, contextStatus } = useStore();

    const modules = [
        { id: 'senaryo' as ModuleType, icon: '📝', label: 'Senaryo', progress: moduleProgress.senaryo },
        { id: 'asset' as ModuleType, icon: '🎨', label: 'Asset', progress: moduleProgress.asset },
        { id: 'shotlist' as ModuleType, icon: '🎥', label: 'Shotlist', progress: moduleProgress.shotlist },
        { id: 'storyboard' as ModuleType, icon: '📐', label: 'Storyboard', progress: moduleProgress.storyboard },
    ];

    // Token kullanımı - gerçek veya varsayılan
    const tokenUsage = {
        current: contextStatus?.current_tokens || 0,
        max: contextStatus?.max_tokens || 1000000
    };
    const usagePercentage = tokenUsage.max > 0 ? (tokenUsage.current / tokenUsage.max) * 100 : 0;
    const usageClass = usagePercentage >= 95 ? 'critical' : usagePercentage >= 80 ? 'warning' : '';

    // Workflow adımlarının tamamlanma durumu
    const steps = ['upload', 'analyze', 'select_concept', 'character_card', 'beat_sheet', 'scene_outline', 'writing'];
    const currentStepIndex = steps.indexOf(currentStep);

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <span className="sidebar-logo-icon">🎬</span>
                    <span className="sidebar-logo-text">Film Stüdyosu</span>
                </div>
            </div>

            {/* Navigation */}
            <div className="sidebar-content">
                {/* Aktif Proje */}
                <div className="sidebar-section">
                    <div className="sidebar-section-title">Proje</div>
                    <ul className="sidebar-nav">
                        <li className="sidebar-nav-item">
                            <div className="sidebar-nav-link active">
                                <span className="sidebar-nav-icon">📁</span>
                                <span className="sidebar-nav-label">
                                    {currentProject?.name || 'Proje Seçilmedi'}
                                </span>
                            </div>
                        </li>
                    </ul>
                </div>

                {/* Modüller */}
                <div className="sidebar-section">
                    <div className="sidebar-section-title">Modüller</div>
                    <ul className="sidebar-nav">
                        {modules.map((module) => (
                            <li key={module.id} className="sidebar-nav-item">
                                <div
                                    className={`sidebar-nav-link ${currentModule === module.id ? 'active' : ''}`}
                                    onClick={() => onModuleSelect?.(module.id)}
                                >
                                    <span className="sidebar-nav-icon">{module.icon}</span>
                                    <span className="sidebar-nav-label">{module.label}</span>
                                    <span className={`sidebar-nav-badge ${module.progress >= 100 ? 'complete' : ''}`}>
                                        {module.progress >= 100 ? '✓' : `${module.progress}%`}
                                    </span>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Akış Adımları */}
                <div className="sidebar-section">
                    <div className="sidebar-section-title">Senaryo Akışı</div>
                    <ul className="sidebar-nav">
                        {WORKFLOW_STEPS.slice(0, 7).map((step, index) => {
                            const isCompleted = index < currentStepIndex;
                            const isActive = steps[index] === currentStep;

                            return (
                                <li key={step.id} className="sidebar-nav-item">
                                    <div className={`sidebar-nav-link ${isActive ? 'active' : ''}`}>
                                        <span className="sidebar-nav-icon">{step.icon}</span>
                                        <span className="sidebar-nav-label">{step.title}</span>
                                        {isCompleted && (
                                            <span className="sidebar-nav-badge complete">✓</span>
                                        )}
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            </div>

            {/* Token Kullanımı */}
            <div className="sidebar-footer">
                <div className="token-usage">
                    <div className="token-usage-header">
                        <span className="token-usage-label">Bağlam</span>
                        <span className="token-usage-value">
                            {(tokenUsage.current / 1000).toFixed(0)}K / {(tokenUsage.max / 1000000).toFixed(0)}M
                        </span>
                    </div>
                    <div className="token-usage-bar">
                        <div
                            className={`token-usage-fill ${usageClass}`}
                            style={{ width: `${usagePercentage}%` }}
                        />
                    </div>
                </div>
            </div>
        </aside>
    );
}
