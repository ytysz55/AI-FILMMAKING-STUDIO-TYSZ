import type { Scene } from '../../types';

interface SceneCardProps {
    scene: Scene;
    isExpanded?: boolean;
    onToggle?: () => void;
    onApprove?: (sceneNumber: number) => void;
    onExpand?: (sceneNumber: number) => void;
    onRevise?: (sceneNumber: number) => void;
}

export default function SceneCard({
    scene,
    isExpanded = false,
    onToggle,
    onApprove,
    onExpand,
    onRevise
}: SceneCardProps) {
    return (
        <div className={`scene-card ${isExpanded ? 'expanded' : ''} ${scene.status === 'approved' ? 'approved' : ''}`}>
            <div className="scene-card-header" onClick={onToggle}>
                <span className="scene-card-title">{scene.header}</span>
                <div className="scene-card-meta">
                    <span className="scene-card-duration">
                        [{scene.duration_seconds || 0}s]
                    </span>
                    <span className={`scene-card-status ${scene.status}`}>
                        {scene.status === 'approved' ? '✓ Onaylı' : 'Taslak'}
                    </span>
                    <span className="scene-card-toggle">▼</span>
                </div>
            </div>

            <div className="scene-card-content">
                <div className="scene-action-text">{scene.action}</div>

                {scene.dialogue && scene.dialogue.length > 0 && (
                    <div className="scene-dialogue">
                        {scene.dialogue.map((d, index) => (
                            <div key={index} className="dialogue-item">
                                <div className="dialogue-character">
                                    {d.character}
                                    {d.parenthetical && (
                                        <span className="dialogue-parenthetical">({d.parenthetical})</span>
                                    )}
                                </div>
                                <div className="dialogue-line">{d.line}</div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Aksiyon butonları - sadece taslak sahneler için */}
                {scene.status !== 'approved' && (onApprove || onExpand || onRevise) && (
                    <div className="scene-card-actions">
                        {onApprove && (
                            <button
                                className="btn btn-sm btn-primary"
                                onClick={(e) => { e.stopPropagation(); onApprove(scene.scene_number); }}
                            >
                                ✓ Onayla
                            </button>
                        )}
                        {onExpand && (
                            <button
                                className="btn btn-sm btn-secondary"
                                onClick={(e) => { e.stopPropagation(); onExpand(scene.scene_number); }}
                            >
                                🔄 Uzat
                            </button>
                        )}
                        {onRevise && (
                            <button
                                className="btn btn-sm btn-secondary"
                                onClick={(e) => { e.stopPropagation(); onRevise(scene.scene_number); }}
                            >
                                ✏️ Düzelt
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
