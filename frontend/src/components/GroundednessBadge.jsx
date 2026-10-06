export default function GroundednessBadge({ score, flagged }) {
  if (score === null || score === undefined) return null

  const pct = Math.round(score * 100)
  const dot = flagged
    ? 'bg-red-500'
    : score >= 0.7
    ? 'bg-emerald-500'
    : 'bg-amber-400'

  const label = flagged ? 'Low confidence' : score >= 0.7 ? 'Well grounded' : 'Partially grounded'

  return (
    <span className="group relative inline-flex items-center gap-1.5 cursor-default">
      <span className={`w-2 h-2 rounded-full ${dot} shrink-0`} />
      <span className="text-[11px] text-muted">{pct}%</span>
      {/* Tooltip */}
      <span className="pointer-events-none absolute bottom-full left-0 mb-1.5 whitespace-nowrap
        bg-surface border border-white/10 text-body text-[11px] px-2 py-1 rounded-lg
        opacity-0 group-hover:opacity-100 transition-opacity duration-150 shadow-lg z-10">
        {label} · groundedness {pct}%
      </span>
    </span>
  )
}
