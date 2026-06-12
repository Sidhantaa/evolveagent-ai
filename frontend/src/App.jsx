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
  MoreHorizontal,
  Paperclip,
  Mic,
  MessageSquarePlus,
  PanelRight,
  Route,
  Send,
  ShieldAlert,
  Sparkles,
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
  getChat,
  getChats,
  getCustomAgents,
  getGoal,
  getGoals,
  getHistory,
  getLearningReport,
  getLinearIssues,
  getLinearLinks,
  getLinearPollStatus,
  getLinearStatus,
  getCodexJobs,
  runCodexForLinearIssue,
  getApprovals,
  submitApprovalDecision,
  getApprovalAudit,
  getProviderStatus,
  getWorkspaceMemory,
  getWorkspaceKnowledge,
  searchWorkspaceKnowledge,
  exportWorkspaceKnowledge,
  getAssistantCommands,
  runAssistantCommand,
  pinWorkspaceMemory,
  getWorkspaces,
  rejectPromptVersion,
  renameChat,
  rollbackPromptVersion,
  runGoalTask,
  runLinearIssue,
  runLinearPollOnce,
  runWorkflow,
  selectLinearIssue,
  sendFeedback,
  syncLinearIssue,
  updateWorkspace,
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
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [selectedRunId, setSelectedRunId] = useState(null)
  const [chats, setChats] = useState([])
  const [history, setHistory] = useState([])
  const [providerStatus, setProviderStatus] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [learningReport, setLearningReport] = useState(null)
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
  const [selectedCommand, setSelectedCommand] = useState('help')
  const [commandInput, setCommandInput] = useState('')
  const [commandResult, setCommandResult] = useState(null)
  const composerRef = useRef(null)
  const [memorySearch, setMemorySearch] = useState('')
  const [memoryType, setMemoryType] = useState('')
  const [linearStatus, setLinearStatus] = useState(null)
  const [linearIssues, setLinearIssues] = useState([])
  const [linearLinks, setLinearLinks] = useState([])
  const [linearPollStatus, setLinearPollStatus] = useState(null)
  const [codexJobs, setCodexJobs] = useState([])
  const [showLinearPanel, setShowLinearPanel] = useState(false)
  const [linearBusyId, setLinearBusyId] = useState('')

  useEffect(() => {
    refreshWorkspaces()
    refreshProviderStatus()
    refreshLinearStatus()
    refreshAssistantCommands()
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
    refreshMissionControl(workspaceId)
    refreshCustomAgents(workspaceId)
    refreshWorkspaceMemory(workspaceId)
    refreshKnowledge(workspaceId)
    refreshLinearData(workspaceId)
  }, [workspaceId])

  useEffect(() => {
    if (!workspaceId || !developerMode) return
    refreshApprovals(workspaceId)
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
  }, [memorySearch, memoryType, workspaceId])

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
  }

  async function refreshAssistantCommands() {
    const commands = await getAssistantCommands()
    setAssistantCommands(commands)
    if (commands.length > 0 && !commands.find((command) => command.name === selectedCommand)) {
      setSelectedCommand(commands[0].name)
    }
  }

  async function refreshAnalytics(nextWorkspaceId = workspaceId) {
    setAnalytics(await getAnalytics(nextWorkspaceId))
  }

  async function refreshLearningReport(nextWorkspaceId = workspaceId) {
    setLearningReport(await getLearningReport(nextWorkspaceId))
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

  async function refreshCustomAgents(nextWorkspaceId = workspaceId) {
    setCustomAgents(await getCustomAgents(nextWorkspaceId))
    setAgentTemplates(await getAgentTemplates())
  }

  async function refreshLinearStatus() {
    setLinearStatus(await getLinearStatus())
  }

  async function refreshLinearData(nextWorkspaceId = workspaceId) {
    const status = await getLinearStatus()
    setLinearStatus(status)
    setLinearLinks(await getLinearLinks(nextWorkspaceId))
    setLinearPollStatus(await getLinearPollStatus())
    try {
      setCodexJobs(await getCodexJobs())
    } catch {
      setCodexJobs([])
    }
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
    setWorkspaceMemory(
      await getWorkspaceMemory(nextWorkspaceId, {
        q: memorySearch,
        memory_type: memoryType,
      }),
    )
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
    } catch (err) {
      setError(err.message)
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

  const modeLabel = providerStatus ? `${providerStatus.llm_mode} mode` : 'checking'
  const providerList = providerStatus?.available_providers?.join(', ') || 'none'
  const realProvidersAvailable = (providerStatus?.available_providers || []).filter((provider) => provider !== 'mock')
  const realModeWithoutRealProvider = providerStatus?.llm_mode === 'real' && realProvidersAvailable.length === 0
  const previewText = (text, limit = 360) => {
    const compact = String(text || '').replace(/\s+/g, ' ').trim()
    if (compact.length <= limit) return compact
    return `${compact.slice(0, limit).trim()}...`
  }

  return (
    <main className={`app-shell chat-shell ${developerMode ? 'developer-mode' : 'simple-mode'}`}>
      <aside className="sidebar">
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
              </div>
              <button className="secondary-button full-width" type="button" onClick={handleAddMemory}>
                Add memory
              </button>
              {workspaceMemory.length === 0 && <p className="muted">No workspace memory yet.</p>}
              {workspaceMemory.slice(0, 8).map((memory) => (
                <div className="memory-card" key={memory.memory_id}>
                  <strong>{memory.title}</strong>
                  <span>
                    {formatType(memory.type)} · {memory.importance}
                    {memory.pinned ? ' · pinned' : ''}
                    {memory.usage_count ? ` · used ${memory.usage_count}` : ''}
                  </span>
                  <p>{previewText(memory.content, 150)}</p>
                  <div className="chat-row-actions">
                    <button type="button" onClick={() => handleToggleMemoryPin(memory)}>
                      {memory.pinned ? 'Unpin' : 'Pin'}
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
              <span>Mode</span>
              <strong>{modeLabel}</strong>
            </div>
            <div>
              <span>Available</span>
              <strong>{providerList}</strong>
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
          {realModeWithoutRealProvider && (
            <p className="provider-warning">Real mode is enabled, but no real provider key is configured. Mock fallback will be used.</p>
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
                <select
                  className="jarvis-workspace-select"
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
                <p>Voice-controlled multi-agent operating system</p>
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
                  <span className="jarvis-option-subtitle">Give EvolveAgent a voice command.</span>
                </button>
                <button type="button" className="jarvis-command-option type" onClick={focusComposer}>
                  <span className="jarvis-option-icon">
                    <Keyboard size={28} />
                  </span>
                  <strong>Type</strong>
                  <span className="jarvis-option-subtitle">Send a text command.</span>
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
                      <img src={assetUrl(imageResult.image_url)} alt="Generated mock preview" />
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
                          <span>{message.result.master_plan.confidence}% confidence</span>
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
                <img className="inspector-image" src={assetUrl(selectedRun.image_result.image_url)} alt="Generated mock preview" />
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
