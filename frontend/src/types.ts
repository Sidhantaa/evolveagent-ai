export type PageId =
  | 'home'
  | 'chat'
  | 'dev-console'
  | 'code-changes'
  | 'mission-control'
  | 'agents'
  | 'approvals'
  | 'project-brain'
  | 'tools'
  | 'governance'
  | 'settings'
  | 'design-system'
  | 'command-center'
  | 'chief-of-staff'
  | 'instructions';

export type RiskLevel = 'low' | 'medium' | 'high';

export type TaskStatus = 'planned' | 'running' | 'waiting_approval' | 'completed' | 'blocked' | 'failed';

export type PermissionLevel = 'read-only' | 'planning-only' | 'approval-gated' | 'high-trust';

export interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  avatar: string;
  status: 'active' | 'idle' | 'running' | 'waiting' | 'blocked';
  qualityScore: number;
  riskLevel: RiskLevel;
  memoryAccess: 'Full Workspace' | 'Scoped Project' | 'Read Only' | 'Restricted';
  permissionLevel: PermissionLevel;
  connectedTools: string[];
  currentTask?: string;
  tasksCompletedToday: number;
  tokensUsed: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  assignedAgentId: string;
  assignedAgentName: string;
  status: TaskStatus;
  riskLevel: RiskLevel;
  phase: string;
  timestamp: string;
  toolCall?: string;
}

export interface Mission {
  id: string;
  title: string;
  description: string;
  progress: number;
  status: 'active' | 'completed' | 'paused';
  assignedAgents: string[];
  phases: {
    id: string;
    title: string;
    status: 'completed' | 'in_progress' | 'pending';
    tasksCount: number;
    completedCount: number;
  }[];
}

export interface ApprovalRequest {
  id: string;
  title: string;
  description: string;
  agentId: string;
  agentName: string;
  riskLevel: RiskLevel;
  timestamp: string;
  status: 'pending' | 'approved' | 'rejected';
  intent: string;
  plannedAction: string;
  permissionScopes: string[];
  toolName: string;
  costLimit?: string;
  workspaceScope: string;
  governanceChecks: {
    label: string;
    passed: boolean;
    detail: string;
  }[];
}

export interface MemoryItem {
  id: string;
  title: string;
  snippet: string;
  type: 'Memory' | 'Decision' | 'Chat Memory' | 'File Index' | 'Goal';
  relevance: number; // e.g. 98%
  tier: 'hot' | 'warm' | 'archived';
  source: string;
  timestamp: string;
  tags: string[];
  pinned?: boolean;
}

export interface ToolConnector {
  id: string;
  name: string;
  category: 'MCP' | 'API' | 'Local CLI' | 'Database';
  status: 'connected' | 'disconnected' | 'approval-gated' | 'error';
  riskLevel: RiskLevel;
  description: string;
  icon: string;
  permissions: string[];
  dryCheckPassed: boolean;
  activeAgentsCount: number;
  callsToday: number;
  lastUsed: string;
}

export interface GovernanceEvent {
  id: string;
  timestamp: string;
  type: 'tool_call' | 'permission_check' | 'safety_block' | 'approval_granted' | 'audit_log';
  agentName: string;
  action: string;
  status: 'allowed' | 'blocked' | 'pending_review' | 'mock_executed';
  risk: RiskLevel;
  details: string;
}

export interface TraceStep {
  step: number;
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  status: 'success' | 'running' | 'waiting' | 'failed';
  durationMs: number;
  toolUsed?: string;
  inputSnippet?: string;
  outputSnippet?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  agentName?: string;
  avatar?: string;
  text: string;
  timestamp: string;
  isWorkingCard?: boolean;
  attachments?: { name: string; size: string; type: string }[];
}

export interface SystemMetric {
  label: string;
  value: string | number;
  trend?: string;
  isPositive?: boolean;
  subtitle?: string;
}
