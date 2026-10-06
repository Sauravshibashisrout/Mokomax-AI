import { useState } from 'react'

export default function SourceCitations({ sources }) {
  const [open, setOpen] = useState(false)
  if (!sources?.length) return null

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1.5 text-[11px] text-muted bg-white/5
          hover:bg-white/10 px-2.5 py-1 rounded-full transition-colors duration-150"
      >
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        {sources.length} source{sources.length > 1 ? 's' : ''}
        <svg className={`w-3 h-3 transition-transform duration-150 ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="mt-2 space-y-1.5">
          {sources.map((s, i) => (
            <div key={i} className="bg-white/5 rounded-2xl px-3 py-2.5 text-[11px]">
              <div className="flex justify-between items-center mb-1">
                <span className="font-semibold text-accent">{s.filename} · chunk {s.chunk_index}</span>
                <span className="text-muted">{s.score}</span>
              </div>
              <p className="text-muted leading-relaxed line-clamp-2">{s.text_preview}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
