import { useEffect, useMemo, useRef, useState } from 'react'

// Phase 3 — ⌘K command palette. Keyboard-first navigation over a flat command list.
// Additive: driven entirely by the `commands` prop provided by App.jsx.
export function CommandPalette({ open, onClose, commands }) {
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const inputRef = useRef(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return commands.slice(0, 40)
    return commands
      .filter((c) => (`${c.label} ${c.group || ''} ${c.hint || ''}`).toLowerCase().includes(q))
      .slice(0, 40)
  }, [query, commands])

  useEffect(() => {
    if (open) {
      setQuery('')
      setActive(0)
      // focus after paint
      const t = setTimeout(() => inputRef.current?.focus(), 20)
      return () => clearTimeout(t)
    }
  }, [open])

  useEffect(() => { setActive(0) }, [query])

  if (!open) return null

  function run(cmd) {
    if (!cmd) return
    onClose()
    cmd.run()
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') { e.preventDefault(); onClose() }
    else if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => Math.min(a + 1, filtered.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)) }
    else if (e.key === 'Enter') { e.preventDefault(); run(filtered[active]) }
  }

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
