import React, { useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Card } from './components/ui/Card.jsx'
import { Button } from './components/ui/Button.jsx'
import { Badge } from './components/ui/Badge.jsx'
import { CommandPalette } from './components/layout/CommandPalette.jsx'
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
  Shield,
  ShieldAlert,
  Sparkles,
  Volume2,
  VolumeX,
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
  createEvaluationABTest,
  createEvaluationRun,
  applyAutomation,
  approvePromptVersion,
  completeLinearIssue,
  exportComplianceReport,
  exportEvaluationResults,
  getLinearCursorHandoff,
  verifyLinearCursorWork,
  createChat,
  deleteChat,
  deleteMessage,
  deleteWorkspace,
  deleteWorkspaceMemory,
  getAnalytics,
  getAgentTemplates,
  getAgentMarketplaceDashboard,
  getAgentMarketplacePacks,
  getAgentMarketplaceTeams,
  getAppBuilderTemplates,
  getChat,
  getChats,
  getComplianceAuditLog,
  getComplianceRetentionPolicies,
  getComplianceSummary,
  getCustomAgents,
  getEvaluationBenchmarks,
  getEvaluationDashboard,
  getProjectManagerDashboard,
  getProjectManagerRisks,
  createProjectManagerRisk,
  generateProjectManagerReport,
  getPortfolioDashboard,
  getPortfolioHealth,
  getPortfolioAnalytics,
  generatePortfolioReport,
  exportPortfolio,
  getOsSummary,
  getOsInstaller,
  getOsSla,
  getOsScheduler,
  getDepartments,
  getDepartmentRuns,
  getDepartmentCollaborations,
  seedDepartmentTemplates,
  createDepartment,
  createDepartmentRun,
  createDepartmentCollaboration,
  getBusinessDashboard,
  getBusinessLeads,
  createBusinessLead,
  getBusinessSupportCases,
  createBusinessSupportCase,
  getBusinessDocuments,
  createBusinessDocument,
  getBusinessProposals,
  createBusinessProposal,
  getBusinessMarketingItems,
  createBusinessMarketingItem,
  getChiefDashboard,
  getChiefPriorities,
  getChiefFollowups,
  createChiefDailyPlan,
  createChiefWeeklyPlan,
  createChiefFollowup,
  updateChiefFollowup,
  getSimulatorDashboard,
  getSimulatorScenarios,
  getSimulatorResults,
  createSimulatorScenario,
  runSimulatorScenario,
  getMultimodalDashboard,
  getMultimodalItems,
  getMultimodalAnalyses,
  createMultimodalItem,
  analyzeMultimodalItem,
  getIndustryModesDashboard,
  getIndustryModes,
  getIndustryModeRuns,
  seedIndustryModes,
  runIndustryMode,
  getAgentNetworkDashboard,
  getAgentNetworkContracts,
  getAgentNetworkAudit,
  createAgentNetworkContract,
  createAgentNetworkHandoff,
  verifyAgentNetworkHandoff,
  getSelfHealingDashboard,
  getSelfHealingChecks,
  getSelfHealingFindings,
  createSelfHealingCheck,
  createSelfHealingRepairTask,
  verifySelfHealingRepair,
  getCompanyBrainDashboard,
  getCompanyBrainDecisions,
  getCompanyBrainReports,
  createCompanyBrainStrategy,
  createCompanyBrainDecision,
  createCompanyBrainReport,
  getDeviceOperatorDashboard,
  getDeviceOperatorSessions,
  getDeviceOperatorAudit,
  createDeviceOperatorSession,
  planDeviceOperatorSession,
  confirmDeviceOperatorAction,
  getTrainingLabDashboard,
  getTrainingDatasets,
  getTrainingDataset,
  createTrainingDataset,
  addTrainingExample,
  updateTrainingExample,
  exportTrainingDataset,
  createTrainingRun,
  getAvatarDashboard,
  getAvatarPersona,
  updateAvatarPersona,
  getAvatarVoiceSettings,
  updateAvatarVoiceSettings,
  getAvatarMeetingSessions,
  createAvatarMeetingSession,
  createAvatarConsent,
  generateAvatarImage,
  getLifeOsDashboard,
  getLifeSchedule,
  getLifeTasks,
  getLifeReminders,
  getLifeDeadlines,
  createLifeScheduleItem,
  createLifeTask,
  updateLifeTask,
  createLifeReminder,
  createLifeDeadline,
  createLifeDailyPlan,
  getUniversalOperatorDashboard,
  getUniversalOperatorSessions,
  getUniversalOperatorWorkflows,
  getUniversalOperatorAudit,
  createUniversalOperatorSession,
  createUniversalOperatorWorkflow,
  planUniversalOperatorWorkflow,
  decideUniversalOperatorAction,
  createUniversalOperatorHandoff,
  getSaasBuilderDashboard,
  getSaasProjects,
  getSaasProject,
  getSaasFeedback,
  createSaasProject,
  validateSaasProject,
  roadmapSaasProject,
  architectureSaasProject,
  launchAssetsSaasProject,
  createSaasFeedback,
  getTeamManagerDashboard,
  getTeamMembers,
  getTeamAssignments,
  getTeamStandups,
  getTeamSprints,
  createTeamMember,
  createTeamAssignment,
  updateTeamAssignment,
  createTeamStandup,
  createTeamSprint,
  reviewTeamSprint,
  getBusinessOperatorDashboard,
  getBusinessOperatorWorkflows,
  getBusinessOperatorReports,
  getBusinessOperatorApprovals,
  getBusinessOperatorAudit,
  createBusinessOperatorWorkflow,
  createBusinessOperatorReport,
  createBusinessOperatorKpiSnapshot,
  createBusinessOperatorApproval,
  updateBusinessOperatorApproval,
  getComplianceIntelDashboard,
  getComplianceIntelPolicies,
  getComplianceScans,
  getComplianceContractReviews,
  getComplianceChecklists,
  createCompliancePolicy,
  runComplianceScan,
  reviewComplianceContract,
  createComplianceChecklist,
  createComplianceAuditPackage,
  getExecutiveBoardDashboard,
  getExecutiveBoardSessions,
  getExecutiveBoardReports,
  createExecutiveBoardSession,
  reviewExecutiveBoardSession,
  voteExecutiveBoardSession,
  reportExecutiveBoardSession,
  getInnovationDashboard,
  getInnovationResearch,
  getInnovationCompetitors,
  getInnovationTrends,
  getInnovationIdeas,
  createInnovationResearch,
  createInnovationCompetitor,
  createInnovationTrend,
  createInnovationIdea,
  createInnovationExperiment,
  createInnovationPrototype,
  createInnovationReport,
  getSimWorldDashboard,
  getSimWorldScenarios,
  getSimWorldPersonas,
  createSimWorldWorld,
  createSimWorldPersona,
  createSimWorldScenario,
  runSimWorldScenario,
  compareSimWorldScenarios,
  createSimWorldReport,
  getOrgOsDashboard,
  getOrgOsOrganizations,
  getOrgOsMembers,
  getOrgOsRoles,
  getOrgOsActivity,
  createOrgOsOrganization,
  createOrgOsMember,
  updateOrgOsMember,
  createOrgOsRole,
  createOrgOsWorkspaceLink,
  getCompanionDashboard,
  getCompanionDevices,
  getCompanionSettings,
  getCompanionReadinessChecks,
  createCompanionDevice,
  updateCompanionSettings,
  createCompanionReadinessCheck,
  createCompanionSession,
  getOperatingLayerDashboard,
  getOperatingLayerRecommendations,
  createOperatingLayerSnapshot,
  createOperatingLayerRecommendations,
  createOperatingLayerReport,
  getMcpSummary,
  getMcpConnectors,
  getMcpTemplates,
  getMcpEvents,
  createMcpConnector,
  enableMcpConnector,
  disableMcpConnector,
  checkMcpConnector,
  planMcpConnectorAction,
  getMcpExecutionSummary,
  getMcpAdapterStatus,
  getMcpInbox,
  getMcpInboxSummary,
  approveMcpInboxItem,
  rejectMcpInboxItem,
  getMcpPolicies,
  getMcpPolicySummary,
  createMcpPolicy,
  updateMcpPolicy,
  getMcpAudit,
  getMcpAuditSummary,
  replayMcpRequest,
  getMcpSecrets,
  getMcpSecretsSummary,
  registerMcpSecret,
  rotateMcpSecret,
  getApprovalsCenter,
  getApprovalsCenterSummary,
  approveCenterItem,
  rejectCenterItem,
  getHealthMonitorDashboard,
  createHealthSnapshot,
  getUsageLedgerSummary,
  recordUsageEntry,
  setUsageBudget,
  getRetrievalSummary,
  indexRetrievalDocument,
  queryRetrieval,
  getEvalSummary,
  getEvalSuites,
  createEvalSuite,
  runEvalSuite,
  getPlaybooksSummary,
  getPlaybooks,
  createPlaybook,
  runPlaybook,
  getOperatingLayerV2Dashboard,
  createOperatingLayerV2Snapshot,
  createOperatingLayerV2Report,
  getNotificationsSummary,
  getNotifications,
  generateNotifications,
  acknowledgeNotification,
  suggestMcp,
  routeMasterAgent,
  getGitStatus,
  discoverGitRepos,
  getGitRepositories,
  getGitLog,
  getGitBranchList,
  getStudioTemplates,
  listAgentProfiles,
  createAgentProfile,
  testAgentProfile,
  evaluateAgentProfile,
  publishAgentProfile,
  duplicateAgentProfile,
  getAgentPreview,
  getVoiceStatus,
  getVoiceSettings,
  updateVoiceSettings,
  logVoiceActivity,
  getVoiceEvents,
  clearVoiceEvents,
  getWorkflowTemplates,
  listWorkflowRuns,
  startWorkflowRun,
  approveWorkflowStep,
  pauseWorkflowRun,
  resumeWorkflowRun,
  cancelWorkflowRun,
  getWorkflowEffects,
  getMarketplaceListings,
  installMarketplaceListing,
  unpublishMarketplaceListing,
  getDesignAgentStatus,
  analyzeDesign,
  getRepoFinderStatus,
  searchRepos,
  getWorkspaceTemplates,
  getWorkspaceTemplatesSummary,
  createWorkspaceTemplate,
  instantiateWorkspaceTemplate,
  getScheduledTasks,
  getScheduledTasksSummary,
  createScheduledTask,
  toggleScheduledTask,
  triggerScheduledTask,
  getDataExportSummary,
  getOs2Dashboard,
  getMasterAgentSummary,
  getMasterAgentCapabilities,
  sendMasterRouteFeedback,
  globalSearch,
  getGlobalSearchSources,
  getActivityTimeline,
  exportActivityTimeline,
  getDashboardHome,
  getFeatures,
  tryFeature,
  getDemoSummary,
  getDemoScript,
  getDemoCaseStudy,
  seedDemoData,
  resetDemoData,
  getSettings,
  updateSettings,
  resetSettings,
  getProviderControl,
  updateProviderControl,
  generateNotificationsInbox,
  getNotificationsInbox,
  resolveNotificationInbox,
  getWorkspaceOsDashboard,
  planContext,
  getAgentQuality,
  recommendWorkflow,
  getProductivityBrain,
  docContractRisk,
  docAtsScore,
  analyzeCode,
  researchAgentClaims,
  researchAgentBias,
  researchAgentBrief,
  getBusinessIntelDashboard,
  getBusinessIntelReport,
  analyzeMeetingTranscript,
  meetingTranscriptToGoal,
  analyzeCollaboration,
  getPermissionProfiles,
  createPermissionProfile,
  deletePermissionProfile,
  evaluatePermission,
  getGovernanceConsoleDashboard,
  getGovernanceConsoleReport,
  getDataManagerBrowse,
  getDataManagerUsage,
  getDataManagerCleanup,
  previewDataRedaction,
  previewImport,
  commitImport,
  getImportRecords,
  exportCenterExport,
  exportCenterPackage,
  getExportCenterCaseStudy,
  getPluginMarketplaceCatalog,
  registerMarketplacePlugin,
  toggleMarketplacePlugin,
  testMarketplacePlugin,
  getPluginMarketplaceActivity,
  getIntegrationHubCards,
  dryRunIntegration,
  getQaCenterDashboard,
  getQaCenterMatrix,
  recordQaStatus,
  getReleaseManagerDashboard,
  getReleaseManagerChangelog,
  generatePrSummary,
  generateReleaseNotes,
  getLaunchConsoleDashboard,
  getLaunchConsoleReport,
  createOs2Snapshot,
  createOs2Report,
  exportDataBundle,
  importDataBundle,
  getMcpExecutions,
  requestMcpExecution,
  approveMcpExecution,
  rejectMcpExecution,
  runMcpExecution,
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
  getSlackStatus,
  getSlackNotifications,
  sendSlackTest,
  getNotionStatus,
  getNotionExports,
  sendNotionExport,
  getAutopilotSettings,
  updateAutopilotSettings,
  getAutopilotRuns,
  getAutopilotCheckpoints,
  decideAutopilotCheckpoint,
  getCodexJobs,
  getDebateSummary,
  runCodexForLinearIssue,
  installAgentMarketplacePack,
  rateAgentMarketplaceTeam,
  exportAgentMarketplaceTeam,
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
  scanCompliancePii,
  selectLinearIssue,
  sendFeedback,
  syncLinearIssue,
  updateWorkspace,
  updateDigitalTwinProfile,
  exportDigitalTwinProfile,
  resetDigitalTwinProfile,
  deleteDigitalTwinProfile,
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
  const [devSection, setDevSection] = useState('agent')
  const [cmdkOpen, setCmdkOpen] = useState(false)
  const [showGitIntel, setShowGitIntel] = useState(false)
  const [gitStatus, setGitStatus] = useState(null)
  const [gitRepos, setGitRepos] = useState([])
  const [gitPath, setGitPath] = useState('')
  const [gitBusy, setGitBusy] = useState(false)
  const [gitLog, setGitLog] = useState(null)
  const [gitBranches, setGitBranches] = useState(null)
  const [gitReadBusy, setGitReadBusy] = useState(false)
  const [showAgentStudio, setShowAgentStudio] = useState(false)
  const [studioTemplates, setStudioTemplates] = useState([])
  const [agentProfiles, setAgentProfiles] = useState([])
  const [agentName, setAgentName] = useState('')
  const [agentRole, setAgentRole] = useState('')
  const [agentTone, setAgentTone] = useState('professional')
  const [agentTestPrompt, setAgentTestPrompt] = useState('')
  const [agentTestResult, setAgentTestResult] = useState(null)
  const [agentBusy, setAgentBusy] = useState(false)
  const [showVoiceConsole, setShowVoiceConsole] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState(null)
  const [voiceSettings, setVoiceSettings] = useState(null)
  const [availableVoices, setAvailableVoices] = useState([])
  const [voiceEvents, setVoiceEvents] = useState([])
  const [showWorkflows, setShowWorkflows] = useState(false)
  const [workflowTemplates, setWorkflowTemplates] = useState([])
  const [workflowRuns, setWorkflowRuns] = useState([])
  const [workflowEffects, setWorkflowEffects] = useState([])
  const [durableBusy, setDurableBusy] = useState(false)
  const [showMarketplaceHub, setShowMarketplaceHub] = useState(false)
  const [marketplaceListings, setMarketplaceListings] = useState([])
  const [marketplaceKind, setMarketplaceKind] = useState('')
  const [marketplaceBusy, setMarketplaceBusy] = useState(false)
  const [marketplaceNote, setMarketplaceNote] = useState('')
  const [showDesignAgent, setShowDesignAgent] = useState(false)
  const [designStatus, setDesignStatus] = useState(null)
  const [designImage, setDesignImage] = useState(null)
  const [designImageName, setDesignImageName] = useState('')
  const [designLenses, setDesignLenses] = useState(['visual', 'ux', 'market'])
  const [designContext, setDesignContext] = useState('')
  const [designLive, setDesignLive] = useState(false)
  const [designResult, setDesignResult] = useState(null)
  const [designBusy, setDesignBusy] = useState(false)
  const [showRepoFinder, setShowRepoFinder] = useState(false)
  const [repoQuery, setRepoQuery] = useState('')
  const [repoResult, setRepoResult] = useState(null)
  const [repoBusy, setRepoBusy] = useState(false)
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
  const [showCompliancePanel, setShowCompliancePanel] = useState(false)
  const [complianceSummary, setComplianceSummary] = useState(null)
  const [complianceAudit, setComplianceAudit] = useState([])
  const [complianceRetention, setComplianceRetention] = useState(null)
  const [piiScanText, setPiiScanText] = useState('person@example.com called 555-123-4567')
  const [piiScanResult, setPiiScanResult] = useState(null)
  const [complianceBusy, setComplianceBusy] = useState(false)
  const [complianceError, setComplianceError] = useState('')
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
  // Voice Ask Console (v-voice): speak answers aloud + task-aware MCP suggestions.
  const [voiceOutputEnabled, setVoiceOutputEnabled] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [mcpSuggestions, setMcpSuggestions] = useState([])
  const [askSources, setAskSources] = useState([])
  const [askFollowups, setAskFollowups] = useState([])
  const [heroInput, setHeroInput] = useState('')
  const [cliBusy, setCliBusy] = useState(false)
  // Master Agent (single top-level AI over all of v1–v60).
  const [masterText, setMasterText] = useState('')
  const [masterResult, setMasterResult] = useState(null)
  const [masterBusy, setMasterBusy] = useState(false)
  const [automationResults, setAutomationResults] = useState({})
  const [goals, setGoals] = useState([])
  const [selectedGoal, setSelectedGoal] = useState(null)
  const [customAgents, setCustomAgents] = useState([])
  const [agentTemplates, setAgentTemplates] = useState([])
  const [agentMarketplaceDashboard, setAgentMarketplaceDashboard] = useState(null)
  const [agentMarketplacePacks, setAgentMarketplacePacks] = useState([])
  const [agentMarketplaceTeams, setAgentMarketplaceTeams] = useState([])
  const [agentMarketplaceBusyId, setAgentMarketplaceBusyId] = useState('')
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
  const [showEvaluationLab, setShowEvaluationLab] = useState(false)
  const [evaluationDashboard, setEvaluationDashboard] = useState(null)
  const [evaluationBenchmarks, setEvaluationBenchmarks] = useState([])
  const [evaluationBusy, setEvaluationBusy] = useState(false)
  const [evaluationError, setEvaluationError] = useState('')
  const [abVariantA, setAbVariantA] = useState('openai')
  const [abVariantB, setAbVariantB] = useState('mock')
  const [showProjectManager, setShowProjectManager] = useState(false)
  const [projectManagerDashboard, setProjectManagerDashboard] = useState(null)
  const [projectManagerRisks, setProjectManagerRisks] = useState([])
  const [projectManagerBusy, setProjectManagerBusy] = useState(false)
  const [projectManagerError, setProjectManagerError] = useState('')
  const [newRiskTitle, setNewRiskTitle] = useState('')
  const [newRiskSeverity, setNewRiskSeverity] = useState('medium')
  const [showPortfolio, setShowPortfolio] = useState(false)
  const [portfolioDashboard, setPortfolioDashboard] = useState(null)
  const [portfolioHealth, setPortfolioHealth] = useState(null)
  const [portfolioAnalytics, setPortfolioAnalytics] = useState(null)
  const [portfolioBusy, setPortfolioBusy] = useState(false)
  const [portfolioError, setPortfolioError] = useState('')
  const [showOsPanel, setShowOsPanel] = useState(false)
  const [osSummary, setOsSummary] = useState(null)
  const [osInstaller, setOsInstaller] = useState(null)
  const [osSla, setOsSla] = useState(null)
  const [osScheduler, setOsScheduler] = useState(null)
  const [showOrgPanel, setShowOrgPanel] = useState(false)
  const [departments, setDepartments] = useState([])
  const [departmentOverview, setDepartmentOverview] = useState(null)
  const [departmentRuns, setDepartmentRuns] = useState([])
  const [departmentCollaborations, setDepartmentCollaborations] = useState([])
  const [orgBusy, setOrgBusy] = useState(false)
  const [orgError, setOrgError] = useState(null)
  const [newDepartmentName, setNewDepartmentName] = useState('')
  const [newDepartmentPermission, setNewDepartmentPermission] = useState('read_only')
  const [runDepartmentId, setRunDepartmentId] = useState('')
  const [runDepartmentTask, setRunDepartmentTask] = useState('')
  const [collabGoal, setCollabGoal] = useState('')
  const [collabDepartments, setCollabDepartments] = useState('')
  const [showBusinessPanel, setShowBusinessPanel] = useState(false)
  const [businessDashboard, setBusinessDashboard] = useState(null)
  const [businessLeads, setBusinessLeads] = useState([])
  const [businessSupportCases, setBusinessSupportCases] = useState([])
  const [businessDocuments, setBusinessDocuments] = useState([])
  const [businessProposals, setBusinessProposals] = useState([])
  const [businessMarketingItems, setBusinessMarketingItems] = useState([])
  const [businessBusy, setBusinessBusy] = useState(false)
  const [businessError, setBusinessError] = useState(null)
  const [leadName, setLeadName] = useState('')
  const [leadCompany, setLeadCompany] = useState('')
  const [caseSubject, setCaseSubject] = useState('')
  const [casePriority, setCasePriority] = useState('medium')
  const [docTitle, setDocTitle] = useState('')
  const [docContent, setDocContent] = useState('')
  const [proposalTitle, setProposalTitle] = useState('')
  const [proposalClient, setProposalClient] = useState('')
  const [marketingTitle, setMarketingTitle] = useState('')
  const [marketingChannel, setMarketingChannel] = useState('email')
  const [showChiefPanel, setShowChiefPanel] = useState(false)
  const [chiefDashboard, setChiefDashboard] = useState(null)
  const [chiefPriorities, setChiefPriorities] = useState([])
  const [chiefFollowups, setChiefFollowups] = useState([])
  const [chiefOverdueCount, setChiefOverdueCount] = useState(0)
  const [chiefBusy, setChiefBusy] = useState(false)
  const [chiefError, setChiefError] = useState(null)
  const [followupTitle, setFollowupTitle] = useState('')
  const [followupDueDate, setFollowupDueDate] = useState('')
  const [followupPriority, setFollowupPriority] = useState('medium')
  const [showSimulatorPanel, setShowSimulatorPanel] = useState(false)
  const [simulatorDashboard, setSimulatorDashboard] = useState(null)
  const [simulatorScenarios, setSimulatorScenarios] = useState([])
  const [simulatorResults, setSimulatorResults] = useState([])
  const [simulatorBusy, setSimulatorBusy] = useState(false)
  const [simulatorError, setSimulatorError] = useState(null)
  const [scenarioTitle, setScenarioTitle] = useState('')
  const [scenarioType, setScenarioType] = useState('decision')
  const [scenarioAssumptions, setScenarioAssumptions] = useState('')
  const [scenarioOptions, setScenarioOptions] = useState('')
  const [latestSimResult, setLatestSimResult] = useState(null)
  const [showMultimodalPanel, setShowMultimodalPanel] = useState(false)
  const [multimodalDashboard, setMultimodalDashboard] = useState(null)
  const [multimodalItems, setMultimodalItems] = useState([])
  const [multimodalBusy, setMultimodalBusy] = useState(false)
  const [multimodalError, setMultimodalError] = useState(null)
  const [mmTitle, setMmTitle] = useState('')
  const [mmType, setMmType] = useState('screenshot')
  const [mmDescription, setMmDescription] = useState('')
  const [latestMmAnalysis, setLatestMmAnalysis] = useState(null)
  const [showIndustryPanel, setShowIndustryPanel] = useState(false)
  const [industryDashboard, setIndustryDashboard] = useState(null)
  const [industryModes, setIndustryModes] = useState([])
  const [industryRuns, setIndustryRuns] = useState([])
  const [industryBusy, setIndustryBusy] = useState(false)
  const [industryError, setIndustryError] = useState(null)
  const [industryRunModeId, setIndustryRunModeId] = useState('')
  const [industryPrompt, setIndustryPrompt] = useState('')
  const [showAgentNetworkPanel, setShowAgentNetworkPanel] = useState(false)
  const [agentNetworkDashboard, setAgentNetworkDashboard] = useState(null)
  const [agentNetworkContracts, setAgentNetworkContracts] = useState([])
  const [agentNetworkAudit, setAgentNetworkAudit] = useState([])
  const [agentNetworkBusy, setAgentNetworkBusy] = useState(false)
  const [agentNetworkError, setAgentNetworkError] = useState(null)
  const [contractTarget, setContractTarget] = useState('')
  const [contractTask, setContractTask] = useState('')
  const [contractExpected, setContractExpected] = useState('')
  const [latestHandoff, setLatestHandoff] = useState(null)
  const [showHealingPanel, setShowHealingPanel] = useState(false)
  const [healingDashboard, setHealingDashboard] = useState(null)
  const [healingFindings, setHealingFindings] = useState([])
  const [healingRepairs, setHealingRepairs] = useState([])
  const [healingBusy, setHealingBusy] = useState(false)
  const [healingError, setHealingError] = useState(null)
  const [healingCommand, setHealingCommand] = useState('pytest')
  const [showCompanyBrainPanel, setShowCompanyBrainPanel] = useState(false)
  const [companyBrainDashboard, setCompanyBrainDashboard] = useState(null)
  const [companyBrainDecisions, setCompanyBrainDecisions] = useState([])
  const [companyBrainReport, setCompanyBrainReport] = useState(null)
  const [companyBrainBusy, setCompanyBrainBusy] = useState(false)
  const [companyBrainError, setCompanyBrainError] = useState(null)
  const [strategyTitle, setStrategyTitle] = useState('')
  const [decisionTitle, setDecisionTitle] = useState('')
  const [decisionImpact, setDecisionImpact] = useState('medium')
  const [showDevicePanel, setShowDevicePanel] = useState(false)
  const [deviceDashboard, setDeviceDashboard] = useState(null)
  const [deviceSessions, setDeviceSessions] = useState([])
  const [deviceAudit, setDeviceAudit] = useState([])
  const [deviceBusy, setDeviceBusy] = useState(false)
  const [deviceError, setDeviceError] = useState(null)
  const [devicePermission, setDevicePermission] = useState('tap_type_with_confirmation')
  const [deviceSessionId, setDeviceSessionId] = useState('')
  const [deviceCommand, setDeviceCommand] = useState('')
  const [deviceScreenText, setDeviceScreenText] = useState('')
  const [devicePlannedActions, setDevicePlannedActions] = useState([])
  const [showTrainingPanel, setShowTrainingPanel] = useState(false)
  const [trainingDashboard, setTrainingDashboard] = useState(null)
  const [trainingDatasets, setTrainingDatasets] = useState([])
  const [trainingDatasetId, setTrainingDatasetId] = useState('')
  const [trainingExamples, setTrainingExamples] = useState([])
  const [trainingExport, setTrainingExport] = useState(null)
  const [trainingBusy, setTrainingBusy] = useState(false)
  const [trainingError, setTrainingError] = useState(null)
  const [datasetName, setDatasetName] = useState('')
  const [examplePrompt, setExamplePrompt] = useState('')
  const [exampleCompletion, setExampleCompletion] = useState('')
  const [showAvatarPanel, setShowAvatarPanel] = useState(false)
  const [avatarDashboard, setAvatarDashboard] = useState(null)
  const [avatarMeetings, setAvatarMeetings] = useState([])
  const [avatarBusy, setAvatarBusy] = useState(false)
  const [avatarError, setAvatarError] = useState(null)
  const [avatarName, setAvatarName] = useState('')
  const [avatarTone, setAvatarTone] = useState('friendly')
  const [avatarVoiceMode, setAvatarVoiceMode] = useState('text_only')
  const [meetingTitle, setMeetingTitle] = useState('')
  const [avatarDescription, setAvatarDescription] = useState('')
  const [avatarStyle, setAvatarStyle] = useState('illustrated')
  const [showLifePanel, setShowLifePanel] = useState(false)
  const [lifeDashboard, setLifeDashboard] = useState(null)
  const [lifeTasks, setLifeTasks] = useState([])
  const [lifeReminders, setLifeReminders] = useState([])
  const [lifeDeadlines, setLifeDeadlines] = useState([])
  const [lifeBusy, setLifeBusy] = useState(false)
  const [lifeError, setLifeError] = useState(null)
  const [lifeTaskTitle, setLifeTaskTitle] = useState('')
  const [lifeTaskPriority, setLifeTaskPriority] = useState('medium')
  const [lifeTaskDue, setLifeTaskDue] = useState('')
  const [lifeScheduleTitle, setLifeScheduleTitle] = useState('')
  const [lifeScheduleDate, setLifeScheduleDate] = useState('')
  const [lifeReminderTitle, setLifeReminderTitle] = useState('')
  const [lifeReminderOn, setLifeReminderOn] = useState('')
  const [lifeDeadlineTitle, setLifeDeadlineTitle] = useState('')
  const [lifeDeadlineKind, setLifeDeadlineKind] = useState('school')
  const [lifeDeadlineDue, setLifeDeadlineDue] = useState('')
  const [lifeDailyPlan, setLifeDailyPlan] = useState(null)
  const [showUniversalPanel, setShowUniversalPanel] = useState(false)
  const [universalDashboard, setUniversalDashboard] = useState(null)
  const [universalSessions, setUniversalSessions] = useState([])
  const [universalWorkflows, setUniversalWorkflows] = useState([])
  const [universalAudit, setUniversalAudit] = useState([])
  const [universalBusy, setUniversalBusy] = useState(false)
  const [universalError, setUniversalError] = useState(null)
  const [universalSurface, setUniversalSurface] = useState('cross_app')
  const [universalGoal, setUniversalGoal] = useState('')
  const [universalSteps, setUniversalSteps] = useState('')
  const [universalPlannedActions, setUniversalPlannedActions] = useState([])
  const [showSaasPanel, setShowSaasPanel] = useState(false)
  const [saasDashboard, setSaasDashboard] = useState(null)
  const [saasProjects, setSaasProjects] = useState([])
  const [saasProjectId, setSaasProjectId] = useState('')
  const [saasArtifact, setSaasArtifact] = useState(null)
  const [saasFeedback, setSaasFeedback] = useState([])
  const [saasBusy, setSaasBusy] = useState(false)
  const [saasError, setSaasError] = useState(null)
  const [saasName, setSaasName] = useState('')
  const [saasIdea, setSaasIdea] = useState('')
  const [saasFeedbackTitle, setSaasFeedbackTitle] = useState('')
  const [saasFeedbackType, setSaasFeedbackType] = useState('feature')
  const [showTeamPanel, setShowTeamPanel] = useState(false)
  const [teamDashboard, setTeamDashboard] = useState(null)
  const [teamMembers, setTeamMembers] = useState([])
  const [teamAssignments, setTeamAssignments] = useState([])
  const [teamStandup, setTeamStandup] = useState(null)
  const [teamSprints, setTeamSprints] = useState([])
  const [teamBusy, setTeamBusy] = useState(false)
  const [teamError, setTeamError] = useState(null)
  const [memberName, setMemberName] = useState('')
  const [memberType, setMemberType] = useState('human')
  const [assignmentTitle, setAssignmentTitle] = useState('')
  const [assignmentOwner, setAssignmentOwner] = useState('')
  const [assignmentPriority, setAssignmentPriority] = useState('medium')
  const [sprintName, setSprintName] = useState('')
  const [showBizOpsPanel, setShowBizOpsPanel] = useState(false)
  const [bizOpsDashboard, setBizOpsDashboard] = useState(null)
  const [bizOpsWorkflows, setBizOpsWorkflows] = useState([])
  const [bizOpsApprovals, setBizOpsApprovals] = useState([])
  const [bizOpsBusy, setBizOpsBusy] = useState(false)
  const [bizOpsError, setBizOpsError] = useState(null)
  const [bizOpsWorkflowType, setBizOpsWorkflowType] = useState('lead_pipeline')
  const [bizOpsApprovalTitle, setBizOpsApprovalTitle] = useState('')
  const [bizOpsApprovalKind, setBizOpsApprovalKind] = useState('external_send')
  const [showComplianceIntelPanel, setShowComplianceIntelPanel] = useState(false)
  const [complianceIntelDashboard, setComplianceIntelDashboard] = useState(null)
  const [complianceScans, setComplianceScans] = useState([])
  const [compIntelBusy, setCompIntelBusy] = useState(false)
  const [complianceIntelError, setComplianceIntelError] = useState(null)
  const [scanContent, setScanContent] = useState('')
  const [contractContent, setContractContent] = useState('')
  const [complianceArtifact, setComplianceArtifact] = useState(null)
  const [checklistFramework, setChecklistFramework] = useState('hipaa')
  const [showBoardPanel, setShowBoardPanel] = useState(false)
  const [boardDashboard, setBoardDashboard] = useState(null)
  const [boardSessions, setBoardSessions] = useState([])
  const [boardSessionId, setBoardSessionId] = useState('')
  const [boardArtifact, setBoardArtifact] = useState(null)
  const [boardBusy, setBoardBusy] = useState(false)
  const [boardError, setBoardError] = useState(null)
  const [boardDecision, setBoardDecision] = useState('')
  const [boardVoteRole, setBoardVoteRole] = useState('CEO')
  const [boardVoteValue, setBoardVoteValue] = useState('approve')
  const [showInnovationPanel, setShowInnovationPanel] = useState(false)
  const [innovationDashboard, setInnovationDashboard] = useState(null)
  const [innovationResearch, setInnovationResearch] = useState([])
  const [innovationIdeas, setInnovationIdeas] = useState([])
  const [innovationBusy, setInnovationBusy] = useState(false)
  const [innovationError, setInnovationError] = useState(null)
  const [researchTitle, setResearchTitle] = useState('')
  const [ideaTitle, setIdeaTitle] = useState('')
  const [ideaImpact, setIdeaImpact] = useState(3)
  const [showSimWorldPanel, setShowSimWorldPanel] = useState(false)
  const [simWorldDashboard, setSimWorldDashboard] = useState(null)
  const [simWorldScenarios, setSimWorldScenarios] = useState([])
  const [simWorldBusy, setSimWorldBusy] = useState(false)
  const [simWorldError, setSimWorldError] = useState(null)
  const [simWorldName, setSimWorldName] = useState('')
  const [simScenarioTitle, setSimScenarioTitle] = useState('')
  const [simScenarioType, setSimScenarioType] = useState('business')
  const [simWorldOutcome, setSimWorldOutcome] = useState(null)
  const [showOrgOsPanel, setShowOrgOsPanel] = useState(false)
  const [orgOsDashboard, setOrgOsDashboard] = useState(null)
  const [orgOsOrganizations, setOrgOsOrganizations] = useState([])
  const [orgOsMembers, setOrgOsMembers] = useState([])
  const [orgOsBusy, setOrgOsBusy] = useState(false)
  const [orgOsError, setOrgOsError] = useState(null)
  const [orgName, setOrgName] = useState('')
  const [orgMemberName, setOrgMemberName] = useState('')
  const [orgMemberRole, setOrgMemberRole] = useState('contributor')
  const [showCompanionPanel, setShowCompanionPanel] = useState(false)
  const [companionDashboard, setCompanionDashboard] = useState(null)
  const [companionDevices, setCompanionDevices] = useState([])
  const [companionBusy, setCompanionBusy] = useState(false)
  const [companionError, setCompanionError] = useState(null)
  const [companionDeviceName, setCompanionDeviceName] = useState('')
  const [companionMode, setCompanionMode] = useState('disabled')
  const [companionReadiness, setCompanionReadiness] = useState(null)
  const [showOperatingLayerPanel, setShowOperatingLayerPanel] = useState(false)
  const [operatingLayerDashboard, setOperatingLayerDashboard] = useState(null)
  const [operatingLayerArtifact, setOperatingLayerArtifact] = useState(null)
  const [operatingLayerBusy, setOperatingLayerBusy] = useState(false)
  const [operatingLayerError, setOperatingLayerError] = useState(null)
  const [showMcpPanel, setShowMcpPanel] = useState(false)
  const [mcpSummary, setMcpSummary] = useState(null)
  const [mcpConnectors, setMcpConnectors] = useState([])
  const [mcpTemplates, setMcpTemplates] = useState([])
  const [mcpBusy, setMcpBusy] = useState(false)
  const [mcpError, setMcpError] = useState(null)
  const [mcpTemplateSlug, setMcpTemplateSlug] = useState('github')
  const [mcpSelectedId, setMcpSelectedId] = useState('')
  const [mcpActionName, setMcpActionName] = useState('')
  const [mcpCheckResult, setMcpCheckResult] = useState(null)
  const [mcpPlanResult, setMcpPlanResult] = useState(null)
  const [mcpExecSummary, setMcpExecSummary] = useState(null)
  const [mcpAdapterStatus, setMcpAdapterStatus] = useState(null)
  const [mcpInbox, setMcpInbox] = useState([])
  const [mcpInboxSummary, setMcpInboxSummary] = useState(null)
  const [mcpPolicies, setMcpPolicies] = useState([])
  const [mcpPolicyName, setMcpPolicyName] = useState('')
  const [mcpPolicySlug, setMcpPolicySlug] = useState('*')
  const [mcpPolicyAction, setMcpPolicyAction] = useState('*')
  const [mcpTab, setMcpTab] = useState('connectors')
  const [mcpAudit, setMcpAudit] = useState([])
  const [mcpAuditSummary, setMcpAuditSummary] = useState(null)
  const [mcpReplayId, setMcpReplayId] = useState('')
  const [mcpReplayResult, setMcpReplayResult] = useState(null)
  const [mcpSecrets, setMcpSecrets] = useState([])
  const [mcpSecretsSummary, setMcpSecretsSummary] = useState(null)
  const [mcpSecretKey, setMcpSecretKey] = useState('')
  const [showApprovalsCenter, setShowApprovalsCenter] = useState(false)
  const [approvalsCenter, setApprovalsCenter] = useState([])
  const [approvalsCenterSummary, setApprovalsCenterSummary] = useState(null)
  const [acBusy, setAcBusy] = useState(false)
  const [acError, setAcError] = useState(null)
  const [showHealthMonitor, setShowHealthMonitor] = useState(false)
  const [healthDashboard, setHealthDashboard] = useState(null)
  const [healthBusy, setHealthBusy] = useState(false)
  const [showUsageLedger, setShowUsageLedger] = useState(false)
  const [usageSummary, setUsageSummary] = useState(null)
  const [usageBusy, setUsageBusy] = useState(false)
  const [usageBudgetInput, setUsageBudgetInput] = useState('')
  const [showRetrieval, setShowRetrieval] = useState(false)
  const [retrievalSummary, setRetrievalSummary] = useState(null)
  const [retrievalBusy, setRetrievalBusy] = useState(false)
  const [retrievalDocText, setRetrievalDocText] = useState('')
  const [retrievalQuery, setRetrievalQuery] = useState('')
  const [retrievalResults, setRetrievalResults] = useState([])
  const [showEvalHarness, setShowEvalHarness] = useState(false)
  const [evalSummary, setEvalSummary] = useState(null)
  const [evalSuites, setEvalSuites] = useState([])
  const [evalBusy, setEvalBusy] = useState(false)
  const [evalRun, setEvalRun] = useState(null)
  const [showPlaybooks, setShowPlaybooks] = useState(false)
  const [playbooksSummary, setPlaybooksSummary] = useState(null)
  const [playbooks, setPlaybooks] = useState([])
  const [playbookBusy, setPlaybookBusy] = useState(false)
  const [playbookRun, setPlaybookRun] = useState(null)
  const [showOpLayer2, setShowOpLayer2] = useState(false)
  const [opLayer2, setOpLayer2] = useState(null)
  const [opLayer2Busy, setOpLayer2Busy] = useState(false)
  const [opLayer2Report, setOpLayer2Report] = useState(null)
  const [showNotifications, setShowNotifications] = useState(false)
  const [notificationsSummary, setNotificationsSummary] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [notifBusy, setNotifBusy] = useState(false)
  const [showWsTemplates, setShowWsTemplates] = useState(false)
  const [wsTemplates, setWsTemplates] = useState([])
  const [wsTemplatesSummary, setWsTemplatesSummary] = useState(null)
  const [wsTemplateBusy, setWsTemplateBusy] = useState(false)
  const [wsTemplateName, setWsTemplateName] = useState('')
  const [showScheduled, setShowScheduled] = useState(false)
  const [scheduledTasks, setScheduledTasks] = useState([])
  const [scheduledSummary, setScheduledSummary] = useState(null)
  const [scheduledBusy, setScheduledBusy] = useState(false)
  const [scheduledName, setScheduledName] = useState('')
  const [scheduledSchedule, setScheduledSchedule] = useState('daily')
  const [showDataExport, setShowDataExport] = useState(false)
  const [dataExportSummary, setDataExportSummary] = useState(null)
  const [dataExportBusy, setDataExportBusy] = useState(false)
  const [showOs2, setShowOs2] = useState(false)
  const [os2Dashboard, setOs2Dashboard] = useState(null)
  const [os2Report, setOs2Report] = useState(null)
  const [os2Busy, setOs2Busy] = useState(false)
  const [showMasterPanel, setShowMasterPanel] = useState(false)
  const [masterSummary, setMasterSummary] = useState(null)
  const [masterCapabilities, setMasterCapabilities] = useState(null)
  const [showGlobalSearch, setShowGlobalSearch] = useState(false)
  const [globalSearchQuery, setGlobalSearchQuery] = useState('')
  const [globalSearchResults, setGlobalSearchResults] = useState(null)
  const [globalSearchSources, setGlobalSearchSources] = useState(null)
  const [globalSearchBusy, setGlobalSearchBusy] = useState(false)
  const [showActivity, setShowActivity] = useState(false)
  const [activityTimeline, setActivityTimeline] = useState(null)
  const [activityType, setActivityType] = useState('')
  const [activityBusy, setActivityBusy] = useState(false)
  const [showHome, setShowHome] = useState(false)
  const [dashboardHome, setDashboardHome] = useState(null)
  const [showFeatures, setShowFeatures] = useState(false)
  const [featuresData, setFeaturesData] = useState(null)
  const [featuresQuery, setFeaturesQuery] = useState('')
  const [featuresStatus, setFeaturesStatus] = useState('')
  const [showDemo, setShowDemo] = useState(false)
  const [demoSummary, setDemoSummary] = useState(null)
  const [demoScript, setDemoScript] = useState(null)
  const [demoBusy, setDemoBusy] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [settingsData, setSettingsData] = useState(null)
  const [settingsBusy, setSettingsBusy] = useState(false)
  const [showProviders, setShowProviders] = useState(false)
  const [providerControl, setProviderControl] = useState(null)
  const [providerBusy, setProviderBusy] = useState(false)
  const [showInbox, setShowInbox] = useState(false)
  const [inboxData, setInboxData] = useState(null)
  const [inboxBusy, setInboxBusy] = useState(false)
  const [showWsOs, setShowWsOs] = useState(false)
  const [wsOsDashboard, setWsOsDashboard] = useState(null)
  const [showContext, setShowContext] = useState(false)
  const [contextQuery, setContextQuery] = useState('')
  const [contextPlan, setContextPlan] = useState(null)
  const [contextBusy, setContextBusy] = useState(false)
  const [showAgentQuality, setShowAgentQuality] = useState(false)
  const [agentQuality, setAgentQuality] = useState(null)
  const [showWorkflowRec, setShowWorkflowRec] = useState(false)
  const [workflowGoal, setWorkflowGoal] = useState('')
  const [workflowRec, setWorkflowRec] = useState(null)
  const [workflowBusy, setWorkflowBusy] = useState(false)
  const [showProductivity, setShowProductivity] = useState(false)
  const [productivityBrain, setProductivityBrain] = useState(null)
  const [showDocIntel, setShowDocIntel] = useState(false)
  const [docIntelText, setDocIntelText] = useState('')
  const [docIntelResult, setDocIntelResult] = useState(null)
  const [docIntelBusy, setDocIntelBusy] = useState(false)
  const [showCodeIntel, setShowCodeIntel] = useState(false)
  const [codeIntelText, setCodeIntelText] = useState('')
  const [codeIntelResult, setCodeIntelResult] = useState(null)
  const [codeIntelBusy, setCodeIntelBusy] = useState(false)
  const [showResearchAgent2, setShowResearchAgent2] = useState(false)
  const [researchAgentText, setResearchAgentText] = useState('This market is clearly the best opportunity. According to a 2025 report, adoption rose 38%.')
  const [researchAgentResult, setResearchAgentResult] = useState(null)
  const [researchAgentBusy, setResearchAgentBusy] = useState(false)
  const [showBizIntel2, setShowBizIntel2] = useState(false)
  const [bizIntel2, setBizIntel2] = useState(null)
  const [bizIntelBusy, setBizIntelBusy] = useState(false)
  const [showMeetingIntel2, setShowMeetingIntel2] = useState(false)
  const [meetingIntelText, setMeetingIntelText] = useState('Monday 10:00 team decided we will launch the demo next week. Alex will update the backend tests. Priya will prepare the follow-up deck.')
  const [meetingIntelResult, setMeetingIntelResult] = useState(null)
  const [meetingIntelBusy, setMeetingIntelBusy] = useState(false)
  const [showCollab2, setShowCollab2] = useState(false)
  const [collabTopic, setCollabTopic] = useState('Should we automate this workflow now?')
  const [collabRoleA, setCollabRoleA] = useState('Strategy Agent')
  const [collabPositionA, setCollabPositionA] = useState('Automate the read-only planning steps because they reduce repeated manual work.')
  const [collabRoleB, setCollabRoleB] = useState('Risk Agent')
  const [collabPositionB, setCollabPositionB] = useState('Do not automate external sending or destructive actions without approval.')
  const [collabResult, setCollabResult] = useState(null)
  const [collabBusy, setCollabBusy] = useState(false)
  const [showPerm3, setShowPerm3] = useState(false)
  const [permProfiles, setPermProfiles] = useState(null)
  const [permEval, setPermEval] = useState(null)
  const [permBusy, setPermBusy] = useState(false)
  const [permAction, setPermAction] = useState('send_email')
  const [showGovConsole, setShowGovConsole] = useState(false)
  const [govConsole, setGovConsole] = useState(null)
  const [govBusy, setGovBusy] = useState(false)
  const [showDataManager, setShowDataManager] = useState(false)
  const [dataManager, setDataManager] = useState(null)
  const [dataManagerPreview, setDataManagerPreview] = useState(null)
  const [dataManagerBusy, setDataManagerBusy] = useState(false)
  const [dataManagerCollection, setDataManagerCollection] = useState('chat_sessions.json')
  const [showImportCenter, setShowImportCenter] = useState(false)
  const [importCenterKind, setImportCenterKind] = useState('markdown')
  const [importCenterContent, setImportCenterContent] = useState('# Project note\nImportant follow-up item.')
  const [importCenterResult, setImportCenterResult] = useState(null)
  const [importCenterRecords, setImportCenterRecords] = useState(null)
  const [importCenterBusy, setImportCenterBusy] = useState(false)
  const [showExportCenter2, setShowExportCenter2] = useState(false)
  const [exportCenterKind, setExportCenterKind] = useState('chats')
  const [exportCenterFormat, setExportCenterFormat] = useState('markdown')
  const [exportCenterResult, setExportCenterResult] = useState(null)
  const [exportCenterBusy, setExportCenterBusy] = useState(false)
  const [showPluginMarket, setShowPluginMarket] = useState(false)
  const [pluginMarket, setPluginMarket] = useState(null)
  const [pluginActivity, setPluginActivity] = useState(null)
  const [pluginBusy, setPluginBusy] = useState(false)
  const [pluginName, setPluginName] = useState('Demo Safe Plugin')
  const [showIntegrationHub2, setShowIntegrationHub2] = useState(false)
  const [integrationHub2, setIntegrationHub2] = useState(null)
  const [integrationBusy, setIntegrationBusy] = useState(false)
  const [showQaCenter2, setShowQaCenter2] = useState(false)
  const [qaCenter, setQaCenter] = useState(null)
  const [qaMatrix, setQaMatrix] = useState(null)
  const [qaBusy, setQaBusy] = useState(false)
  const [showReleaseMgr, setShowReleaseMgr] = useState(false)
  const [releaseMgr, setReleaseMgr] = useState(null)
  const [releaseResult, setReleaseResult] = useState(null)
  const [releaseBusy, setReleaseBusy] = useState(false)
  const [showLaunchConsole, setShowLaunchConsole] = useState(false)
  const [launchConsole, setLaunchConsole] = useState(null)
  const [launchReport, setLaunchReport] = useState(null)
  const [launchBusy, setLaunchBusy] = useState(false)
  const [importText, setImportText] = useState('')
  const [importResult, setImportResult] = useState(null)
  const [mcpExecutions, setMcpExecutions] = useState([])
  const [mcpExecActionName, setMcpExecActionName] = useState('')
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
  const [showIntegrations, setShowIntegrations] = useState(false)
  const [slackStatus, setSlackStatus] = useState(null)
  const [slackNotifications, setSlackNotifications] = useState([])
  const [slackBusy, setSlackBusy] = useState(false)
  const [notionStatus, setNotionStatus] = useState(null)
  const [notionExports, setNotionExports] = useState([])
  const [notionBusy, setNotionBusy] = useState(false)
  const [showAutopilot, setShowAutopilot] = useState(false)
  const [autopilotSettings, setAutopilotSettings] = useState(null)
  const [autopilotRuns, setAutopilotRuns] = useState([])
  const [autopilotCheckpoints, setAutopilotCheckpoints] = useState([])
  const [autopilotBusy, setAutopilotBusy] = useState(false)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('evolveagent-theme', theme)
  }, [theme])

  useEffect(() => {
    if (!developerMode) setSidebarOpen(false)
  }, [developerMode])

  // ⌘K / Ctrl+K opens the command palette.
  useEffect(() => {
    function onKey(e) {
      if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault()
        setCmdkOpen((o) => !o)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // Phase 4 Voice Console: enumerate browser voices + load saved preferences once.
  useEffect(() => {
    const synth = window.speechSynthesis
    if (!synth) return
    const loadVoices = () => setAvailableVoices(synth.getVoices() || [])
    loadVoices()
    synth.addEventListener?.('voiceschanged', loadVoices)
    getVoiceSettings(workspaceId || 'global').then((s) => { if (s) setVoiceSettings(s) }).catch(() => {})
    getVoiceStatus().then(setVoiceStatus).catch(() => {})
    return () => synth.removeEventListener?.('voiceschanged', loadVoices)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const commandPaletteCommands = useMemo(() => {
    const gotoSection = (id) => () => { setDeveloperMode(true); setDevSection(id) }
    return [
      { id: 'mode-simple', label: 'Switch to Simple Mode', group: 'Mode', run: () => setDeveloperMode(false) },
      { id: 'mode-dev', label: 'Switch to Developer Mode', group: 'Mode', run: () => setDeveloperMode(true) },
      { id: 'new-chat', label: 'New chat', group: 'Chat', run: () => newChat() },
      { id: 'theme', label: 'Toggle light / dark theme', group: 'Appearance', run: () => toggleTheme() },
      { id: 'voice', label: 'Toggle spoken answers', group: 'Voice', run: () => setVoiceOutputEnabled((v) => !v) },
      { id: 'sec-agent', label: 'Go to Agent', group: 'Section', run: gotoSection('agent') },
      { id: 'sec-workspace', label: 'Go to Workspace', group: 'Section', run: gotoSection('workspace') },
      { id: 'sec-ops', label: 'Go to Ops', group: 'Section', run: gotoSection('ops') },
      { id: 'sec-tools', label: 'Go to Tools', group: 'Section', run: gotoSection('tools') },
      { id: 'sec-intel', label: 'Go to Intelligence', group: 'Section', run: gotoSection('intel') },
      { id: 'sec-build', label: 'Go to Build & Ship', group: 'Section', run: gotoSection('build') },
      { id: 'open-git', label: 'Open Git Intelligence', group: 'Open', run: () => { setDeveloperMode(true); setDevSection('workspace'); setShowGitIntel(true); if (!gitStatus) refreshGitIntel() } },
      { id: 'open-studio', label: 'Open Agent Studio', group: 'Open', run: () => { setDeveloperMode(true); setDevSection('agent'); setShowAgentStudio(true); if (!studioTemplates.length) refreshAgentStudio() } },
      { id: 'open-master', label: 'Open Master Agent', group: 'Open', run: () => { setDeveloperMode(true); setDevSection('agent'); setShowMasterPanel(true) } },
      { id: 'open-voice', label: 'Open Voice Console', group: 'Open', run: () => { setDeveloperMode(true); setDevSection('tools'); setShowVoiceConsole(true); refreshVoiceConsole() } },
      { id: 'open-workflows', label: 'Open Durable Workflows', group: 'Open', run: () => { setDeveloperMode(true); setDevSection('ops'); setShowWorkflows(true); refreshWorkflows() } },
      { id: 'open-marketplace', label: 'Open Marketplace', group: 'Open', run: () => { setDeveloperMode(true); setDevSection('build'); setShowMarketplaceHub(true); refreshMarketplaceHub() } },
      { id: 'open-design', label: 'Open Design Agent', group: 'Open', run: () => { setDeveloperMode(true); setDevSection('tools'); setShowDesignAgent(true); refreshDesignAgent() } },
      { id: 'open-repo-finder', label: 'Open Repo Finder', group: 'Open', run: () => { setDeveloperMode(true); setDevSection('intel'); setShowRepoFinder(true) } },
    ]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gitStatus, studioTemplates])

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
    refreshCompliance(workspaceId)
    refreshLearningReport(workspaceId)
    refreshDigitalTwin(workspaceId)
    refreshMissionControl(workspaceId)
    refreshCustomAgents(workspaceId)
    refreshAgentMarketplace(workspaceId)
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
    refreshCompliance(workspaceId)
    refreshIntegrations()
    refreshAutopilot(workspaceId)
    refreshEvaluationLab(workspaceId)
    refreshProjectManager(workspaceId)
    refreshPortfolio()
    refreshOsPanel()
    refreshOrgPanel()
    refreshAgentMarketplace(workspaceId)
    refreshBusinessPanel(workspaceId)
    refreshChiefPanel(workspaceId)
    refreshSimulatorPanel(workspaceId)
    refreshMultimodalPanel(workspaceId)
    refreshIndustryPanel()
    refreshAgentNetworkPanel()
    refreshHealingPanel()
    refreshCompanyBrainPanel()
    refreshDevicePanel()
    refreshTrainingPanel()
    refreshAvatarPanel()
    refreshLifePanel(workspaceId)
    refreshUniversalPanel()
    refreshSaasPanel()
    refreshTeamPanel()
    refreshBizOpsPanel()
    refreshComplianceIntelPanel()
    refreshBoardPanel()
    refreshInnovationPanel()
    refreshSimWorldPanel()
    refreshOrgOsPanel()
    refreshCompanionPanel()
    refreshOperatingLayerPanel()
    refreshMcpPanel()
    refreshApprovalsCenter()
    refreshHealthMonitor()
    refreshUsageLedger()
    refreshRetrieval()
    refreshEvalHarness()
    refreshPlaybooks()
    refreshOpLayer2()
    refreshNotifications()
    refreshWsTemplates()
    refreshScheduled()
    refreshDataExport()
    refreshOs2()
    refreshMasterPanel()
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

  async function refreshCompliance(nextWorkspaceId = workspaceId) {
    if (!nextWorkspaceId) return
    const [summary, audit, retention] = await Promise.all([
      getComplianceSummary(nextWorkspaceId),
      getComplianceAuditLog(nextWorkspaceId, 25),
      getComplianceRetentionPolicies(nextWorkspaceId),
    ])
    setComplianceSummary(summary)
    setComplianceAudit(audit?.events || [])
    setComplianceRetention(retention)
  }

  async function handlePiiScan() {
    setComplianceBusy(true)
    setComplianceError('')
    try {
      setPiiScanResult(await scanCompliancePii(piiScanText, true))
      await refreshCompliance(workspaceId)
    } catch (err) {
      setComplianceError(err.message)
    } finally {
      setComplianceBusy(false)
    }
  }

  async function handleComplianceExport(format) {
    setComplianceBusy(true)
    setComplianceError('')
    try {
      const content = await exportComplianceReport(workspaceId, format)
      const extension = format === 'json' ? 'json' : 'md'
      downloadFile(
        `evolveagent-compliance.${extension}`,
        content,
        format === 'json' ? 'application/json' : 'text/markdown',
      )
    } catch (err) {
      setComplianceError(err.message)
    } finally {
      setComplianceBusy(false)
    }
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

  async function refreshEvaluationLab(nextWorkspaceId = workspaceId) {
    const [dashboard, benchmarks] = await Promise.all([
      getEvaluationDashboard(nextWorkspaceId),
      getEvaluationBenchmarks(),
    ])
    setEvaluationDashboard(dashboard)
    setEvaluationBenchmarks(benchmarks.benchmarks || [])
  }

  async function refreshProjectManager(nextWorkspaceId = workspaceId) {
    const [dashboard, risks] = await Promise.all([
      getProjectManagerDashboard(nextWorkspaceId),
      getProjectManagerRisks(nextWorkspaceId),
    ])
    setProjectManagerDashboard(dashboard)
    setProjectManagerRisks(risks.risks || [])
  }

  async function handleCreateProjectRisk() {
    if (!newRiskTitle.trim()) return
    setProjectManagerBusy(true)
    setProjectManagerError('')
    try {
      await createProjectManagerRisk({
        title: newRiskTitle.trim(),
        severity: newRiskSeverity,
        workspace_id: workspaceId,
      })
      setNewRiskTitle('')
      await refreshProjectManager(workspaceId)
      setCopied('Risk logged')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setProjectManagerError(err.message)
    } finally {
      setProjectManagerBusy(false)
    }
  }

  async function handleGenerateProjectReport() {
    setProjectManagerBusy(true)
    setProjectManagerError('')
    try {
      await generateProjectManagerReport(workspaceId)
      await refreshProjectManager(workspaceId)
      setCopied('Status report generated')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setProjectManagerError(err.message)
    } finally {
      setProjectManagerBusy(false)
    }
  }

  async function refreshPortfolio() {
    const [dashboard, health, analytics] = await Promise.all([
      getPortfolioDashboard(),
      getPortfolioHealth(),
      getPortfolioAnalytics(),
    ])
    setPortfolioDashboard(dashboard)
    setPortfolioHealth(health)
    setPortfolioAnalytics(analytics)
  }

  async function handleGeneratePortfolioReport() {
    setPortfolioBusy(true)
    setPortfolioError('')
    try {
      await generatePortfolioReport()
      await refreshPortfolio()
      setCopied('Executive summary generated')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setPortfolioError(err.message)
    } finally {
      setPortfolioBusy(false)
    }
  }

  async function handleExportPortfolio(format) {
    setPortfolioBusy(true)
    setPortfolioError('')
    try {
      const content = await exportPortfolio(format)
      const mime = format === 'markdown' ? 'text/markdown' : 'application/json'
      const blob = new Blob([content], { type: mime })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `evolveagent-portfolio.${format === 'markdown' ? 'md' : 'json'}`
      link.click()
      URL.revokeObjectURL(url)
      setCopied(`Portfolio exported (${format})`)
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setPortfolioError(err.message)
    } finally {
      setPortfolioBusy(false)
    }
  }

  async function refreshOsPanel() {
    const [summary, installer, sla, scheduler] = await Promise.all([
      getOsSummary(),
      getOsInstaller(),
      getOsSla(),
      getOsScheduler(),
    ])
    setOsSummary(summary)
    setOsInstaller(installer)
    setOsSla(sla)
    setOsScheduler(scheduler)
  }

  async function handleCopyOsSummary() {
    if (!osSummary) return
    try {
      await navigator.clipboard.writeText(JSON.stringify(osSummary, null, 2))
      setCopied('EvolveAgent OS summary copied')
      window.setTimeout(() => setCopied(''), 1300)
    } catch {
      setCopied('Copy failed')
      window.setTimeout(() => setCopied(''), 1300)
    }
  }

  async function refreshOrgPanel() {
    const [overview, runs, collaborations] = await Promise.all([
      getDepartments(),
      getDepartmentRuns(),
      getDepartmentCollaborations(),
    ])
    setDepartmentOverview(overview)
    setDepartments(overview?.departments || [])
    setDepartmentRuns(runs?.runs || [])
    setDepartmentCollaborations(collaborations?.collaborations || [])
  }

  async function handleSeedDepartments() {
    setOrgBusy(true)
    setOrgError(null)
    try {
      await seedDepartmentTemplates()
      await refreshOrgPanel()
    } catch (error) {
      setOrgError(error.message || 'Failed to seed departments')
    } finally {
      setOrgBusy(false)
    }
  }

  async function handleCreateDepartment(event) {
    event.preventDefault()
    if (!newDepartmentName.trim()) return
    setOrgBusy(true)
    setOrgError(null)
    try {
      await createDepartment({ name: newDepartmentName.trim(), permission_level: newDepartmentPermission })
      setNewDepartmentName('')
      setNewDepartmentPermission('read_only')
      await refreshOrgPanel()
    } catch (error) {
      setOrgError(error.message || 'Failed to create department')
    } finally {
      setOrgBusy(false)
    }
  }

  async function handleCreateDepartmentRun(event) {
    event.preventDefault()
    if (!runDepartmentId || !runDepartmentTask.trim()) return
    setOrgBusy(true)
    setOrgError(null)
    try {
      await createDepartmentRun(runDepartmentId, runDepartmentTask.trim())
      setRunDepartmentTask('')
      await refreshOrgPanel()
    } catch (error) {
      setOrgError(error.message || 'Failed to plan department run')
    } finally {
      setOrgBusy(false)
    }
  }

  async function handleCreateCollaboration(event) {
    event.preventDefault()
    if (!collabGoal.trim()) return
    setOrgBusy(true)
    setOrgError(null)
    try {
      const names = collabDepartments
        .split(',')
        .map((name) => name.trim())
        .filter(Boolean)
      await createDepartmentCollaboration({ goal: collabGoal.trim(), departments: names })
      setCollabGoal('')
      setCollabDepartments('')
      await refreshOrgPanel()
    } catch (error) {
      setOrgError(error.message || 'Failed to plan collaboration')
    } finally {
      setOrgBusy(false)
    }
  }

  async function refreshBusinessPanel(nextWorkspaceId = workspaceId) {
    const [dashboard, leads, cases, documents, proposals, marketing] = await Promise.all([
      getBusinessDashboard(nextWorkspaceId),
      getBusinessLeads(nextWorkspaceId),
      getBusinessSupportCases(nextWorkspaceId),
      getBusinessDocuments(nextWorkspaceId),
      getBusinessProposals(nextWorkspaceId),
      getBusinessMarketingItems(nextWorkspaceId),
    ])
    setBusinessDashboard(dashboard)
    setBusinessLeads(leads?.leads || [])
    setBusinessSupportCases(cases?.support_cases || [])
    setBusinessDocuments(documents?.documents || [])
    setBusinessProposals(proposals?.proposals || [])
    setBusinessMarketingItems(marketing?.marketing_items || [])
  }

  async function runBusinessAction(action) {
    setBusinessBusy(true)
    setBusinessError(null)
    try {
      await action()
      await refreshBusinessPanel(workspaceId)
    } catch (error) {
      setBusinessError(error.message || 'Business action failed')
    } finally {
      setBusinessBusy(false)
    }
  }

  async function handleCreateLead(event) {
    event.preventDefault()
    if (!leadName.trim() && !leadCompany.trim()) return
    await runBusinessAction(async () => {
      await createBusinessLead({ name: leadName.trim(), company: leadCompany.trim(), workspace_id: workspaceId })
      setLeadName('')
      setLeadCompany('')
    })
  }

  async function handleCreateSupportCase(event) {
    event.preventDefault()
    if (!caseSubject.trim()) return
    await runBusinessAction(async () => {
      await createBusinessSupportCase({ subject: caseSubject.trim(), priority: casePriority, workspace_id: workspaceId })
      setCaseSubject('')
      setCasePriority('medium')
    })
  }

  async function handleCreateBusinessDocument(event) {
    event.preventDefault()
    if (!docContent.trim()) return
    await runBusinessAction(async () => {
      await createBusinessDocument({ title: docTitle.trim(), content: docContent.trim(), workspace_id: workspaceId })
      setDocTitle('')
      setDocContent('')
    })
  }

  async function handleCreateProposal(event) {
    event.preventDefault()
    if (!proposalTitle.trim()) return
    await runBusinessAction(async () => {
      await createBusinessProposal({ title: proposalTitle.trim(), client: proposalClient.trim(), workspace_id: workspaceId })
      setProposalTitle('')
      setProposalClient('')
    })
  }

  async function handleCreateMarketingItem(event) {
    event.preventDefault()
    if (!marketingTitle.trim()) return
    await runBusinessAction(async () => {
      await createBusinessMarketingItem({ title: marketingTitle.trim(), channel: marketingChannel, workspace_id: workspaceId })
      setMarketingTitle('')
      setMarketingChannel('email')
    })
  }

  async function refreshChiefPanel(nextWorkspaceId = workspaceId) {
    const [dashboard, priorities, followups] = await Promise.all([
      getChiefDashboard(nextWorkspaceId),
      getChiefPriorities(nextWorkspaceId),
      getChiefFollowups(nextWorkspaceId),
    ])
    setChiefDashboard(dashboard)
    setChiefPriorities(priorities?.priority_items || [])
    setChiefFollowups(followups?.followups || [])
    setChiefOverdueCount(followups?.overdue_count || 0)
  }

  async function runChiefAction(action) {
    setChiefBusy(true)
    setChiefError(null)
    try {
      await action()
      await refreshChiefPanel(workspaceId)
    } catch (error) {
      setChiefError(error.message || 'Chief of Staff action failed')
    } finally {
      setChiefBusy(false)
    }
  }

  async function handleCreateDailyPlan() {
    await runChiefAction(() => createChiefDailyPlan(workspaceId))
  }

  async function handleCreateWeeklyPlan() {
    await runChiefAction(() => createChiefWeeklyPlan(workspaceId))
  }

  async function handleCreateFollowup(event) {
    event.preventDefault()
    if (!followupTitle.trim()) return
    await runChiefAction(async () => {
      await createChiefFollowup({
        title: followupTitle.trim(),
        due_date: followupDueDate.trim(),
        priority: followupPriority,
        workspace_id: workspaceId,
      })
      setFollowupTitle('')
      setFollowupDueDate('')
      setFollowupPriority('medium')
    })
  }

  async function handleMarkFollowupDone(followupId) {
    await runChiefAction(() => updateChiefFollowup(followupId, { status: 'done' }))
  }

  async function refreshSimulatorPanel(nextWorkspaceId = workspaceId) {
    const [dashboard, scenarios, results] = await Promise.all([
      getSimulatorDashboard(nextWorkspaceId),
      getSimulatorScenarios(nextWorkspaceId),
      getSimulatorResults(nextWorkspaceId),
    ])
    setSimulatorDashboard(dashboard)
    setSimulatorScenarios(scenarios?.scenarios || [])
    setSimulatorResults(results?.results || [])
  }

  async function runSimulatorAction(action) {
    setSimulatorBusy(true)
    setSimulatorError(null)
    try {
      const value = await action()
      await refreshSimulatorPanel(workspaceId)
      return value
    } catch (error) {
      setSimulatorError(error.message || 'Simulator action failed')
      return null
    } finally {
      setSimulatorBusy(false)
    }
  }

  async function handleCreateScenario(event) {
    event.preventDefault()
    if (!scenarioTitle.trim()) return
    await runSimulatorAction(async () => {
      await createSimulatorScenario({
        title: scenarioTitle.trim(),
        scenario_type: scenarioType,
        assumptions: scenarioAssumptions.split(',').map((value) => value.trim()).filter(Boolean),
        options: scenarioOptions.split(',').map((value) => value.trim()).filter(Boolean),
        workspace_id: workspaceId,
      })
      setScenarioTitle('')
      setScenarioType('decision')
      setScenarioAssumptions('')
      setScenarioOptions('')
    })
  }

  async function handleRunSimulation(scenarioId) {
    const result = await runSimulatorAction(() => runSimulatorScenario(scenarioId))
    if (result) setLatestSimResult(result)
  }

  async function refreshMultimodalPanel(nextWorkspaceId = workspaceId) {
    const [dashboard, items] = await Promise.all([
      getMultimodalDashboard(nextWorkspaceId),
      getMultimodalItems(nextWorkspaceId),
    ])
    setMultimodalDashboard(dashboard)
    setMultimodalItems(items?.items || [])
  }

  async function runMultimodalAction(action) {
    setMultimodalBusy(true)
    setMultimodalError(null)
    try {
      const value = await action()
      await refreshMultimodalPanel(workspaceId)
      return value
    } catch (error) {
      setMultimodalError(error.message || 'Multi-modal action failed')
      return null
    } finally {
      setMultimodalBusy(false)
    }
  }

  async function handleCreateMultimodalItem(event) {
    event.preventDefault()
    if (!mmTitle.trim()) return
    await runMultimodalAction(async () => {
      await createMultimodalItem({
        title: mmTitle.trim(),
        item_type: mmType,
        description: mmDescription.trim(),
        workspace_id: workspaceId,
      })
      setMmTitle('')
      setMmType('screenshot')
      setMmDescription('')
    })
  }

  async function handleAnalyzeMultimodalItem(itemId, analysisType) {
    const analysis = await runMultimodalAction(() => analyzeMultimodalItem(itemId, analysisType))
    if (analysis) setLatestMmAnalysis(analysis)
  }

  async function refreshIndustryPanel() {
    const [dashboard, modes, runs] = await Promise.all([
      getIndustryModesDashboard(),
      getIndustryModes(),
      getIndustryModeRuns(),
    ])
    setIndustryDashboard(dashboard)
    setIndustryModes(modes?.modes || [])
    setIndustryRuns(runs?.runs || [])
  }

  async function runIndustryAction(action) {
    setIndustryBusy(true)
    setIndustryError(null)
    try {
      await action()
      await refreshIndustryPanel()
    } catch (error) {
      setIndustryError(error.message || 'Industry mode action failed')
    } finally {
      setIndustryBusy(false)
    }
  }

  async function handleSeedIndustryModes() {
    await runIndustryAction(() => seedIndustryModes())
  }

  async function handleRunIndustryMode(event) {
    event.preventDefault()
    if (!industryRunModeId || !industryPrompt.trim()) return
    await runIndustryAction(async () => {
      await runIndustryMode(industryRunModeId, industryPrompt.trim())
      setIndustryPrompt('')
    })
  }

  async function refreshAgentNetworkPanel() {
    const [dashboard, contracts, audit] = await Promise.all([
      getAgentNetworkDashboard(),
      getAgentNetworkContracts(),
      getAgentNetworkAudit(),
    ])
    setAgentNetworkDashboard(dashboard)
    setAgentNetworkContracts(contracts?.contracts || [])
    setAgentNetworkAudit(audit?.audit || [])
  }

  async function runAgentNetworkAction(action) {
    setAgentNetworkBusy(true)
    setAgentNetworkError(null)
    try {
      const value = await action()
      await refreshAgentNetworkPanel()
      return value
    } catch (error) {
      setAgentNetworkError(error.message || 'Agent network action failed')
      return null
    } finally {
      setAgentNetworkBusy(false)
    }
  }

  async function handleCreateContract(event) {
    event.preventDefault()
    if (!contractTask.trim()) return
    await runAgentNetworkAction(async () => {
      await createAgentNetworkContract({
        target_agent: contractTarget.trim(),
        task: contractTask.trim(),
        expected_output: contractExpected.trim(),
      })
      setContractTarget('')
      setContractTask('')
      setContractExpected('')
    })
  }

  async function handleCreateHandoff(contractId, handoffType) {
    const handoff = await runAgentNetworkAction(() => createAgentNetworkHandoff(contractId, handoffType))
    if (handoff) setLatestHandoff(handoff)
  }

  async function handleVerifyHandoff(handoffId) {
    const verified = await runAgentNetworkAction(() => verifyAgentNetworkHandoff(handoffId))
    if (verified) setLatestHandoff(verified)
  }

  async function refreshHealingPanel() {
    const [dashboard, findings] = await Promise.all([
      getSelfHealingDashboard(),
      getSelfHealingFindings(),
    ])
    setHealingDashboard(dashboard)
    setHealingFindings(findings?.findings || [])
  }

  async function runHealingAction(action) {
    setHealingBusy(true)
    setHealingError(null)
    try {
      const value = await action()
      await refreshHealingPanel()
      return value
    } catch (error) {
      setHealingError(error.message || 'Self-healing action failed')
      return null
    } finally {
      setHealingBusy(false)
    }
  }

  async function handleRunHealingCheck() {
    await runHealingAction(() => createSelfHealingCheck({ command: healingCommand, mode: 'run' }))
  }

  async function handleCreateRepairTask(findingId) {
    const repair = await runHealingAction(() => createSelfHealingRepairTask(findingId))
    if (repair) setHealingRepairs((current) => [repair, ...current].slice(0, 8))
  }

  async function handleVerifyRepair(repairId) {
    await runHealingAction(() => verifySelfHealingRepair(repairId, { mode: 'run' }))
  }

  async function refreshCompanyBrainPanel() {
    const [dashboard, decisions] = await Promise.all([
      getCompanyBrainDashboard(),
      getCompanyBrainDecisions(),
    ])
    setCompanyBrainDashboard(dashboard)
    setCompanyBrainDecisions(decisions?.decisions || [])
  }

  async function runCompanyBrainAction(action) {
    setCompanyBrainBusy(true)
    setCompanyBrainError(null)
    try {
      const value = await action()
      await refreshCompanyBrainPanel()
      return value
    } catch (error) {
      setCompanyBrainError(error.message || 'Company Brain action failed')
      return null
    } finally {
      setCompanyBrainBusy(false)
    }
  }

  async function handleCreateStrategy(event) {
    event.preventDefault()
    if (!strategyTitle.trim()) return
    await runCompanyBrainAction(async () => {
      await createCompanyBrainStrategy({ title: strategyTitle.trim() })
      setStrategyTitle('')
    })
  }

  async function handleCreateCompanyDecision(event) {
    event.preventDefault()
    if (!decisionTitle.trim()) return
    await runCompanyBrainAction(async () => {
      await createCompanyBrainDecision({ title: decisionTitle.trim(), impact: decisionImpact })
      setDecisionTitle('')
      setDecisionImpact('medium')
    })
  }

  async function handleGenerateCompanyReport() {
    const report = await runCompanyBrainAction(() => createCompanyBrainReport())
    if (report) setCompanyBrainReport(report)
  }

  async function refreshDevicePanel() {
    const [dashboard, sessions, audit] = await Promise.all([
      getDeviceOperatorDashboard(),
      getDeviceOperatorSessions(),
      getDeviceOperatorAudit(),
    ])
    setDeviceDashboard(dashboard)
    setDeviceSessions(sessions?.sessions || [])
    setDeviceAudit(audit?.audit || [])
  }

  async function runDeviceAction(action) {
    setDeviceBusy(true)
    setDeviceError(null)
    try {
      const value = await action()
      await refreshDevicePanel()
      return value
    } catch (error) {
      setDeviceError(error.message || 'Device operator action failed')
      return null
    } finally {
      setDeviceBusy(false)
    }
  }

  async function handleCreateDeviceSession() {
    const session = await runDeviceAction(() => createDeviceOperatorSession({ permission_level: devicePermission }))
    if (session) setDeviceSessionId(session.session_id)
  }

  async function handlePlanDevice(event) {
    event.preventDefault()
    if (!deviceSessionId || (!deviceCommand.trim() && !deviceScreenText.trim())) return
    const plan = await runDeviceAction(() =>
      planDeviceOperatorSession(deviceSessionId, { command: deviceCommand.trim(), screen_text: deviceScreenText.trim() }),
    )
    if (plan) {
      setDevicePlannedActions(plan.planned_actions || [])
      setDeviceCommand('')
      setDeviceScreenText('')
    }
  }

  async function handleConfirmDeviceAction(actionId, approve) {
    await runDeviceAction(async () => {
      const updated = await confirmDeviceOperatorAction(deviceSessionId, actionId, approve)
      setDevicePlannedActions((current) =>
        current.map((item) => (item.action_id === actionId ? { ...item, status: updated.status } : item)),
      )
    })
  }

  async function refreshTrainingPanel() {
    const [dashboard, datasets] = await Promise.all([
      getTrainingLabDashboard(),
      getTrainingDatasets(),
    ])
    setTrainingDashboard(dashboard)
    setTrainingDatasets(datasets?.datasets || [])
  }

  async function loadTrainingExamples(datasetId) {
    if (!datasetId) {
      setTrainingExamples([])
      return
    }
    const detail = await getTrainingDataset(datasetId)
    setTrainingExamples(detail?.examples || [])
  }

  async function runTrainingAction(action) {
    setTrainingBusy(true)
    setTrainingError(null)
    try {
      const value = await action()
      await refreshTrainingPanel()
      if (trainingDatasetId) await loadTrainingExamples(trainingDatasetId)
      return value
    } catch (error) {
      setTrainingError(error.message || 'Training lab action failed')
      return null
    } finally {
      setTrainingBusy(false)
    }
  }

  async function handleCreateDataset(event) {
    event.preventDefault()
    if (!datasetName.trim()) return
    const dataset = await runTrainingAction(() => createTrainingDataset({ name: datasetName.trim() }))
    if (dataset) {
      setDatasetName('')
      setTrainingDatasetId(dataset.dataset_id)
      await loadTrainingExamples(dataset.dataset_id)
    }
  }

  async function handleSelectTrainingDataset(datasetId) {
    setTrainingDatasetId(datasetId)
    setTrainingExport(null)
    await loadTrainingExamples(datasetId)
  }

  async function handleAddExample(event) {
    event.preventDefault()
    if (!trainingDatasetId || !examplePrompt.trim()) return
    await runTrainingAction(async () => {
      await addTrainingExample(trainingDatasetId, { prompt: examplePrompt.trim(), completion: exampleCompletion.trim() })
      setExamplePrompt('')
      setExampleCompletion('')
    })
  }

  async function handleSetExampleStatus(exampleId, status) {
    await runTrainingAction(() => updateTrainingExample(exampleId, { status }))
  }

  async function handleExportDataset() {
    if (!trainingDatasetId) return
    const result = await runTrainingAction(() => exportTrainingDataset(trainingDatasetId))
    if (result) setTrainingExport(result)
  }

  async function handleCreateTrainingRun() {
    await runTrainingAction(() => createTrainingRun({ dataset_id: trainingDatasetId || null }))
  }

  async function refreshAvatarPanel() {
    const [dashboard, meetings] = await Promise.all([
      getAvatarDashboard(),
      getAvatarMeetingSessions(),
    ])
    setAvatarDashboard(dashboard)
    setAvatarMeetings(meetings?.meeting_sessions || [])
    if (dashboard?.persona?.avatar_name && !avatarName) setAvatarName(dashboard.persona.avatar_name)
    if (dashboard?.voice_settings?.voice_mode) setAvatarVoiceMode(dashboard.voice_settings.voice_mode)
  }

  async function runAvatarAction(action) {
    setAvatarBusy(true)
    setAvatarError(null)
    try {
      await action()
      await refreshAvatarPanel()
    } catch (error) {
      setAvatarError(error.message || 'Avatar action failed')
    } finally {
      setAvatarBusy(false)
    }
  }

  async function handleSavePersona(event) {
    event.preventDefault()
    await runAvatarAction(() => updateAvatarPersona({ avatar_name: avatarName.trim() || undefined, tone: avatarTone }))
  }

  async function handleSaveVoiceMode(mode) {
    setAvatarVoiceMode(mode)
    await runAvatarAction(() => updateAvatarVoiceSettings({ voice_mode: mode }))
  }

  async function handleCreateMeetingSession(event) {
    event.preventDefault()
    if (!meetingTitle.trim()) return
    await runAvatarAction(async () => {
      await createAvatarMeetingSession({ title: meetingTitle.trim() })
      setMeetingTitle('')
    })
  }

  async function handleGrantConsent() {
    await runAvatarAction(() => createAvatarConsent({ scope: 'persona_behavior', granted: true }))
  }

  async function handleGenerateAvatarImage(event) {
    event.preventDefault()
    await runAvatarAction(() => generateAvatarImage({ description: avatarDescription.trim(), style: avatarStyle }))
  }

  async function refreshLifePanel(nextWorkspaceId = workspaceId) {
    const [dashboard, tasks, reminders, deadlines] = await Promise.all([
      getLifeOsDashboard(nextWorkspaceId),
      getLifeTasks(nextWorkspaceId),
      getLifeReminders(nextWorkspaceId),
      getLifeDeadlines(nextWorkspaceId),
    ])
    setLifeDashboard(dashboard)
    setLifeTasks(tasks?.ranked || [])
    setLifeReminders(reminders?.reminders || [])
    setLifeDeadlines(deadlines?.deadlines || [])
  }

  async function runLifeAction(action) {
    setLifeBusy(true)
    setLifeError(null)
    try {
      const value = await action()
      await refreshLifePanel(workspaceId)
      return value
    } catch (error) {
      setLifeError(error.message || 'Life OS action failed')
      return null
    } finally {
      setLifeBusy(false)
    }
  }

  async function handleCreateLifeTask(event) {
    event.preventDefault()
    if (!lifeTaskTitle.trim()) return
    await runLifeAction(async () => {
      await createLifeTask({ title: lifeTaskTitle.trim(), priority: lifeTaskPriority, due_date: lifeTaskDue.trim(), workspace_id: workspaceId })
      setLifeTaskTitle('')
      setLifeTaskPriority('medium')
      setLifeTaskDue('')
    })
  }

  async function handleCompleteLifeTask(taskId) {
    await runLifeAction(() => updateLifeTask(taskId, { status: 'done' }))
  }

  async function handleCreateLifeSchedule(event) {
    event.preventDefault()
    if (!lifeScheduleTitle.trim()) return
    await runLifeAction(async () => {
      await createLifeScheduleItem({ title: lifeScheduleTitle.trim(), date: lifeScheduleDate.trim(), workspace_id: workspaceId })
      setLifeScheduleTitle('')
      setLifeScheduleDate('')
    })
  }

  async function handleCreateLifeReminder(event) {
    event.preventDefault()
    if (!lifeReminderTitle.trim()) return
    await runLifeAction(async () => {
      await createLifeReminder({ title: lifeReminderTitle.trim(), remind_on: lifeReminderOn.trim(), workspace_id: workspaceId })
      setLifeReminderTitle('')
      setLifeReminderOn('')
    })
  }

  async function handleCreateLifeDeadline(event) {
    event.preventDefault()
    if (!lifeDeadlineTitle.trim()) return
    await runLifeAction(async () => {
      await createLifeDeadline({ title: lifeDeadlineTitle.trim(), kind: lifeDeadlineKind, due_date: lifeDeadlineDue.trim(), workspace_id: workspaceId })
      setLifeDeadlineTitle('')
      setLifeDeadlineKind('school')
      setLifeDeadlineDue('')
    })
  }

  async function handleGenerateLifeDailyPlan() {
    const plan = await runLifeAction(() => createLifeDailyPlan(workspaceId))
    if (plan) setLifeDailyPlan(plan)
  }

  async function refreshUniversalPanel() {
    const [dashboard, sessions, workflows, audit] = await Promise.all([
      getUniversalOperatorDashboard(),
      getUniversalOperatorSessions(),
      getUniversalOperatorWorkflows(),
      getUniversalOperatorAudit(),
    ])
    setUniversalDashboard(dashboard)
    setUniversalSessions(sessions?.sessions || [])
    setUniversalWorkflows(workflows?.workflows || [])
    setUniversalAudit(audit?.audit || [])
  }

  async function runUniversalAction(action) {
    setUniversalBusy(true)
    setUniversalError(null)
    try {
      const value = await action()
      await refreshUniversalPanel()
      return value
    } catch (error) {
      setUniversalError(error.message || 'Universal operator action failed')
      return null
    } finally {
      setUniversalBusy(false)
    }
  }

  async function handleCreateUniversalSession() {
    await runUniversalAction(() => createUniversalOperatorSession({ surface: universalSurface }))
  }

  async function handleCreateUniversalWorkflow(event) {
    event.preventDefault()
    if (!universalGoal.trim()) return
    await runUniversalAction(async () => {
      const steps = universalSteps.split('\n').map((s) => s.trim()).filter(Boolean)
      await createUniversalOperatorWorkflow({ goal: universalGoal.trim(), steps })
      setUniversalGoal('')
      setUniversalSteps('')
    })
  }

  async function handlePlanUniversalWorkflow(workflowId) {
    const plan = await runUniversalAction(() => planUniversalOperatorWorkflow(workflowId))
    if (plan) setUniversalPlannedActions(plan.planned_actions || [])
  }

  async function handleDecideUniversalAction(actionId, decision) {
    await runUniversalAction(async () => {
      const updated = await decideUniversalOperatorAction(actionId, decision)
      setUniversalPlannedActions((current) =>
        current.map((item) => (item.action_id === actionId ? { ...item, status: updated.status } : item)),
      )
    })
  }

  async function handleCreateUniversalHandoff() {
    await runUniversalAction(() => createUniversalOperatorHandoff({ from_device: 'laptop', to_device: 'phone', summary: 'Continue current workflow' }))
  }

  async function refreshTeamPanel() {
    const [dashboard, members, assignments, sprints] = await Promise.all([
      getTeamManagerDashboard(),
      getTeamMembers(),
      getTeamAssignments(),
      getTeamSprints(),
    ])
    setTeamDashboard(dashboard)
    setTeamMembers(members?.members || [])
    setTeamAssignments(assignments?.assignments || [])
    setTeamSprints(sprints?.sprints || [])
  }

  async function runTeamAction(action) {
    setTeamBusy(true)
    setTeamError(null)
    try {
      const value = await action()
      await refreshTeamPanel()
      return value
    } catch (error) {
      setTeamError(error.message || 'Team manager action failed')
      return null
    } finally {
      setTeamBusy(false)
    }
  }

  async function handleCreateTeamMember(event) {
    event.preventDefault()
    if (!memberName.trim()) return
    await runTeamAction(async () => {
      await createTeamMember({ name: memberName.trim(), member_type: memberType })
      setMemberName('')
      setMemberType('human')
    })
  }

  async function handleCreateTeamAssignment(event) {
    event.preventDefault()
    if (!assignmentTitle.trim()) return
    await runTeamAction(async () => {
      await createTeamAssignment({ title: assignmentTitle.trim(), owner_name: assignmentOwner.trim(), priority: assignmentPriority })
      setAssignmentTitle('')
      setAssignmentOwner('')
      setAssignmentPriority('medium')
    })
  }

  async function handleCompleteAssignment(assignmentId) {
    await runTeamAction(() => updateTeamAssignment(assignmentId, { status: 'done' }))
  }

  async function handleGenerateStandup() {
    const standup = await runTeamAction(() => createTeamStandup())
    if (standup) setTeamStandup(standup)
  }

  async function handleCreateTeamSprint(event) {
    event.preventDefault()
    if (!sprintName.trim()) return
    await runTeamAction(async () => {
      await createTeamSprint({ name: sprintName.trim() })
      setSprintName('')
    })
  }

  async function handleReviewSprint(sprintId) {
    await runTeamAction(() => reviewTeamSprint(sprintId, {}))
  }

  async function refreshSaasPanel() {
    const [dashboard, projects] = await Promise.all([
      getSaasBuilderDashboard(),
      getSaasProjects(),
    ])
    setSaasDashboard(dashboard)
    setSaasProjects(projects?.projects || [])
  }

  async function runSaasAction(action) {
    setSaasBusy(true)
    setSaasError(null)
    try {
      const value = await action()
      await refreshSaasPanel()
      return value
    } catch (error) {
      setSaasError(error.message || 'SaaS builder action failed')
      return null
    } finally {
      setSaasBusy(false)
    }
  }

  async function loadSaasFeedback(projectId) {
    if (!projectId) {
      setSaasFeedback([])
      return
    }
    const result = await getSaasFeedback(projectId)
    setSaasFeedback(result?.feedback || [])
  }

  async function handleCreateSaasProject(event) {
    event.preventDefault()
    if (!saasName.trim()) return
    const project = await runSaasAction(() => createSaasProject({ name: saasName.trim(), idea: saasIdea.trim() }))
    if (project) {
      setSaasName('')
      setSaasIdea('')
      setSaasProjectId(project.project_id)
      setSaasArtifact(null)
      await loadSaasFeedback(project.project_id)
    }
  }

  async function handleSaasStep(kind) {
    if (!saasProjectId) return
    const fn = {
      validate: validateSaasProject,
      roadmap: roadmapSaasProject,
      architecture: architectureSaasProject,
      launch: launchAssetsSaasProject,
    }[kind]
    const artifact = await runSaasAction(() => fn(saasProjectId))
    if (artifact) setSaasArtifact({ kind, data: artifact })
  }

  async function handleCreateSaasFeedback(event) {
    event.preventDefault()
    if (!saasProjectId || !saasFeedbackTitle.trim()) return
    await runSaasAction(async () => {
      await createSaasFeedback(saasProjectId, { title: saasFeedbackTitle.trim(), type: saasFeedbackType })
      setSaasFeedbackTitle('')
      setSaasFeedbackType('feature')
      await loadSaasFeedback(saasProjectId)
    })
  }

  async function refreshBizOpsPanel() {
    const [dashboard, workflows, approvals] = await Promise.all([
      getBusinessOperatorDashboard(),
      getBusinessOperatorWorkflows(),
      getBusinessOperatorApprovals(),
    ])
    setBizOpsDashboard(dashboard)
    setBizOpsWorkflows(workflows?.workflows || [])
    setBizOpsApprovals(approvals?.approvals || [])
  }

  async function runBizOpsAction(action) {
    setBizOpsBusy(true)
    setBizOpsError(null)
    try {
      await action()
      await refreshBizOpsPanel()
    } catch (error) {
      setBizOpsError(error.message || 'Business operator action failed')
    } finally {
      setBizOpsBusy(false)
    }
  }

  async function handleCreateBizOpsWorkflow() {
    await runBizOpsAction(() => createBusinessOperatorWorkflow({ workflow_type: bizOpsWorkflowType }))
  }

  async function handleCreateBizOpsReport() {
    await runBizOpsAction(() => createBusinessOperatorReport({ title: 'Operations report' }))
  }

  async function handleCreateBizOpsKpiSnapshot() {
    await runBizOpsAction(() => createBusinessOperatorKpiSnapshot())
  }

  async function handleCreateBizOpsApproval(event) {
    event.preventDefault()
    if (!bizOpsApprovalTitle.trim()) return
    await runBizOpsAction(async () => {
      await createBusinessOperatorApproval({ title: bizOpsApprovalTitle.trim(), kind: bizOpsApprovalKind })
      setBizOpsApprovalTitle('')
      setBizOpsApprovalKind('external_send')
    })
  }

  async function handleDecideBizOpsApproval(approvalId, decision) {
    await runBizOpsAction(() => updateBusinessOperatorApproval(approvalId, decision))
  }

  async function refreshComplianceIntelPanel() {
    const [dashboard, scans] = await Promise.all([
      getComplianceIntelDashboard(),
      getComplianceScans(),
    ])
    setComplianceIntelDashboard(dashboard)
    setComplianceScans(scans?.scans || [])
  }

  async function runComplianceIntelAction(action) {
    setCompIntelBusy(true)
    setComplianceIntelError(null)
    try {
      const value = await action()
      await refreshComplianceIntelPanel()
      return value
    } catch (error) {
      setComplianceIntelError(error.message || 'Compliance action failed')
      return null
    } finally {
      setCompIntelBusy(false)
    }
  }

  async function handleRunComplianceScan(event) {
    event.preventDefault()
    if (!scanContent.trim()) return
    const finding = await runComplianceIntelAction(() => runComplianceScan({ content: scanContent.trim(), label: 'manual scan' }))
    if (finding) {
      setComplianceArtifact({ kind: 'scan', data: finding })
      setScanContent('')
    }
  }

  async function handleReviewContract(event) {
    event.preventDefault()
    if (!contractContent.trim()) return
    const review = await runComplianceIntelAction(() => reviewComplianceContract({ title: 'Contract', content: contractContent.trim() }))
    if (review) {
      setComplianceArtifact({ kind: 'contract', data: review })
      setContractContent('')
    }
  }

  async function handleCreateComplianceChecklist() {
    const checklist = await runComplianceIntelAction(() => createComplianceChecklist({ framework: checklistFramework }))
    if (checklist) setComplianceArtifact({ kind: 'checklist', data: checklist })
  }

  async function handleCreateAuditPackage() {
    const pkg = await runComplianceIntelAction(() => createComplianceAuditPackage({ title: 'Audit package' }))
    if (pkg) setComplianceArtifact({ kind: 'audit_package', data: pkg })
  }

  async function handleCreateCompliancePolicy() {
    await runComplianceIntelAction(() => createCompliancePolicy({ name: 'New policy', category: 'general' }))
  }

  async function refreshBoardPanel() {
    const [dashboard, sessions] = await Promise.all([
      getExecutiveBoardDashboard(),
      getExecutiveBoardSessions(),
    ])
    setBoardDashboard(dashboard)
    setBoardSessions(sessions?.sessions || [])
  }

  async function runBoardAction(action) {
    setBoardBusy(true)
    setBoardError(null)
    try {
      const value = await action()
      await refreshBoardPanel()
      return value
    } catch (error) {
      setBoardError(error.message || 'Executive board action failed')
      return null
    } finally {
      setBoardBusy(false)
    }
  }

  async function handleCreateBoardSession(event) {
    event.preventDefault()
    if (!boardDecision.trim()) return
    const session = await runBoardAction(() => createExecutiveBoardSession({ title: boardDecision.trim(), decision: boardDecision.trim() }))
    if (session) {
      setBoardDecision('')
      setBoardSessionId(session.session_id)
      setBoardArtifact({ kind: 'session', data: session })
    }
  }

  async function handleBoardReview() {
    if (!boardSessionId) return
    const review = await runBoardAction(() => reviewExecutiveBoardSession(boardSessionId))
    if (review) setBoardArtifact({ kind: 'review', data: review })
  }

  async function handleBoardVote() {
    if (!boardSessionId) return
    await runBoardAction(() => voteExecutiveBoardSession(boardSessionId, { role: boardVoteRole, vote: boardVoteValue }))
  }

  async function handleBoardReport() {
    if (!boardSessionId) return
    const report = await runBoardAction(() => reportExecutiveBoardSession(boardSessionId))
    if (report) setBoardArtifact({ kind: 'report', data: report })
  }

  async function refreshInnovationPanel() {
    const [dashboard, research, ideas] = await Promise.all([
      getInnovationDashboard(),
      getInnovationResearch(),
      getInnovationIdeas(),
    ])
    setInnovationDashboard(dashboard)
    setInnovationResearch(research?.research || [])
    setInnovationIdeas(ideas?.ideas || [])
  }

  async function runInnovationAction(action) {
    setInnovationBusy(true)
    setInnovationError(null)
    try {
      await action()
      await refreshInnovationPanel()
    } catch (error) {
      setInnovationError(error.message || 'Innovation lab action failed')
    } finally {
      setInnovationBusy(false)
    }
  }

  async function handleCreateResearch(event) {
    event.preventDefault()
    if (!researchTitle.trim()) return
    await runInnovationAction(async () => {
      await createInnovationResearch({ title: researchTitle.trim() })
      setResearchTitle('')
    })
  }

  async function handleCreateIdea(event) {
    event.preventDefault()
    if (!ideaTitle.trim()) return
    await runInnovationAction(async () => {
      await createInnovationIdea({ title: ideaTitle.trim(), impact: Number(ideaImpact) })
      setIdeaTitle('')
      setIdeaImpact(3)
    })
  }

  async function handleCreateInnovationReport() {
    await runInnovationAction(() => createInnovationReport({ title: 'Innovation report' }))
  }

  async function refreshSimWorldPanel() {
    const [dashboard, scenarios] = await Promise.all([
      getSimWorldDashboard(),
      getSimWorldScenarios(),
    ])
    setSimWorldDashboard(dashboard)
    setSimWorldScenarios(scenarios?.scenarios || [])
  }

  async function runSimWorldAction(action) {
    setSimWorldBusy(true)
    setSimWorldError(null)
    try {
      const value = await action()
      await refreshSimWorldPanel()
      return value
    } catch (error) {
      setSimWorldError(error.message || 'Simulation world action failed')
      return null
    } finally {
      setSimWorldBusy(false)
    }
  }

  async function handleCreateSimWorld(event) {
    event.preventDefault()
    if (!simWorldName.trim()) return
    await runSimWorldAction(async () => {
      await createSimWorldWorld({ name: simWorldName.trim() })
      setSimWorldName('')
    })
  }

  async function handleCreateSimScenario(event) {
    event.preventDefault()
    if (!simScenarioTitle.trim()) return
    await runSimWorldAction(async () => {
      await createSimWorldScenario({ title: simScenarioTitle.trim(), scenario_type: simScenarioType })
      setSimScenarioTitle('')
      setSimScenarioType('business')
    })
  }

  async function handleRunSimScenario(scenarioId) {
    const outcome = await runSimWorldAction(() => runSimWorldScenario(scenarioId))
    if (outcome) setSimWorldOutcome(outcome)
  }

  async function handleSimWorldReport() {
    await runSimWorldAction(() => createSimWorldReport({ title: 'Simulation report' }))
  }

  async function refreshOrgOsPanel() {
    const [dashboard, organizations, members] = await Promise.all([
      getOrgOsDashboard(),
      getOrgOsOrganizations(),
      getOrgOsMembers(),
    ])
    setOrgOsDashboard(dashboard)
    setOrgOsOrganizations(organizations?.organizations || [])
    setOrgOsMembers(members?.members || [])
  }

  async function runOrgOsAction(action) {
    setOrgOsBusy(true)
    setOrgOsError(null)
    try {
      await action()
      await refreshOrgOsPanel()
    } catch (error) {
      setOrgOsError(error.message || 'Organization OS action failed')
    } finally {
      setOrgOsBusy(false)
    }
  }

  async function handleCreateOrg(event) {
    event.preventDefault()
    if (!orgName.trim()) return
    await runOrgOsAction(async () => {
      await createOrgOsOrganization({ name: orgName.trim() })
      setOrgName('')
    })
  }

  async function handleCreateOrgMember(event) {
    event.preventDefault()
    if (!orgMemberName.trim()) return
    await runOrgOsAction(async () => {
      await createOrgOsMember({ display_name: orgMemberName.trim(), role: orgMemberRole })
      setOrgMemberName('')
      setOrgMemberRole('contributor')
    })
  }

  async function handleSetMemberRole(memberId, role) {
    await runOrgOsAction(() => updateOrgOsMember(memberId, { role }))
  }

  async function refreshCompanionPanel() {
    const [dashboard, devices, settings] = await Promise.all([
      getCompanionDashboard(),
      getCompanionDevices(),
      getCompanionSettings(),
    ])
    setCompanionDashboard(dashboard)
    setCompanionDevices(devices?.devices || [])
    if (settings?.companion_mode) setCompanionMode(settings.companion_mode)
  }

  async function runCompanionAction(action) {
    setCompanionBusy(true)
    setCompanionError(null)
    try {
      const value = await action()
      await refreshCompanionPanel()
      return value
    } catch (error) {
      setCompanionError(error.message || 'Companion action failed')
      return null
    } finally {
      setCompanionBusy(false)
    }
  }

  async function handleCreateCompanionDevice(event) {
    event.preventDefault()
    if (!companionDeviceName.trim()) return
    await runCompanionAction(async () => {
      await createCompanionDevice({ name: companionDeviceName.trim(), has_mic: true, has_speaker: true, local_processing: true })
      setCompanionDeviceName('')
    })
  }

  async function handleSetCompanionMode(mode) {
    setCompanionMode(mode)
    await runCompanionAction(() => updateCompanionSettings({ companion_mode: mode }))
  }

  async function handleCompanionReadiness(deviceId) {
    const check = await runCompanionAction(() => createCompanionReadinessCheck({ device_id: deviceId }))
    if (check) setCompanionReadiness(check)
  }

  async function handleCreateCompanionSession() {
    await runCompanionAction(() => createCompanionSession({ title: 'Companion session' }))
  }

  async function refreshOperatingLayerPanel() {
    const dashboard = await getOperatingLayerDashboard()
    setOperatingLayerDashboard(dashboard)
  }

  async function runOperatingLayerAction(action) {
    setOperatingLayerBusy(true)
    setOperatingLayerError(null)
    try {
      const value = await action()
      await refreshOperatingLayerPanel()
      return value
    } catch (error) {
      setOperatingLayerError(error.message || 'Operating layer action failed')
      return null
    } finally {
      setOperatingLayerBusy(false)
    }
  }

  async function handleOperatingLayerSnapshot() {
    const snapshot = await runOperatingLayerAction(() => createOperatingLayerSnapshot())
    if (snapshot) setOperatingLayerArtifact({ kind: 'snapshot', data: snapshot })
  }

  async function handleOperatingLayerRecommendations() {
    const rec = await runOperatingLayerAction(() => createOperatingLayerRecommendations())
    if (rec) setOperatingLayerArtifact({ kind: 'recommendations', data: rec })
  }

  async function handleOperatingLayerReport() {
    const report = await runOperatingLayerAction(() => createOperatingLayerReport())
    if (report) setOperatingLayerArtifact({ kind: 'report', data: report })
  }

  async function refreshApprovalsCenter() {
    const [items, summary] = await Promise.all([
      getApprovalsCenter(),
      getApprovalsCenterSummary(),
    ])
    setApprovalsCenter(items?.items || [])
    setApprovalsCenterSummary(summary)
  }

  async function refreshHealthMonitor() {
    const dashboard = await getHealthMonitorDashboard()
    setHealthDashboard(dashboard)
  }

  async function refreshUsageLedger() {
    const summary = await getUsageLedgerSummary(workspaceId)
    setUsageSummary(summary)
  }

  async function refreshRetrieval() {
    const summary = await getRetrievalSummary(workspaceId)
    setRetrievalSummary(summary)
  }

  async function refreshEvalHarness() {
    const [summary, suites] = await Promise.all([getEvalSummary(), getEvalSuites()])
    setEvalSummary(summary)
    setEvalSuites(suites?.suites || [])
  }

  async function refreshPlaybooks() {
    const [summary, list] = await Promise.all([getPlaybooksSummary(), getPlaybooks()])
    setPlaybooksSummary(summary)
    setPlaybooks(list?.playbooks || [])
  }

  async function refreshOpLayer2() {
    const dashboard = await getOperatingLayerV2Dashboard()
    setOpLayer2(dashboard)
  }

  async function refreshWsTemplates() {
    const [summary, list] = await Promise.all([getWorkspaceTemplatesSummary(), getWorkspaceTemplates()])
    setWsTemplatesSummary(summary)
    setWsTemplates(list?.templates || [])
  }

  async function refreshScheduled() {
    const [summary, list] = await Promise.all([getScheduledTasksSummary(), getScheduledTasks()])
    setScheduledSummary(summary)
    setScheduledTasks(list?.tasks || [])
  }

  async function refreshDataExport() {
    const summary = await getDataExportSummary()
    setDataExportSummary(summary)
  }

  async function refreshOs2() {
    const dashboard = await getOs2Dashboard()
    setOs2Dashboard(dashboard)
  }

  async function refreshMasterPanel() {
    try {
      const [summary, capabilities] = await Promise.all([getMasterAgentSummary(), getMasterAgentCapabilities()])
      setMasterSummary(summary)
      setMasterCapabilities(capabilities)
    } catch {
      // Master Agent summary is best-effort; ignore transient errors.
    }
  }

  async function refreshGitIntel() {
    try {
      const [status, repos] = await Promise.all([getGitStatus(), getGitRepositories(workspaceId)])
      setGitStatus(status)
      setGitRepos(repos.repositories || [])
    } catch {
      // best-effort
    }
  }

  async function runGitDiscover(optIn) {
    setGitBusy(true)
    try {
      await discoverGitRepos(optIn ? gitPath : null, optIn, workspaceId)
      await refreshGitIntel()
    } finally {
      setGitBusy(false)
    }
  }

  async function runGitRead(which) {
    if (!gitPath.trim()) return
    setGitReadBusy(true)
    try {
      if (which === 'log') {
        setGitLog(await getGitLog(gitPath, 20))
      } else {
        setGitBranches(await getGitBranchList(gitPath))
      }
    } finally {
      setGitReadBusy(false)
    }
  }

  async function refreshAgentStudio() {
    try {
      const [tpl, list] = await Promise.all([getStudioTemplates(), listAgentProfiles()])
      setStudioTemplates(tpl.templates || [])
      setAgentProfiles(list.agents || [])
    } catch {
      // best-effort
    }
  }

  function applyAgentTemplate(t) {
    setAgentName(t.name)
    setAgentRole(t.role)
    setAgentTone(t.personality?.tone || 'professional')
  }

  async function refreshVoiceConsole() {
    try {
      const [status, settings, events] = await Promise.all([
        getVoiceStatus(), getVoiceSettings(workspaceId || 'global'), getVoiceEvents(workspaceId || 'global', 20),
      ])
      setVoiceStatus(status)
      if (settings) setVoiceSettings(settings)
      setVoiceEvents(events?.events || [])
    } catch {
      // best-effort
    }
  }

  async function saveVoiceSettings(patch) {
    const next = { ...(voiceSettings || {}), ...patch, workspace_id: workspaceId || 'global' }
    setVoiceSettings(next) // optimistic
    try {
      const saved = await updateVoiceSettings({ workspace_id: workspaceId || 'global', ...patch })
      setVoiceSettings(saved)
    } catch {
      // keep optimistic value; backend best-effort
    }
  }

  async function clearVoiceHistory() {
    try {
      await clearVoiceEvents(workspaceId || 'global')
      setVoiceEvents([])
    } catch {
      // best-effort
    }
  }

  async function refreshWorkflows() {
    try {
      const [tpl, runs, eff] = await Promise.all([getWorkflowTemplates(), listWorkflowRuns(), getWorkflowEffects()])
      setWorkflowTemplates(tpl?.templates || [])
      setWorkflowRuns(runs?.runs || [])
      setWorkflowEffects(eff?.effects || [])
    } catch {
      // best-effort
    }
  }

  async function runWorkflowAction(fn) {
    setDurableBusy(true)
    try {
      await fn()
      await refreshWorkflows()
    } finally {
      setDurableBusy(false)
    }
  }

  async function refreshMarketplaceHub(kind = marketplaceKind) {
    try {
      const data = await getMarketplaceListings(kind || undefined)
      setMarketplaceListings(data?.listings || [])
    } catch {
      // best-effort
    }
  }

  async function handleInstallListing(listing) {
    setMarketplaceBusy(true)
    setMarketplaceNote('')
    try {
      const res = await installMarketplaceListing(listing.listing_id)
      const where = res.kind === 'agent' ? 'Agent Studio' : 'Durable Workflows'
      setMarketplaceNote(`Installed “${res.installed?.name}” into ${where}.`)
      await refreshMarketplaceHub()
    } catch {
      setMarketplaceNote('Install failed — is the backend running?')
    } finally {
      setMarketplaceBusy(false)
    }
  }

  async function handleUnpublishListing(listingId) {
    setMarketplaceBusy(true)
    try {
      await unpublishMarketplaceListing(listingId)
      await refreshMarketplaceHub()
    } catch {
      setMarketplaceNote('Featured starter listings cannot be removed.')
    } finally {
      setMarketplaceBusy(false)
    }
  }

  async function refreshDesignAgent() {
    try {
      setDesignStatus(await getDesignAgentStatus())
    } catch {
      // best-effort
    }
  }

  function onDesignFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setDesignImageName(file.name)
    const reader = new FileReader()
    reader.onload = () => setDesignImage(reader.result) // data URL
    reader.readAsDataURL(file)
  }

  function toggleDesignLens(lens) {
    setDesignLenses((cur) => (cur.includes(lens) ? cur.filter((l) => l !== lens) : [...cur, lens]))
  }

  async function handleAnalyzeDesign() {
    if (!designImage) return
    setDesignBusy(true)
    setDesignResult(null)
    try {
      const res = await analyzeDesign({
        image: designImage,
        analyses: designLenses,
        context: designContext,
        allowLive: designLive && designStatus?.key_configured,
      })
      setDesignResult(res)
    } catch {
      setDesignResult({ mode: 'error', sections: [], note: 'Analysis failed — is the backend running?' })
    } finally {
      setDesignBusy(false)
    }
  }

  async function handleRepoSearch(q) {
    const query = (q ?? repoQuery).trim()
    if (!query) return
    if (q) setRepoQuery(q)
    setRepoBusy(true)
    try {
      setRepoResult(await searchRepos(query, { limit: 8, sort: 'best' }))
    } catch {
      setRepoResult({ count: 0, results: [], related_topics: [], note: 'Search failed — is the backend running?' })
    } finally {
      setRepoBusy(false)
    }
  }

  async function handleCreateAgent() {
    if (!agentName.trim()) return
    setAgentBusy(true)
    try {
      await createAgentProfile({ name: agentName, role: agentRole, personality: { tone: agentTone, verbosity: 'medium' } })
      setAgentName(''); setAgentRole('')
      await refreshAgentStudio()
    } finally {
      setAgentBusy(false)
    }
  }

  async function handleTestAgent(agentId) {
    if (!agentTestPrompt.trim()) return
    setAgentBusy(true)
    try {
      setAgentTestResult(await testAgentProfile(agentId, agentTestPrompt))
    } finally {
      setAgentBusy(false)
    }
  }

  async function handleAgentAction(agentId, action) {
    setAgentBusy(true)
    try {
      if (action === 'evaluate') await evaluateAgentProfile(agentId)
      else if (action === 'publish') await publishAgentProfile(agentId)
      else if (action === 'duplicate') await duplicateAgentProfile(agentId)
      else if (action === 'preview') { setAgentTestResult({ agent_id: agentId, simulated_response: (await getAgentPreview(agentId)).preview }); return }
      await refreshAgentStudio()
    } finally {
      setAgentBusy(false)
    }
  }

  async function handleMasterRouteFeedback(runId, correct) {
    try {
      await sendMasterRouteFeedback(runId, correct)
      await refreshMasterPanel()
    } catch {
      // best-effort feedback
    }
  }

  async function runGlobalSearch(event) {
    if (event) event.preventDefault()
    const q = globalSearchQuery.trim()
    if (!q) return
    setGlobalSearchBusy(true)
    try {
      const [results, sources] = await Promise.all([
        globalSearch(q, { workspaceId }),
        globalSearchSources ? Promise.resolve(globalSearchSources) : getGlobalSearchSources(),
      ])
      setGlobalSearchResults(results)
      setGlobalSearchSources(sources)
    } catch (err) {
      setGlobalSearchResults({ error: err.message, results: [] })
    } finally {
      setGlobalSearchBusy(false)
    }
  }

  function useSearchResultAsContext(result) {
    const seed = `Context from ${result.label} — "${result.title}": ${result.preview}\n\n`
    setInput((current) => seed + (current || ''))
    setDeveloperMode(true)
    composerRef.current?.focus()
  }

  async function refreshActivity(type = activityType) {
    setActivityBusy(true)
    try {
      const data = await getActivityTimeline({ workspaceId, types: type || undefined, limit: 40 })
      setActivityTimeline(data)
    } catch {
      setActivityTimeline({ events: [], event_count: 0 })
    } finally {
      setActivityBusy(false)
    }
  }

  async function refreshHome() {
    try {
      setDashboardHome(await getDashboardHome(workspaceId))
    } catch {
      // best-effort
    }
  }

  async function refreshFeatures() {
    try {
      setFeaturesData(await getFeatures({ q: featuresQuery || undefined, status: featuresStatus || undefined }))
    } catch {
      // best-effort
    }
  }

  async function handleTryFeature(key) {
    try {
      const data = await tryFeature(key)
      setCopied(data.launch_note || `Open ${data.open_route}`)
      setTimeout(() => setCopied(''), 3500)
    } catch {
      // best-effort
    }
  }

  async function refreshDemo() {
    try {
      const [summary, script] = await Promise.all([getDemoSummary(), demoScript ? Promise.resolve(demoScript) : getDemoScript()])
      setDemoSummary(summary)
      setDemoScript(script)
    } catch {
      // best-effort
    }
  }

  async function handleDemoSeed() {
    setDemoBusy(true)
    try {
      const data = await seedDemoData()
      setCopied(`Seeded demo workspace (${data.seeded_count} records).`)
      setTimeout(() => setCopied(''), 3500)
      await refreshDemo()
    } finally {
      setDemoBusy(false)
    }
  }

  async function handleDemoReset() {
    setDemoBusy(true)
    try {
      const data = await resetDemoData()
      setCopied(`Reset demo data — removed ${data.removed_count} demo record(s). User data untouched.`)
      setTimeout(() => setCopied(''), 4000)
      await refreshDemo()
    } finally {
      setDemoBusy(false)
    }
  }

  async function refreshSettings() {
    try {
      setSettingsData(await getSettings())
    } catch {
      // best-effort
    }
  }

  async function refreshProviderControl() {
    try {
      setProviderControl(await getProviderControl())
    } catch {
      // best-effort
    }
  }

  async function refreshInbox() {
    setInboxBusy(true)
    try {
      await generateNotificationsInbox()
      setInboxData(await getNotificationsInbox())
    } catch {
      // best-effort
    } finally {
      setInboxBusy(false)
    }
  }

  async function handleInboxResolve(id) {
    try {
      await resolveNotificationInbox(id)
      setInboxData(await getNotificationsInbox())
    } catch {
      // best-effort
    }
  }

  async function refreshWsOs() {
    if (!workspaceId) { setWsOsDashboard({ error: 'No active workspace selected.' }); return }
    try {
      setWsOsDashboard(await getWorkspaceOsDashboard(workspaceId))
    } catch {
      setWsOsDashboard(null)
    }
  }

  async function refreshAgentQuality() {
    try {
      setAgentQuality(await getAgentQuality())
    } catch {
      // best-effort
    }
  }

  async function refreshProductivity() {
    try {
      setProductivityBrain(await getProductivityBrain(workspaceId))
    } catch {
      // best-effort
    }
  }

  async function runCodeAnalyze() {
    if (!codeIntelText.trim()) return
    setCodeIntelBusy(true)
    try {
      setCodeIntelResult(await analyzeCode(codeIntelText))
    } catch (err) {
      setCodeIntelResult({ error: err.message })
    } finally {
      setCodeIntelBusy(false)
    }
  }

  async function runResearchAgent2(mode) {
    if (!researchAgentText.trim()) return
    setResearchAgentBusy(true)
    try {
      const data = mode === 'bias'
        ? await researchAgentBias(researchAgentText)
        : mode === 'brief'
          ? await researchAgentBrief(researchAgentText, [])
          : await researchAgentClaims(researchAgentText)
      setResearchAgentResult({ mode, data })
    } catch (err) {
      setResearchAgentResult({ error: err.message })
    } finally {
      setResearchAgentBusy(false)
    }
  }

  async function refreshBizIntel2() {
    setBizIntelBusy(true)
    try {
      setBizIntel2(await getBusinessIntelDashboard(workspaceId))
    } catch (err) {
      setBizIntel2({ error: err.message })
    } finally {
      setBizIntelBusy(false)
    }
  }

  async function downloadBizIntelReport() {
    const report = await getBusinessIntelReport(workspaceId)
    downloadFile('business-intelligence-report.md', report.content || JSON.stringify(report, null, 2), 'text/markdown')
  }

  async function runMeetingIntel2(mode) {
    if (!meetingIntelText.trim()) return
    setMeetingIntelBusy(true)
    try {
      const data = mode === 'goal'
        ? await meetingTranscriptToGoal(meetingIntelText, 'Meeting follow-up goal')
        : await analyzeMeetingTranscript(meetingIntelText)
      setMeetingIntelResult({ mode, data })
    } catch (err) {
      setMeetingIntelResult({ error: err.message })
    } finally {
      setMeetingIntelBusy(false)
    }
  }

  async function runCollab2(event) {
    if (event) event.preventDefault()
    if (!collabTopic.trim()) return
    setCollabBusy(true)
    try {
      setCollabResult(await analyzeCollaboration(collabTopic, [
        { role: collabRoleA, position: collabPositionA },
        { role: collabRoleB, position: collabPositionB },
      ]))
    } catch (err) {
      setCollabResult({ error: err.message })
    } finally {
      setCollabBusy(false)
    }
  }

  async function refreshPerm3() {
    setPermBusy(true)
    try {
      setPermProfiles(await getPermissionProfiles())
    } catch (err) {
      setPermProfiles({ error: err.message })
    } finally {
      setPermBusy(false)
    }
  }

  async function createPermProfile() {
    setPermBusy(true)
    try {
      await createPermissionProfile({
        name: `Approval gate ${Date.now().toString().slice(-4)}`,
        action_pattern: permAction || '*',
        effect: 'require_approval',
        risk_level: 'high',
      })
      await refreshPerm3()
    } finally {
      setPermBusy(false)
    }
  }

  async function deletePermProfile(profileId) {
    setPermBusy(true)
    try {
      await deletePermissionProfile(profileId)
      await refreshPerm3()
    } finally {
      setPermBusy(false)
    }
  }

  async function runPermEval() {
    if (!permAction.trim()) return
    setPermBusy(true)
    try {
      setPermEval(await evaluatePermission({ action: permAction, risk_level: 'high' }))
    } catch (err) {
      setPermEval({ error: err.message })
    } finally {
      setPermBusy(false)
    }
  }

  async function refreshGovConsole() {
    setGovBusy(true)
    try {
      setGovConsole(await getGovernanceConsoleDashboard())
    } catch (err) {
      setGovConsole({ error: err.message })
    } finally {
      setGovBusy(false)
    }
  }

  async function downloadGovConsole(format = 'markdown') {
    const report = await getGovernanceConsoleReport(format)
    downloadFile(`governance-console-report.${format === 'json' ? 'json' : 'md'}`, report.content || JSON.stringify(report, null, 2), format === 'json' ? 'application/json' : 'text/markdown')
  }

  async function refreshDataManager() {
    setDataManagerBusy(true)
    try {
      const [browse, usage, cleanup] = await Promise.all([
        getDataManagerBrowse(),
        getDataManagerUsage(),
        getDataManagerCleanup(),
      ])
      setDataManager({ browse, usage, cleanup })
      const collections = browse?.collections || []
      if (collections.length && !collections.some((item) => item.collection === dataManagerCollection)) {
        setDataManagerCollection(collections[0].collection)
      }
    } catch (err) {
      setDataManager({ error: err.message })
    } finally {
      setDataManagerBusy(false)
    }
  }

  async function runDataManagerPreview() {
    if (!dataManagerCollection.trim()) return
    setDataManagerBusy(true)
    try {
      setDataManagerPreview(await previewDataRedaction(dataManagerCollection))
    } catch (err) {
      setDataManagerPreview({ error: err.message })
    } finally {
      setDataManagerBusy(false)
    }
  }

  async function runImportCenter(mode) {
    if (!importCenterContent.trim()) return
    setImportCenterBusy(true)
    try {
      const result = mode === 'commit'
        ? await commitImport(importCenterKind, importCenterContent, workspaceId)
        : await previewImport(importCenterKind, importCenterContent)
      setImportCenterResult(result)
      setImportCenterRecords(await getImportRecords(importCenterKind))
    } catch (err) {
      setImportCenterResult({ error: err.message })
    } finally {
      setImportCenterBusy(false)
    }
  }

  async function runExportCenter2(mode) {
    setExportCenterBusy(true)
    try {
      const result = mode === 'package'
        ? await exportCenterPackage([exportCenterKind], exportCenterFormat, workspaceId)
        : mode === 'case'
          ? await getExportCenterCaseStudy()
          : await exportCenterExport(exportCenterKind, exportCenterFormat, workspaceId)
      setExportCenterResult(result)
      const content = result.content || result.package_content || JSON.stringify(result, null, 2)
      downloadFile(`evolveagent-${mode}.${exportCenterFormat === 'json' ? 'json' : 'md'}`, content, exportCenterFormat === 'json' ? 'application/json' : 'text/markdown')
    } catch (err) {
      setExportCenterResult({ error: err.message })
    } finally {
      setExportCenterBusy(false)
    }
  }

  async function refreshPluginMarket() {
    setPluginBusy(true)
    try {
      const [catalog, activity] = await Promise.all([
        getPluginMarketplaceCatalog(),
        getPluginMarketplaceActivity(),
      ])
      setPluginMarket(catalog)
      setPluginActivity(activity)
    } catch (err) {
      setPluginMarket({ error: err.message })
    } finally {
      setPluginBusy(false)
    }
  }

  async function registerPluginMarket(event) {
    if (event) event.preventDefault()
    if (!pluginName.trim()) return
    setPluginBusy(true)
    try {
      await registerMarketplacePlugin({ name: pluginName, description: 'Registered from Developer Mode', permissions: ['read'] })
      setPluginName('')
      await refreshPluginMarket()
    } finally {
      setPluginBusy(false)
    }
  }

  async function runPluginAction(pluginId, action, enabled) {
    setPluginBusy(true)
    try {
      if (action === 'toggle') await toggleMarketplacePlugin(pluginId, enabled)
      if (action === 'test') await testMarketplacePlugin(pluginId)
      await refreshPluginMarket()
    } finally {
      setPluginBusy(false)
    }
  }

  async function refreshIntegrationHub2() {
    setIntegrationBusy(true)
    try {
      setIntegrationHub2(await getIntegrationHubCards())
    } catch (err) {
      setIntegrationHub2({ error: err.message })
    } finally {
      setIntegrationBusy(false)
    }
  }

  async function runIntegrationDry(integrationId) {
    setIntegrationBusy(true)
    try {
      const dryRun = await dryRunIntegration(integrationId)
      setIntegrationHub2((current) => ({ ...(current || {}), dry_run: dryRun }))
    } finally {
      setIntegrationBusy(false)
    }
  }

  async function refreshQaCenter2() {
    setQaBusy(true)
    try {
      const [dashboard, matrix] = await Promise.all([
        getQaCenterDashboard(),
        getQaCenterMatrix(),
      ])
      setQaCenter(dashboard)
      setQaMatrix(matrix)
    } catch (err) {
      setQaCenter({ error: err.message })
    } finally {
      setQaBusy(false)
    }
  }

  async function recordQaItem(featureKey, status) {
    setQaBusy(true)
    try {
      await recordQaStatus(featureKey, status, `Marked ${status} from Developer Mode`)
      await refreshQaCenter2()
    } finally {
      setQaBusy(false)
    }
  }

  async function refreshReleaseMgr() {
    setReleaseBusy(true)
    try {
      const [dashboard, changelog] = await Promise.all([
        getReleaseManagerDashboard(),
        getReleaseManagerChangelog(),
      ])
      setReleaseMgr({ dashboard, changelog })
    } catch (err) {
      setReleaseMgr({ error: err.message })
    } finally {
      setReleaseBusy(false)
    }
  }

  async function runReleaseMgr(mode) {
    setReleaseBusy(true)
    try {
      const result = mode === 'notes'
        ? await generateReleaseNotes('v90.0', ['Developer Mode panels connected', 'Launch console ready'])
        : await generatePrSummary('Developer-Mode panels for v77-v90', ['Research, BI, meetings, governance, QA, release, and launch panels'])
      setReleaseResult(result)
      downloadFile(`release-manager-${mode}.md`, result.content || JSON.stringify(result, null, 2), 'text/markdown')
    } catch (err) {
      setReleaseResult({ error: err.message })
    } finally {
      setReleaseBusy(false)
    }
  }

  async function refreshLaunchConsole() {
    setLaunchBusy(true)
    try {
      const [dashboard, report] = await Promise.all([
        getLaunchConsoleDashboard(),
        getLaunchConsoleReport(),
      ])
      setLaunchConsole(dashboard)
      setLaunchReport(report)
    } catch (err) {
      setLaunchConsole({ error: err.message })
    } finally {
      setLaunchBusy(false)
    }
  }

  async function downloadLaunchReport() {
    const report = launchReport || await getLaunchConsoleReport()
    downloadFile('evolveagent-launch-report.md', report.content || JSON.stringify(report, null, 2), 'text/markdown')
    setLaunchReport(report)
  }

  async function runDocContractRisk() {
    if (!docIntelText.trim()) return
    setDocIntelBusy(true)
    try {
      const r = await docContractRisk(docIntelText)
      setDocIntelResult({ mode: 'contract', data: r })
    } catch (err) {
      setDocIntelResult({ error: err.message })
    } finally {
      setDocIntelBusy(false)
    }
  }

  async function runDocAts() {
    if (!docIntelText.trim()) return
    setDocIntelBusy(true)
    try {
      const [resume, ...kw] = docIntelText.split('---')
      const keywords = (kw.join('---') || '').split(',').map((s) => s.trim()).filter(Boolean)
      const r = await docAtsScore(resume, keywords)
      setDocIntelResult({ mode: 'ats', data: r })
    } catch (err) {
      setDocIntelResult({ error: err.message })
    } finally {
      setDocIntelBusy(false)
    }
  }

  async function runWorkflowRec(event) {
    if (event) event.preventDefault()
    const goal = workflowGoal.trim()
    if (!goal) return
    setWorkflowBusy(true)
    try {
      setWorkflowRec(await recommendWorkflow(goal))
    } catch (err) {
      setWorkflowRec({ error: err.message })
    } finally {
      setWorkflowBusy(false)
    }
  }

  async function runContextPlan(event) {
    if (event) event.preventDefault()
    const q = contextQuery.trim()
    if (!q) return
    setContextBusy(true)
    try {
      setContextPlan(await planContext(q, { workspaceId }))
    } catch (err) {
      setContextPlan({ error: err.message })
    } finally {
      setContextBusy(false)
    }
  }

  async function handleCapabilityMode(capability, mode) {
    setProviderBusy(true)
    try {
      await updateProviderControl({ capability_modes: { [capability]: mode } })
      await refreshProviderControl()
    } finally {
      setProviderBusy(false)
    }
  }

  async function handleSettingToggle(category, key, value) {
    setSettingsBusy(true)
    try {
      const data = await updateSettings({ [category]: { [key]: value } })
      setSettingsData((current) => ({ ...(current || {}), settings: data.settings }))
    } finally {
      setSettingsBusy(false)
    }
  }

  async function handleSettingsReset() {
    setSettingsBusy(true)
    try {
      const data = await resetSettings()
      setSettingsData((current) => ({ ...(current || {}), settings: data.settings }))
    } finally {
      setSettingsBusy(false)
    }
  }

  async function handleDemoCaseStudy() {
    const data = await getDemoCaseStudy()
    const blob = new Blob([data.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'evolveagent-case-study.md'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  async function handleActivityExport() {
    const data = await exportActivityTimeline('markdown')
    const blob = new Blob([data.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `evolveagent-activity-${new Date().toISOString().slice(0, 10)}.md`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  async function handleOs2Snapshot() {
    setOs2Busy(true)
    try {
      await createOs2Snapshot()
      await refreshOs2()
    } finally {
      setOs2Busy(false)
    }
  }

  async function handleOs2Report() {
    setOs2Busy(true)
    try {
      const report = await createOs2Report()
      setOs2Report(report)
      await refreshOs2()
    } finally {
      setOs2Busy(false)
    }
  }

  async function handleExportDownload() {
    setDataExportBusy(true)
    try {
      const bundle = await exportDataBundle()
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `evolveagent-backup-${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
      await refreshDataExport()
    } finally {
      setDataExportBusy(false)
    }
  }

  async function handleImportBundle(event) {
    event.preventDefault()
    if (!importText.trim()) return
    setDataExportBusy(true)
    try {
      const bundle = JSON.parse(importText)
      const result = await importDataBundle(bundle)
      setImportResult(result)
      setImportText('')
      await refreshDataExport()
    } catch (err) {
      setImportResult({ error: err.message })
    } finally {
      setDataExportBusy(false)
    }
  }

  async function runScheduledAction(action) {
    setScheduledBusy(true)
    try {
      await action()
      await refreshScheduled()
    } finally {
      setScheduledBusy(false)
    }
  }

  async function handleCreateScheduled(event) {
    event.preventDefault()
    if (!scheduledName.trim()) return
    await runScheduledAction(async () => {
      await createScheduledTask({ name: scheduledName.trim(), schedule: scheduledSchedule, action_type: 'plan' })
      setScheduledName('')
    })
  }

  async function handleTriggerScheduled(taskId) {
    await runScheduledAction(() => triggerScheduledTask(taskId))
  }

  async function handleToggleScheduled(taskId, enabled) {
    await runScheduledAction(() => toggleScheduledTask(taskId, enabled))
  }

  async function runWsTemplateAction(action) {
    setWsTemplateBusy(true)
    try {
      await action()
      await refreshWsTemplates()
    } finally {
      setWsTemplateBusy(false)
    }
  }

  async function handleCreateWsTemplate(event) {
    event.preventDefault()
    if (!wsTemplateName.trim()) return
    await runWsTemplateAction(async () => {
      await createWorkspaceTemplate({ name: wsTemplateName.trim(), default_tags: [], preset: {} })
      setWsTemplateName('')
    })
  }

  async function handleInstantiateWsTemplate(templateId) {
    await runWsTemplateAction(() => instantiateWorkspaceTemplate(templateId, {}))
    await refreshWorkspaces?.()
  }

  async function refreshNotifications() {
    const [summary, list] = await Promise.all([getNotificationsSummary(), getNotifications(true)])
    setNotificationsSummary(summary)
    setNotifications(list?.notifications || [])
  }

  async function runNotifAction(action) {
    setNotifBusy(true)
    try {
      await action()
      await refreshNotifications()
    } finally {
      setNotifBusy(false)
    }
  }

  async function handleGenerateNotifications() {
    await runNotifAction(() => generateNotifications())
  }

  async function handleAckNotification(notifId) {
    await runNotifAction(() => acknowledgeNotification(notifId))
  }

  async function runOpLayer2Action(action) {
    setOpLayer2Busy(true)
    try {
      const value = await action()
      await refreshOpLayer2()
      return value
    } finally {
      setOpLayer2Busy(false)
    }
  }

  async function handleOpLayer2Snapshot() {
    await runOpLayer2Action(() => createOperatingLayerV2Snapshot())
  }

  async function handleOpLayer2Report() {
    const report = await runOpLayer2Action(() => createOperatingLayerV2Report())
    if (report) setOpLayer2Report(report)
  }

  async function runPlaybookAction(action) {
    setPlaybookBusy(true)
    try {
      const value = await action()
      await refreshPlaybooks()
      return value
    } finally {
      setPlaybookBusy(false)
    }
  }

  async function handleCreateSamplePlaybook() {
    await runPlaybookAction(() => createPlaybook({
      name: 'Sample release playbook',
      steps: [
        { title: 'Draft changelog', step_type: 'plan', detail: 'Summarize changes.' },
        { title: 'Notify reviewers', step_type: 'note', detail: 'Ping the team.' },
        { title: 'Publish release', step_type: 'approval_required', detail: 'Risky — needs approval.' },
      ],
    }))
  }

  async function handleRunPlaybook(playbookId) {
    const run = await runPlaybookAction(() => runPlaybook(playbookId))
    if (run) setPlaybookRun(run)
  }

  async function runEvalAction(action) {
    setEvalBusy(true)
    try {
      const value = await action()
      await refreshEvalHarness()
      return value
    } finally {
      setEvalBusy(false)
    }
  }

  async function handleCreateSampleEvalSuite() {
    await runEvalAction(() => createEvalSuite({
      name: 'Sample quality suite',
      cases: [
        { prompt: 'Explain governance', reference_answer: 'Governance logs every action and blocks risky ones.', expected_keywords: ['governance', 'logs', 'blocks'] },
        { prompt: 'Explain memory', reference_answer: 'Memory is scored and retrieved locally.', expected_keywords: ['memory', 'local', 'scored'] },
      ],
    }))
  }

  async function handleRunEvalSuite(suiteId) {
    const run = await runEvalAction(() => runEvalSuite(suiteId))
    if (run) setEvalRun(run)
  }

  async function runRetrievalAction(action) {
    setRetrievalBusy(true)
    try {
      const value = await action()
      await refreshRetrieval()
      return value
    } finally {
      setRetrievalBusy(false)
    }
  }

  async function handleIndexRetrievalDoc(event) {
    event.preventDefault()
    if (!retrievalDocText.trim()) return
    await runRetrievalAction(async () => {
      await indexRetrievalDocument({ workspace_id: workspaceId, title: 'Note', content: retrievalDocText.trim() })
      setRetrievalDocText('')
    })
  }

  async function handleQueryRetrieval(event) {
    event.preventDefault()
    if (!retrievalQuery.trim()) return
    const result = await runRetrievalAction(() => queryRetrieval({ workspace_id: workspaceId, query: retrievalQuery.trim() }))
    if (result) setRetrievalResults(result.results || [])
  }

  async function runUsageAction(action) {
    setUsageBusy(true)
    try {
      await action()
      await refreshUsageLedger()
    } finally {
      setUsageBusy(false)
    }
  }

  async function handleSetUsageBudget(event) {
    event.preventDefault()
    if (!usageBudgetInput.trim()) return
    await runUsageAction(async () => {
      await setUsageBudget({ workspace_id: workspaceId, monthly_limit: Number(usageBudgetInput) })
      setUsageBudgetInput('')
    })
  }

  async function handleRecordSampleUsage() {
    await runUsageAction(() => recordUsageEntry({ workspace_id: workspaceId, capability: 'text', units: 1000 }))
  }

  async function handleCreateHealthSnapshot() {
    setHealthBusy(true)
    try {
      await createHealthSnapshot()
      await refreshHealthMonitor()
    } finally {
      setHealthBusy(false)
    }
  }

  async function runAcAction(action) {
    setAcBusy(true)
    setAcError(null)
    try {
      await action()
      await refreshApprovalsCenter()
    } catch (error) {
      setAcError(error.message || 'Approvals action failed')
    } finally {
      setAcBusy(false)
    }
  }

  async function handleApproveCenter(source, itemId) {
    await runAcAction(() => approveCenterItem(source, itemId))
  }

  async function handleRejectCenter(source, itemId) {
    await runAcAction(() => rejectCenterItem(source, itemId))
  }

  async function refreshMcpPanel() {
    const [summary, connectors, templates] = await Promise.all([
      getMcpSummary(),
      getMcpConnectors(),
      getMcpTemplates(),
    ])
    setMcpSummary(summary)
    setMcpConnectors(connectors?.connectors || [])
    setMcpTemplates(templates?.templates || [])
    const [execSummary, executions, adapterStatus] = await Promise.all([
      getMcpExecutionSummary(),
      getMcpExecutions(),
      getMcpAdapterStatus(),
    ])
    setMcpExecSummary(execSummary)
    setMcpExecutions(executions?.requests || [])
    setMcpAdapterStatus(adapterStatus)
    const [inbox, inboxSummary] = await Promise.all([
      getMcpInbox(),
      getMcpInboxSummary(),
    ])
    setMcpInbox(inbox?.items || [])
    setMcpInboxSummary(inboxSummary)
    const policies = await getMcpPolicies()
    setMcpPolicies(policies?.policies || [])
    const [audit, auditSummary] = await Promise.all([
      getMcpAudit(),
      getMcpAuditSummary(),
    ])
    setMcpAudit(audit?.events || [])
    setMcpAuditSummary(auditSummary)
    const [secrets, secretsSummary] = await Promise.all([
      getMcpSecrets(),
      getMcpSecretsSummary(),
    ])
    setMcpSecrets(secrets?.refs || [])
    setMcpSecretsSummary(secretsSummary)
  }

  async function handleRegisterMcpSecret(event) {
    event.preventDefault()
    if (!mcpSecretKey.trim()) return
    await runMcpAction(async () => {
      await registerMcpSecret({ key_name: mcpSecretKey.trim() })
      setMcpSecretKey('')
    })
  }

  async function handleRotateMcpSecret(refId) {
    await runMcpAction(() => rotateMcpSecret(refId))
  }

  async function handleReplayMcpRequest(event) {
    event.preventDefault()
    if (!mcpReplayId.trim()) return
    const result = await runMcpAction(() => replayMcpRequest(mcpReplayId.trim()))
    if (result) setMcpReplayResult(result)
  }

  async function handleApproveInboxItem(itemId) {
    await runMcpAction(() => approveMcpInboxItem(itemId))
  }

  async function handleRejectInboxItem(itemId) {
    await runMcpAction(() => rejectMcpInboxItem(itemId))
  }

  async function handleCreateMcpPolicy(event) {
    event.preventDefault()
    if (!mcpPolicyName.trim()) return
    await runMcpAction(async () => {
      await createMcpPolicy({
        name: mcpPolicyName.trim(),
        connector_slug: mcpPolicySlug.trim() || '*',
        action: mcpPolicyAction.trim() || '*',
      })
      setMcpPolicyName('')
      setMcpPolicySlug('*')
      setMcpPolicyAction('*')
    })
  }

  async function handleToggleMcpPolicy(policyId, enabled) {
    await runMcpAction(() => updateMcpPolicy(policyId, { enabled }))
  }

  async function runMcpAction(action) {
    setMcpBusy(true)
    setMcpError(null)
    try {
      const value = await action()
      await refreshMcpPanel()
      return value
    } catch (error) {
      setMcpError(error.message || 'MCP action failed')
      return null
    } finally {
      setMcpBusy(false)
    }
  }

  async function handleAddMcpConnector() {
    await runMcpAction(() => createMcpConnector({ slug: mcpTemplateSlug }))
  }

  async function handleEnableMcpConnector(connectorId) {
    await runMcpAction(() => enableMcpConnector(connectorId))
  }

  async function handleDisableMcpConnector(connectorId) {
    await runMcpAction(() => disableMcpConnector(connectorId))
  }

  async function handleCheckMcpConnector(connectorId) {
    const result = await runMcpAction(() => checkMcpConnector(connectorId))
    if (result) setMcpCheckResult(result)
  }

  async function handlePlanMcpAction(event) {
    event.preventDefault()
    if (!mcpSelectedId || !mcpActionName.trim()) return
    const result = await runMcpAction(() => planMcpConnectorAction(mcpSelectedId, mcpActionName.trim()))
    if (result) setMcpPlanResult(result)
  }

  async function handleRequestMcpExecution(event) {
    event.preventDefault()
    if (!mcpSelectedId || !mcpExecActionName.trim()) return
    await runMcpAction(async () => {
      await requestMcpExecution(mcpSelectedId, mcpExecActionName.trim())
      setMcpExecActionName('')
    })
  }

  async function handleApproveMcpExecution(requestId) {
    await runMcpAction(() => approveMcpExecution(requestId))
  }

  async function handleRejectMcpExecution(requestId) {
    await runMcpAction(() => rejectMcpExecution(requestId))
  }

  async function handleRunMcpExecution(requestId) {
    await runMcpAction(() => runMcpExecution(requestId))
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
        title: 'Diagnostic health check',
        job_type: 'health_check',
        workspace_id: workspaceId,
        payload: { source: 'developer_ui', note: 'Manual diagnostic check' },
      })
      await refreshAgentJobs(workspaceId)
      setCopied('Diagnostic job created')
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

  async function refreshAgentMarketplace(nextWorkspaceId = workspaceId) {
    const [dashboard, packs, teams] = await Promise.all([
      getAgentMarketplaceDashboard(nextWorkspaceId),
      getAgentMarketplacePacks(),
      getAgentMarketplaceTeams(nextWorkspaceId),
    ])
    setAgentMarketplaceDashboard(dashboard)
    setAgentMarketplacePacks(packs)
    setAgentMarketplaceTeams(teams)
  }

  async function refreshCodexJobs() {
    const result = await getCodexJobs()
    setCodexJobsAvailable(result.available)
    setCodexJobs(result.items || [])
  }

  async function refreshIntegrations() {
    const [slack, notion] = await Promise.all([getSlackStatus(), getNotionStatus()])
    setSlackStatus(slack)
    setNotionStatus(notion)
    setSlackNotifications(await getSlackNotifications(10))
    setNotionExports(await getNotionExports(10))
  }

  async function handleSlackTest() {
    setSlackBusy(true)
    setError('')
    try {
      await sendSlackTest({})
      await refreshIntegrations()
      setCopied('Slack test sent')
      window.setTimeout(() => setCopied(''), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setSlackBusy(false)
    }
  }

  async function handleNotionTestExport() {
    setNotionBusy(true)
    setError('')
    try {
      await sendNotionExport({ title: 'Test export', content: 'This is a test export from EvolveAgent AI.' })
      await refreshIntegrations()
      setCopied('Notion test export sent')
      window.setTimeout(() => setCopied(''), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setNotionBusy(false)
    }
  }

  async function refreshAutopilot(nextWorkspaceId = workspaceId) {
    const [settings, runs, checkpoints] = await Promise.all([
      getAutopilotSettings(),
      getAutopilotRuns(nextWorkspaceId),
      getAutopilotCheckpoints({ workspaceId: nextWorkspaceId, status: 'pending' }),
    ])
    setAutopilotSettings(settings)
    setAutopilotRuns(runs.slice(0, 8))
    setAutopilotCheckpoints(checkpoints)
  }

  async function handleToggleKillSwitch() {
    if (!autopilotSettings) return
    setAutopilotBusy(true)
    setError('')
    try {
      const next = !autopilotSettings.kill_switch_enabled
      await updateAutopilotSettings({ kill_switch_enabled: next })
      await refreshAutopilot()
      setCopied(next ? 'Autopilot kill switch ON' : 'Autopilot kill switch OFF')
      window.setTimeout(() => setCopied(''), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setAutopilotBusy(false)
    }
  }

  async function handleCheckpointDecision(checkpointId, decision) {
    setAutopilotBusy(true)
    setError('')
    try {
      await decideAutopilotCheckpoint(checkpointId, decision)
      await refreshAutopilot()
      setCopied(decision === 'approve' ? 'Checkpoint approved' : 'Checkpoint rejected')
      window.setTimeout(() => setCopied(''), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setAutopilotBusy(false)
    }
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

  async function handleCreateEvaluationRun(taskType = '') {
    setEvaluationBusy(true)
    setEvaluationError('')
    try {
      await createEvaluationRun({
        workspace_id: workspaceId,
        task_type: taskType || undefined,
        notes: 'Created from Developer Mode Evaluation Lab.',
      })
      await refreshEvaluationLab(workspaceId)
      setCopied('Evaluation run created')
    } catch (err) {
      setEvaluationError(err.message)
    } finally {
      setEvaluationBusy(false)
    }
  }

  async function handleCreateEvaluationABTest() {
    setEvaluationBusy(true)
    setEvaluationError('')
    try {
      await createEvaluationABTest({
        workspace_id: workspaceId,
        name: `${abVariantA} vs ${abVariantB}`,
        variant_a: abVariantA,
        variant_b: abVariantB,
      })
      await refreshEvaluationLab(workspaceId)
      setCopied('Evaluation A/B comparison created')
    } catch (err) {
      setEvaluationError(err.message)
    } finally {
      setEvaluationBusy(false)
    }
  }

  async function handleExportEvaluation(format) {
    setEvaluationBusy(true)
    setEvaluationError('')
    try {
      const content = await exportEvaluationResults(workspaceId, format)
      downloadFile(
        `evolveagent-evaluation.${format}`,
        content,
        format === 'json' ? 'application/json' : 'text/csv',
      )
    } catch (err) {
      setEvaluationError(err.message)
    } finally {
      setEvaluationBusy(false)
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

  async function handleInstallAgentPack(packId) {
    setAgentMarketplaceBusyId(packId)
    try {
      await installAgentMarketplacePack(packId, workspaceId)
      await Promise.all([
        refreshAgentMarketplace(workspaceId),
        refreshCustomAgents(workspaceId),
        refreshAnalytics(workspaceId),
      ])
      setCopied('Agent team installed')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setError(err.message)
    } finally {
      setAgentMarketplaceBusyId('')
    }
  }

  async function handleRateAgentTeam(teamId) {
    const rating = Number(window.prompt('Rating 1-5:', '5') || 0)
    if (!rating) return
    const review = window.prompt('Optional review:', '') || ''
    setAgentMarketplaceBusyId(teamId)
    try {
      await rateAgentMarketplaceTeam(teamId, rating, review, workspaceId)
      await refreshAgentMarketplace(workspaceId)
      setCopied('Agent team rated')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setError(err.message)
    } finally {
      setAgentMarketplaceBusyId('')
    }
  }

  async function handleExportAgentTeam(teamId) {
    setAgentMarketplaceBusyId(teamId)
    try {
      const exported = await exportAgentMarketplaceTeam(teamId)
      downloadFile(
        `evolveagent-agent-team-${teamId}.json`,
        JSON.stringify(exported, null, 2),
        'application/json',
      )
      setCopied('Agent team exported')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setError(err.message)
    } finally {
      setAgentMarketplaceBusyId('')
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

  async function handleExportDigitalTwin() {
    setDigitalTwinBusy(true)
    setDigitalTwinError('')
    try {
      const data = await exportDigitalTwinProfile(workspaceId)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `digital-twin-${workspaceId || 'profile'}.json`
      link.click()
      URL.revokeObjectURL(url)
      setCopied('Digital Twin profile exported')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setDigitalTwinError(err.message)
    } finally {
      setDigitalTwinBusy(false)
    }
  }

  async function handleResetDigitalTwin() {
    if (!window.confirm('Reset Digital Twin profile? This clears your manual style overrides and re-derives from activity.')) return
    setDigitalTwinBusy(true)
    setDigitalTwinError('')
    try {
      setDigitalTwinProfile(await resetDigitalTwinProfile(workspaceId))
      setCopied('Digital Twin profile reset')
      window.setTimeout(() => setCopied(''), 1300)
    } catch (err) {
      setDigitalTwinError(err.message)
    } finally {
      setDigitalTwinBusy(false)
    }
  }

  async function handleDeleteDigitalTwin() {
    if (!window.confirm('Delete all Digital Twin profile data for this workspace? This cannot be undone.')) return
    setDigitalTwinBusy(true)
    setDigitalTwinError('')
    try {
      await deleteDigitalTwinProfile(workspaceId)
      setDigitalTwinProfile(null)
      setCopied('Digital Twin profile deleted')
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
    // `mcp:` prefix routes into the MCP hub instead of the full workflow.
    if (/^mcp:/i.test(prompt)) {
      await handleMcpCommand(prompt)
      return
    }
    // `/`-commands route to the governed CLI palette (no raw shell).
    if (prompt.startsWith('/')) {
      await runSlashCommand(prompt)
      return
    }
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
      // Voice Ask Console: speak the answer aloud + Perplexity-style sources/follow-ups + MCP suggestions.
      speak(assistantMessage.content)
      refreshAskSources(prompt)
      refreshMcpSuggestions(prompt).then((suggestions) => buildFollowups(prompt, suggestions))
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
      // Push-to-talk, auto-submit: speaking a request runs it immediately.
      if (transcript.trim()) {
        submitMessage(transcript)
      }
    }
    recognition.onerror = () => {
      setError('Voice input could not be transcribed. Try again or type your message.')
    }
    recognition.onend = () => setListening(false)
    recognition.start()
  }

  function heroSubmit(event) {
    event.preventDefault()
    const value = heroInput.trim()
    if (!value || loading) return
    setHeroInput('')
    submitMessage(value)
  }

  // ---- Master Agent: one AI surface that routes across all of v1–v60 ----
  async function askMaster(rawText, voiceUsed = false) {
    const text = (rawText ?? masterText).trim()
    if (!text || masterBusy) return
    // Command prefixes route to their governed surfaces instead of the router.
    if (/^mcp:/i.test(text)) { setMasterText(''); return handleMcpCommand(text) }
    if (text.startsWith('/')) { setMasterText(''); return runSlashCommand(text) }
    setMasterBusy(true)
    setError('')
    try {
      const result = await routeMasterAgent(text, { workspaceId, voiceUsed })
      setMasterResult(result)
      setAskSources(result.sources || [])
      setAskFollowups(result.followups || [])
      setMcpSuggestions(result.mcp_suggestions || [])
      setMasterText('')
      // Two-way voice: read the answer aloud (voice requests always speak; typed obeys the toggle).
      if (voiceUsed && !voiceOutputEnabled) setVoiceOutputEnabled(true)
      speak(result.requires_approval
        ? `${result.answer}. Heads up — this needs your approval before anything runs.`
        : result.answer)
    } catch (err) {
      setError(`Master Agent could not route that: ${err.message}`)
    } finally {
      setMasterBusy(false)
    }
  }

  function masterSubmit(event) {
    event.preventDefault()
    askMaster(masterText, false)
  }

  // Push-to-talk for the Master Agent: speak → auto-route → spoken answer.
  function startMasterVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Voice input is not supported in this browser yet.')
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onstart = () => { setListening(true); setError('') }
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || ''
      if (transcript.trim()) askMaster(transcript, true)
    }
    recognition.onerror = () => setError('Voice input could not be transcribed. Try again or type.')
    recognition.onend = () => setListening(false)
    recognition.start()
  }

  // ---- CLI command palette (governed /-commands; no raw shell) ----
  const SLASH_COMMANDS = [
    { cmd: '/help', desc: 'List available commands' },
    { cmd: '/mcp', desc: 'Suggest MCP tools for a task (e.g. /mcp connect github)' },
    { cmd: '/connectors', desc: 'List MCP connectors' },
    { cmd: '/health', desc: 'Show platform health score' },
    { cmd: '/approvals', desc: 'Show pending approvals across sources' },
    { cmd: '/notifications', desc: 'Generate & show alerts' },
    { cmd: '/playbooks', desc: 'List saved playbooks' },
    { cmd: '/run-playbook', desc: 'Run a playbook by name (planning-first)' },
    { cmd: '/scorecard', desc: 'Operating Layer 2.0 readiness scorecard' },
    { cmd: '/snapshot', desc: 'Capture an operating-layer snapshot' },
  ]

  function postCliResult(command, text, spokenSummary) {
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: 'user', content: command },
      { id: crypto.randomUUID(), role: 'assistant', content: text, cli_command: true },
    ])
    if (spokenSummary) speak(spokenSummary)
  }

  async function runSlashCommand(raw) {
    const parts = raw.trim().split(/\s+/)
    const cmd = parts[0].toLowerCase()
    const arg = parts.slice(1).join(' ').trim()
    setInput('')
    setHeroInput('')
    setCliBusy(true)
    try {
      if (cmd === '/help') {
        postCliResult(raw, 'Available commands:\n' + SLASH_COMMANDS.map((c) => `${c.cmd} — ${c.desc}`).join('\n'), 'Here are the available commands.')
      } else if (cmd === '/mcp') {
        await handleMcpCommand(`mcp: ${arg || 'general task'}`)
      } else if (cmd === '/connectors') {
        const data = await getMcpConnectors()
        const list = (data.connectors || []).map((c) => `• ${c.name} — ${c.status} · ${c.enabled ? 'enabled' : 'disabled'}`).join('\n') || 'No connectors registered yet.'
        postCliResult(raw, `MCP connectors:\n${list}`, `${data.count || 0} connectors registered.`)
      } else if (cmd === '/health') {
        const h = await getHealthMonitorDashboard()
        const checks = (h.checks || []).map((c) => `• [${c.status}] ${c.name} — ${c.detail}`).join('\n')
        postCliResult(raw, `Health: ${h.status} (score ${h.health_score})\n${checks}`, `Platform health is ${h.status}, score ${h.health_score}.`)
      } else if (cmd === '/approvals') {
        const a = await getApprovalsCenterSummary()
        postCliResult(raw, `Pending approvals: ${a.pending_count} (high-risk ${a.high_risk_pending}). Sources: ${JSON.stringify(a.by_source)}`, `${a.pending_count} approvals pending.`)
      } else if (cmd === '/notifications') {
        await generateNotifications()
        const s = await getNotificationsSummary()
        postCliResult(raw, `Notifications — unread ${s.unread} (critical ${s.critical_unread}).`, `${s.unread} unread notifications.`)
        refreshNotifications()
      } else if (cmd === '/playbooks') {
        const p = await getPlaybooks()
        const list = (p.playbooks || []).map((pb) => `• ${pb.name} (${pb.step_count} steps)`).join('\n') || 'No playbooks saved.'
        postCliResult(raw, `Playbooks:\n${list}`, `${p.count || 0} playbooks saved.`)
      } else if (cmd === '/run-playbook') {
        const p = await getPlaybooks()
        const match = (p.playbooks || []).find((pb) => pb.name.toLowerCase().includes(arg.toLowerCase())) || (p.playbooks || [])[0]
        if (!match) { postCliResult(raw, 'No playbooks to run. Create one first.', 'No playbooks to run.') }
        else {
          const run = await runPlaybook(match.playbook_id)
          postCliResult(raw, `Ran "${match.name}" (planning-first): ${run.planned_count} planned, ${run.approval_required_count} need approval. Nothing was executed.`, `Ran ${match.name}. ${run.approval_required_count} steps need approval.`)
        }
      } else if (cmd === '/scorecard') {
        const d = await getOperatingLayerV2Dashboard()
        postCliResult(raw, `Operating Layer 2.0 — grade ${d.overall_grade} (${d.overall_score}/100), coverage ${d.coverage_pct}%.`, `Overall grade ${d.overall_grade}.`)
        refreshOpLayer2()
      } else if (cmd === '/snapshot') {
        await createOperatingLayerV2Snapshot()
        postCliResult(raw, 'Captured an Operating Layer 2.0 snapshot.', 'Snapshot captured.')
        refreshOpLayer2()
      } else {
        postCliResult(raw, `Unknown command "${cmd}". Type /help for the list.`, 'Unknown command.')
      }
    } catch (err) {
      postCliResult(raw, `Command failed: ${err.message}`, 'The command failed.')
    } finally {
      setCliBusy(false)
    }
  }

  // Speak an answer aloud via the browser (local text-to-speech; no external service).
  function speak(text) {
    if (!voiceOutputEnabled || !text) return
    const synth = window.speechSynthesis
    if (!synth) return
    try {
      synth.cancel()
      const clipped = String(text).slice(0, 1200)
      const utterance = new SpeechSynthesisUtterance(clipped)
      utterance.lang = 'en-US'
      // Apply Voice Console preferences when available.
      const s = voiceSettings
      if (s) {
        if (typeof s.rate === 'number') utterance.rate = s.rate
        if (typeof s.pitch === 'number') utterance.pitch = s.pitch
        if (typeof s.volume === 'number') utterance.volume = s.volume
        if (s.voice_name) {
          const match = (availableVoices.length ? availableVoices : synth.getVoices() || []).find((v) => v.name === s.voice_name)
          if (match) utterance.voice = match
        }
      }
      utterance.onstart = () => setSpeaking(true)
      utterance.onend = () => setSpeaking(false)
      utterance.onerror = () => setSpeaking(false)
      synth.speak(utterance)
      // Privacy-safe audit: metadata only (char count), never the spoken text.
      logVoiceActivity('speak', { workspaceId: workspaceId || 'global', meta: { chars: String(clipped.length) } }).catch(() => {})
    } catch {
      setSpeaking(false)
    }
  }

  function stopSpeaking() {
    window.speechSynthesis?.cancel()
    setSpeaking(false)
  }

  // Task-aware MCP suggestions: which connector(s) a request needs + key readiness (never values).
  async function refreshMcpSuggestions(prompt) {
    if (!prompt || !prompt.trim()) {
      setMcpSuggestions([])
      return
    }
    try {
      const result = await suggestMcp(prompt.trim())
      setMcpSuggestions(result?.suggestions || [])
      return result?.suggestions || []
    } catch {
      setMcpSuggestions([])
      return []
    }
  }

  // Perplexity-style sources: ground the answer in indexed workspace docs (local retrieval, v51).
  async function refreshAskSources(prompt) {
    if (!prompt || !prompt.trim()) {
      setAskSources([])
      return
    }
    try {
      const result = await queryRetrieval({ workspace_id: workspaceId, query: prompt.trim(), top_k: 4 })
      setAskSources(result?.results || [])
    } catch {
      setAskSources([])
    }
  }

  // Build clickable follow-up questions from the task + suggested tools.
  function buildFollowups(prompt, suggestions) {
    const followups = []
    for (const s of (suggestions || []).slice(0, 2)) {
      followups.push(s.missing_keys.length > 0 ? `How do I set ${s.missing_keys[0]} for ${s.name}?` : `Connect ${s.name}`)
    }
    followups.push('Explain this in more detail', 'What are the risks and approvals involved?')
    setAskFollowups(followups.slice(0, 5))
  }

  // `mcp:` / `/mcp` command prefix → route straight into the MCP hub (suggest + open panel).
  async function handleMcpCommand(rawPrompt) {
    const task = rawPrompt.replace(/^\/?mcp:?\s*/i, '').trim() || rawPrompt
    const userMessage = { id: crypto.randomUUID(), role: 'user', content: rawPrompt }
    setInput('')
    const suggestions = await refreshMcpSuggestions(task)
    setShowMcpPanel(true)
    const lines = suggestions.length
      ? suggestions.map((s) => `• ${s.name} — ${s.recommended_action}`).join('\n')
      : 'No specific MCP connector matched that task.'
    const answer = `MCP command routed to the Connector Hub.\n\n${lines}\n\nOpen Developer Mode → MCP Hub to register/enable and manage keys. (Key values are never shown — only whether each required key is set.)`
    setMessages((current) => [
      ...current,
      userMessage,
      { id: crypto.randomUUID(), role: 'assistant', content: answer, mcp_command: true },
    ])
    buildFollowups(task, suggestions)
    speak('Opened the MCP connector hub with tool suggestions for your task.')
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
    document.body.appendChild(link)
    link.click()
    link.remove()
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
      <CommandPalette open={cmdkOpen} onClose={() => setCmdkOpen(false)} commands={commandPaletteCommands} />
      <button type="button" className="cmdk-trigger" onClick={() => setCmdkOpen(true)} title="Command palette (⌘K)" aria-label="Open command palette">
        <Terminal size={14} /> <span>⌘K</span>
      </button>
      {developerMode && sidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar"
        />
      )}
      {!developerMode && (
        <nav className="simple-rail" aria-label="EvolveAgent">
          <div className="simple-rail-avatar" aria-hidden="true" />
          <button type="button" className="simple-rail-btn active" onClick={newChat} title="New chat"><MessageSquarePlus size={18} /></button>
          <button type="button" className="simple-rail-btn" onClick={() => setSelectedRunId(null)} title="History"><Clock size={18} /></button>
          <button type="button" className="simple-rail-btn" onClick={() => setDeveloperMode(true)} title="Tools & panels"><Layers3 size={18} /></button>
          <button type="button" className="simple-rail-btn" onClick={() => setDeveloperMode(true)} title="Library"><Library size={18} /></button>
          <button type="button" className="simple-rail-btn" onClick={() => setDeveloperMode(true)} title="Memory & brain"><Brain size={18} /></button>
          <button type="button" className="simple-rail-btn" onClick={() => setDeveloperMode(true)} title="Data"><Database size={18} /></button>
          <button
            type="button"
            className={`simple-rail-btn ${voiceOutputEnabled ? 'on' : ''}`}
            onClick={() => { if (speaking) stopSpeaking(); setVoiceOutputEnabled((v) => !v) }}
            title={voiceOutputEnabled ? 'Spoken answers on' : 'Spoken answers off'}
          >
            {voiceOutputEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>
          <div className="simple-rail-spacer" />
          <button type="button" className="simple-rail-btn" onClick={toggleTheme} title="Toggle theme">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </nav>
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
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`} data-active={developerMode ? devSection : undefined}>
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

        {developerMode && (
          <nav className="dev-nav" aria-label="Sections">
            {[
              { id: 'agent', label: 'Agent', icon: <Brain size={14} /> },
              { id: 'workspace', label: 'Workspace', icon: <Layers3 size={14} /> },
              { id: 'ops', label: 'Ops', icon: <Gauge size={14} /> },
              { id: 'tools', label: 'Tools', icon: <Cpu size={14} /> },
              { id: 'intel', label: 'Intelligence', icon: <Sparkles size={14} /> },
              { id: 'build', label: 'Build & Ship', icon: <Flag size={14} /> },
            ].map((s) => (
              <button
                key={s.id}
                type="button"
                className={`dev-nav-btn ${devSection === s.id ? 'active' : ''}`}
                onClick={() => setDevSection(s.id)}
              >
                {s.icon}<span>{s.label}</span>
              </button>
            ))}
          </nav>
        )}

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

        <section data-group="agent" className="sidebar-section">
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

        <section data-group="agent" className="sidebar-section">
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

        <section data-group="tools" className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowIntegrations((current) => !current)}>
            <span>
              <Layers3 size={15} />
              Integrations
            </span>
            <ChevronDown size={15} />
          </button>
          {showIntegrations && (
            <div className="memory-panel integrations-panel">
              <div className="integration-card">
                <div className="integration-card-header">
                  <strong>Slack</strong>
                  <span className={`integration-badge ${slackStatus?.enabled ? 'enabled' : 'disabled'}`}>
                    {slackStatus?.enabled ? 'enabled' : 'disabled'}
                  </span>
                </div>
                {slackStatus ? (
                  <>
                    <div className="mini-grid">
                      <div>
                        <span>Configured</span>
                        <strong>{slackStatus.configured ? 'Yes' : 'No'}</strong>
                      </div>
                      <div>
                        <span>Channel</span>
                        <strong>{slackStatus.default_channel || 'none'}</strong>
                      </div>
                    </div>
                    {slackStatus.last_error && (
                      <p className="integration-error">Last error: {slackStatus.last_error}</p>
                    )}
                    {!slackStatus.enabled && (
                      <p className="muted">Set SLACK_NOTIFICATIONS_ENABLED=true and SLACK_WEBHOOK_URL in .env to enable.</p>
                    )}
                    {slackStatus.enabled && !slackStatus.configured && (
                      <p className="muted">Enabled but webhook not configured. Set SLACK_WEBHOOK_URL in .env.</p>
                    )}
                    {slackStatus.enabled && slackStatus.configured && (
                      <button
                        className="secondary-button full-width"
                        type="button"
                        onClick={handleSlackTest}
                        disabled={slackBusy}
                      >
                        {slackBusy ? 'Sending...' : 'Send test notification'}
                      </button>
                    )}
                  </>
                ) : (
                  <p className="muted">Slack status unavailable.</p>
                )}
                {slackNotifications.length > 0 ? (
                  <details className="developer-prompt-block">
                    <summary>Recent notifications ({slackNotifications.length})</summary>
                    {slackNotifications.slice(0, 5).map((item, index) => (
                      <div className="integration-activity" key={item.notification_id || index}>
                        <span className={item.success ? 'success' : 'failed'}>{item.success ? 'sent' : 'failed'}</span>
                        <p>{previewText(item.text || item.message || '', 100)}</p>
                        {item.created_at && <small>{new Date(item.created_at).toLocaleString()}</small>}
                      </div>
                    ))}
                  </details>
                ) : slackStatus?.enabled ? (
                  <p className="muted">No notifications yet.</p>
                ) : null}
              </div>

              <div className="integration-card">
                <div className="integration-card-header">
                  <strong>Notion</strong>
                  <span className={`integration-badge ${notionStatus?.enabled ? 'enabled' : 'disabled'}`}>
                    {notionStatus?.enabled ? 'enabled' : 'disabled'}
                  </span>
                </div>
                {notionStatus ? (
                  <>
                    <div className="mini-grid">
                      <div>
                        <span>Configured</span>
                        <strong>{notionStatus.configured ? 'Yes' : 'No'}</strong>
                      </div>
                      <div>
                        <span>Parent page</span>
                        <strong>{notionStatus.parent_page_id ? 'set' : 'none'}</strong>
                      </div>
                    </div>
                    {notionStatus.last_error && (
                      <p className="integration-error">Last error: {notionStatus.last_error}</p>
                    )}
                    {!notionStatus.enabled && (
                      <p className="muted">Set NOTION_SYNC_ENABLED=true, NOTION_API_KEY, and NOTION_PARENT_PAGE_ID in .env to enable.</p>
                    )}
                    {notionStatus.enabled && !notionStatus.configured && (
                      <p className="muted">Enabled but not fully configured. Set NOTION_API_KEY and NOTION_PARENT_PAGE_ID in .env.</p>
                    )}
                    {notionStatus.enabled && notionStatus.configured && (
                      <button
                        className="secondary-button full-width"
                        type="button"
                        onClick={handleNotionTestExport}
                        disabled={notionBusy}
                      >
                        {notionBusy ? 'Exporting...' : 'Send test export'}
                      </button>
                    )}
                  </>
                ) : (
                  <p className="muted">Notion status unavailable.</p>
                )}
                {notionExports.length > 0 ? (
                  <details className="developer-prompt-block">
                    <summary>Recent exports ({notionExports.length})</summary>
                    {notionExports.slice(0, 5).map((item, index) => (
                      <div className="integration-activity" key={item.export_id || index}>
                        <span className={item.success ? 'success' : 'failed'}>{item.success ? 'exported' : 'failed'}</span>
                        <p>{previewText(item.title || '', 100)}</p>
                        {item.created_at && <small>{new Date(item.created_at).toLocaleString()}</small>}
                      </div>
                    ))}
                  </details>
                ) : notionStatus?.enabled ? (
                  <p className="muted">No exports yet.</p>
                ) : null}
              </div>

              <button
                className="secondary-button full-width"
                type="button"
                onClick={refreshIntegrations}
              >
                Refresh status
              </button>
            </div>
          )}
        </section>

        <section data-group="agent" className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowAutopilot((current) => !current)}>
            <span>
              <Bot size={15} />
              Autopilot
            </span>
            <ChevronDown size={15} />
          </button>
          {showAutopilot && (
            <div className="memory-panel autopilot-panel">
              <div className="integration-card">
                <div className="integration-card-header">
                  <strong>Supervised autopilot</strong>
                  <span className={`integration-badge ${autopilotSettings?.kill_switch_enabled ? 'disabled' : 'enabled'}`}>
                    {autopilotSettings?.kill_switch_enabled ? 'kill switch on' : 'active'}
                  </span>
                </div>
                {autopilotSettings ? (
                  <>
                    <div className="mini-grid">
                      <div>
                        <span>Permission mode</span>
                        <strong>{autopilotSettings.permission_mode || 'supervised'}</strong>
                      </div>
                      <div>
                        <span>Default tier</span>
                        <strong>{autopilotSettings.default_permission_level || 'plan_only'}</strong>
                      </div>
                    </div>
                    {autopilotSettings.kill_switch_enabled && (
                      <p className="integration-error">Kill switch is ON — all autopilot execution is blocked. Planning still works.</p>
                    )}
                    <button
                      className="secondary-button full-width"
                      type="button"
                      onClick={handleToggleKillSwitch}
                      disabled={autopilotBusy}
                    >
                      {autopilotBusy
                        ? 'Updating...'
                        : autopilotSettings.kill_switch_enabled
                          ? 'Disable kill switch'
                          : 'Enable kill switch'}
                    </button>
                  </>
                ) : (
                  <p className="muted">Autopilot status unavailable.</p>
                )}
              </div>

              <div className="integration-card">
                <div className="integration-card-header">
                  <strong>Pending checkpoints</strong>
                  <span className="integration-badge disabled">{autopilotCheckpoints.length}</span>
                </div>
                {autopilotCheckpoints.length > 0 ? (
                  autopilotCheckpoints.map((checkpoint) => (
                    <div className="autopilot-checkpoint" key={checkpoint.checkpoint_id}>
                      <p>{previewText(checkpoint.summary || checkpoint.action_type || '', 120)}</p>
                      <div className="autopilot-checkpoint-meta">
                        <span>{checkpoint.permission_level}</span>
                        <span className={`risk-${checkpoint.risk_level || 'medium'}`}>{checkpoint.risk_level || 'medium'} risk</span>
                      </div>
                      <div className="autopilot-checkpoint-actions">
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => handleCheckpointDecision(checkpoint.checkpoint_id, 'approve')}
                          disabled={autopilotBusy}
                        >
                          Approve
                        </button>
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => handleCheckpointDecision(checkpoint.checkpoint_id, 'reject')}
                          disabled={autopilotBusy}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="muted">No checkpoints waiting for approval.</p>
                )}
              </div>

              <div className="integration-card">
                <div className="integration-card-header">
                  <strong>Recent runs</strong>
                  <span className="integration-badge disabled">{autopilotRuns.length}</span>
                </div>
                {autopilotRuns.length > 0 ? (
                  autopilotRuns.map((run) => (
                    <div className="integration-activity" key={run.run_id}>
                      <span className={run.status === 'blocked' || run.status === 'stopped' ? 'failed' : 'success'}>
                        {run.status}
                      </span>
                      <p>{previewText(run.prompt || '', 100)}</p>
                      <small>
                        {run.mode} · {run.actions_count ?? 0} action(s)
                        {run.pending_checkpoints_count ? ` · ${run.pending_checkpoints_count} pending` : ''}
                      </small>
                    </div>
                  ))
                ) : (
                  <p className="muted">No autopilot runs yet.</p>
                )}
              </div>

              <button
                className="secondary-button full-width"
                type="button"
                onClick={() => refreshAutopilot()}
              >
                Refresh autopilot
              </button>
            </div>
          )}
        </section>

        <section data-group="agent" className="sidebar-section">
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

        <section data-group="ops" className="sidebar-section">
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

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowCompliancePanel((current) => !current)}>
              <span>
                <ShieldAlert size={15} />
                Compliance
              </span>
              <ChevronDown size={15} />
            </button>
            {showCompliancePanel && (
              <div className="analytics-panel">
                {complianceSummary ? (
                  <>
                    <div>
                      <span>Audit events</span>
                      <strong>{complianceSummary.summary?.total_audit_events || 0}</strong>
                    </div>
                    <div>
                      <span>Blocked</span>
                      <strong>{complianceSummary.summary?.blocked_actions || 0}</strong>
                    </div>
                    <div>
                      <span>High risk</span>
                      <strong>{complianceSummary.summary?.high_risk_events || 0}</strong>
                    </div>
                    <div>
                      <span>PII findings</span>
                      <strong>{complianceSummary.summary?.pii_findings || 0}</strong>
                    </div>
                    <div>
                      <span>Retention review</span>
                      <strong>{complianceSummary.summary?.retention_items_needing_review || 0}</strong>
                    </div>
                    <div>
                      <span>Policies</span>
                      <strong>{complianceRetention?.policies?.length || 0}</strong>
                    </div>
                  </>
                ) : (
                  <p className="muted">Compliance data is not available yet.</p>
                )}
                <div className="developer-prompt-block">
                  <span>PII scan</span>
                  <textarea value={piiScanText} onChange={(event) => setPiiScanText(event.target.value)} />
                  <button className="secondary-button" type="button" onClick={handlePiiScan} disabled={complianceBusy}>
                    Scan sample
                  </button>
                  {piiScanResult && (
                    <p>
                      {piiScanResult.status}: {piiScanResult.redaction_count} redaction(s){' '}
                      {(piiScanResult.detected_types || []).join(', ')}
                    </p>
                  )}
                </div>
                <div className="agent-list compact-list">
                  <h3>Retention review</h3>
                  {(complianceRetention?.reviews || []).slice(0, 5).map((item) => (
                    <div className="provider-row" key={item.collection}>
                      <strong>{item.collection}</strong>
                      <div className="model-meta">
                        <span>{item.action}</span>
                        <span>{item.records_needing_review} review</span>
                        <span>{item.retention_days} days</span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="agent-list compact-list">
                  <h3>Recent audit events</h3>
                  {complianceAudit.slice(0, 5).map((event) => (
                    <div className="provider-row" key={event.event_id || `${event.action_type}-${event.created_at}`}>
                      <strong>{event.action_type}</strong>
                      <div className="model-meta">
                        <span>{event.permission_level}</span>
                        {event.blocked && <span>blocked</span>}
                        <span>risk {event.risk_score || 0}</span>
                      </div>
                      <p>{event.reason}</p>
                    </div>
                  ))}
                </div>
                <div className="button-row">
                  <button className="secondary-button" type="button" onClick={() => handleComplianceExport('markdown')} disabled={complianceBusy}>
                    Export MD
                  </button>
                  <button className="secondary-button" type="button" onClick={() => handleComplianceExport('json')} disabled={complianceBusy}>
                    Export JSON
                  </button>
                </div>
                {complianceError && <p className="error-text">{complianceError}</p>}
              </div>
            )}
          </section>
        )}

        <section data-group="workspace" className="sidebar-section">
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

        <section data-group="agent" className="sidebar-section">
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

        <section data-group="agent" className="sidebar-section">
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
          <section data-group="intel" className="sidebar-section">
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
          <section data-group="intel" className="sidebar-section">
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
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowEvaluationLab((current) => !current)}>
              <span>
                <BarChart3 size={15} />
                Evaluation Lab
              </span>
              <ChevronDown size={15} />
            </button>
            {showEvaluationLab && (
              <div className="mission-panel">
                <button
                  className="secondary-button full-width"
                  type="button"
                  disabled={evaluationBusy}
                  onClick={() => handleCreateEvaluationRun('')}
                >
                  {evaluationBusy ? 'Running eval...' : 'Run full benchmark'}
                </button>
                {evaluationError && <p className="provider-warning">{evaluationError}</p>}
                {evaluationDashboard ? (
                  <>
                    <div className="provider-card">
                      <div>
                        <span>Benchmarks</span>
                        <strong>{evaluationDashboard.benchmark_count || 0}</strong>
                      </div>
                      <div>
                        <span>Eval runs</span>
                        <strong>{evaluationDashboard.evaluation_run_count || 0}</strong>
                      </div>
                      <div>
                        <span>Average</span>
                        <strong>{evaluationDashboard.average_score || 0}</strong>
                      </div>
                      <div>
                        <span>Regressions</span>
                        <strong>{evaluationDashboard.regression_count || 0}</strong>
                      </div>
                    </div>
                    {evaluationDashboard.latest_run && (
                      <div className="agent-template-card">
                        <strong>Latest eval: {evaluationDashboard.latest_run.score}</strong>
                        <span>{evaluationDashboard.latest_run.status} · {new Date(evaluationDashboard.latest_run.created_at).toLocaleString()}</span>
                      </div>
                    )}
                    {(evaluationDashboard.score_trend || []).slice(-5).map((point, index) => (
                      <p className="muted" key={`${point.created_at}-${index}`}>
                        Trend {index + 1}: score {point.score} · {point.status}
                      </p>
                    ))}
                    {(evaluationDashboard.task_scores || []).slice(0, 5).map((task) => (
                      <div className="agent-template-card" key={task.task_type}>
                        <strong>{formatType(task.task_type)}</strong>
                        <span>avg {task.average_score} · {task.runs} run(s)</span>
                        <button type="button" disabled={evaluationBusy} onClick={() => handleCreateEvaluationRun(task.task_type)}>
                          Run task eval
                        </button>
                      </div>
                    ))}
                    {(evaluationDashboard.regressions || []).slice(0, 3).map((regression) => (
                      <div className="fallback-note" key={regression.regression_id}>
                        <strong>{regression.severity} regression · drop {regression.drop}</strong>
                        <p>{regression.recommendation}</p>
                      </div>
                    ))}
                  </>
                ) : (
                  <p className="muted">Evaluation dashboard is not available yet.</p>
                )}
                <div className="agent-template-card">
                  <strong>A/B agent comparison</strong>
                  <input value={abVariantA} onChange={(event) => setAbVariantA(event.target.value)} />
                  <input value={abVariantB} onChange={(event) => setAbVariantB(event.target.value)} />
                  <button type="button" disabled={evaluationBusy} onClick={handleCreateEvaluationABTest}>
                    Compare variants
                  </button>
                </div>
                <details>
                  <summary>Benchmark suites ({evaluationBenchmarks.length})</summary>
                  {evaluationBenchmarks.slice(0, 8).map((benchmark) => (
                    <p className="muted" key={benchmark.benchmark_id}>
                      {formatType(benchmark.task_type)} · {benchmark.name}
                    </p>
                  ))}
                </details>
                <div className="inline-actions">
                  <button type="button" disabled={evaluationBusy} onClick={() => handleExportEvaluation('json')}>
                    Export JSON
                  </button>
                  <button type="button" disabled={evaluationBusy} onClick={() => handleExportEvaluation('csv')}>
                    Export CSV
                  </button>
                  <button type="button" disabled={evaluationBusy} onClick={() => refreshEvaluationLab(workspaceId)}>
                    Refresh
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowProjectManager((current) => !current)}>
              <span>
                <Flag size={15} />
                AI Project Manager
              </span>
              <ChevronDown size={15} />
            </button>
            {showProjectManager && (
              <div className="mission-panel">
                <button
                  className="secondary-button full-width"
                  type="button"
                  disabled={projectManagerBusy}
                  onClick={handleGenerateProjectReport}
                >
                  {projectManagerBusy ? 'Working...' : 'Generate status report'}
                </button>
                {projectManagerError && <p className="provider-warning">{projectManagerError}</p>}
                {projectManagerDashboard ? (
                  <>
                    <div className="provider-card">
                      <div>
                        <span>Milestones</span>
                        <strong>{projectManagerDashboard.milestone_summary?.total || 0}</strong>
                      </div>
                      <div>
                        <span>Done</span>
                        <strong>{projectManagerDashboard.milestone_summary?.completed || 0}</strong>
                      </div>
                      <div>
                        <span>Avg progress</span>
                        <strong>{projectManagerDashboard.milestone_summary?.average_progress || 0}%</strong>
                      </div>
                      <div>
                        <span>Open risks</span>
                        <strong>{projectManagerDashboard.risk_summary?.open_risk_count || 0}</strong>
                      </div>
                    </div>
                    {projectManagerDashboard.latest_report && (
                      <div className="agent-template-card">
                        <strong>{projectManagerDashboard.latest_report.headline}</strong>
                        <span>{new Date(projectManagerDashboard.latest_report.generated_at).toLocaleString()}</span>
                      </div>
                    )}
                    <h3>Upcoming milestones</h3>
                    {(projectManagerDashboard.upcoming_milestones || []).slice(0, 5).map((milestone) => (
                      <div className="agent-template-card" key={milestone.goal_id}>
                        <strong>{milestone.title}</strong>
                        <span>{milestone.status} · {milestone.progress_percent}% · {milestone.task_count} task(s)</span>
                      </div>
                    ))}
                    {(projectManagerDashboard.resource_summary?.agent_load || []).slice(0, 4).map((entry) => (
                      <p className="muted" key={entry.agent}>
                        {entry.agent}: {entry.effort_points} effort point(s)
                      </p>
                    ))}
                  </>
                ) : (
                  <p className="muted">Project dashboard is not available yet.</p>
                )}
                <h3>Risk register ({projectManagerRisks.length})</h3>
                {projectManagerRisks.slice(0, 5).map((risk, index) => (
                  <div className={`fallback-note risk-${risk.severity}`} key={risk.risk_id || `${risk.title}-${index}`}>
                    <strong>{risk.severity} · {risk.title}</strong>
                    {risk.mitigation && <p>{risk.mitigation}</p>}
                  </div>
                ))}
                <div className="agent-template-card">
                  <strong>Log a risk</strong>
                  <input
                    value={newRiskTitle}
                    placeholder="Risk description"
                    onChange={(event) => setNewRiskTitle(event.target.value)}
                  />
                  <select value={newRiskSeverity} onChange={(event) => setNewRiskSeverity(event.target.value)}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                  <button type="button" disabled={projectManagerBusy} onClick={handleCreateProjectRisk}>
                    Add risk
                  </button>
                </div>
                <div className="inline-actions">
                  <button type="button" disabled={projectManagerBusy} onClick={() => refreshProjectManager(workspaceId)}>
                    Refresh
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowPortfolio((current) => !current)}>
              <span>
                <Layers3 size={15} />
                Portfolio Mode
              </span>
              <ChevronDown size={15} />
            </button>
            {showPortfolio && (
              <div className="mission-panel">
                <button
                  className="secondary-button full-width"
                  type="button"
                  disabled={portfolioBusy}
                  onClick={handleGeneratePortfolioReport}
                >
                  {portfolioBusy ? 'Working...' : 'Generate executive summary'}
                </button>
                {portfolioError && <p className="provider-warning">{portfolioError}</p>}
                {portfolioHealth && (
                  <div className={`agent-template-card risk-${portfolioHealth.rating === 'at_risk' ? 'high' : portfolioHealth.rating === 'watch' ? 'medium' : 'low'}`}>
                    <strong>Health: {portfolioHealth.score}/100 · {portfolioHealth.rating}</strong>
                    {(portfolioHealth.drivers || []).slice(0, 2).map((driver) => (
                      <span key={driver}>{driver}</span>
                    ))}
                  </div>
                )}
                {portfolioDashboard ? (
                  <>
                    <div className="provider-card">
                      <div>
                        <span>Workspaces</span>
                        <strong>{portfolioDashboard.total_workspaces || 0}</strong>
                      </div>
                      <div>
                        <span>Active goals</span>
                        <strong>{portfolioDashboard.active_goals || 0}</strong>
                      </div>
                      <div>
                        <span>Tasks done</span>
                        <strong>{portfolioDashboard.completed_tasks || 0}/{portfolioDashboard.total_tasks || 0}</strong>
                      </div>
                      <div>
                        <span>Open risks</span>
                        <strong>{portfolioDashboard.open_risks || 0}</strong>
                      </div>
                    </div>
                    <h3>Projects</h3>
                    {(portfolioDashboard.workspace_summaries || []).slice(0, 6).map((summary) => (
                      <div className="agent-template-card" key={summary.workspace_id}>
                        <strong>{summary.name}</strong>
                        <span>
                          goals {summary.completed_goals}/{summary.goal_count} · tasks {summary.completed_tasks}/{summary.total_tasks} · avg {summary.average_judge_score}
                        </span>
                      </div>
                    ))}
                    {portfolioAnalytics && (
                      <>
                        <h3>Top agents</h3>
                        {(portfolioAnalytics.top_agents || []).slice(0, 4).map((entry) => (
                          <p className="muted" key={entry.agent}>{entry.agent}: {entry.runs} run(s)</p>
                        ))}
                      </>
                    )}
                  </>
                ) : (
                  <p className="muted">Portfolio dashboard is not available yet.</p>
                )}
                <div className="inline-actions">
                  <button type="button" disabled={portfolioBusy} onClick={() => handleExportPortfolio('json')}>
                    Export JSON
                  </button>
                  <button type="button" disabled={portfolioBusy} onClick={() => handleExportPortfolio('markdown')}>
                    Export Markdown
                  </button>
                  <button type="button" disabled={portfolioBusy} onClick={() => refreshPortfolio()}>
                    Refresh
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowOsPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                EvolveAgent OS
              </span>
              <ChevronDown size={15} />
            </button>
            {showOsPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>EvolveAgent OS · v15.0</strong>
                  <span>Local-first, workspace-aware multi-agent platform.</span>
                </div>
                {osSummary ? (
                  <>
                    <div className="provider-card">
                      <div>
                        <span>SLA</span>
                        <strong>{osSummary.sla_rating} ({osSummary.uptime_proxy_score ?? osSla?.uptime_proxy_score ?? 0})</strong>
                      </div>
                      <div>
                        <span>Scheduler</span>
                        <strong>{osSummary.scheduler_health}</strong>
                      </div>
                      <div>
                        <span>Installer</span>
                        <strong>{(osSummary.installer_readiness?.missing_recommended_config || []).length === 0 ? 'ready' : 'needs config'}</strong>
                      </div>
                      <div>
                        <span>Plugin SDK</span>
                        <strong>v{osSummary.plugin_sdk?.sdk_version || '1.0'}</strong>
                      </div>
                    </div>
                    {osInstaller && (osInstaller.readiness?.missing_recommended_config || []).length > 0 && (
                      <>
                        <h3>Missing config</h3>
                        {osInstaller.readiness.missing_recommended_config.map((item) => (
                          <p className="muted" key={item}>{item}</p>
                        ))}
                      </>
                    )}
                    {osScheduler && (osScheduler.bottlenecks || []).length > 0 && (
                      <>
                        <h3>Scheduler bottlenecks</h3>
                        {osScheduler.bottlenecks.map((item) => (
                          <p className="muted" key={item}>{item}</p>
                        ))}
                      </>
                    )}
                    {osSla && (osSla.recommendations || []).length > 0 && (
                      <>
                        <h3>SLA recommendations</h3>
                        {osSla.recommendations.slice(0, 3).map((item) => (
                          <p className="muted" key={item}>{item}</p>
                        ))}
                      </>
                    )}
                    <h3>Safety</h3>
                    {(osSummary.safety_notes || []).slice(0, 2).map((note) => (
                      <p className="muted" key={note}>{note}</p>
                    ))}
                  </>
                ) : (
                  <p className="muted">EvolveAgent OS status is not available yet.</p>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleCopyOsSummary} disabled={!osSummary}>
                    Copy launch summary
                  </button>
                  <button type="button" onClick={() => refreshOsPanel()}>
                    Refresh
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowOrgPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Agent Organization
              </span>
              <ChevronDown size={15} />
            </button>
            {showOrgPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Multi-Agent Organization · v16.0</strong>
                  <span>Model EvolveAgent as an AI company: departments, managers, workers, reviewers, auditors.</span>
                </div>
                {departmentOverview && (
                  <div className="provider-card">
                    <div>
                      <span>Departments</span>
                      <strong>{departmentOverview.total_departments ?? departments.length}</strong>
                    </div>
                    <div>
                      <span>Active</span>
                      <strong>{departmentOverview.active_departments ?? 0}</strong>
                    </div>
                    <div>
                      <span>Runs</span>
                      <strong>{departmentOverview.department_runs ?? departmentRuns.length}</strong>
                    </div>
                    <div>
                      <span>Collaborations</span>
                      <strong>{departmentOverview.collaboration_count ?? departmentCollaborations.length}</strong>
                    </div>
                  </div>
                )}
                {orgError && <p className="error-text">{orgError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleSeedDepartments} disabled={orgBusy}>
                    Seed default departments
                  </button>
                  <button type="button" onClick={() => refreshOrgPanel()} disabled={orgBusy}>
                    Refresh
                  </button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateDepartment}>
                  <h3>Create department</h3>
                  <input
                    type="text"
                    placeholder="Department name"
                    value={newDepartmentName}
                    onChange={(event) => setNewDepartmentName(event.target.value)}
                  />
                  <select value={newDepartmentPermission} onChange={(event) => setNewDepartmentPermission(event.target.value)}>
                    <option value="read_only">read_only</option>
                    <option value="plan_only">plan_only</option>
                    <option value="approve_to_edit">approve_to_edit</option>
                    <option value="approve_to_run">approve_to_run</option>
                    <option value="blocked">blocked</option>
                  </select>
                  <button type="submit" disabled={orgBusy || !newDepartmentName.trim()}>
                    Create
                  </button>
                </form>

                <h3>Departments</h3>
                {departments.length === 0 && <p className="muted">No departments yet. Seed defaults to get started.</p>}
                {departments.map((department) => (
                  <div className="agent-template-card" key={department.department_id}>
                    <strong>
                      {department.name} {department.active === false ? '· archived' : ''}
                    </strong>
                    <span>{department.description}</span>
                    <p className="muted">Manager: {department.manager_agent}</p>
                    <p className="muted">Workers: {(department.worker_agents || []).join(', ') || '—'}</p>
                    <p className="muted">Reviewers: {(department.reviewer_agents || []).join(', ') || '—'}</p>
                    <p className="muted">Auditors: {(department.auditor_agents || []).join(', ') || '—'}</p>
                    <p className="muted">Tools: {(department.allowed_tools || []).join(', ') || '—'}</p>
                    <p className="muted">Permission: {department.permission_level}</p>
                    <p className="muted code-id">{department.department_id}</p>
                  </div>
                ))}

                <form className="stacked-form" onSubmit={handleCreateDepartmentRun}>
                  <h3>Run department task</h3>
                  <select value={runDepartmentId} onChange={(event) => setRunDepartmentId(event.target.value)}>
                    <option value="">Select department…</option>
                    {departments
                      .filter((department) => department.active !== false)
                      .map((department) => (
                        <option key={department.department_id} value={department.department_id}>
                          {department.name}
                        </option>
                      ))}
                  </select>
                  <input
                    type="text"
                    placeholder="Task for this department"
                    value={runDepartmentTask}
                    onChange={(event) => setRunDepartmentTask(event.target.value)}
                  />
                  <button type="submit" disabled={orgBusy || !runDepartmentId || !runDepartmentTask.trim()}>
                    Plan run
                  </button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateCollaboration}>
                  <h3>Collaboration planner</h3>
                  <input
                    type="text"
                    placeholder="Cross-department goal"
                    value={collabGoal}
                    onChange={(event) => setCollabGoal(event.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Departments (comma separated names)"
                    value={collabDepartments}
                    onChange={(event) => setCollabDepartments(event.target.value)}
                  />
                  <button type="submit" disabled={orgBusy || !collabGoal.trim()}>
                    Plan collaboration
                  </button>
                </form>

                {departmentRuns.length > 0 && (
                  <>
                    <h3>Recent department runs</h3>
                    {departmentRuns.slice(0, 5).map((run) => (
                      <div className="agent-template-card" key={run.department_run_id}>
                        <strong>{run.department_name || run.department_id}</strong>
                        <span>{run.task}</span>
                        <p className="muted">
                          Risk: {run.risk_level} · {run.requires_approval ? 'approval required' : 'no approval'} · {run.status}
                        </p>
                      </div>
                    ))}
                  </>
                )}

                {departmentCollaborations.length > 0 && (
                  <>
                    <h3>Recent collaborations</h3>
                    {departmentCollaborations.slice(0, 5).map((collab) => (
                      <div className="agent-template-card" key={collab.collaboration_id}>
                        <strong>{collab.goal}</strong>
                        <p className="muted">Lead: {collab.lead_department || '—'}</p>
                        <p className="muted">Departments: {(collab.departments || []).join(' → ') || '—'}</p>
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowBusinessPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Business Operator
              </span>
              <ChevronDown size={15} />
            </button>
            {showBusinessPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Business Operator · v18.0</strong>
                  <span>Leads, support triage, document processing, proposals, marketing — drafts only, governed.</span>
                </div>
                {businessDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Leads</span><strong>{businessDashboard.total_leads}</strong></div>
                    <div><span>Qualified</span><strong>{businessDashboard.qualified_leads}</strong></div>
                    <div><span>Open cases</span><strong>{businessDashboard.open_support_cases}</strong></div>
                    <div><span>High prio</span><strong>{businessDashboard.high_priority_cases}</strong></div>
                    <div><span>Proposals</span><strong>{businessDashboard.proposal_count}</strong></div>
                    <div><span>Drafts</span><strong>{businessDashboard.draft_proposals}</strong></div>
                    <div><span>Won</span><strong>{businessDashboard.won_leads}</strong></div>
                    <div><span>Conv. %</span><strong>{businessDashboard.conversion_rate}</strong></div>
                  </div>
                )}
                {businessError && <p className="error-text">{businessError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshBusinessPanel(workspaceId)} disabled={businessBusy}>
                    Refresh
                  </button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateLead}>
                  <h3>New lead</h3>
                  <input type="text" placeholder="Name" value={leadName} onChange={(event) => setLeadName(event.target.value)} />
                  <input type="text" placeholder="Company" value={leadCompany} onChange={(event) => setLeadCompany(event.target.value)} />
                  <button type="submit" disabled={businessBusy || (!leadName.trim() && !leadCompany.trim())}>Add lead</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateSupportCase}>
                  <h3>New support case</h3>
                  <input type="text" placeholder="Subject" value={caseSubject} onChange={(event) => setCaseSubject(event.target.value)} />
                  <select value={casePriority} onChange={(event) => setCasePriority(event.target.value)}>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                  <button type="submit" disabled={businessBusy || !caseSubject.trim()}>Triage case</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateBusinessDocument}>
                  <h3>Process document</h3>
                  <input type="text" placeholder="Title" value={docTitle} onChange={(event) => setDocTitle(event.target.value)} />
                  <textarea placeholder="Paste document content" value={docContent} onChange={(event) => setDocContent(event.target.value)} rows={3} />
                  <button type="submit" disabled={businessBusy || !docContent.trim()}>Process</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateProposal}>
                  <h3>New proposal draft</h3>
                  <input type="text" placeholder="Title" value={proposalTitle} onChange={(event) => setProposalTitle(event.target.value)} />
                  <input type="text" placeholder="Client" value={proposalClient} onChange={(event) => setProposalClient(event.target.value)} />
                  <button type="submit" disabled={businessBusy || !proposalTitle.trim()}>Draft proposal</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateMarketingItem}>
                  <h3>New marketing item</h3>
                  <input type="text" placeholder="Title" value={marketingTitle} onChange={(event) => setMarketingTitle(event.target.value)} />
                  <select value={marketingChannel} onChange={(event) => setMarketingChannel(event.target.value)}>
                    <option value="email">email</option>
                    <option value="linkedin">linkedin</option>
                    <option value="website">website</option>
                    <option value="instagram">instagram</option>
                    <option value="other">other</option>
                  </select>
                  <button type="submit" disabled={businessBusy || !marketingTitle.trim()}>Plan item</button>
                </form>

                {businessLeads.length > 0 && (
                  <>
                    <h3>Leads</h3>
                    {businessLeads.slice(0, 6).map((lead) => (
                      <div className="agent-template-card" key={lead.lead_id}>
                        <strong>{lead.name || lead.company || lead.lead_id}</strong>
                        <span>{lead.company}</span>
                        <p className="muted">Status: {lead.status} · Source: {lead.source}</p>
                        {lead.next_step && <p className="muted">Next: {lead.next_step}</p>}
                        <p className="muted code-id">{lead.lead_id}</p>
                      </div>
                    ))}
                  </>
                )}

                {businessSupportCases.length > 0 && (
                  <>
                    <h3>Support cases</h3>
                    {businessSupportCases.slice(0, 6).map((supportCase) => (
                      <div className="agent-template-card" key={supportCase.case_id}>
                        <strong>{supportCase.subject}</strong>
                        <p className="muted">Priority: {supportCase.priority} · {supportCase.status}</p>
                        <p className="muted">{supportCase.triage_summary}</p>
                      </div>
                    ))}
                  </>
                )}

                {businessDocuments.length > 0 && (
                  <>
                    <h3>Documents</h3>
                    {businessDocuments.slice(0, 6).map((doc) => (
                      <div className="agent-template-card" key={doc.document_id}>
                        <strong>{doc.title || doc.document_id}</strong>
                        <p className="muted">Type: {doc.document_type}</p>
                        <p className="muted">{doc.extracted_summary}</p>
                        {(doc.risk_flags || []).length > 0 && (
                          <p className="muted">Risks: {doc.risk_flags.join('; ')}</p>
                        )}
                      </div>
                    ))}
                  </>
                )}

                {businessProposals.length > 0 && (
                  <>
                    <h3>Proposal drafts</h3>
                    {businessProposals.slice(0, 6).map((proposal) => (
                      <div className="agent-template-card" key={proposal.proposal_id}>
                        <strong>{proposal.title}</strong>
                        <p className="muted">Client: {proposal.client || '—'} · {proposal.status}</p>
                      </div>
                    ))}
                  </>
                )}

                {businessMarketingItems.length > 0 && (
                  <>
                    <h3>Marketing calendar</h3>
                    {businessMarketingItems.slice(0, 6).map((item) => (
                      <div className="agent-template-card" key={item.item_id}>
                        <strong>{item.title}</strong>
                        <p className="muted">{item.channel} · {item.scheduled_for || 'unscheduled'} · {item.status}</p>
                      </div>
                    ))}
                  </>
                )}

                <p className="muted">Drafts only — EvolveAgent never sends email, processes payments, or contacts an external CRM.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowChiefPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Chief of Staff
              </span>
              <ChevronDown size={15} />
            </button>
            {showChiefPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>AI Chief of Staff · v19.0</strong>
                  <span>Daily/weekly plans, ranked priorities, and follow-ups from your local data — recommendations only.</span>
                </div>
                {chiefDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Priorities</span><strong>{(chiefDashboard.priority_items || []).length}</strong></div>
                    <div><span>Open f/ups</span><strong>{(chiefDashboard.open_followups || []).length}</strong></div>
                    <div><span>Overdue</span><strong>{(chiefDashboard.overdue_followups || []).length}</strong></div>
                    <div><span>Blocked</span><strong>{(chiefDashboard.blocked_items || []).length}</strong></div>
                    <div><span>Risks</span><strong>{chiefDashboard.risk_summary?.open_risk_count ?? 0}</strong></div>
                    <div><span>Today</span><strong>{chiefDashboard.today}</strong></div>
                  </div>
                )}
                {chiefDashboard?.recommended_next_action && (
                  <p className="muted">Next: {chiefDashboard.recommended_next_action}</p>
                )}
                {chiefError && <p className="error-text">{chiefError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleCreateDailyPlan} disabled={chiefBusy}>Daily plan</button>
                  <button type="button" onClick={handleCreateWeeklyPlan} disabled={chiefBusy}>Weekly plan</button>
                  <button type="button" onClick={() => refreshChiefPanel(workspaceId)} disabled={chiefBusy}>Refresh</button>
                </div>

                {chiefDashboard?.daily_plan && (
                  <div className="agent-template-card">
                    <strong>Daily plan · {chiefDashboard.daily_plan.date}</strong>
                    <span>{chiefDashboard.daily_plan.summary}</span>
                  </div>
                )}
                {chiefDashboard?.weekly_plan && (
                  <div className="agent-template-card">
                    <strong>Weekly plan · {chiefDashboard.weekly_plan.week_start}</strong>
                    <span>{chiefDashboard.weekly_plan.summary}</span>
                  </div>
                )}

                {chiefPriorities.length > 0 && (
                  <>
                    <h3>Ranked priorities</h3>
                    {chiefPriorities.slice(0, 6).map((item) => (
                      <div className="agent-template-card" key={item.item_id}>
                        <strong>{item.title}</strong>
                        <p className="muted">{item.item_type} · score {item.priority_score}</p>
                        <p className="muted">{item.reason}</p>
                        <p className="muted">→ {item.recommended_action}</p>
                      </div>
                    ))}
                  </>
                )}

                <form className="stacked-form" onSubmit={handleCreateFollowup}>
                  <h3>New follow-up</h3>
                  <input type="text" placeholder="Title" value={followupTitle} onChange={(event) => setFollowupTitle(event.target.value)} />
                  <input type="text" placeholder="Due date YYYY-MM-DD" value={followupDueDate} onChange={(event) => setFollowupDueDate(event.target.value)} />
                  <select value={followupPriority} onChange={(event) => setFollowupPriority(event.target.value)}>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                  <button type="submit" disabled={chiefBusy || !followupTitle.trim()}>Add follow-up</button>
                </form>

                {chiefFollowups.filter((item) => item.status === 'open' || item.status === 'snoozed').length > 0 && (
                  <>
                    <h3>Open follow-ups {chiefOverdueCount > 0 ? `(${chiefOverdueCount} overdue)` : ''}</h3>
                    {chiefFollowups
                      .filter((item) => item.status === 'open' || item.status === 'snoozed')
                      .slice(0, 8)
                      .map((followup) => (
                        <div className="agent-template-card" key={followup.followup_id}>
                          <strong>{followup.title}</strong>
                          <p className="muted">{followup.priority} · due {followup.due_date || 'n/a'} · {followup.status}</p>
                          <div className="inline-actions">
                            <button type="button" onClick={() => handleMarkFollowupDone(followup.followup_id)} disabled={chiefBusy}>
                              Mark done
                            </button>
                          </div>
                        </div>
                      ))}
                  </>
                )}

                <p className="muted">Recommendations only — no reminders are sent, no calendar/email is written, nothing runs automatically.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowSimulatorPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Business Simulator
              </span>
              <ChevronDown size={15} />
            </button>
            {showSimulatorPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Autonomous Business Simulator · v20.0</strong>
                  <span>Simulate decisions, cost, time, and risk before acting. Simulation only — not financial advice.</span>
                </div>
                {simulatorDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Scenarios</span><strong>{simulatorDashboard.total_scenarios}</strong></div>
                    <div><span>Results</span><strong>{simulatorDashboard.total_results}</strong></div>
                    <div><span>Avg risk</span><strong>{simulatorDashboard.average_risk_score}</strong></div>
                    <div><span>High risk</span><strong>{(simulatorDashboard.high_risk_scenarios || []).length}</strong></div>
                  </div>
                )}
                {simulatorDashboard?.recommended_next_simulation && (
                  <p className="muted">Next: {simulatorDashboard.recommended_next_simulation}</p>
                )}
                {simulatorError && <p className="error-text">{simulatorError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshSimulatorPanel(workspaceId)} disabled={simulatorBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateScenario}>
                  <h3>New scenario</h3>
                  <input type="text" placeholder="Title (e.g. Launch with 3 features)" value={scenarioTitle} onChange={(event) => setScenarioTitle(event.target.value)} />
                  <select value={scenarioType} onChange={(event) => setScenarioType(event.target.value)}>
                    <option value="decision">decision</option>
                    <option value="cost">cost</option>
                    <option value="time">time</option>
                    <option value="risk">risk</option>
                    <option value="launch">launch</option>
                    <option value="workflow">workflow</option>
                    <option value="custom">custom</option>
                  </select>
                  <input type="text" placeholder="Assumptions (comma separated)" value={scenarioAssumptions} onChange={(event) => setScenarioAssumptions(event.target.value)} />
                  <input type="text" placeholder="Options (comma separated)" value={scenarioOptions} onChange={(event) => setScenarioOptions(event.target.value)} />
                  <button type="submit" disabled={simulatorBusy || !scenarioTitle.trim()}>Create scenario</button>
                </form>

                {simulatorScenarios.length > 0 && (
                  <>
                    <h3>Scenarios</h3>
                    {simulatorScenarios.slice(0, 6).map((scenario) => (
                      <div className="agent-template-card" key={scenario.scenario_id}>
                        <strong>{scenario.title}</strong>
                        <p className="muted">{scenario.scenario_type} · {(scenario.options || []).length} option(s)</p>
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleRunSimulation(scenario.scenario_id)} disabled={simulatorBusy}>
                            Run simulation
                          </button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {latestSimResult && (
                  <div className="agent-template-card">
                    <strong>Latest result (simulation only)</strong>
                    <span>{latestSimResult.summary}</span>
                    <p className="muted">Decision score: {latestSimResult.decision_score}/100 · Confidence: {latestSimResult.confidence}</p>
                    <p className="muted">
                      Cost (est.): ${latestSimResult.cost_estimate?.low}–${latestSimResult.cost_estimate?.high}
                      (~${latestSimResult.cost_estimate?.expected})
                    </p>
                    <p className="muted">
                      Time (est.): {latestSimResult.time_estimate?.best_case_days}–{latestSimResult.time_estimate?.worst_case_days} days
                      (~{latestSimResult.time_estimate?.expected_days})
                    </p>
                    <p className="muted">
                      Risk: {latestSimResult.risk_estimate?.risk_level} ({latestSimResult.risk_estimate?.risk_score})
                    </p>
                    {(latestSimResult.option_comparison || []).length > 0 && (
                      <>
                        <p className="muted">Option comparison:</p>
                        {latestSimResult.option_comparison.map((option, index) => (
                          <p className="muted" key={index}>
                            • {option.option}: ~${option.estimated_cost}, ~{option.estimated_days}d, {option.risk_level} risk
                          </p>
                        ))}
                      </>
                    )}
                    <p className="muted">→ {latestSimResult.recommendation}</p>
                  </div>
                )}

                {simulatorResults.length > 0 && (
                  <>
                    <h3>Recent results</h3>
                    {simulatorResults.slice(0, 5).map((result) => (
                      <div className="agent-template-card" key={result.result_id}>
                        <strong>{result.risk_estimate?.risk_level} risk · score {result.decision_score}</strong>
                        <span>{result.summary}</span>
                      </div>
                    ))}
                  </>
                )}

                <p className="muted">Simulation only — rough estimates, not financial advice; nothing is executed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowMultimodalPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Multi-Modal Agent
              </span>
              <ChevronDown size={15} />
            </button>
            {showMultimodalPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Multi-Modal Agent · v21.0</strong>
                  <span>Describe a screenshot, UI bug, diagram, or whiteboard to get a structured plan. Local, demo-safe analysis.</span>
                </div>
                {multimodalDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Items</span><strong>{multimodalDashboard.total_items}</strong></div>
                    <div><span>Analyses</span><strong>{multimodalDashboard.total_analyses}</strong></div>
                    <div><span>Issues</span><strong>{multimodalDashboard.total_issues_found}</strong></div>
                    <div><span>Demo-safe</span><strong>{multimodalDashboard.mock_mode ? 'on' : 'off'}</strong></div>
                  </div>
                )}
                {multimodalError && <p className="error-text">{multimodalError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshMultimodalPanel(workspaceId)} disabled={multimodalBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateMultimodalItem}>
                  <h3>New visual item</h3>
                  <input type="text" placeholder="Title" value={mmTitle} onChange={(event) => setMmTitle(event.target.value)} />
                  <select value={mmType} onChange={(event) => setMmType(event.target.value)}>
                    <option value="screenshot">screenshot</option>
                    <option value="ui_bug">ui_bug</option>
                    <option value="diagram">diagram</option>
                    <option value="whiteboard">whiteboard</option>
                    <option value="document_image">document_image</option>
                    <option value="custom">custom</option>
                  </select>
                  <textarea placeholder="Describe what the image shows" value={mmDescription} onChange={(event) => setMmDescription(event.target.value)} rows={3} />
                  <button type="submit" disabled={multimodalBusy || !mmTitle.trim()}>Create item</button>
                </form>

                {multimodalItems.length > 0 && (
                  <>
                    <h3>Items</h3>
                    {multimodalItems.slice(0, 6).map((item) => (
                      <div className="agent-template-card" key={item.item_id}>
                        <strong>{item.title}</strong>
                        <p className="muted">{item.item_type}</p>
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleAnalyzeMultimodalItem(item.item_id, item.item_type)} disabled={multimodalBusy}>
                            Analyze
                          </button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {latestMmAnalysis && (
                  <div className="agent-template-card">
                    <strong>Latest analysis · {latestMmAnalysis.analysis_type} (mock)</strong>
                    <span>{latestMmAnalysis.summary}</span>
                    {(latestMmAnalysis.detected_elements || []).length > 0 && (
                      <p className="muted">Detected: {latestMmAnalysis.detected_elements.join(', ')}</p>
                    )}
                    {(latestMmAnalysis.issues || []).length > 0 && (
                      <p className="muted">Issues: {latestMmAnalysis.issues.join('; ')}</p>
                    )}
                    {(latestMmAnalysis.recommended_actions || []).map((action, index) => (
                      <p className="muted" key={index}>→ {action}</p>
                    ))}
                    <p className="muted">Confidence: {latestMmAnalysis.confidence}</p>
                  </div>
                )}

                <p className="muted">Local, demo-safe analysis — no external vision API is called.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowIndustryPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Industry Modes
              </span>
              <ChevronDown size={15} />
            </button>
            {showIndustryPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Industry Workflow Modes · v22.0</strong>
                  <span>Configure terminology, recommended agents, templates, and risk/approval rules per industry.</span>
                </div>
                {industryDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Modes</span><strong>{industryDashboard.total_modes}</strong></div>
                    <div><span>Enabled</span><strong>{industryDashboard.enabled_modes}</strong></div>
                    <div><span>Runs</span><strong>{industryDashboard.total_runs}</strong></div>
                  </div>
                )}
                {industryError && <p className="error-text">{industryError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleSeedIndustryModes} disabled={industryBusy}>Seed default modes</button>
                  <button type="button" onClick={() => refreshIndustryPanel()} disabled={industryBusy}>Refresh</button>
                </div>

                {industryModes.length > 0 && (
                  <>
                    <h3>Modes</h3>
                    {industryModes.map((mode) => (
                      <div className="agent-template-card" key={mode.mode_id}>
                        <strong>{mode.name} {mode.enabled === false ? '· disabled' : ''}</strong>
                        <span>{mode.description}</span>
                        <p className="muted">Agents: {(mode.recommended_agents || []).join(', ') || '—'}</p>
                        <p className="muted">Templates: {(mode.workflow_templates || []).join('; ') || '—'}</p>
                        <p className="muted">Risk rules: {(mode.risk_rules || []).join('; ') || '—'}</p>
                        <p className="muted">Approval: {(mode.approval_rules || []).join('; ') || '—'}</p>
                      </div>
                    ))}
                  </>
                )}

                <form className="stacked-form" onSubmit={handleRunIndustryMode}>
                  <h3>Run a mode</h3>
                  <select value={industryRunModeId} onChange={(event) => setIndustryRunModeId(event.target.value)}>
                    <option value="">Select mode…</option>
                    {industryModes
                      .filter((mode) => mode.enabled !== false)
                      .map((mode) => (
                        <option key={mode.mode_id} value={mode.mode_id}>{mode.name}</option>
                      ))}
                  </select>
                  <input type="text" placeholder="Prompt for this mode" value={industryPrompt} onChange={(event) => setIndustryPrompt(event.target.value)} />
                  <button type="submit" disabled={industryBusy || !industryRunModeId || !industryPrompt.trim()}>Run mode</button>
                </form>

                {industryRuns.length > 0 && (
                  <>
                    <h3>Recent runs</h3>
                    {industryRuns.slice(0, 5).map((run) => (
                      <div className="agent-template-card" key={run.run_id}>
                        <strong>{run.mode_name}</strong>
                        <span>{run.prompt}</span>
                        <p className="muted">{run.requires_approval ? 'approval required' : 'no approval'} · {run.status}</p>
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowAgentNetworkPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Agent Network
              </span>
              <ChevronDown size={15} />
            </button>
            {showAgentNetworkPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Agent-to-Agent Network · v23.0</strong>
                  <span>Local task contracts, demo-safe handoffs, result verification, and audit logs. No real external agent calls.</span>
                </div>
                {agentNetworkDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Contracts</span><strong>{agentNetworkDashboard.total_contracts}</strong></div>
                    <div><span>Handoffs</span><strong>{agentNetworkDashboard.total_handoffs}</strong></div>
                    <div><span>Verified</span><strong>{agentNetworkDashboard.verified_handoffs}</strong></div>
                    <div><span>Audits</span><strong>{agentNetworkDashboard.audit_event_count}</strong></div>
                  </div>
                )}
                {agentNetworkError && <p className="error-text">{agentNetworkError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshAgentNetworkPanel()} disabled={agentNetworkBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateContract}>
                  <h3>New task contract</h3>
                  <input type="text" placeholder="Target agent" value={contractTarget} onChange={(event) => setContractTarget(event.target.value)} />
                  <input type="text" placeholder="Task" value={contractTask} onChange={(event) => setContractTask(event.target.value)} />
                  <input type="text" placeholder="Expected output" value={contractExpected} onChange={(event) => setContractExpected(event.target.value)} />
                  <button type="submit" disabled={agentNetworkBusy || !contractTask.trim()}>Create contract</button>
                </form>

                {agentNetworkContracts.length > 0 && (
                  <>
                    <h3>Contracts</h3>
                    {agentNetworkContracts.slice(0, 6).map((contract) => (
                      <div className="agent-template-card" key={contract.contract_id}>
                        <strong>{contract.source_agent} → {contract.target_agent}</strong>
                        <span>{contract.task}</span>
                        <p className="muted">Status: {contract.status}</p>
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleCreateHandoff(contract.contract_id, 'local')} disabled={agentNetworkBusy}>
                            Handoff
                          </button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {latestHandoff && (
                  <div className="agent-template-card">
                    <strong>Latest handoff · {latestHandoff.handoff_type} ({latestHandoff.status})</strong>
                    <span>{latestHandoff.result?.output}</span>
                    {latestHandoff.verification?.verified !== undefined && (
                      <p className="muted">Verified: {String(latestHandoff.verification.verified)}</p>
                    )}
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleVerifyHandoff(latestHandoff.handoff_id)} disabled={agentNetworkBusy}>
                        Verify
                      </button>
                    </div>
                  </div>
                )}

                {agentNetworkAudit.length > 0 && (
                  <>
                    <h3>Audit log</h3>
                    {agentNetworkAudit.slice(0, 6).map((entry) => (
                      <p className="muted" key={entry.audit_id}>{entry.event_type}: {entry.detail}</p>
                    ))}
                  </>
                )}

                <p className="muted">Local, demo-safe protocol — no real external agent is contacted; every action is audited.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowHealingPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Self-Healing
              </span>
              <ChevronDown size={15} />
            </button>
            {showHealingPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Self-Healing Project System · v24.0</strong>
                  <span>Run allowlisted build/test checks, parse findings, draft repair tasks, verify. No auto-apply.</span>
                </div>
                {healingDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Checks</span><strong>{healingDashboard.total_checks}</strong></div>
                    <div><span>Failed</span><strong>{healingDashboard.failed_checks}</strong></div>
                    <div><span>Blocked</span><strong>{healingDashboard.blocked_checks}</strong></div>
                    <div><span>Findings</span><strong>{healingDashboard.open_findings}</strong></div>
                    <div><span>Drafts</span><strong>{healingDashboard.repair_drafts}</strong></div>
                    <div><span>Verified</span><strong>{healingDashboard.verified_repairs}</strong></div>
                  </div>
                )}
                {healingError && <p className="error-text">{healingError}</p>}
                <div className="inline-actions">
                  <select value={healingCommand} onChange={(event) => setHealingCommand(event.target.value)}>
                    <option value="pytest">pytest</option>
                    <option value="npm run build">npm run build</option>
                  </select>
                  <button type="button" onClick={handleRunHealingCheck} disabled={healingBusy}>Run check</button>
                  <button type="button" onClick={() => refreshHealingPanel()} disabled={healingBusy}>Refresh</button>
                </div>

                {healingFindings.length > 0 && (
                  <>
                    <h3>Findings</h3>
                    {healingFindings.slice(0, 6).map((finding) => (
                      <div className="agent-template-card" key={finding.finding_id}>
                        <strong>{finding.finding_type} · {finding.severity}</strong>
                        <span>{finding.message}</span>
                        <p className="muted">Status: {finding.status}</p>
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleCreateRepairTask(finding.finding_id)} disabled={healingBusy}>
                            Draft repair task
                          </button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {healingRepairs.length > 0 && (
                  <>
                    <h3>Repair drafts (approval required)</h3>
                    {healingRepairs.slice(0, 5).map((repair) => (
                      <div className="agent-template-card" key={repair.repair_id}>
                        <strong>{repair.title}</strong>
                        <p className="muted">Status: {repair.status} · verify: {repair.verify_command}</p>
                        {(repair.suggested_patch_plan || []).map((step, index) => (
                          <p className="muted" key={index}>• {step}</p>
                        ))}
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleVerifyRepair(repair.repair_id)} disabled={healingBusy}>
                            Verify
                          </button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                <p className="muted">No auto-apply — repairs are drafts requiring human approval; only allowlisted commands run; no package installs.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowCompanyBrainPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Company Brain
              </span>
              <ChevronDown size={15} />
            </button>
            {showCompanyBrainPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>AI Company Brain · v25.0</strong>
                  <span>One company-level view across departments, workforce, business, projects, risks, and governance.</span>
                </div>
                {companyBrainDashboard && (
                  <>
                    <div className="analytics-mini-grid">
                      <div><span>Health</span><strong>{companyBrainDashboard.company_health_score}</strong></div>
                      <div><span>Depts</span><strong>{companyBrainDashboard.departments?.active}</strong></div>
                      <div><span>Agents</span><strong>{companyBrainDashboard.agent_workforce?.custom_agents}</strong></div>
                      <div><span>Leads</span><strong>{companyBrainDashboard.business?.total_leads}</strong></div>
                      <div><span>Goals</span><strong>{companyBrainDashboard.projects?.active_goals}</strong></div>
                      <div><span>Risks</span><strong>{(companyBrainDashboard.risks || []).length}</strong></div>
                    </div>
                    <div className="agent-template-card">
                      <strong>Business</strong>
                      <p className="muted">
                        Won {companyBrainDashboard.business?.won_leads} · Conv {companyBrainDashboard.business?.conversion_rate}% ·
                        Open cases {companyBrainDashboard.business?.open_support_cases}
                      </p>
                    </div>
                    <div className="agent-template-card">
                      <strong>Projects / Portfolio</strong>
                      <p className="muted">
                        {companyBrainDashboard.projects?.completed_goals}/{companyBrainDashboard.projects?.total_goals} goals done ·
                        {companyBrainDashboard.projects?.portfolio_reports} portfolio report(s)
                      </p>
                    </div>
                    {(companyBrainDashboard.risks || []).length > 0 && (
                      <>
                        <h3>Top risks</h3>
                        {companyBrainDashboard.risks.slice(0, 5).map((risk, index) => (
                          <p className="muted" key={index}>• {risk.title} ({risk.severity})</p>
                        ))}
                      </>
                    )}
                    <h3>Recommended next actions</h3>
                    {(companyBrainDashboard.recommended_next_actions || []).map((action, index) => (
                      <p className="muted" key={index}>→ {action}</p>
                    ))}
                  </>
                )}
                {companyBrainError && <p className="error-text">{companyBrainError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleGenerateCompanyReport} disabled={companyBrainBusy}>Generate report</button>
                  <button type="button" onClick={() => refreshCompanyBrainPanel()} disabled={companyBrainBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateStrategy}>
                  <h3>Generate strategy</h3>
                  <input type="text" placeholder="Strategy title" value={strategyTitle} onChange={(event) => setStrategyTitle(event.target.value)} />
                  <button type="submit" disabled={companyBrainBusy || !strategyTitle.trim()}>Create strategy</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateCompanyDecision}>
                  <h3>Log a decision</h3>
                  <input type="text" placeholder="Decision title" value={decisionTitle} onChange={(event) => setDecisionTitle(event.target.value)} />
                  <select value={decisionImpact} onChange={(event) => setDecisionImpact(event.target.value)}>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                  <button type="submit" disabled={companyBrainBusy || !decisionTitle.trim()}>Log decision</button>
                </form>

                {companyBrainReport && (
                  <div className="agent-template-card">
                    <strong>Latest report</strong>
                    <span>{companyBrainReport.headline}</span>
                  </div>
                )}

                {companyBrainDecisions.length > 0 && (
                  <>
                    <h3>Recent decisions</h3>
                    {companyBrainDecisions.slice(0, 5).map((decision) => (
                      <div className="agent-template-card" key={decision.decision_id}>
                        <strong>{decision.title}</strong>
                        <p className="muted">Impact: {decision.impact}</p>
                      </div>
                    ))}
                  </>
                )}

                <p className="muted">Aggregated from local data only — recommendations, not automated execution.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowDevicePanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Device Operator
              </span>
              <ChevronDown size={15} />
            </button>
            {showDevicePanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Personal Device Operator · v26.0</strong>
                  <span>Plan phone/device actions from voice/text + provided screen text. Demo-safe planning — no real device control.</span>
                </div>
                {deviceDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Sessions</span><strong>{deviceDashboard.total_sessions}</strong></div>
                    <div><span>Actions</span><strong>{deviceDashboard.total_actions}</strong></div>
                    <div><span>Blocked</span><strong>{deviceDashboard.blocked_actions}</strong></div>
                    <div><span>Awaiting</span><strong>{deviceDashboard.actions_awaiting_confirmation}</strong></div>
                  </div>
                )}
                {deviceError && <p className="error-text">{deviceError}</p>}
                <div className="inline-actions">
                  <select value={devicePermission} onChange={(event) => setDevicePermission(event.target.value)}>
                    <option value="suggest_only">suggest_only</option>
                    <option value="read_screen_only">read_screen_only</option>
                    <option value="tap_type_with_confirmation">tap_type_with_confirmation</option>
                    <option value="auto_safe_actions">auto_safe_actions</option>
                    <option value="blocked">blocked</option>
                  </select>
                  <button type="button" onClick={handleCreateDeviceSession} disabled={deviceBusy}>New session</button>
                  <button type="button" onClick={() => refreshDevicePanel()} disabled={deviceBusy}>Refresh</button>
                </div>

                {deviceSessions.length > 0 && (
                  <>
                    <h3>Sessions</h3>
                    <select value={deviceSessionId} onChange={(event) => setDeviceSessionId(event.target.value)}>
                      <option value="">Select session…</option>
                      {deviceSessions.map((session) => (
                        <option key={session.session_id} value={session.session_id}>
                          {session.device_label} · {session.permission_level}
                        </option>
                      ))}
                    </select>
                  </>
                )}

                <form className="stacked-form" onSubmit={handlePlanDevice}>
                  <h3>Plan actions</h3>
                  <input type="text" placeholder="Voice/text command" value={deviceCommand} onChange={(event) => setDeviceCommand(event.target.value)} />
                  <textarea placeholder="Screen text (read-screen mode)" value={deviceScreenText} onChange={(event) => setDeviceScreenText(event.target.value)} rows={2} />
                  <button type="submit" disabled={deviceBusy || !deviceSessionId || (!deviceCommand.trim() && !deviceScreenText.trim())}>Plan</button>
                </form>

                {devicePlannedActions.length > 0 && (
                  <>
                    <h3>Planned actions</h3>
                    {devicePlannedActions.map((action) => (
                      <div className="agent-template-card" key={action.action_id}>
                        <strong>{action.action_type} · {action.risk_level} risk</strong>
                        <span>{action.description}</span>
                        <p className="muted">Status: {action.status}{action.blocked ? ' · blocked' : ''}</p>
                        {action.requires_confirmation && !action.blocked && (
                          <div className="inline-actions">
                            <button type="button" onClick={() => handleConfirmDeviceAction(action.action_id, true)} disabled={deviceBusy}>Confirm</button>
                            <button type="button" onClick={() => handleConfirmDeviceAction(action.action_id, false)} disabled={deviceBusy}>Reject</button>
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}

                {deviceAudit.length > 0 && (
                  <>
                    <h3>Audit</h3>
                    {deviceAudit.slice(0, 6).map((entry) => (
                      <p className="muted" key={entry.audit_id}>{entry.event_type}: {entry.detail}</p>
                    ))}
                  </>
                )}

                <p className="muted">Demo-safe planning — no real phone automation; send/pay/delete/share/password/call/post/submit require approval; dangerous actions blocked.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowTrainingPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Training Lab
              </span>
              <ChevronDown size={15} />
            </button>
            {showTrainingPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Private Training Lab · v27.0</strong>
                  <span>Prepare approved, sanitized fine-tuning datasets. The app does not train the base model automatically.</span>
                </div>
                {trainingDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Datasets</span><strong>{trainingDashboard.total_datasets}</strong></div>
                    <div><span>Examples</span><strong>{trainingDashboard.total_examples}</strong></div>
                    <div><span>Approved</span><strong>{trainingDashboard.approved_examples}</strong></div>
                    <div><span>Redacted</span><strong>{trainingDashboard.examples_with_redactions}</strong></div>
                    <div><span>Exports</span><strong>{trainingDashboard.total_exports}</strong></div>
                    <div><span>Runs</span><strong>{trainingDashboard.total_runs}</strong></div>
                  </div>
                )}
                {trainingError && <p className="error-text">{trainingError}</p>}

                <form className="stacked-form" onSubmit={handleCreateDataset}>
                  <h3>New dataset</h3>
                  <input type="text" placeholder="Dataset name" value={datasetName} onChange={(event) => setDatasetName(event.target.value)} />
                  <button type="submit" disabled={trainingBusy || !datasetName.trim()}>Create</button>
                </form>

                {trainingDatasets.length > 0 && (
                  <>
                    <h3>Datasets</h3>
                    <select value={trainingDatasetId} onChange={(event) => handleSelectTrainingDataset(event.target.value)}>
                      <option value="">Select dataset…</option>
                      {trainingDatasets.map((dataset) => (
                        <option key={dataset.dataset_id} value={dataset.dataset_id}>{dataset.name}</option>
                      ))}
                    </select>
                    <div className="inline-actions">
                      <button type="button" onClick={handleExportDataset} disabled={trainingBusy || !trainingDatasetId}>Export approved (JSONL)</button>
                      <button type="button" onClick={handleCreateTrainingRun} disabled={trainingBusy}>Dry run</button>
                    </div>
                  </>
                )}

                <form className="stacked-form" onSubmit={handleAddExample}>
                  <h3>Add example (auto-redacted)</h3>
                  <textarea placeholder="Prompt" value={examplePrompt} onChange={(event) => setExamplePrompt(event.target.value)} rows={2} />
                  <textarea placeholder="Completion" value={exampleCompletion} onChange={(event) => setExampleCompletion(event.target.value)} rows={2} />
                  <button type="submit" disabled={trainingBusy || !trainingDatasetId || !examplePrompt.trim()}>Add example</button>
                </form>

                {trainingExamples.length > 0 && (
                  <>
                    <h3>Examples</h3>
                    {trainingExamples.slice(0, 8).map((example) => (
                      <div className="agent-template-card" key={example.example_id}>
                        <strong>{example.status}</strong>
                        <span>{example.prompt.slice(0, 120)}</span>
                        {(example.redaction?.secrets_detected || example.redaction?.pii_detected) && (
                          <p className="muted">Redacted: {[...(example.redaction.secret_types || []), ...(example.redaction.pii_types || [])].join(', ')}</p>
                        )}
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleSetExampleStatus(example.example_id, 'approved')} disabled={trainingBusy}>Approve</button>
                          <button type="button" onClick={() => handleSetExampleStatus(example.example_id, 'rejected')} disabled={trainingBusy}>Reject</button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {trainingExport && (
                  <div className="agent-template-card">
                    <strong>Export · {trainingExport.approved_example_count} approved</strong>
                    <p className="muted">Excluded non-approved: {trainingExport.excluded_non_approved}</p>
                    <p className="muted">{trainingExport.safety_note}</p>
                  </div>
                )}

                <p className="muted">No auto-training — only approved + sanitized examples export; secrets and PII are redacted before inclusion.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="agent" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowAvatarPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Avatar / Voice Twin
              </span>
              <ChevronDown size={15} />
            </button>
            {showAvatarPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Personal AI Avatar / Voice Twin · v28.0</strong>
                  <span>Persona, voice-response, and meeting-assistant settings. The avatar is always an AI — no impersonation, no voice cloning.</span>
                </div>
                {avatarDashboard && (
                  <div className="provider-card">
                    <div><span>Avatar</span><strong>{avatarDashboard.persona?.avatar_name}</strong></div>
                    <div><span>Tone</span><strong>{avatarDashboard.persona?.tone}</strong></div>
                    <div><span>Voice</span><strong>{avatarDashboard.voice_settings?.voice_mode}</strong></div>
                    <div><span>Consent</span><strong>{String(avatarDashboard.latest_consent_granted)}</strong></div>
                  </div>
                )}
                {avatarError && <p className="error-text">{avatarError}</p>}

                {avatarDashboard?.persona?.avatar_image?.image_url && (
                  <div className="agent-template-card">
                    <strong>Avatar</strong>
                    <img
                      src={avatarDashboard.persona.avatar_image.image_url}
                      alt={`${avatarDashboard.persona.avatar_name} avatar`}
                      style={{ width: '120px', height: '120px', borderRadius: '12px', objectFit: 'cover', marginTop: '8px' }}
                    />
                    <p className="muted">
                      {avatarDashboard.persona.avatar_image.mock_preview ? 'Mock preview' : avatarDashboard.persona.avatar_image.provider} ·
                      {' '}{avatarDashboard.persona.avatar_image.style}
                    </p>
                    <p className="muted">{avatarDashboard.persona.avatar_image.note}</p>
                  </div>
                )}

                <form className="stacked-form" onSubmit={handleGenerateAvatarImage}>
                  <h3>Generate avatar (looks like you)</h3>
                  <textarea
                    placeholder="Describe how it should look (e.g. short black hair, glasses, friendly smile, hoodie)"
                    value={avatarDescription}
                    onChange={(event) => setAvatarDescription(event.target.value)}
                    rows={2}
                  />
                  <select value={avatarStyle} onChange={(event) => setAvatarStyle(event.target.value)}>
                    <option value="illustrated">illustrated</option>
                    <option value="cartoon">cartoon</option>
                    <option value="minimal">minimal</option>
                    <option value="3d_stylized">3d_stylized</option>
                    <option value="pixel">pixel</option>
                  </select>
                  <button type="submit" disabled={avatarBusy}>Generate avatar</button>
                  <p className="muted">Stylized avatar from your description (mock preview unless real image mode is enabled). Not a photo-real clone; never claims to be you.</p>
                </form>

                <form className="stacked-form" onSubmit={handleSavePersona}>
                  <h3>Persona</h3>
                  <input type="text" placeholder="Avatar name" value={avatarName} onChange={(event) => setAvatarName(event.target.value)} />
                  <select value={avatarTone} onChange={(event) => setAvatarTone(event.target.value)}>
                    <option value="friendly">friendly</option>
                    <option value="professional">professional</option>
                    <option value="concise">concise</option>
                    <option value="encouraging">encouraging</option>
                    <option value="neutral">neutral</option>
                  </select>
                  <button type="submit" disabled={avatarBusy}>Save persona</button>
                </form>

                <h3>Voice response mode</h3>
                <div className="inline-actions">
                  {['text_only', 'spoken_summary_ready', 'disabled'].map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      onClick={() => handleSaveVoiceMode(mode)}
                      disabled={avatarBusy}
                      className={avatarVoiceMode === mode ? 'active' : ''}
                    >
                      {mode}
                    </button>
                  ))}
                </div>

                <form className="stacked-form" onSubmit={handleCreateMeetingSession}>
                  <h3>Meeting assistant session</h3>
                  <input type="text" placeholder="Meeting title" value={meetingTitle} onChange={(event) => setMeetingTitle(event.target.value)} />
                  <button type="submit" disabled={avatarBusy || !meetingTitle.trim()}>Create session</button>
                </form>

                {avatarMeetings.length > 0 && (
                  <>
                    <h3>Recent meeting sessions</h3>
                    {avatarMeetings.slice(0, 5).map((session) => (
                      <div className="agent-template-card" key={session.meeting_session_id}>
                        <strong>{session.title}</strong>
                        <p className="muted">{session.status} · consent required</p>
                      </div>
                    ))}
                  </>
                )}

                <div className="inline-actions">
                  <button type="button" onClick={handleGrantConsent} disabled={avatarBusy}>Record consent</button>
                  <button type="button" onClick={() => refreshAvatarPanel()} disabled={avatarBusy}>Refresh</button>
                </div>

                {avatarDashboard?.safety_rules && (
                  <>
                    <h3>Safety</h3>
                    {avatarDashboard.safety_rules.map((rule, index) => (
                      <p className="muted" key={index}>• {rule}</p>
                    ))}
                  </>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowLifePanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Life OS
              </span>
              <ChevronDown size={15} />
            </button>
            {showLifePanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Real-Time Life OS · v29.0</strong>
                  <span>Plan your day from local schedule, tasks, reminders, and deadlines. No real calendar/email integration.</span>
                </div>
                {lifeDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Tasks</span><strong>{lifeDashboard.active_task_count}</strong></div>
                    <div><span>Overdue</span><strong>{lifeDashboard.overdue_task_count}</strong></div>
                    <div><span>Events</span><strong>{lifeDashboard.schedule_item_count}</strong></div>
                    <div><span>Reminders</span><strong>{lifeDashboard.open_reminder_count}</strong></div>
                    <div><span>Deadlines</span><strong>{lifeDashboard.upcoming_deadline_count}</strong></div>
                    <div><span>Today</span><strong>{lifeDashboard.today}</strong></div>
                  </div>
                )}
                {lifeError && <p className="error-text">{lifeError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleGenerateLifeDailyPlan} disabled={lifeBusy}>Generate daily plan</button>
                  <button type="button" onClick={() => refreshLifePanel(workspaceId)} disabled={lifeBusy}>Refresh</button>
                </div>

                {lifeDailyPlan && (
                  <div className="agent-template-card">
                    <strong>Daily plan · {lifeDailyPlan.date}</strong>
                    <span>{lifeDailyPlan.summary}</span>
                    <p className="muted">Focus: {lifeDailyPlan.focus_suggestion}</p>
                  </div>
                )}

                <form className="stacked-form" onSubmit={handleCreateLifeTask}>
                  <h3>New task</h3>
                  <input type="text" placeholder="Task title" value={lifeTaskTitle} onChange={(event) => setLifeTaskTitle(event.target.value)} />
                  <select value={lifeTaskPriority} onChange={(event) => setLifeTaskPriority(event.target.value)}>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                  <input type="text" placeholder="Due date YYYY-MM-DD" value={lifeTaskDue} onChange={(event) => setLifeTaskDue(event.target.value)} />
                  <button type="submit" disabled={lifeBusy || !lifeTaskTitle.trim()}>Add task</button>
                </form>

                {lifeTasks.length > 0 && (
                  <>
                    <h3>Top tasks (ranked)</h3>
                    {lifeTasks.slice(0, 6).map((task) => (
                      <div className="agent-template-card" key={task.task_id}>
                        <strong>{task.title}</strong>
                        <p className="muted">
                          {task.priority} · score {task.priority_score}
                          {task.overdue ? ' · overdue' : task.days_until_due != null ? ` · in ${task.days_until_due}d` : ''}
                        </p>
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleCompleteLifeTask(task.task_id)} disabled={lifeBusy}>Mark done</button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                <form className="stacked-form" onSubmit={handleCreateLifeSchedule}>
                  <h3>New schedule item</h3>
                  <input type="text" placeholder="Event title" value={lifeScheduleTitle} onChange={(event) => setLifeScheduleTitle(event.target.value)} />
                  <input type="text" placeholder="Date YYYY-MM-DD" value={lifeScheduleDate} onChange={(event) => setLifeScheduleDate(event.target.value)} />
                  <button type="submit" disabled={lifeBusy || !lifeScheduleTitle.trim()}>Add event</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateLifeReminder}>
                  <h3>New reminder</h3>
                  <input type="text" placeholder="Reminder title" value={lifeReminderTitle} onChange={(event) => setLifeReminderTitle(event.target.value)} />
                  <input type="text" placeholder="Remind on YYYY-MM-DD" value={lifeReminderOn} onChange={(event) => setLifeReminderOn(event.target.value)} />
                  <button type="submit" disabled={lifeBusy || !lifeReminderTitle.trim()}>Add reminder</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateLifeDeadline}>
                  <h3>New deadline</h3>
                  <input type="text" placeholder="Deadline title" value={lifeDeadlineTitle} onChange={(event) => setLifeDeadlineTitle(event.target.value)} />
                  <select value={lifeDeadlineKind} onChange={(event) => setLifeDeadlineKind(event.target.value)}>
                    <option value="school">school</option>
                    <option value="work">work</option>
                    <option value="personal">personal</option>
                    <option value="other">other</option>
                  </select>
                  <input type="text" placeholder="Due date YYYY-MM-DD" value={lifeDeadlineDue} onChange={(event) => setLifeDeadlineDue(event.target.value)} />
                  <button type="submit" disabled={lifeBusy || !lifeDeadlineTitle.trim()}>Add deadline</button>
                </form>

                {lifeDeadlines.length > 0 && (
                  <>
                    <h3>Deadlines</h3>
                    {lifeDeadlines.slice(0, 5).map((deadline) => (
                      <div className="agent-template-card" key={deadline.deadline_id}>
                        <strong>{deadline.title}</strong>
                        <p className="muted">
                          {deadline.kind} · {deadline.due_date || 'no date'}
                          {deadline.days_until_due != null ? ` · in ${deadline.days_until_due}d` : ''}
                        </p>
                      </div>
                    ))}
                  </>
                )}

                {lifeReminders.length > 0 && (
                  <>
                    <h3>Reminders</h3>
                    {lifeReminders.slice(0, 5).map((reminder) => (
                      <p className="muted" key={reminder.reminder_id}>• {reminder.title} ({reminder.status}{reminder.remind_on ? ` · ${reminder.remind_on}` : ''})</p>
                    ))}
                  </>
                )}

                <p className="muted">Local planning only — nothing is synced to a real calendar or sent anywhere.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="agent" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowUniversalPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Universal Operator
              </span>
              <ChevronDown size={15} />
            </button>
            {showUniversalPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Universal App Operator · v30.0</strong>
                  <span>Plan cross-app/desktop/browser workflows with a permission model and audit trail. Mock/planning-first — no real app automation.</span>
                </div>
                {universalDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Sessions</span><strong>{universalDashboard.total_sessions}</strong></div>
                    <div><span>Workflows</span><strong>{universalDashboard.total_workflows}</strong></div>
                    <div><span>Actions</span><strong>{universalDashboard.total_actions}</strong></div>
                    <div><span>Sensitive</span><strong>{universalDashboard.sensitive_actions}</strong></div>
                    <div><span>Awaiting</span><strong>{universalDashboard.actions_awaiting_approval}</strong></div>
                    <div><span>Handoffs</span><strong>{universalDashboard.total_handoffs}</strong></div>
                  </div>
                )}
                {universalError && <p className="error-text">{universalError}</p>}
                <div className="inline-actions">
                  <select value={universalSurface} onChange={(event) => setUniversalSurface(event.target.value)}>
                    <option value="cross_app">cross_app</option>
                    <option value="desktop">desktop</option>
                    <option value="browser">browser</option>
                    <option value="mobile">mobile</option>
                  </select>
                  <button type="button" onClick={handleCreateUniversalSession} disabled={universalBusy}>New session</button>
                  <button type="button" onClick={handleCreateUniversalHandoff} disabled={universalBusy}>Device handoff</button>
                  <button type="button" onClick={() => refreshUniversalPanel()} disabled={universalBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateUniversalWorkflow}>
                  <h3>New cross-app workflow</h3>
                  <input type="text" placeholder="Goal" value={universalGoal} onChange={(event) => setUniversalGoal(event.target.value)} />
                  <textarea placeholder="Steps (one per line, e.g. Read inbox / Draft reply / Send email)" value={universalSteps} onChange={(event) => setUniversalSteps(event.target.value)} rows={3} />
                  <button type="submit" disabled={universalBusy || !universalGoal.trim()}>Create workflow</button>
                </form>

                {universalWorkflows.length > 0 && (
                  <>
                    <h3>Workflows</h3>
                    {universalWorkflows.slice(0, 6).map((workflow) => (
                      <div className="agent-template-card" key={workflow.workflow_id}>
                        <strong>{workflow.goal}</strong>
                        <p className="muted">{workflow.status} · {(workflow.steps || []).length} step(s)</p>
                        <div className="inline-actions">
                          <button type="button" onClick={() => handlePlanUniversalWorkflow(workflow.workflow_id)} disabled={universalBusy}>Plan</button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {universalPlannedActions.length > 0 && (
                  <>
                    <h3>Planned actions</h3>
                    {universalPlannedActions.map((action) => (
                      <div className="agent-template-card" key={action.action_id}>
                        <strong>{action.permission_level}{action.sensitive ? ' · sensitive' : ''}</strong>
                        <span>{action.description}</span>
                        <p className="muted">Status: {action.status}</p>
                        {action.requires_approval && (
                          <div className="inline-actions">
                            <button type="button" onClick={() => handleDecideUniversalAction(action.action_id, 'approve')} disabled={universalBusy}>Approve</button>
                            <button type="button" onClick={() => handleDecideUniversalAction(action.action_id, 'reject')} disabled={universalBusy}>Reject</button>
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}

                {universalAudit.length > 0 && (
                  <>
                    <h3>Audit trail</h3>
                    {universalAudit.slice(0, 6).map((entry) => (
                      <p className="muted" key={entry.audit_id}>{entry.event_type}: {entry.detail}</p>
                    ))}
                  </>
                )}

                <p className="muted">Mock/planning-first — no real desktop/browser/app automation; sensitive actions (send/delete/pay/share) require approval; nothing is executed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowTeamPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Team Lead / Manager
              </span>
              <ChevronDown size={15} />
            </button>
            {showTeamPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>AI Team Lead / Manager · v31.0</strong>
                  <span>Manage a mixed human + AI team: members, assignments, standups, sprints, analytics. Local planning only.</span>
                </div>
                {teamDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Members</span><strong>{teamDashboard.member_count}</strong></div>
                    <div><span>AI</span><strong>{teamDashboard.ai_member_count}</strong></div>
                    <div><span>Done</span><strong>{teamDashboard.analytics?.completed_tasks}</strong></div>
                    <div><span>Blocked</span><strong>{teamDashboard.analytics?.blocked_tasks}</strong></div>
                    <div><span>Overdue</span><strong>{teamDashboard.analytics?.overdue_tasks}</strong></div>
                    <div><span>Sprints</span><strong>{teamDashboard.sprint_count}</strong></div>
                  </div>
                )}
                {teamError && <p className="error-text">{teamError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleGenerateStandup} disabled={teamBusy}>Generate standup</button>
                  <button type="button" onClick={() => refreshTeamPanel()} disabled={teamBusy}>Refresh</button>
                </div>

                {teamStandup && (
                  <div className="agent-template-card">
                    <strong>Standup · {teamStandup.date}</strong>
                    <span>{teamStandup.summary}</span>
                  </div>
                )}

                <form className="stacked-form" onSubmit={handleCreateTeamMember}>
                  <h3>Add member</h3>
                  <input type="text" placeholder="Name" value={memberName} onChange={(event) => setMemberName(event.target.value)} />
                  <select value={memberType} onChange={(event) => setMemberType(event.target.value)}>
                    <option value="human">human</option>
                    <option value="ai_agent">ai_agent</option>
                  </select>
                  <button type="submit" disabled={teamBusy || !memberName.trim()}>Add member</button>
                </form>

                {teamMembers.length > 0 && (
                  <>
                    <h3>Members</h3>
                    {teamMembers.slice(0, 6).map((member) => (
                      <p className="muted" key={member.member_id}>• {member.name} ({member.member_type}{member.role ? ` · ${member.role}` : ''})</p>
                    ))}
                  </>
                )}

                <form className="stacked-form" onSubmit={handleCreateTeamAssignment}>
                  <h3>New assignment</h3>
                  <input type="text" placeholder="Task title" value={assignmentTitle} onChange={(event) => setAssignmentTitle(event.target.value)} />
                  <input type="text" placeholder="Owner name" value={assignmentOwner} onChange={(event) => setAssignmentOwner(event.target.value)} />
                  <select value={assignmentPriority} onChange={(event) => setAssignmentPriority(event.target.value)}>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                  <button type="submit" disabled={teamBusy || !assignmentTitle.trim()}>Add assignment</button>
                </form>

                {teamAssignments.length > 0 && (
                  <>
                    <h3>Assignments</h3>
                    {teamAssignments.slice(0, 6).map((assignment) => (
                      <div className="agent-template-card" key={assignment.assignment_id}>
                        <strong>{assignment.title}</strong>
                        <p className="muted">{assignment.owner_name || 'unassigned'} · {assignment.priority} · {assignment.status}</p>
                        {assignment.status !== 'done' && (
                          <div className="inline-actions">
                            <button type="button" onClick={() => handleCompleteAssignment(assignment.assignment_id)} disabled={teamBusy}>Mark done</button>
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}

                <form className="stacked-form" onSubmit={handleCreateTeamSprint}>
                  <h3>New sprint</h3>
                  <input type="text" placeholder="Sprint name" value={sprintName} onChange={(event) => setSprintName(event.target.value)} />
                  <button type="submit" disabled={teamBusy || !sprintName.trim()}>Create sprint</button>
                </form>

                {teamSprints.length > 0 && (
                  <>
                    <h3>Sprints</h3>
                    {teamSprints.slice(0, 5).map((sprint) => (
                      <div className="agent-template-card" key={sprint.sprint_id}>
                        <strong>{sprint.name}</strong>
                        <p className="muted">{sprint.status}</p>
                        {sprint.status !== 'reviewed' && (
                          <div className="inline-actions">
                            <button type="button" onClick={() => handleReviewSprint(sprint.sprint_id)} disabled={teamBusy}>Review</button>
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}

                <p className="muted">Local planning only — no external messages sent and no real project state is changed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowSaasPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                SaaS Builder
              </span>
              <ChevronDown size={15} />
            </button>
            {showSaasPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Autonomous SaaS Builder · v32.0</strong>
                  <span>Plan and draft a SaaS: validation, roadmap, architecture, launch assets, feedback loop. Plans/drafts only — no deploy or payments.</span>
                </div>
                {saasDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Projects</span><strong>{saasDashboard.total_projects}</strong></div>
                    <div><span>Validations</span><strong>{saasDashboard.total_validations}</strong></div>
                    <div><span>Roadmaps</span><strong>{saasDashboard.total_roadmaps}</strong></div>
                    <div><span>Feedback</span><strong>{saasDashboard.total_feedback}</strong></div>
                  </div>
                )}
                {saasError && <p className="error-text">{saasError}</p>}

                <form className="stacked-form" onSubmit={handleCreateSaasProject}>
                  <h3>New SaaS project</h3>
                  <input type="text" placeholder="Project name" value={saasName} onChange={(event) => setSaasName(event.target.value)} />
                  <textarea placeholder="Idea (target user, pain, solution)" value={saasIdea} onChange={(event) => setSaasIdea(event.target.value)} rows={2} />
                  <button type="submit" disabled={saasBusy || !saasName.trim()}>Create project</button>
                </form>

                {saasProjects.length > 0 && (
                  <>
                    <h3>Projects</h3>
                    <select
                      value={saasProjectId}
                      onChange={(event) => {
                        setSaasProjectId(event.target.value)
                        setSaasArtifact(null)
                        loadSaasFeedback(event.target.value)
                      }}
                    >
                      <option value="">Select project…</option>
                      {saasProjects.map((project) => (
                        <option key={project.project_id} value={project.project_id}>{project.name}</option>
                      ))}
                    </select>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleSaasStep('validate')} disabled={saasBusy || !saasProjectId}>Validate</button>
                      <button type="button" onClick={() => handleSaasStep('roadmap')} disabled={saasBusy || !saasProjectId}>Roadmap</button>
                      <button type="button" onClick={() => handleSaasStep('architecture')} disabled={saasBusy || !saasProjectId}>Architecture</button>
                      <button type="button" onClick={() => handleSaasStep('launch')} disabled={saasBusy || !saasProjectId}>Launch assets</button>
                    </div>
                  </>
                )}

                {saasArtifact && (
                  <div className="agent-template-card">
                    <strong>{saasArtifact.kind} (draft)</strong>
                    <pre className="muted" style={{ whiteSpace: 'pre-wrap', maxHeight: '160px', overflow: 'auto', margin: 0 }}>
                      {JSON.stringify(saasArtifact.data, null, 2).slice(0, 1200)}
                    </pre>
                  </div>
                )}

                <form className="stacked-form" onSubmit={handleCreateSaasFeedback}>
                  <h3>Feedback / bug</h3>
                  <input type="text" placeholder="Title" value={saasFeedbackTitle} onChange={(event) => setSaasFeedbackTitle(event.target.value)} />
                  <select value={saasFeedbackType} onChange={(event) => setSaasFeedbackType(event.target.value)}>
                    <option value="feature">feature</option>
                    <option value="bug">bug</option>
                    <option value="improvement">improvement</option>
                    <option value="question">question</option>
                  </select>
                  <button type="submit" disabled={saasBusy || !saasProjectId || !saasFeedbackTitle.trim()}>Log feedback</button>
                </form>

                {saasFeedback.length > 0 && (
                  <>
                    <h3>Feedback</h3>
                    {saasFeedback.slice(0, 6).map((item) => (
                      <p className="muted" key={item.feedback_id}>• [{item.type}] {item.title} ({item.status})</p>
                    ))}
                  </>
                )}

                <p className="muted">Plans and drafts only — no deploy, no payments, no account creation; nothing is built without the existing approval flow.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowBizOpsPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Business Operator Advanced
              </span>
              <ChevronDown size={15} />
            </button>
            {showBizOpsPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Business Operator Advanced · v33.0</strong>
                  <span>Operations workflows, reporting, KPI snapshots, approvals, and audit. Draft-only — no real send, payment, or CRM sync.</span>
                </div>
                {bizOpsDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Workflows</span><strong>{bizOpsDashboard.total_workflows}</strong></div>
                    <div><span>Approvals</span><strong>{bizOpsDashboard.pending_approvals}</strong></div>
                    <div><span>Reports</span><strong>{bizOpsDashboard.total_reports}</strong></div>
                    <div><span>KPI snaps</span><strong>{bizOpsDashboard.total_kpi_snapshots}</strong></div>
                    <div><span>Leads</span><strong>{bizOpsDashboard.kpis?.total_leads}</strong></div>
                    <div><span>Conv %</span><strong>{bizOpsDashboard.kpis?.conversion_rate}</strong></div>
                  </div>
                )}
                {bizOpsError && <p className="error-text">{bizOpsError}</p>}
                <div className="inline-actions">
                  <select value={bizOpsWorkflowType} onChange={(event) => setBizOpsWorkflowType(event.target.value)}>
                    <option value="lead_pipeline">lead_pipeline</option>
                    <option value="support_triage">support_triage</option>
                    <option value="invoice_processing">invoice_processing</option>
                    <option value="custom">custom</option>
                  </select>
                  <button type="button" onClick={handleCreateBizOpsWorkflow} disabled={bizOpsBusy}>New workflow</button>
                </div>
                <div className="inline-actions">
                  <button type="button" onClick={handleCreateBizOpsReport} disabled={bizOpsBusy}>Generate report</button>
                  <button type="button" onClick={handleCreateBizOpsKpiSnapshot} disabled={bizOpsBusy}>KPI snapshot</button>
                  <button type="button" onClick={() => refreshBizOpsPanel()} disabled={bizOpsBusy}>Refresh</button>
                </div>

                {bizOpsWorkflows.length > 0 && (
                  <>
                    <h3>Workflows</h3>
                    {bizOpsWorkflows.slice(0, 6).map((workflow) => (
                      <div className="agent-template-card" key={workflow.workflow_id}>
                        <strong>{workflow.title}</strong>
                        <p className="muted">{workflow.workflow_type} · {workflow.status}</p>
                        {(workflow.next_steps || []).map((step, index) => (
                          <p className="muted" key={index}>→ {step}</p>
                        ))}
                      </div>
                    ))}
                  </>
                )}

                <form className="stacked-form" onSubmit={handleCreateBizOpsApproval}>
                  <h3>Request approval (risky/external action)</h3>
                  <input type="text" placeholder="Title" value={bizOpsApprovalTitle} onChange={(event) => setBizOpsApprovalTitle(event.target.value)} />
                  <select value={bizOpsApprovalKind} onChange={(event) => setBizOpsApprovalKind(event.target.value)}>
                    <option value="external_send">external_send</option>
                    <option value="payment">payment</option>
                    <option value="high_risk">high_risk</option>
                    <option value="data_share">data_share</option>
                  </select>
                  <button type="submit" disabled={bizOpsBusy || !bizOpsApprovalTitle.trim()}>Request approval</button>
                </form>

                {bizOpsApprovals.length > 0 && (
                  <>
                    <h3>Approvals</h3>
                    {bizOpsApprovals.slice(0, 6).map((approval) => (
                      <div className="agent-template-card" key={approval.approval_id}>
                        <strong>{approval.title}</strong>
                        <p className="muted">{approval.kind} · {approval.status}</p>
                        {approval.status === 'pending' && (
                          <div className="inline-actions">
                            <button type="button" onClick={() => handleDecideBizOpsApproval(approval.approval_id, 'approved')} disabled={bizOpsBusy}>Approve</button>
                            <button type="button" onClick={() => handleDecideBizOpsApproval(approval.approval_id, 'rejected')} disabled={bizOpsBusy}>Reject</button>
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}

                <p className="muted">Draft-only operations — approving records a decision but performs no real email send, payment, or external CRM action.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowComplianceIntelPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Compliance Intelligence
              </span>
              <ChevronDown size={15} />
            </button>
            {showComplianceIntelPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Legal / Compliance Intelligence · v34.0</strong>
                  <span>Policies, sensitive-data scanning (PII/PHI/secrets), contract review, checklists, audit packages. Not legal advice.</span>
                </div>
                {complianceIntelDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Policies</span><strong>{complianceIntelDashboard.policy_count}</strong></div>
                    <div><span>Scans</span><strong>{complianceIntelDashboard.scan_count}</strong></div>
                    <div><span>High risk</span><strong>{complianceIntelDashboard.high_risk_findings}</strong></div>
                    <div><span>PHI</span><strong>{complianceIntelDashboard.phi_findings}</strong></div>
                    <div><span>Contracts</span><strong>{complianceIntelDashboard.contract_review_count}</strong></div>
                    <div><span>Audits</span><strong>{complianceIntelDashboard.audit_package_count}</strong></div>
                  </div>
                )}
                {complianceIntelError && <p className="error-text">{complianceIntelError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleCreateCompliancePolicy} disabled={compIntelBusy}>New policy</button>
                  <button type="button" onClick={handleCreateAuditPackage} disabled={compIntelBusy}>Audit package</button>
                  <button type="button" onClick={() => refreshComplianceIntelPanel()} disabled={compIntelBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleRunComplianceScan}>
                  <h3>Sensitive-data scan</h3>
                  <textarea placeholder="Paste content to scan for PII / PHI / secrets" value={scanContent} onChange={(event) => setScanContent(event.target.value)} rows={2} />
                  <button type="submit" disabled={compIntelBusy || !scanContent.trim()}>Scan</button>
                </form>

                <form className="stacked-form" onSubmit={handleReviewContract}>
                  <h3>Contract review</h3>
                  <textarea placeholder="Paste contract text to flag risky clauses" value={contractContent} onChange={(event) => setContractContent(event.target.value)} rows={2} />
                  <button type="submit" disabled={compIntelBusy || !contractContent.trim()}>Review</button>
                </form>

                <div className="inline-actions">
                  <select value={checklistFramework} onChange={(event) => setChecklistFramework(event.target.value)}>
                    <option value="hipaa">hipaa</option>
                    <option value="gdpr">gdpr</option>
                    <option value="soc2">soc2</option>
                    <option value="general">general</option>
                  </select>
                  <button type="button" onClick={handleCreateComplianceChecklist} disabled={compIntelBusy}>Generate checklist</button>
                </div>

                {complianceArtifact && (
                  <div className="agent-template-card">
                    <strong>{complianceArtifact.kind}</strong>
                    <pre className="muted" style={{ whiteSpace: 'pre-wrap', maxHeight: '160px', overflow: 'auto', margin: 0 }}>
                      {JSON.stringify(complianceArtifact.data, null, 2).slice(0, 1200)}
                    </pre>
                  </div>
                )}

                {complianceScans.length > 0 && (
                  <>
                    <h3>Recent scans</h3>
                    {complianceScans.slice(0, 5).map((scan) => (
                      <p className="muted" key={scan.finding_id}>
                        • {scan.label || 'scan'} · {scan.risk_level}{scan.phi_detected ? ' · PHI' : ''}{scan.secrets_detected ? ' · secrets' : ''}
                      </p>
                    ))}
                  </>
                )}

                <p className="muted">Not legal advice — produces checklists, warnings, and audit material for human review.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowBoardPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Executive Board
              </span>
              <ChevronDown size={15} />
            </button>
            {showBoardPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>AI Executive Board · v35.0</strong>
                  <span>Review a decision from CEO/CTO/CFO/COO/Legal/Product/Marketing/Security perspectives. Advises and summarizes — does not execute.</span>
                </div>
                {boardDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Sessions</span><strong>{boardDashboard.total_sessions}</strong></div>
                    <div><span>Reviewed</span><strong>{boardDashboard.reviewed_sessions}</strong></div>
                    <div><span>Votes</span><strong>{boardDashboard.total_votes}</strong></div>
                    <div><span>Reports</span><strong>{boardDashboard.total_reports}</strong></div>
                  </div>
                )}
                {boardError && <p className="error-text">{boardError}</p>}

                <form className="stacked-form" onSubmit={handleCreateBoardSession}>
                  <h3>New decision review</h3>
                  <textarea placeholder="Describe the decision/question for the board" value={boardDecision} onChange={(event) => setBoardDecision(event.target.value)} rows={2} />
                  <button type="submit" disabled={boardBusy || !boardDecision.trim()}>Create session</button>
                </form>

                {boardSessions.length > 0 && (
                  <>
                    <h3>Sessions</h3>
                    <select value={boardSessionId} onChange={(event) => { setBoardSessionId(event.target.value); setBoardArtifact(null) }}>
                      <option value="">Select session…</option>
                      {boardSessions.map((session) => (
                        <option key={session.session_id} value={session.session_id}>{session.title}</option>
                      ))}
                    </select>
                    <div className="inline-actions">
                      <button type="button" onClick={handleBoardReview} disabled={boardBusy || !boardSessionId}>Review</button>
                      <button type="button" onClick={handleBoardReport} disabled={boardBusy || !boardSessionId}>Report</button>
                    </div>
                    <div className="inline-actions">
                      <select value={boardVoteRole} onChange={(event) => setBoardVoteRole(event.target.value)}>
                        {['CEO', 'CTO', 'CFO', 'COO', 'Legal/Compliance', 'Product', 'Marketing', 'Security'].map((role) => (
                          <option key={role} value={role}>{role}</option>
                        ))}
                      </select>
                      <select value={boardVoteValue} onChange={(event) => setBoardVoteValue(event.target.value)}>
                        <option value="approve">approve</option>
                        <option value="reject">reject</option>
                        <option value="abstain">abstain</option>
                      </select>
                      <button type="button" onClick={handleBoardVote} disabled={boardBusy || !boardSessionId}>Cast vote</button>
                    </div>
                  </>
                )}

                {boardArtifact && (
                  <div className="agent-template-card">
                    <strong>{boardArtifact.kind}</strong>
                    <pre className="muted" style={{ whiteSpace: 'pre-wrap', maxHeight: '180px', overflow: 'auto', margin: 0 }}>
                      {JSON.stringify(boardArtifact.data, null, 2).slice(0, 1400)}
                    </pre>
                  </div>
                )}

                <p className="muted">Advisory only — the board reviews and recommends from multiple perspectives; it does not execute any action.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowInnovationPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Innovation Lab
              </span>
              <ChevronDown size={15} />
            </button>
            {showInnovationPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Autonomous Research + Innovation Lab · v36.0</strong>
                  <span>Track research, competitors, trends, scored ideas, experiments, and prototype plans. Local/manual research only.</span>
                </div>
                {innovationDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Research</span><strong>{innovationDashboard.research_count}</strong></div>
                    <div><span>Competitors</span><strong>{innovationDashboard.competitor_count}</strong></div>
                    <div><span>Trends</span><strong>{innovationDashboard.trend_count}</strong></div>
                    <div><span>Ideas</span><strong>{innovationDashboard.idea_count}</strong></div>
                    <div><span>Experiments</span><strong>{innovationDashboard.experiment_count}</strong></div>
                    <div><span>Prototypes</span><strong>{innovationDashboard.prototype_count}</strong></div>
                  </div>
                )}
                {innovationError && <p className="error-text">{innovationError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleCreateInnovationReport} disabled={innovationBusy}>Generate report</button>
                  <button type="button" onClick={() => refreshInnovationPanel()} disabled={innovationBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateResearch}>
                  <h3>Add research item</h3>
                  <input type="text" placeholder="Research title" value={researchTitle} onChange={(event) => setResearchTitle(event.target.value)} />
                  <button type="submit" disabled={innovationBusy || !researchTitle.trim()}>Add research</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateIdea}>
                  <h3>Score an idea</h3>
                  <input type="text" placeholder="Idea title" value={ideaTitle} onChange={(event) => setIdeaTitle(event.target.value)} />
                  <select value={ideaImpact} onChange={(event) => setIdeaImpact(event.target.value)}>
                    {[1, 2, 3, 4, 5].map((n) => (<option key={n} value={n}>impact {n}</option>))}
                  </select>
                  <button type="submit" disabled={innovationBusy || !ideaTitle.trim()}>Add idea</button>
                </form>

                {innovationIdeas.length > 0 && (
                  <>
                    <h3>Top ideas</h3>
                    {innovationIdeas.slice(0, 6).map((idea) => (
                      <div className="agent-template-card" key={idea.idea_id}>
                        <strong>{idea.title}</strong>
                        <p className="muted">score {idea.composite_score} · impact {idea.impact} · risk {idea.risk}</p>
                      </div>
                    ))}
                  </>
                )}

                {innovationResearch.length > 0 && (
                  <>
                    <h3>Research</h3>
                    {innovationResearch.slice(0, 5).map((item) => (
                      <p className="muted" key={item.research_id}>• {item.title} ({item.credibility})</p>
                    ))}
                  </>
                )}

                <p className="muted">Local/manual research only — no web browsing or external scraping.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowSimWorldPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Simulation World
              </span>
              <ChevronDown size={15} />
            </button>
            {showSimWorldPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>AI Simulation World · v37.0</strong>
                  <span>Model decisions, personas, and scenarios safely. Deterministic mock simulation — no real-world actions.</span>
                </div>
                {simWorldDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Worlds</span><strong>{simWorldDashboard.world_count}</strong></div>
                    <div><span>Personas</span><strong>{simWorldDashboard.persona_count}</strong></div>
                    <div><span>Scenarios</span><strong>{simWorldDashboard.scenario_count}</strong></div>
                    <div><span>Outcomes</span><strong>{simWorldDashboard.outcome_count}</strong></div>
                    <div><span>Avg score</span><strong>{simWorldDashboard.average_score}</strong></div>
                  </div>
                )}
                {simWorldError && <p className="error-text">{simWorldError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleSimWorldReport} disabled={simWorldBusy}>Generate report</button>
                  <button type="button" onClick={() => refreshSimWorldPanel()} disabled={simWorldBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateSimWorld}>
                  <h3>New world</h3>
                  <input type="text" placeholder="World name" value={simWorldName} onChange={(event) => setSimWorldName(event.target.value)} />
                  <button type="submit" disabled={simWorldBusy || !simWorldName.trim()}>Create world</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateSimScenario}>
                  <h3>New scenario</h3>
                  <input type="text" placeholder="Scenario title" value={simScenarioTitle} onChange={(event) => setSimScenarioTitle(event.target.value)} />
                  <select value={simScenarioType} onChange={(event) => setSimScenarioType(event.target.value)}>
                    {['business', 'product', 'project', 'bug', 'risk', 'launch'].map((t) => (<option key={t} value={t}>{t}</option>))}
                  </select>
                  <button type="submit" disabled={simWorldBusy || !simScenarioTitle.trim()}>Create scenario</button>
                </form>

                {simWorldScenarios.length > 0 && (
                  <>
                    <h3>Scenarios</h3>
                    {simWorldScenarios.slice(0, 6).map((scenario) => (
                      <div className="agent-template-card" key={scenario.scenario_id}>
                        <strong>{scenario.title}</strong>
                        <p className="muted">{scenario.scenario_type} · {scenario.status}{scenario.last_score != null ? ` · score ${scenario.last_score}` : ''}</p>
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleRunSimScenario(scenario.scenario_id)} disabled={simWorldBusy}>Run</button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {simWorldOutcome && (
                  <div className="agent-template-card">
                    <strong>Outcome · {simWorldOutcome.likely_result} ({simWorldOutcome.success_score})</strong>
                    <p className="muted">Risks: {(simWorldOutcome.risks || []).join(', ')}</p>
                    <p className="muted">{simWorldOutcome.note}</p>
                  </div>
                )}

                <p className="muted">Safe local sandbox — deterministic mock simulation; no real-world actions are taken.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowOrgOsPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Organization OS
              </span>
              <ChevronDown size={15} />
            </button>
            {showOrgOsPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Multi-User Organization OS · v38.0</strong>
                  <span>Local organizations, member profiles, roles, permissions, workspace links, and activity. No production auth.</span>
                </div>
                {orgOsDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Orgs</span><strong>{orgOsDashboard.organization_count}</strong></div>
                    <div><span>Members</span><strong>{orgOsDashboard.member_count}</strong></div>
                    <div><span>Active</span><strong>{orgOsDashboard.active_member_count}</strong></div>
                    <div><span>Links</span><strong>{orgOsDashboard.workspace_link_count}</strong></div>
                  </div>
                )}
                {orgOsError && <p className="error-text">{orgOsError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshOrgOsPanel()} disabled={orgOsBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateOrg}>
                  <h3>New organization</h3>
                  <input type="text" placeholder="Organization name" value={orgName} onChange={(event) => setOrgName(event.target.value)} />
                  <button type="submit" disabled={orgOsBusy || !orgName.trim()}>Create org</button>
                </form>

                <form className="stacked-form" onSubmit={handleCreateOrgMember}>
                  <h3>Add member (local profile)</h3>
                  <input type="text" placeholder="Display name" value={orgMemberName} onChange={(event) => setOrgMemberName(event.target.value)} />
                  <select value={orgMemberRole} onChange={(event) => setOrgMemberRole(event.target.value)}>
                    {['owner', 'admin', 'manager', 'contributor', 'viewer'].map((r) => (<option key={r} value={r}>{r}</option>))}
                  </select>
                  <button type="submit" disabled={orgOsBusy || !orgMemberName.trim()}>Add member</button>
                </form>

                {orgOsOrganizations.length > 0 && (
                  <>
                    <h3>Organizations</h3>
                    {orgOsOrganizations.slice(0, 5).map((org) => (
                      <p className="muted" key={org.organization_id}>• {org.name}</p>
                    ))}
                  </>
                )}

                {orgOsMembers.length > 0 && (
                  <>
                    <h3>Members</h3>
                    {orgOsMembers.slice(0, 6).map((member) => (
                      <div className="agent-template-card" key={member.member_id}>
                        <strong>{member.display_name}</strong>
                        <p className="muted">{member.role} · {(member.permissions || []).join(', ')}</p>
                        <select value={member.role} onChange={(event) => handleSetMemberRole(member.member_id, event.target.value)} disabled={orgOsBusy}>
                          {['owner', 'admin', 'manager', 'contributor', 'viewer'].map((r) => (<option key={r} value={r}>{r}</option>))}
                        </select>
                      </div>
                    ))}
                  </>
                )}

                <p className="muted">Local organization records only — no production authentication or real user login.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowCompanionPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                Hardware Companion
              </span>
              <ChevronDown size={15} />
            </button>
            {showCompanionPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>AI Hardware / Always-On Companion · v39.0</strong>
                  <span>Device readiness, companion-mode settings, and session planning. No mic recording, no wake-word, no hardware access.</span>
                </div>
                {companionDashboard && (
                  <div className="analytics-mini-grid">
                    <div><span>Devices</span><strong>{companionDashboard.device_count}</strong></div>
                    <div><span>Sessions</span><strong>{companionDashboard.session_count}</strong></div>
                    <div><span>Mode</span><strong>{companionDashboard.companion_mode}</strong></div>
                    <div><span>Listening</span><strong>{String(companionDashboard.background_listening)}</strong></div>
                  </div>
                )}
                {companionError && <p className="error-text">{companionError}</p>}

                <h3>Companion mode</h3>
                <div className="inline-actions">
                  {['disabled', 'push_to_talk_ready', 'local_only_ready'].map((mode) => (
                    <button key={mode} type="button" onClick={() => handleSetCompanionMode(mode)} disabled={companionBusy} className={companionMode === mode ? 'active' : ''}>
                      {mode}
                    </button>
                  ))}
                </div>
                <div className="inline-actions">
                  <button type="button" onClick={handleCreateCompanionSession} disabled={companionBusy}>New session</button>
                  <button type="button" onClick={() => refreshCompanionPanel()} disabled={companionBusy}>Refresh</button>
                </div>

                <form className="stacked-form" onSubmit={handleCreateCompanionDevice}>
                  <h3>Register device profile</h3>
                  <input type="text" placeholder="Device name" value={companionDeviceName} onChange={(event) => setCompanionDeviceName(event.target.value)} />
                  <button type="submit" disabled={companionBusy || !companionDeviceName.trim()}>Register device</button>
                </form>

                {companionDevices.length > 0 && (
                  <>
                    <h3>Devices</h3>
                    {companionDevices.slice(0, 6).map((device) => (
                      <div className="agent-template-card" key={device.device_id}>
                        <strong>{device.name}</strong>
                        <p className="muted">{device.device_type} · mic {String(device.has_mic)} · local {String(device.local_processing)}</p>
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleCompanionReadiness(device.device_id)} disabled={companionBusy}>Readiness check</button>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {companionReadiness && (
                  <div className="agent-template-card">
                    <strong>Readiness · {companionReadiness.readiness} ({companionReadiness.ready_count}/{companionReadiness.total})</strong>
                    {(companionReadiness.checklist || []).map((c, index) => (
                      <p className="muted" key={index}>{c.ready ? '✓' : '○'} {c.item}</p>
                    ))}
                  </div>
                )}

                {companionDashboard?.safety_rules && (
                  <>
                    <h3>Safety</h3>
                    {companionDashboard.safety_rules.map((rule, index) => (
                      <p className="muted" key={index}>• {rule}</p>
                    ))}
                  </>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowOperatingLayerPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                EvolveAgent Operating Layer
              </span>
              <ChevronDown size={15} />
            </button>
            {showOperatingLayerPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>EvolveAgent Operating Layer · v40.0</strong>
                  <span>A governed orchestration dashboard across personal, project, business, agent, simulation, organization, and companion systems.</span>
                </div>
                {operatingLayerDashboard && (
                  <>
                    <div className="analytics-mini-grid">
                      <div><span>Capabilities</span><strong>{operatingLayerDashboard.active_capability_groups}/{operatingLayerDashboard.total_capability_groups}</strong></div>
                      <div><span>Snapshots</span><strong>{operatingLayerDashboard.snapshot_count}</strong></div>
                      <div><span>Recs</span><strong>{operatingLayerDashboard.recommendation_count}</strong></div>
                    </div>
                    <h3>Capability map</h3>
                    {(operatingLayerDashboard.capability_groups || []).map((group) => (
                      <p className="muted" key={group.group}>{group.active ? '✓' : '○'} {group.group} — {group.label}</p>
                    ))}
                  </>
                )}
                {operatingLayerError && <p className="error-text">{operatingLayerError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={handleOperatingLayerSnapshot} disabled={operatingLayerBusy}>Readiness snapshot</button>
                  <button type="button" onClick={handleOperatingLayerRecommendations} disabled={operatingLayerBusy}>Recommendations</button>
                  <button type="button" onClick={handleOperatingLayerReport} disabled={operatingLayerBusy}>Final report</button>
                </div>

                {operatingLayerArtifact && (
                  <div className="agent-template-card">
                    <strong>{operatingLayerArtifact.kind}</strong>
                    <pre className="muted" style={{ whiteSpace: 'pre-wrap', maxHeight: '180px', overflow: 'auto', margin: 0 }}>
                      {JSON.stringify(operatingLayerArtifact.data, null, 2).slice(0, 1400)}
                    </pre>
                  </div>
                )}

                {operatingLayerDashboard?.safety_boundaries && (
                  <>
                    <h3>Safety boundaries</h3>
                    {operatingLayerDashboard.safety_boundaries.map((rule, index) => (
                      <p className="muted" key={index}>• {rule}</p>
                    ))}
                  </>
                )}

                {operatingLayerDashboard?.disclaimer && (
                  <p className="muted"><strong>Disclaimer:</strong> {operatingLayerDashboard.disclaimer}</p>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowDataExport((current) => !current)}>
              <span>
                <Cpu size={15} />
                Data Export & Backup
              </span>
              <ChevronDown size={15} />
            </button>
            {showDataExport && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Data Export & Backup · v59.0</strong>
                  <span>Download a local JSON bundle of your content collections, or import one. Local only — no external upload. Import is non-destructive (merge).</span>
                </div>
                {dataExportSummary && (
                  <p className="muted">collections: {dataExportSummary.exportable_collections} · items: {dataExportSummary.total_current_items} · exports: {dataExportSummary.export_events} · imports: {dataExportSummary.import_events}</p>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleExportDownload} disabled={dataExportBusy}>Download backup (.json)</button>
                  <button type="button" onClick={() => refreshDataExport()} disabled={dataExportBusy}>Refresh</button>
                </div>
                <form className="stacked-form" onSubmit={handleImportBundle}>
                  <h3>Import a bundle</h3>
                  <textarea placeholder="Paste a backup bundle JSON to merge (non-destructive)" value={importText} onChange={(event) => setImportText(event.target.value)} rows={2} />
                  <button type="submit" disabled={dataExportBusy || !importText.trim()}>Import (merge)</button>
                </form>
                {importResult && (
                  <div className="agent-template-card">
                    <strong>{importResult.error ? 'Import failed' : `Imported ${importResult.total_imported} new item(s)`}</strong>
                    <p className="muted">{importResult.error || importResult.note}</p>
                  </div>
                )}
                <p className="muted">Local export/import only — no external upload; import merges (never overwrites or deletes).</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowCodeIntel((current) => !current)}>
              <span>
                <GitBranch size={15} />
                Code Intelligence
              </span>
              <ChevronDown size={15} />
            </button>
            {showCodeIntel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Code Intelligence · v76.0</strong>
                  <span>Static, read-only analysis of pasted code — bug-risk scan, refactor plan, metrics, route map, dependencies. Never reads the filesystem or edits code.</span>
                </div>
                <form className="stacked-form" onSubmit={(event) => { event.preventDefault(); runCodeAnalyze() }}>
                  <textarea placeholder="Paste code to analyze…" value={codeIntelText} onChange={(event) => setCodeIntelText(event.target.value)} rows={4} />
                  <button type="submit" disabled={codeIntelBusy || !codeIntelText.trim()}>{codeIntelBusy ? 'Analyzing…' : 'Analyze code'}</button>
                </form>
                {codeIntelResult?.error ? (
                  <p className="error">{codeIntelResult.error}</p>
                ) : codeIntelResult && (
                  <>
                    <p className="muted">
                      risk <span className={`feature-badge ${codeIntelResult.risk_level === 'low' ? 'active' : 'needs_config'}`}>{codeIntelResult.risk_level}</span> · {codeIntelResult.risk_count} findings · {codeIntelResult.metrics?.lines} lines · {codeIntelResult.metrics?.functions} fns
                    </p>
                    <div className="agent-template-list">
                      {codeIntelResult.bug_risks?.slice(0, 8).map((f, i) => (
                        <div key={i} className="agent-template-card">
                          <strong><span className={`feature-badge ${f.severity === 'high' ? 'needs_config' : f.severity === 'medium' ? 'demo_safe' : 'active'}`}>{f.severity}</span> line {f.line}</strong>
                          <span className="gs-trace">{f.message}</span>
                        </div>
                      ))}
                    </div>
                    <div className="agent-template-card">
                      <strong>Refactor plan</strong>
                      {codeIntelResult.suggested_refactors?.map((s, i) => (<span key={i} className="home-action">• {s}</span>))}
                    </div>
                  </>
                )}
                <p className="muted">Static analysis of submitted text only — read-only, no edits, no filesystem access.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowResearchAgent2((current) => !current)}>
              <span><Library size={15} /> Research Agent</span>
              <ChevronDown size={15} />
            </button>
            {showResearchAgent2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Research Agent · v77.0</strong>
                  <span>Claim extraction, citation-quality brief, and bias flagging for research text.</span>
                </div>
                <textarea value={researchAgentText} onChange={(event) => setResearchAgentText(event.target.value)} rows={3} />
                <div className="inline-actions">
                  <button type="button" onClick={() => runResearchAgent2('claims')} disabled={researchAgentBusy}>Claims</button>
                  <button type="button" onClick={() => runResearchAgent2('bias')} disabled={researchAgentBusy}>Bias flags</button>
                  <button type="button" onClick={() => runResearchAgent2('brief')} disabled={researchAgentBusy}>Brief</button>
                </div>
                {researchAgentResult?.error ? <p className="error">{researchAgentResult.error}</p> : researchAgentResult && (
                  <div className="agent-template-card dev-result">
                    {researchAgentResult.mode === 'bias' && (
                      <>
                        <strong>Bias check <span className={`feature-badge ${researchAgentResult.data.risk === 'low' ? 'active' : 'needs_config'}`}>{researchAgentResult.data.risk}</span> · {researchAgentResult.data.count} flag(s)</strong>
                        <div className="dev-tags">{(researchAgentResult.data.flags || []).map((f) => <span className="dev-tag" key={f}>{f}</span>)}</div>
                      </>
                    )}
                    {researchAgentResult.mode === 'claims' && (
                      <>
                        <strong>{researchAgentResult.data.claim_count} claims · {researchAgentResult.data.evidence_count} evidence</strong>
                        {(researchAgentResult.data.rows || []).slice(0, 6).map((r, i) => (
                          <p className="dev-line" key={i}><span className={`feature-badge ${r.type === 'evidence' ? 'active' : 'demo_safe'}`}>{r.type}</span> {r.statement}</p>
                        ))}
                      </>
                    )}
                    {researchAgentResult.mode === 'brief' && (
                      <>
                        <strong>Research brief</strong>
                        <p className="dev-line">Avg citation quality <strong>{researchAgentResult.data.average_citation_quality}/100</strong> · {researchAgentResult.data.contradiction_count} contradiction(s)</p>
                        <button type="button" className="master-fb" onClick={() => downloadFile('research-brief.md', researchAgentResult.data.content, 'text/markdown')}>Download brief</button>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowBizIntel2((current) => !current); if (!bizIntel2) refreshBizIntel2() }}>
              <span><BarChart3 size={15} /> Business Intelligence</span>
              <ChevronDown size={15} />
            </button>
            {showBizIntel2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Business Intelligence · v78.0</strong>
                  <span>KPIs, pipeline, proposal tracking, mock forecast, and business risk register.</span>
                </div>
                <div className="inline-actions">
                  <button type="button" onClick={refreshBizIntel2} disabled={bizIntelBusy}>Refresh</button>
                  <button type="button" onClick={downloadBizIntelReport}>Download report</button>
                </div>
                {bizIntel2?.error ? <p className="error">{bizIntel2.error}</p> : bizIntel2 && (
                  <>
                    <div className="analytics-mini-grid">
                      {Object.entries(bizIntel2.kpis || {}).slice(0, 6).map(([key, value]) => (
                        <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{String(value)}</strong></div>
                      ))}
                    </div>
                    {(bizIntel2.risk_register?.risks || []).slice(0, 4).map((risk, index) => (
                      <p className="muted" key={index}>• {typeof risk === 'string' ? risk : JSON.stringify(risk)}</p>
                    ))}
                  </>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowMeetingIntel2((current) => !current)}>
              <span><MessageSquarePlus size={15} /> Meeting Intelligence</span>
              <ChevronDown size={15} />
            </button>
            {showMeetingIntel2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Meeting Intelligence · v79.0</strong>
                  <span>Transcript summary, decisions, action items, follow-up drafts, and goal conversion.</span>
                </div>
                <textarea value={meetingIntelText} onChange={(event) => setMeetingIntelText(event.target.value)} rows={3} />
                <div className="inline-actions">
                  <button type="button" onClick={() => runMeetingIntel2('analyze')} disabled={meetingIntelBusy}>Analyze</button>
                  <button type="button" onClick={() => runMeetingIntel2('goal')} disabled={meetingIntelBusy}>To goal</button>
                </div>
                {meetingIntelResult?.error ? <p className="error">{meetingIntelResult.error}</p> : meetingIntelResult && (
                  <div className="agent-template-card dev-result">
                    {meetingIntelResult.mode === 'goal' ? (
                      <>
                        <strong>Proposed goal: {meetingIntelResult.data.proposed_goal?.title}</strong>
                        <p className="dev-line">{meetingIntelResult.data.task_count} task(s) proposed (planning-only)</p>
                        {(meetingIntelResult.data.proposed_tasks || []).slice(0, 6).map((t, i) => (
                          <p className="dev-line" key={i}>• {t.title}{t.owner ? ` — ${t.owner}` : ''}</p>
                        ))}
                      </>
                    ) : (
                      <>
                        <p className="dev-line"><strong>Summary:</strong> {meetingIntelResult.data.summary}</p>
                        {meetingIntelResult.data.decisions?.length > 0 && <div className="dev-section-title">Decisions</div>}
                        {(meetingIntelResult.data.decisions || []).slice(0, 4).map((d, i) => <p className="dev-line" key={i}>• {d}</p>)}
                        {meetingIntelResult.data.action_items?.length > 0 && <div className="dev-section-title">Action items</div>}
                        {(meetingIntelResult.data.action_items || []).slice(0, 6).map((a, i) => (
                          <p className="dev-line" key={i}>• {a.item}{a.owner ? <span className="dev-tag" style={{ marginLeft: 6 }}>{a.owner}</span> : ''}</p>
                        ))}
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowCollab2((current) => !current)}>
              <span><Bot size={15} /> Multi-Agent Collaboration</span>
              <ChevronDown size={15} />
            </button>
            {showCollab2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Multi-Agent Collaboration · v80.0</strong>
                  <span>Compare agent positions, disagreements, reviewer pass, consensus, and final decision.</span>
                </div>
                <form className="stacked-form" onSubmit={runCollab2}>
                  <input value={collabTopic} onChange={(event) => setCollabTopic(event.target.value)} placeholder="Topic" />
                  <input value={collabRoleA} onChange={(event) => setCollabRoleA(event.target.value)} placeholder="Role A" />
                  <textarea value={collabPositionA} onChange={(event) => setCollabPositionA(event.target.value)} rows={2} />
                  <input value={collabRoleB} onChange={(event) => setCollabRoleB(event.target.value)} placeholder="Role B" />
                  <textarea value={collabPositionB} onChange={(event) => setCollabPositionB(event.target.value)} rows={2} />
                  <button type="submit" disabled={collabBusy}>Analyze collaboration</button>
                </form>
                {collabResult?.error ? <p className="error">{collabResult.error}</p> : collabResult && (
                  <div className="agent-template-card">
                    <strong>{collabResult.final_decision?.recommended_by ? `Recommended by ${collabResult.final_decision.recommended_by}` : 'Collaboration result'}</strong>
                    <span className="gs-trace">{Array.isArray(collabResult.consensus_summary) ? collabResult.consensus_summary.join(', ') : collabResult.consensus_summary}</span>
                    {collabResult.final_decision?.position && <span className="home-action">{collabResult.final_decision.position}</span>}
                    {(collabResult.disagreement_notes || []).slice(0, 4).map((note, index) => (
                      <span className="home-action" key={index}>• {typeof note === 'string' ? note : `${(note.between || []).join(' vs ') || 'agents'}: ${note.reason || JSON.stringify(note)}`}</span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowPerm3((current) => !current); if (!permProfiles) refreshPerm3() }}>
              <span><Shield size={15} /> Permission System</span>
              <ChevronDown size={15} />
            </button>
            {showPerm3 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Permission System · v81.0</strong>
                  <span>Permission profiles, action evaluation, and approval decisions before risky work.</span>
                </div>
                <input value={permAction} onChange={(event) => setPermAction(event.target.value)} placeholder="Action to evaluate" />
                <div className="inline-actions">
                  <button type="button" onClick={runPermEval} disabled={permBusy}>Evaluate</button>
                  <button type="button" onClick={createPermProfile} disabled={permBusy}>Create profile</button>
                  <button type="button" onClick={refreshPerm3} disabled={permBusy}>Refresh</button>
                </div>
                {permEval && <p className="muted">decision: <strong>{permEval.decision || permEval.effect}</strong> · {permEval.explanation || permEval.reason}</p>}
                {(permProfiles?.profiles || []).slice(0, 5).map((profile) => (
                  <div className="agent-template-card" key={profile.profile_id}>
                    <strong>{profile.name}</strong>
                    <span className="gs-trace">{profile.action_pattern} · {profile.effect} · {profile.risk_level}</span>
                    <button type="button" onClick={() => deletePermProfile(profile.profile_id)} disabled={permBusy}>Delete</button>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowGovConsole((current) => !current); if (!govConsole) refreshGovConsole() }}>
              <span><ShieldAlert size={15} /> Governance Console</span>
              <ChevronDown size={15} />
            </button>
            {showGovConsole && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Governance Console · v82.0</strong>
                  <span>Blocked ratio, risk summaries, policy violations, injection warnings, approval and external audit.</span>
                </div>
                <div className="inline-actions">
                  <button type="button" onClick={refreshGovConsole} disabled={govBusy}>Refresh</button>
                  <button type="button" onClick={() => downloadGovConsole('markdown')}>Markdown</button>
                  <button type="button" onClick={() => downloadGovConsole('json')}>JSON</button>
                </div>
                {govConsole?.error ? <p className="error">{govConsole.error}</p> : govConsole && (
                  <div className="dev-result">
                    <div className="dev-stats">
                      <div className="dev-stat"><strong>{govConsole.total_events}</strong><span>events</span></div>
                      <div className="dev-stat"><strong>{govConsole.blocked_events}</strong><span>blocked</span></div>
                      <div className="dev-stat"><strong>{govConsole.blocked_ratio_pct}%</strong><span>blocked ratio</span></div>
                    </div>
                    <div className="dev-row"><span>Risk (high / med / low)</span><span>{govConsole.by_risk?.high} / {govConsole.by_risk?.medium} / {govConsole.by_risk?.low}</span></div>
                    <div className="dev-row"><span>Policy violations</span><span>{govConsole.policy_violations?.count ?? 0}</span></div>
                    <div className="dev-row"><span>Prompt-injection warnings</span><span>{govConsole.prompt_injection_warnings?.count ?? 0}</span></div>
                    <div className="dev-row"><span>Secret/PII events</span><span>{govConsole.secret_redactions?.count ?? 0}</span></div>
                    <div className="dev-row"><span>Approval audit</span><span>{govConsole.approval_audit?.count ?? 0}</span></div>
                    <div className="dev-row"><span>External-action audit</span><span>{govConsole.external_action_audit?.count ?? 0}</span></div>
                    {govConsole.top_actions?.length > 0 && <div className="dev-section-title">Top actions</div>}
                    {(govConsole.top_actions || []).slice(0, 5).map((a) => (
                      <div className="dev-row" key={a.action}><span>{a.action}</span><span>{a.count}</span></div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowDataManager((current) => !current); if (!dataManager) refreshDataManager() }}>
              <span><Database size={15} /> Local Data Manager</span>
              <ChevronDown size={15} />
            </button>
            {showDataManager && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Local Data Manager · v83.0</strong>
                  <span>Browse local collections, usage totals, cleanup suggestions, and redaction previews.</span>
                </div>
                <input value={dataManagerCollection} onChange={(event) => setDataManagerCollection(event.target.value)} placeholder="collection name" />
                <div className="inline-actions">
                  <button type="button" onClick={refreshDataManager} disabled={dataManagerBusy}>Refresh</button>
                  <button type="button" onClick={runDataManagerPreview} disabled={dataManagerBusy}>Redaction preview</button>
                </div>
                {dataManager?.error ? <p className="error">{dataManager.error}</p> : dataManager && (
                  <div className="dev-result">
                    <p className="muted">{dataManager.count} collections</p>
                    {(dataManager.collections || []).slice(0, 10).map((c) => (
                      <div className="dev-row" key={c.collection}><span>{c.collection.replace('.json', '')}</span><span>{c.records} · {(c.bytes / 1024).toFixed(1)}KB</span></div>
                    ))}
                  </div>
                )}
                {dataManagerPreview && (
                  <div className="agent-template-card dev-result">
                    <strong>Redaction preview: {dataManagerPreview.total_matches} sensitive match(es)</strong>
                    <div className="dev-tags">{Object.entries(dataManagerPreview.sensitive_matches || {}).map(([k, v]) => <span className="dev-tag" key={k}>{k}: {v}</span>)}</div>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowImportCenter((current) => !current)}>
              <span><Paperclip size={15} /> Import Center</span>
              <ChevronDown size={15} />
            </button>
            {showImportCenter && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Import Center · v84.0</strong>
                  <span>Preview, sanitize, and commit imported document, CSV, markdown, chat, or project notes.</span>
                </div>
                <select value={importCenterKind} onChange={(event) => setImportCenterKind(event.target.value)}>
                  {['document', 'csv', 'markdown', 'chat_history', 'project_notes'].map((kind) => <option key={kind}>{kind}</option>)}
                </select>
                <textarea value={importCenterContent} onChange={(event) => setImportCenterContent(event.target.value)} rows={3} />
                <div className="inline-actions">
                  <button type="button" onClick={() => runImportCenter('preview')} disabled={importCenterBusy}>Preview</button>
                  <button type="button" onClick={() => runImportCenter('commit')} disabled={importCenterBusy}>Commit</button>
                </div>
                {importCenterResult?.error ? <p className="error">{importCenterResult.error}</p> : importCenterResult && (
                  <div className="agent-template-card dev-result">
                    {importCenterResult.imported_count != null ? (
                      <strong>✓ Imported {importCenterResult.imported_count} record(s) · {importCenterResult.redactions} redaction(s)</strong>
                    ) : (
                      <>
                        <strong>Preview: {importCenterResult.record_count} record(s) · {importCenterResult.redactions} redaction(s)</strong>
                        {(importCenterResult.preview || []).slice(0, 4).map((r, i) => <p className="dev-line" key={i}>• {r.content}</p>)}
                      </>
                    )}
                  </div>
                )}
                {importCenterRecords?.records && <p className="muted">records: {importCenterRecords.records.length}</p>}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowExportCenter2((current) => !current)}>
              <span><Download size={15} /> Export Center</span>
              <ChevronDown size={15} />
            </button>
            {showExportCenter2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Export Center · v85.0</strong>
                  <span>Portable markdown/JSON exports, package generation, and project case-study export.</span>
                </div>
                <select value={exportCenterKind} onChange={(event) => setExportCenterKind(event.target.value)}>
                  {['chats', 'reports', 'goals', 'memory', 'imported'].map((kind) => <option key={kind}>{kind}</option>)}
                </select>
                <select value={exportCenterFormat} onChange={(event) => setExportCenterFormat(event.target.value)}>
                  <option>markdown</option>
                  <option>json</option>
                </select>
                <div className="inline-actions">
                  <button type="button" onClick={() => runExportCenter2('export')} disabled={exportCenterBusy}>Export</button>
                  <button type="button" onClick={() => runExportCenter2('package')} disabled={exportCenterBusy}>Package</button>
                  <button type="button" onClick={() => runExportCenter2('case')} disabled={exportCenterBusy}>Case study</button>
                </div>
                {exportCenterResult?.error ? <p className="error">{exportCenterResult.error}</p> : exportCenterResult && (
                  <p className="dev-line">✓ Exported <strong>{exportCenterResult.item_count ?? exportCenterResult.total_items ?? ''}</strong> {exportCenterResult.kind || 'item(s)'} as {exportCenterResult.format} — downloaded.</p>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowPluginMarket((current) => !current); if (!pluginMarket) refreshPluginMarket() }}>
              <span><Cpu size={15} /> Plugin Marketplace</span>
              <ChevronDown size={15} />
            </button>
            {showPluginMarket && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Plugin Marketplace · v86.0</strong>
                  <span>Safe plugin catalog with health badges, registration, enable toggles, and mock tests.</span>
                </div>
                <form className="stacked-form" onSubmit={registerPluginMarket}>
                  <input value={pluginName} onChange={(event) => setPluginName(event.target.value)} placeholder="Plugin name" />
                  <button type="submit" disabled={pluginBusy || !pluginName.trim()}>Register</button>
                </form>
                {(pluginMarket?.plugins || pluginMarket?.catalog || []).slice(0, 6).map((plugin) => (
                  <div className="agent-template-card" key={plugin.plugin_id || plugin.id || plugin.name}>
                    <strong>{plugin.name} <span className={`feature-badge ${plugin.enabled ? 'active' : 'demo_safe'}`}>{plugin.enabled ? 'enabled' : 'disabled'}</span></strong>
                    <span className="gs-trace">{plugin.description || plugin.health?.status || 'safe marketplace plugin'} · health {plugin.health?.score ?? 'n/a'}</span>
                    <div className="inline-actions">
                      <button type="button" onClick={() => runPluginAction(plugin.plugin_id || plugin.id, 'toggle', !plugin.enabled)} disabled={pluginBusy}>Toggle</button>
                      <button type="button" onClick={() => runPluginAction(plugin.plugin_id || plugin.id, 'test')} disabled={pluginBusy}>Test</button>
                    </div>
                  </div>
                ))}
                {pluginActivity?.events && <p className="muted">activity events: {pluginActivity.events.length}</p>}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowIntegrationHub2((current) => !current); if (!integrationHub2) refreshIntegrationHub2() }}>
              <span><Route size={15} /> Integration Hub</span>
              <ChevronDown size={15} />
            </button>
            {showIntegrationHub2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Integration Hub · v87.0</strong>
                  <span>Integration readiness cards, connected scopes, last sync, and dry-run checks.</span>
                </div>
                <div className="inline-actions"><button type="button" onClick={refreshIntegrationHub2} disabled={integrationBusy}>Refresh</button></div>
                {(integrationHub2?.cards || integrationHub2?.integrations || []).map((card) => (
                  <div className="agent-template-card" key={card.integration_id || card.id || card.name}>
                    <strong>{card.name} <span className={`feature-badge ${card.connected ? 'active' : 'needs_config'}`}>{card.connected ? 'connected' : 'not connected'}</span></strong>
                    <span className="gs-trace">scopes: {(card.scopes || []).join(', ') || 'none'} · last sync: {card.last_sync || 'never'}</span>
                    <button type="button" onClick={() => runIntegrationDry(card.integration_id || card.id)} disabled={integrationBusy}>Dry run</button>
                  </div>
                ))}
                {integrationHub2?.dry_run && <p className="muted">dry run: {integrationHub2.dry_run.status || integrationHub2.dry_run.result}</p>}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowQaCenter2((current) => !current); if (!qaCenter) refreshQaCenter2() }}>
              <span><Gauge size={15} /> QA Center</span>
              <ChevronDown size={15} />
            </button>
            {showQaCenter2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>QA Center · v88.0</strong>
                  <span>Release readiness score, verification matrix, failed tracker, and QA record controls.</span>
                </div>
                <div className="inline-actions"><button type="button" onClick={refreshQaCenter2} disabled={qaBusy}>Refresh</button></div>
                {qaCenter && <p className="muted">readiness: <strong>{qaCenter.release_readiness_score ?? qaCenter.readiness_score ?? 'n/a'}</strong></p>}
                {(qaMatrix?.features || qaMatrix?.matrix || []).slice(0, 8).map((item) => (
                  <div className="agent-template-card" key={item.feature_key || item.key || item.name}>
                    <strong>{item.feature_key || item.key || item.name}</strong>
                    <span className="gs-trace">{item.status || item.result || 'unchecked'}</span>
                    <div className="inline-actions">
                      <button type="button" onClick={() => recordQaItem(item.feature_key || item.key || item.name, 'pass')} disabled={qaBusy}>Pass</button>
                      <button type="button" onClick={() => recordQaItem(item.feature_key || item.key || item.name, 'fail')} disabled={qaBusy}>Fail</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowReleaseMgr((current) => !current); if (!releaseMgr) refreshReleaseMgr() }}>
              <span><Flag size={15} /> Release Manager</span>
              <ChevronDown size={15} />
            </button>
            {showReleaseMgr && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Release Manager · v89.0</strong>
                  <span>Release checklist, changelog, tag planning, PR summary, and release notes generators.</span>
                </div>
                <div className="inline-actions">
                  <button type="button" onClick={refreshReleaseMgr} disabled={releaseBusy}>Refresh</button>
                  <button type="button" onClick={() => runReleaseMgr('pr')} disabled={releaseBusy}>PR summary</button>
                  <button type="button" onClick={() => runReleaseMgr('notes')} disabled={releaseBusy}>Release notes</button>
                </div>
                {releaseMgr?.error ? <p className="error">{releaseMgr.error}</p> : releaseMgr && (
                  <div className="dev-result">
                    {releaseMgr.tag_planner && (
                      <div className="dev-tags">
                        <span className="dev-tag">patch {releaseMgr.tag_planner.suggested_patch}</span>
                        <span className="dev-tag">minor {releaseMgr.tag_planner.suggested_minor}</span>
                        <span className="dev-tag">major {releaseMgr.tag_planner.suggested_major}</span>
                      </div>
                    )}
                    <div className="dev-section-title">Version checklist</div>
                    {(releaseMgr.version_checklist || []).slice(0, 6).map((c, i) => <p className="dev-line" key={i}>☐ {c}</p>)}
                    <button type="button" className="master-fb" style={{ marginTop: 6 }} onClick={async () => { const cl = await getReleaseManagerChangelog(); downloadFile('changelog.md', cl.content, 'text/markdown') }}>Download changelog</button>
                  </div>
                )}
                {releaseResult && <p className="muted">generated: {releaseResult.title || releaseResult.version || releaseResult.format || 'artifact'}</p>}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowLaunchConsole((current) => !current); if (!launchConsole) refreshLaunchConsole() }}>
              <span><Sparkles size={15} /> Product Launch Console</span>
              <ChevronDown size={15} />
            </button>
            {showLaunchConsole && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Product Launch Console · v90.0</strong>
                  <span>Capstone readiness dashboard with positioning, feature matrix, demo mode, exports, and launch report.</span>
                </div>
                <div className="inline-actions">
                  <button type="button" onClick={refreshLaunchConsole} disabled={launchBusy}>Refresh</button>
                  <button type="button" onClick={downloadLaunchReport}>Download report</button>
                </div>
                {launchConsole?.error ? <p className="error">{launchConsole.error}</p> : launchConsole && (
                  <div className="dev-result">
                    <div className="dev-stats">
                      <div className="dev-stat"><strong>{launchConsole.final_readiness?.score ?? '—'}</strong><span>readiness</span></div>
                      <div className="dev-stat"><strong>{launchConsole.feature_matrix?.total_features ?? '—'}</strong><span>features</span></div>
                      <div className="dev-stat"><strong>{launchConsole.milestones?.implementation_versions ?? '—'}</strong><span>versions</span></div>
                    </div>
                    <p className="dev-line"><strong>{launchConsole.positioning?.name}</strong> — {launchConsole.positioning?.tagline}</p>
                    <p className="dev-line">Status: <span className={`feature-badge ${launchConsole.final_readiness?.status === 'launch-ready' ? 'active' : 'demo_safe'}`}>{launchConsole.final_readiness?.status}</span></p>
                    {launchConsole.positioning?.pillars?.length > 0 && <div className="dev-section-title">Pillars</div>}
                    {(launchConsole.positioning?.pillars || []).slice(0, 5).map((p, i) => <p className="dev-line" key={i}>• {p}</p>)}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowDocIntel((current) => !current)}>
              <span>
                <FileText size={15} />
                Document Intelligence
              </span>
              <ChevronDown size={15} />
            </button>
            {showDocIntel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Document Intelligence · v75.0</strong>
                  <span>Deterministic, local document tools — contract/risk summary, resume ATS scoring, CSV insight, comparison, Q&A. No external model calls.</span>
                </div>
                <form className="stacked-form" onSubmit={(event) => event.preventDefault()}>
                  <textarea placeholder="Paste text… (for ATS: resume --- keyword1, keyword2)" value={docIntelText} onChange={(event) => setDocIntelText(event.target.value)} rows={3} />
                  <div className="inline-actions">
                    <button type="button" onClick={runDocContractRisk} disabled={docIntelBusy || !docIntelText.trim()}>Contract risk</button>
                    <button type="button" onClick={runDocAts} disabled={docIntelBusy || !docIntelText.trim()}>ATS score</button>
                  </div>
                </form>
                {docIntelResult?.error ? (
                  <p className="error">{docIntelResult.error}</p>
                ) : docIntelResult?.mode === 'contract' ? (
                  <div className="agent-template-card">
                    <strong>Contract risk: <span className={`feature-badge ${docIntelResult.data.risk_level === 'low' ? 'active' : 'needs_config'}`}>{docIntelResult.data.risk_level}</span></strong>
                    {docIntelResult.data.flagged_clauses.map((f, i) => (<span key={i} className="gs-trace">• {f.clause}: {f.matched.join(', ')}</span>))}
                    <span className="gs-trace">{docIntelResult.data.note}</span>
                  </div>
                ) : docIntelResult?.mode === 'ats' ? (
                  <div className="agent-template-card">
                    <strong>ATS score: {docIntelResult.data.ats_score}%</strong>
                    <span className="gs-trace">matched: {docIntelResult.data.matched_keywords.join(', ') || 'none'}</span>
                    <span className="gs-trace">missing: {docIntelResult.data.missing_keywords.join(', ') || 'none'}</span>
                    <span className="home-action">{docIntelResult.data.recommendation}</span>
                  </div>
                ) : null}
                <p className="muted">Deterministic + local — no external model calls; nothing is stored beyond governance logging.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowProductivity((current) => !current); if (!productivityBrain) refreshProductivity() }}>
              <span>
                <Flag size={15} />
                Productivity Brain
              </span>
              <ChevronDown size={15} />
            </button>
            {showProductivity && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Productivity Brain · v74.0</strong>
                  <span>Priority recommendations, daily focus, blockers, overdue review, goal progress, and "what should I work on now?" — read-only.</span>
                </div>
                {productivityBrain && (
                  <>
                    {productivityBrain.what_now?.pick && (
                      <div className="agent-template-card">
                        <strong>▶ What now: {productivityBrain.what_now.pick}</strong>
                        <span className="gs-trace">{productivityBrain.what_now.reason}</span>
                      </div>
                    )}
                    <p className="muted">{productivityBrain.open_task_count} open · {productivityBrain.overdue?.length} overdue · {productivityBrain.blockers?.length} blocked · goals {productivityBrain.goal_progress?.avg_progress_pct}%</p>
                    <div className="agent-template-card">
                      <strong>Daily focus</strong>
                      {(productivityBrain.daily_focus || []).map((t, i) => (<span key={i} className="home-action">• {t.title}{t.due_date ? ` (due ${String(t.due_date).slice(0, 10)})` : ''}</span>))}
                      {(!productivityBrain.daily_focus || productivityBrain.daily_focus.length === 0) && <span className="gs-trace">No open tasks.</span>}
                    </div>
                    {productivityBrain.upcoming_deadlines?.length > 0 && (
                      <div className="agent-template-card">
                        <strong>Upcoming deadlines</strong>
                        {productivityBrain.upcoming_deadlines.map((d, i) => (<span key={i} className="gs-trace">• {d.title} — {String(d.due_date).slice(0, 10)}</span>))}
                      </div>
                    )}
                  </>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshProductivity()}>Refresh</button>
                </div>
                <p className="muted">Read-only — nothing is created or completed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowWorkflowRec((current) => !current)}>
              <span>
                <Route size={15} />
                Workflow Recommender
              </span>
              <ChevronDown size={15} />
            </button>
            {showWorkflowRec && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Workflow Recommender · v73.0</strong>
                  <span>Recommends the best workflow for a goal — expected steps, risk level, approval needs, time/complexity, and similar past runs. Planning-only.</span>
                </div>
                <form className="stacked-form" onSubmit={runWorkflowRec}>
                  <input type="text" placeholder="Describe a goal…" value={workflowGoal} onChange={(event) => setWorkflowGoal(event.target.value)} />
                  <button type="submit" disabled={workflowBusy || !workflowGoal.trim()}>{workflowBusy ? 'Thinking…' : 'Recommend'}</button>
                </form>
                {workflowRec?.error ? (
                  <p className="error">{workflowRec.error}</p>
                ) : workflowRec && (
                  <>
                    <p className="muted">
                      {workflowRec.task_type} · risk {workflowRec.risk_level} · ~{workflowRec.estimated_minutes}min · {workflowRec.complexity}
                      {workflowRec.requires_approval ? ' · needs approval' : ''}
                    </p>
                    <div className="agent-template-card">
                      <strong>Recommended steps</strong>
                      {workflowRec.recommended_workflow?.map((step, i) => (<span key={i} className="home-action">{i + 1}. {step}</span>))}
                    </div>
                    {workflowRec.approval_reason && <p className="gs-trace">🔒 {workflowRec.approval_reason}</p>}
                    {workflowRec.similar_past_runs?.length > 0 && (
                      <div className="agent-template-card">
                        <strong>Similar past runs</strong>
                        {workflowRec.similar_past_runs.map((r, i) => (<span key={i} className="gs-trace">• [{r.domain}] {r.request}</span>))}
                      </div>
                    )}
                  </>
                )}
                <p className="muted">Read-only recommendation — nothing is executed; risky steps require approval.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowAgentQuality((current) => !current); if (!agentQuality) refreshAgentQuality() }}>
              <span>
                <ThumbsUp size={15} />
                Agent Quality
              </span>
              <ChevronDown size={15} />
            </button>
            {showAgentQuality && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Agent Quality Optimizer · v72.0</strong>
                  <span>Score trends, weak-agent detection, regression checks, best-agent-by-task, and human-feedback correlation. Read-only analysis.</span>
                </div>
                {agentQuality && (
                  <>
                    <p className="muted">{agentQuality.agents_tracked} agents · {agentQuality.weak_agents?.length} weak · {agentQuality.regressions?.length} regressed · scale {agentQuality.score_scale}</p>
                    <div className="agent-template-list">
                      {agentQuality.score_trends?.slice(0, 8).map((t) => (
                        <div key={t.agent} className="agent-template-card">
                          <strong>{t.agent} <span className={`feature-badge ${t.avg_score >= 60 ? 'active' : 'needs_config'}`}>{t.avg_score}</span> {t.trend === 'up' ? '↑' : t.trend === 'down' ? '↓' : '→'}</strong>
                          <span className="gs-trace">{t.runs} runs · recent {t.recent_avg}</span>
                        </div>
                      ))}
                    </div>
                    {agentQuality.weak_agents?.length > 0 && (
                      <div className="agent-template-card">
                        <strong>Suggestions</strong>
                        {agentQuality.weak_agents.slice(0, 3).map((w) => (<span key={w.agent} className="home-action">• {w.agent}: {w.suggestion}</span>))}
                      </div>
                    )}
                    {agentQuality.best_by_task?.length > 0 && (
                      <div className="agent-template-card">
                        <strong>Best agent by task</strong>
                        <span className="gs-trace">{agentQuality.best_by_task.slice(0, 6).map((b) => `${b.task_type}:${b.best_agent}(${b.avg_score})`).join(' · ')}</span>
                      </div>
                    )}
                  </>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshAgentQuality()}>Refresh</button>
                </div>
                <p className="muted">Read-only — no prompts are changed and nothing is executed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="agent" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowContext((current) => !current)}>
              <span>
                <Brain size={15} />
                Smart Context
              </span>
              <ChevronDown size={15} />
            </button>
            {showContext && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Smart Context Engine · v71.0</strong>
                  <span>Plan which memory/files/goals feed an answer — with reasons, budget, dedup, and sensitive-content filtering. Read-only preview.</span>
                </div>
                <form className="stacked-form" onSubmit={runContextPlan}>
                  <input type="text" placeholder="Plan context for a query…" value={contextQuery} onChange={(event) => setContextQuery(event.target.value)} />
                  <button type="submit" disabled={contextBusy || !contextQuery.trim()}>{contextBusy ? 'Planning…' : 'Plan context'}</button>
                </form>
                {contextPlan?.error ? (
                  <p className="error">{contextPlan.error}</p>
                ) : contextPlan && (
                  <>
                    <p className="muted">{contextPlan.selected_count} selected · {contextPlan.excluded_count} excluded · {contextPlan.used_chars}/{contextPlan.budget_chars} chars</p>
                    <div className="agent-template-list">
                      {contextPlan.selected?.map((item, i) => (
                        <div key={`s${i}`} className="agent-template-card">
                          <strong>✓ [{item.kind}] <span className="feature-badge active">score {item.score}</span></strong>
                          <span>{item.preview}</span>
                          <span className="gs-trace">{item.reason}</span>
                        </div>
                      ))}
                      {contextPlan.excluded?.slice(0, 6).map((item, i) => (
                        <div key={`e${i}`} className="agent-template-card">
                          <strong>✗ [{item.kind}]</strong>
                          <span className="gs-trace">{item.reason}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
                <p className="muted">Read-only plan — sensitive content is filtered out and never included.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowWsOs((current) => !current); if (!wsOsDashboard) refreshWsOs() }}>
              <span>
                <Layers3 size={15} />
                Workspace OS
              </span>
              <ChevronDown size={15} />
            </button>
            {showWsOs && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Workspace OS · v70.0</strong>
                  <span>Per-workspace overview — dashboard, memory graph, feature usage, agents, reports, timeline, and a health score.</span>
                </div>
                {wsOsDashboard?.error ? (
                  <p className="muted">{wsOsDashboard.error}</p>
                ) : wsOsDashboard && (
                  <>
                    <div className="home-grid">
                      <div className="home-stat"><strong>{wsOsDashboard.health?.score ?? '—'}</strong><span>health {wsOsDashboard.health?.status}</span></div>
                      <div className="home-stat"><strong>{wsOsDashboard.memory_graph?.node_count ?? 0}</strong><span>memory nodes</span></div>
                      <div className="home-stat"><strong>{wsOsDashboard.memory_graph?.edge_count ?? 0}</strong><span>memory edges</span></div>
                      <div className="home-stat"><strong>{wsOsDashboard.agents?.length ?? 0}</strong><span>agents</span></div>
                    </div>
                    <p className="muted">{wsOsDashboard.workspace_name}</p>
                    <div className="agent-template-card">
                      <strong>Feature usage</strong>
                      <span className="gs-trace">{Object.entries(wsOsDashboard.feature_usage || {}).map(([k, v]) => `${k}:${v}`).join(' · ')}</span>
                    </div>
                    {wsOsDashboard.timeline?.length > 0 && (
                      <div className="agent-template-list">
                        {wsOsDashboard.timeline.slice(0, 6).map((event, i) => (
                          <div key={i} className="agent-template-card">
                            <strong>[{event.type}] {event.title}</strong>
                            <span className="gs-trace">{event.timestamp}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshWsOs()}>Refresh</button>
                </div>
                <p className="muted">Read-only, workspace-scoped — nothing is created or executed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowInbox((current) => !current); if (!inboxData) refreshInbox() }}>
              <span>
                <Flag size={15} />
                Notifications Inbox
              </span>
              <ChevronDown size={15} />
            </button>
            {showInbox && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Notifications Inbox · v69.0</strong>
                  <span>Actionable alerts — approvals, failed runs, provider fallback, reminders, health — grouped by severity with mark-resolved and source links.</span>
                </div>
                {inboxData && (
                  <p className="muted">{inboxData.count} open{inboxData.by_severity ? ` · ${Object.entries(inboxData.by_severity).map(([s, n]) => `${s}:${n}`).join(' ')}` : ''}</p>
                )}
                <div className="agent-template-list">
                  {(inboxData?.items || []).map((item) => (
                    <div key={item.id} className="agent-template-card">
                      <strong><span className={`feature-badge ${item.severity === 'critical' ? 'needs_config' : item.severity === 'warning' ? 'demo_safe' : 'active'}`}>{item.severity}</span> {item.title}</strong>
                      <span className="gs-trace">{item.type} · {item.source_route}</span>
                      <div className="master-fb-row">
                        <button type="button" className="master-fb" onClick={() => handleInboxResolve(item.id)}>Mark resolved</button>
                      </div>
                    </div>
                  ))}
                  {inboxData && inboxData.count === 0 && <p className="muted">All clear — no open alerts.</p>}
                </div>
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshInbox()} disabled={inboxBusy}>Refresh</button>
                </div>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowProviders((current) => !current); if (!providerControl) refreshProviderControl() }}>
              <span>
                <Gauge size={15} />
                Provider Control
              </span>
              <ChevronDown size={15} />
            </button>
            {showProviders && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Provider Control · v68.0</strong>
                  <span>Readiness for OpenAI / Claude / Gemini / Mistral / local, model-per-task + real/mock preferences, cost & latency. Key readiness is boolean-only.</span>
                </div>
                {providerControl && (
                  <>
                    <p className="muted">{providerControl.ready_count}/{providerControl.providers?.length} ready · est cost ${providerControl.cost_estimate_usd}</p>
                    <div className="agent-template-list">
                      {providerControl.providers?.map((p) => (
                        <div key={p.id} className="agent-template-card">
                          <strong>{p.name} <span className={`feature-badge ${p.ready ? 'active' : 'needs_config'}`}>{p.ready ? 'ready' : 'needs key'}</span></strong>
                          <span className="gs-trace">~{p.est_latency_ms}ms · ${p.est_cost_per_1k_usd}/1k · keys: {p.required_keys.join(', ') || 'none'}</span>
                        </div>
                      ))}
                    </div>
                    <div className="agent-template-card">
                      <strong>Capability mode (mock/real)</strong>
                      {Object.entries(providerControl.capability_modes || {}).map(([cap, mode]) => (
                        <label key={cap} className="settings-row">
                          <span>{cap}</span>
                          <select value={mode} disabled={providerBusy} onChange={(event) => handleCapabilityMode(cap, event.target.value)}>
                            <option value="mock">mock</option>
                            <option value="real">real</option>
                          </select>
                        </label>
                      ))}
                    </div>
                  </>
                )}
                <p className="muted">{providerControl?.fallback_policy?.chain || 'Fallback: real when key set + mode real; else mock.'} No secret values are shown.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowSettings((current) => !current); if (!settingsData) refreshSettings() }}>
              <span>
                <Cpu size={15} />
                Settings Center
              </span>
              <ChevronDown size={15} />
            </button>
            {showSettings && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Settings Center · v67.0</strong>
                  <span>Central local configuration — provider, modes, features, safety, voice, theme. No secret values are ever stored here.</span>
                </div>
                {settingsData?.settings && Object.entries(settingsData.settings).map(([category, keys]) => (
                  <div key={category} className="agent-template-card">
                    <strong>{category}</strong>
                    {Object.entries(keys).map(([key, value]) => (
                      <label key={key} className="settings-row">
                        <span>{key}</span>
                        {typeof value === 'boolean' ? (
                          <input type="checkbox" checked={value} disabled={settingsBusy} onChange={(event) => handleSettingToggle(category, key, event.target.checked)} />
                        ) : (
                          <span className="settings-val">{String(value)}</span>
                        )}
                      </label>
                    ))}
                  </div>
                ))}
                {settingsData?.enforced_safety && (
                  <details className="master-panel-caps">
                    <summary>Enforced safety (read-only)</summary>
                    <div className="agent-template-list">
                      {settingsData.enforced_safety.map((s, i) => (<div key={i} className="agent-template-card"><span>🔒 {s}</span></div>))}
                    </div>
                  </details>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleSettingsReset} disabled={settingsBusy}>Reset to defaults</button>
                </div>
                <p className="muted">Preferences only — hard safety boundaries are enforced and cannot be disabled here.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowDemo((current) => !current); if (!demoSummary) refreshDemo() }}>
              <span>
                <Sparkles size={15} />
                Demo / Portfolio Mode
              </span>
              <ChevronDown size={15} />
            </button>
            {showDemo && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Demo / Portfolio Mode · v66.0</strong>
                  <span>One-click demo script, guided walkthrough, demo-safe sample data (scoped + resettable), resume bullets, and case-study export.</span>
                </div>
                {demoScript?.script?.length > 0 && (
                  <div className="agent-template-list">
                    {demoScript.script.map((step) => (
                      <div key={step.step} className="agent-template-card">
                        <strong>{step.step}. {step.title}</strong>
                        <span>{step.action}</span>
                        <span className="gs-trace">{step.route} · {step.why}</span>
                      </div>
                    ))}
                  </div>
                )}
                {demoSummary && (
                  <p className="muted">active demo batches: {demoSummary.active_demo_batches}</p>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleDemoSeed} disabled={demoBusy}>Seed demo data</button>
                  <button type="button" onClick={handleDemoReset} disabled={demoBusy}>Reset demo data</button>
                  <button type="button" onClick={handleDemoCaseStudy}>Export case study</button>
                </div>
                <p className="muted">Demo content is read-only. Seed/reset only touch demo-tagged records — your data is never removed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowFeatures((current) => !current); if (!featuresData) refreshFeatures() }}>
              <span>
                <Library size={15} />
                Feature Registry
              </span>
              <ChevronDown size={15} />
            </button>
            {showFeatures && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Feature Registry · v65.0</strong>
                  <span>Canonical, searchable map of every feature — service, route, category, and status (active / demo-safe / mock / needs-config).</span>
                </div>
                <form className="stacked-form" onSubmit={(event) => { event.preventDefault(); refreshFeatures() }}>
                  <input type="text" placeholder="Search features…" value={featuresQuery} onChange={(event) => setFeaturesQuery(event.target.value)} />
                  <div className="inline-actions">
                    <select value={featuresStatus} onChange={(event) => { setFeaturesStatus(event.target.value); }} aria-label="Status filter">
                      <option value="">All statuses</option>
                      {(featuresData?.statuses || ['active', 'demo_safe', 'mock', 'needs_config']).map((s) => (<option key={s} value={s}>{s}</option>))}
                    </select>
                    <button type="submit">Search</button>
                  </div>
                </form>
                {featuresData && (
                  <p className="muted">{featuresData.feature_count} of {featuresData.total_features} features · {featuresData.categories?.length} categories</p>
                )}
                <div className="agent-template-list">
                  {(featuresData?.features || []).map((feature) => (
                    <div key={feature.key} className="agent-template-card">
                      <strong>{feature.name} <span className="feature-version">{feature.version}</span></strong>
                      <span>{feature.category} · {feature.route}</span>
                      <div className="feature-status-row">
                        {feature.status.map((s) => (<span key={s} className={`feature-badge ${s}`}>{s}</span>))}
                      </div>
                      <div className="master-fb-row">
                        <button type="button" className="master-fb" onClick={() => handleTryFeature(feature.key)}>Try this feature</button>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="muted">Read-only discovery — "Try" shows the route to open.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowHome((current) => !current); if (!dashboardHome) refreshHome() }}>
              <span>
                <Gauge size={15} />
                Dashboard Home
              </span>
              <ChevronDown size={15} />
            </button>
            {showHome && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Dashboard Home · v64.0</strong>
                  <span>One professional homepage — Today, active workspace, approvals, recent runs, health, upcoming tasks, and suggested actions.</span>
                </div>
                {dashboardHome && (
                  <>
                    <div className="home-grid">
                      <div className="home-stat"><strong>{dashboardHome.today?.events_today ?? 0}</strong><span>events today</span></div>
                      <div className="home-stat"><strong>{dashboardHome.today?.pending_approvals ?? 0}</strong><span>approvals</span></div>
                      <div className="home-stat"><strong>{dashboardHome.today?.upcoming_tasks ?? 0}</strong><span>upcoming</span></div>
                      <div className="home-stat"><strong>{dashboardHome.system_health?.score ?? '—'}</strong><span>health {dashboardHome.system_health?.status}</span></div>
                    </div>
                    <p className="muted">workspace: {dashboardHome.active_workspace?.name}</p>
                    {dashboardHome.suggested_actions?.length > 0 && (
                      <div className="agent-template-card">
                        <strong>Suggested next</strong>
                        <span>{dashboardHome.suggested_actions.map((a, i) => <span key={i} className="home-action">• {a}</span>)}</span>
                      </div>
                    )}
                    {dashboardHome.recent_runs?.length > 0 && (
                      <div className="agent-template-list">
                        {dashboardHome.recent_runs.map((run, i) => (
                          <div key={i} className="agent-template-card">
                            <strong>{run.domain || 'Routed'}{run.requires_approval ? ' · needs approval' : ''}</strong>
                            <span>{run.request}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="home-launch">
                      {dashboardHome.quick_launch?.map((card) => (
                        <span key={card.route} className="home-launch-card">{card.label}</span>
                      ))}
                    </div>
                  </>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshHome()}>Refresh</button>
                </div>
                <p className="muted">Read-only overview — nothing is created or executed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowActivity((current) => !current); if (!activityTimeline) refreshActivity() }}>
              <span>
                <Route size={15} />
                Activity Timeline
              </span>
              <ChevronDown size={15} />
            </button>
            {showActivity && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Activity Timeline · v63.0</strong>
                  <span>One chronological view of everything the OS did — runs, approvals, tool executions, memory, files, reports, goals. Read-only.</span>
                </div>
                <div className="inline-actions">
                  <select value={activityType} onChange={(event) => { setActivityType(event.target.value); refreshActivity(event.target.value) }} aria-label="Filter by type">
                    <option value="">All types</option>
                    {(activityTimeline?.types || []).map((t) => (<option key={t} value={t}>{t}</option>))}
                  </select>
                  <button type="button" onClick={() => refreshActivity()} disabled={activityBusy}>Refresh</button>
                  <button type="button" onClick={handleActivityExport}>Export</button>
                </div>
                {activityTimeline && (
                  <p className="muted">{activityTimeline.event_count} of {activityTimeline.total_available} events{activityTimeline.by_type ? ` · ${Object.entries(activityTimeline.by_type).map(([t, n]) => `${t}:${n}`).join(' ')}` : ''}</p>
                )}
                <div className="agent-template-list">
                  {(activityTimeline?.events || []).map((event, index) => (
                    <details key={`${event.source_collection}-${index}`} className="activity-event">
                      <summary>
                        <span className={`activity-dot ${event.governance_linked ? 'gov' : ''}`} />
                        [{event.type}] {event.title}{event.status ? ` · ${event.status}` : ''}
                      </summary>
                      <div className="activity-detail">
                        {event.detail && <p>{event.detail}</p>}
                        <p className="gs-trace">{event.timestamp || 'n/a'} · source: {event.source_collection}{event.actor ? ` · ${event.actor}` : ''}</p>
                      </div>
                    </details>
                  ))}
                </div>
                <p className="muted">Read-only chronological aggregation — no secrets, no writes.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowGlobalSearch((current) => !current)}>
              <span>
                <Layers3 size={15} />
                Global Search
              </span>
              <ChevronDown size={15} />
            </button>
            {showGlobalSearch && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Global Search · v62.0</strong>
                  <span>One read-only search across chats, files, goals, agents, memory, workflows, reports, simulations, schedules, and more.</span>
                </div>
                <form className="stacked-form" onSubmit={runGlobalSearch}>
                  <input type="text" placeholder="Search everything…" value={globalSearchQuery} onChange={(event) => setGlobalSearchQuery(event.target.value)} />
                  <button type="submit" disabled={globalSearchBusy || !globalSearchQuery.trim()}>{globalSearchBusy ? 'Searching…' : 'Search'}</button>
                </form>
                {globalSearchSources && (
                  <p className="muted">{globalSearchSources.total_indexed_items} items across {globalSearchSources.sources?.length} sources</p>
                )}
                {globalSearchResults && (
                  <>
                    {globalSearchResults.error ? (
                      <p className="error">{globalSearchResults.error}</p>
                    ) : (
                      <p className="muted">{globalSearchResults.result_count} result{globalSearchResults.result_count === 1 ? '' : 's'}{globalSearchResults.by_type && Object.keys(globalSearchResults.by_type).length > 0 ? ` · ${Object.entries(globalSearchResults.by_type).map(([t, n]) => `${t}:${n}`).join(' ')}` : ''}</p>
                    )}
                    <div className="agent-template-list">
                      {(globalSearchResults.results || []).map((result) => (
                        <div key={`${result.source_collection}-${result.id}-${result.score}`} className="agent-template-card">
                          <strong>[{result.type}] {result.title}</strong>
                          <span>{result.preview}</span>
                          <span className="gs-trace">source: {result.source_collection} · score {result.score}</span>
                          <div className="master-fb-row">
                            <button type="button" className="master-fb" onClick={() => useSearchResultAsContext(result)}>Use as context</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
                <p className="muted">Read-only — nothing is modified. "Use as context" seeds the composer.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowGitIntel((c) => !c); if (!gitStatus) refreshGitIntel() }}>
              <span>
                <GitBranch size={15} />
                Git Intelligence
              </span>
              <ChevronDown size={15} />
            </button>
            {showGitIntel && (
              <div className="mission-panel" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Card>
                  <p className="ds-title">Git Intelligence</p>
                  <p className="ds-sub">Read-only, opt-in repo discovery — reads git metadata only (no code, no secrets, no git commands).</p>
                  {gitStatus && (
                    <div style={{ marginTop: 8 }}>
                      <Badge tone={gitStatus.enabled ? 'success' : 'default'}>{gitStatus.enabled ? `${gitStatus.indexed_repos} repos indexed` : 'not enabled'}</Badge>
                    </div>
                  )}
                </Card>
                <input className="ds-input" placeholder="Local path to scan (e.g. ~/Projects)" value={gitPath} onChange={(e) => setGitPath(e.target.value)}
                  style={{ padding: '9px 12px', borderRadius: 12, border: '1px solid var(--ds-line-strong)', background: 'var(--ds-surface)', color: 'var(--ds-ink)' }} />
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button variant="primary" size="sm" disabled={gitBusy || !gitPath.trim()} onClick={() => runGitDiscover(true)}>{gitBusy ? 'Scanning…' : 'Discover repos'}</Button>
                  <Button size="sm" disabled={gitBusy} onClick={() => runGitDiscover(false)}>Load sample</Button>
                  <Button variant="ghost" size="sm" onClick={refreshGitIntel}>Refresh</Button>
                </div>
                {gitRepos.map((repo) => (
                  <Card key={repo.repo_id} hover>
                    <p className="ds-title" style={{ fontSize: 14 }}>
                      {repo.name} <Badge tone={repo.provider === 'local' ? 'default' : 'accent'}>{repo.provider}</Badge>
                      {repo.is_sample && <Badge tone="warn">sample</Badge>}
                    </p>
                    <div className="ds-row"><span>Default branch</span><span>{repo.default_branch || '—'}</span></div>
                    <div className="ds-row"><span>Branches</span><span>{(repo.branches || []).length}</span></div>
                    <div className="ds-row"><span>Remote</span><span style={{ fontSize: 11, fontWeight: 400 }}>{repo.remote_url_sanitized || 'none'}</span></div>
                    {repo.recent_activity?.length > 0 && (
                      <p className="ds-sub" style={{ marginTop: 8 }}>Latest: {repo.recent_activity[0].message}</p>
                    )}
                  </Card>
                ))}
                <div className="ds-row" style={{ marginTop: 4 }}>
                  <span className="ds-title" style={{ fontSize: 13 }}>Real reads</span>
                  <span style={{ display: 'flex', gap: 6 }}>
                    <Button size="sm" variant="ghost" disabled={gitReadBusy || !gitPath.trim()} onClick={() => runGitRead('log')}>Log</Button>
                    <Button size="sm" variant="ghost" disabled={gitReadBusy || !gitPath.trim()} onClick={() => runGitRead('branches')}>Branches</Button>
                  </span>
                </div>
                {gitBranches?.branches && (
                  <Card>
                    <p className="ds-title" style={{ fontSize: 13 }}>Branches ({gitBranches.count})</p>
                    {gitBranches.branches.slice(0, 12).map((b) => (
                      <div key={b.name} className="ds-row"><span>{b.current ? '● ' : ''}{b.name}</span><span style={{ fontSize: 11, fontWeight: 400 }}>{b.head}</span></div>
                    ))}
                  </Card>
                )}
                {gitLog?.commits && (
                  <Card>
                    <p className="ds-title" style={{ fontSize: 13 }}>Recent commits ({gitLog.count})</p>
                    {gitLog.commits.slice(0, 12).map((c) => (
                      <div key={c.sha} style={{ marginTop: 4 }}>
                        <div className="ds-row"><span>{c.subject}</span><span style={{ fontSize: 11, fontWeight: 400 }}>{c.short}</span></div>
                        <p className="ds-sub" style={{ fontSize: 11 }}>{c.author} · {(c.date || '').slice(0, 10)}</p>
                      </div>
                    ))}
                  </Card>
                )}
                <p className="ds-sub">Discovery + reads are opt-in and read-only (fixed argv, no shell). Any push/merge/PR/deploy would require approval (not built here).</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="agent" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowAgentStudio((c) => !c); if (!studioTemplates.length) refreshAgentStudio() }}>
              <span>
                <Sparkles size={15} />
                Agent Studio
              </span>
              <ChevronDown size={15} />
            </button>
            {showAgentStudio && (
              <div className="mission-panel" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Card>
                  <p className="ds-title">Build your own agent</p>
                  <p className="ds-sub">Configure a custom agent — role, personality, tools, guardrails, examples. This is configuration + examples, not model training. Test/evaluate are mock-safe.</p>
                </Card>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {studioTemplates.map((t) => (
                    <Button key={t.key} size="sm" variant="ghost" onClick={() => applyAgentTemplate(t)}>{t.name}</Button>
                  ))}
                </div>
                <input placeholder="Agent name" value={agentName} onChange={(e) => setAgentName(e.target.value)}
                  style={{ padding: '9px 12px', borderRadius: 12, border: '1px solid var(--ds-line-strong)', background: 'var(--ds-surface)', color: 'var(--ds-ink)' }} />
                <input placeholder="Role — what should it do?" value={agentRole} onChange={(e) => setAgentRole(e.target.value)}
                  style={{ padding: '9px 12px', borderRadius: 12, border: '1px solid var(--ds-line-strong)', background: 'var(--ds-surface)', color: 'var(--ds-ink)' }} />
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <select value={agentTone} onChange={(e) => setAgentTone(e.target.value)}
                    style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid var(--ds-line-strong)', background: 'var(--ds-surface)', color: 'var(--ds-ink)' }}>
                    {['professional', 'friendly', 'direct', 'creative'].map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <Button variant="primary" size="sm" disabled={agentBusy || !agentName.trim()} onClick={handleCreateAgent}>Create agent</Button>
                </div>
                {agentProfiles.map((a) => (
                  <Card key={a.agent_id} hover>
                    <p className="ds-title" style={{ fontSize: 14 }}>
                      {a.name} <Badge tone="accent">v{a.version}</Badge>
                      {a.published_local && <Badge tone="success">published</Badge>}
                      {a.evaluation?.score != null && <Badge tone={a.evaluation.score >= 60 ? 'success' : 'warn'}>score {a.evaluation.score}{a.evaluation.grade ? ` · ${a.evaluation.grade}` : ''}</Badge>}
                      {(a.versions?.length > 0) && <Badge tone="default">{a.versions.length} prior</Badge>}
                    </p>
                    <p className="ds-sub">{a.role || '—'} · {a.personality?.tone}</p>
                    <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                      <input placeholder="Test prompt…" value={agentTestPrompt} onChange={(e) => setAgentTestPrompt(e.target.value)}
                        style={{ flex: 1, minWidth: 120, padding: '6px 10px', borderRadius: 10, border: '1px solid var(--ds-line)', background: 'var(--ds-surface-2)', color: 'var(--ds-ink)', fontSize: 12 }} />
                      <Button size="sm" disabled={agentBusy} onClick={() => handleTestAgent(a.agent_id)}>Test</Button>
                      <Button size="sm" variant="ghost" disabled={agentBusy} onClick={() => handleAgentAction(a.agent_id, 'evaluate')}>Evaluate</Button>
                      <Button size="sm" variant="ghost" disabled={agentBusy} onClick={() => handleAgentAction(a.agent_id, 'preview')}>Preview</Button>
                      <Button size="sm" variant="ghost" disabled={agentBusy} onClick={() => handleAgentAction(a.agent_id, 'duplicate')}>Fork</Button>
                      <Button size="sm" variant="ghost" disabled={agentBusy} onClick={() => handleAgentAction(a.agent_id, 'publish')}>Publish</Button>
                    </div>
                    {agentTestResult && agentTestResult.agent_id === a.agent_id && (
                      <div style={{ marginTop: 8 }}>
                        <p className="ds-sub">{agentTestResult.simulated_response}</p>
                        {agentTestResult.requires_approval && <Badge tone="warn">requires approval</Badge>}
                      </div>
                    )}
                  </Card>
                ))}
                <p className="ds-sub">Personalization = config + few-shot examples + evaluation feedback. No base-model training; risky actions always held for approval.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowVoiceConsole((c) => !c); if (!voiceSettings) refreshVoiceConsole() }}>
              <span>
                <Volume2 size={15} />
                Voice Console
              </span>
              <ChevronDown size={15} />
            </button>
            {showVoiceConsole && (
              <div className="mission-panel" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Card>
                  <p className="ds-title">Voice Console</p>
                  <p className="ds-sub">Tune how spoken answers sound and how push-to-talk behaves. Voice runs in your browser (Web Speech API).</p>
                  {voiceStatus && (
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                      <Badge tone="success">push-to-talk only</Badge>
                      <Badge tone="default">no recording</Badge>
                      <Badge tone="default">no audio stored</Badge>
                    </div>
                  )}
                </Card>

                <Card>
                  <div className="ds-row"><span>Spoken answers</span>
                    <Button size="sm" variant={voiceOutputEnabled ? 'primary' : 'ghost'} onClick={() => { if (speaking) stopSpeaking(); setVoiceOutputEnabled((v) => !v) }}>{voiceOutputEnabled ? 'On' : 'Off'}</Button>
                  </div>
                  <label className="ds-sub" style={{ display: 'block', marginTop: 10 }}>Voice</label>
                  <select value={voiceSettings?.voice_name || ''} onChange={(e) => saveVoiceSettings({ voice_name: e.target.value })}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: 10, border: '1px solid var(--ds-line-strong)', background: 'var(--ds-surface)', color: 'var(--ds-ink)', marginTop: 4 }}>
                    <option value="">Browser default</option>
                    {availableVoices.map((v) => <option key={v.name} value={v.name}>{v.name} ({v.lang})</option>)}
                  </select>

                  <label className="ds-sub" style={{ display: 'block', marginTop: 10 }}>Speed — {(voiceSettings?.rate ?? 1).toFixed(2)}×</label>
                  <input type="range" min="0.5" max="2" step="0.05" value={voiceSettings?.rate ?? 1} onChange={(e) => saveVoiceSettings({ rate: Number(e.target.value) })} style={{ width: '100%' }} />
                  <label className="ds-sub" style={{ display: 'block', marginTop: 6 }}>Pitch — {(voiceSettings?.pitch ?? 1).toFixed(2)}</label>
                  <input type="range" min="0" max="2" step="0.05" value={voiceSettings?.pitch ?? 1} onChange={(e) => saveVoiceSettings({ pitch: Number(e.target.value) })} style={{ width: '100%' }} />
                  <label className="ds-sub" style={{ display: 'block', marginTop: 6 }}>Volume — {Math.round((voiceSettings?.volume ?? 1) * 100)}%</label>
                  <input type="range" min="0" max="1" step="0.05" value={voiceSettings?.volume ?? 1} onChange={(e) => saveVoiceSettings({ volume: Number(e.target.value) })} style={{ width: '100%' }} />

                  <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                    <Button size="sm" variant="primary" onClick={() => { setVoiceOutputEnabled(true); speak('This is how spoken answers will sound.') }}>Test voice</Button>
                    <Button size="sm" variant="ghost" onClick={stopSpeaking}>Stop</Button>
                  </div>
                </Card>

                <Card>
                  <div className="ds-row"><span>Show live transcript</span>
                    <Button size="sm" variant={voiceSettings?.transcript_enabled ? 'primary' : 'ghost'} onClick={() => saveVoiceSettings({ transcript_enabled: !voiceSettings?.transcript_enabled })}>{voiceSettings?.transcript_enabled ? 'On' : 'Off'}</Button>
                  </div>
                  <div className="ds-row"><span>Store transcript text <span className="ds-sub">(opt-in)</span></span>
                    <Button size="sm" variant={voiceSettings?.store_transcripts ? 'primary' : 'ghost'} onClick={() => saveVoiceSettings({ store_transcripts: !voiceSettings?.store_transcripts })}>{voiceSettings?.store_transcripts ? 'On' : 'Off'}</Button>
                  </div>
                  <p className="ds-sub" style={{ marginTop: 8 }}>Off by default: only counts and timestamps are recorded, never the words you speak.</p>
                </Card>

                <Card>
                  <div className="ds-row"><span>Activity log</span>
                    <Button size="sm" variant="ghost" onClick={clearVoiceHistory}>Clear</Button>
                  </div>
                  {voiceEvents.length === 0 && <p className="ds-sub" style={{ marginTop: 6 }}>No voice activity yet.</p>}
                  {voiceEvents.slice(0, 8).map((ev) => (
                    <div key={ev.id} className="ds-row"><span>{ev.kind}</span><span style={{ fontSize: 11, fontWeight: 400 }}>{ev.char_count} chars</span></div>
                  ))}
                </Card>
                <p className="ds-sub">All voice processing stays in your browser. Nothing is recorded, uploaded, or stored as audio.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowDesignAgent((c) => !c); if (!designStatus) refreshDesignAgent() }}>
              <span>
                <Image size={15} />
                Design Agent
              </span>
              <ChevronDown size={15} />
            </button>
            {showDesignAgent && (
              <div className="mission-panel" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Card>
                  <p className="ds-title">Design Agent</p>
                  <p className="ds-sub">Upload a UI/UX screenshot and get Visual · UX · Market analysis. Mock-safe by default; a live model run is opt-in and only sends the image when you enable it.</p>
                  {designStatus && (
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                      <Badge tone={designStatus.key_configured ? 'success' : 'default'}>{designStatus.key_configured ? 'live model ready' : 'no key — heuristic mode'}</Badge>
                      <Badge tone="default">{designStatus.model}</Badge>
                    </div>
                  )}
                </Card>

                <Card>
                  <label className="ds-btn" style={{ cursor: 'pointer', display: 'inline-flex' }}>
                    {designImageName ? `📎 ${designImageName}` : 'Choose image…'}
                    <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" onChange={onDesignFile} style={{ display: 'none' }} />
                  </label>
                  {designImage && <img src={designImage} alt="preview" style={{ maxWidth: '100%', maxHeight: 160, borderRadius: 10, marginTop: 8, border: '1px solid var(--ds-line)' }} />}

                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
                    {['visual', 'ux', 'market'].map((lens) => (
                      <Button key={lens} size="sm" variant={designLenses.includes(lens) ? 'primary' : 'ghost'} onClick={() => toggleDesignLens(lens)}>{lens}</Button>
                    ))}
                  </div>
                  <textarea placeholder="Optional context — product, audience, a specific question…" value={designContext} onChange={(e) => setDesignContext(e.target.value)}
                    style={{ width: '100%', marginTop: 8, minHeight: 54, padding: '8px 10px', borderRadius: 10, border: '1px solid var(--ds-line-strong)', background: 'var(--ds-surface)', color: 'var(--ds-ink)', resize: 'vertical' }} />

                  <div className="ds-row" style={{ marginTop: 8 }}>
                    <span>Use live model {!designStatus?.key_configured && <span className="ds-sub">(set OPENROUTER_API_KEY)</span>}</span>
                    <Button size="sm" variant={designLive ? 'primary' : 'ghost'} disabled={!designStatus?.key_configured} onClick={() => setDesignLive((v) => !v)}>{designLive ? 'On' : 'Off'}</Button>
                  </div>
                  {designLive && <p className="ds-sub">⚠ Live run sends this image to {designStatus?.model} via OpenRouter.</p>}

                  <div style={{ marginTop: 10 }}>
                    <Button variant="primary" size="sm" disabled={designBusy || !designImage || designLenses.length === 0} onClick={handleAnalyzeDesign}>
                      {designBusy ? 'Analyzing…' : 'Analyze design'}
                    </Button>
                  </div>
                </Card>

                {designResult && (
                  <Card>
                    <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
                      <Badge tone={designResult.mode === 'live' ? 'accent' : designResult.mode === 'error' ? 'warn' : 'default'}>{designResult.mode}</Badge>
                    </div>
                    {designResult.note && <p className="ds-sub" style={{ color: 'var(--ds-accent)' }}>{designResult.note}</p>}
                    {designResult.sections.map((s) => (
                      <div key={s.lens} style={{ marginTop: 8 }}>
                        <p className="ds-title" style={{ fontSize: 13 }}>{s.title}</p>
                        <div className="ds-sub" style={{ fontSize: 12 }}><ReactMarkdown remarkPlugins={[remarkGfm]}>{s.body}</ReactMarkdown></div>
                      </div>
                    ))}
                  </Card>
                )}
                <p className="ds-sub">Ported from the Multimodal Design Agent. Key is read from the environment (never stored/logged); image bytes are never persisted.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowRepoFinder((c) => !c)}>
              <span>
                <GitBranch size={15} />
                Repo Finder
              </span>
              <ChevronDown size={15} />
            </button>
            {showRepoFinder && (
              <div className="mission-panel" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Card>
                  <p className="ds-title">Repo Finder</p>
                  <p className="ds-sub">Describe what you need (e.g. “multi-agent framework”, “voice assistant”) and get relevant GitHub repos to compare — with stars, language, and topics.</p>
                </Card>
                <div style={{ display: 'flex', gap: 6 }}>
                  <input placeholder="What are you looking for?" value={repoQuery} onChange={(e) => setRepoQuery(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleRepoSearch() }}
                    style={{ flex: 1, padding: '9px 12px', borderRadius: 12, border: '1px solid var(--ds-line-strong)', background: 'var(--ds-surface)', color: 'var(--ds-ink)' }} />
                  <Button variant="primary" size="sm" disabled={repoBusy || !repoQuery.trim()} onClick={() => handleRepoSearch()}>{repoBusy ? '…' : 'Find'}</Button>
                </div>
                {repoResult?.related_topics?.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {repoResult.related_topics.map((t) => (
                      <Button key={t} size="sm" variant="ghost" disabled={repoBusy} onClick={() => handleRepoSearch(t)}>{t}</Button>
                    ))}
                  </div>
                )}
                {repoResult?.note && <p className="ds-sub" style={{ color: 'var(--ds-accent)' }}>{repoResult.note}</p>}
                {repoResult && repoResult.count === 0 && !repoResult.note && <p className="ds-sub">No repositories found.</p>}
                {repoResult?.results?.map((r) => (
                  <Card key={r.full_name} hover>
                    <p className="ds-title" style={{ fontSize: 14 }}>
                      <a href={r.url} target="_blank" rel="noreferrer" style={{ color: 'var(--ds-accent)', textDecoration: 'none' }}>{r.full_name}</a>
                      {' '}<Badge tone="default">★ {r.stars.toLocaleString()}</Badge>
                      {r.language && <Badge tone="accent">{r.language}</Badge>}
                    </p>
                    <p className="ds-sub">{r.description || '—'}</p>
                    {r.topics?.length > 0 && <p className="ds-sub" style={{ fontSize: 11 }}>{r.topics.slice(0, 6).map((t) => `#${t}`).join(' ')}</p>}
                  </Card>
                ))}
                <p className="ds-sub">Read-only search of public GitHub. Set GITHUB_TOKEN in the backend env for higher rate limits (token is never stored or shown).</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowWorkflows((c) => !c); if (!workflowTemplates.length) refreshWorkflows() }}>
              <span>
                <Workflow size={15} />
                Durable Workflows
              </span>
              <ChevronDown size={15} />
            </button>
            {showWorkflows && (
              <div className="mission-panel" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Card>
                  <p className="ds-title">Durable Workflows</p>
                  <p className="ds-sub">Long-running, resumable runs. Each step is checkpointed so a run survives restarts; risky steps (send/deploy/pay/…) halt for approval and never auto-run. Execution is simulated (mock-safe).</p>
                </Card>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {workflowTemplates.map((t) => (
                    <Button key={t.key} size="sm" variant="ghost" disabled={durableBusy}
                      onClick={() => runWorkflowAction(() => startWorkflowRun({ template: null, name: t.name, steps: t.steps }))}>
                      ▶ {t.name}
                    </Button>
                  ))}
                </div>
                {workflowRuns.length === 0 && <p className="ds-sub">No runs yet — start one from a template above.</p>}
                {workflowRuns.slice(0, 6).map((run) => {
                  const tone = run.status === 'completed' ? 'success'
                    : run.status === 'waiting_approval' ? 'warn'
                    : run.status === 'cancelled' ? 'default' : 'accent'
                  const doneCount = (run.steps || []).filter((s) => s.status === 'done' || s.status === 'skipped').length
                  return (
                    <Card key={run.run_id} hover>
                      <p className="ds-title" style={{ fontSize: 14 }}>
                        {run.name} <Badge tone={tone}>{run.status.replace('_', ' ')}</Badge>
                        <Badge tone="default">{doneCount}/{(run.steps || []).length}</Badge>
                      </p>
                      <div style={{ marginTop: 6 }}>
                        {(run.steps || []).map((s) => (
                          <div key={s.id} className="ds-row">
                            <span style={{ opacity: s.status === 'pending' ? 0.5 : 1 }}>
                              {s.status === 'done' ? '✓' : s.status === 'skipped' ? '⤼' : s.status === 'waiting_approval' ? '⏸' : '•'} {s.name}
                            </span>
                            {s.requires_approval && <Badge tone="warn">approval</Badge>}
                          </div>
                        ))}
                      </div>
                      <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                        {run.status === 'waiting_approval' && (
                          <>
                            <Button size="sm" variant="primary" disabled={durableBusy} onClick={() => runWorkflowAction(() => approveWorkflowStep(run.run_id, true))}>Approve step</Button>
                            <Button size="sm" variant="ghost" disabled={durableBusy} onClick={() => runWorkflowAction(() => approveWorkflowStep(run.run_id, false))}>Reject</Button>
                          </>
                        )}
                        {run.status === 'running' && <Button size="sm" variant="ghost" disabled={durableBusy} onClick={() => runWorkflowAction(() => pauseWorkflowRun(run.run_id))}>Pause</Button>}
                        {run.status === 'paused' && <Button size="sm" variant="primary" disabled={durableBusy} onClick={() => runWorkflowAction(() => resumeWorkflowRun(run.run_id))}>Resume</Button>}
                        {!['completed', 'cancelled'].includes(run.status) && <Button size="sm" variant="ghost" disabled={durableBusy} onClick={() => runWorkflowAction(() => cancelWorkflowRun(run.run_id))}>Cancel</Button>}
                      </div>
                    </Card>
                  )
                })}
                {workflowEffects.length > 0 && (
                  <Card>
                    <p className="ds-title" style={{ fontSize: 13 }}>Actions performed ({workflowEffects.length})</p>
                    {workflowEffects.slice(0, 8).map((e) => (
                      <div key={e.effect_id} className="ds-row">
                        <span><Badge tone="success">{e.action_type}</Badge> {e.params?.title || e.params?.message || ''}</span>
                        <span style={{ fontSize: 11, fontWeight: 400 }}>{(e.created_at || '').slice(0, 10)}</span>
                      </div>
                    ))}
                  </Card>
                )}
                <p className="ds-sub">Approval-gated and governance-logged. Most steps simulate; steps with a whitelisted internal action (create_task · create_note · notify) perform a real, local, reversible effect only after you approve — never an external mutation.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="build" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => { setShowMarketplaceHub((c) => !c); if (!marketplaceListings.length) refreshMarketplaceHub() }}>
              <span>
                <Store size={15} />
                Marketplace
              </span>
              <ChevronDown size={15} />
            </button>
            {showMarketplaceHub && (
              <div className="mission-panel" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Card>
                  <p className="ds-title">Marketplace</p>
                  <p className="ds-sub">Install agents and workflows as sanitized, local bundles. No network, no accounts — installing re-derives guardrails so risky powers always start held for approval.</p>
                </Card>
                <div style={{ display: 'flex', gap: 6 }}>
                  {['', 'agent', 'workflow'].map((k) => (
                    <Button key={k || 'all'} size="sm" variant={marketplaceKind === k ? 'primary' : 'ghost'}
                      onClick={() => { setMarketplaceKind(k); refreshMarketplaceHub(k) }}>
                      {k === '' ? 'All' : k === 'agent' ? 'Agents' : 'Workflows'}
                    </Button>
                  ))}
                </div>
                {marketplaceNote && <p className="ds-sub" style={{ color: 'var(--ds-accent)' }}>{marketplaceNote}</p>}
                {marketplaceListings.length === 0 && <p className="ds-sub">No listings.</p>}
                {marketplaceListings.map((l) => (
                  <Card key={l.listing_id} hover>
                    <p className="ds-title" style={{ fontSize: 14 }}>
                      {l.name} <Badge tone={l.kind === 'agent' ? 'accent' : 'default'}>{l.kind}</Badge>
                      {l.is_featured && <Badge tone="success">featured</Badge>}
                    </p>
                    <p className="ds-sub">{l.summary || '—'}</p>
                    <div className="ds-row"><span>by {l.publisher}</span><span style={{ fontSize: 11, fontWeight: 400 }}>{l.installs} installs</span></div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                      <Button size="sm" variant="primary" disabled={marketplaceBusy} onClick={() => handleInstallListing(l)}>Install</Button>
                      {!l.is_featured && <Button size="sm" variant="ghost" disabled={marketplaceBusy} onClick={() => handleUnpublishListing(l.listing_id)}>Remove</Button>}
                    </div>
                  </Card>
                ))}
                <p className="ds-sub">Installed agents land in Agent Studio; installed workflows land in Durable Workflows. Bundles carry config only — never secrets.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="agent" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowMasterPanel((current) => !current)}>
              <span>
                <Brain size={15} />
                Master Agent
              </span>
              <ChevronDown size={15} />
            </button>
            {showMasterPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Master Agent · v60.1</strong>
                  <span>Single top-level AI routing across all of v1–v60. Planning-first &amp; approval-gated — risky actions are always held for approval. Not AGI.</span>
                </div>
                {masterSummary && (
                  <p className="muted">
                    routes: {masterSummary.total_routes} · approvals: {masterSummary.approvals_required} · fallback: {masterSummary.fallback_routes ?? 0}
                    {masterSummary.avg_confidence != null && <> · avg conf: {Math.round(masterSummary.avg_confidence * 100)}%</>}
                    {masterSummary.route_accuracy?.accuracy_pct != null && <> · accuracy: {masterSummary.route_accuracy.accuracy_pct}% ({masterSummary.route_accuracy.rated_routes} rated)</>}
                  </p>
                )}
                {masterSummary && Object.keys(masterSummary.by_domain || {}).length > 0 && (
                  <div className="agent-template-list">
                    {Object.entries(masterSummary.by_domain).map(([domain, count]) => (
                      <div key={domain} className="agent-template-card">
                        <strong>{domain}</strong>
                        <span>{count} route{count === 1 ? '' : 's'}</span>
                      </div>
                    ))}
                  </div>
                )}
                {masterSummary?.recent?.length > 0 && (
                  <div className="agent-template-list">
                    {masterSummary.recent.slice(0, 6).map((run) => (
                      <div key={run.run_id} className="agent-template-card">
                        <strong>
                          {run.primary_domain || 'Routed'}
                          {run.fallback_used ? ' · fallback' : run.confidence != null ? ` · ${Math.round(run.confidence * 100)}%` : ''}
                          {run.requires_approval ? ' · needs approval' : ''}
                        </strong>
                        <span>{run.request}</span>
                        <div className="master-fb-row">
                          {run.feedback ? (
                            <span className="master-fb-done">{run.feedback.correct ? '✓ marked correct' : '✗ marked wrong'}</span>
                          ) : (
                            <>
                              <button type="button" className="master-fb" onClick={() => handleMasterRouteFeedback(run.run_id, true)}>👍 correct</button>
                              <button type="button" className="master-fb" onClick={() => handleMasterRouteFeedback(run.run_id, false)}>👎 wrong</button>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {masterCapabilities?.capabilities?.length > 0 && (
                  <details className="master-panel-caps">
                    <summary>{masterCapabilities.capability_count} capabilities</summary>
                    <div className="agent-template-list">
                      {masterCapabilities.capabilities.map((cap) => (
                        <div key={cap.domain} className="agent-template-card">
                          <strong>{cap.domain}{cap.risky ? ' · risky' : ''}</strong>
                          <span>{cap.route} — {(cap.trigger_examples || []).join(', ')}</span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshMasterPanel()}>Refresh</button>
                </div>
                <p className="muted">{masterSummary?.disclaimer || 'Not AGI — a governed orchestration router over the existing systems. Secret key readiness is boolean-only; risky actions require approval.'}</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowOs2((current) => !current)}>
              <span>
                <Cpu size={15} />
                EvolveAgent OS 2.0
              </span>
              <ChevronDown size={15} />
            </button>
            {showOs2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>EvolveAgent OS 2.0 · v60.0 (capstone)</strong>
                  <span>Unified command center over every system (v1–v59) + live platform scorecard. Read-only aggregation of local data — not AGI.</span>
                </div>
                {os2Dashboard && (
                  <>
                    <p className="muted">
                      grade {os2Dashboard.scorecard?.overall_grade} ({os2Dashboard.scorecard?.overall_score}/100) · systems {os2Dashboard.command_center?.active_systems}/{os2Dashboard.command_center?.total_systems} active · health {os2Dashboard.health?.status}
                    </p>
                    <div className="agent-template-list">
                      {(os2Dashboard.command_center?.domains || []).map((domain) => (
                        <div key={domain.domain} className="agent-template-card">
                          <strong>{domain.domain} · {domain.active_count}/{domain.system_count} active</strong>
                          <span>{(domain.systems || []).map((system) => system.label).join(' · ')}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleOs2Snapshot} disabled={os2Busy}>Snapshot</button>
                  <button type="button" onClick={handleOs2Report} disabled={os2Busy}>Generate report</button>
                  <button type="button" onClick={() => refreshOs2()} disabled={os2Busy}>Refresh</button>
                </div>
                {os2Report && (
                  <div className="agent-template-card">
                    <strong>{os2Report.title}</strong>
                    <p className="muted">{os2Report.headline}</p>
                  </div>
                )}
                <p className="muted">{os2Dashboard?.disclaimer || 'This is not AGI — a governed orchestration layer across existing agents, workflows, tools, memory, simulations, and dashboards.'}</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowScheduled((current) => !current)}>
              <span>
                <Cpu size={15} />
                Scheduled Tasks
              </span>
              <ChevronDown size={15} />
            </button>
            {showScheduled && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Scheduled Tasks · v58.0</strong>
                  <span>Local registry of scheduled tasks. Planning-first — no real background scheduler; triggers produce mock/planned runs, risky steps need approval.</span>
                </div>
                {scheduledSummary && (
                  <p className="muted">tasks: {scheduledSummary.task_count} · enabled: {scheduledSummary.enabled_count} · due: {scheduledSummary.due_count} · runs: {scheduledSummary.run_count}</p>
                )}
                <form className="stacked-form" onSubmit={handleCreateScheduled}>
                  <input type="text" placeholder="Task name" value={scheduledName} onChange={(event) => setScheduledName(event.target.value)} />
                  <select value={scheduledSchedule} onChange={(event) => setScheduledSchedule(event.target.value)}>
                    {['manual', 'hourly', 'daily', 'weekly'].map((s) => (<option key={s} value={s}>{s}</option>))}
                  </select>
                  <button type="submit" disabled={scheduledBusy || !scheduledName.trim()}>Create task</button>
                </form>
                {scheduledTasks.slice(0, 6).map((t) => (
                  <div className="agent-template-card" key={t.task_id}>
                    <strong>{t.name}</strong>
                    <p className="muted">{t.schedule} · {t.enabled ? 'enabled' : 'disabled'} · ran {t.trigger_count || 0}×</p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleTriggerScheduled(t.task_id)} disabled={scheduledBusy || !t.enabled}>Trigger (mock)</button>
                      <button type="button" onClick={() => handleToggleScheduled(t.task_id, !t.enabled)} disabled={scheduledBusy}>{t.enabled ? 'Disable' : 'Enable'}</button>
                    </div>
                  </div>
                ))}
                <p className="muted">Planning-first — no real background scheduler or execution; nothing runs on a timer.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="workspace" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowWsTemplates((current) => !current)}>
              <span>
                <Cpu size={15} />
                Workspace Templates
              </span>
              <ChevronDown size={15} />
            </button>
            {showWsTemplates && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Workspace Templates & Cloning · v57.0</strong>
                  <span>Define reusable workspace presets and instantiate them into new local workspaces. Local records only — no production provisioning or auth.</span>
                </div>
                {wsTemplatesSummary && (
                  <p className="muted">templates: {wsTemplatesSummary.template_count} · instantiations: {wsTemplatesSummary.total_instantiations}</p>
                )}
                <form className="stacked-form" onSubmit={handleCreateWsTemplate}>
                  <input type="text" placeholder="Template name (e.g. Engineering workspace)" value={wsTemplateName} onChange={(event) => setWsTemplateName(event.target.value)} />
                  <button type="submit" disabled={wsTemplateBusy || !wsTemplateName.trim()}>Create template</button>
                </form>
                {wsTemplates.slice(0, 6).map((t) => (
                  <div className="agent-template-card" key={t.template_id}>
                    <strong>{t.name}</strong>
                    <p className="muted">{t.default_tags?.join(', ') || 'no tags'} · used {t.instantiation_count || 0}×</p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleInstantiateWsTemplate(t.template_id)} disabled={wsTemplateBusy}>Create workspace from this</button>
                    </div>
                  </div>
                ))}
                <p className="muted">Local workspace templates and clones only — no production provisioning or authentication.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowNotifications((current) => !current)}>
              <span>
                <Cpu size={15} />
                Notifications{notificationsSummary?.unread ? ` (${notificationsSummary.unread})` : ''}
              </span>
              <ChevronDown size={15} />
            </button>
            {showNotifications && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Notifications & Alerts Center · v56.0</strong>
                  <span>Local in-app digest of governance blocks, health, and approvals backlog. No email/SMS/push is sent.</span>
                </div>
                {notificationsSummary && (
                  <p className="muted">unread: {notificationsSummary.unread} · critical: {notificationsSummary.critical_unread} · total: {notificationsSummary.total}</p>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleGenerateNotifications} disabled={notifBusy}>Generate</button>
                  <button type="button" onClick={() => refreshNotifications()} disabled={notifBusy}>Refresh</button>
                </div>
                {notifications.length === 0 && <p className="muted">No unread notifications. 🎉</p>}
                {notifications.slice(0, 8).map((n) => (
                  <div className="agent-template-card" key={n.notif_id}>
                    <strong><span className={`risk-badge ${n.severity === 'info' ? 'risk-low' : n.severity === 'warning' ? 'risk-medium' : 'risk-high'}`}>{n.severity}</span> {n.type}</strong>
                    <p className="muted">{n.message}</p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleAckNotification(n.notif_id)} disabled={notifBusy}>Acknowledge</button>
                    </div>
                  </div>
                ))}
                <p className="muted">In-app digest only — no external delivery (email/SMS/push).</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowOpLayer2((current) => !current)}>
              <span>
                <Cpu size={15} />
                Operating Layer 2.0
              </span>
              <ChevronDown size={15} />
            </button>
            {showOpLayer2 && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>EvolveAgent Operating Layer 2.0 · v55.0</strong>
                  <span>Expanded capability map across v41–v53 + a platform readiness & governance scorecard.</span>
                </div>
                {opLayer2 && (
                  <>
                    <div className="agent-template-card">
                      <strong>Overall: {opLayer2.overall_score}/100 · grade {opLayer2.overall_grade} · coverage {opLayer2.coverage_pct}%</strong>
                    </div>
                    {(opLayer2.dimensions || []).map((dim) => (
                      <p className="muted" key={dim.name}>
                        <span className={`risk-badge ${dim.grade === 'A' || dim.grade === 'B' ? 'risk-low' : dim.grade === 'C' ? 'risk-medium' : 'risk-high'}`}>{dim.grade}</span> {dim.name} — {dim.score}
                      </p>
                    ))}
                    <p className="muted">capabilities active: {opLayer2.active_capability_groups}/{opLayer2.total_capability_groups}</p>
                  </>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleOpLayer2Snapshot} disabled={opLayer2Busy}>Snapshot</button>
                  <button type="button" onClick={handleOpLayer2Report} disabled={opLayer2Busy}>Final report</button>
                  <button type="button" onClick={() => refreshOpLayer2()} disabled={opLayer2Busy}>Refresh</button>
                </div>
                {opLayer2Report && (
                  <div className="agent-template-card">
                    <strong>{opLayer2Report.headline}</strong>
                    <p className="muted">{opLayer2Report.disclaimer}</p>
                  </div>
                )}
                {opLayer2?.disclaimer && <p className="muted"><strong>Disclaimer:</strong> {opLayer2.disclaimer}</p>}
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowPlaybooks((current) => !current)}>
              <span>
                <Cpu size={15} />
                Playbook Library
              </span>
              <ChevronDown size={15} />
            </button>
            {showPlaybooks && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Playbook Library · v53.0</strong>
                  <span>Reusable multi-step playbooks. Runs are planning-first — steps are planned or held for approval; nothing is executed.</span>
                </div>
                {playbooksSummary && (
                  <p className="muted">playbooks: {playbooksSummary.playbook_count} · runs: {playbooksSummary.run_count}</p>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleCreateSamplePlaybook} disabled={playbookBusy}>New sample playbook</button>
                  <button type="button" onClick={() => refreshPlaybooks()} disabled={playbookBusy}>Refresh</button>
                </div>
                {playbooks.slice(0, 6).map((pb) => (
                  <div className="agent-template-card" key={pb.playbook_id}>
                    <strong>{pb.name}</strong>
                    <p className="muted">{pb.step_count} step(s)</p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleRunPlaybook(pb.playbook_id)} disabled={playbookBusy}>Run (planning)</button>
                    </div>
                  </div>
                ))}
                {playbookRun && (
                  <div className="agent-template-card">
                    <strong>Run · {playbookRun.planned_count} planned · {playbookRun.approval_required_count} need approval</strong>
                    {(playbookRun.steps || []).map((step) => (
                      <p className="muted" key={step.step_index}>{step.status === 'approval_required' ? '⏸️' : step.status === 'planned' ? '📝' : 'ℹ️'} {step.title} — {step.status}</p>
                    ))}
                  </div>
                )}
                <p className="muted">Planning-first — nothing is executed; risky steps require approval.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="intel" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowEvalHarness((current) => !current)}>
              <span>
                <Cpu size={15} />
                Evaluation Harness
              </span>
              <ChevronDown size={15} />
            </button>
            {showEvalHarness && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Evaluation Harness 2.0 · v52.0</strong>
                  <span>Repeatable eval suites + scorecards with regression tracking. Deterministic, mock-safe — no real LLM call.</span>
                </div>
                {evalSummary && (
                  <p className="muted">suites: {evalSummary.suite_count} · runs: {evalSummary.run_count} · latest score: {evalSummary.latest_score ?? '—'} · regressions: {evalSummary.regressed_runs}</p>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleCreateSampleEvalSuite} disabled={evalBusy}>New sample suite</button>
                  <button type="button" onClick={() => refreshEvalHarness()} disabled={evalBusy}>Refresh</button>
                </div>
                {evalSuites.slice(0, 6).map((suite) => (
                  <div className="agent-template-card" key={suite.suite_id}>
                    <strong>{suite.name}</strong>
                    <p className="muted">{suite.case_count} case(s)</p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleRunEvalSuite(suite.suite_id)} disabled={evalBusy}>Run</button>
                    </div>
                  </div>
                ))}
                {evalRun && (
                  <div className="agent-template-card">
                    <strong>Run · score {evalRun.score} · {evalRun.pass_count}/{evalRun.case_count} passed{evalRun.regressed ? ' · ⚠️ REGRESSED' : ''}</strong>
                    <p className="muted">delta vs previous: {evalRun.delta ?? '—'}</p>
                  </div>
                )}
                <p className="muted">Deterministic, mock-safe scoring — scores are stable and regressions detectable across runs.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowRetrieval((current) => !current)}>
              <span>
                <Cpu size={15} />
                Local Retrieval
              </span>
              <ChevronDown size={15} />
            </button>
            {showRetrieval && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Local Retrieval Layer · v51.0</strong>
                  <span>Index workspace notes and query them with local keyword retrieval + citations. No external vector DB, no network.</span>
                </div>
                {retrievalSummary && (
                  <p className="muted">documents: {retrievalSummary.document_count} · chunks: {retrievalSummary.chunk_count} · queries: {retrievalSummary.query_count}</p>
                )}
                <form className="stacked-form" onSubmit={handleIndexRetrievalDoc}>
                  <textarea placeholder="Paste a note/document to index for this workspace" value={retrievalDocText} onChange={(event) => setRetrievalDocText(event.target.value)} rows={2} />
                  <button type="submit" disabled={retrievalBusy || !retrievalDocText.trim()}>Index document</button>
                </form>
                <form className="stacked-form" onSubmit={handleQueryRetrieval}>
                  <input type="text" placeholder="Query (keyword retrieval)" value={retrievalQuery} onChange={(event) => setRetrievalQuery(event.target.value)} />
                  <button type="submit" disabled={retrievalBusy || !retrievalQuery.trim()}>Query</button>
                </form>
                {retrievalResults.map((result, index) => (
                  <div className="agent-template-card" key={index}>
                    <strong>{result.citation} · score {result.score}</strong>
                    <p className="muted">{result.text?.slice(0, 240)}</p>
                    <p className="muted">matched: {(result.matched_terms || []).join(', ')}</p>
                  </div>
                ))}
                <p className="muted">Local-first retrieval — chunks and scores computed locally; no external vector database or network call.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowUsageLedger((current) => !current)}>
              <span>
                <Cpu size={15} />
                Cost & Usage Ledger
              </span>
              <ChevronDown size={15} />
            </button>
            {showUsageLedger && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Cost & Usage Ledger · v50.0</strong>
                  <span>Local usage estimates + per-workspace budget for this workspace. Estimates only — no billing or charge.</span>
                </div>
                {usageSummary && (
                  <>
                    <div className="analytics-mini-grid">
                      <div><span>Entries</span><strong>{usageSummary.entry_count}</strong></div>
                      <div><span>Est. cost</span><strong>${usageSummary.total_estimated_cost}</strong></div>
                      <div><span>Budget</span><strong>${usageSummary.monthly_limit}</strong></div>
                      <div><span>Status</span><strong>{usageSummary.budget_status}</strong></div>
                    </div>
                    {usageSummary.warning && <p className="error-text">{usageSummary.warning}</p>}
                    {Object.entries(usageSummary.by_capability || {}).map(([cap, cost]) => (
                      <p className="muted" key={cap}>{cap}: ${cost}</p>
                    ))}
                  </>
                )}
                <form className="stacked-form" onSubmit={handleSetUsageBudget}>
                  <input type="number" step="0.01" placeholder="monthly budget ($)" value={usageBudgetInput} onChange={(event) => setUsageBudgetInput(event.target.value)} />
                  <button type="submit" disabled={usageBusy || !usageBudgetInput.trim()}>Set budget</button>
                </form>
                <div className="inline-actions">
                  <button type="button" onClick={handleRecordSampleUsage} disabled={usageBusy}>Record sample usage</button>
                  <button type="button" onClick={() => refreshUsageLedger()} disabled={usageBusy}>Refresh</button>
                </div>
                <p className="muted">Estimates only — extends v11 cost visibility; no billing, charging, or payment is performed.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowHealthMonitor((current) => !current)}>
              <span>
                <Cpu size={15} />
                Health & Readiness
              </span>
              <ChevronDown size={15} />
            </button>
            {showHealthMonitor && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Health & Readiness Monitor · v49.0</strong>
                  <span>Read-only scored health across governance, approvals backlog, secret readiness, connectors, and policies.</span>
                </div>
                {healthDashboard && (
                  <>
                    <div className="agent-template-card">
                      <strong>Health score: {healthDashboard.health_score} · <span className={`risk-badge ${healthDashboard.status === 'healthy' ? 'risk-low' : healthDashboard.status === 'degraded' ? 'risk-medium' : 'risk-high'}`}>{healthDashboard.status}</span></strong>
                    </div>
                    {(healthDashboard.checks || []).map((check) => (
                      <p className="muted" key={check.name}>
                        <span className={`risk-badge ${check.status === 'ok' || check.status === 'info' ? 'risk-low' : check.status === 'warn' ? 'risk-medium' : 'risk-high'}`}>{check.status}</span> {check.name} — {check.detail}
                      </p>
                    ))}
                    {(healthDashboard.recommendations || []).map((rec, index) => (
                      <p className="muted" key={index}>• {rec}</p>
                    ))}
                  </>
                )}
                <div className="inline-actions">
                  <button type="button" onClick={handleCreateHealthSnapshot} disabled={healthBusy}>Snapshot</button>
                  <button type="button" onClick={() => refreshHealthMonitor()} disabled={healthBusy}>Refresh</button>
                </div>
                <p className="muted">Read-only aggregation — no actions are taken.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowApprovalsCenter((current) => !current)}>
              <span>
                <Cpu size={15} />
                Approvals Center
              </span>
              <ChevronDown size={15} />
            </button>
            {showApprovalsCenter && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>Unified Approvals Center · v48.0</strong>
                  <span>One prioritized queue across all approval sources (MCP executions + business-operator). Approve/reject delegates to the owning governed service.</span>
                </div>
                {approvalsCenterSummary && (
                  <div className="analytics-mini-grid">
                    <div><span>Pending</span><strong>{approvalsCenterSummary.pending_count}</strong></div>
                    <div><span>High risk</span><strong>{approvalsCenterSummary.high_risk_pending}</strong></div>
                    <div><span>MCP</span><strong>{approvalsCenterSummary.by_source?.mcp_execution}</strong></div>
                    <div><span>Business</span><strong>{approvalsCenterSummary.by_source?.business_operator}</strong></div>
                  </div>
                )}
                {acError && <p className="error-text">{acError}</p>}
                <div className="inline-actions">
                  <button type="button" onClick={() => refreshApprovalsCenter()} disabled={acBusy}>Refresh</button>
                </div>
                {approvalsCenter.length === 0 && <p className="muted">No pending approvals across any source. 🎉</p>}
                {approvalsCenter.slice(0, 8).map((item) => (
                  <div className="agent-template-card" key={`${item.source}:${item.item_id}`}>
                    <strong>{item.title}</strong>
                    <p className="muted">
                      {item.source} · <span className={`risk-badge risk-${item.risk_level}`}>{item.risk_level} risk</span> · {item.age_seconds}s old
                    </p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleApproveCenter(item.source, item.item_id)} disabled={acBusy}>Approve</button>
                      <button type="button" onClick={() => handleRejectCenter(item.source, item.item_id)} disabled={acBusy}>Reject</button>
                    </div>
                  </div>
                ))}
                <p className="muted">Triage + delegated decisions only — each decision routes to its owning governed service and is logged there.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="tools" className="sidebar-section">
            <button className="analytics-toggle" type="button" onClick={() => setShowMcpPanel((current) => !current)}>
              <span>
                <Cpu size={15} />
                MCP Hub
              </span>
              <ChevronDown size={15} />
            </button>
            {showMcpPanel && (
              <div className="mission-panel">
                <div className="agent-template-card">
                  <strong>MCP Connector Hub · v41.0</strong>
                  <span>Register, configure, and safely plan tool connections (GitHub, Linear, Filesystem, Playwright, Slack, Notion, …). Planning-first — no real MCP execution; no secrets exposed.</span>
                </div>
                {mcpSummary && (
                  <div className="analytics-mini-grid">
                    <div><span>Connectors</span><strong>{mcpSummary.total_connectors}</strong></div>
                    <div><span>Enabled</span><strong>{mcpSummary.enabled_connectors}</strong></div>
                    <div><span>High risk</span><strong>{mcpSummary.high_risk_connectors}</strong></div>
                    <div><span>Approval</span><strong>{mcpSummary.approval_required_connectors}</strong></div>
                  </div>
                )}
                {mcpError && <p className="error-text">{mcpError}</p>}

                <div className="inline-actions">
                  <select value={mcpTemplateSlug} onChange={(event) => setMcpTemplateSlug(event.target.value)}>
                    {mcpTemplates.map((template) => (
                      <option key={template.slug} value={template.slug}>{template.name} ({template.risk_level})</option>
                    ))}
                  </select>
                  <button type="button" onClick={handleAddMcpConnector} disabled={mcpBusy}>Add connector</button>
                  <button type="button" onClick={() => refreshMcpPanel()} disabled={mcpBusy}>Refresh</button>
                </div>

                <div className="mcp-tabbar">
                  {[
                    { id: 'connectors', label: `Connectors${mcpConnectors.length ? ` (${mcpConnectors.length})` : ''}` },
                    { id: 'policies', label: `Policies${mcpPolicies.length ? ` (${mcpPolicies.length})` : ''}` },
                    { id: 'approvals', label: `Approvals${mcpInboxSummary?.pending_count ? ` (${mcpInboxSummary.pending_count})` : ''}` },
                    { id: 'executions', label: 'Executions' },
                    { id: 'audit', label: 'Audit' },
                    { id: 'secrets', label: `Secrets${mcpSecretsSummary?.total_refs ? ` (${mcpSecretsSummary.total_refs})` : ''}` },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      className={`mcp-tab${mcpTab === tab.id ? ' active' : ''}`}
                      onClick={() => setMcpTab(tab.id)}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {mcpTab === 'connectors' && (
                <>
                {mcpConnectors.length > 0 && (
                  <>
                    <h3>Connectors</h3>
                    {mcpConnectors.map((connector) => (
                      <div className="agent-template-card" key={connector.connector_id}>
                        <strong>{connector.name}</strong>
                        <p className="muted">{connector.description}</p>
                        <p className="muted">
                          status: {connector.status} · <span className={`risk-badge risk-${connector.risk_level}`}>{connector.risk_level} risk</span> · mode: {connector.mode} · {connector.enabled ? 'enabled' : 'disabled'}
                        </p>
                        {connector.risk_level === 'high' && (
                          <p className="muted">⚠️ High-risk connector — requires explicit approval; keep disabled unless needed.</p>
                        )}
                        <div className="inline-actions">
                          <button type="button" onClick={() => handleCheckMcpConnector(connector.connector_id)} disabled={mcpBusy}>Check status</button>
                          {connector.enabled
                            ? <button type="button" onClick={() => handleDisableMcpConnector(connector.connector_id)} disabled={mcpBusy}>Disable</button>
                            : <button type="button" onClick={() => handleEnableMcpConnector(connector.connector_id)} disabled={mcpBusy || connector.mode === 'disabled'}>Enable</button>}
                          <button type="button" onClick={() => setMcpSelectedId(connector.connector_id)} disabled={mcpBusy}>Select</button>
                        </div>
                        {/* Developer Mode extras — env-key readiness (booleans only) + capabilities/actions */}
                        {connector.env_keys_required?.length > 0 && (
                          <p className="muted">env keys set: {Object.entries(connector.env_keys_status || {}).map(([k, v]) => `${k}=${v ? 'yes' : 'no'}`).join(', ')}</p>
                        )}
                        {connector.capabilities?.length > 0 && (
                          <p className="muted">capabilities: {connector.capabilities.join(', ')}</p>
                        )}
                        {connector.blocked_actions?.length > 0 && (
                          <p className="muted">blocked: {connector.blocked_actions.join(', ')}</p>
                        )}
                      </div>
                    ))}
                  </>
                )}

                {mcpCheckResult && (
                  <div className="agent-template-card">
                    <strong>Dry status check · {mcpCheckResult.status}</strong>
                    <p className="muted">{mcpCheckResult.note}</p>
                    <p className="muted">required keys set: {JSON.stringify(mcpCheckResult.env_keys_status)}</p>
                  </div>
                )}

                <form className="stacked-form" onSubmit={handlePlanMcpAction}>
                  <h3>Plan an action (selected connector)</h3>
                  <input type="text" placeholder="action_name (e.g. list_issues)" value={mcpActionName} onChange={(event) => setMcpActionName(event.target.value)} />
                  <button type="submit" disabled={mcpBusy || !mcpSelectedId || !mcpActionName.trim()}>Plan action</button>
                </form>

                {mcpPlanResult && (
                  <div className="agent-template-card">
                    <strong>{mcpPlanResult.planned ? 'Action planned' : 'Action blocked'}</strong>
                    {mcpPlanResult.planned ? (
                      <>
                        <p className="muted">requires approval: {String(mcpPlanResult.requires_approval)} · risk: {mcpPlanResult.risk_level}</p>
                        {(mcpPlanResult.plan || []).map((step, index) => (<p className="muted" key={index}>→ {step}</p>))}
                      </>
                    ) : (
                      <p className="muted">blocked: {mcpPlanResult.blocked_reason}</p>
                    )}
                  </div>
                )}
                </>
                )}

                {mcpTab === 'policies' && (
                <>
                {/* v45 — MCP Policy Engine (tighten-only deny rules) */}
                <h3>Policies (v45 · deny-only)</h3>
                <p className="muted">Tighten-only rules evaluated before planning. They can only add blocks, never grant access.</p>
                <form className="stacked-form" onSubmit={handleCreateMcpPolicy}>
                  <input type="text" placeholder="Policy name" value={mcpPolicyName} onChange={(event) => setMcpPolicyName(event.target.value)} />
                  <input type="text" placeholder="connector slug (or *)" value={mcpPolicySlug} onChange={(event) => setMcpPolicySlug(event.target.value)} />
                  <input type="text" placeholder="action (or *)" value={mcpPolicyAction} onChange={(event) => setMcpPolicyAction(event.target.value)} />
                  <button type="submit" disabled={mcpBusy || !mcpPolicyName.trim()}>Add deny policy</button>
                </form>
                {mcpPolicies.slice(0, 6).map((policy) => (
                  <div className="agent-template-card" key={policy.policy_id}>
                    <strong>{policy.name}</strong>
                    <p className="muted">deny {policy.connector_slug}/{policy.action}/{policy.risk_level}{policy.except_actions?.length ? ` · except ${policy.except_actions.join(', ')}` : ''} · {policy.enabled ? 'enabled' : 'disabled'}</p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleToggleMcpPolicy(policy.policy_id, !policy.enabled)} disabled={mcpBusy}>{policy.enabled ? 'Disable' : 'Enable'}</button>
                    </div>
                  </div>
                ))}
                </>
                )}

                {mcpTab === 'approvals' && (
                <>
                {/* v44 — MCP Approvals Inbox (prioritized queue of pending approvals) */}
                <h3>Approvals Inbox (v44)</h3>
                {mcpInboxSummary && (
                  <p className="muted">
                    pending: {mcpInboxSummary.pending_count} · high-risk: {mcpInboxSummary.high_risk_pending} · oldest: {mcpInboxSummary.oldest_pending_seconds}s
                  </p>
                )}
                {mcpInbox.length === 0 && <p className="muted">No pending approvals. 🎉</p>}
                {mcpInbox.slice(0, 6).map((item) => (
                  <div className="agent-template-card" key={item.item_id}>
                    <strong>{item.action_name}</strong>
                    <p className="muted">
                      {item.connector_name} · <span className={`risk-badge risk-${item.risk_level}`}>{item.risk_level} risk</span> · {item.age_seconds}s old
                    </p>
                    <p className="muted">{item.recommended_action}</p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleApproveInboxItem(item.item_id)} disabled={mcpBusy}>Approve</button>
                      <button type="button" onClick={() => handleRejectInboxItem(item.item_id)} disabled={mcpBusy}>Reject</button>
                    </div>
                  </div>
                ))}
                </>
                )}

                {mcpTab === 'executions' && (
                <>
                {/* v42 — MCP Execution Adapter (approval-gated) · v43 — Read-Only Adapter (opt-in) */}
                <h3>Executions (v42/v43 · mock-by-default)</h3>
                {mcpExecSummary && (
                  <p className="muted">
                    mode: {mcpExecSummary.execution_mode} · requests: {mcpExecSummary.total_requests} · pending: {mcpExecSummary.pending_approval} · executed: {mcpExecSummary.executed} · blocked: {mcpExecSummary.blocked}
                  </p>
                )}
                {mcpAdapterStatus && (
                  <div className="agent-template-card">
                    <strong>Read-only adapter (v43) · {mcpAdapterStatus.real_readonly_enabled ? 'REAL opt-in ON' : 'mock (opt-in off)'}</strong>
                    <p className="muted">allow-list: {(mcpAdapterStatus.allowed_actions || []).join(', ')}</p>
                    <p className="muted">sandbox: {mcpAdapterStatus.sandbox_root}</p>
                    <p className="muted">shell: {String(mcpAdapterStatus.capabilities?.shell)} · network: {String(mcpAdapterStatus.capabilities?.network)} · writes: {String(mcpAdapterStatus.capabilities?.writes)} · returns secrets: {String(mcpAdapterStatus.capabilities?.returns_secrets)}</p>
                    <p className="muted">Set <code>{mcpAdapterStatus.opt_in_env}</code> to enable real read-only execution for allow-listed actions (still approval-gated).</p>
                  </div>
                )}
                <form className="stacked-form" onSubmit={handleRequestMcpExecution}>
                  <input type="text" placeholder="action to execute (selected connector)" value={mcpExecActionName} onChange={(event) => setMcpExecActionName(event.target.value)} />
                  <button type="submit" disabled={mcpBusy || !mcpSelectedId || !mcpExecActionName.trim()}>Request execution</button>
                </form>
                {mcpExecutions.slice(0, 6).map((request) => (
                  <div className="agent-template-card" key={request.request_id}>
                    <strong>{request.action_name}</strong>
                    <p className="muted">status: {request.status} · risk: {request.risk_level}{request.blocked_reason ? ` · ${request.blocked_reason}` : ''}</p>
                    <div className="inline-actions">
                      {request.status === 'pending_approval' && (
                        <>
                          <button type="button" onClick={() => handleApproveMcpExecution(request.request_id)} disabled={mcpBusy}>Approve</button>
                          <button type="button" onClick={() => handleRejectMcpExecution(request.request_id)} disabled={mcpBusy}>Reject</button>
                        </>
                      )}
                      {request.status === 'approved' && (
                        <button type="button" onClick={() => handleRunMcpExecution(request.request_id)} disabled={mcpBusy}>Run (mock)</button>
                      )}
                    </div>
                  </div>
                ))}
                {mcpExecSummary?.safety_summary && (
                  <p className="muted">execution: real={String(mcpExecSummary.safety_summary.real_execution_enabled)} · shell={String(mcpExecSummary.safety_summary.shell_used)} · network={String(mcpExecSummary.safety_summary.network_calls_made)} · writes need approval={String(mcpExecSummary.safety_summary.write_actions_require_approval)}</p>
                )}
                </>
                )}

                {mcpTab === 'audit' && (
                <>
                {/* v46 — MCP Audit & Replay (read-only timeline + dry replay) */}
                <h3>Audit timeline (v46)</h3>
                {mcpAuditSummary && (
                  <p className="muted">events: {mcpAuditSummary.total_events} · blocked: {mcpAuditSummary.blocked_events} · replays: {mcpAuditSummary.replay_count}</p>
                )}
                <div className="inline-actions">
                  <a href={`${API_BASE}/api/mcp/audit/export?format=markdown`} target="_blank" rel="noreferrer"><button type="button">Export .md</button></a>
                  <a href={`${API_BASE}/api/mcp/audit/export?format=json`} target="_blank" rel="noreferrer"><button type="button">Export .json</button></a>
                  <button type="button" onClick={() => refreshMcpPanel()} disabled={mcpBusy}>Refresh</button>
                </div>
                {mcpAudit.slice(0, 12).map((event, index) => (
                  <p className="muted" key={index}>
                    <code>{(event.created_at || '').slice(11, 19)}</code> · {event.source}/{event.event_type}{event.blocked ? ' · blocked' : ''} — {event.message}
                  </p>
                ))}
                <form className="stacked-form" onSubmit={handleReplayMcpRequest}>
                  <h3>Replay a request (read-only)</h3>
                  <input type="text" placeholder="execution request_id" value={mcpReplayId} onChange={(event) => setMcpReplayId(event.target.value)} />
                  <button type="submit" disabled={mcpBusy || !mcpReplayId.trim()}>Replay (dry)</button>
                </form>
                {mcpReplayResult && (
                  <div className="agent-template-card">
                    <strong>Replay · would be allowed: {String(mcpReplayResult.would_be_allowed)}{mcpReplayResult.changed ? ' · CHANGED' : ''}</strong>
                    <p className="muted">{mcpReplayResult.note}</p>
                  </div>
                )}
                </>
                )}

                {mcpTab === 'secrets' && (
                <>
                {/* v47 — Secret Reference Registry (key names + readiness only; never values) */}
                <h3>Secret references (v47)</h3>
                <p className="muted">Catalog of required secret/env keys and readiness. Values are never stored, logged, or shown — only the key name and whether it is set.</p>
                {mcpSecretsSummary && (
                  <p className="muted">refs: {mcpSecretsSummary.total_refs} · set: {mcpSecretsSummary.set_count} · unset: {mcpSecretsSummary.unset_count} · rotation due: {mcpSecretsSummary.rotation_due_count}</p>
                )}
                <form className="stacked-form" onSubmit={handleRegisterMcpSecret}>
                  <input type="text" placeholder="env key name (e.g. GITHUB_TOKEN)" value={mcpSecretKey} onChange={(event) => setMcpSecretKey(event.target.value)} />
                  <button type="submit" disabled={mcpBusy || !mcpSecretKey.trim()}>Register reference</button>
                </form>
                {mcpSecrets.slice(0, 8).map((ref) => (
                  <div className="agent-template-card" key={ref.ref_id}>
                    <strong>{ref.key_name}</strong>
                    <p className="muted">
                      {ref.category} · <span className={`risk-badge ${ref.is_set ? 'risk-low' : 'risk-high'}`}>{ref.is_set ? 'set' : 'not set'}</span>{ref.rotation_due ? ' · ⚠️ rotation due' : ''}{ref.owner ? ` · ${ref.owner}` : ''}
                    </p>
                    <div className="inline-actions">
                      <button type="button" onClick={() => handleRotateMcpSecret(ref.ref_id)} disabled={mcpBusy}>Mark rotated</button>
                    </div>
                  </div>
                ))}
                </>
                )}

                {mcpSummary?.safety_summary && (
                  <>
                    <h3>Safety</h3>
                    <p className="muted">secrets exposed: {String(mcpSummary.safety_summary.secrets_exposed)} · shell: {String(mcpSummary.safety_summary.unrestricted_shell_allowed)} · desktop control: {String(mcpSummary.safety_summary.desktop_control_enabled)} · external send needs approval: {String(mcpSummary.safety_summary.external_send_requires_approval)}</p>
                  </>
                )}
                <p className="muted">Planning-first — connectors prepare and govern tool connections through local records, dry checks, approval boundaries, and audit logs. Execution is mock-by-default (no real MCP/network/shell/device call); tokens are never shown.</p>
              </div>
            )}
          </section>
        )}

        {developerMode && (
          <section data-group="ops" className="sidebar-section">
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
          <section data-group="agent" className="sidebar-section">
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
                      Run diagnostic job
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
          <section data-group="agent" className="sidebar-section">
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
          <section data-group="agent" className="sidebar-section">
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

        <section data-group="agent" className="sidebar-section">
          <button className="analytics-toggle" type="button" onClick={() => setShowAgentBuilder((current) => !current)}>
            <span>
              <Layers3 size={15} />
              Agent Builder / Skill Store
            </span>
            <ChevronDown size={15} />
          </button>
          {showAgentBuilder && (
            <div className="mission-panel">
              <h3>Skill Store 2.0</h3>
              {agentMarketplaceDashboard && (
                <div className="analytics-mini-grid">
                  <div>
                    <span>Packs</span>
                    <strong>{agentMarketplaceDashboard.total_packs || 0}</strong>
                  </div>
                  <div>
                    <span>Installed</span>
                    <strong>{agentMarketplaceDashboard.installed_teams || 0}</strong>
                  </div>
                  <div>
                    <span>Enabled</span>
                    <strong>{agentMarketplaceDashboard.enabled_teams || 0}</strong>
                  </div>
                  <div>
                    <span>Rating</span>
                    <strong>{agentMarketplaceDashboard.average_rating || 0}</strong>
                  </div>
                </div>
              )}
              {agentMarketplacePacks.slice(0, 6).map((pack) => (
                <div className="agent-template-card" key={pack.pack_id}>
                  <strong>{pack.name}</strong>
                  <span>{pack.category} · {pack.permission_profile} · v{pack.version}</span>
                  <p>{pack.description}</p>
                  <small className="muted">
                    {pack.agents?.join(', ')} · installs {pack.install_count || 0} · rating {pack.average_rating || 0}
                  </small>
                  <button
                    type="button"
                    disabled={agentMarketplaceBusyId === pack.pack_id}
                    onClick={() => handleInstallAgentPack(pack.pack_id)}
                  >
                    {agentMarketplaceBusyId === pack.pack_id ? 'Installing...' : 'Install team'}
                  </button>
                </div>
              ))}
              <h3>Installed agent teams</h3>
              {agentMarketplaceTeams.length === 0 && <p className="muted">No installed agent teams yet.</p>}
              {agentMarketplaceTeams.slice(0, 6).map((team) => (
                <div className="agent-template-card" key={team.team_id}>
                  <strong>{team.name}</strong>
                  <span>{team.permission_profile} · v{team.version} · {team.enabled ? 'enabled' : 'disabled'}</span>
                  <p>{team.description}</p>
                  <small className="muted">
                    {(team.agents || []).map((agent) => agent.name || agent.agent_id).join(', ') || 'No agents'} · rating {team.average_rating || 0}
                  </small>
                  <div className="inline-actions">
                    <button type="button" onClick={() => handleRateAgentTeam(team.team_id)}>Rate</button>
                    <button type="button" onClick={() => handleExportAgentTeam(team.team_id)}>Export</button>
                  </div>
                </div>
              ))}
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
                <button type="button" className="sa-upgrade" onClick={() => setDeveloperMode(true)} title="Explore all tools">
                  <Sparkles size={14} /> Upgrade
                </button>
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

        <section className="chat-scroll">
          {messages.length === 0 && !loading && !developerMode && (
            <div className="master-hero">
              <div className="sa-today"><span>Today</span></div>
              <div className="sa-greeting">
                <p className="sa-greet-hi">Hey — great to meet you!</p>
                <p>I'm your <strong>Master Agent</strong> — one AI over everything. I can be your <strong>chief of staff</strong> to run your day, a <strong>research assistant</strong> that digs things up, or an <strong>inbox &amp; ops manager</strong> that keeps you on top of things.</p>
                <p>Or we can just start chatting and figure out the right agent as we go.</p>
                <p>So — what can I take off your plate?</p>
                <div className="sa-msg-actions">
                  <button type="button" onClick={() => { navigator.clipboard?.writeText('Hey — what can I take off your plate?'); }} aria-label="Copy"><Copy size={14} /></button>
                  <button type="button" onClick={() => { setVoiceOutputEnabled(true); speak('Hey, great to meet you. What can I take off your plate?') }} aria-label="Read aloud"><Volume2 size={14} /></button>
                  <span className="sa-msg-time">now</span>
                </div>
              </div>
              <form className="master-hero-bar" onSubmit={masterSubmit}>
                <input
                  type="text"
                  className="master-hero-input"
                  placeholder="Ask anything, or say a command… (mcp: … or /help)"
                  value={masterText}
                  onChange={(event) => setMasterText(event.target.value)}
                  disabled={masterBusy}
                />
                <button
                  type="button"
                  className={`master-hero-mic ${listening ? 'listening' : ''}`}
                  onClick={startMasterVoice}
                  aria-label="Push to talk"
                  title="Push to talk — speak and it routes automatically"
                >
                  <Mic size={18} />
                </button>
                <button
                  type="button"
                  className={`master-hero-tts ${voiceOutputEnabled ? 'on' : ''} ${speaking ? 'speaking' : ''}`}
                  onClick={() => { if (speaking) stopSpeaking(); setVoiceOutputEnabled((v) => !v) }}
                  aria-label="Toggle spoken answers"
                  title={voiceOutputEnabled ? 'Spoken answers ON — tap to mute' : 'Spoken answers OFF — tap to hear answers'}
                >
                  {voiceOutputEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
                </button>
                <button type="submit" className="master-hero-go" disabled={masterBusy || !masterText.trim()}>
                  {masterBusy ? <Activity size={16} /> : 'Ask'}
                </button>
              </form>
              {masterText.startsWith('/') && (
                <div className="master-cli">
                  {SLASH_COMMANDS.filter((c) => c.cmd.startsWith(masterText.split(' ')[0].toLowerCase())).map((c) => (
                    <button key={c.cmd} type="button" className="master-cli-cmd" onClick={() => setMasterText(c.cmd + ' ')}>
                      <strong>{c.cmd}</strong><span>{c.desc}</span>
                    </button>
                  ))}
                </div>
              )}
              {listening && <p className="master-hero-hint listening">Listening… speak your request.</p>}
              {!masterResult && !listening && (
                <div className="master-hero-chips sa-chips">
                  {[
                    { icon: <Flag size={14} />, label: 'Run my day as chief of staff', prompt: 'Act as my chief of staff and plan my day.' },
                    { icon: <Library size={14} />, label: 'Research a topic for me', prompt: 'Be my research assistant and dig up sources on a topic.' },
                    { icon: <MessageSquarePlus size={14} />, label: 'Set up inbox & ops mode', prompt: 'Set up an inbox and ops manager workflow.' },
                    { icon: <Route size={14} />, label: 'Plan a GitHub PR workflow', prompt: 'Plan a GitHub PR workflow.' },
                  ].map((chip) => (
                    <button key={chip.label} type="button" className="master-chip sa-chip" onClick={() => askMaster(chip.prompt, false)} disabled={masterBusy}>
                      <span className="sa-chip-icon">{chip.icon}</span>{chip.label}
                    </button>
                  ))}
                </div>
              )}

              {masterResult && (
                <div className="master-answer">
                  {masterResult.requires_approval && (
                    <div className="master-approval">
                      <Shield size={15} />
                      <span>Approval required before anything runs. {masterResult.approval_reasons?.join(' ')}</span>
                    </div>
                  )}
                  <div className="master-answer-head">
                    <span className="master-badge">{masterResult.intent?.primary_domain || 'Routed'}</span>
                    {typeof masterResult.confidence === 'number' && (
                      <span className={`master-confidence ${masterResult.fallback_used ? 'low' : ''}`}>
                        {masterResult.fallback_used ? 'fallback' : `${Math.round(masterResult.confidence * 100)}% confident`}
                      </span>
                    )}
                    <button type="button" className="master-answer-tts" onClick={() => (speaking ? stopSpeaking() : (setVoiceOutputEnabled(true), speak(masterResult.answer)))}>
                      {speaking ? <><VolumeX size={13} /> Stop</> : <><Volume2 size={13} /> Read aloud</>}
                    </button>
                  </div>
                  {masterResult.route_explanation && (
                    <p className="master-why">Why this route: {masterResult.route_explanation}</p>
                  )}
                  {masterResult.suggested_workflow && (
                    <p className="master-workflow">Suggested next: {masterResult.suggested_workflow}</p>
                  )}
                  <div className="master-answer-body"><MarkdownMessage content={masterResult.answer || '(no answer)'} /></div>

                  {askSources.length > 0 && (
                    <div className="master-block">
                      <h4>Sources</h4>
                      <div className="master-source-list">
                        {askSources.map((s, i) => (
                          <span key={i} className="master-source">{s.label}{s.why ? ` · ${s.why}` : ''}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {mcpSuggestions.length > 0 && (
                    <div className="master-block">
                      <h4>MCP tools</h4>
                      <div className="master-source-list">
                        {mcpSuggestions.map((m) => (
                          <span key={m.slug} className={`master-mcp ${m.keys_ready ? 'ready' : 'missing'}`}>
                            {m.name} · {m.keys_ready ? 'keys ready' : `needs ${m.missing_keys.join(', ')}`}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {askFollowups.length > 0 && (
                    <div className="master-block">
                      <h4>Follow-ups</h4>
                      <div className="master-followups">
                        {askFollowups.map((q, i) => (
                          <button key={i} type="button" className="master-followup" onClick={() => askMaster(q, false)} disabled={masterBusy}>{q}</button>
                        ))}
                      </div>
                    </div>
                  )}
                  <p className="master-disclaimer">{masterResult.disclaimer}</p>
                </div>
              )}
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

        {(askSources.length > 0 || askFollowups.length > 0 || mcpSuggestions.length > 0) && (
          <section className="ask-panel">
            {askSources.length > 0 && (
              <div className="ask-block">
                <span className="ask-block-label">Sources</span>
                <div className="ask-sources">
                  {askSources.map((src, index) => (
                    <span key={index} className="ask-source-chip" title={src.text?.slice(0, 200)}>
                      [{index + 1}] {src.citation}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {mcpSuggestions.length > 0 && (
              <div className="ask-block">
                <span className="ask-block-label">🔌 Tools this task may need</span>
                <div className="ask-sources">
                  {mcpSuggestions.map((s) => (
                    <span key={s.slug} className={`mcp-suggest-chip ${s.keys_ready ? 'ready' : 'needs-key'}`} title={s.recommended_action}>
                      {s.name}
                      {s.missing_keys.length > 0
                        ? ` · needs ${s.missing_keys.join(', ')} ✗`
                        : s.already_enabled ? ' · enabled ✓' : ' · key ready ✓'}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {askFollowups.length > 0 && (
              <div className="ask-block">
                <span className="ask-block-label">Follow-ups</span>
                <div className="ask-followups">
                  {askFollowups.map((q, index) => (
                    <button key={index} type="button" className="ask-followup-chip" onClick={() => submitMessage(q)} disabled={loading}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        <section className={`chat-composer ${developerMode ? '' : 'sa-composer'}`}>
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
            {!developerMode && <span className="sa-mode-label">Automatic</span>}
            {!developerMode && (
              <button
                type="button"
                className={`sa-voice-button ${listening ? 'listening' : ''}`}
                onClick={startMasterVoice}
                aria-label="Voice mode"
                title="Push to talk"
              >
                <Activity size={16} />
              </button>
            )}
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
                      <button className="secondary-button" type="button" disabled={digitalTwinBusy} onClick={handleExportDigitalTwin}>Export</button>
                      <button className="secondary-button" type="button" disabled={digitalTwinBusy} onClick={handleResetDigitalTwin}>Reset</button>
                      <button className="secondary-button danger" type="button" disabled={digitalTwinBusy} onClick={handleDeleteDigitalTwin}>Delete</button>
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
