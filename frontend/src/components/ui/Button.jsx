// Phase 0 design-system primitive. Additive; opt-in.
export function Button({ variant = 'default', size = 'md', className = '', children, ...rest }) {
  const v = variant === 'primary' ? 'ds-btn--primary' : variant === 'ghost' ? 'ds-btn--ghost' : ''
  const s = size === 'sm' ? 'ds-btn--sm' : ''
  return (
    <button type="button" className={`ds-btn ${v} ${s} ${className}`} {...rest}>
      {children}
    </button>
  )
}

export default Button
