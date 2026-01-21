import type { SceneOutline } from '../../types';

interface SceneWriterProps {
    outline: SceneOutline;
    streamingText?: string;
    isStreaming?: boolean;
}

export default function SceneWriter({
    outline,
    streamingText = '',
    isStreaming = false
}: SceneWriterProps) {
    return (
        <div className="scene-writer">
            <div className="scene-writer-header">
                <div className="scene-writer-title">
                    <span className="scene-writer-icon">✍️</span>
                    <span className="scene-writer-label">
                        SCENE {outline.scene_number}: {outline.location} - {outline.time_of_day}
                    </span>
                </div>
                <div className="scene-writer-status">
                    {isStreaming ? (
                        <>
                            <span className="loading-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </span>
                            <span>Yazılıyor...</span>
                        </>
                    ) : (
                        <span>Bekleniyor</span>
                    )}
                </div>
            </div>

            <div className="scene-writer-content">
                <div className="scene-writer-text">
                    {streamingText}
                    {isStreaming && <span className="typing-cursor" />}
                </div>
            </div>
        </div>
    );
}
