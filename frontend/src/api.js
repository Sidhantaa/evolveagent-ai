export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export async function runWorkflow(payload) {
  let response
  try {
    response = await fetch(`${API_BASE}/api/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new Error(`Backend is not reachable at ${API_BASE}. Start the FastAPI server, then try again.`)
  }

  if (!response.ok) {
    let message = `Workflow request failed with status ${response.status}`
    try {
      const errorBody = await response.json()
      const detail = Array.isArray(errorBody.detail)
        ? errorBody.detail.map((item) => item.msg).join(', ')
        : errorBody.detail
      if (detail) message = detail
    } catch {
      // Keep the status-based message if the backend did not return JSON.
    }
    throw new Error(message)
  }

  return response.json()
}

function query(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value)
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

export async function uploadFiles(files, sessionId, workspaceId) {
  const formData = new FormData()
  Array.from(files).forEach((file) => formData.append('files', file))
  if (sessionId) formData.append('session_id', sessionId)
  if (workspaceId) formData.append('workspace_id', workspaceId)

  let response
  try {
    response = await fetch(`${API_BASE}/api/files/upload`, {
      method: 'POST',
      body: formData,
    })
  } catch {
    throw new Error(`Backend is not reachable at ${API_BASE}. Start the FastAPI server, then try again.`)
  }

  if (!response.ok) {
    throw new Error(`File upload failed with status ${response.status}`)
  }

  return response.json()
}

export async function uploadRecordings(files, sessionId, workspaceId) {
  const formData = new FormData()
  Array.from(files).forEach((file) => formData.append('files', file))
  if (sessionId) formData.append('session_id', sessionId)
  if (workspaceId) formData.append('workspace_id', workspaceId)

  let response
  try {
    response = await fetch(`${API_BASE}/api/recordings/upload`, {
      method: 'POST',
      body: formData,
    })
  } catch {
    throw new Error(`Backend is not reachable at ${API_BASE}. Start the FastAPI server, then try again.`)
  }

  if (!response.ok) {
    throw new Error(`Recording upload failed with status ${response.status}`)
  }

  return response.json()
}

export async function getHistory() {
  try {
    const response = await fetch(`${API_BASE}/api/history`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getProviderStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/providers/status`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function runProviderSmokeTest(payload = {}) {
  const response = await fetch(`${API_BASE}/api/providers/smoke-test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Provider check failed with status ${response.status}`)
  }
  return body
}

export async function getImageProviderStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/images/status`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function runImageSmokeTest(payload = {}) {
  const response = await fetch(`${API_BASE}/api/images/smoke-test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Image provider check failed with status ${response.status}`)
  }
  return body
}

export async function getTranscriptionProviderStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/transcription/status`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function runTranscriptionSmokeTest(payload = {}) {
  const response = await fetch(`${API_BASE}/api/transcription/smoke-test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Transcription provider check failed with status ${response.status}`)
  }
  return body
}

export async function getRealApiSummary() {
  try {
    const response = await fetch(`${API_BASE}/api/real-api/summary`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getRealApiLiveWarning(capability) {
  const response = await fetch(`${API_BASE}/api/real-api/live-warning/${capability}`)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Real API warning failed with status ${response.status}`)
  }
  return body
}

export async function decodeRealApiError(error) {
  const response = await fetch(`${API_BASE}/api/real-api/decode-error`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ error }),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Real API error decode failed with status ${response.status}`)
  }
  return body
}

export async function getAnalytics(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/analytics${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function sendFeedback(payload) {
  const response = await fetch(`${API_BASE}/api/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Feedback failed with status ${response.status}`)
  }
  return response.json()
}

export async function getChats(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/chats${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getChat(sessionId) {
  const response = await fetch(`${API_BASE}/api/chats/${sessionId}`)
  if (!response.ok) {
    throw new Error(`Chat load failed with status ${response.status}`)
  }
  return response.json()
}

export async function createChat(title = 'New Chat', workspaceId = null) {
  const response = await fetch(`${API_BASE}/api/chats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, workspace_id: workspaceId }),
  })
  if (!response.ok) {
    throw new Error(`Chat creation failed with status ${response.status}`)
  }
  return response.json()
}

export async function renameChat(sessionId, title) {
  const response = await fetch(`${API_BASE}/api/chats/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!response.ok) {
    throw new Error(`Chat rename failed with status ${response.status}`)
  }
  return response.json()
}

export async function deleteChat(sessionId) {
  const response = await fetch(`${API_BASE}/api/chats/${sessionId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`Chat delete failed with status ${response.status}`)
  }
  return response.json()
}

export async function deleteMessage(sessionId, messageId) {
  const response = await fetch(`${API_BASE}/api/chats/${sessionId}/messages/${messageId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`Message delete failed with status ${response.status}`)
  }
  return response.json()
}

export async function applyAutomation(payload) {
  const response = await fetch(`${API_BASE}/api/automation/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Automation apply failed with status ${response.status}`)
  }
  return response.json()
}

export async function getLearningReport(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/learning/report${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function approvePromptVersion(payload) {
  const response = await fetch(`${API_BASE}/api/learning/approve-prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Prompt approval failed with status ${response.status}`)
  return response.json()
}

export async function rejectPromptVersion(payload) {
  const response = await fetch(`${API_BASE}/api/learning/reject-prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Prompt rejection failed with status ${response.status}`)
  return response.json()
}

export async function rollbackPromptVersion(payload) {
  const response = await fetch(`${API_BASE}/api/learning/rollback-prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Prompt rollback failed with status ${response.status}`)
  return response.json()
}

export async function getGoals(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/goals${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getGoal(goalId) {
  const response = await fetch(`${API_BASE}/api/goals/${goalId}`)
  if (!response.ok) throw new Error(`Goal load failed with status ${response.status}`)
  return response.json()
}

export async function createGoal(payload) {
  const response = await fetch(`${API_BASE}/api/goals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Goal creation failed with status ${response.status}`)
  return response.json()
}

export async function updateGoal(goalId, payload) {
  const response = await fetch(`${API_BASE}/api/goals/${goalId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Goal update failed with status ${response.status}`)
  return response.json()
}

export async function addGoalTask(goalId, payload) {
  const response = await fetch(`${API_BASE}/api/goals/${goalId}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Goal task creation failed with status ${response.status}`)
  return response.json()
}

export async function updateGoalTask(goalId, taskId, payload) {
  const response = await fetch(`${API_BASE}/api/goals/${goalId}/tasks/${taskId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Goal task update failed with status ${response.status}`)
  return response.json()
}

export async function runGoalTask(goalId, taskId) {
  const response = await fetch(`${API_BASE}/api/goals/${goalId}/tasks/${taskId}/run`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Goal task run failed with status ${response.status}`)
  return response.json()
}

export async function getAgentTemplates() {
  try {
    const response = await fetch(`${API_BASE}/api/agents/templates`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getCustomAgents(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/agents/custom${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function createCustomAgent(payload) {
  const response = await fetch(`${API_BASE}/api/agents/custom`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Custom agent creation failed with status ${response.status}`)
  return response.json()
}

export async function updateCustomAgent(agentId, payload) {
  const response = await fetch(`${API_BASE}/api/agents/custom/${agentId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Custom agent update failed with status ${response.status}`)
  return response.json()
}

export async function deleteCustomAgent(agentId) {
  const response = await fetch(`${API_BASE}/api/agents/custom/${agentId}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error(`Custom agent delete failed with status ${response.status}`)
  return response.json()
}

export async function getWorkspaces() {
  try {
    const response = await fetch(`${API_BASE}/api/workspaces`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function createWorkspace(payload) {
  const response = await fetch(`${API_BASE}/api/workspaces`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Workspace creation failed with status ${response.status}`)
  return response.json()
}

export async function updateWorkspace(workspaceId, payload) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Workspace update failed with status ${response.status}`)
  return response.json()
}

export async function deleteWorkspace(workspaceId) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error(`Workspace archive failed with status ${response.status}`)
  return response.json()
}

export async function getWorkspaceMemory(workspaceId, params = {}) {
  if (!workspaceId) return []
  try {
    const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory${query(params)}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getWorkspaceMemoryIntelligence(workspaceId) {
  if (!workspaceId) return null
  try {
    const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/intelligence`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function rescoreWorkspaceMemory(workspaceId) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/re-score`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Memory re-score failed with status ${response.status}`)
  return response.json()
}

export async function maintainWorkspaceMemoryTiers(workspaceId) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/tiers/maintain`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Memory tier maintenance failed with status ${response.status}`)
  return response.json()
}

export async function rebuildWorkspaceMemoryIndex(workspaceId) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/index/rebuild`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Memory index rebuild failed with status ${response.status}`)
  return response.json()
}

export async function consolidateWorkspaceMemory(workspaceId, approved = false) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/consolidate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved }),
  })
  if (!response.ok) throw new Error(`Memory consolidation failed with status ${response.status}`)
  return response.json()
}

