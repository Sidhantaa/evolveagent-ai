// Phase 0 design-system primitive. Additive; opt-in.
export function GlassPanel({ className = '', children, ...rest }) {
  return <div className={`ds-glass ${className}`} {...rest}>{children}</div>
}

export default GlassPanel
