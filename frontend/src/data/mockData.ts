import {
  Agent,
  Mission,
  Task,
  ApprovalRequest,
  MemoryItem,
  ToolConnector,
  GovernanceEvent,
  TraceStep,
  ChatMessage,
  SystemMetric
} from '../types';

export const INITIAL_AGENTS: Agent[] = [
  {
    id: 'agent-master',
    name: 'Master Orchestrator',
    role: 'System Router & Mission Chief',
    description: 'Deconstructs high-level user intents into sub-tasks, delegates to specialized agents, and oversees execution safety.',
    avatar: '🤖',
    status: 'active',
    qualityScore: 99,
    riskLevel: 'low',
    memoryAccess: 'Full Workspace',
    permissionLevel: 'high-trust',
    connectedTools: ['MCP Router', 'Workspace Memory', 'Task Delegation CLI'],
    currentTask: 'Orchestrating UI Redesign Mission #409',
    tasksCompletedToday: 42,
    tokensUsed: '142.5k'
  },
  {
    id: 'agent-ui',
    name: 'UI Design Agent',
    role: 'Frontend Architect & Token Stylist',
    description: 'Specializes in React, Tailwind CSS, glassmorphism design systems, and responsive layout generation.',
    avatar: '🎨',
    status: 'running',
    qualityScore: 96,
    riskLevel: 'low',
    memoryAccess: 'Scoped Project',
    permissionLevel: 'planning-only',
    connectedTools: ['Tailwind Validator', 'Lucide Icon Index', 'Component Generator'],
    currentTask: 'Generating responsive grid for Agents Overview',
    tasksCompletedToday: 18,
    tokensUsed: '88.2k'
  },
  {
    id: 'agent-memory',
    name: 'Memory Agent',
    role: 'Knowledge Graph & Vector Indexer',
    description: 'Maintains long-term workspace context, indexes project documents, and extracts architectural decisions.',
    avatar: '🧠',
    status: 'active',
    qualityScore: 98,
    riskLevel: 'low',
    memoryAccess: 'Full Workspace',
    permissionLevel: 'read-only',
    connectedTools: ['Vector DB Scanner', 'AST Parser', 'Semantic Search Engine'],
    currentTask: 'Indexing 19 recent file modifications in Project Brain',
    tasksCompletedToday: 31,
    tokensUsed: '64.0k'
  },
  {
    id: 'agent-gov',
    name: 'Governance Agent',
    role: 'Safety Enforcement & Risk Judge',
    description: 'Audits every tool invocation, enforces mock-safe sandboxing, and intercepts high-risk operations for user approval.',
    avatar: '🛡️',
    status: 'active',
    qualityScore: 100,
    riskLevel: 'medium',
    memoryAccess: 'Read Only',
    permissionLevel: 'approval-gated',
    connectedTools: ['Permission Policy Engine', 'Audit Logger', 'Risk Evaluator'],
    currentTask: 'Evaluating GitHub Repo Scan Request for permission scope',
    tasksCompletedToday: 128,
    tokensUsed: '45.1k'
  },
  {
    id: 'agent-impl',
    name: 'Implementation Agent',
    role: 'Full-Stack Code Synthesizer',
    description: 'Writes clean TypeScript, React components, and Node API endpoints with strict type safety.',
    avatar: '⚡',
    status: 'waiting',
    qualityScore: 94,
    riskLevel: 'medium',
    memoryAccess: 'Scoped Project',
    permissionLevel: 'approval-gated',
    connectedTools: ['TypeScript Compiler', 'Vite Dev Server', 'ESLint CLI'],
    currentTask: 'Waiting for approval on filesystem write to /src/components',
    tasksCompletedToday: 24,
    tokensUsed: '110.8k'
  },
  {
    id: 'agent-research',
    name: 'Research Agent',
    role: 'API Doc & Best Practice Analyst',
    description: 'Scans technical documentation, verifies library compatibility, and synthesizes architecture summaries.',
    avatar: '🔍',
    status: 'idle',
    qualityScore: 95,
    riskLevel: 'low',
    memoryAccess: 'Read Only',
    permissionLevel: 'read-only',
    connectedTools: ['Web Searcher', 'MDN Indexer', 'GitHub Doc Reader'],
    tasksCompletedToday: 15,
    tokensUsed: '39.4k'
  },
  {
    id: 'agent-judge',
    name: 'Judge Agent',
    role: 'Output Quality & Testing Critic',
    description: 'Evaluates code against design system tokens, checks accessibility contrast, and runs simulated unit tests.',
    avatar: '⚖️',
    status: 'active',
    qualityScore: 97,
    riskLevel: 'low',
    memoryAccess: 'Scoped Project',
    permissionLevel: 'read-only',
    connectedTools: ['DOM Inspector', 'Contrast Checker', 'Test Runner'],
    currentTask: 'Verifying contrast ratios on Charcoal Glass cards',
    tasksCompletedToday: 29,
    tokensUsed: '52.7k'
  }
];

