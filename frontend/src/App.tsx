import { useState, useEffect } from 'react';
import { Layout } from './components/layout';
import { HomePage, WorkflowPage } from './pages';
import { useStore } from './store/useStore';
import './styles/design-system.css';

type View = 'home' | 'workflow';

function App() {
  const [view, setView] = useState<View>('home');
  const { selectProject, loadProjects } = useStore();

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleProjectSelect = async (projectId: string) => {
    await selectProject(projectId);
    setView('workflow');
  };

  const handleGoHome = () => {
    setView('home');
  };

  // Ana sayfa - Layout olmadan
  if (view === 'home') {
    return (
      <div className="app-home">
        <HomePage onProjectSelect={handleProjectSelect} />
      </div>
    );
  }

  // Workflow sayfası - Layout ile
  return (
    <Layout>
      <div className="app-header-actions">
        <button className="btn btn-ghost" onClick={handleGoHome}>
          ← Projelere Dön
        </button>
      </div>
      <WorkflowPage />
    </Layout>
  );
}

export default App;
