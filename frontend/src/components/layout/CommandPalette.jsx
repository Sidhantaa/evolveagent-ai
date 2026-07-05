import { useEffect, useMemo, useRef, useState } from 'react'

// Fuzzy subsequence score: all query chars must appear in order. Rewards
// contiguous runs and word-start matches so "ogit" ~ "Open Git Intelligence".
function fuzzyScore(query, text) {
  const q = query.toLowerCase()
  const t = text.toLowerCase()
  if (!q) return 1
  let qi = 0
  let score = 0
  let streak = 0
  let prev = -1
  for (let ti = 0; ti < t.length && qi < q.length; ti += 1) {
    if (t[ti] === q[qi]) {
      streak += 1
      score += 1 + streak // contiguous chars worth more
      if (ti === 0 || t[ti - 1] === ' ') score += 3 // word-start bonus
      if (prev >= 0 && ti === prev + 1) score += 1
      prev = ti
      qi += 1
    } else {
      streak = 0
    }
  }
  return qi === q.length ? score : 0
}

// Phase 3 — ⌘K command palette, polished: fuzzy scoring + recent commands.
export function CommandPalette({ open, onClose, commands, recentIds = [], onRun }) {
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const inputRef = useRef(null)

  const filtered = useMemo(() => {
    const q = query.trim()
    if (!q) {
      // No query: recent commands first (in recency order), then the rest.
      const byId = new Map(commands.map((c) => [c.id, c]))
      const recent = recentIds.map((id) => byId.get(id)).filter(Boolean)
      const recentSet = new Set(recentIds)
      const rest = commands.filter((c) => !recentSet.has(c.id))
      return [...recent, ...rest].slice(0, 40).map((c) => ({ ...c, recent: recentSet.has(c.id) }))
    }
    return commands
      .map((c) => ({ c, s: fuzzyScore(q, `${c.label} ${c.group || ''} ${c.hint || ''}`) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s)
      .slice(0, 40)
      .map((x) => x.c)
  }, [query, commands, recentIds])

  useEffect(() => {
    if (open) {
      setQuery('')
      setActive(0)
      const t = setTimeout(() => inputRef.current?.focus(), 20)
      return () => clearTimeout(t)
    }
  }, [open])

  useEffect(() => { setActive(0) }, [query])

  if (!open) return null

  function run(cmd) {
    if (!cmd) return
    onClose()
    onRun?.(cmd.id)
    cmd.run()
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') { e.preventDefault(); onClose() }
    else if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => Math.min(a + 1, filtered.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)) }
    else if (e.key === 'Enter') { e.preventDefault(); run(filtered[active]) }
  }

  const showingRecent = !query.trim() && recentIds.length > 0

  return (
    <div className="cmdk-overlay" onMouseDown={onClose}>
      <div className="cmdk" onMouseDown={(e) => e.stopPropagation()} role="dialog" aria-label="Command palette">
        <input
          ref={inputRef}
          className="cmdk-input"
          placeholder="Type a command or search…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <div className="cmdk-list">
          {filtered.length === 0 && <div className="cmdk-empty">No matching commands</div>}
          {filtered.map((cmd, i) => (
            <button
              key={cmd.id}
              type="button"
              className={`cmdk-item ${i === active ? 'active' : ''}`}
              onMouseEnter={() => setActive(i)}
              onClick={() => run(cmd)}
            >
              {cmd.icon && <span className="cmdk-icon">{cmd.icon}</span>}
              <span className="cmdk-label">{cmd.label}</span>
              {showingRecent && cmd.recent && <span className="cmdk-group">recent</span>}
              {cmd.group && <span className="cmdk-group">{cmd.group}</span>}
            </button>
          ))}
        </div>
        <div className="cmdk-footer"><span>↑↓ navigate</span><span>↵ run</span><span>esc close</span></div>
      </div>
    </div>
  )
}

export default CommandPalette
