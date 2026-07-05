// Phase 0 design-system primitive. Additive; opt-in.
export function Card({ hover = false, className = '', children, ...rest }) {
  return (
    <div className={`ds-card ${hover ? 'ds-card--hover' : ''} ${className}`} {...rest}>
      {children}
    </div>
  )
}

export default Card
