/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { Toast } from './components/shared/Toast';
import { CommandModal } from './components/shared/CommandModal';

// Pages
import { HomeDashboard } from './pages/HomeDashboard';
import { SimpleModeChat } from './pages/SimpleModeChat';
import { DevModeConsole } from './pages/DevModeConsole';
import { CodeChangesPage } from './pages/CodeChangesPage';
import { MissionControl } from './pages/MissionControl';
import { AgentsPage } from './pages/AgentsPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { ProjectBrain } from './pages/ProjectBrain';
import { ToolsMcpHub } from './pages/ToolsMcpHub';
import { GovernancePage } from './pages/GovernancePage';
import { SettingsPage } from './pages/SettingsPage';
import { DesignSystemPage } from './pages/DesignSystemPage';
import { CommandCenterPage } from './pages/CommandCenterPage';
import { ChiefOfStaffPage } from './pages/ChiefOfStaffPage';
import { InstructionsPage } from './pages/InstructionsPage';
import { MarketplaceHubPage } from './pages/MarketplaceHubPage';
import { CompliancePage } from './pages/CompliancePage';

const MainContent: React.FC = () => {
  const { activePage } = useApp();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#0a0a0a] text-[#e5e5e5] selection:bg-cyan-500/30 font-sans">
      {/* Sidebar navigation */}
      <Sidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />

      {/* Main page container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
        <TopBar setMobileOpen={setMobileOpen} />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {activePage === 'home' && <HomeDashboard />}
          {activePage === 'instructions' && <InstructionsPage />}
          {activePage === 'chat' && <SimpleModeChat />}
          {activePage === 'dev-console' && <DevModeConsole />}
          {activePage === 'code-changes' && <CodeChangesPage />}
          {activePage === 'mission-control' && <MissionControl />}
          {activePage === 'agents' && <AgentsPage />}
          {activePage === 'approvals' && <ApprovalsPage />}
          {activePage === 'project-brain' && <ProjectBrain />}
          {activePage === 'tools' && <ToolsMcpHub />}
          {activePage === 'governance' && <GovernancePage />}
          {activePage === 'settings' && <SettingsPage />}
          {activePage === 'design-system' && <DesignSystemPage />}
          {activePage === 'command-center' && <CommandCenterPage />}
          {activePage === 'chief-of-staff' && <ChiefOfStaffPage />}
          {activePage === 'marketplace-hub' && <MarketplaceHubPage />}
          {activePage === 'compliance' && <CompliancePage />}
        </main>
      </div>

      {/* Global modals and toasts */}
      <CommandModal />
      <Toast />
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <MainContent />
    </AppProvider>
  );
}
