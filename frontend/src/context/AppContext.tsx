import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  PageId,
  Agent,
  Mission,
  Task,
  ApprovalRequest,
  MemoryItem,
  ToolConnector,
  GovernanceEvent,
  TraceStep,
  ChatMessage,
  SystemMetric,
  RiskLevel
} from '../types';
import {
  INITIAL_AGENTS,
  INITIAL_MISSION,
  INITIAL_TASKS,
  INITIAL_APPROVALS,
  INITIAL_MEMORIES,
  INITIAL_CONNECTORS,
  INITIAL_GOVERNANCE_LOGS,
  INITIAL_TRACE_STEPS,
  INITIAL_CHAT_MESSAGES,
  SYSTEM_METRICS
} from '../data/mockData';
import { fetchLiveData } from '../data/api';

interface SafetySettings {
  planningFirst: boolean;
  mockSafe: boolean;
  requireApproval: boolean;
  auditLogging: boolean;
  blockDestructive: boolean;
}

interface AppContextType {
  activePage: PageId;
  setActivePage: (page: PageId) => void;
  agents: Agent[];
  mission: Mission;
  tasks: Task[];
  approvals: ApprovalRequest[];
  memories: MemoryItem[];
  connectors: ToolConnector[];
  governanceLogs: GovernanceEvent[];
  traceSteps: TraceStep[];
  chatMessages: ChatMessage[];
  systemMetrics: SystemMetric[];
  isCommandModalOpen: boolean;
  setIsCommandModalOpen: (open: boolean) => void;
  safetySettings: SafetySettings;
  toggleSafetySetting: (key: keyof SafetySettings) => void;
  toast: { message: string; type: 'success' | 'info' | 'warning' } | null;
  showToast: (message: string, type?: 'success' | 'info' | 'warning') => void;
  liveConnected: boolean;
  refreshLive: () => Promise<void>;