export const INITIAL_MISSION: Mission = {
  id: 'mission-01',
  title: 'Redesign EvolveAgent AI Workspace UI',
  description: 'Transform standard dashboard into a premium dark graphite multi-agent operating system with deep observability and governance.',
  progress: 62,
  status: 'active',
  assignedAgents: ['agent-master', 'agent-ui', 'agent-memory', 'agent-gov', 'agent-impl'],
  phases: [
    { id: 'p1', title: 'Understand product vision & token tokens', status: 'completed', tasksCount: 4, completedCount: 4 },
    { id: 'p2', title: 'Design Home Dashboard & Navigation', status: 'completed', tasksCount: 5, completedCount: 5 },
    { id: 'p3', title: 'Design Mission Control & Agents Grid', status: 'in_progress', tasksCount: 6, completedCount: 4 },
    { id: 'p4', title: 'Design Approvals, Project Brain & Tools Hub', status: 'in_progress', tasksCount: 5, completedCount: 2 },
    { id: 'p5', title: 'Export Design System & Verify Audit Logs', status: 'pending', tasksCount: 4, completedCount: 0 }
  ]
};

export const INITIAL_TASKS: Task[] = [
  {
    id: 'task-101',
    title: 'Extract design system tokens from reference images',
    description: 'Identify exact hex values (#0a0a0a, #171717) and glassmorphism blur settings.',
    assignedAgentId: 'agent-ui',
    assignedAgentName: 'UI Design Agent',
    status: 'completed',
    riskLevel: 'low',
    phase: 'Understand product vision',
    timestamp: '10:14 AM'
  },
  {
    id: 'task-102',
    title: 'Synthesize Home Dashboard command center input',
    description: 'Build ⌘ K responsive search bar with quick action buttons and metric counters.',
    assignedAgentId: 'agent-ui',
    assignedAgentName: 'UI Design Agent',
    status: 'completed',
    riskLevel: 'low',
    phase: 'Design Home Dashboard',
    timestamp: '10:32 AM'
  },
  {
    id: 'task-103',
    title: 'Generate Agents Page responsive grid & permission profiles',
    description: 'Render agent cards showing quality score, memory access, and live status badges.',
    assignedAgentId: 'agent-ui',
    assignedAgentName: 'UI Design Agent',
    status: 'running',
    riskLevel: 'low',
    phase: 'Design Mission Control & Agents Grid',
    timestamp: '11:05 AM',
    toolCall: 'component_generator --target=AgentsGrid'
  },
  {
    id: 'task-104',
    title: 'Scan workspace files for memory indexing',
    description: 'Index 19 recent file modifications into vector Project Brain.',
    assignedAgentId: 'agent-memory',
    assignedAgentName: 'Memory Agent',
    status: 'running',
    riskLevel: 'low',
    phase: 'Design Approvals, Project Brain & Tools Hub',
    timestamp: '11:12 AM',
    toolCall: 'vector_db_scanner --path=/src'
  },
  {
    id: 'task-105',
    title: 'Execute GitHub Repo Scan for MCP integration',
    description: 'Requires read access to github.com/evolveagent/core repository metadata.',
    assignedAgentId: 'agent-impl',
    assignedAgentName: 'Implementation Agent',
    status: 'waiting_approval',
    riskLevel: 'medium',
    phase: 'Design Approvals, Project Brain & Tools Hub',
    timestamp: '11:18 AM',
    toolCall: 'github_connector --action=scan_repo --scope=metadata'
  },
  {
    id: 'task-106',
    title: 'Modify filesystem styles in /src/index.css',
    description: 'Inject custom scrollbar rules and glow utilities.',
    assignedAgentId: 'agent-impl',
    assignedAgentName: 'Implementation Agent',
    status: 'waiting_approval',
    riskLevel: 'medium',
    phase: 'Design Approvals, Project Brain & Tools Hub',
    timestamp: '11:20 AM',
    toolCall: 'fs_write --path=/src/index.css'
  },
  {
    id: 'task-107',
    title: 'Run full security audit against Mock-Safe policies',
    description: 'Verify no real destructive shell execution occurs without explicit confirmation.',
    assignedAgentId: 'agent-gov',
    assignedAgentName: 'Governance Agent',
    status: 'planned',
    riskLevel: 'high',
    phase: 'Export Design System',
    timestamp: '11:30 AM'
  }
];