export async function createMemoryConsolidationJob(workspaceId, apply = false) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/consolidation-jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ apply }),
  })
  if (!response.ok) throw new Error(`Memory consolidation job failed with status ${response.status}`)
  return response.json()
}

export async function getMemoryConsolidationJobs(workspaceId) {
  if (!workspaceId) return []
  try {
    const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/consolidation-jobs`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function applyMemoryConsolidationJob(workspaceId, jobId) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/consolidation-jobs/${jobId}/apply`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Memory consolidation job apply failed with status ${response.status}`)
  return response.json()
}

export async function createWorkspaceMemory(workspaceId, payload) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Memory creation failed with status ${response.status}`)
  return response.json()
}

export async function updateWorkspaceMemory(workspaceId, memoryId, payload) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/${memoryId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Memory update failed with status ${response.status}`)
  return response.json()
}

export async function pinWorkspaceMemory(workspaceId, memoryId, pinned = true) {
  const action = pinned ? 'pin' : 'unpin'
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/${memoryId}/${action}`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Memory ${action} failed with status ${response.status}`)
  return response.json()
}

export async function archiveWorkspaceMemory(workspaceId, memoryId, archived = true) {
  const action = archived ? 'archive' : 'restore'
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/${memoryId}/${action}`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Memory ${action} failed with status ${response.status}`)
  return response.json()
}

export async function deleteWorkspaceMemory(workspaceId, memoryId) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/memory/${memoryId}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error(`Memory delete failed with status ${response.status}`)
  return response.json()
}

export async function getWorkspaceKnowledge(workspaceId) {
  if (!workspaceId) return null
  try {
    const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/knowledge`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function searchWorkspaceKnowledge(workspaceId, params = {}) {
  if (!workspaceId) return { results: [], related_links: [] }
  try {
    const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/knowledge/search${query(params)}`)
    if (!response.ok) return { results: [], related_links: [] }
    return response.json()
  } catch {
    return { results: [], related_links: [] }
  }
}

export async function exportWorkspaceKnowledge(workspaceId, format = 'markdown') {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/knowledge/export${query({ format })}`)
  if (!response.ok) throw new Error(`Knowledge export failed with status ${response.status}`)
  if (format === 'json') return response.json()
  return response.text()
}

export async function createKnowledgeLink(workspaceId, payload) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/knowledge/links`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Knowledge link creation failed with status ${response.status}`)
  return response.json()
}

