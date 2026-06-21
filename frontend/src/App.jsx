import React, { useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  Activity,
  BarChart3,
  Bot,
  Brain,
  ChevronDown,
  Clock,
  Copy,
  Cpu,
  Database,
  Download,
  Edit3,
  FileText,
  Flag,
  Gauge,
  GitBranch,
  Keyboard,
  Layers3,
  Library,
  Menu,
  Moon,
  MoreHorizontal,
  Paperclip,
  Mic,
  MessageSquarePlus,
  PanelRight,
  Route,
  RefreshCw,
  Send,
  ShieldAlert,
  Sparkles,
  Sun,
  Terminal,
  ThumbsDown,
  ThumbsUp,
  User,
  Trash2,
  X,
} from 'lucide-react'
import remarkGfm from 'remark-gfm'
import {
  API_BASE,
  createAppBuilderPlan,
  createDebateSession,
  createMemoryConsolidationJob,
  createResearchSession,
  createSimulationRun,
  createCustomAgent,
  createGoal,
  createWorkspace,
  createWorkspaceMemory,
  applyAutomation,
  approvePromptVersion,
  completeLinearIssue,
  getLinearCursorHandoff,
  verifyLinearCursorWork,
  createChat,
  deleteChat,
  deleteMessage,
  deleteWorkspace,
  deleteWorkspaceMemory,
  getAnalytics,
  getAgentTemplates,
  getAppBuilderTemplates,
  getChat,
  getChats,
  getCustomAgents,
  getGoal,
  getGoals,
  getHistory,
  getLearningReport,
  getDigitalTwinProfile,
  getMemoryConsolidationJobs,
  getLinearIssues,
  getLinearLinks,
  getLinearPollStatus,
  getLinearStatus,
  getCodexJobs,
  getDebateSummary,
  runCodexForLinearIssue,
  getApprovals,
  submitApprovalDecision,
  getApprovalAudit,
  getAgentJobs,
  getAgentJobHealth,
  createAgentJob,
  startNextAgentJob,
  pauseAgentJob,
  resumeAgentJob,
  cancelAgentJob,
  heartbeatAgentJob,
  getSystemPrompts,
  getSystemPrompt,
  upsertSystemPrompt,
  getToolHistory,
  getToolSummary,
  maintainWorkspaceMemoryTiers,
  getProviderStatus,
  runProviderSmokeTest,
  getImageProviderStatus,
  runImageSmokeTest,
  refreshDigitalTwinProfile,
  getTranscriptionProviderStatus,
  runTranscriptionSmokeTest,
  getRealApiSummary,
  getRealApiLiveWarning,
  getResearchReport,
  getResearchSessions,
  getQualityStatus,
  getWorkspaceMemory,
  getWorkspaceMemoryIntelligence,
  getWorkspaceKnowledge,
  searchWorkspaceKnowledge,
  exportWorkspaceKnowledge,
  getAssistantCommands,
  runAssistantCommand,
  archiveWorkspaceMemory,
  consolidateWorkspaceMemory,
  pinWorkspaceMemory,
  rebuildWorkspaceMemoryIndex,
  rescoreWorkspaceMemory,
  applyMemoryConsolidationJob,
  getWorkspaces,
  rejectPromptVersion,
  approveResearchSession,
  rejectResearchSession,
  runSessionControlledSearch,
  renameChat,
  rollbackPromptVersion,
  runGoalTask,
  runLinearIssue,
  runLinearPollOnce,
  runQualityChecks,
  runWorkflow,
  scaffoldAppBuilderPlan,
  selectLinearIssue,
  sendFeedback,
  syncLinearIssue,
  updateWorkspace,
  updateDigitalTwinProfile,
  updateWorkspaceMemory,
  updateGoalTask,
  uploadFiles,
  uploadRecordings,
} from './api'

const taskTypes = [
  'auto',
  'goal_planning',
  'resume',
  'coding',
  'business',
  'research',
  'finance',
  'pharmacy',
  'image_generation',
  'app_automation',
  'recording_summary',
  'system_explanation',
  'document_analysis',
  'file_summary',
  'resume_review',
  'code_review',
  'data_analysis',
  'general',
]

const promptCards = [
  'Explain how EvolveAgent AI works',
  'Improve my resume for a software engineering internship',
  'Review my FastAPI backend architecture',
  'Analyze a business idea and find risks',
  'Create a 2-minute project demo script',
  'Generate an image prompt for a futuristic AI assistant',
  'Add a small settings panel to this app',
  'Summarize this recording',
  'Upload a resume and ask for improvements',
  'Upload a CSV and analyze patterns',
  'Upload a code file and explain it',
  'Build an AI resume analyzer app',
  'Create a full implementation plan for a SaaS app',
]

const ONBOARDING_STEPS = [
  {
    title: 'Speak or Type',
    body: 'Simple Mode opens with a voice-first command center. Tap Speak for microphone input or Type to focus the composer.',
  },
  {
    title: 'Developer Mode',
    body: 'Switch to Dev for the engineering dashboard: inspector, tool trace, approvals, analytics, and raw run JSON.',
  },
  {
    title: 'Mission Control',
    body: 'Create goals, run tasks, and track completion. Linear-linked issues sync branches and handoffs when configured.',
  },
  {
    title: 'Knowledge Base',
    body: 'Search workspace knowledge and manage pinned memory to give EvolveAgent stronger project context.',
  },
  {
    title: 'Agent Jobs',
    body: 'Queue, start, pause, and monitor background agent jobs from the Developer sidebar when the scheduler is enabled.',
  },
]

function codexJobDisplayStatus(job) {
  const status = job?.status
  if (status === 'blocked') return 'needs manual review'
  if (status === 'passed' && !job.linear_done) return 'needs manual review'
  if (status === 'failed') return 'failed'
  if (status === 'passed') return 'passed'
  if (status === 'running') return 'running'
  if (status === 'queued') return 'queued'
  return 'idle'
}

function codexWorkerSummaryStatus(jobs) {
  if (!jobs.length) return 'idle'
  if (jobs.some((job) => job.status === 'running')) return 'running'
  if (jobs.some((job) => job.status === 'queued')) return 'queued'
  if (jobs.some((job) => job.status === 'blocked' || (job.status === 'passed' && !job.linear_done))) {
    return 'needs manual review'
  }
  if (jobs.some((job) => job.status === 'failed')) return 'failed'
  if (jobs.every((job) => job.status === 'passed')) return 'passed'
  return 'idle'
}

function codexTestResult(job, command) {
  return (job.test_results || []).find((item) => item.command === command)
}

const progressSteps = [
  'Master Agent is understanding your request',
  'Task type is being detected',
  'Specialist agents are analyzing',
  'Judge Agent is reviewing quality',
  'Evolution Agent is preparing improvement notes',
  'Memory Agent is saving the result',
  'Final answer is ready',
]

function formatType(type = '') {
  return type.replaceAll('_', ' ')
}

function formatSimpleAnswer(result, fallback = '') {
  if (!result) return fallback
  if (result.image_result) {
    return result.final_output || 'I created an image preview using a safe image prompt.'
  }
  return (result.final_output || fallback || '').replace(/The Master Agent classified this as .*?\.\s*/gi, '').trim()
}