export const INITIAL_APPROVALS: ApprovalRequest[] = [
  {
    id: 'app-01',
    title: 'GitHub Repo Scan Request',
    description: 'Implementation Agent requested permission to invoke GitHub Connector to scan repository structure and index open pull requests.',
    agentId: 'agent-impl',
    agentName: 'Implementation Agent',
    riskLevel: 'medium',
    timestamp: '2 mins ago',
    status: 'pending',
    intent: 'Analyze repository architecture to suggest optimal multi-agent folder structure for EvolveAgent.',
    plannedAction: 'Invoke MCP Connector "github-connector" with read-only metadata scope on repository "evolve-ai/core".',
    permissionScopes: ['Read Repo Metadata', 'List Open Issues', 'View File Tree'],
    toolName: 'github-connector (MCP)',
    costLimit: '$0.00 (Free Tier)',
    workspaceScope: '/projects/evolve-ai',
    governanceChecks: [
      { label: 'Mock-Safe Sandboxing Verified', passed: true, detail: 'Action will run in read-only sandbox without altering external state.' },
      { label: 'Token Budget Compliance', passed: true, detail: 'Estimated context payload is 4.2k tokens (within 25k limit).' },
      { label: 'No Destructive Shell Commands', passed: true, detail: 'No bash or write operations requested in this batch.' },
      { label: 'External Network Call', passed: false, detail: 'Requires outbound API connection to api.github.com.' }
    ]
  },
  {
    id: 'app-02',
    title: 'Write File to /src/components/layout/Sidebar.tsx',
    description: 'UI Design Agent wants to overwrite Sidebar navigation code to add live activity indicators and badge counts.',
    agentId: 'agent-ui',
    agentName: 'UI Design Agent',
    riskLevel: 'medium',
    timestamp: '5 mins ago',
    status: 'pending',
    intent: 'Update sidebar navigation items with real-time dynamic counter props.',
    plannedAction: 'Execute fs_write on workspace path /src/components/layout/Sidebar.tsx.',
    permissionScopes: ['Write Local Files', 'Modify Component Tree'],
    toolName: 'filesystem-access (Local CLI)',
    costLimit: '$0.00 (Local)',
    workspaceScope: '/src/components/layout',
    governanceChecks: [
      { label: 'Git Backup Confirmed', passed: true, detail: 'Working tree is clean; undo checkpoint created automatically.' },
      { label: 'AST Syntax Validation', passed: true, detail: 'TypeScript syntax check passed with 0 compile errors.' },
      { label: 'Mock-Safe Sandboxing Verified', passed: true, detail: 'Operation restricted to user workspace container.' }
    ]
  },
  {
    id: 'app-03',
    title: 'Query Cloud Postgres Database Schema',
    description: 'Memory Agent requested read-only connection to inspect telemetry tables and user session stats.',
    agentId: 'agent-memory',
    agentName: 'Memory Agent',
    riskLevel: 'low',
    timestamp: '12 mins ago',
    status: 'pending',
    intent: 'Extract user activity metrics to enrich Home Dashboard counters.',
    plannedAction: 'Run SQL query: SELECT count(*), status FROM agent_tasks GROUP BY status;',
    permissionScopes: ['Read Database Schema', 'Execute SELECT Queries'],
    toolName: 'postgres-client (MCP)',
    costLimit: '$0.01 (Compute)',
    workspaceScope: 'Database: evolve_prod',
    governanceChecks: [
      { label: 'Read-Only Query Confirmed', passed: true, detail: 'Query parsed: No INSERT, UPDATE, DELETE, or DROP statements detected.' },
      { label: 'PII Scrubbing Enabled', passed: true, detail: 'User email and credential columns automatically masked.' }
    ]
  },
  {
    id: 'app-04',
    title: 'Execute Automated E2E Test Suite in Playwright',
    description: 'Judge Agent wants to launch headless Chromium to test navigation flow across all 11 EvolveAgent screens.',
    agentId: 'agent-judge',
    agentName: 'Judge Agent',
    riskLevel: 'low',
    timestamp: '18 mins ago',
    status: 'pending',
    intent: 'Verify visual regression and contrast ratios on responsive layout.',
    plannedAction: 'Run `npx playwright test --project=chromium` in background container.',
    permissionScopes: ['Run Browser Automation', 'Take Screen Snapshots'],
    toolName: 'playwright-mcp (MCP)',
    costLimit: '$0.05 (CPU)',
    workspaceScope: '/tests/e2e',
    governanceChecks: [
      { label: 'Headless Sandboxing', passed: true, detail: 'Browser isolated to localhost:3000 container network.' },
      { label: 'Resource Cap Active', passed: true, detail: 'Memory capped at 1.5GB; timeout set to 60s.' }
    ]
  },
  {
    id: 'app-05',
    title: 'Export Design System Tokens to JSON Manifest',
    description: 'Master Orchestrator requested permission to write final theme variables to /public/design-tokens.json.',
    agentId: 'agent-master',
    agentName: 'Master Orchestrator',
    riskLevel: 'low',
    timestamp: '25 mins ago',
    status: 'pending',
    intent: 'Provide standardized color palette and font typography rules for external documentation.',
    plannedAction: 'Generate and save 128-line JSON file to public root.',
    permissionScopes: ['Write Public Directory'],
    toolName: 'filesystem-access',
    workspaceScope: '/public',
    governanceChecks: [
      { label: 'No Overwrite Conflict', passed: true, detail: 'Target file does not exist; clean write.' }
    ]
  }
];

