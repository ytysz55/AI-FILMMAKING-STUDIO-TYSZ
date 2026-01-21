import type { ReactNode } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import { useStore } from '../../store/useStore';
import './Layout.css';

interface LayoutProps {
    children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
    const { currentStep, currentProject } = useStore();

    return (
        <div className="app-layout">
            <Sidebar currentStep={currentStep} />
            <div className="main-container">
                <Header projectName={currentProject?.name} />
                <main className="main-content">
                    {children}
                </main>
            </div>
        </div>
    );
}