function assetUrl(path = '') {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${API_BASE}${path}`
}

function runModeLabel(result, fallbackMode) {
  if (result?.image_result) {
    return result.image_result.provider
  }
  return fallbackMode
}

function capabilityModeLabel(label, status, modeKey, activeKey) {
  if (!status) return `${label}: checking`
  const mode = status[modeKey] || 'unknown'
  const active = status[activeKey] || ''
  return active ? `${label}: ${mode} (${active})` : `${label}: ${mode}`
}

function messageKey(message) {
  return message.message_id || message.id
}

function CodeBlock({ inline, className = '', children }) {
  const code = String(children).replace(/\n$/, '')
  const language = /language-(\w+)/.exec(className)?.[1] || 'code'
  if (inline) {
    return <code className="inline-code">{children}</code>
  }
  return (
    <div className="code-block">
      <div className="code-toolbar">
        <span>{language}</span>
        <button type="button" onClick={() => navigator.clipboard.writeText(code)}>
          Copy code
        </button>
      </div>
      <pre>
        <code className={className}>{code}</code>
      </pre>
    </div>
  )
}

function MarkdownMessage({ content }) {
  return (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: CodeBlock }}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

function App() {
  const [input, setInput] = useState('')
  const [taskType, setTaskType] = useState('auto')
  const [deepMode, setDeepMode] = useState(false)
  const [developerMode, setDeveloperMode] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('evolveagent-theme') || 'dark')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(() => !localStorage.getItem('evolveagent-onboarding-dismissed'))
  const [onboardingStep, setOnboardingStep] = useState(0)
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [selectedRunId, setSelectedRunId] = useState(null)
  const [chats, setChats] = useState([])
  const [history, setHistory] = useState([])
  const [providerStatus, setProviderStatus] = useState(null)
  const [providerCheck, setProviderCheck] = useState(null)
  const [providerCheckBusy, setProviderCheckBusy] = useState(false)
  const [imageProviderStatus, setImageProviderStatus] = useState(null)
  const [imageProviderCheck, setImageProviderCheck] = useState(null)
  const [imageProviderBusy, setImageProviderBusy] = useState(false)
  const [transcriptionProviderStatus, setTranscriptionProviderStatus] = useState(null)
  const [transcriptionProviderCheck, setTranscriptionProviderCheck] = useState(null)
  const [transcriptionProviderBusy, setTranscriptionProviderBusy] = useState(false)
  const [realApiSummary, setRealApiSummary] = useState(null)
  const [realApiWarning, setRealApiWarning] = useState(null)
  const [realApiWarningBusy, setRealApiWarningBusy] = useState(false)
  const [analytics, setAnalytics] = useState(null)
  const [learningReport, setLearningReport] = useState(null)
  const [digitalTwinProfile, setDigitalTwinProfile] = useState(null)
  const [digitalTwinBusy, setDigitalTwinBusy] = useState(false)
  const [digitalTwinError, setDigitalTwinError] = useState('')
  const [showAnalytics, setShowAnalytics] = useState(false)
  const [loading, setLoading] = useState(false)
  const [progressIndex, setProgressIndex] = useState(0)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState('')
  const [showRawJson, setShowRawJson] = useState(false)
  const [attachedFiles, setAttachedFiles] = useState([])
  const [attachedRecordings, setAttachedRecordings] = useState([])
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const [uploadingRecordings, setUploadingRecordings] = useState(false)
  const [voiceUsed, setVoiceUsed] = useState(false)
  const [voiceTranscript, setVoiceTranscript] = useState('')
  const [listening, setListening] = useState(false)
  const [automationResults, setAutomationResults] = useState({})
  const [goals, setGoals] = useState([])
  const [selectedGoal, setSelectedGoal] = useState(null)
  const [customAgents, setCustomAgents] = useState([])
  const [agentTemplates, setAgentTemplates] = useState([])
  const [showMissionControl, setShowMissionControl] = useState(false)
  const [showApprovals, setShowApprovals] = useState(false)
  const [approvals, setApprovals] = useState([])
  const [approvalsAvailable, setApprovalsAvailable] = useState(false)
  const [approvalAudit, setApprovalAudit] = useState([])
  const [approvalAuditAvailable, setApprovalAuditAvailable] = useState(false)
  const [approvalBusyId, setApprovalBusyId] = useState('')
  const [showAgentJobs, setShowAgentJobs] = useState(false)
  const [agentJobs, setAgentJobs] = useState([])
  const [agentJobsAvailable, setAgentJobsAvailable] = useState(false)
  const [agentJobHealth, setAgentJobHealth] = useState(null)
  const [agentJobBusyId, setAgentJobBusyId] = useState('')
  const [showSystemPrompts, setShowSystemPrompts] = useState(false)
  const [systemPrompts, setSystemPrompts] = useState([])
  const [systemPromptsAvailable, setSystemPromptsAvailable] = useState(false)
  const [selectedPromptAgent, setSelectedPromptAgent] = useState('')
  const [promptDraft, setPromptDraft] = useState('')
  const [promptSaveBusy, setPromptSaveBusy] = useState(false)
  const [showAgentBuilder, setShowAgentBuilder] = useState(false)
  const [workspaces, setWorkspaces] = useState([])
  const [workspaceId, setWorkspaceId] = useState(null)
  const [workspaceMemory, setWorkspaceMemory] = useState([])
  const [showMemoryPanel, setShowMemoryPanel] = useState(false)
  const [showKnowledgePanel, setShowKnowledgePanel] = useState(false)
  const [knowledgeSummary, setKnowledgeSummary] = useState(null)
  const [knowledgeSearch, setKnowledgeSearch] = useState('')
  const [knowledgeSource, setKnowledgeSource] = useState('')
  const [knowledgeResults, setKnowledgeResults] = useState([])
  const [knowledgeLinks, setKnowledgeLinks] = useState([])
  const [showToolsPanel, setShowToolsPanel] = useState(false)
  const [assistantCommands, setAssistantCommands] = useState([])
  const [toolHistory, setToolHistory] = useState([])
  const [toolSummary, setToolSummary] = useState(null)
  const [toolHistoryUpdatedAt, setToolHistoryUpdatedAt] = useState('')
  const [toolHistoryBusy, setToolHistoryBusy] = useState(false)
  const [selectedCommand, setSelectedCommand] = useState('help')
  const [commandInput, setCommandInput] = useState('')
  const [commandResult, setCommandResult] = useState(null)
  const [showQualityPanel, setShowQualityPanel] = useState(false)
  const [qualityStatus, setQualityStatus] = useState(null)
  const [qualityBusy, setQualityBusy] = useState(false)
  const [qualityError, setQualityError] = useState('')
  const [showAppBuilder, setShowAppBuilder] = useState(false)
  const [appBuilderTemplates, setAppBuilderTemplates] = useState([])
  const [appBuilderPrompt, setAppBuilderPrompt] = useState('Build an AI resume analyzer app with upload, dashboard, and chat')
  const [appBuilderStack, setAppBuilderStack] = useState('fastapi-react')
  const [appBuilderPlan, setAppBuilderPlan] = useState(null)
  const [appBuilderResult, setAppBuilderResult] = useState(null)
  const [appBuilderBusy, setAppBuilderBusy] = useState(false)
  const [appBuilderError, setAppBuilderError] = useState('')
  const [showDebatePanel, setShowDebatePanel] = useState(false)
  const [debatePrompt, setDebatePrompt] = useState('Debate whether we should automate this workflow now or simulate it first')
  const [simulationScenario, setSimulationScenario] = useState('No file edits, commands, or external calls during simulation')
  const [debateSummary, setDebateSummary] = useState(null)
  const [debateResult, setDebateResult] = useState(null)
  const [simulationResult, setSimulationResult] = useState(null)
  const [debateBusy, setDebateBusy] = useState(false)
  const [debateError, setDebateError] = useState('')
  const [showResearchPanel, setShowResearchPanel] = useState(false)
  const [researchQuery, setResearchQuery] = useState('Research real API provider readiness and summarize trustworthy sources')
  const [researchSessions, setResearchSessions] = useState([])
  const [researchReport, setResearchReport] = useState(null)
  const [researchBusy, setResearchBusy] = useState(false)
  const [researchError, setResearchError] = useState('')
  const composerRef = useRef(null)
  const [memorySearch, setMemorySearch] = useState('')
  const [memoryType, setMemoryType] = useState('')
  const [memoryTier, setMemoryTier] = useState('')
  const [memoryIntelligence, setMemoryIntelligence] = useState(null)
  const [memoryConsolidationJobs, setMemoryConsolidationJobs] = useState([])
  const [memoryBusy, setMemoryBusy] = useState(false)
  const [linearStatus, setLinearStatus] = useState(null)
  const [linearIssues, setLinearIssues] = useState([])
  const [linearLinks, setLinearLinks] = useState([])
  const [linearPollStatus, setLinearPollStatus] = useState(null)
  const [codexJobs, setCodexJobs] = useState([])
  const [codexJobsAvailable, setCodexJobsAvailable] = useState(false)
  const [showCodexJobs, setShowCodexJobs] = useState(false)
  const [linearBusyId, setLinearBusyId] = useState('')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('evolveagent-theme', theme)
  }, [theme])

  useEffect(() => {
    if (!developerMode) setSidebarOpen(false)
  }, [developerMode])

  useEffect(() => {
    refreshWorkspaces()
    refreshProviderStatus()
    refreshLinearStatus()
    refreshAssistantCommands()
    refreshAppBuilderTemplates()
  }, [])

  useEffect(() => {
    if (!workspaceId) return
    setSessionId(null)
    setMessages([])
    setSelectedRunId(null)
    setSelectedGoal(null)
    refreshHistory()
    refreshChats(workspaceId)
    refreshAnalytics(workspaceId)
    refreshLearningReport(workspaceId)
    refreshDigitalTwin(workspaceId)
    refreshMissionControl(workspaceId)
    refreshCustomAgents(workspaceId)
    refreshWorkspaceMemory(workspaceId)
    refreshKnowledge(workspaceId)
    refreshLinearData(workspaceId)
    refreshDebateSummary(workspaceId)
    refreshResearchSessions(workspaceId)
  }, [workspaceId])

  useEffect(() => {
    if (!workspaceId || !developerMode) return
    refreshApprovals(workspaceId)
    refreshAgentJobs(workspaceId)
    refreshSystemPrompts()
    refreshToolHistory(workspaceId)
    refreshCodexJobs()
    refreshQualityStatus()
  }, [workspaceId, developerMode])

  useEffect(() => {
    if (!loading) return undefined
    const timer = window.setInterval(() => {
      setProgressIndex((current) => Math.min(current + 1, progressSteps.length - 1))
    }, 900)
    return () => window.clearInterval(timer)
  }, [loading])

  useEffect(() => {
    if (!workspaceId) return
    const timer = window.setTimeout(() => {
      refreshWorkspaceMemory(workspaceId)
    }, 250)
    return () => window.clearTimeout(timer)
  }, [memorySearch, memoryType, memoryTier, workspaceId])

  useEffect(() => {
    if (!workspaceId) return
    const timer = window.setTimeout(() => {
      refreshKnowledge(workspaceId)
    }, 250)
    return () => window.clearTimeout(timer)
  }, [knowledgeSearch, knowledgeSource, workspaceId])

  const selectedRun = useMemo(() => {
    const assistantMessages = messages.filter((message) => message.role === 'assistant' && message.result)
    const selectedMessage = assistantMessages.find((message) => message.id === selectedRunId) || assistantMessages.at(-1)
    return selectedMessage?.result
  }, [messages, selectedRunId])

  async function refreshHistory() {
    setHistory(await getHistory())
  }

  async function refreshWorkspaces() {
    const items = await getWorkspaces()
    setWorkspaces(items)
    if (!workspaceId && items.length > 0) {
      const defaultWorkspace = items.find((item) => item.default) || items[0]
      setWorkspaceId(defaultWorkspace.workspace_id)
    }
  }

  async function refreshProviderStatus() {
    setProviderStatus(await getProviderStatus())
    setImageProviderStatus(await getImageProviderStatus())
    setTranscriptionProviderStatus(await getTranscriptionProviderStatus())
    setRealApiSummary(await getRealApiSummary())
  }

  async function handleProviderCheck(provider) {
    setProviderCheckBusy(true)
    try {
      const result = await runProviderSmokeTest({ provider, live: false })
      setProviderCheck(result)
      await refreshProviderStatus()
    } catch (err) {
      setError(err.message)
    } finally {
      setProviderCheckBusy(false)
    }
  }

  async function handleImageProviderCheck() {
    setImageProviderBusy(true)
    try {
      const result = await runImageSmokeTest({ live: false })
      setImageProviderCheck(result)
      setImageProviderStatus(await getImageProviderStatus())
    } catch (err) {
      setError(err.message)
    } finally {
      setImageProviderBusy(false)
    }
  }

  async function handleTranscriptionProviderCheck() {
    setTranscriptionProviderBusy(true)
    try {
      const result = await runTranscriptionSmokeTest({ live: false })
      setTranscriptionProviderCheck(result)
      setTranscriptionProviderStatus(await getTranscriptionProviderStatus())
    } catch (err) {
      setError(err.message)
    } finally {
      setTranscriptionProviderBusy(false)
    }
  }

  async function handleRealApiWarning(capability) {
    setRealApiWarningBusy(true)
    try {
      setRealApiWarning(await getRealApiLiveWarning(capability))
    } catch (err) {
      setError(err.message)
    } finally {
      setRealApiWarningBusy(false)
    }
  }

  async function refreshAssistantCommands() {
    const commands = await getAssistantCommands()
    setAssistantCommands(commands)
    if (commands.length > 0 && !commands.find((command) => command.name === selectedCommand)) {
      setSelectedCommand(commands[0].name)
    }
  }

  async function refreshToolHistory(nextWorkspaceId = workspaceId) {
    if (!nextWorkspaceId) return
    setToolHistoryBusy(true)
    try {
      const [history, summary] = await Promise.all([
        getToolHistory(nextWorkspaceId, 20),
        getToolSummary(nextWorkspaceId),
      ])
      setToolHistory(history)
      setToolSummary(summary)
      setToolHistoryUpdatedAt(new Date().toLocaleTimeString())
    } finally {
      setToolHistoryBusy(false)
    }
  }

  async function refreshAnalytics(nextWorkspaceId = workspaceId) {
    setAnalytics(await getAnalytics(nextWorkspaceId))
  }

  async function refreshLearningReport(nextWorkspaceId = workspaceId) {
    setLearningReport(await getLearningReport(nextWorkspaceId))
  }

  async function refreshDigitalTwin(nextWorkspaceId = workspaceId) {
    if (!nextWorkspaceId) return
    try {
      setDigitalTwinProfile(await getDigitalTwinProfile(nextWorkspaceId))
      setDigitalTwinError('')
    } catch (err) {
      setDigitalTwinError(err.message)
    }
  }

  async function refreshQualityStatus() {
    setQualityStatus(await getQualityStatus())
  }

  async function refreshAppBuilderTemplates() {
    const templates = await getAppBuilderTemplates()
    setAppBuilderTemplates(templates)
    if (templates.length > 0 && !templates.find((template) => template.stack_id === appBuilderStack)) {
      setAppBuilderStack(templates[0].stack_id)
    }
  }

  async function refreshDebateSummary(nextWorkspaceId = workspaceId) {
    setDebateSummary(await getDebateSummary(nextWorkspaceId))
  }

  async function refreshResearchSessions(nextWorkspaceId = workspaceId) {
    setResearchSessions(await getResearchSessions(nextWorkspaceId))
  }

  async function refreshMissionControl(nextWorkspaceId = workspaceId) {
    setGoals(await getGoals(nextWorkspaceId))
  }

  async function refreshApprovals(nextWorkspaceId = workspaceId) {
    const [queue, audit] = await Promise.all([
      getApprovals(nextWorkspaceId),
      getApprovalAudit(nextWorkspaceId),
    ])
    setApprovalsAvailable(queue.available)
    setApprovals(queue.items || [])
    setApprovalAuditAvailable(audit.available)
    setApprovalAudit(audit.items || [])
  }

  async function handleApprovalDecision(approvalId, decision) {
    setApprovalBusyId(approvalId)
    setError('')
    try {
      const comment = window.prompt(`Optional comment for ${decision}:`, '') || undefined
      await submitApprovalDecision(approvalId, { decision, comment: comment?.trim() || undefined })
      await refreshApprovals(workspaceId)
    } catch (err) {
      setError(err.message)
    } finally {
      setApprovalBusyId('')
    }
  }

  const pendingApprovals = useMemo(
    () => approvals.filter((item) => item.status === 'pending'),
    [approvals],
  )

  async function refreshAgentJobs(nextWorkspaceId = workspaceId) {
    const [jobs, health] = await Promise.all([
      getAgentJobs(nextWorkspaceId),
      getAgentJobHealth(),
    ])
    setAgentJobsAvailable(jobs.available)
    setAgentJobs(jobs.items || [])
    setAgentJobHealth(health)
  }

  async function handleCreateTestAgentJob() {
    setAgentJobBusyId('create')
    setError('')
    try {
      await createAgentJob({
        title: 'Test agent job',
        job_type: 'health_check',
        workspace_id: workspaceId,
        payload: { source: 'developer_ui', note: 'Manual test job' },
      })
      await refreshAgentJobs(workspaceId)
      setCopied('Test agent job created')
      window.setTimeout(() => setCopied(''), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setAgentJobBusyId('')
    }
  }

  async function handleStartNextAgentJob() {
    setAgentJobBusyId('start-next')
    setError('')
    try {
      const result = await startNextAgentJob()
      if (!result.started) {
        setError(result.reason || 'No queued job could be started.')
      } else {
        setCopied('Next agent job started')
        window.setTimeout(() => setCopied(''), 2000)
      }
      await refreshAgentJobs(workspaceId)
    } catch (err) {
      setError(err.message)
    } finally {
      setAgentJobBusyId('')
    }
  }

  async function handleAgentJobAction(jobId, action) {
    setAgentJobBusyId(jobId)
    setError('')
    const reason = window.prompt(`Optional reason for ${action}:`, '') || undefined
    try {
      if (action === 'pause') await pauseAgentJob(jobId, reason?.trim() || undefined)
      if (action === 'resume') await resumeAgentJob(jobId, reason?.trim() || undefined)
      if (action === 'cancel') await cancelAgentJob(jobId, reason?.trim() || undefined)
      if (action === 'heartbeat') await heartbeatAgentJob(jobId)
      await refreshAgentJobs(workspaceId)
    } catch (err) {
      setError(err.message)
    } finally {
      setAgentJobBusyId('')
    }
  }

  async function refreshSystemPrompts() {
    const prompts = await getSystemPrompts()
    setSystemPromptsAvailable(prompts.available)
    setSystemPrompts(prompts.items || [])
  }

  async function handleSelectSystemPrompt(agentName) {
    setSelectedPromptAgent(agentName)
    setError('')
    try {
      const result = await getSystemPrompt(agentName)
      setPromptDraft(result.prompt || '')
    } catch (err) {
      const local = systemPrompts.find((item) => item.agent_name === agentName)
      setPromptDraft(local?.prompt || '')
      if (!local) setError(err.message)
    }
  }

  async function handleSaveSystemPrompt() {
    if (!selectedPromptAgent || !promptDraft.trim()) return
    setPromptSaveBusy(true)
    setError('')
    try {
      const reason = window.prompt('Optional reason for prompt update:', '') || undefined
      await upsertSystemPrompt({
        agent_name: selectedPromptAgent,
        prompt: promptDraft.trim(),
        reason: reason?.trim() || undefined,
      })
      await refreshSystemPrompts()
      setCopied(`Prompt saved for ${selectedPromptAgent}`)
      window.setTimeout(() => setCopied(''), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setPromptSaveBusy(false)
    }
  }

  async function refreshCustomAgents(nextWorkspaceId = workspaceId) {
    setCustomAgents(await getCustomAgents(nextWorkspaceId))
    setAgentTemplates(await getAgentTemplates())
  }

  async function refreshCodexJobs() {
    const result = await getCodexJobs()
    setCodexJobsAvailable(result.available)
    setCodexJobs(result.items || [])
  }

  async function refreshLinearStatus() {
    setLinearStatus(await getLinearStatus())
  }

  async function refreshLinearData(nextWorkspaceId = workspaceId) {
    const status = await getLinearStatus()
    setLinearStatus(status)
    setLinearLinks(await getLinearLinks(nextWorkspaceId))
    setLinearPollStatus(await getLinearPollStatus())
    if (status?.configured) {
      try {
        setLinearIssues(await getLinearIssues())
      } catch {
        setLinearIssues([])
      }
    } else {
      setLinearIssues([])
    }
  }

  async function handleLinearAction(action, issueId) {
    setLinearBusyId(issueId)
    setError('')
    try {
      if (action === 'sync') await syncLinearIssue(issueId, workspaceId)
      if (action === 'select') await selectLinearIssue(issueId, workspaceId)
      if (action === 'run') await runLinearIssue(issueId, workspaceId)
      if (action === 'complete') await completeLinearIssue(issueId)
      if (action === 'cursor-handoff') await handleCopyCursorHandoff(issueId)
      if (action === 'cursor-verify') await handleVerifyCursorWork(issueId)
      await refreshLinearData(workspaceId)
      await refreshMissionControl(workspaceId)
      await refreshAnalytics(workspaceId)
      await refreshLearningReport(workspaceId)
    } catch (err) {
      setError(err.message)
    } finally {
      setLinearBusyId('')
    }
  }

  async function handleCopyCursorHandoff(issueId, variant = 'cursor') {
    const handoff = await getLinearCursorHandoff(issueId)
    const text = variant === 'codex' ? handoff.codex_prompt : handoff.cursor_prompt
    if (!text) throw new Error('Cursor handoff not available yet. Move issue to In Progress or Select first.')
    await navigator.clipboard.writeText(text)
    setCopied(`${variant === 'codex' ? 'Codex' : 'Cursor'} prompt copied`)
    window.setTimeout(() => setCopied(''), 2000)
    return handoff
  }

  async function handleVerifyCursorWork(issueId) {
    const note = window.prompt(
      'Optional: what did Cursor/Codex change and how was it tested?',
      '',
    )
    const autoCommit = window.confirm('Auto-commit safe staged files if verification passes?')
    const result = await verifyLinearCursorWork(issueId, {
      completion_note: note?.trim() || undefined,
      auto_commit: autoCommit,
    })
    if (result.verified) {
      setCopied(`Verified — Linear ${result.linear_completion?.identifier || 'issue'} marked Done`)
    } else {
      setError('Verification failed. Fix tests/build, then try again.')
    }
    window.setTimeout(() => setCopied(''), 2500)
    return result
  }

  function linearLinkForIssue(issueId) {
    return linearLinks.find((item) => item.linear_issue_id === issueId)
  }

  function latestCodexJobForIssue(issueId) {
    return codexJobs.find((item) => item.issue_id === issueId)
  }

  async function handleRunAutonomousCodex(issueId) {
    setLinearBusyId(issueId)
    setError('')
    try {
      const result = await runCodexForLinearIssue(issueId)
      const job = result.job
      if (job?.status === 'passed') {
        setCopied(`Codex worker passed — ${job.issue_identifier} marked Done in Linear`)
      } else if (job?.error) {
        setError(job.error)
      } else if (result.error) {
        setError(result.error)
      }
      await refreshCodexJobs()
      await refreshLinearData(workspaceId)
      window.setTimeout(() => setCopied(''), 3000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLinearBusyId('')
    }
  }

  function linearLinkForGoal(goalId) {
    return linearLinks.find((item) => item.goal_id === goalId)
  }

  async function refreshWorkspaceMemory(nextWorkspaceId = workspaceId) {
    if (!nextWorkspaceId) return
    const [memories, intelligence] = await Promise.all([
      getWorkspaceMemory(nextWorkspaceId, {
        q: memorySearch,
        memory_type: memoryType,
        tier: memoryTier,
      }),
      getWorkspaceMemoryIntelligence(nextWorkspaceId),
    ])
    setWorkspaceMemory(memories)
    setMemoryIntelligence(intelligence)
    setMemoryConsolidationJobs(await getMemoryConsolidationJobs(nextWorkspaceId))
  }

  async function refreshKnowledge(nextWorkspaceId = workspaceId) {
    if (!nextWorkspaceId) return
    const [summary, search] = await Promise.all([
      getWorkspaceKnowledge(nextWorkspaceId),
      searchWorkspaceKnowledge(nextWorkspaceId, {
        q: knowledgeSearch,
        source_type: knowledgeSource,
        limit: 10,
      }),
    ])
    setKnowledgeSummary(summary)
    setKnowledgeResults(search.results || [])
    setKnowledgeLinks(search.related_links || [])
  }

  async function handleExportKnowledge(format) {
    try {
      const exported = await exportWorkspaceKnowledge(workspaceId, format)
      const filename = `workspace-knowledge.${format === 'json' ? 'json' : 'md'}`
      const text = format === 'json' ? JSON.stringify(exported, null, 2) : exported
      downloadFile(filename, text, format === 'json' ? 'application/json' : 'text/markdown')
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRunAssistantCommand() {
    try {
      const result = await runAssistantCommand(selectedCommand, {
        input_text: commandInput,
        workspace_id: workspaceId,
      })
      setCommandResult(result)
      await refreshToolHistory(workspaceId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRunQualityChecks() {
    setQualityBusy(true)
    setQualityError('')
    try {
      const result = await runQualityChecks({ commands: ['pytest', 'npm run build'] })
      setQualityStatus((current) => ({
        ...(current || {}),
        latest_run: result,
      }))
      await refreshQualityStatus()
    } catch (err) {
      setQualityError(err.message)
    } finally {
      setQualityBusy(false)
    }
  }

  async function handleCreateAppBuilderPlan() {
    setAppBuilderBusy(true)
    setAppBuilderError('')
    setAppBuilderResult(null)
    try {
      const plan = await createAppBuilderPlan({
        prompt: appBuilderPrompt,
        stack_id: appBuilderStack,
        workspace_id: workspaceId,
      })
      setAppBuilderPlan(plan)
    } catch (err) {
      setAppBuilderError(err.message)
    } finally {
      setAppBuilderBusy(false)
    }
  }

  async function handleScaffoldAppBuilderPlan() {
    if (!appBuilderPlan?.plan_id) return
    setAppBuilderBusy(true)
    setAppBuilderError('')
    try {
      const result = await scaffoldAppBuilderPlan({ plan_id: appBuilderPlan.plan_id, approved: true })
      setAppBuilderResult(result)
      setAppBuilderPlan(result.plan || appBuilderPlan)
    } catch (err) {
      setAppBuilderError(err.message)
    } finally {
      setAppBuilderBusy(false)
    }
  }

  async function handleCreateDebateSession() {
    setDebateBusy(true)
    setDebateError('')
    try {
      const result = await createDebateSession({ prompt: debatePrompt, workspace_id: workspaceId })
      setDebateResult(result)
      await refreshDebateSummary(workspaceId)
    } catch (err) {
      setDebateError(err.message)
    } finally {
      setDebateBusy(false)
    }
  }

  async function handleCreateSimulationRun() {
    setDebateBusy(true)
    setDebateError('')
    try {
      const result = await createSimulationRun({
        prompt: debatePrompt,
        scenario: simulationScenario,
        workspace_id: workspaceId,
      })
      setSimulationResult(result)
      await refreshDebateSummary(workspaceId)
    } catch (err) {
      setDebateError(err.message)
    } finally {
      setDebateBusy(false)
    }
  }

  async function handleCreateResearchSession() {
    if (!researchQuery.trim()) return
    setResearchBusy(true)
    setResearchError('')
    try {
      const session = await createResearchSession({
        query: researchQuery,
        workspace_id: workspaceId,
        require_approval: true,
      })
      setResearchReport(await getResearchReport(session.research_id))
      await refreshResearchSessions(workspaceId)
    } catch (err) {
      setResearchError(err.message)
    } finally {
      setResearchBusy(false)
    }
  }

  async function handleResearchDecision(researchId, decision) {
    setResearchBusy(true)
    setResearchError('')
    try {
      const session = decision === 'approve'
        ? await approveResearchSession(researchId)
        : await rejectResearchSession(researchId)
      setResearchReport(await getResearchReport(session.research_id))
      await refreshResearchSessions(workspaceId)
    } catch (err) {
      setResearchError(err.message)
    } finally {
      setResearchBusy(false)
    }
  }

  async function handleViewResearchReport(researchId) {
    setResearchBusy(true)
    setResearchError('')
    try {
      setResearchReport(await getResearchReport(researchId))
    } catch (err) {
      setResearchError(err.message)
    } finally {
      setResearchBusy(false)
    }
  }

  async function handleRunControlledSearch(researchId, query) {
    setResearchBusy(true)
    setResearchError('')
    try {
      const updated = await runSessionControlledSearch(researchId, {
        query: query,
        workspace_id: workspaceId,
        max_results: 5,
      })
      setResearchReport(await getResearchReport(updated.research_id))
      await refreshResearchSessions(workspaceId)
    } catch (err) {
      setResearchError(err.message)
    } finally {
      setResearchBusy(false)
    }
  }

  async function handleCreateWorkspace() {
    const name = window.prompt('Workspace name', 'New Workspace')
    if (!name?.trim()) return
    try {
      const workspace = await createWorkspace({ name: name.trim(), description: '' })
      await refreshWorkspaces()
      setWorkspaceId(workspace.workspace_id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRenameWorkspace() {
    const current = workspaces.find((item) => item.workspace_id === workspaceId)
    if (!current) return
    const name = window.prompt('Rename workspace', current.name)
    if (!name?.trim()) return
    try {
      await updateWorkspace(workspaceId, { name: name.trim() })
      await refreshWorkspaces()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleArchiveWorkspace() {
    const current = workspaces.find((item) => item.workspace_id === workspaceId)
    if (!current || current.default) return
    try {
      await deleteWorkspace(workspaceId)
      const next = workspaces.find((item) => item.default) || workspaces.find((item) => item.workspace_id !== workspaceId)
      setWorkspaceId(next?.workspace_id || null)
      await refreshWorkspaces()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleAddMemory() {
    if (!workspaceId) return
    const title = window.prompt('Memory title')
    if (!title?.trim()) return
    const content = window.prompt('Memory content')
    if (!content?.trim()) return
    try {
      await createWorkspaceMemory(workspaceId, {
        title: title.trim(),
        content: content.trim(),
        type: 'project_fact',
        source: 'manual',
        importance: 'medium',
        tags: [],
      })
      await refreshWorkspaceMemory(workspaceId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleEditMemory(memory) {
    const content = window.prompt('Edit memory content', memory.content)
    if (!content?.trim()) return
    try {
      await updateWorkspaceMemory(workspaceId, memory.memory_id, { content: content.trim() })
      await refreshWorkspaceMemory(workspaceId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDeleteMemory(memoryId) {
    try {
      await deleteWorkspaceMemory(workspaceId, memoryId)
      await refreshWorkspaceMemory(workspaceId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleToggleMemoryPin(memory) {
    try {
      await pinWorkspaceMemory(workspaceId, memory.memory_id, !memory.pinned)
      await refreshWorkspaceMemory(workspaceId)
      await refreshKnowledge(workspaceId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRescoreMemory() {
    if (!workspaceId) return
    setMemoryBusy(true)
    try {
      const result = await rescoreWorkspaceMemory(workspaceId)
      setMemoryIntelligence(result)
      await refreshWorkspaceMemory(workspaceId)
      setCopied('Memory re-scored')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setError(err.message)
    } finally {
      setMemoryBusy(false)
    }
  }

  async function handleMaintainMemoryTiers() {
    if (!workspaceId) return
    setMemoryBusy(true)
    try {
      const result = await maintainWorkspaceMemoryTiers(workspaceId)
      setMemoryIntelligence(result)
      await refreshWorkspaceMemory(workspaceId)
      setCopied(`${result.tier_transitions?.length || 0} tier transition(s) applied`)
      window.setTimeout(() => setCopied(''), 1600)
    } catch (err) {
      setError(err.message)
    } finally {
      setMemoryBusy(false)
    }
  }

  async function handleConsolidateMemory(approved = false) {
    if (!workspaceId) return
    setMemoryBusy(true)
    try {
      const result = await consolidateWorkspaceMemory(workspaceId, approved)
      setMemoryIntelligence((current) => ({
        ...(current || {}),
        suggested_consolidations: result.groups || [],
      }))
      await refreshWorkspaceMemory(workspaceId)
      setCopied(approved ? 'Duplicate memories archived' : 'Consolidation preview ready')
      window.setTimeout(() => setCopied(''), 1600)
    } catch (err) {
      setError(err.message)
    } finally {
      setMemoryBusy(false)
    }
  }

  async function handleCreateConsolidationJob(apply = false) {
    if (!workspaceId) return
    setMemoryBusy(true)
    try {
      await createMemoryConsolidationJob(workspaceId, apply)
      await refreshWorkspaceMemory(workspaceId)
      setCopied(apply ? 'Consolidation job completed' : 'Consolidation job created')
      window.setTimeout(() => setCopied(''), 1600)
    } catch (err) {
      setError(err.message)
    } finally {
      setMemoryBusy(false)
    }
  }

  async function handleApplyConsolidationJob(jobId) {
    if (!workspaceId || !jobId) return
    setMemoryBusy(true)
    try {
      await applyMemoryConsolidationJob(workspaceId, jobId)
      await refreshWorkspaceMemory(workspaceId)
      setCopied('Consolidation job applied')
      window.setTimeout(() => setCopied(''), 1600)
    } catch (err) {
      setError(err.message)
    } finally {
      setMemoryBusy(false)
    }
  }

  async function handleRebuildMemoryIndex() {
    if (!workspaceId) return
    setMemoryBusy(true)
    try {
      await rebuildWorkspaceMemoryIndex(workspaceId)
      await refreshWorkspaceMemory(workspaceId)
      setCopied('Memory index rebuilt')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setError(err.message)
    } finally {
      setMemoryBusy(false)
    }
  }

  async function handleArchiveMemory(memory) {
    if (!workspaceId) return
    try {
      await archiveWorkspaceMemory(workspaceId, memory.memory_id, memory.memory_tier !== 'archived')
      await refreshWorkspaceMemory(workspaceId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleCreateGoalFromPrompt(prompt) {
    try {
      const result = await createGoal({ prompt, workspace_id: workspaceId })
      setSelectedGoal(result)
      setShowMissionControl(true)
      await refreshMissionControl()
      await refreshAnalytics()
      setCopied('Goal created')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleSelectGoal(goalId) {
    try {
      const result = await getGoal(goalId)
      setSelectedGoal(result)
      setShowMissionControl(true)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRunGoalTask(goalId, taskId) {
    try {
      const result = await runGoalTask(goalId, taskId)
      const assistantMessage = {
        id: result.message_id,
        message_id: result.message_id,
        role: 'assistant',
        content: formatSimpleAnswer(result),
        result,
      }
      setMessages((current) => [...current, assistantMessage])
      setSessionId(result.session_id)
      setSelectedRunId(result.message_id)
      await refreshMissionControl()
      await refreshAnalytics()
      await refreshLearningReport()
      await refreshToolHistory(result.workspace_id || workspaceId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleMarkGoalTaskDone(goalId, taskId) {
    try {
      const completionNote = window.prompt(
        'Optional completion note (what was done, how it was verified):',
        '',
      )
      const payload = { status: 'done' }
      if (completionNote && completionNote.trim()) {
        payload.completion_note = completionNote.trim()
        payload.last_result_summary = completionNote.trim()
      }
      const result = await updateGoalTask(goalId, taskId, payload)
      await handleSelectGoal(goalId)
      await refreshMissionControl()
      await refreshLinearData(workspaceId)
      if (result?.linear_sync?.completed) {
        setCopied(`Linear ${result.linear_sync.identifier || 'issue'} marked Done`)
        window.setTimeout(() => setCopied(''), 2000)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleCreateAgentFromTemplate(templateName) {
    try {
      await createCustomAgent({ template_name: templateName, workspace_id: workspaceId })
      await refreshCustomAgents()
      await refreshAnalytics()
      setCopied('Custom agent created')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setError(err.message)
    }
  }

  async function decidePromptVersion(version, action) {
    try {
      const payload = { agent_name: version.agent_name, version_id: version.version_id }
      if (action === 'approve') await approvePromptVersion(payload)
      if (action === 'reject') await rejectPromptVersion(payload)
      if (action === 'rollback') await rollbackPromptVersion(payload)
      await refreshLearningReport()
      setCopied(`Prompt ${action} saved`)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRefreshDigitalTwin() {
    setDigitalTwinBusy(true)
    setDigitalTwinError('')
    try {
      setDigitalTwinProfile(await refreshDigitalTwinProfile(workspaceId))
      setCopied('Digital Twin profile refreshed')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setDigitalTwinError(err.message)
    } finally {
      setDigitalTwinBusy(false)
    }
  }

  async function handleUpdateDigitalTwin() {
    const detailLevel = window.prompt('Detail level', digitalTwinProfile?.style_profile?.detail_level || 'balanced')
    if (!detailLevel) return
    const format = window.prompt('Preferred format', digitalTwinProfile?.style_profile?.format || 'mixed')
    if (!format) return
    const tone = window.prompt('Preferred tone', digitalTwinProfile?.style_profile?.tone || 'direct and practical')
    if (!tone) return
    setDigitalTwinBusy(true)
    setDigitalTwinError('')
    try {
      setDigitalTwinProfile(await updateDigitalTwinProfile({
        workspace_id: workspaceId,
        detail_level: detailLevel,
        format,
        tone,
      }))
      setCopied('Digital Twin profile updated')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setDigitalTwinError(err.message)
    } finally {
      setDigitalTwinBusy(false)
    }
  }

  async function refreshChats(nextWorkspaceId = workspaceId) {
    setChats(await getChats(nextWorkspaceId))
  }

  async function newChat() {
    try {
      const chat = await createChat('New Chat', workspaceId)
      setSessionId(chat.session_id)
      await refreshChats()
    } catch {
      setSessionId(null)
    }
    setMessages([])
    setSelectedRunId(null)
    setError('')
    setInput('')
  }

  async function loadChat(nextSessionId) {
    try {
      const chat = await getChat(nextSessionId)
      setSessionId(chat.session_id)
      setMessages(chat.messages || [])
      const lastAssistant = [...(chat.messages || [])].reverse().find((message) => message.role === 'assistant' && message.result)
      setSelectedRunId(messageKey(lastAssistant || {}) || null)
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRenameChat(nextSessionId, currentTitle) {
    const title = window.prompt('Rename chat', currentTitle)
    if (!title?.trim()) return
    await renameChat(nextSessionId, title.trim())
    await refreshChats()
  }

  async function handleDeleteChat(nextSessionId) {
    await deleteChat(nextSessionId)
    if (sessionId === nextSessionId) {
      newChat()
    }
    await refreshChats()
  }

  async function submitMessage(text = input) {
    const prompt = text.trim()
    if (!prompt || loading) return
    const processedFiles = attachedFiles.filter((file) => file.status === 'processed')
    const processedRecordings = attachedRecordings.filter((recording) => recording.status === 'processed')

    const userMessage = {
      id: crypto.randomUUID(),
      message_id: crypto.randomUUID(),
      role: 'user',
      content: prompt,
      attached_files: processedFiles,
      attached_recordings: processedRecordings,
      voice_used: voiceUsed,
      voice_transcript: voiceTranscript,
    }
    setMessages((current) => [...current, userMessage])
    setInput('')
    setLoading(true)
    setError('')
    setProgressIndex(0)

    try {
      const data = await runWorkflow({
        user_input: prompt,
        task_type: taskType,
        deep_mode: deepMode,
        session_id: sessionId,
        workspace_id: workspaceId,
        file_ids: processedFiles.map((file) => file.file_id),
        recording_ids: processedRecordings.map((recording) => recording.recording_id),
        voice_used: voiceUsed,
        voice_transcript: voiceTranscript || null,
      })
      const assistantMessage = {
        id: data.message_id,
        message_id: data.message_id,
        role: 'assistant',
        content: formatSimpleAnswer(data),
        result: data,
      }
      setMessages((current) => [...current, assistantMessage])
      setSessionId(data.session_id)
      setSelectedRunId(assistantMessage.id)
      await refreshHistory()
      await refreshChats()
      await refreshProviderStatus()
      await refreshAnalytics()
      await refreshLearningReport()
      await refreshMissionControl()
      await refreshWorkspaceMemory(workspaceId)
      await refreshToolHistory(data.workspace_id || workspaceId)
      setAttachedFiles([])
      setAttachedRecordings([])
      setVoiceUsed(false)
      setVoiceTranscript('')
    } catch (err) {
      setError(err.message)
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `I could not run the workflow: ${err.message}`,
          error: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  async function submitFeedback(result, rating) {
    if (!result) return
    try {
      await sendFeedback({
        session_id: result.session_id,
        message_id: result.message_id,
        run_id: result.run_id,
        workspace_id: result.workspace_id || workspaceId,
        rating,
      })
      setCopied(rating === 'saved' ? 'Saved as good answer' : 'Feedback saved')
      window.setTimeout(() => setCopied(''), 1300)
      await refreshAnalytics()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleFileSelect(event) {
    const files = Array.from(event.target.files || [])
    event.target.value = ''
    if (files.length === 0) return
    if (files.length + attachedFiles.length > 5) {
      setError('You can attach up to 5 files per message.')
      return
    }
    setUploadingFiles(true)
    setError('')
    try {
      const result = await uploadFiles(files, sessionId, workspaceId)
      setAttachedFiles((current) => [...current, ...(result.files || [])])
    } catch (err) {
      setError(err.message)
    } finally {
      setUploadingFiles(false)
    }
  }

  async function handleRecordingSelect(event) {
    const files = Array.from(event.target.files || [])
    event.target.value = ''
    if (files.length === 0) return
    if (files.length + attachedRecordings.length > 5) {
      setError('You can attach up to 5 recordings per message.')
      return
    }
    setUploadingRecordings(true)
    setError('')
    try {
      const result = await uploadRecordings(files, sessionId, workspaceId)
      setAttachedRecordings((current) => [...current, ...(result.recordings || [])])
    } catch (err) {
      setError(err.message)
    } finally {
      setUploadingRecordings(false)
    }
  }

  function removeAttachedFile(fileId) {
    setAttachedFiles((current) => current.filter((file) => file.file_id !== fileId))
  }

  function removeAttachedRecording(recordingId) {
    setAttachedRecordings((current) => current.filter((recording) => recording.recording_id !== recordingId))
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submitMessage()
    }
  }

  function startVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Voice input is not supported in this browser yet.')
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onstart = () => {
      setListening(true)
      setError('')
    }
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || ''
      setInput(transcript)
      setVoiceTranscript(transcript)
      setVoiceUsed(Boolean(transcript))
    }
    recognition.onerror = () => {
      setError('Voice input could not be transcribed. Try again or type your message.')
    }
    recognition.onend = () => setListening(false)
    recognition.start()
  }

  function focusComposer() {
    composerRef.current?.focus()
  }

  function handleJarvisSpeak() {
    focusComposer()
    startVoiceInput()
  }

  async function copyText(text) {
    await navigator.clipboard.writeText(text)
    setCopied('Copied')
    window.setTimeout(() => setCopied(''), 1300)
  }

  async function regenerateLastResponse() {
    const lastUser = [...messages].reverse().find((message) => message.role === 'user')
    if (lastUser) {
      await submitMessage(lastUser.content)
    }
  }

  async function handleAutomationApply(result, approved) {
    if (!result?.run_id) return
    try {
      const applyResult = await applyAutomation({ run_id: result.run_id, approved })
      setAutomationResults((current) => ({ ...current, [result.run_id]: applyResult }))
      setCopied(approved ? 'Automation approval processed' : 'Automation rejected')
      window.setTimeout(() => setCopied(''), 1300)
      await refreshLearningReport()
    } catch (err) {
      setError(err.message)
    }
  }

  function editMessage(message) {
    setInput(message.content)
  }

  async function handleDeleteMessage(message) {
    const id = messageKey(message)
    if (!id) return
    setMessages((current) => current.filter((item) => messageKey(item) !== id))
    if (message.result && selectedRunId === id) {
      setSelectedRunId(null)
    }
    if (sessionId) {
      try {
        await deleteMessage(sessionId, id)
        await refreshChats()
      } catch (err) {
        setError(err.message)
      }
    }
  }

  function currentChatTitle() {
    return chats.find((item) => item.session_id === sessionId)?.title || 'EvolveAgent AI Chat'
  }

  function exportMarkdown() {
    const lines = [`# ${currentChatTitle()}`, '', `Exported: ${new Date().toLocaleString()}`, '']
    messages.forEach((message) => {
      lines.push(`## ${message.role === 'user' ? 'User' : 'EvolveAgent AI'}`)
      lines.push('')
      lines.push(message.result ? formatSimpleAnswer(message.result, message.content) : message.content)
      const files = message.attached_files || []
      const recordings = message.attached_recordings || []
      if (files.length) {
        lines.push('')
        lines.push(`Attached files: ${files.map((file) => file.filename).join(', ')}`)
      }
      if (recordings.length) {
        lines.push('')
        lines.push(`Attached recordings: ${recordings.map((recording) => recording.filename).join(', ')}`)
      }
      lines.push('')
    })
    downloadFile(`${currentChatTitle().replace(/[^a-z0-9]+/gi, '-').toLowerCase()}-chat.md`, lines.join('\n'), 'text/markdown')
  }

  function exportJson() {
    const payload = {
      session: chats.find((item) => item.session_id === sessionId) || { session_id: sessionId, title: currentChatTitle() },
      messages,
    }
    downloadFile(`${currentChatTitle().replace(/[^a-z0-9]+/gi, '-').toLowerCase()}-chat.json`, JSON.stringify(payload, null, 2), 'application/json')
  }

  function copyConversation() {
    const text = messages
      .map((message) => `${message.role === 'user' ? 'User' : 'EvolveAgent AI'}:\n${message.result ? formatSimpleAnswer(message.result, message.content) : message.content}`)
      .join('\n\n')
    copyText(text)
  }

  function downloadFile(filename, content, type) {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }

  const modeLabel = capabilityModeLabel('Text', providerStatus, 'llm_mode', 'default_provider')
  const imageModeLabel = capabilityModeLabel('Image', imageProviderStatus, 'image_mode', 'active_provider')
  const transcriptionModeLabel = capabilityModeLabel('Audio', transcriptionProviderStatus, 'transcription_mode', 'active_provider')
  const providerList = providerStatus?.available_providers?.join(', ') || 'none'
  const realProvidersAvailable = (providerStatus?.available_providers || []).filter((provider) => provider !== 'mock')
  const realModeWithoutRealProvider = providerStatus?.llm_mode === 'real' && realProvidersAvailable.length === 0
  function toggleTheme() {
    setTheme((current) => (current === 'dark' ? 'light' : 'dark'))
  }

  function dismissOnboarding() {
    localStorage.setItem('evolveagent-onboarding-dismissed', '1')
    setShowOnboarding(false)
  }

  function nextOnboardingStep() {
    if (onboardingStep >= ONBOARDING_STEPS.length - 1) {
      dismissOnboarding()
      return
    }
    setOnboardingStep((current) => current + 1)
  }

  const previewText = (text, limit = 360) => {
    const compact = String(text || '').replace(/\s+/g, ' ').trim()
    if (compact.length <= limit) return compact
    return `${compact.slice(0, limit).trim()}...`
  }

  return (
    <main className={`app-shell chat-shell ${developerMode ? 'developer-mode' : 'simple-mode'} ${sidebarOpen ? 'sidebar-open' : ''}`}>
      {developerMode && sidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar"
        />
      )}
      {showOnboarding && (
        <div className="onboarding-overlay" role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
          <div className="onboarding-card">
            <div className="onboarding-steps" aria-hidden="true">
              {ONBOARDING_STEPS.map((step, index) => (
                <span className={`onboarding-step-dot ${index === onboardingStep ? 'active' : ''}`} key={step.title} />
              ))}
            </div>
            <h3 id="onboarding-title">{ONBOARDING_STEPS[onboardingStep].title}</h3>
            <p>{ONBOARDING_STEPS[onboardingStep].body}</p>
            <div className="onboarding-actions">
              <button type="button" onClick={dismissOnboarding}>Skip</button>
              <button type="button" onClick={nextOnboardingStep}>
                {onboardingStep >= ONBOARDING_STEPS.length - 1 ? 'Get started' : 'Next'}
              </button>
            </div>
          </div>
        </div>
      )}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <div className="brand-mark">
            <Brain size={21} />
          </div>
          <div>
            <h1>EvolveAgent AI</h1>
            <p>Agent Chat</p>
          </div>
        </div>

        <button className="new-chat-button" onClick={newChat}>
          <MessageSquarePlus size={16} />
          New Chat
        </button>

        <div className="sidebar-dev-only">
        <section className="sidebar-section">
          <div className="side-heading">
            <Library size={15} />
            <span>Workspace</span>
          </div>
          <div className="workspace-card">
            <select
              value={workspaceId || ''}
              onChange={(event) => setWorkspaceId(event.target.value)}
              aria-label="Select workspace"
            >
              {workspaces.map((workspace) => (
                <option key={workspace.workspace_id} value={workspace.workspace_id}>
                  {workspace.name}
                </option>
              ))}
            </select>
            <div className="workspace-actions">
              <button type="button" onClick={handleCreateWorkspace}>New</button>
              <button type="button" onClick={handleRenameWorkspace} disabled={!workspaceId}>Rename</button>
              <button
                type="button"
                onClick={handleArchiveWorkspace}
                disabled={!workspaceId || workspaces.find((item) => item.workspace_id === workspaceId)?.default}
              >
                Archive
              </button>
            </div>
            <p>{workspaces.find((item) => item.workspace_id === workspaceId)?.description || 'Project-specific chats, memory, goals, and agents.'}</p>
          </div>
        </section>

        <section className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowMemoryPanel((current) => !current)}>
            <span>
              <Database size={15} />
              Memory
            </span>
            <ChevronDown size={15} />
          </button>
          {showMemoryPanel && (
            <div className="memory-panel">
              <div className="memory-controls">
                <input
                  value={memorySearch}
                  onChange={(event) => setMemorySearch(event.target.value)}
                  placeholder="Search memory"
                />
                <select value={memoryType} onChange={(event) => setMemoryType(event.target.value)}>
                  <option value="">All types</option>
                  <option value="preference">Preference</option>
                  <option value="project_fact">Project fact</option>
                  <option value="decision">Decision</option>
                  <option value="summary">Summary</option>
                  <option value="task_result">Task result</option>
                  <option value="learned_pattern">Learned pattern</option>
                </select>
                <select value={memoryTier} onChange={(event) => setMemoryTier(event.target.value)}>
                  <option value="">All tiers</option>
                  <option value="hot">Hot</option>
                  <option value="warm">Warm</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
              {memoryIntelligence && (
                <div className="memory-intelligence">
                  <strong>Memory Intelligence</strong>
                  <span>
                    {memoryIntelligence.total_memories || 0} memories · avg score {memoryIntelligence.average_quality_score || 0}
                  </span>
                  <div className="memory-tier-row">
                    {(memoryIntelligence.tiers || []).map((tier) => (
                      <span className="status-pill" key={tier.tier}>{formatType(tier.tier)} {tier.count}</span>
                    ))}
                  </div>
                  {memoryIntelligence.vector_index && (
                    <span>
                      Index: {memoryIntelligence.vector_index.indexed_memories || 0} memories · {memoryIntelligence.vector_index.model}
                    </span>
                  )}
                  {(memoryIntelligence.vector_index?.top_terms || []).length > 0 && (
                    <p>Top terms: {memoryIntelligence.vector_index.top_terms.slice(0, 5).map((term) => term.term).join(', ')}</p>
                  )}
                  {(memoryIntelligence.suggested_consolidations || []).length > 0 && (
                    <p>{memoryIntelligence.suggested_consolidations.length} duplicate group(s) can be consolidated.</p>
                  )}
                  {(memoryIntelligence.recommended_actions || []).length > 0 && (
                    <p>{memoryIntelligence.recommended_actions.length} memory item(s) need review or archive attention.</p>
                  )}
                </div>
              )}
              <div className="inline-actions">
                <button className="secondary-button" type="button" onClick={handleRescoreMemory} disabled={memoryBusy}>
                  Re-score
                </button>
                <button className="secondary-button" type="button" onClick={handleMaintainMemoryTiers} disabled={memoryBusy}>
                  Maintain tiers
                </button>
                <button className="secondary-button" type="button" onClick={handleRebuildMemoryIndex} disabled={memoryBusy}>
                  Rebuild index
                </button>
                <button className="secondary-button" type="button" onClick={() => handleCreateConsolidationJob(false)} disabled={memoryBusy}>
                  Create job
                </button>
                <button className="secondary-button" type="button" onClick={() => handleCreateConsolidationJob(true)} disabled={memoryBusy}>
                  Run job
                </button>
              </div>
              {memoryConsolidationJobs.length > 0 && (
                <div className="memory-jobs">
                  <strong>Consolidation jobs</strong>
                  {memoryConsolidationJobs.slice(0, 3).map((job) => (
                    <div className="memory-job-row" key={job.job_id}>
                      <span>{formatType(job.status)} · {job.duplicate_group_count || 0} groups · {job.archived_memory_ids?.length || 0} archived</span>
                      <span>{job.created_at ? new Date(job.created_at).toLocaleString() : ''}</span>
                      {job.status === 'preview_ready' && (
                        <button type="button" onClick={() => handleApplyConsolidationJob(job.job_id)} disabled={memoryBusy}>
                          Apply
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <button className="secondary-button full-width" type="button" onClick={handleAddMemory}>
                Add memory
              </button>
              {workspaceMemory.length === 0 && <p className="muted">No workspace memory yet.</p>}
              {workspaceMemory.slice(0, 8).map((memory) => (
                <div className="memory-card" key={memory.memory_id}>
                  <strong>{memory.title}</strong>
                  <span>
                    {formatType(memory.type)} · {memory.importance}
                    {memory.memory_tier ? ` · ${formatType(memory.memory_tier)}` : ''}
                    {memory.quality_score !== undefined ? ` · score ${memory.quality_score}` : ''}
                    {memory.pinned ? ' · pinned' : ''}
                    {memory.usage_count ? ` · used ${memory.usage_count}` : ''}
                  </span>
                  <p>{previewText(memory.content, 150)}</p>
                  {(memory.quality_reasons || []).length > 0 && (
                    <p className="muted">Why: {(memory.quality_reasons || []).join(', ')}</p>
                  )}
                  {memory.tier_reason && (
                    <p className="muted">Tier: {memory.tier_reason} · {memory.retention_action || 'keep'}</p>
                  )}
                  {memory.quality_recommendation && (
                    <p className="muted">Recommendation: {memory.quality_recommendation}</p>
                  )}
                  {(memory.tier_history || []).length > 0 && (
                    <p className="muted">Last move: {formatType(memory.tier_history[memory.tier_history.length - 1].from)} → {formatType(memory.tier_history[memory.tier_history.length - 1].to)}</p>
                  )}
                  <div className="chat-row-actions">
                    <button type="button" onClick={() => handleToggleMemoryPin(memory)}>
                      {memory.pinned ? 'Unpin' : 'Pin'}
                    </button>
                    <button type="button" onClick={() => handleArchiveMemory(memory)}>
                      {memory.memory_tier === 'archived' ? 'Restore' : 'Archive'}
                    </button>
                    <button type="button" onClick={() => handleEditMemory(memory)}>Edit</button>
                    <button type="button" onClick={() => handleDeleteMemory(memory.memory_id)}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowKnowledgePanel((current) => !current)}>
            <span>
              <Brain size={15} />
              Knowledge Base
            </span>
            <ChevronDown size={15} />
          </button>
          {showKnowledgePanel && (
            <div className="memory-panel knowledge-panel">
              <div className="knowledge-summary">
                <div>
                  <span>Records</span>
                  <strong>{knowledgeSummary?.total_records || 0}</strong>
                </div>
                <div>
                  <span>High value</span>
                  <strong>{knowledgeSummary?.high_importance_count || 0}</strong>
                </div>
              </div>
              <div className="memory-controls">
                <input
                  value={knowledgeSearch}
                  onChange={(event) => setKnowledgeSearch(event.target.value)}
                  placeholder="Search project brain"
                />
                <select value={knowledgeSource} onChange={(event) => setKnowledgeSource(event.target.value)}>
                  <option value="">All sources</option>
                  <option value="memory">Memory</option>
                  <option value="chat">Chats</option>
                  <option value="file">Files</option>
                  <option value="recording">Recordings</option>
                  <option value="goal">Goals</option>
                  <option value="custom_agent">Custom agents</option>
                </select>
              </div>
              <div className="workspace-actions">
                <button type="button" onClick={() => handleExportKnowledge('markdown')}>Export MD</button>
                <button type="button" onClick={() => handleExportKnowledge('json')}>Export JSON</button>
                <button type="button" onClick={() => refreshKnowledge(workspaceId)}>Refresh</button>
              </div>
              {knowledgeResults.length === 0 && <p className="muted">No knowledge records match this search.</p>}
              {knowledgeResults.slice(0, 8).map((item) => (
                <div className="memory-card knowledge-card" key={`${item.source_type}-${item.record_id}`}>
                  <strong>{item.title}</strong>
                  <span>{formatType(item.source_type)} · score {item.score}</span>
                  <p>{previewText(item.content_preview, 150)}</p>
                  {item.tags?.length > 0 && <small>{item.tags.slice(0, 4).join(', ')}</small>}
                  {item.linked_items?.length > 0 && (
                    <small>
                      Linked: {item.linked_items.slice(0, 3).map((linked) => linked.title).join(', ')}
                    </small>
                  )}
                </div>
              ))}
              {knowledgeLinks.length > 0 && (
                <details className="developer-prompt-block">
                  <summary>Related knowledge</summary>
                  {knowledgeLinks.slice(0, 5).map((link) => (
                    <p className="muted" key={`${link.source_type}-${link.record_id}`}>
                      {formatType(link.source_type)} · {link.title}
                    </p>
                  ))}
                </details>
              )}
            </div>
          )}
        </section>

        <section className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowToolsPanel((current) => !current)}>
            <span>
              <Terminal size={15} />
              Assistant Tools
            </span>
            <ChevronDown size={15} />
          </button>
          {showToolsPanel && (
            <div className="memory-panel tools-panel">
              <select value={selectedCommand} onChange={(event) => setSelectedCommand(event.target.value)}>
                {assistantCommands.map((command) => (
                  <option key={command.name} value={command.name}>
                    {command.name}
                  </option>
                ))}
              </select>
              <textarea
                value={commandInput}
                onChange={(event) => setCommandInput(event.target.value)}
                placeholder="Input, e.g. 24 * (7 + 3)"
                rows={3}
              />
              <button className="secondary-button full-width" type="button" onClick={handleRunAssistantCommand}>
                Run tool
              </button>
              {assistantCommands.find((command) => command.name === selectedCommand)?.description && (
                <p className="muted">{assistantCommands.find((command) => command.name === selectedCommand).description}</p>
              )}
              {commandResult && (
                <div className={`command-result ${commandResult.success ? 'success' : 'failed'}`}>
                  <strong>{commandResult.command}</strong>
                  <pre>{commandResult.output}</pre>
                </div>
              )}
              {developerMode && (
                <details className="developer-prompt-block">
                  <summary>Tool execution history</summary>
                  <div className="tool-history-header">
                    <p className="muted">
                      Recent governed tool selections and execution quality.
                      {toolHistoryUpdatedAt ? ` Refreshed ${toolHistoryUpdatedAt}.` : ''}
                    </p>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => refreshToolHistory(workspaceId)}
                      disabled={toolHistoryBusy}
                    >
                      <RefreshCw size={14} />
                      Refresh
                    </button>
                  </div>
                  {toolSummary ? (
                    <div className="mini-grid">
                      <div>
                        <span>Total</span>
                        <strong>{toolSummary.total_executions || 0}</strong>
                      </div>
                      <div>
                        <span>Executed</span>
                        <strong>{toolSummary.executed || 0}</strong>
                      </div>
                      <div>
                        <span>Blocked</span>
                        <strong>{toolSummary.blocked || 0}</strong>
                      </div>
                      <div>
                        <span>Quality</span>
                        <strong>{toolSummary.average_quality_score || 0}</strong>
                      </div>
                    </div>
                  ) : (
                    <p className="muted">Tool history is not available yet.</p>
                  )}
                  {toolHistory.length === 0 ? (
                    <p className="muted">No tool executions have been recorded.</p>
                  ) : (
                    <div className="agent-list compact-list">
                      {toolHistory.slice(0, 8).map((item) => (
                        <div className="provider-row" key={item.execution_id}>
                          <div className="tool-history-title">
                            <strong>{item.tool_name}</strong>
                            <small>{item.created_at ? new Date(item.created_at).toLocaleString() : ''}</small>
                          </div>
                          <div className="model-meta">
                            <span>{item.source || 'n/a'}</span>
                            <span>{item.permission_level}</span>
                            {item.executed && <span>executed</span>}
                            {item.blocked && <span>blocked</span>}
                            {item.approval_required && <span>approval</span>}
                            <span>quality {item.quality_score}</span>
                          </div>
                          {item.result_summary && <p>{previewText(item.result_summary, 120)}</p>}
                          {item.quality_notes && <small>{item.quality_notes}</small>}
                        </div>
                      ))}
                    </div>
                  )}
                </details>
              )}
            </div>
          )}
        </section>

        <section className="sidebar-section">
          <div className="side-heading">
            <Cpu size={15} />
            <span>Providers</span>
          </div>
          <div className="provider-card">
            <div>
              <span>Text</span>
              <strong>{modeLabel}</strong>
            </div>
            <div>
              <span>Text providers</span>
              <strong>{providerList}</strong>
            </div>
            <div>
              <span>Image</span>
              <strong>{imageModeLabel}</strong>
            </div>
            <div>
              <span>Audio</span>
              <strong>{transcriptionModeLabel}</strong>
            </div>
          </div>
          {providerStatus && (
            <div className="provider-flags">
              <span className={providerStatus.openai_configured ? 'configured' : ''}>OpenAI {providerStatus.openai_configured ? 'ready' : 'not set'}</span>
              <span className={providerStatus.anthropic_configured ? 'configured' : ''}>Claude {providerStatus.anthropic_configured ? 'ready' : 'not set'}</span>
              <span className={providerStatus.gemini_configured ? 'configured' : ''}>Gemini {providerStatus.gemini_configured ? 'ready' : 'not set'}</span>
              <span className={providerStatus.mistral_configured ? 'configured' : ''}>Mistral {providerStatus.mistral_configured ? 'ready' : 'not set'}</span>
            </div>
          )}
          {providerStatus?.status_message && (
            <p className={`provider-warning ${providerStatus.real_mode_ready ? 'provider-ok' : ''}`}>
              {providerStatus.status_message}
            </p>
          )}
          {providerStatus?.provider_details?.length > 0 && (
            <details className="developer-prompt-block">
              <summary>Provider readiness</summary>
              <div className="agent-list compact-list">
                {providerStatus.provider_details.map((provider) => (
                  <div className="provider-row" key={provider.provider}>
                    <strong>{provider.label}</strong>
                    <div className="model-meta">
                      <span>{provider.model}</span>
                      <span>{provider.configured ? 'configured' : 'missing key'}</span>
                      {provider.ready && <span>ready</span>}
                      {provider.fallback_provider && <span>fallback {provider.fallback_provider}</span>}
                    </div>
                    <p>{provider.reason}</p>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => handleProviderCheck(provider.provider)}
                      disabled={providerCheckBusy}
                    >
                      Check {provider.label}
                    </button>
                  </div>
                ))}
              </div>
              {providerCheck && (
                <div className={`command-result ${providerCheck.success ? 'success' : 'failed'}`}>
                  <strong>{providerCheck.provider} check</strong>
                  <pre>{providerCheck.message}</pre>
                </div>
              )}
            </details>
          )}
          {realModeWithoutRealProvider && (
            <p className="provider-warning">Real mode is enabled, but no real provider key is configured. Mock fallback will be used.</p>
          )}
          {imageProviderStatus && (
            <details className="developer-prompt-block">
              <summary>Image provider</summary>
              <div className="provider-row">
                <strong>{imageProviderStatus.active_provider}</strong>
                <div className="model-meta">
                  <span>{imageProviderStatus.image_mode} mode</span>
                  <span>{imageProviderStatus.active_model}</span>
                  <span>{imageProviderStatus.image_size}</span>
                  {imageProviderStatus.real_image_ready && <span>real ready</span>}
                  <span>fallback {imageProviderStatus.fallback_provider}</span>
                </div>
                <p>{imageProviderStatus.status_message}</p>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={handleImageProviderCheck}
                  disabled={imageProviderBusy}
                >
                  Check image provider
                </button>
              </div>
              {imageProviderCheck && (
                <div className={`command-result ${imageProviderCheck.success ? 'success' : 'failed'}`}>
                  <strong>image check</strong>
                  <pre>{imageProviderCheck.message}</pre>
                </div>
              )}
            </details>
          )}
          {transcriptionProviderStatus && (
            <details className="developer-prompt-block">
              <summary>Transcription provider</summary>
              <div className="provider-row">
                <strong>{transcriptionProviderStatus.active_provider}</strong>
                <div className="model-meta">
                  <span>{transcriptionProviderStatus.transcription_mode} mode</span>
                  <span>{transcriptionProviderStatus.active_model}</span>
                  {transcriptionProviderStatus.real_transcription_ready && <span>real ready</span>}
                  <span>fallback {transcriptionProviderStatus.fallback_provider}</span>
                </div>
                <p>{transcriptionProviderStatus.status_message}</p>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={handleTranscriptionProviderCheck}
                  disabled={transcriptionProviderBusy}
                >
                  Check transcription provider
                </button>
              </div>
              {transcriptionProviderCheck && (
                <div className={`command-result ${transcriptionProviderCheck.success ? 'success' : 'failed'}`}>
                  <strong>transcription check</strong>
                  <pre>{transcriptionProviderCheck.message}</pre>
                </div>
              )}
            </details>
          )}
          {realApiSummary && (
            <details className="developer-prompt-block">
              <summary>Real API control</summary>
              <div className="provider-row">
                <strong>{realApiSummary.paid_api_ready ? 'Paid APIs ready' : 'Mock-safe mode'}</strong>
                <div className="model-meta">
                  <span>dry checks default</span>
                  <span>live checks require confirmation</span>
                  <span>{realApiSummary.paid_capabilities?.length || 0} ready</span>
                </div>
                <p>
                  Dry checks do not call paid APIs. Live text checks, image generation, and recording
                  transcription can use paid provider APIs when their real modes are enabled.
                </p>
              </div>
              <div className="agent-list compact-list">
                {Object.entries(realApiSummary.capabilities || {}).map(([capability, item]) => (
                  <div className="provider-row" key={capability}>
                    <strong>{formatType(capability)}</strong>
                    <div className="model-meta">
                      <span>{item.mode}</span>
                      <span>{item.provider}</span>
                      <span>{item.model}</span>
                      {item.ready && <span>ready</span>}
                    </div>
                    <p>{item.estimate_note}</p>
                    <button
                      className="secondary-button"
                      type="button"
                      disabled={realApiWarningBusy}
                      onClick={() => handleRealApiWarning(capability)}
                    >
                      Show live warning
                    </button>
                  </div>
                ))}
              </div>
              {realApiWarning && (
                <div className="fallback-note">
                  <strong>{formatType(realApiWarning.capability)} live API warning</strong>
                  <p>{realApiWarning.warning}</p>
                  <small>{realApiWarning.estimate_note}</small>
                </div>
              )}
            </details>
          )}
        </section>

        <section className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowAnalytics((current) => !current)}>
            <span>
              <BarChart3 size={15} />
              Analytics
            </span>
            <ChevronDown size={15} />
          </button>
          {showAnalytics && analytics && (
            <div className="analytics-panel">
              <div>
                <span>Total runs</span>
                <strong>{analytics.total_runs}</strong>
              </div>
              <div>
                <span>Average score</span>
                <strong>{analytics.average_judge_score}</strong>
              </div>
              <div>
                <span>Common task</span>
                <strong>{formatType(analytics.most_common_task_type || 'none')}</strong>
              </div>
              <div>
                <span>Top agent</span>
                <strong>{analytics.most_used_agents?.[0]?.agent_name || 'none'}</strong>
              </div>
              <div>
                <span>Fallbacks</span>
                <strong>{analytics.fallback_count}</strong>
              </div>
              <div>
                <span>File tasks</span>
                <strong>{analytics.file_task_count}</strong>
              </div>
              <div>
                <span>Image tasks</span>
                <strong>{analytics.image_task_count}</strong>
              </div>
              <div>
                <span>Recording tasks</span>
                <strong>{analytics.recording_task_count || 0}</strong>
              </div>
              <div>
                <span>Goals</span>
                <strong>{analytics.active_goals || 0}/{analytics.total_goals || 0}</strong>
              </div>
              <div>
                <span>Goal tasks done</span>
                <strong>{analytics.completed_goal_tasks || 0}/{analytics.total_goal_tasks || 0}</strong>
              </div>
              <div>
                <span>Custom agents</span>
                <strong>{analytics.custom_agents_count || 0}</strong>
              </div>
              <div>
                <span>Linear synced</span>
                <strong>{analytics.linear_issues_synced || 0}</strong>
              </div>
              <div>
                <span>Linear commits</span>
                <strong>{analytics.linear_linked_commits || 0}</strong>
              </div>
              <div>
                <span>Feedback</span>
                <strong>
                  {analytics.feedback_summary?.helpful || 0}/{analytics.feedback_summary?.not_helpful || 0}/{analytics.feedback_summary?.saved || 0}
                </strong>
              </div>
              <div className="recent-runs">
                <span>Recent runs</span>
                {(analytics.recent_runs || []).slice(0, 4).map((run) => (
                  <p key={run.run_id}>
                    {formatType(run.task_type)} · score {run.overall_judge_score}
                  </p>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowMissionControl((current) => !current)}>
            <span>
              <Flag size={15} />
              Mission Control
            </span>
            <ChevronDown size={15} />
          </button>
          {showMissionControl && (
            <div className="mission-panel">
              <button
                className="secondary-button full-width"
                type="button"
                onClick={() => handleCreateGoalFromPrompt(input.trim() || 'Build an AI resume analyzer app')}
              >
                Create goal from prompt
              </button>
              {goals.length === 0 && <p className="muted">No goals yet.</p>}
              {goals.slice(0, 6).map((goal) => {
                const link = linearLinkForGoal(goal.goal_id)
                return (
                  <button className="goal-card" type="button" key={goal.goal_id} onClick={() => handleSelectGoal(goal.goal_id)}>
                    <strong>{goal.title}</strong>
                    <span>{goal.status} · {goal.progress_percent || 0}% · {goal.risk_level} risk</span>
                    {link && (
                      <span className="linear-badge">
                        {link.linear_identifier}
                        {link.branch_name ? ` · ${link.branch_name}` : ''}
                        {link.commits?.length ? ` · ${link.commits[link.commits.length - 1].hash?.slice(0, 7)}` : ''}
                        {link.pushes?.length ? ' · pushed' : ''}
                      </span>
                    )}
                  </button>
                )
              })}
              {selectedGoal?.goal && (
                <div className="goal-detail">
                  <h3>{selectedGoal.goal.title}</h3>
                  <p>{selectedGoal.goal.description}</p>
                  {(() => {
                    const link = linearLinkForGoal(selectedGoal.goal.goal_id)
                    if (!link) return null
                    return (
                      <div className="linear-goal-meta">
                        <span>Linear: {link.linear_identifier} · {link.status}</span>
                        {link.linear_url && (
                          <a href={link.linear_url} target="_blank" rel="noreferrer">
                            Open in Linear
                          </a>
                        )}
                        {link.branch_name && <span>Branch: {link.branch_name}</span>}
                        {link.commits?.length ? (
                          <span>Latest commit: {link.commits[link.commits.length - 1].hash}</span>
                        ) : null}
                        {link.pushes?.length ? <span>Push: completed</span> : <span>Push: not yet</span>}
                      </div>
                    )
                  })()}
                  <div className="progress-bar">
                    <span style={{ width: `${selectedGoal.goal.progress_percent || 0}%` }} />
                  </div>
                  {(selectedGoal.task_graph?.tasks || []).map((task) => (
                    <div className="task-card" key={task.task_id}>
                      <div>
                        <strong>{task.title}</strong>
                        <span>{task.phase} · {task.priority} · {task.status}</span>
                      </div>
                      <p>{task.description}</p>
                      {task.last_result_summary && (
                        <p className="task-notes">
                          <strong>Notes:</strong> {task.last_result_summary}
                        </p>
                      )}
                      <div className="inline-actions">
                        <button type="button" onClick={() => handleRunGoalTask(selectedGoal.goal.goal_id, task.task_id)}>
                          Run task
                        </button>
                        <button type="button" onClick={() => handleMarkGoalTaskDone(selectedGoal.goal.goal_id, task.task_id)}>
                          Mark done
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>

        <section className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowAppBuilder((current) => !current)}>
            <span>
              <Layers3 size={15} />
              App Builder
            </span>
            <ChevronDown size={15} />
          </button>
          {showAppBuilder && (
            <div className="mission-panel">
              <select value={appBuilderStack} onChange={(event) => setAppBuilderStack(event.target.value)}>
                {appBuilderTemplates.map((template) => (
                  <option key={template.stack_id} value={template.stack_id}>
                    {template.name}
                  </option>
                ))}
              </select>
              <textarea
                value={appBuilderPrompt}
                onChange={(event) => setAppBuilderPrompt(event.target.value)}
                placeholder="Describe the app you want to scaffold"
                rows={4}
              />
              <button className="secondary-button full-width" type="button" disabled={appBuilderBusy} onClick={handleCreateAppBuilderPlan}>
                {appBuilderBusy ? 'Working...' : 'Create build plan'}
              </button>
              {appBuilderError && <p className="provider-warning">{appBuilderError}</p>}
              {appBuilderPlan && (
                <div className="goal-detail">
                  <h3>{appBuilderPlan.app_name}</h3>
                  <p>{appBuilderPlan.stack?.name} · {appBuilderPlan.risk_level} risk · {appBuilderPlan.status}</p>
                  {(appBuilderPlan.features || []).length > 0 && (
                    <ul>{appBuilderPlan.features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
                  )}
                  {(appBuilderPlan.wizard_steps || []).map((step) => (
                    <div className="agent-template-card" key={`${appBuilderPlan.plan_id}-${step.step}`}>
                      <strong>{step.step}. {step.title}</strong>
                      <span>{step.value}</span>
                    </div>
                  ))}
                  <p className="muted">
                    Scaffold output writes to an ignored local preview folder only after approval.
                  </p>
                  <button
                    className="secondary-button full-width"
                    type="button"
                    disabled={appBuilderBusy || appBuilderPlan.status === 'blocked'}
                    onClick={handleScaffoldAppBuilderPlan}
                  >
                    Approve scaffold preview
                  </button>
                </div>
              )}
              {appBuilderResult && (
                <div className={`command-result ${appBuilderResult.success ? 'success' : 'failed'}`}>
                  <strong>{appBuilderResult.success ? 'Scaffold created' : 'Scaffold not created'}</strong>
                  <pre>{appBuilderResult.summary || JSON.stringify(appBuilderResult.errors || [], null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </section>

        <section className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowDebatePanel((current) => !current)}>
            <span>
              <Route size={15} />
              Debate + Simulation
            </span>
            <ChevronDown size={15} />
          </button>
          {showDebatePanel && (
            <div className="mission-panel">
              <textarea
                value={debatePrompt}
                onChange={(event) => setDebatePrompt(event.target.value)}
                placeholder="Decision or plan to debate"
                rows={3}
              />
              <textarea
                value={simulationScenario}
                onChange={(event) => setSimulationScenario(event.target.value)}
                placeholder="Simulation scenario"
                rows={2}
              />
              <div className="inline-actions">
                <button type="button" disabled={debateBusy} onClick={handleCreateDebateSession}>
                  Run debate
                </button>
                <button type="button" disabled={debateBusy} onClick={handleCreateSimulationRun}>
                  Simulate
                </button>
              </div>
              {debateError && <p className="provider-warning">{debateError}</p>}
              {debateSummary && (
                <div className="provider-card">
                  <div>
                    <span>Debates</span>
                    <strong>{debateSummary.total_debates || 0}</strong>
                  </div>
                  <div>
                    <span>Simulations</span>
                    <strong>{debateSummary.total_simulations || 0}</strong>
                  </div>
                </div>
              )}
              {debateResult && (
                <div className="goal-detail">
                  <h3>Debate result</h3>
                  <p>{debateResult.consensus?.final_recommendation}</p>
                  {(debateResult.turns || []).map((turn) => (
                    <div className="agent-template-card" key={`${debateResult.debate_id}-${turn.agent_name}`}>
                      <strong>{turn.agent_name}</strong>
                      <span>score {turn.score}</span>
                      <p className="muted">{turn.recommendation}</p>
                    </div>
                  ))}
                  <p className="muted">{debateResult.consensus?.why}</p>
                </div>
              )}
              {simulationResult && (
                <div className="goal-detail">
                  <h3>Simulation result</h3>
                  <p>{simulationResult.recommendation?.summary}</p>
                  {(simulationResult.outcomes || []).map((outcome) => (
                    <div className="agent-template-card" key={`${simulationResult.simulation_id}-${outcome.mode}`}>
                      <strong>{outcome.mode}</strong>
                      <span>{outcome.risk_level} risk</span>
                      <p className="muted">{outcome.expected_result}</p>
                    </div>
                  ))}
                  <p className="muted">Side effects: {(simulationResult.side_effects || []).length}</p>
                </div>
              )}
            </div>
          )}
        </section>

        {developerMode && (
          <section className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowResearchPanel((current) => !current)}>
              <span>
                <Library size={15} />
                Research Agent
              </span>
              <ChevronDown size={15} />
            </button>
            {showResearchPanel && (
              <div className="mission-panel">
                <textarea
                  value={researchQuery}
                  onChange={(event) => setResearchQuery(event.target.value)}
                  rows={3}
                  aria-label="Research query"
                />
                <button
                  className="secondary-button full-width"
                  type="button"
                  disabled={researchBusy}
                  onClick={handleCreateResearchSession}
                >
                  {researchBusy ? 'Creating...' : 'Create governed research'}
                </button>
                {researchError && <p className="provider-warning">{researchError}</p>}
                {researchReport && (
                  <div className="goal-detail">
                    <h3>Research report</h3>
                    <p>{researchReport.summary}</p>
                    <div className="provider-card">
                      <div>
                        <span>Sources</span>
                        <strong>{researchReport.source_count || 0}</strong>
                      </div>
                      <div>
                        <span>Citations</span>
                        <strong>{researchReport.citation_count || 0}</strong>
                      </div>
                      <div>
                        <span>Status</span>
                        <strong>{researchReport.status}</strong>
                      </div>
                    </div>
                    {(researchReport.evidence_gaps || []).map((gap) => (
                      <p className="muted" key={gap}>{gap}</p>
                    ))}
                  </div>
                )}
                {researchSessions.length === 0 && <p className="muted">No research sessions yet.</p>}
                {researchSessions.slice(0, 6).map((session) => (
                  <div className="agent-template-card" key={session.research_id}>
                    <strong>{session.query}</strong>
                    <span>
                      {session.status} · {session.source_count || 0} sources · {session.citation_count || 0} citations
                    </span>
                    <p className="muted">Credibility avg: {session.average_credibility_score || 0}</p>
                    <div className="inline-actions">
                      {session.status === 'pending_approval' && (
                        <>
                          <button type="button" disabled={researchBusy} onClick={() => handleResearchDecision(session.research_id, 'approve')}>
                            Approve
                          </button>
                          <button type="button" disabled={researchBusy} onClick={() => handleResearchDecision(session.research_id, 'reject')}>
                            Reject
                          </button>
                        </>
                      )}
                      {session.status === 'active' && (
                        <button type="button" disabled={researchBusy} onClick={() => handleRunControlledSearch(session.research_id, session.query)}>
                          Run controlled search
                        </button>
                      )}
                      <button type="button" disabled={researchBusy} onClick={() => handleViewResearchReport(session.research_id)}>
                        Report
                      </button>
                    </div>
                    {researchReport && researchReport.research_id === session.research_id && researchReport.top_sources && researchReport.top_sources.length > 0 && (
                      <div style={{ marginTop: '8px', paddingLeft: '8px', borderLeft: '2px solid #5a5a5a' }}>
                        <p style={{ fontWeight: 'bold', fontSize: '11px', margin: '4px 0' }}>Controlled Search Sources:</p>
                        {researchReport.top_sources.map((source) => (
                          <div key={source.source_id || source.url} style={{ fontSize: '11px', marginBottom: '4px' }}>
                            <a href={source.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'underline', color: '#61afef' }}>
                              {source.title}
                            </a>
                            <span style={{ color: '#abb2bf', marginLeft: '6px' }}>
                              ({source.publisher} · Score: {source.credibility_score})
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowQualityPanel((current) => !current)}>
              <span>
                <Gauge size={15} />
                Quality Gate
              </span>
              <ChevronDown size={15} />
            </button>
            {showQualityPanel && (
              <div className="mission-panel">
                <button
                  className="secondary-button full-width"
                  type="button"
                  disabled={qualityBusy}
                  onClick={handleRunQualityChecks}
                >
                  {qualityBusy ? 'Running checks...' : 'Run pytest + build'}
                </button>
                {qualityError && <p className="provider-warning">{qualityError}</p>}
                {!qualityStatus?.latest_run && <p className="muted">No quality run recorded yet.</p>}
                {qualityStatus?.latest_run && (
                  <>
                    <div className="provider-card">
                      <div>
                        <span>Gate</span>
                        <strong>{qualityStatus.latest_run.quality_gate?.passed ? 'passed' : 'blocked'}</strong>
                      </div>
                      <div>
                        <span>Runs</span>
                        <strong>{qualityStatus.total_quality_runs || 0}</strong>
                      </div>
                      <div>
                        <span>Branch</span>
                        <strong>{qualityStatus.latest_run.branch || 'unknown'}</strong>
                      </div>
                      <div>
                        <span>Flaky</span>
                        <strong>{qualityStatus.flaky_tests?.length || 0}</strong>
                      </div>
                    </div>
                    <p className="muted">{qualityStatus.latest_run.quality_gate?.reason}</p>
                    {(qualityStatus.latest_run.command_results || []).map((command) => (
                      <div className="agent-template-card" key={`${qualityStatus.latest_run.quality_run_id}-${command.command}`}>
                        <strong>{command.command}</strong>
                        <span>{command.success ? 'passed' : 'failed'} · exit {command.exit_code}</span>
                      </div>
                    ))}
                    {(qualityStatus.latest_run.test_suggestions?.suggestions || []).slice(0, 4).map((suggestion) => (
                      <div className="agent-template-card" key={`${suggestion.source_file}-${suggestion.test_target}`}>
                        <strong>{suggestion.test_target}</strong>
                        <span>{suggestion.priority} · {suggestion.source_file}</span>
                        <p className="muted">{suggestion.reason}</p>
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowApprovals((current) => !current)}>
              <span>
                <ShieldAlert size={15} />
                Approval Queue
              </span>
              <ChevronDown size={15} />
            </button>
            {showApprovals && (
              <div className="mission-panel">
                {!approvalsAvailable && (
                  <p className="muted">Approval queue is not available yet.</p>
                )}
                {approvalsAvailable && pendingApprovals.length === 0 && (
                  <p className="muted">No pending approvals.</p>
                )}
                {approvalsAvailable && pendingApprovals.map((approval) => (
                  <div className="agent-template-card" key={approval.approval_id}>
                    <strong>{approval.summary || approval.action_type || 'Approval request'}</strong>
                    <span>
                      {formatType(approval.action_type || 'action')} · {approval.risk_level || 'unknown'} risk · {approval.status}
                    </span>
                    {approval.created_at && (
                      <p className="muted">{new Date(approval.created_at).toLocaleString()}</p>
                    )}
                    {(approval.steps || []).length > 0 && (
                      <p className="muted">
                        Steps: {(approval.steps || []).map((step) => step.title || step.step_id).join(', ')}
                      </p>
                    )}
                    <div className="inline-actions">
                      <button
                        type="button"
                        disabled={approvalBusyId === approval.approval_id}
                        onClick={() => handleApprovalDecision(approval.approval_id, 'approve')}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        disabled={approvalBusyId === approval.approval_id}
                        onClick={() => handleApprovalDecision(approval.approval_id, 'reject')}
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowAgentJobs((current) => !current)}>
              <span>
                <Cpu size={15} />
                Agent Jobs
              </span>
              <ChevronDown size={15} />
            </button>
            {showAgentJobs && (
              <div className="mission-panel">
                {!agentJobsAvailable && (
                  <p className="muted">Agent jobs are not available yet.</p>
                )}
                {agentJobsAvailable && agentJobHealth && (
                  <div className="provider-card">
                    <div>
                      <span>Health</span>
                      <strong>{agentJobHealth.healthy ? 'healthy' : 'stale jobs'}</strong>
                    </div>
                    <div>
                      <span>Queued</span>
                      <strong>{agentJobHealth.queued ?? 0}</strong>
                    </div>
                    <div>
                      <span>Running</span>
                      <strong>{agentJobHealth.running ?? 0}</strong>
                    </div>
                    <div>
                      <span>Paused</span>
                      <strong>{agentJobHealth.paused ?? 0}</strong>
                    </div>
                    <div>
                      <span>Total</span>
                      <strong>{agentJobHealth.total_jobs ?? 0}</strong>
                    </div>
                  </div>
                )}
                {agentJobsAvailable && (
                  <div className="inline-actions">
                    <button type="button" disabled={agentJobBusyId === 'create'} onClick={handleCreateTestAgentJob}>
                      Create test job
                    </button>
                    <button type="button" disabled={agentJobBusyId === 'start-next'} onClick={handleStartNextAgentJob}>
                      Start next
                    </button>
                  </div>
                )}
                {agentJobsAvailable && agentJobs.length === 0 && (
                  <p className="muted">No agent jobs yet.</p>
                )}
                {agentJobsAvailable && agentJobs.slice(0, 8).map((job) => (
                  <div className="agent-template-card" key={job.job_id}>
                    <strong>{job.title || job.job_type}</strong>
                    <span>
                      {job.status} · {formatType(job.job_type || 'workflow')}
                      {job.workspace_id ? ` · ${job.workspace_id.slice(0, 8)}` : ''}
                    </span>
                    {job.created_at && (
                      <p className="muted">{new Date(job.created_at).toLocaleString()}</p>
                    )}
                    {job.result_summary && <p className="muted">{job.result_summary}</p>}
                    {job.error && <p className="muted">{job.error}</p>}
                    <div className="inline-actions">
                      {job.status === 'running' && (
                        <>
                          <button type="button" disabled={agentJobBusyId === job.job_id} onClick={() => handleAgentJobAction(job.job_id, 'pause')}>
                            Pause
                          </button>
                          <button type="button" disabled={agentJobBusyId === job.job_id} onClick={() => handleAgentJobAction(job.job_id, 'heartbeat')}>
                            Heartbeat
                          </button>
                        </>
                      )}
                      {job.status === 'paused' && (
                        <button type="button" disabled={agentJobBusyId === job.job_id} onClick={() => handleAgentJobAction(job.job_id, 'resume')}>
                          Resume
                        </button>
                      )}
                      {job.status === 'queued' && (
                        <button type="button" disabled={agentJobBusyId === job.job_id} onClick={() => handleAgentJobAction(job.job_id, 'cancel')}>
                          Cancel
                        </button>
                      )}
                      {!['completed', 'failed', 'canceled'].includes(job.status) && job.status !== 'queued' && (
                        <button type="button" disabled={agentJobBusyId === job.job_id} onClick={() => handleAgentJobAction(job.job_id, 'cancel')}>
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowCodexJobs((current) => !current)}>
              <span>
                <GitBranch size={15} />
                Codex Jobs
              </span>
              <ChevronDown size={15} />
            </button>
            {showCodexJobs && (
              <div className="mission-panel codex-jobs-panel">
                {!codexJobsAvailable && (
                  <p className="muted">Codex worker status is not available yet.</p>
                )}
                {codexJobsAvailable && (
                  <>
                    <div className="codex-worker-summary">
                      <span className={`codex-status-badge codex-status-${codexWorkerSummaryStatus(codexJobs).replace(/\s+/g, '-')}`}>
                        {codexWorkerSummaryStatus(codexJobs)}
                      </span>
                      <span className="muted">{codexJobs.length} job{codexJobs.length === 1 ? '' : 's'}</span>
                    </div>
                    {codexJobs.length === 0 && (
                      <p className="muted">Codex worker idle — no jobs yet.</p>
                    )}
                    {codexJobs.slice(0, 10).map((job) => {
                      const displayStatus = codexJobDisplayStatus(job)
                      const pytest = codexTestResult(job, 'pytest')
                      const build = codexTestResult(job, 'npm run build')
                      return (
                        <div className="codex-job-card" key={job.job_id}>
                          <div className="codex-job-card-header">
                            <strong>{job.issue_identifier || job.issue_id || 'Codex job'}</strong>
                            <span className={`codex-status-badge codex-status-${displayStatus.replace(/\s+/g, '-')}`}>
                              {displayStatus}
                            </span>
                          </div>
                          <p className="muted codex-job-id">{job.job_id}</p>
                          {job.branch_name && <p className="muted">Branch: {job.branch_name}</p>}
                          {job.started_at && (
                            <p className="muted">Started: {new Date(job.started_at).toLocaleString()}</p>
                          )}
                          {job.completed_at && (
                            <p className="muted">Completed: {new Date(job.completed_at).toLocaleString()}</p>
                          )}
                          {job.changed_files?.length > 0 && (
                            <p className="muted">Changed: {job.changed_files.join(', ')}</p>
                          )}
                          <div className="codex-job-results">
                            <span>Tests: {pytest ? (pytest.success ? 'pass' : 'fail') : 'n/a'}</span>
                            <span>Build: {build ? (build.success ? 'pass' : 'fail') : 'n/a'}</span>
                          </div>
                          {job.commit_hash && <p className="muted">Commit: {job.commit_hash}</p>}
                          {job.linear_done && <p className="muted">Linear Done: yes</p>}
                          {job.error && <p className="codex-job-error">{job.error}</p>}
                        </div>
                      )
                    })}
                  </>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowSystemPrompts((current) => !current)}>
              <span>
                <FileText size={15} />
                System Prompts
              </span>
              <ChevronDown size={15} />
            </button>
            {showSystemPrompts && (
              <div className="mission-panel">
                {!systemPromptsAvailable && (
                  <p className="muted">System prompt registry is not available yet.</p>
                )}
                {systemPromptsAvailable && systemPrompts.length === 0 && (
                  <p className="muted">No registered prompts yet.</p>
                )}
                {systemPromptsAvailable && systemPrompts.slice(0, 10).map((prompt) => (
                  <button
                    type="button"
                    className={`goal-card ${selectedPromptAgent === prompt.agent_name ? 'active' : ''}`}
                    key={prompt.prompt_id || prompt.agent_name}
                    onClick={() => handleSelectSystemPrompt(prompt.agent_name)}
                  >
                    <strong>{prompt.agent_name}</strong>
                    <span>{prompt.source || 'registry'} · {prompt.updated_at ? new Date(prompt.updated_at).toLocaleString() : 'n/a'}</span>
                  </button>
                ))}
                {selectedPromptAgent && (
                  <div className="developer-prompt-block">
                    <span>Edit prompt: {selectedPromptAgent}</span>
                    <textarea
                      value={promptDraft}
                      onChange={(event) => setPromptDraft(event.target.value)}
                      rows={8}
                      placeholder="System prompt text..."
                    />
                    <button type="button" disabled={promptSaveBusy || !promptDraft.trim()} onClick={handleSaveSystemPrompt}>
                      Save prompt
                    </button>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        <section className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowAgentBuilder((current) => !current)}>
            <span>
              <Layers3 size={15} />
              Agent Builder
            </span>
            <ChevronDown size={15} />
          </button>
          {showAgentBuilder && (
            <div className="mission-panel">
              <h3>Custom agents</h3>
              {customAgents.length === 0 && <p className="muted">No custom agents yet.</p>}
              {customAgents.slice(0, 6).map((agent) => (
                <div className="agent-template-card" key={agent.agent_id}>
                  <strong>{agent.name}</strong>
                  <span>{agent.enabled ? 'enabled' : 'disabled'} · {agent.approval_level}</span>
                  <p>{agent.description}</p>
                </div>
              ))}
              <h3>Templates</h3>
              {agentTemplates.slice(0, 8).map((template) => (
                <div className="agent-template-card" key={template.name}>
                  <strong>{template.name}</strong>
                  <span>{template.approval_level}</span>
                  <p>{template.description}</p>
                  <button type="button" onClick={() => handleCreateAgentFromTemplate(template.name)}>
                    Create from template
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="sidebar-section history-panel">
          <div className="side-heading">
            <Clock size={15} />
            <span>Run History</span>
          </div>
          <div className="history-list">
            {chats.length === 0 && <p className="muted">No chats yet.</p>}
            {chats.slice(0, 12).map((item) => (
              <div className={`history-item ${sessionId === item.session_id ? 'active' : ''}`} key={item.session_id}>
                <button type="button" onClick={() => loadChat(item.session_id)}>
                  <span>{item.title}</span>
                  <strong>{item.message_count}</strong>
                  <small>{item.updated_at ? new Date(item.updated_at).toLocaleString() : ''}</small>
                </button>
                <div className="chat-row-actions">
                  <button type="button" onClick={() => handleRenameChat(item.session_id, item.title)}>Rename</button>
                  <button type="button" onClick={() => handleDeleteChat(item.session_id)} aria-label="Delete chat">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
        </div>
      </aside>

      <section className="chat-workspace">
        <header className={`chat-topbar ${developerMode ? '' : 'jarvis-topbar'}`}>
          {developerMode ? (
            <>
              <div>
                <div className="section-kicker">
                  <Terminal size={16} />
                  AI Workbench
                </div>
                <h2>Ask EvolveAgent AI</h2>
                <p>Your request is routed through specialist agents and returned as one final answer.</p>
              </div>
              <div className="topbar-actions">
                <button
                  type="button"
                  className="sidebar-toggle"
                  onClick={() => setSidebarOpen((current) => !current)}
                  aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
                  aria-expanded={sidebarOpen}
                >
                  <Menu size={16} />
                </button>
                <button
                  type="button"
                  className="theme-toggle-button"
                  onClick={toggleTheme}
                  aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
                >
                  {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                </button>
                <div className="mode-toggle" role="group" aria-label="Mode toggle">
                  <button className={!developerMode ? 'active' : ''} onClick={() => setDeveloperMode(false)}>
                    Simple
                  </button>
                  <button className={developerMode ? 'active' : ''} onClick={() => setDeveloperMode(true)}>
                    Developer
                  </button>
                </div>
                <div className="status-pill">
                  <Sparkles size={16} />
                  {modeLabel}
                </div>
                <div className="export-actions">
                  <button type="button" onClick={copyConversation} disabled={messages.length === 0}>
                    <Copy size={14} />
                    Copy chat
                  </button>
                  <button type="button" onClick={exportMarkdown} disabled={messages.length === 0}>
                    <Download size={14} />
                    Markdown
                  </button>
                  <button type="button" onClick={exportJson} disabled={messages.length === 0}>
                    JSON
                  </button>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="jarvis-topbar-brand">
                <h2>EvolveAgent AI</h2>
                <p>Voice-controlled multi-agent operating system</p>
              </div>
              <div className="topbar-actions jarvis-topbar-actions">
                <div className="jarvis-status-strip" aria-label="System status">
                  <span>{modeLabel}</span>
                  <span>{imageModeLabel}</span>
                  <span>{workspaces.find((workspace) => workspace.workspace_id === workspaceId)?.name || 'Default Workspace'}</span>
                </div>
                <button
                  type="button"
                  className="theme-toggle-button"
                  onClick={toggleTheme}
                  aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
                >
                  {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                </button>
                <button className="jarvis-icon-button" type="button" onClick={newChat} aria-label="New chat">
                  <MessageSquarePlus size={16} />
                </button>
                <div className="mode-toggle mode-toggle-compact" role="group" aria-label="Mode toggle">
                  <button className={!developerMode ? 'active' : ''} onClick={() => setDeveloperMode(false)}>
                    Simple
                  </button>
                  <button className={developerMode ? 'active' : ''} onClick={() => setDeveloperMode(true)}>
                    Dev
                  </button>
                </div>
              </div>
            </>
          )}
        </header>

        <section className={`chat-scroll ${!developerMode ? 'jarvis-scroll' : ''}`}>
          {messages.length === 0 && !loading && !developerMode && (
            <div className="jarvis-command-center">
              <div className="jarvis-glow" aria-hidden="true" />
              <div className="jarvis-ring" aria-hidden="true" />
              <div className="jarvis-command-header">
                <h2>EvolveAgent AI</h2>
                <p>Speak a command or type a mission</p>
              </div>
              <div className="jarvis-system-readout" aria-label="Capabilities">
                <span>Agents online</span>
                <span>Memory active</span>
                <span>Tools governed</span>
              </div>
              <div className="jarvis-command-options">
                <button
                  type="button"
                  className={`jarvis-command-option speak ${listening ? 'active' : ''}`}
                  onClick={handleJarvisSpeak}
                >
                  <span className="jarvis-option-icon">
                    <Mic size={28} />
                  </span>
                  <strong>Speak</strong>
                  <span className="jarvis-option-subtitle">Start with voice and edit before sending.</span>
                </button>
                <button type="button" className="jarvis-command-option type" onClick={focusComposer}>
                  <span className="jarvis-option-icon">
                    <Keyboard size={28} />
                  </span>
                  <strong>Type</strong>
                  <span className="jarvis-option-subtitle">Open the command line for text, files, or goals.</span>
                </button>
              </div>
              {listening && <p className="jarvis-listening">Listening for your command...</p>}
            </div>
          )}

          {messages.length === 0 && !loading && developerMode && (
              <div className="chat-empty">
              <div className="empty-orb">
                <Brain size={30} />
              </div>
              <h2>Ask EvolveAgent AI</h2>
              <p>A multi-agent AI workspace for planning, writing, coding, analysis, and image prompts.</p>
              <div className="prompt-grid">
                {promptCards.map((prompt) => (
                  <button key={prompt} onClick={() => submitMessage(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => {
            const displayContent = message.result ? formatSimpleAnswer(message.result, message.content) : message.content
            const imageResult = message.result?.image_result
            const automationPlan = message.result?.automation_plan
            const goalResult = message.result?.goal
            const taskGraph = message.result?.task_graph
            const automationResult = message.result?.run_id ? automationResults[message.result.run_id] : null
            const files = message.attached_files || []
            const recordings = message.attached_recordings || []
            const id = messageKey(message)

            return (
              <article
                className={`chat-message ${message.role} ${message.error ? 'error-message' : ''}`}
                key={id}
                onClick={() => message.result && setSelectedRunId(id)}
              >
                <div className="message-avatar">{message.role === 'user' ? <User size={17} /> : <Bot size={17} />}</div>
                <div className="message-body">
                  <div className="message-label">{message.role === 'user' ? 'You' : 'EvolveAgent AI'}</div>
                  <div className="message-content">
                    {message.role === 'assistant' && !message.error ? <MarkdownMessage content={displayContent} /> : displayContent}
                  </div>

                  {files.length > 0 && (
                    <div className="attached-file-list">
                      <span>Attached files</span>
                      {files.map((file) => (
                        <div className="attached-file-pill" key={file.file_id || file.filename}>
                          <FileText size={14} />
                          {file.filename}
                        </div>
                      ))}
                    </div>
                  )}

                  {recordings.length > 0 && (
                    <div className="attached-file-list">
                      <span>Attached recordings</span>
                      {recordings.map((recording) => (
                        <div className="attached-file-pill" key={recording.recording_id || recording.filename}>
                          <Mic size={14} />
                          {recording.filename}
                        </div>
                      ))}
                    </div>
                  )}

                  {imageResult && (
                    <div className="image-result-card">
                      <img src={assetUrl(imageResult.image_url)} alt="Generated image preview" />
                      {imageResult.fallback_used && (
                        <p className="fallback-note">
                          Real image generation failed, so this preview used the mock fallback.
                        </p>
                      )}
                      <div className="prompt-box">
                        <span>Prompt used</span>
                        <p>{imageResult.prompt}</p>
                      </div>
                    </div>
                  )}

                  {automationPlan && (
                    <div className="automation-plan-card">
                      <div className="automation-plan-header">
                        <span>Approval required</span>
                        <strong>{automationPlan.risk_level} risk</strong>
                      </div>
                      <p>{automationPlan.summary}</p>
                      <div className="automation-columns">
                        <div>
                          <span>Files to change</span>
                          {(automationPlan.files_to_change || []).length ? (
                            <ul>{automationPlan.files_to_change.map((file) => <li key={file}>{file}</li>)}</ul>
                          ) : (
                            <p>No direct file edits proposed.</p>
                          )}
                        </div>
                        <div>
                          <span>Commands</span>
                          {(automationPlan.commands_to_run || []).length ? (
                            <ul>{automationPlan.commands_to_run.map((command) => <li key={command}>{command}</li>)}</ul>
                          ) : (
                            <p>No commands proposed.</p>
                          )}
                        </div>
                      </div>
                      {!automationResult ? (
                        <div className="automation-actions">
                          <button type="button" onClick={(event) => {
                            event.stopPropagation()
                            handleAutomationApply(message.result, true)
                          }}>
                            Approve plan
                          </button>
                          <button type="button" onClick={(event) => {
                            event.stopPropagation()
                            handleAutomationApply(message.result, false)
                          }}>
                            Reject
                          </button>
                        </div>
                      ) : (
                        <div className={`automation-result ${automationResult.success ? 'success' : 'failed'}`}>
                          {automationResult.summary}
                        </div>
                      )}
                    </div>
                  )}

                  {goalResult && taskGraph && (
                    <div className="goal-result-card">
                      <div className="automation-plan-header">
                        <span>Mission Control</span>
                        <strong>{goalResult.progress_percent || 0}%</strong>
                      </div>
                      <h3>{goalResult.title}</h3>
                      <p>{goalResult.description}</p>
                      <div className="progress-bar">
                        <span style={{ width: `${goalResult.progress_percent || 0}%` }} />
                      </div>
                      <div className="task-preview-list">
                        {(taskGraph.tasks || []).slice(0, 8).map((task) => (
                          <div className="task-preview" key={task.task_id}>
                            <strong>{task.title}</strong>
                            <span>{task.phase} · {task.priority} · {task.status}</span>
                          </div>
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation()
                          setSelectedGoal({ goal: goalResult, task_graph: taskGraph })
                          setShowMissionControl(true)
                        }}
                      >
                        Open Mission Control
                      </button>
                    </div>
                  )}

                  {message.result && (
                    <>
                      {developerMode && message.role === 'assistant' && (
                        <div className="message-chips">
                          <span>{formatType(message.result.task_type)}</span>
                          <span>{message.result.master_plan.confidence}% routing</span>
                          <span>score {message.result.judge_result.overall_score}</span>
                          <span>{runModeLabel(message.result, modeLabel)}</span>
                          <span>{message.result.memory_saved ? 'memory saved' : 'memory open'}</span>
                        </div>
                      )}
                      <div className="message-actions">
                        {message.role === 'assistant' && (
                          <>
                            <button
                              onClick={(event) => {
                                event.stopPropagation()
                                submitFeedback(message.result, 'helpful')
                              }}
                            >
                              <ThumbsUp size={14} />
                              Helpful
                            </button>
                            <button
                              onClick={(event) => {
                                event.stopPropagation()
                                submitFeedback(message.result, 'not_helpful')
                              }}
                            >
                              <ThumbsDown size={14} />
                              Not helpful
                            </button>
                            <button
                              onClick={(event) => {
                                event.stopPropagation()
                                submitFeedback(message.result, 'saved')
                              }}
                            >
                              Save as good answer
                            </button>
                          </>
                        )}
                        <button
                          onClick={(event) => {
                            event.stopPropagation()
                            copyText(imageResult?.prompt || displayContent)
                          }}
                        >
                          <Copy size={14} />
                          {imageResult ? 'Copy Prompt' : 'Copy'}
                        </button>
                        {message.role === 'user' && (
                          <button
                            onClick={(event) => {
                              event.stopPropagation()
                              editMessage(message)
                            }}
                          >
                            <Edit3 size={14} />
                            Edit
                          </button>
                        )}
                        <button
                          onClick={(event) => {
                            event.stopPropagation()
                            regenerateLastResponse()
                          }}
                        >
                          Regenerate
                        </button>
                        <button
                          onClick={(event) => {
                            event.stopPropagation()
                            setSelectedRunId(id)
                            setDeveloperMode(true)
                          }}
                        >
                          View details
                        </button>
                        <button
                          onClick={(event) => {
                            event.stopPropagation()
                            handleDeleteMessage(message)
                          }}
                        >
                          <Trash2 size={14} />
                          Delete
                        </button>
                      </div>
                    </>
                  )}
                  {!message.result && message.role === 'user' && (
                    <div className="message-actions">
                      <button onClick={() => editMessage(message)}>
                        <Edit3 size={14} />
                        Edit
                      </button>
                      <button onClick={() => handleDeleteMessage(message)}>
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </article>
            )
          })}

          {loading && (
            <article className="chat-message assistant loading-message">
              <div className="message-avatar">
                <Activity size={17} />
              </div>
              <div className="message-body">
                <div className="message-label">EvolveAgent AI</div>
                <div className="progress-timeline">
                  {progressSteps.map((step, index) => (
                    <div className={`progress-step ${index <= progressIndex ? 'active' : ''}`} key={step}>
                      <span>{index + 1}</span>
                      <p>{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            </article>
          )}
        </section>

        <section className={`chat-composer ${developerMode ? '' : 'jarvis-composer'}`}>
          {developerMode && (
          <div className="composer-controls">
            <select value={taskType} onChange={(event) => setTaskType(event.target.value)} aria-label="Task type">
              {taskTypes.map((type) => (
                <option key={type} value={type}>
                  {formatType(type)[0].toUpperCase() + formatType(type).slice(1)}
                </option>
              ))}
            </select>
            <label className="toggle-row" htmlFor="deep-mode">
              <input
                id="deep-mode"
                type="checkbox"
                checked={deepMode}
                onChange={(event) => setDeepMode(event.target.checked)}
              />
              Deep Mode
            </label>
          </div>
          )}
          {attachedFiles.length > 0 && (
            <div className="file-chip-row">
              {attachedFiles.map((file) => (
                <div className={`file-chip ${file.status}`} key={file.file_id}>
                  <FileText size={15} />
                  <div>
                    <strong>{file.filename}</strong>
                    <span>{file.status === 'processed' ? file.extension : file.error || file.status}</span>
                  </div>
                  <button type="button" onClick={() => removeAttachedFile(file.file_id)} aria-label={`Remove ${file.filename}`}>
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
          {attachedRecordings.length > 0 && (
            <div className="file-chip-row">
              {attachedRecordings.map((recording) => (
                <div className={`file-chip ${recording.status}`} key={recording.recording_id}>
                  <Mic size={15} />
                  <div>
                    <strong>{recording.filename}</strong>
                    <span>{recording.status === 'processed' ? `${recording.extension} transcript ready` : recording.error || recording.status}</span>
                  </div>
                  <button type="button" onClick={() => removeAttachedRecording(recording.recording_id)} aria-label={`Remove ${recording.filename}`}>
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="input-shell">
            <label className="upload-button" aria-label="Attach files">
              <input
                type="file"
                multiple
                onChange={handleFileSelect}
                accept=".txt,.md,.json,.csv,.py,.js,.ts,.jsx,.tsx,.html,.css,.pdf,.docx"
              />
              {uploadingFiles ? <Activity size={18} /> : <Paperclip size={18} />}
            </label>
            <label className="upload-button" aria-label="Attach recordings">
              <input
                type="file"
                multiple
                onChange={handleRecordingSelect}
                accept=".mp3,.m4a,.wav,.mp4,.webm,audio/*,video/mp4,video/webm"
              />
              {uploadingRecordings ? <Activity size={18} /> : <Mic size={18} />}
            </label>
            <button className={`mic-button ${listening ? 'listening' : ''}`} type="button" onClick={startVoiceInput} aria-label="Use voice input">
              <Mic size={18} />
            </button>
            <textarea
              ref={composerRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={developerMode ? 'Ask EvolveAgent AI anything...' : 'Send a command...'}
              rows={1}
            />
            <button className="send-button" onClick={() => submitMessage()} disabled={loading || uploadingFiles || uploadingRecordings || input.trim().length < 1} aria-label="Send message">
              {loading ? <Activity size={18} /> : <Send size={18} />}
            </button>
          </div>
          {listening && <p className="voice-status">Listening for your command...</p>}
          {voiceUsed && voiceTranscript && <p className="voice-status">Voice transcript ready. You can edit it before sending.</p>}
          {error && <p className="error">{error}</p>}
          {copied && <p className="copy-toast">{copied}</p>}
        </section>
      </section>

      <aside className={`inspector ${developerMode ? 'visible' : 'simple-hidden'}`}>
        <div className="side-heading">
          <PanelRight size={15} />
          <span>Inspector</span>
        </div>

        {selectedRun ? (
          <>
            <details className="inspector-section" open>
              <summary>
                <Database size={15} />
                Run Summary
                <ChevronDown size={15} />
              </summary>
              <div className="mini-grid">
                <div>
                  <span>Type</span>
                  <strong>{formatType(selectedRun.master_plan.detected_task_type)}</strong>
                </div>
                <div>
                  <span>Confidence</span>
                  <strong>{selectedRun.master_plan.confidence}%</strong>
                </div>
                <div>
                  <span>Score</span>
                  <strong>{selectedRun.judge_result.overall_score}</strong>
                </div>
                <div>
                  <span>Memory</span>
                  <strong>{selectedRun.memory_saved ? 'Saved' : 'Open'}</strong>
                </div>
                <div>
                  <span>Session</span>
                  <strong>{selectedRun.session_id?.slice(0, 8) || 'n/a'}</strong>
                </div>
                <div>
                  <span>Message</span>
                  <strong>{selectedRun.message_id?.slice(0, 8) || 'n/a'}</strong>
                </div>
                <div>
                  <span>Run</span>
                  <strong>{selectedRun.run_id?.slice(0, 8) || 'n/a'}</strong>
                </div>
                <div>
                  <span>Workspace</span>
                  <strong>{selectedRun.workspace_id?.slice(0, 8) || 'default'}</strong>
                </div>
                <div>
                  <span>Memory used</span>
                  <strong>{selectedRun.memory_used ? 'Yes' : 'No'}</strong>
                </div>
              </div>
            </details>

            {(selectedRun.memory_used || selectedRun.workspace_memory_used?.length > 0) && (
              <details className="inspector-section" open>
                <summary>
                  <Database size={15} />
                  Workspace Memory
                  <ChevronDown size={15} />
                </summary>
                <div className="mini-grid">
                  <div>
                    <span>Entries used</span>
                    <strong>{selectedRun.workspace_memory_used?.length || 0}</strong>
                  </div>
                  <div>
                    <span>Context chars</span>
                    <strong>{selectedRun.memory_context_characters || 0}</strong>
                  </div>
                </div>
                <div className="agent-list">
                  {(selectedRun.workspace_memory_used || []).map((memory) => (
                    <div className="provider-row" key={memory.memory_id}>
                      <strong>{memory.title}</strong>
                      <div className="model-meta">
                        <span>{formatType(memory.type)}</span>
                        <span>{memory.importance}</span>
                        <span>{memory.memory_id}</span>
                      </div>
                      <p>{memory.content}</p>
                    </div>
                  ))}
                </div>
              </details>
            )}

            {(selectedRun.goal || selectedRun.goal_id || selectedRun.custom_agent) && (
              <details className="inspector-section" open>
                <summary>
                  <Flag size={15} />
                  Mission / Custom Agent
                  <ChevronDown size={15} />
                </summary>
                {selectedRun.goal && (
                  <div className="developer-prompt-block">
                    <span>Goal</span>
                    <p>{selectedRun.goal.title}</p>
                    <div className="model-meta">
                      <span>{selectedRun.goal.goal_id}</span>
                      <span>{selectedRun.goal.status}</span>
                      <span>{selectedRun.goal.progress_percent || 0}%</span>
                      <span>{selectedRun.goal.risk_level} risk</span>
                    </div>
                  </div>
                )}
                {selectedRun.goal_id && !selectedRun.goal && (
                  <div className="developer-prompt-block">
                    <span>Goal metadata</span>
                    <p>goal_id: {selectedRun.goal_id}</p>
                    {selectedRun.goal_task_id && <p>task_id: {selectedRun.goal_task_id}</p>}
                  </div>
                )}
                {selectedRun.task_graph && (
                  <div className="agent-list">
                    {(selectedRun.task_graph.tasks || []).map((task) => (
                      <div className="provider-row" key={task.task_id}>
                        <strong>{task.title}</strong>
                        <div className="model-meta">
                          <span>{task.phase}</span>
                          <span>{task.status}</span>
                          <span>{task.priority}</span>
                          <span>{task.recommended_agent}</span>
                          {task.requires_approval && <span>approval</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {selectedRun.custom_agent && (
                  <div className="developer-prompt-block">
                    <span>Custom agent</span>
                    <p>{selectedRun.custom_agent.name}: {selectedRun.custom_agent.description}</p>
                    <div className="model-meta">
                      <span>{selectedRun.custom_agent.agent_id}</span>
                      <span>{selectedRun.custom_agent.model_preference}</span>
                      <span>{selectedRun.custom_agent.memory_scope}</span>
                      <span>{selectedRun.custom_agent.approval_level}</span>
                    </div>
                    <p>{selectedRun.custom_agent.prompt}</p>
                  </div>
                )}
              </details>
            )}

            {selectedRun.quality_gates && (
              <details className="inspector-section" open>
                <summary>
                  <ShieldAlert size={15} />
                  Security & Governance
                  <ChevronDown size={15} />
                </summary>
                <div className="mini-grid">
                  <div>
                    <span>Prompt check</span>
                    <strong>{selectedRun.quality_gates.prompt_injection_check}</strong>
                  </div>
                  <div>
                    <span>Secret scan</span>
                    <strong>{selectedRun.quality_gates.secret_scan}</strong>
                  </div>
                  <div>
                    <span>Permission</span>
                    <strong>{selectedRun.quality_gates.permission_check}</strong>
                  </div>
                  <div>
                    <span>File context</span>
                    <strong>{selectedRun.quality_gates.file_context_check}</strong>
                  </div>
                </div>
                {selectedRun.security_report && (
                  <div className="developer-prompt-block">
                    <span>Risk assessment</span>
                    <p>
                      {selectedRun.security_report.risk_level} risk · score {selectedRun.security_report.risk_score} · permission{' '}
                      {selectedRun.security_report.permission_level}
                    </p>
                    <p>{selectedRun.security_report.recommendation}</p>
                    {(selectedRun.security_report.prompt_injection?.suspicious_phrases || []).length > 0 && (
                      <>
                        <h3>Suspicious phrases</h3>
                        <ul>
                          {selectedRun.security_report.prompt_injection.suspicious_phrases.map((phrase) => (
                            <li key={phrase}>{phrase}</li>
                          ))}
                        </ul>
                      </>
                    )}
                    {selectedRun.security_report.secret_scan?.secrets_detected && (
                      <p>
                        Redacted {selectedRun.security_report.secret_scan.redaction_count} secret-like value(s):{' '}
                        {(selectedRun.security_report.secret_scan.detected_types || []).join(', ')}
                      </p>
                    )}
                  </div>
                )}
                {(selectedRun.governance_events || []).length > 0 && (
                  <div className="agent-list">
                    <h3>Governance events</h3>
                    {selectedRun.governance_events.map((event, index) => (
                      <div className="provider-row" key={`${event.action_type}-${index}`}>
                        <strong>{event.action_type}</strong>
                        <div className="model-meta">
                          <span>{event.permission_level}</span>
                          {event.blocked && <span>blocked</span>}
                          {event.approved && <span>approved</span>}
                          <span>risk {event.risk_score}</span>
                        </div>
                        <p>{event.reason}</p>
                      </div>
                    ))}
                  </div>
                )}
              </details>
            )}

            {developerMode && (
              <details className="inspector-section">
                <summary>
                  <Route size={15} />
                  Tool Trace
                  <ChevronDown size={15} />
                </summary>
                {(selectedRun.tool_trace || []).length === 0 ? (
                  <p className="muted">No tools were selected for this run.</p>
                ) : (
                  <div className="agent-list">
                    {(selectedRun.tool_trace || []).map((tool, index) => (
                      <div className="provider-row" key={`${tool.tool_name || 'tool'}-${index}`}>
                        <strong>{tool.tool_name || 'unknown'}</strong>
                        <div className="model-meta">
                          <span>{tool.source || 'n/a'}</span>
                          <span>{tool.permission_level || 'n/a'}</span>
                          {tool.selected && <span>selected</span>}
                          {tool.executed && <span>executed</span>}
                          {tool.blocked && <span>blocked</span>}
                          {tool.approval_required && <span>approval required</span>}
                        </div>
                        {tool.sanitized_input && (
                          <p>
                            <span>Input: </span>
                            {tool.sanitized_input}
                          </p>
                        )}
                        {tool.result_summary && (
                          <p>
                            <span>Result: </span>
                            {tool.result_summary}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </details>
            )}

            <article className="metric-card score-card">
              <div className="section-title">
                <Gauge size={17} />
                <h2>Judge Score</h2>
              </div>
              <strong>{selectedRun.judge_result.overall_score}</strong>
              <p>{selectedRun.judge_result.recommendation}</p>
            </article>

            <details className="inspector-section" open>
              <summary>
                <MoreHorizontal size={15} />
                Provider Metadata
                <ChevronDown size={15} />
              </summary>
              <div className="agent-list">
                {selectedRun.agent_outputs.map((item) => (
                  <div className="provider-row" key={`${item.agent_name}-${item.model}`}>
                    <strong>{item.agent_name}</strong>
                    <div className="model-meta">
                      <span>{item.provider}</span>
                      <span>{item.model}</span>
                      <span>{item.latency_ms} ms</span>
                      {item.fallback_used && <span>fallback</span>}
                      {item.error && <span>{item.error}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </details>

            {selectedRun.image_result && (
              <article className="metric-card">
                <div className="section-title">
                  <Sparkles size={17} />
                  <h2>Image Result</h2>
                </div>
                <img className="inspector-image" src={assetUrl(selectedRun.image_result.image_url)} alt="Generated image preview" />
                <div className="model-meta">
                  <span>{selectedRun.image_result.provider}</span>
                  <span>{selectedRun.image_result.model}</span>
                  {selectedRun.image_result.fallback_used && <span>fallback used</span>}
                  {selectedRun.image_result.safety_rewritten && <span>safety rewritten</span>}
                </div>
                {selectedRun.image_result.fallback_error && (
                  <div className="developer-prompt-block warning-block">
                    <span>Fallback reason</span>
                    <p>{selectedRun.image_result.fallback_error}</p>
                  </div>
                )}
                <div className="developer-prompt-block">
                  <span>Original user prompt</span>
                  <p>{selectedRun.image_result.original_prompt || 'Not stored for this run.'}</p>
                </div>
                <div className="developer-prompt-block">
                  <span>Safe rewritten prompt</span>
                  <p>{selectedRun.image_result.prompt}</p>
                </div>
              </article>
            )}

            {selectedRun.file_context_used && (
              <details className="inspector-section" open>
                <summary>
                  <FileText size={15} />
                  File Context
                  <ChevronDown size={15} />
                </summary>
                <div className="mini-grid">
                  <div>
                    <span>Context used</span>
                    <strong>{selectedRun.file_context_used ? 'Yes' : 'No'}</strong>
                  </div>
                  <div>
                    <span>Characters</span>
                    <strong>{selectedRun.file_context_characters || 0}</strong>
                  </div>
                  <div>
                    <span>Files</span>
                    <strong>{selectedRun.files_used?.length || 0}</strong>
                  </div>
                </div>
                <div className="agent-list">
                  {(selectedRun.files_used || []).map((file) => (
                    <div className="provider-row" key={file.file_id}>
                      <strong>{file.filename}</strong>
                      <div className="model-meta">
                        <span>{file.extension}</span>
                        <span>{file.content_type || 'unknown type'}</span>
                        <span>{file.size_bytes} bytes</span>
                        <span>{file.extracted_text_length} chars</span>
                      </div>
                    </div>
                  ))}
                </div>
                {selectedRun.file_summary && (
                  <div className="developer-prompt-block">
                    <span>File summary</span>
                    <p>{selectedRun.file_summary.summary}</p>
                    <ul>{selectedRun.file_summary.key_points.map((point) => <li key={point}>{point}</li>)}</ul>
                  </div>
                )}
              </details>
            )}

            {selectedRun.recording_context_used && (
              <details className="inspector-section" open>
                <summary>
                  <Mic size={15} />
                  Recording Context
                  <ChevronDown size={15} />
                </summary>
                <div className="mini-grid">
                  <div>
                    <span>Context used</span>
                    <strong>{selectedRun.recording_context_used ? 'Yes' : 'No'}</strong>
                  </div>
                  <div>
                    <span>Recordings</span>
                    <strong>{selectedRun.recordings_used?.length || 0}</strong>
                  </div>
                  <div>
                    <span>Actions</span>
                    <strong>{selectedRun.action_items?.length || 0}</strong>
                  </div>
                  <div>
                    <span>Decisions</span>
                    <strong>{selectedRun.decisions?.length || 0}</strong>
                  </div>
                </div>
                <div className="agent-list">
                  {(selectedRun.recordings_used || []).map((recording) => (
                    <div className="provider-row" key={recording.recording_id}>
                      <strong>{recording.filename}</strong>
                      <div className="model-meta">
                        <span>{recording.extension}</span>
                        <span>{recording.content_type || 'unknown type'}</span>
                        <span>{recording.transcript_length} chars</span>
                        <span>{recording.provider}/{recording.model}</span>
                        {recording.fallback_used && <span>fallback</span>}
                      </div>
                    </div>
                  ))}
                </div>
                {selectedRun.transcript_preview && (
                  <div className="developer-prompt-block">
                    <span>Transcript preview</span>
                    <p>{selectedRun.transcript_preview}</p>
                  </div>
                )}
                {selectedRun.recording_summary && (
                  <div className="developer-prompt-block">
                    <span>Recording summary</span>
                    <p>{selectedRun.recording_summary.detailed_summary}</p>
                    <h3>Action items</h3>
                    <ul>{(selectedRun.recording_summary.action_items || []).map((item) => <li key={item}>{item}</li>)}</ul>
                    <h3>Decisions</h3>
                    <ul>{(selectedRun.recording_summary.decisions || []).map((item) => <li key={item}>{item}</li>)}</ul>
                  </div>
                )}
              </details>
            )}

            <details className="inspector-section" open>
              <summary>
                <Route size={15} />
                Workflow Trace
                <ChevronDown size={15} />
              </summary>
              <p className="plan-reason">{selectedRun.master_plan.selection_reason}</p>
              <div className="trace-list compact">
                {selectedRun.workflow_trace.map((step) => (
                  <div className="trace-item" key={`${step.step}-${step.stage}-${step.agent_name}`}>
                    <div className={`trace-number ${step.status}`}>{step.step}</div>
                    <div>
                      <div className="trace-heading">
                        <strong>{step.stage}</strong>
                        <span>{step.agent_name}</span>
                      </div>
                      <p>{step.summary}</p>
                    </div>
                  </div>
                ))}
              </div>
            </details>

            <details className="inspector-section">
              <summary>
                <Gauge size={15} />
                Judge Result
                <ChevronDown size={15} />
              </summary>
              <p className="plan-reason">{selectedRun.judge_result.recommendation}</p>
              <h3>Strengths</h3>
              <ul>{selectedRun.judge_result.strengths.map((item) => <li key={item}>{item}</li>)}</ul>
              <h3>Weaknesses</h3>
              <ul>{selectedRun.judge_result.weaknesses.map((item) => <li key={item}>{item}</li>)}</ul>
            </details>

            <details className="inspector-section" open>
              <summary>
                <BarChart3 size={15} />
                Agent Evaluation
                <ChevronDown size={15} />
              </summary>
              <div className="mini-grid">
                <div>
                  <span>Strongest</span>
                  <strong>{selectedRun.judge_result.strongest_agent || 'n/a'}</strong>
                </div>
                <div>
                  <span>Weakest</span>
                  <strong>{selectedRun.judge_result.weakest_agent || 'n/a'}</strong>
                </div>
              </div>
              <h3>Per-agent scores</h3>
              <div className="agent-list">
                {(selectedRun.judge_result.per_agent_scores || []).map((item) => (
                  <div className="provider-row" key={item.agent_name}>
                    <strong>{item.agent_name}</strong>
                    <div className="model-meta">
                      <span>usefulness {item.usefulness_score}</span>
                      <span>clarity {item.clarity_score}</span>
                    </div>
                    <p>{item.contribution_summary}</p>
                    <p><strong>Weakness:</strong> {item.weakness}</p>
                    <p><strong>Improve:</strong> {item.improvement_suggestion}</p>
                  </div>
                ))}
              </div>
              <h3>Workflow strengths</h3>
              <ul>{(selectedRun.judge_result.workflow_strengths || []).map((item) => <li key={item}>{item}</li>)}</ul>
              <h3>Workflow weaknesses</h3>
              <ul>{(selectedRun.judge_result.workflow_weaknesses || []).map((item) => <li key={item}>{item}</li>)}</ul>
            </details>

            <details className="inspector-section" open={developerMode}>
              <summary>
                <Bot size={15} />
                Agent Outputs
                <ChevronDown size={15} />
              </summary>
              <div className="agent-list">
                {selectedRun.agent_outputs.length === 0 && <p className="muted">No text agents were run for this task.</p>}
                {selectedRun.agent_outputs.map((item) => (
                  <details key={item.agent_name}>
                    <summary>{item.agent_name}</summary>
                    <div className="model-meta">
                      <span>{item.provider}</span>
                      <span>{item.model}</span>
                      <span>{item.latency_ms} ms</span>
                      {item.fallback_used && <span>fallback</span>}
                    </div>
                    <p>{item.output}</p>
                  </details>
                ))}
              </div>
            </details>

            <details className="inspector-section" open={developerMode && selectedRun.consensus_candidates.length > 0}>
              <summary>
                <GitBranch size={15} />
                Deep Mode Consensus
                <ChevronDown size={15} />
              </summary>
              {selectedRun.consensus_candidates.length === 0 ? (
                <p className="muted">Deep Mode was not used for this response.</p>
              ) : (
                <div className="agent-list">
                  <p className="developer-help">Deep Mode compares multiple model candidates before writing the final answer.</p>
                  {selectedRun.consensus_winner && (
                    <div className="detail-card">
                      <strong>Selected winner</strong>
                      <p>{selectedRun.consensus_winner}</p>
                      {selectedRun.consensus_judge_reason && <p>{selectedRun.consensus_judge_reason}</p>}
                      {(selectedRun.consensus_disagreement_notes || []).length > 0 && (
                        <ul>
                          {selectedRun.consensus_disagreement_notes.map((note) => <li key={note}>{note}</li>)}
                        </ul>
                      )}
                    </div>
                  )}
                  {selectedRun.consensus_candidates.map((item) => (
                    <details key={item.agent_name}>
                      <summary>{item.agent_name}</summary>
                      <div className="model-meta">
                        <span>{item.provider}</span>
                        <span>{item.model}</span>
                        <span>{item.latency_ms} ms</span>
                        {item.fallback_used && <span>fallback</span>}
                      </div>
                      {item.fallback_used && (
                        <p className="fallback-note">Fallback used because provider was unavailable or failed.</p>
                      )}
                      <p>{previewText(item.output)}</p>
                    </details>
                  ))}
                </div>
              )}
            </details>

            <details className="inspector-section" open>
              <summary>
                <ShieldAlert size={15} />
                Evolution Notes
                <ChevronDown size={15} />
              </summary>
              <ul>
                {selectedRun.evolution_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </details>

            {selectedRun.automation_plan && (
              <details className="inspector-section" open>
                <summary>
                  <Terminal size={15} />
                  Automation Plan
                  <ChevronDown size={15} />
                </summary>
                <div className="developer-prompt-block">
                  <span>Plan summary</span>
                  <p>{selectedRun.automation_plan.summary}</p>
                </div>
                <div className="mini-grid">
                  <div>
                    <span>Risk</span>
                    <strong>{selectedRun.automation_plan.risk_level}</strong>
                  </div>
                  <div>
                    <span>Status</span>
                    <strong>{selectedRun.automation_status || 'pending'}</strong>
                  </div>
                </div>
                {selectedRun.automation_plan.project_scan && (
                  <div className="developer-prompt-block">
                    <span>Project scan</span>
                    <p>{selectedRun.automation_plan.project_scan.scan_summary}</p>
                    <div className="model-meta">
                      {(selectedRun.automation_plan.project_scan.frameworks_detected || []).map((framework) => (
                        <span key={framework}>{framework}</span>
                      ))}
                      {selectedRun.automation_plan.project_scan.package_manager && (
                        <span>{selectedRun.automation_plan.project_scan.package_manager}</span>
                      )}
                    </div>
                  </div>
                )}
                <h3>Files to change</h3>
                <ul>{(selectedRun.automation_plan.files_to_change || []).map((file) => <li key={file}>{file}</li>)}</ul>
                <h3>Commands to run</h3>
                <ul>{(selectedRun.automation_plan.commands_to_run || []).map((command) => <li key={command}>{command}</li>)}</ul>
                <h3>Consensus planning</h3>
                <p>{selectedRun.automation_plan.judge_reason}</p>
              </details>
            )}

            {developerMode && (
              <details className="inspector-section">
                <summary>
                  <ShieldAlert size={15} />
                  Approval Audit
                  <ChevronDown size={15} />
                </summary>
                {!approvalAuditAvailable && (
                  <p className="muted">Approval queue is not available yet.</p>
                )}
                {approvalAuditAvailable && approvalAudit.length === 0 && (
                  <p className="muted">No approval audit entries yet.</p>
                )}
                {approvalAuditAvailable && approvalAudit.length > 0 && (
                  <div className="agent-list">
                    {approvalAudit.map((entry, index) => (
                      <div className="provider-row" key={entry.approval_id || entry.audit_id || index}>
                        <strong>{entry.decision || entry.status || 'decision'}</strong>
                        <div className="model-meta">
                          <span>{formatType(entry.action_type || 'action')}</span>
                          <span>{entry.risk_level || 'unknown'} risk</span>
                          {entry.run_id && <span>{entry.run_id.slice(0, 8)}</span>}
                        </div>
                        {entry.comment && <p>{entry.comment}</p>}
                        {entry.created_at && (
                          <p className="muted">{new Date(entry.created_at).toLocaleString()}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </details>
            )}

            {developerMode && selectedRun.automation_apply_result && (
              <details className="inspector-section">
                <summary>
                  <Edit3 size={15} />
                  File Apply Result
                  <ChevronDown size={15} />
                </summary>
                <div className={`automation-result ${selectedRun.automation_apply_result.success ? 'success' : 'failed'}`}>
                  <div className="mini-grid">
                    <div>
                      <span>Result</span>
                      <strong>{selectedRun.automation_apply_result.success ? 'Success' : 'Failed'}</strong>
                    </div>
                  </div>
                  {selectedRun.automation_apply_result.summary && (
                    <p>{selectedRun.automation_apply_result.summary}</p>
                  )}
                </div>
                <h3>Changed files</h3>
                {(selectedRun.automation_apply_result.changed_files || []).length > 0 ? (
                  <ul>{selectedRun.automation_apply_result.changed_files.map((file) => <li key={file}>{file}</li>)}</ul>
                ) : (
                  <p className="muted">None</p>
                )}
                <h3>Created files</h3>
                {(selectedRun.automation_apply_result.created_files || []).length > 0 ? (
                  <ul>{selectedRun.automation_apply_result.created_files.map((file) => <li key={file}>{file}</li>)}</ul>
                ) : (
                  <p className="muted">None</p>
                )}
                <h3>Backup paths</h3>
                {(selectedRun.automation_apply_result.backup_paths || []).length > 0 ? (
                  <ul>{selectedRun.automation_apply_result.backup_paths.map((backupPath) => <li key={backupPath}>{backupPath}</li>)}</ul>
                ) : (
                  <p className="muted">None</p>
                )}
                <h3>Diff paths</h3>
                {(selectedRun.automation_apply_result.diff_paths || []).length > 0 ? (
                  <ul>{selectedRun.automation_apply_result.diff_paths.map((diffPath) => <li key={diffPath}>{diffPath}</li>)}</ul>
                ) : (
                  <p className="muted">None</p>
                )}
                <h3>Errors</h3>
                {(selectedRun.automation_apply_result.errors || []).length > 0 ? (
                  <ul>{selectedRun.automation_apply_result.errors.map((error) => <li key={error}>{error}</li>)}</ul>
                ) : (
                  <p className="muted">None</p>
                )}
                {(selectedRun.automation_apply_result.command_results || []).length > 0 && (
                  <>
                    <h3>Command results</h3>
                    <div className="agent-list">
                      {selectedRun.automation_apply_result.command_results.map((commandResult, index) => (
                        <div
                          className={`command-result ${commandResult.success ? 'success' : 'failed'}`}
                          key={`${commandResult.command || 'command'}-${index}`}
                        >
                          <strong>{commandResult.command || 'unknown command'}</strong>
                          <div className="model-meta">
                            <span>exit {commandResult.exit_code ?? 'n/a'}</span>
                            <span>{commandResult.success ? 'passed' : 'failed'}</span>
                          </div>
                          {commandResult.stdout && <pre>{commandResult.stdout}</pre>}
                          {commandResult.stderr && <pre>{commandResult.stderr}</pre>}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </details>
            )}


            {learningReport && (
              <details className="inspector-section">
                <summary>
                  <Brain size={15} />
                  Digital Twin
                  <ChevronDown size={15} />
                </summary>
                {digitalTwinError && <p className="provider-warning">{digitalTwinError}</p>}
                {digitalTwinProfile ? (
                  <>
                    <div className="mini-grid">
                      <div>
                        <span>Detail</span>
                        <strong>{digitalTwinProfile.style_profile?.detail_level || 'balanced'}</strong>
                      </div>
                      <div>
                        <span>Technical</span>
                        <strong>{digitalTwinProfile.style_profile?.technical_level || 'adaptive'}</strong>
                      </div>
                      <div>
                        <span>Format</span>
                        <strong>{digitalTwinProfile.style_profile?.format || 'mixed'}</strong>
                      </div>
                      <div>
                        <span>Planning</span>
                        <strong>{digitalTwinProfile.style_profile?.planning_style || 'pragmatic'}</strong>
                      </div>
                    </div>
                    <h3>Top preferences</h3>
                    <ul>
                      {(digitalTwinProfile.top_preferences || []).slice(0, 5).map((item) => (
                        <li key={item.preference}>{item.preference}: {item.score}</li>
                      ))}
                    </ul>
                    <h3>Recommendations</h3>
                    <ul>
                      {(digitalTwinProfile.recommendations || []).map((item) => <li key={item}>{item}</li>)}
                    </ul>
                    <p className="muted">{digitalTwinProfile.safety_note}</p>
                    <div className="inline-actions">
                      <button className="secondary-button" type="button" disabled={digitalTwinBusy} onClick={handleRefreshDigitalTwin}>Refresh</button>
                      <button className="secondary-button" type="button" disabled={digitalTwinBusy} onClick={handleUpdateDigitalTwin}>Update style</button>
                    </div>
                  </>
                ) : (
                  <button className="secondary-button" type="button" disabled={digitalTwinBusy} onClick={handleRefreshDigitalTwin}>
                    Create Digital Twin profile
                  </button>
                )}
              </details>
            )}

            {learningReport && (
              <details className="inspector-section">
                <summary>
                  <Brain size={15} />
                  Learning Report
                  <ChevronDown size={15} />
                </summary>
                <div className="mini-grid">
                  <div>
                    <span>Runs analyzed</span>
                    <strong>{learningReport.total_runs_analyzed}</strong>
                  </div>
                  <div>
                    <span>Prompt proposals</span>
                    <strong>{learningReport.proposed_prompt_versions?.length || 0}</strong>
                  </div>
                </div>
                <h3>Strongest agents</h3>
                <ul>{(learningReport.strongest_agents || []).map((item) => <li key={item.agent_name}>{item.agent_name}: {item.average_score}</li>)}</ul>
                <h3>Weakest agents by task</h3>
                {(learningReport.weakest_agents_by_task_type || []).map((group) => (
                  <div className="detail-card" key={group.task_type}>
                    <strong>{formatType(group.task_type)}</strong>
                    <ul>{(group.agents || []).map((item) => <li key={item.agent_name}>{item.agent_name}: {item.average_score}</li>)}</ul>
                  </div>
                ))}
                <h3>Workflow recommendations</h3>
                {(learningReport.best_workflows_by_task_type || []).slice(0, 4).map((workflow) => (
                  <div className="detail-card" key={workflow.task_type}>
                    <strong>{formatType(workflow.task_type)} · score {workflow.average_score}</strong>
                    <p>Feedback positive rate: {Math.round((workflow.feedback_positive_rate || 0) * 100)}%</p>
                    <p>Fallback rate: {Math.round((workflow.fallback_rate || 0) * 100)}%</p>
                    <p>Recommended workflow: {(workflow.recommended_workflow || workflow.best_agents || []).join(', ')}</p>
                  </div>
                ))}
                <h3>Prompt suggestions</h3>
                <ul>{(learningReport.prompt_improvement_suggestions || []).map((item) => <li key={item}>{item}</li>)}</ul>
                <h3>Model routing</h3>
                <ul>{(learningReport.model_routing_suggestions || []).map((item) => <li key={`${item.category}-${item.recommendation}`}>{item.category}: {item.recommendation}</li>)}</ul>
                <h3>User preferences</h3>
                <ul>{(learningReport.user_preference_patterns || []).map((item) => <li key={item.preference}>{item.preference}: {item.score}</li>)}</ul>
                <h3>Recurring failure reasons</h3>
                <ul>{(learningReport.recurring_failure_reasons || []).map((item) => <li key={item.reason}>{item.reason}: {item.count}</li>)}</ul>
                <h3>Recommended next actions</h3>
                <ul>{(learningReport.recommended_next_actions || []).map((item) => <li key={item}>{item}</li>)}</ul>
                <h3>Goal workflow improvements</h3>
                <ul>{(learningReport.workflow_improvements_for_goals || []).map((item) => <li key={item}>{item}</li>)}</ul>
                <h3>Custom agent recommendations</h3>
                <ul>{(learningReport.recommended_custom_agents || []).map((item) => <li key={`${item.agent_name}-${item.recommendation}`}>{item.agent_name || 'Agent Builder'}: {item.recommendation}</li>)}</ul>
                <h3>Goal blockers</h3>
                <ul>{(learningReport.recurring_goal_blockers || []).map((item) => <li key={item.task_id || item.reason}>{item.title || item.reason}</li>)}</ul>
                <h3>Prompt versions</h3>
                {(learningReport.active_prompt_versions || []).map((version) => (
                  <div className="detail-card" key={version.version_id}>
                    <strong>{version.agent_name} · active</strong>
                    <p>{version.reason}</p>
                    <button className="secondary-button" type="button" onClick={() => decidePromptVersion(version, 'rollback')}>Rollback</button>
                  </div>
                ))}
                {(learningReport.proposed_prompt_versions || []).map((version) => (
                  <div className="detail-card" key={version.version_id}>
                    <strong>{version.agent_name} · proposed</strong>
                    <p>{version.reason}</p>
                    <div className="inline-actions">
                      <button className="secondary-button" type="button" onClick={() => decidePromptVersion(version, 'approve')}>Approve</button>
                      <button className="secondary-button" type="button" onClick={() => decidePromptVersion(version, 'reject')}>Reject</button>
                    </div>
                  </div>
                ))}
              </details>
            )}

            <details className="inspector-section">
              <summary>
                <MoreHorizontal size={15} />
                Raw JSON
                <ChevronDown size={15} />
              </summary>
              <button className="raw-toggle" type="button" onClick={() => setShowRawJson((current) => !current)}>
                {showRawJson ? 'Hide raw JSON' : 'Show raw JSON'}
              </button>
              {showRawJson && <pre className="raw-json">{JSON.stringify(selectedRun, null, 2)}</pre>}
            </details>
          </>
        ) : (
          <p className="muted">Run a task to inspect routing, model choices, score, and saved memory.</p>
        )}

        <p className="safety">
          Decision-support only. Not legal, medical, financial, or professional advice. Human review is required.
        </p>
      </aside>
    </main>
  )
}

export default App