export const INITIAL_MEMORIES: MemoryItem[] = [
  {
    id: 'mem-01',
    title: 'Dark Graphite Theme Palette Rules',
    snippet: 'Primary background must be #0a0a0a. Card surfaces use charcoal #171717 with rgba(255,255,255,0.07) border and backdrop-blur-12px. Never use pure black or stark white borders.',
    type: 'Decision',
    relevance: 99,
    tier: 'hot',
    source: 'Architectural Decision Record #12',
    timestamp: '10 mins ago',
    tags: ['Design System', 'Tokens', 'Glassmorphism'],
    pinned: true
  },
  {
    id: 'mem-02',
    title: 'Planning-First & Mock-Safe Execution Policy',
    snippet: 'All external tool calls (GitHub, Slack, Shell, Filesystem) must execute in dry-run Planning-First mode by default. High-risk operations must enter the Approval Queue before side effects trigger.',
    type: 'Decision',
    relevance: 96,
    tier: 'hot',
    source: 'Governance Safety Manifesto v2.4',
    timestamp: '1 hour ago',
    tags: ['Governance', 'Safety', 'Approvals'],
    pinned: true
  },
  {
    id: 'mem-03',
    title: 'User Preference: ChatGPT Agent Mode vs Dev Console',
    snippet: 'User prefers switching seamlessly between Simple Chat Mode (with live orchestration working cards) and Developer Mode Console (with step-by-step workflow trace inspector and tool call JSON tables).',
    type: 'Chat Memory',
    relevance: 94,
    tier: 'hot',
    source: 'Session #892 with Master Orchestrator',
    timestamp: '3 hours ago',
    tags: ['UX Preferences', 'Modes', 'Trace Inspector']
  },
  {
    id: 'mem-04',
    title: 'Lucide Icon Standard Enforcement',
    snippet: 'All UI components must import icons exclusively from lucide-react. Custom SVGs or external icon libraries are strictly prohibited to maintain bundle size and visual consistency.',
    type: 'Memory',
    relevance: 91,
    tier: 'warm',
    source: 'Frontend Guidelines v1.2',
    timestamp: 'Yesterday',
    tags: ['Icons', 'React', 'Standards']
  },
  {
    id: 'mem-05',
    title: 'Mission Control Task Graph Architecture',
    snippet: 'Tasks in a mission follow a 4-state lifecycle: Planned -> Running -> Waiting Approval -> Completed. Any failure triggers automated rollback and notifies the Governance Agent.',
    type: 'File Index',
    relevance: 88,
    tier: 'warm',
    source: '/src/types.ts line 14',
    timestamp: '2 days ago',
    tags: ['Mission Control', 'State Machine', 'Workflow']
  },
  {
    id: 'mem-06',
    title: 'MCP Connector Hub Security Sandbox',
    snippet: 'Connectors like GitHub, Linear, Slack, and Notion run in isolated Docker containers with OAuth scope trimming. Dry-check validation runs every 30 minutes.',
    type: 'Goal',
    relevance: 84,
    tier: 'archived',
    source: 'Infrastructure Roadmap 2026',
    timestamp: '5 days ago',
    tags: ['MCP', 'Connectors', 'Docker']
  }
];