  // Actions
  approveRequest: (id: string) => void;
  rejectRequest: (id: string) => void;
  approveBatchLowRisk: () => void;
  toggleAgentStatus: (id: string) => void;
  sendMessage: (text: string, attachments?: { name: string; size: string; type: string }[]) => void;
  runMockWorkflowStep: () => void;
  togglePinMemory: (id: string) => void;
  toggleToolConnection: (id: string) => void;
  addMemoryItem: (title: string, snippet: string, type: MemoryItem['type'], tags: string[]) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activePage, setActivePage] = useState<PageId>('home');
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);
  const [mission, setMission] = useState<Mission>(INITIAL_MISSION);
  const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>(INITIAL_APPROVALS);
  const [memories, setMemories] = useState<MemoryItem[]>(INITIAL_MEMORIES);
  const [connectors, setConnectors] = useState<ToolConnector[]>(INITIAL_CONNECTORS);
  const [governanceLogs, setGovernanceLogs] = useState<GovernanceEvent[]>(INITIAL_GOVERNANCE_LOGS);
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>(INITIAL_TRACE_STEPS);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(INITIAL_CHAT_MESSAGES);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetric[]>(SYSTEM_METRICS);
  const [isCommandModalOpen, setIsCommandModalOpen] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' | 'warning' } | null>(null);
  const [liveConnected, setLiveConnected] = useState(false);

  const [safetySettings, setSafetySettings] = useState<SafetySettings>({
    planningFirst: true,
    mockSafe: true,
    requireApproval: true,
    auditLogging: true,
    blockDestructive: true
  });

  // Keyboard shortcut for Command K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandModalOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Load real backend data on mount; keep mock data as a fallback so the UI
  // works even if the backend is down. Only overrides slices that came back.
  const refreshLive = async () => {
    const live = await fetchLiveData();
    if (!live) { setLiveConnected(false); return; }
    setLiveConnected(true);
    if (live.agents && live.agents.length) setAgents(live.agents);
    if (live.governanceLogs && live.governanceLogs.length) setGovernanceLogs(live.governanceLogs);
    if (live.systemMetrics && live.systemMetrics.length) setSystemMetrics(live.systemMetrics);
  };

  useEffect(() => {
    refreshLive();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const showToast = (message: string, type: 'success' | 'info' | 'warning' = 'success') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  const toggleSafetySetting = (key: keyof SafetySettings) => {
    setSafetySettings(prev => {
      const updated = { ...prev, [key]: !prev[key] };
      showToast(`Safety setting "${key}" updated to ${updated[key] ? 'Enabled' : 'Disabled'}`, 'info');
      return updated;
    });
  };

  const approveRequest = (id: string) => {
    const target = approvals.find(a => a.id === id);
    if (!target) return;

    setApprovals(prev => prev.map(a => a.id === id ? { ...a, status: 'approved' } : a));
    
    // Log governance event
    const newLog: GovernanceEvent = {
      id: `gov-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type: 'approval_granted',
      agentName: target.agentName,
      action: target.toolName,
      status: 'allowed',
      risk: target.riskLevel,
      details: `User explicitly approved: ${target.title}. Action executed in mock sandbox.`
    };
    setGovernanceLogs(prev => [newLog, ...prev]);

    // Update tasks
    setTasks(prev => prev.map(t => t.id === 'task-105' || t.id === 'task-106' ? { ...t, status: 'completed' } : t));
    
    // Update metrics
    setSystemMetrics(prev => prev.map(m => {
      if (m.label === 'Pending Approvals') {
        const current = parseInt(m.value.toString()) || 5;
        return { ...m, value: Math.max(0, current - 1) < 10 ? `0${Math.max(0, current - 1)}` : Math.max(0, current - 1) };
      }
      return m;
    }));

    showToast(`Approved "${target.title}". Agent resumed execution.`, 'success');
  };

  const rejectRequest = (id: string) => {
    const target = approvals.find(a => a.id === id);
    if (!target) return;

    setApprovals(prev => prev.map(a => a.id === id ? { ...a, status: 'rejected' } : a));
    
    const newLog: GovernanceEvent = {
      id: `gov-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type: 'safety_block',
      agentName: target.agentName,
      action: target.toolName,
      status: 'blocked',
      risk: target.riskLevel,
      details: `User REJECTED action: ${target.title}. Sub-task marked as blocked.`
    };
    setGovernanceLogs(prev => [newLog, ...prev]);

    showToast(`Rejected "${target.title}". Agent notified to replan without this tool.`, 'warning');
  };

  const approveBatchLowRisk = () => {
    const lowRiskPending = approvals.filter(a => a.status === 'pending' && a.riskLevel === 'low');
    if (lowRiskPending.length === 0) {
      showToast('No pending low-risk items in the queue.', 'info');
      return;
    }

    setApprovals(prev => prev.map(a => (a.status === 'pending' && a.riskLevel === 'low') ? { ...a, status: 'approved' } : a));
    
    const newLog: GovernanceEvent = {
      id: `gov-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type: 'approval_granted',
      agentName: 'Master Orchestrator',
      action: 'Batch Low-Risk Approval',
      status: 'allowed',
      risk: 'low',
      details: `Approved ${lowRiskPending.length} low-risk operations simultaneously.`
    };
    setGovernanceLogs(prev => [newLog, ...prev]);

    showToast(`Approved ${lowRiskPending.length} low-risk operations successfully!`, 'success');
  };

  const toggleAgentStatus = (id: string) => {
    setAgents(prev => prev.map(agent => {
      if (agent.id === id) {
        const nextStatus = agent.status === 'active' ? 'idle' : agent.status === 'idle' ? 'running' : 'active';
        showToast(`Agent "${agent.name}" status changed to ${nextStatus.toUpperCase()}`, 'info');
        return { ...agent, status: nextStatus };
      }
      return agent;
    }));
  };

  const sendMessage = (text: string, attachments?: { name: string; size: string; type: string }[]) => {
    if (!text.trim() && !attachments?.length) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      attachments
    };

    setChatMessages(prev => [...prev, userMsg]);

    // Simulate Agent response after short delay
    setTimeout(() => {
      const isQuestion = text.toLowerCase().includes('?');
      const isDeploy = text.toLowerCase().includes('deploy') || text.toLowerCase().includes('run');
      
      const replyText = isDeploy
        ? `I have verified the build artifacts. Under our **Planning-First Mode**, I prepared a dry-run package for Cloud Run container deployment. Would you like me to submit the deployment request to the Approvals Queue?`
        : isQuestion
        ? `I checked Project Brain memories and our 7 connected tools. All agent permissions are compliant with Governance Safety rules (Score: 98%). How would you like to proceed with the current mission?`
        : `Understood! I've routed your request to the **UI Design Agent** and **Memory Agent** for parallel processing. They are currently synthesizing the required updates.`;

      const agentMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: 'agent',
        agentName: 'Master Orchestrator',
        avatar: '🤖',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isWorkingCard: isDeploy
      };

      setChatMessages(prev => [...prev, agentMsg]);
    }, 800);
  };

  const runMockWorkflowStep = () => {
    // Advance mission progress
    setMission(prev => ({
      ...prev,
      progress: Math.min(100, prev.progress + 8)
    }));

    // Add a new step to trace
    const nextStepNum = traceSteps.length + 1;
    const newStep: TraceStep = {
      step: nextStepNum,
      id: `tr-0${nextStepNum}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      agent: 'Implementation Agent',
      action: `Synthesize component batch #${nextStepNum} with glassmorphic tokens`,
      status: 'success',
      durationMs: Math.floor(Math.random() * 400) + 150,
      toolUsed: 'Component Generator',
      inputSnippet: `Generate responsive JSX with border-white/7 and background rgba(23,23,23,0.75)`,
      outputSnippet: `Successfully emitted 142 lines of clean React code.`
    };

    setTraceSteps(prev => [...prev, newStep]);
    showToast('Simulated workflow step executed! Mission progress advanced to ' + Math.min(100, mission.progress + 8) + '%', 'success');
  };

  const togglePinMemory = (id: string) => {
    setMemories(prev => prev.map(m => {
      if (m.id === id) {
        const nextPin = !m.pinned;
        showToast(nextPin ? `Pinned "${m.title}" to top of Project Brain` : `Unpinned memory item`, 'info');
        return { ...m, pinned: nextPin };
      }
      return m;
    }));
  };

  const toggleToolConnection = (id: string) => {
    setConnectors(prev => prev.map(c => {
      if (c.id === id) {
        const nextStatus = c.status === 'connected' ? 'disconnected' : 'connected';
        showToast(`Tool connector "${c.name}" is now ${nextStatus.toUpperCase()}`, nextStatus === 'connected' ? 'success' : 'warning');
        return { ...c, status: nextStatus };
      }
      return c;
    }));
  };

  const addMemoryItem = (title: string, snippet: string, type: MemoryItem['type'], tags: string[]) => {
    const newMem: MemoryItem = {
      id: `mem-${Date.now()}`,
      title,
      snippet,
      type,
      relevance: 95,
      tier: 'hot',
      source: 'Manual User Annotation',
      timestamp: 'Just now',
      tags,
      pinned: false
    };
    setMemories(prev => [newMem, ...prev]);
    showToast(`Added new memory "${title}" to Project Brain!`, 'success');
  };

  return (
    <AppContext.Provider
      value={{
        activePage,
        setActivePage,
        agents,
        mission,
        tasks,
        approvals,
        memories,
        connectors,
        governanceLogs,
        traceSteps,
        chatMessages,
        systemMetrics,
        isCommandModalOpen,
        setIsCommandModalOpen,
        safetySettings,
        toggleSafetySetting,
        toast,
        showToast,
        liveConnected,
        refreshLive,
        approveRequest,
        rejectRequest,
        approveBatchLowRisk,
        toggleAgentStatus,
        sendMessage,
        runMockWorkflowStep,
        togglePinMemory,
        toggleToolConnection,
        addMemoryItem
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
