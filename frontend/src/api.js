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

export async function getEvaluationDashboard(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/evaluation/dashboard${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getEvaluationBenchmarks(taskType) {
  try {
    const response = await fetch(`${API_BASE}/api/evaluation/benchmarks${query({ task_type: taskType })}`)
    if (!response.ok) return { benchmarks: [] }
    return response.json()
  } catch {
    return { benchmarks: [] }
  }
}

export async function createEvaluationRun(payload) {
  const response = await fetch(`${API_BASE}/api/evaluation/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Evaluation run failed with status ${response.status}`)
  }
  return body
}

export async function createEvaluationABTest(payload) {
  const response = await fetch(`${API_BASE}/api/evaluation/ab-tests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `A/B evaluation failed with status ${response.status}`)
  }
  return body
}

export async function exportEvaluationResults(workspaceId, format = 'json') {
  const response = await fetch(`${API_BASE}/api/evaluation/export${query({ workspace_id: workspaceId, format })}`)
  if (!response.ok) throw new Error(`Evaluation export failed with status ${response.status}`)
  return response.text()
}

export async function getProjectManagerDashboard(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/project-manager/dashboard${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getProjectManagerRisks(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/project-manager/risks${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return { risks: [] }
    return response.json()
  } catch {
    return { risks: [] }
  }
}

export async function createProjectManagerRisk(payload) {
  const response = await fetch(`${API_BASE}/api/project-manager/risks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Risk create failed with status ${response.status}`)
  }
  return body
}

export async function generateProjectManagerReport(workspaceId) {
  const response = await fetch(`${API_BASE}/api/project-manager/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workspace_id: workspaceId }),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Report generation failed with status ${response.status}`)
  }
  return body
}

export async function getPortfolioDashboard() {
  try {
    const response = await fetch(`${API_BASE}/api/portfolio/dashboard`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getPortfolioHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/portfolio/health`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getPortfolioAnalytics() {
  try {
    const response = await fetch(`${API_BASE}/api/portfolio/analytics`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function generatePortfolioReport() {
  const response = await fetch(`${API_BASE}/api/portfolio/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Portfolio report failed with status ${response.status}`)
  }
  return body
}

export async function exportPortfolio(format = 'json') {
  const response = await fetch(`${API_BASE}/api/portfolio/export${query({ format })}`)
  if (!response.ok) throw new Error(`Portfolio export failed with status ${response.status}`)
  return response.text()
}

export async function getComplianceSummary(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/compliance/summary${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getComplianceAuditLog(workspaceId, limit = 25) {
  try {
    const response = await fetch(`${API_BASE}/api/compliance/audit-log${query({ workspace_id: workspaceId, limit })}`)
    if (!response.ok) return { events: [] }
    return response.json()
  } catch {
    return { events: [] }
  }
}

export async function getComplianceRetentionPolicies(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/compliance/retention-policies${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function scanCompliancePii(text, redact = true) {
  const response = await fetch(`${API_BASE}/api/compliance/pii-scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, redact }),
  })
  if (!response.ok) throw new Error(`PII scan failed with status ${response.status}`)
  return response.json()
}

export async function exportComplianceReport(workspaceId, format = 'markdown') {
  const response = await fetch(`${API_BASE}/api/compliance/export${query({ workspace_id: workspaceId, format })}`)
  if (!response.ok) throw new Error(`Compliance export failed with status ${response.status}`)
  return response.text()
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

export async function getDigitalTwinProfile(workspaceId) {
  const response = await fetch(`${API_BASE}/api/digital-twin/profile${query({ workspace_id: workspaceId })}`)
  if (!response.ok) throw new Error(`Digital Twin profile failed with status ${response.status}`)
  return response.json()
}

export async function refreshDigitalTwinProfile(workspaceId) {
  const response = await fetch(`${API_BASE}/api/digital-twin/profile/refresh${query({ workspace_id: workspaceId })}`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Digital Twin refresh failed with status ${response.status}`)
  return response.json()
}

export async function updateDigitalTwinProfile(payload) {
  const response = await fetch(`${API_BASE}/api/digital-twin/profile`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Digital Twin update failed with status ${response.status}`)
  return response.json()
}

export async function exportDigitalTwinProfile(workspaceId) {
  const response = await fetch(`${API_BASE}/api/digital-twin/profile/export${query({ workspace_id: workspaceId })}`)
  if (!response.ok) throw new Error(`Digital Twin export failed with status ${response.status}`)
  return response.json()
}

export async function resetDigitalTwinProfile(workspaceId) {
  const response = await fetch(`${API_BASE}/api/digital-twin/profile/reset${query({ workspace_id: workspaceId })}`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error(`Digital Twin reset failed with status ${response.status}`)
  return response.json()
}

export async function deleteDigitalTwinProfile(workspaceId) {
  const response = await fetch(`${API_BASE}/api/digital-twin/profile${query({ workspace_id: workspaceId })}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error(`Digital Twin delete failed with status ${response.status}`)
  return response.json()
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

export async function runSessionControlledSearch(researchId, payload) {
  const response = await fetch(`${API_BASE}/api/research/sessions/${researchId}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Search failed with status ${response.status}`)
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

export async function getSlackStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/integrations/slack/status`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getSlackNotifications(limit = 20) {
  try {
    const response = await fetch(`${API_BASE}/api/integrations/slack/notifications${query({ limit })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function sendSlackTest(payload = {}) {
  const response = await fetch(`${API_BASE}/api/integrations/slack/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Slack test failed with status ${response.status}`)
  }
  return body
}

export async function getNotionStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/integrations/notion/status`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getNotionExports(limit = 20) {
  try {
    const response = await fetch(`${API_BASE}/api/integrations/notion/exports${query({ limit })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function sendNotionExport(payload) {
  const response = await fetch(`${API_BASE}/api/integrations/notion/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Notion export failed with status ${response.status}`)
  }
  return body
}

export async function getAutopilotSettings() {
  try {
    const response = await fetch(`${API_BASE}/api/autopilot/settings`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function updateAutopilotSettings(payload) {
  const response = await fetch(`${API_BASE}/api/autopilot/settings`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Autopilot settings update failed with status ${response.status}`)
  }
  return body
}

export async function getAutopilotRuns(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/autopilot/runs${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getAutopilotActions(workspaceId, limit) {
  try {
    const response = await fetch(`${API_BASE}/api/autopilot/actions${query({ workspace_id: workspaceId, limit })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getAutopilotCheckpoints({ workspaceId, status } = {}) {
  try {
    const response = await fetch(
      `${API_BASE}/api/autopilot/checkpoints${query({ workspace_id: workspaceId, status })}`,
    )
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function decideAutopilotCheckpoint(checkpointId, decision, comment) {
  const response = await fetch(`${API_BASE}/api/autopilot/checkpoints/${checkpointId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, comment }),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Checkpoint decision failed with status ${response.status}`)
  }
  return body
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

export async function getOsSummary() {
  try {
    const response = await fetch(`${API_BASE}/api/os/summary`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getOsInstaller() {
  try {
    const response = await fetch(`${API_BASE}/api/os/installer`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getOsSla() {
  try {
    const response = await fetch(`${API_BASE}/api/os/sla`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getOsScheduler() {
  try {
    const response = await fetch(`${API_BASE}/api/os/scheduler`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getAgentMarketplaceDashboard(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/agent-marketplace/dashboard${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getAgentMarketplacePacks() {
  try {
    const response = await fetch(`${API_BASE}/api/agent-marketplace/packs`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function getAgentMarketplaceTeams(workspaceId) {
  try {
    const response = await fetch(`${API_BASE}/api/agent-marketplace/teams${query({ workspace_id: workspaceId })}`)
    if (!response.ok) return []
    return response.json()
  } catch {
    return []
  }
}

export async function installAgentMarketplacePack(packId, workspaceId) {
  const response = await fetch(`${API_BASE}/api/agent-marketplace/packs/${packId}/install`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workspace_id: workspaceId }),
  })
  if (!response.ok) throw new Error(`Skill pack install failed with status ${response.status}`)
  return response.json()
}

export async function rateAgentMarketplaceTeam(teamId, rating, review = '', workspaceId = null) {
  const response = await fetch(`${API_BASE}/api/agent-marketplace/teams/${teamId}/rate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rating, review, workspace_id: workspaceId }),
  })
  if (!response.ok) throw new Error(`Agent team rating failed with status ${response.status}`)
  return response.json()
}

export async function exportAgentMarketplaceTeam(teamId) {
  const response = await fetch(`${API_BASE}/api/agent-marketplace/teams/${teamId}/export`)
  if (!response.ok) throw new Error(`Agent team export failed with status ${response.status}`)
  return response.json()
}

export async function getDepartments() {
  try {
    const response = await fetch(`${API_BASE}/api/departments?include_archived=true`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getDepartmentRuns() {
  try {
    const response = await fetch(`${API_BASE}/api/departments/runs`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function getDepartmentCollaborations() {
  try {
    const response = await fetch(`${API_BASE}/api/departments/collaborations`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function seedDepartmentTemplates() {
  try {
    const response = await fetch(`${API_BASE}/api/departments/templates/seed`, { method: 'POST' })
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export async function createDepartment(payload) {
  const response = await fetch(`${API_BASE}/api/departments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error('Failed to create department')
  return response.json()
}

export async function createDepartmentRun(departmentId, task) {
  const response = await fetch(`${API_BASE}/api/departments/${departmentId}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task }),
  })
  if (!response.ok) throw new Error('Failed to plan department run')
  return response.json()
}

export async function createDepartmentCollaboration(payload) {
  const response = await fetch(`${API_BASE}/api/departments/collaborations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error('Failed to plan collaboration')
  return response.json()
}

async function getJson(path) {
  try {
    const response = await fetch(`${API_BASE}${path}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Request failed (${response.status})`)
  return response.json()
}

async function patchJson(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`Request failed (${response.status})`)
  return response.json()
}

export function getBusinessDashboard(workspaceId) {
  return getJson(`/api/business/dashboard${query({ workspace_id: workspaceId })}`)
}
export function getBusinessLeads(workspaceId) {
  return getJson(`/api/business/leads${query({ workspace_id: workspaceId })}`)
}
export function createBusinessLead(payload) {
  return postJson('/api/business/leads', payload)
}
export function updateBusinessLead(leadId, payload) {
  return patchJson(`/api/business/leads/${leadId}`, payload)
}
export function getBusinessSupportCases(workspaceId) {
  return getJson(`/api/business/support-cases${query({ workspace_id: workspaceId })}`)
}
export function createBusinessSupportCase(payload) {
  return postJson('/api/business/support-cases', payload)
}
export function updateBusinessSupportCase(caseId, payload) {
  return patchJson(`/api/business/support-cases/${caseId}`, payload)
}
export function getBusinessDocuments(workspaceId) {
  return getJson(`/api/business/documents${query({ workspace_id: workspaceId })}`)
}
export function createBusinessDocument(payload) {
  return postJson('/api/business/documents', payload)
}
export function getBusinessProposals(workspaceId) {
  return getJson(`/api/business/proposals${query({ workspace_id: workspaceId })}`)
}
export function createBusinessProposal(payload) {
  return postJson('/api/business/proposals', payload)
}
export function getBusinessMarketingItems(workspaceId) {
  return getJson(`/api/business/marketing-calendar${query({ workspace_id: workspaceId })}`)
}
export function createBusinessMarketingItem(payload) {
  return postJson('/api/business/marketing-calendar', payload)
}

export function getChiefDashboard(workspaceId) {
  return getJson(`/api/chief-of-staff/dashboard${query({ workspace_id: workspaceId })}`)
}
export function getChiefPriorities(workspaceId) {
  return getJson(`/api/chief-of-staff/priorities${query({ workspace_id: workspaceId })}`)
}
export function getChiefFollowups(workspaceId) {
  return getJson(`/api/chief-of-staff/followups${query({ workspace_id: workspaceId })}`)
}
export function createChiefDailyPlan(workspaceId) {
  return postJson('/api/chief-of-staff/daily-plan', { workspace_id: workspaceId })
}
export function createChiefWeeklyPlan(workspaceId) {
  return postJson('/api/chief-of-staff/weekly-plan', { workspace_id: workspaceId })
}
export function createChiefFollowup(payload) {
  return postJson('/api/chief-of-staff/followups', payload)
}
export function updateChiefFollowup(followupId, payload) {
  return patchJson(`/api/chief-of-staff/followups/${followupId}`, payload)
}

export function getSimulatorDashboard(workspaceId) {
  return getJson(`/api/business-simulator/dashboard${query({ workspace_id: workspaceId })}`)
}
export function getSimulatorScenarios(workspaceId) {
  return getJson(`/api/business-simulator/scenarios${query({ workspace_id: workspaceId })}`)
}
export function getSimulatorResults(workspaceId) {
  return getJson(`/api/business-simulator/results${query({ workspace_id: workspaceId })}`)
}
export function createSimulatorScenario(payload) {
  return postJson('/api/business-simulator/scenarios', payload)
}
export function runSimulatorScenario(scenarioId) {
  return postJson(`/api/business-simulator/scenarios/${scenarioId}/run`, {})
}

export function getMultimodalDashboard(workspaceId) {
  return getJson(`/api/multimodal/dashboard${query({ workspace_id: workspaceId })}`)
}
export function getMultimodalItems(workspaceId) {
  return getJson(`/api/multimodal/items${query({ workspace_id: workspaceId })}`)
}
export function getMultimodalAnalyses(workspaceId) {
  return getJson(`/api/multimodal/analyses${query({ workspace_id: workspaceId })}`)
}
export function createMultimodalItem(payload) {
  return postJson('/api/multimodal/items', payload)
}
export function analyzeMultimodalItem(itemId, analysisType) {
  return postJson(`/api/multimodal/items/${itemId}/analyze`, { analysis_type: analysisType })
}

export function getIndustryModesDashboard() {
  return getJson('/api/industry-modes/dashboard')
}
export function getIndustryModes() {
  return getJson('/api/industry-modes')
}
export function getIndustryModeRuns() {
  return getJson('/api/industry-modes/runs')
}
export function seedIndustryModes() {
  return postJson('/api/industry-modes/seed', {})
}
export function runIndustryMode(modeId, prompt) {
  return postJson(`/api/industry-modes/${modeId}/run`, { prompt })
}

export function getAgentNetworkDashboard() {
  return getJson('/api/agent-network/dashboard')
}
export function getAgentNetworkContracts() {
  return getJson('/api/agent-network/contracts')
}
export function getAgentNetworkAudit() {
  return getJson('/api/agent-network/audit')
}
export function createAgentNetworkContract(payload) {
  return postJson('/api/agent-network/contracts', payload)
}
export function createAgentNetworkHandoff(contractId, handoffType) {
  return postJson(`/api/agent-network/contracts/${contractId}/handoff`, { handoff_type: handoffType, payload: {} })
}
export function verifyAgentNetworkHandoff(handoffId) {
  return postJson(`/api/agent-network/handoffs/${handoffId}/verify`, {})
}

export function getSelfHealingDashboard() {
  return getJson('/api/self-healing/dashboard')
}
export function getSelfHealingChecks() {
  return getJson('/api/self-healing/checks')
}
export function getSelfHealingFindings() {
  return getJson('/api/self-healing/findings')
}
export function createSelfHealingCheck(payload) {
  return postJson('/api/self-healing/checks', payload)
}
export function createSelfHealingRepairTask(findingId) {
  return postJson(`/api/self-healing/findings/${findingId}/repair-task`, {})
}
export function verifySelfHealingRepair(repairId, payload) {
  return postJson(`/api/self-healing/repairs/${repairId}/verify`, payload || {})
}

export function getCompanyBrainDashboard() {
  return getJson('/api/company-brain/dashboard')
}
export function getCompanyBrainDecisions() {
  return getJson('/api/company-brain/decisions')
}
export function getCompanyBrainReports() {
  return getJson('/api/company-brain/reports')
}
export function createCompanyBrainStrategy(payload) {
  return postJson('/api/company-brain/strategy', payload)
}
export function createCompanyBrainDecision(payload) {
  return postJson('/api/company-brain/decisions', payload)
}
export function createCompanyBrainReport() {
  return postJson('/api/company-brain/reports', {})
}

export function getDeviceOperatorDashboard() {
  return getJson('/api/device-operator/dashboard')
}
export function getDeviceOperatorSessions() {
  return getJson('/api/device-operator/sessions')
}
export function getDeviceOperatorAudit() {
  return getJson('/api/device-operator/audit')
}
export function createDeviceOperatorSession(payload) {
  return postJson('/api/device-operator/sessions', payload)
}
export function planDeviceOperatorSession(sessionId, payload) {
  return postJson(`/api/device-operator/sessions/${sessionId}/plan`, payload)
}
export function confirmDeviceOperatorAction(sessionId, actionId, approve) {
  return postJson(`/api/device-operator/sessions/${sessionId}/confirm-action`, { action_id: actionId, approve })
}

export function getTrainingLabDashboard() {
  return getJson('/api/training-lab/dashboard')
}
export function getTrainingDatasets() {
  return getJson('/api/training-lab/datasets')
}
export function getTrainingDataset(datasetId) {
  return getJson(`/api/training-lab/datasets/${datasetId}`)
}
export function createTrainingDataset(payload) {
  return postJson('/api/training-lab/datasets', payload)
}
export function addTrainingExample(datasetId, payload) {
  return postJson(`/api/training-lab/datasets/${datasetId}/examples`, payload)
}
export function updateTrainingExample(exampleId, payload) {
  return patchJson(`/api/training-lab/examples/${exampleId}`, payload)
}
export function exportTrainingDataset(datasetId) {
  return postJson(`/api/training-lab/datasets/${datasetId}/export`, {})
}
export function createTrainingRun(payload) {
  return postJson('/api/training-lab/runs', payload)
}
export function createTrainingComparison(payload) {
  return postJson('/api/training-lab/comparisons', payload)
}

export function getAvatarDashboard() {
  return getJson('/api/avatar/dashboard')
}
export function getAvatarPersona() {
  return getJson('/api/avatar/persona')
}
export function updateAvatarPersona(payload) {
  return patchJson('/api/avatar/persona', payload)
}
export function getAvatarVoiceSettings() {
  return getJson('/api/avatar/voice-settings')
}
export function updateAvatarVoiceSettings(payload) {
  return patchJson('/api/avatar/voice-settings', payload)
}
export function getAvatarMeetingSessions() {
  return getJson('/api/avatar/meeting-sessions')
}
export function createAvatarMeetingSession(payload) {
  return postJson('/api/avatar/meeting-sessions', payload)
}
export function createAvatarConsent(payload) {
  return postJson('/api/avatar/consent', payload)
}
export function generateAvatarImage(payload) {
  return postJson('/api/avatar/persona/avatar-image', payload)
}

export function getLifeOsDashboard(workspaceId) {
  return getJson(`/api/life-os/dashboard${query({ workspace_id: workspaceId })}`)
}
export function getLifeSchedule(workspaceId) {
  return getJson(`/api/life-os/schedule${query({ workspace_id: workspaceId })}`)
}
export function getLifeTasks(workspaceId) {
  return getJson(`/api/life-os/tasks${query({ workspace_id: workspaceId })}`)
}
export function getLifeReminders(workspaceId) {
  return getJson(`/api/life-os/reminders${query({ workspace_id: workspaceId })}`)
}
export function getLifeDeadlines(workspaceId) {
  return getJson(`/api/life-os/deadlines${query({ workspace_id: workspaceId })}`)
}
export function createLifeScheduleItem(payload) {
  return postJson('/api/life-os/schedule', payload)
}
export function createLifeTask(payload) {
  return postJson('/api/life-os/tasks', payload)
}
export function updateLifeTask(taskId, payload) {
  return patchJson(`/api/life-os/tasks/${taskId}`, payload)
}
export function createLifeReminder(payload) {
  return postJson('/api/life-os/reminders', payload)
}
export function createLifeDeadline(payload) {
  return postJson('/api/life-os/deadlines', payload)
}
export function createLifeDailyPlan(workspaceId) {
  return postJson('/api/life-os/daily-plan', { workspace_id: workspaceId })
}

export function getUniversalOperatorDashboard() {
  return getJson('/api/universal-operator/dashboard')
}
export function getUniversalOperatorSessions() {
  return getJson('/api/universal-operator/sessions')
}
export function getUniversalOperatorWorkflows() {
  return getJson('/api/universal-operator/workflows')
}
export function getUniversalOperatorAudit() {
  return getJson('/api/universal-operator/audit')
}
export function getUniversalOperatorHandoffs() {
  return getJson('/api/universal-operator/handoffs')
}
export function createUniversalOperatorSession(payload) {
  return postJson('/api/universal-operator/sessions', payload)
}
export function createUniversalOperatorWorkflow(payload) {
  return postJson('/api/universal-operator/workflows', payload)
}
export function planUniversalOperatorWorkflow(workflowId) {
  return postJson(`/api/universal-operator/workflows/${workflowId}/plan`, {})
}
export function decideUniversalOperatorAction(actionId, decision) {
  return postJson(`/api/universal-operator/actions/${actionId}/decision`, { decision })
}
export function createUniversalOperatorHandoff(payload) {
  return postJson('/api/universal-operator/handoffs', payload)
}

export function getSaasBuilderDashboard() {
  return getJson('/api/saas-builder/dashboard')
}
export function getSaasProjects() {
  return getJson('/api/saas-builder/projects')
}
export function getSaasProject(projectId) {
  return getJson(`/api/saas-builder/projects/${projectId}`)
}
export function getSaasFeedback(projectId) {
  return getJson(`/api/saas-builder/projects/${projectId}/feedback`)
}
export function createSaasProject(payload) {
  return postJson('/api/saas-builder/projects', payload)
}
export function validateSaasProject(projectId) {
  return postJson(`/api/saas-builder/projects/${projectId}/validate`, {})
}
export function roadmapSaasProject(projectId) {
  return postJson(`/api/saas-builder/projects/${projectId}/roadmap`, {})
}
export function architectureSaasProject(projectId) {
  return postJson(`/api/saas-builder/projects/${projectId}/architecture`, {})
}
export function launchAssetsSaasProject(projectId) {
  return postJson(`/api/saas-builder/projects/${projectId}/launch-assets`, {})
}
export function createSaasFeedback(projectId, payload) {
  return postJson(`/api/saas-builder/projects/${projectId}/feedback`, payload)
}
export function getTeamManagerDashboard() {
  return getJson('/api/team-manager/dashboard')
}
export function getTeamMembers() {
  return getJson('/api/team-manager/members')
}
export function getTeamAssignments() {
  return getJson('/api/team-manager/assignments')
}
export function getTeamStandups() {
  return getJson('/api/team-manager/standups')
}
export function getTeamSprints() {
  return getJson('/api/team-manager/sprints')
}
export function createTeamMember(payload) {
  return postJson('/api/team-manager/members', payload)
}
export function createTeamAssignment(payload) {
  return postJson('/api/team-manager/assignments', payload)
}
export function updateTeamAssignment(assignmentId, payload) {
  return patchJson(`/api/team-manager/assignments/${assignmentId}`, payload)
}
export function createTeamStandup() {
  return postJson('/api/team-manager/standups', {})
}
export function createTeamSprint(payload) {
  return postJson('/api/team-manager/sprints', payload)
}
export function reviewTeamSprint(sprintId, payload) {
  return postJson(`/api/team-manager/sprints/${sprintId}/review`, payload || {})
}

export function getBusinessOperatorDashboard() {
  return getJson('/api/business-operator/dashboard')
}
export function getBusinessOperatorWorkflows() {
  return getJson('/api/business-operator/workflows')
}
export function getBusinessOperatorReports() {
  return getJson('/api/business-operator/reports')
}
export function getBusinessOperatorKpiSnapshots() {
  return getJson('/api/business-operator/kpi-snapshots')
}
export function getBusinessOperatorApprovals() {
  return getJson('/api/business-operator/approvals')
}
export function getBusinessOperatorAudit() {
  return getJson('/api/business-operator/audit')
}
export function createBusinessOperatorWorkflow(payload) {
  return postJson('/api/business-operator/workflows', payload)
}
export function createBusinessOperatorReport(payload) {
  return postJson('/api/business-operator/reports', payload || {})
}
export function createBusinessOperatorKpiSnapshot() {
  return postJson('/api/business-operator/kpi-snapshots', {})
}
export function createBusinessOperatorApproval(payload) {
  return postJson('/api/business-operator/approvals', payload)
}
export function updateBusinessOperatorApproval(approvalId, decision) {
  return patchJson(`/api/business-operator/approvals/${approvalId}`, { decision })
}

export function getComplianceIntelDashboard() {
  return getJson('/api/compliance/dashboard')
}
export function getComplianceIntelPolicies() {
  return getJson('/api/compliance/policies')
}
export function getComplianceScans() {
  return getJson('/api/compliance/scans')
}
export function getComplianceContractReviews() {
  return getJson('/api/compliance/contracts/reviews')
}
export function getComplianceChecklists() {
  return getJson('/api/compliance/checklists')
}
export function getComplianceAuditPackages() {
  return getJson('/api/compliance/audit-packages')
}
export function createCompliancePolicy(payload) {
  return postJson('/api/compliance/policies', payload)
}
export function runComplianceScan(payload) {
  return postJson('/api/compliance/scan', payload)
}
export function reviewComplianceContract(payload) {
  return postJson('/api/compliance/contracts/review', payload)
}
export function createComplianceChecklist(payload) {
  return postJson('/api/compliance/checklists', payload)
}
export function createComplianceAuditPackage(payload) {
  return postJson('/api/compliance/audit-packages', payload || {})
}

export function getExecutiveBoardDashboard() {
  return getJson('/api/executive-board/dashboard')
}
export function getExecutiveBoardSessions() {
  return getJson('/api/executive-board/sessions')
}
export function getExecutiveBoardReports() {
  return getJson('/api/executive-board/reports')
}
export function createExecutiveBoardSession(payload) {
  return postJson('/api/executive-board/sessions', payload)
}
export function reviewExecutiveBoardSession(sessionId) {
  return postJson(`/api/executive-board/sessions/${sessionId}/review`, {})
}
export function voteExecutiveBoardSession(sessionId, payload) {
  return postJson(`/api/executive-board/sessions/${sessionId}/vote`, payload)
}
export function reportExecutiveBoardSession(sessionId) {
  return postJson(`/api/executive-board/sessions/${sessionId}/report`, {})
}

export function getInnovationDashboard() {
  return getJson('/api/innovation-lab/dashboard')
}
export function getInnovationResearch() {
  return getJson('/api/innovation-lab/research')
}
export function getInnovationCompetitors() {
  return getJson('/api/innovation-lab/competitors')
}
export function getInnovationTrends() {
  return getJson('/api/innovation-lab/trends')
}
export function getInnovationIdeas() {
  return getJson('/api/innovation-lab/ideas')
}
export function getInnovationExperiments() {
  return getJson('/api/innovation-lab/experiments')
}
export function getInnovationPrototypes() {
  return getJson('/api/innovation-lab/prototypes')
}
export function createInnovationResearch(payload) {
  return postJson('/api/innovation-lab/research', payload)
}
export function createInnovationCompetitor(payload) {
  return postJson('/api/innovation-lab/competitors', payload)
}
export function createInnovationTrend(payload) {
  return postJson('/api/innovation-lab/trends', payload)
}
export function createInnovationIdea(payload) {
  return postJson('/api/innovation-lab/ideas', payload)
}
export function createInnovationExperiment(payload) {
  return postJson('/api/innovation-lab/experiments', payload)
}
export function createInnovationPrototype(payload) {
  return postJson('/api/innovation-lab/prototypes', payload)
}
export function createInnovationReport(payload) {
  return postJson('/api/innovation-lab/reports', payload || {})
}

export function getSimWorldDashboard() {
  return getJson('/api/simulation-world/dashboard')
}
export function getSimWorldWorlds() {
  return getJson('/api/simulation-world/worlds')
}
export function getSimWorldPersonas() {
  return getJson('/api/simulation-world/personas')
}
export function getSimWorldScenarios() {
  return getJson('/api/simulation-world/scenarios')
}
export function getSimWorldReports() {
  return getJson('/api/simulation-world/reports')
}
export function createSimWorldWorld(payload) {
  return postJson('/api/simulation-world/worlds', payload)
}
export function createSimWorldPersona(payload) {
  return postJson('/api/simulation-world/personas', payload)
}
export function createSimWorldScenario(payload) {
  return postJson('/api/simulation-world/scenarios', payload)
}
export function runSimWorldScenario(scenarioId) {
  return postJson(`/api/simulation-world/scenarios/${scenarioId}/run`, {})
}
export function compareSimWorldScenarios(scenarioIds) {
  return postJson('/api/simulation-world/compare', { scenario_ids: scenarioIds })
}
export function createSimWorldReport(payload) {
  return postJson('/api/simulation-world/reports', payload || {})
}

export function getOrgOsDashboard() {
  return getJson('/api/organization-os/dashboard')
}
export function getOrgOsOrganizations() {
  return getJson('/api/organization-os/organizations')
}
export function getOrgOsMembers() {
  return getJson('/api/organization-os/members')
}
export function getOrgOsRoles() {
  return getJson('/api/organization-os/roles')
}
export function getOrgOsActivity() {
  return getJson('/api/organization-os/activity')
}
export function createOrgOsOrganization(payload) {
  return postJson('/api/organization-os/organizations', payload)
}
export function createOrgOsMember(payload) {
  return postJson('/api/organization-os/members', payload)
}
export function updateOrgOsMember(memberId, payload) {
  return patchJson(`/api/organization-os/members/${memberId}`, payload)
}
export function createOrgOsRole(payload) {
  return postJson('/api/organization-os/roles', payload)
}
export function createOrgOsWorkspaceLink(payload) {
  return postJson('/api/organization-os/workspace-links', payload)
}

export function getCompanionDashboard() {
  return getJson('/api/hardware-companion/dashboard')
}
export function getCompanionDevices() {
  return getJson('/api/hardware-companion/devices')
}
export function getCompanionSettings() {
  return getJson('/api/hardware-companion/settings')
}
export function getCompanionReadinessChecks() {
  return getJson('/api/hardware-companion/readiness-checks')
}
export function getCompanionSessions() {
  return getJson('/api/hardware-companion/sessions')
}
export function createCompanionDevice(payload) {
  return postJson('/api/hardware-companion/devices', payload)
}
export function updateCompanionSettings(payload) {
  return patchJson('/api/hardware-companion/settings', payload)
}
export function createCompanionReadinessCheck(payload) {
  return postJson('/api/hardware-companion/readiness-checks', payload || {})
}
export function createCompanionSession(payload) {
  return postJson('/api/hardware-companion/sessions', payload)
}

export function getOperatingLayerDashboard() {
  return getJson('/api/operating-layer/dashboard')
}
export function getOperatingLayerCapabilities() {
  return getJson('/api/operating-layer/capabilities')
}
export function getOperatingLayerSnapshots() {
  return getJson('/api/operating-layer/snapshots')
}
export function getOperatingLayerRecommendations() {
  return getJson('/api/operating-layer/recommendations')
}
export function createOperatingLayerSnapshot() {
  return postJson('/api/operating-layer/snapshots', {})
}
export function createOperatingLayerRecommendations() {
  return postJson('/api/operating-layer/recommendations', {})
}
export function createOperatingLayerReport() {
  return postJson('/api/operating-layer/report', {})
}

export function getMcpSummary() {
  return getJson('/api/mcp/summary')
}
export function getMcpTemplates() {
  return getJson('/api/mcp/templates')
}
export function getMcpConnectors() {
  return getJson('/api/mcp/connectors')
}
export function getMcpEvents(connectorId) {
  return getJson(connectorId ? `/api/mcp/events?connector_id=${connectorId}` : '/api/mcp/events')
}
export function createMcpConnector(payload) {
  return postJson('/api/mcp/connectors', payload)
}
export function enableMcpConnector(connectorId) {
  return postJson(`/api/mcp/connectors/${connectorId}/enable`, {})
}
export function disableMcpConnector(connectorId) {
  return postJson(`/api/mcp/connectors/${connectorId}/disable`, {})
}
export function checkMcpConnector(connectorId) {
  return postJson(`/api/mcp/connectors/${connectorId}/check`, {})
}
export function planMcpConnectorAction(connectorId, actionName, payload) {
  return postJson(`/api/mcp/connectors/${connectorId}/plan-action`, { action_name: actionName, payload: payload || {} })
}

export function getMcpExecutionSummary() {
  return getJson('/api/mcp/executions/summary')
}
export function getMcpAdapterStatus() {
  return getJson('/api/mcp/adapter/status')
}
export function getMcpInbox(riskLevel) {
  return getJson(riskLevel ? `/api/mcp/inbox?risk_level=${riskLevel}` : '/api/mcp/inbox')
}
export function getMcpInboxSummary() {
  return getJson('/api/mcp/inbox/summary')
}
export function approveMcpInboxItem(itemId) {
  return postJson(`/api/mcp/inbox/${itemId}/approve`, {})
}
export function rejectMcpInboxItem(itemId) {
  return postJson(`/api/mcp/inbox/${itemId}/reject`, {})
}
export function getMcpPolicies() {
  return getJson('/api/mcp/policies')
}
export function getMcpPolicySummary() {
  return getJson('/api/mcp/policies/summary')
}
export function createMcpPolicy(payload) {
  return postJson('/api/mcp/policies', payload)
}
export function updateMcpPolicy(policyId, payload) {
  return patchJson(`/api/mcp/policies/${policyId}`, payload)
}
export function getMcpAudit(params) {
  const qs = new URLSearchParams(params || {}).toString()
  return getJson(qs ? `/api/mcp/audit?${qs}` : '/api/mcp/audit')
}
export function getMcpAuditSummary() {
  return getJson('/api/mcp/audit/summary')
}
export function replayMcpRequest(requestId) {
  return postJson('/api/mcp/audit/replay', { request_id: requestId })
}
export function getMcpSecrets() {
  return getJson('/api/mcp/secrets')
}
export function getMcpSecretsSummary() {
  return getJson('/api/mcp/secrets/summary')
}
export function registerMcpSecret(payload) {
  return postJson('/api/mcp/secrets', payload)
}
export function rotateMcpSecret(refId) {
  return postJson(`/api/mcp/secrets/${refId}/rotate`, {})
}
export function getApprovalsCenter(source) {
  return getJson(source ? `/api/approvals-center?source=${source}` : '/api/approvals-center')
}
export function getApprovalsCenterSummary() {
  return getJson('/api/approvals-center/summary')
}
export function approveCenterItem(source, itemId) {
  return postJson('/api/approvals-center/approve', { source, item_id: itemId })
}
export function rejectCenterItem(source, itemId) {
  return postJson('/api/approvals-center/reject', { source, item_id: itemId })
}
export function getHealthMonitorDashboard() {
  return getJson('/api/health-monitor/dashboard')
}
export function createHealthSnapshot() {
  return postJson('/api/health-monitor/snapshots', {})
}
export function getMcpExecutions(connectorId) {
  return getJson(connectorId ? `/api/mcp/executions?connector_id=${connectorId}` : '/api/mcp/executions')
}
export function requestMcpExecution(connectorId, actionName, payload) {
  return postJson(`/api/mcp/connectors/${connectorId}/execute`, { action_name: actionName, payload: payload || {} })
}
export function approveMcpExecution(requestId) {
  return postJson(`/api/mcp/executions/${requestId}/approve`, {})
}
export function rejectMcpExecution(requestId) {
  return postJson(`/api/mcp/executions/${requestId}/reject`, {})
}
export function runMcpExecution(requestId) {
  return postJson(`/api/mcp/executions/${requestId}/run`, {})
}