export const INITIAL_CONNECTORS: ToolConnector[] = [
  {
    id: 'conn-github',
    name: 'GitHub Connector',
    category: 'MCP',
    status: 'connected',
    riskLevel: 'medium',
    description: 'Read repository file trees, scan pull requests, create draft branches, and index codebase structure.',
    icon: 'Github',
    permissions: ['repo:read', 'issues:write', 'pull_request:read'],
    dryCheckPassed: true,
    activeAgentsCount: 4,
    callsToday: 14,
    lastUsed: '4 mins ago'
  },
  {
    id: 'conn-fs',
    name: 'Filesystem Access',
    category: 'Local CLI',
    status: 'approval-gated',
    riskLevel: 'high',
    description: 'Read and write source files in /src directory. File modifications require automated AST syntax checks and user sign-off.',
    icon: 'FolderGit2',
    permissions: ['fs:read_workspace', 'fs:write_scoped', 'git:checkpoint'],
    dryCheckPassed: true,
    activeAgentsCount: 3,
    callsToday: 28,
    lastUsed: 'Just now'
  },
  {
    id: 'conn-postgres',
    name: 'Postgres Cloud DB',
    category: 'Database',
    status: 'connected',
    riskLevel: 'medium',
    description: 'Execute read-only SQL queries against application telemetry and agent metrics tables.',
    icon: 'Database',
    permissions: ['db:select', 'db:explain_query'],
    dryCheckPassed: true,
    activeAgentsCount: 2,
    callsToday: 19,
    lastUsed: '15 mins ago'
  },
  {
    id: 'conn-linear',
    name: 'Linear Task Sync',
    category: 'API',
    status: 'connected',
    riskLevel: 'low',
    description: 'Sync mission progress to Linear project boards and auto-create engineering tickets from blocked agent tasks.',
    icon: 'CheckSquare',
    permissions: ['issues:read', 'issues:create'],
    dryCheckPassed: true,
    activeAgentsCount: 2,
    callsToday: 8,
    lastUsed: '1 hour ago'
  },
  {
    id: 'conn-slack',
    name: 'Slack Workspace Bot',
    category: 'API',
    status: 'approval-gated',
    riskLevel: 'medium',
    description: 'Send draft summary notifications to #ai-updates channel when high-priority missions complete.',
    icon: 'MessageSquare',
    permissions: ['chat:postMessage', 'channels:read'],
    dryCheckPassed: true,
    activeAgentsCount: 1,
    callsToday: 3,
    lastUsed: '3 hours ago'
  },
  {
    id: 'conn-playwright',
    name: 'Playwright Browser',
    category: 'MCP',
    status: 'connected',
    riskLevel: 'low',
    description: 'Headless browser automation for visual regression testing, UI snapshot verification, and contrast audits.',
    icon: 'Monitor',
    permissions: ['browser:navigate', 'browser:screenshot'],
    dryCheckPassed: true,
    activeAgentsCount: 1,
    callsToday: 12,
    lastUsed: '20 mins ago'
  }
];

