// Phase 0 design-system primitive. Additive; opt-in.
export function Badge({ tone = 'default', className = '', children, ...rest }) {
  const t = tone === 'accent' ? 'ds-badge--accent'
    : tone === 'success' ? 'ds-badge--success'
    : tone === 'warn' ? 'ds-badge--warn'
    : tone === 'danger' ? 'ds-badge--danger' : ''
  return <span className={`ds-badge ${t} ${className}`} {...rest}>{children}</span>
}

export default Badge