export async function deleteKnowledgeLink(workspaceId, linkId) {
  const response = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/knowledge/links/${linkId}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error(`Knowledge link delete failed with status ${response.status}`)
  return response.json()
}

export async function getResearchSessions(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/research/sessions${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function createResearchSession(payload) {
  const response = await fetch(`${API_BASE}/api/research/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Research session failed with status ${response.status}`)
  return response.json()
}

export async function approveResearchSession(researchId) {
  const response = await fetch(`${API_BASE}/api/research/sessions/${researchId}/approve`, { method: 'POST' })
  if (!response.ok) throw new Error(`Research approval failed with status ${response.status}`)
  return response.json()
}

export async function rejectResearchSession(researchId) {
  const response = await fetch(`${API_BASE}/api/research/sessions/${researchId}/reject`, { method: 'POST' })
  if (!response.ok) throw new Error(`Research rejection failed with status ${response.status}`)
  return response.json()
}

export async function addResearchSource(researchId, payload) {
  const response = await fetch(`${API_BASE}/api/research/sessions/${researchId}/sources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Research source failed with status ${response.status}`)
  return response.json()
}

export async function addResearchCitation(researchId, payload) {
  const response = await fetch(`${API_BASE}/api/research/sessions/${researchId}/citations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Research citation failed with status ${response.status}`)
  return response.json()
}

export async function getResearchReport(researchId) {
  const response = await fetch(`${API_BASE}/api/research/sessions/${researchId}/report`)
  if (!response.ok) throw new Error(`Research report failed with status ${response.status}`)
  return response.json()
}

export async function getAssistantCommands() {
  try {
    const response = await fetch(`${API_BASE}/api/assistant/commands`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function runAssistantCommand(commandName, payload) {
  const response = await fetch(`${API_BASE}/api/assistant/commands/${commandName}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Assistant command failed with status ${response.status}`)
  return response.json()
}

export async function getQualityStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/quality/status`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function runQualityChecks(payload = {}) {
  const response = await fetch(`${API_BASE}/api/quality/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Quality run failed with status ${response.status}`)
  return response.json()
}

export async function suggestQualityTests(changedFiles = []) {
  const response = await fetch(`${API_BASE}/api/quality/suggest-tests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ changed_files: changedFiles }),
  })
  if (!response.ok) throw new Error(`Test suggestion request failed with status ${response.status}`)
  return response.json()
}