export const INITIAL_GOVERNANCE_LOGS: GovernanceEvent[] = [
  {
    id: 'gov-1001',
    timestamp: '11:32:04 AM',
    type: 'tool_call',
    agentName: 'UI Design Agent',
    action: 'component_generator --target=AgentsGrid',
    status: 'allowed',
    risk: 'low',
    details: 'Passed Mock-Safe sandboxing. Validated against design tokens.'
  },
  {
    id: 'gov-1002',
    timestamp: '11:28:15 AM',
    type: 'permission_check',
    agentName: 'Implementation Agent',
    action: 'github_connector --action=scan_repo',
    status: 'pending_review',
    risk: 'medium',
    details: 'Intercepted by Governance Policy: Outbound network call requires user approval in queue.'
  },
  {
    id: 'gov-1003',
    timestamp: '11:20:42 AM',
    type: 'safety_block',
    agentName: 'Implementation Agent',
    action: 'run_command "rm -rf /dist && npm run build"',
    status: 'blocked',
    risk: 'high',
    details: 'BLOCKED: Destructive shell command "rm -rf" is strictly forbidden under Safety Default Rules.'
  },
  {
    id: 'gov-1004',
    timestamp: '11:15:00 AM',
    type: 'approval_granted',
    agentName: 'Master Orchestrator',
    action: 'delegate_mission --id=mission-01',
    status: 'allowed',
    risk: 'low',
    details: 'User approved task delegation to 5 specialized sub-agents.'
  },
  {
    id: 'gov-1005',
    timestamp: '11:04:19 AM',
    type: 'tool_call',
    agentName: 'Memory Agent',
    action: 'vector_db_scanner --path=/src',
    status: 'mock_executed',
    risk: 'low',
    details: 'Executed in Read-Only indexer mode. 19 files parsed and embedded.'
  },
  {
    id: 'gov-1006',
    timestamp: '10:48:30 AM',
    type: 'audit_log',
    agentName: 'Governance Agent',
    action: 'System Routine Audit Check',
    status: 'allowed',
    risk: 'low',
    details: 'All 7 connected tools verified against global permission profiles. Score: 98/100 A+.'
  }
];

