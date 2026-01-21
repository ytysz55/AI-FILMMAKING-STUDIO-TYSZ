import type { Scene } from '../../types';

interface SceneCardProps {
    scene: Scene;
    isExpanded?: boolean;
    onToggle?: () => void;
}

export default function SceneCard({ scene, isExpanded = false, onToggle }: SceneCardProps) {
    return (
        <div className={`scene-card ${isExpanded ? 'expanded' : ''}`}>
            <div className="scene-card-header" onClick={onToggle}>
                <span className="scene-card-title">{scene.header}</span>
                <div className="scene-card-meta">
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
            </div>
        </div>
    );
}