export async function getAppBuilderTemplates() {
  try {
    const response = await fetch(`${API_BASE}/api/app-builder/templates`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function createAppBuilderPlan(payload) {
  const response = await fetch(`${API_BASE}/api/app-builder/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`App Builder plan failed with status ${response.status}`)
  return response.json()
}

export async function scaffoldAppBuilderPlan(payload) {
  const response = await fetch(`${API_BASE}/api/app-builder/scaffold`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`App Builder scaffold failed with status ${response.status}`)
  return response.json()
}

export async function getDebateSummary(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/debate/summary${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function createDebateSession(payload) {
  const response = await fetch(`${API_BASE}/api/debate/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Debate session failed with status ${response.status}`)
  return response.json()
}

export async function createSimulationRun(payload) {
  const response = await fetch(`${API_BASE}/api/simulations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Simulation run failed with status ${response.status}`)
  return response.json()
}

export async function getLinearStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/linear/status`)
    if (!response.ok) return { configured: false }
    return response.json()
  } catch {
    return { configured: false }
  }
}

export async function getLinearIssues() {
  const response = await fetch(`${API_BASE}/api/linear/issues`)
  if (!response.ok) throw new Error(`Linear issues request failed with status ${response.status}`)
  return response.json()
}

export async function getLinearLinks(workspaceId) {
  const response = await fetch(`${API_BASE}/api/linear/links${query({ workspace_id: workspaceId })}`)
  if (!response.ok) return []
  return response.json()
}

export async function syncLinearIssue(issueId, workspaceId) {
  const response = await fetch(`${API_BASE}/api/linear/issues/${issueId}/sync${query({ workspace_id: workspaceId })}`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Linear sync failed with status ${response.status}`)
  return response.json()
}

export async function selectLinearIssue(issueId, workspaceId) {
  const response = await fetch(`${API_BASE}/api/linear/issues/${issueId}/select${query({ workspace_id: workspaceId })}`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Linear select failed with status ${response.status}`)
  return response.json()
}

export async function runLinearIssue(issueId, workspaceId) {
  const response = await fetch(`${API_BASE}/api/linear/issues/${issueId}/run${query({ workspace_id: workspaceId })}`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Linear run failed with status ${response.status}`)
  return response.json()
}

export async function getLinearPollStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/linear/poll/status`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function runLinearPollOnce() {
  const response = await fetch(`${API_BASE}/api/linear/poll/run-once`, { method: 'POST' })
  if (!response.ok) throw new Error(`Linear poll failed with status ${response.status}`)
  return response.json()
}

export async function completeLinearIssue(issueId) {
  const response = await fetch(`${API_BASE}/api/linear/issues/${issueId}/complete`, { method: 'POST' })
  if (!response.ok) throw new Error(`Linear complete failed with status ${response.status}`)
  return response.json()
}

export async function getLinearCursorHandoff(issueId) {
  const response = await fetch(`${API_BASE}/api/linear/issues/${issueId}/cursor-handoff`)
  if (!response.ok) throw new Error(`Cursor handoff failed with status ${response.status}`)
  return response.json()
}

export async function verifyLinearCursorWork(issueId, payload = {}) {
  const response = await fetch(`${API_BASE}/api/linear/issues/${issueId}/cursor-verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Cursor verify failed with status ${response.status}`)
  return response.json()
}

export async function runCodexForLinearIssue(issueId) {
  const response = await fetch(`${API_BASE}/api/linear/issues/${issueId}/codex-run`, { method: 'POST' })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Codex run failed with status ${response.status}`)
  }
  return body
}

export async function getCodexJobs() {
  try {
    const response = await fetch(`${API_BASE}/api/codex/jobs`)
    if (!response.ok) return { available: false, items: [] }
    const data = await response.json()
    const items = Array.isArray(data) ? data : data.jobs || data.items || []
    return { available: true, items }
  } catch {
    return { available: false, items: [] }
  }
}

export async function getCodexJob(jobId) {
  const response = await fetch(`${API_BASE}/api/codex/jobs/${jobId}`)
  if (!response.ok) throw new Error(`Codex job failed with status ${response.status}`)
  return response.json()
}

export async function getApprovals(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/approvals${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return { available: false, items: [] }
    const data = await response.json()
    const items = Array.isArray(data) ? data : data.approvals || data.items || []
    return { available: true, items }
  } catch {
    return { available: false, items: [] }
  }
}

export async function getApproval(approvalId) {
  try {
    const response = await fetch(`${API_BASE}/api/approvals/${approvalId}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function submitApprovalDecision(approvalId, payload) {
  const response = await fetch(`${API_BASE}/api/approvals/${approvalId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Approval decision failed with status ${response.status}`)
  }
  return body
}

export async function getApprovalAudit(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/approvals/audit${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return { available: false, items: [] }
    const data = await response.json()
    const items = Array.isArray(data) ? data : data.audit || data.items || []
    return { available: true, items }
  } catch {
    return { available: false, items: [] }
  }
}

export async function getAgentJobs(workspaceId, status) {
  try {
    const response = await fetch(`${API_BASE}/api/agent-jobs${query({ workspace_id: workspaceId, status })}`)
    if (!response.ok) return { available: false, items: [] }
    const data = await response.json()
    const items = Array.isArray(data) ? data : data.jobs || data.items || []
    return { available: true, items }
  } catch {
    return { available: false, items: [] }
  }
}

export async function getAgentJob(jobId) {
  try {
    const response = await fetch(`${API_BASE}/api/agent-jobs/${jobId}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getAgentJobHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/agent-jobs/health`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function createAgentJob(payload) {
  const response = await fetch(`${API_BASE}/api/agent-jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Create agent job failed with status ${response.status}`)
  }
  return body
}

export async function startNextAgentJob() {
  const response = await fetch(`${API_BASE}/api/agent-jobs/start-next`, { method: 'POST' })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Start next job failed with status ${response.status}`)
  }
  return body
}

export async function pauseAgentJob(jobId, reason) {
  const response = await fetch(`${API_BASE}/api/agent-jobs/${jobId}/pause`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Pause job failed with status ${response.status}`)
  }
  return body
}

export async function resumeAgentJob(jobId, reason) {
  const response = await fetch(`${API_BASE}/api/agent-jobs/${jobId}/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Resume job failed with status ${response.status}`)
  }
  return body
}

export async function cancelAgentJob(jobId, reason) {
  const response = await fetch(`${API_BASE}/api/agent-jobs/${jobId}/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Cancel job failed with status ${response.status}`)
  }
  return body
}

export async function heartbeatAgentJob(jobId) {
  const response = await fetch(`${API_BASE}/api/agent-jobs/${jobId}/heartbeat`, { method: 'POST' })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Heartbeat failed with status ${response.status}`)
  }
  return body
}

export async function getSystemPrompts() {
  try {
    const response = await fetch(`${API_BASE}/api/system-prompts`)
    if (!response.ok) return { available: false, items: [] }
    const data = await response.json()
    const items = Array.isArray(data) ? data : data.prompts || data.items || []
    return { available: true, items }
  } catch {
    return { available: false, items: [] }
  }
}

export async function getToolHistory(workspaceId, limit = 20) {
  try {
    const response = await fetch(`${API_BASE}/api/tools/history${query({ workspace_id: workspaceId, limit })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getToolSummary(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/tools/summary${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getSystemPrompt(agentName) {
  const response = await fetch(`${API_BASE}/api/system-prompts/${encodeURIComponent(agentName)}`)
  if (!response.ok) throw new Error(`System prompt failed with status ${response.status}`)
  return response.json()
}

export async function upsertSystemPrompt(payload) {
  const response = await fetch(`${API_BASE}/api/system-prompts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Update system prompt failed with status ${response.status}`)
  }
  return body
}