export const INITIAL_TRACE_STEPS: TraceStep[] = [
  {
    step: 1,
    id: 'tr-01',
    timestamp: '11:30:01 AM',
    agent: 'Master Orchestrator',
    action: 'Receive user prompt & classify intent',
    status: 'success',
    durationMs: 140,
    inputSnippet: '"Redesign EvolveAgent AI Workspace UI with dark graphite theme and 11 screens"',
    outputSnippet: 'Intent: Full-stack UI implementation. Mission ID: mission-01 created.'
  },
  {
    step: 2,
    id: 'tr-02',
    timestamp: '11:30:02 AM',
    agent: 'Master Orchestrator',
    action: 'Generate tool execution plan & delegate sub-tasks',
    status: 'success',
    durationMs: 280,
    toolUsed: 'Task Delegation CLI',
    inputSnippet: 'Deconstruct into 7 atomic tasks across 4 specialized agents.',
    outputSnippet: 'Tasks assigned to UI Design Agent, Memory Agent, and Implementation Agent.'
  },
  {
    step: 3,
    id: 'tr-03',
    timestamp: '11:30:03 AM',
    agent: 'Memory Agent',
    action: 'Retrieve architectural decisions & theme tokens from Project Brain',
    status: 'success',
    durationMs: 310,
    toolUsed: 'Semantic Search Engine',
    inputSnippet: 'Query: "Dark graphite theme color palette and glassmorphism rules"',
    outputSnippet: 'Retrieved ADR #12: #0a0a0a background, #171717 charcoal cards, border-white/8.'
  },
  {
    step: 4,
    id: 'tr-04',
    timestamp: '11:30:04 AM',
    agent: 'UI Design Agent',
    action: 'Synthesize layout component hierarchy & responsive grid',
    status: 'success',
    durationMs: 520,
    toolUsed: 'Component Generator',
    inputSnippet: 'Generate Sidebar, TopBar, GlassCard, and HomeDashboard layout.',
    outputSnippet: 'Component JSX synthesized with Tailwind v4 utility classes.'
  },
  {
    step: 5,
    id: 'tr-05',
    timestamp: '11:30:05 AM',
    agent: 'Governance Agent',
    action: 'Validate tool calls against Mock-Safe sandboxing rules',
    status: 'running',
    durationMs: 180,
    toolUsed: 'Permission Policy Engine',
    inputSnippet: 'Check write permission on /src/components/layout/Sidebar.tsx',
    outputSnippet: 'Status: INTERCEPTED. Action routed to Approval Queue (Medium Risk).'
  },
  {
    step: 6,
    id: 'tr-06',
    timestamp: '11:30:06 AM',
    agent: 'Implementation Agent',
    action: 'Wait for user approval before writing file modifications',
    status: 'waiting',
    durationMs: 0,
    toolUsed: 'Filesystem Access CLI',
    inputSnippet: 'Waiting on Approval ID #app-02...',
    outputSnippet: 'No side effects executed. Zero state divergence.'
  }
];

export const INITIAL_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-01',
    sender: 'user',
    text: 'Let’s start designing the new EvolveAgent AI workspace. Make sure it has a dark graphite theme, purple/blue glow accents, and full observability over all our agents and tool calls.',
    timestamp: '11:28 AM'
  },
  {
    id: 'msg-02',
    sender: 'agent',
    agentName: 'Master Orchestrator',
    avatar: '🤖',
    text: 'Understood. I have initiated **Mission #01: Redesign EvolveAgent AI Workspace UI**. I have retrieved our design system decisions from Project Brain (ADR #12) and delegated sub-tasks to the UI Design Agent, Memory Agent, Governance Agent, and Implementation Agent.\n\nHere is our active orchestration status:',
    timestamp: '11:29 AM',
    isWorkingCard: true
  },
  {
    id: 'msg-03',
    sender: 'agent',
    agentName: 'UI Design Agent',
    avatar: '🎨',
    text: 'I’ve generated the 11 core screens with responsive glassmorphism cards (`#171717` with `border-white/[0.07]`). Notice that our **Planning-First Mode** is enabled: no filesystem writes will occur until you review and approve them in the Approvals queue or directly from this chat card!',
    timestamp: '11:30 AM'
  }
];

export const SYSTEM_METRICS: SystemMetric[] = [
  { label: 'Active Agents', value: '08', trend: '+2 today', isPositive: true, subtitle: '4 executing now' },
  { label: 'Running Tasks', value: '03', trend: '2 waiting', subtitle: '62% mission complete' },
  { label: 'Pending Approvals', value: '05', trend: '1 high risk', isPositive: false, subtitle: 'Avg review: 42s' },
  { label: 'Connected Tools', value: '07', trend: 'All safe', isPositive: true, subtitle: '32 calls today' },
  { label: 'System Health', value: '98%', trend: 'Score A+', isPositive: true, subtitle: 'Governance active' }
];
